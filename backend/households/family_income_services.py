from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .access import Capability, locked_access
from .exceptions import SourceConflict
from .models import (
    Company,
    Contract,
    ContractType,
    HouseholdMember,
    IncomeKind,
    IncomeSource,
)
from .record_services import income_snapshot, save_validated, write_audit

SOURCE_FIELDS = frozenset({"member_id", "name", "start_date", "end_date", "currency"})
CONTRACT_FIELDS = frozenset(
    {"company_id", "contract_type", "other_type_name", "position", "gross_amount", "gross_basis"}
)


def company_snapshot(company):
    return {
        "name": company.name,
        "is_active": company.is_active,
        "deactivated_at": (company.deactivated_at.isoformat() if company.deactivated_at else None),
    }


def source_snapshot(source):
    return {**income_snapshot(source), "kind": source.kind, "version": source.version}


def contract_snapshot(source, contract):
    return {
        **source_snapshot(source),
        "company_id": str(contract.company_id),
        "contract_type": contract.contract_type,
        "other_type_name": contract.other_type_name,
        "position": contract.position,
        "gross_amount": format(contract.gross_amount, ".2f"),
        "gross_basis": contract.gross_basis,
    }


def require_active_link(model, *, household_id, record_id, field):
    if not model.objects.filter(household_id=household_id, pk=record_id, is_active=True).exists():
        raise ValidationError({field: "Wybierz aktywny obiekt z tego gospodarstwa."})


def validate_contract_details(contract):
    if contract.contract_type == ContractType.OTHER:
        if not contract.other_type_name.strip():
            raise ValidationError({"other_type_name": "Podaj nazwę rodzaju umowy."})
    elif contract.other_type_name:
        raise ValidationError({"other_type_name": "To pole dotyczy tylko innej umowy."})
    if contract.position and contract.contract_type not in {
        ContractType.EMPLOYMENT,
        ContractType.MANDATE,
    }:
        raise ValidationError({"position": "Stanowisko nie dotyczy tego rodzaju umowy."})
    if not isinstance(contract.gross_amount, Decimal) or not contract.gross_amount.is_finite():
        raise ValidationError({"gross_amount": "Podaj poprawną kwotę dziesiętną."})


def write_company(*, user, household_id, data, company_id=None, archive=False):
    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        company = (
            get_object_or_404(
                Company.objects.select_for_update(), household_id=household_id, pk=company_id
            )
            if company_id is not None
            else Company(household_id=household_id)
        )
        before = company_snapshot(company) if company_id is not None else None
        if archive:
            if not company.is_active:
                return company
            company.is_active = False
            company.deactivated_at = timezone.now()
        else:
            if not company.is_active:
                raise ValidationError({"detail": "Nie można edytować archiwalnej firmy."})
            company.name = data["name"]
        save_validated(company)
        write_audit(
            user=user,
            household_id=household_id,
            action="archived" if archive else "updated" if company_id else "created",
            object_type="company",
            object_id=company.pk,
            before=before,
            after=company_snapshot(company),
        )
        return company


def write_contract(*, user, household_id, data, source_id=None, archive=False, conversion=False):
    data = dict(data)
    expected_version = data.pop("expected_version", None)
    if conversion and expected_version is None:
        raise ValidationError({"expected_version": "Podaj wersję źródła."})
    if source_id is None and expected_version is not None:
        raise ValidationError({"expected_version": "Nowa umowa nie ma jeszcze wersji."})

    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        source = (
            get_object_or_404(
                IncomeSource.objects.select_for_update(),
                household_id=household_id,
                pk=source_id,
            )
            if source_id is not None
            else IncomeSource(household_id=household_id, kind=IncomeKind.CONTRACT)
        )
        if source_id is not None:
            wanted_kind = IncomeKind.OTHER if conversion else IncomeKind.CONTRACT
            if source.kind != wanted_kind:
                raise SourceConflict()
            if not archive and expected_version is None:
                raise ValidationError({"expected_version": "Podaj wersję źródła."})
            if expected_version is not None and source.version != expected_version:
                raise SourceConflict("Źródło zostało zmienione. Odśwież dane i spróbuj ponownie.")
        contract = (
            Contract.objects.select_related("company").get(source=source)
            if source_id is not None and not conversion
            else Contract(source=source)
        )
        before = (
            source_snapshot(source)
            if conversion
            else contract_snapshot(source, contract)
            if source_id is not None
            else None
        )
        if archive:
            if not source.is_active:
                return contract
            source.is_active = False
            source.deactivated_at = timezone.now()
        else:
            if not source.is_active:
                raise ValidationError({"detail": "Nie można edytować archiwalnej umowy."})
            if source_id is None or conversion:
                source.kind = IncomeKind.CONTRACT
                source.category = ""
                source.payer = ""
                source.default_monthly_amount = None
                source.frequency = ""
                source.is_regular = None
                source.description = ""
            for field in SOURCE_FIELDS & data.keys():
                value = data[field]
                if field == "member_id" and (
                    source_id is None or conversion or value != source.member_id
                ):
                    require_active_link(
                        HouseholdMember,
                        household_id=household_id,
                        record_id=value,
                        field=field,
                    )
                setattr(source, field, value)
            if source.member_id is None:
                raise ValidationError({"member_id": "Umowa wymaga członka gospodarstwa."})
            for field in CONTRACT_FIELDS & data.keys():
                value = data[field]
                if field == "company_id" and (
                    source_id is None or conversion or value != contract.company_id
                ):
                    require_active_link(
                        Company,
                        household_id=household_id,
                        record_id=value,
                        field=field,
                    )
                setattr(contract, field, value)
            if "contract_type" in data:
                if "other_type_name" not in data and contract.contract_type != ContractType.OTHER:
                    contract.other_type_name = ""
                if "position" not in data and contract.contract_type not in {
                    ContractType.EMPLOYMENT,
                    ContractType.MANDATE,
                }:
                    contract.position = ""
            validate_contract_details(contract)
        if source_id is not None:
            source.version += 1
        save_validated(source)
        save_validated(contract)
        write_audit(
            user=user,
            household_id=household_id,
            action=(
                "converted"
                if conversion
                else "archived"
                if archive
                else "updated"
                if source_id
                else "created"
            ),
            object_type="income_source",
            object_id=source.pk,
            before=before,
            after=contract_snapshot(source, contract),
        )
        return contract
