import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from .access import Capability, locked_access, require_access
from .exceptions import (
    IdempotencyConflict,
    IncomePeriodConflict,
    IncomeVersionConflict,
)
from .models import (
    AccountingMonth,
    AccountingMonthState,
    AccountingYear,
    Household,
    HouseholdMember,
    IncomeCreateIdempotency,
    IncomeKind,
    IncomeRecord,
    IncomeSource,
)
from .record_services import write_audit


@dataclass(frozen=True)
class IncomeCreateResult:
    status_code: int
    body: dict


def resolve_income_period(*, household_id, year_id, month_id, lock_year=False):
    years = AccountingYear.objects.filter(household_id=household_id)
    if lock_year:
        years = years.select_for_update()
    year = get_object_or_404(years, pk=year_id)
    month = get_object_or_404(
        AccountingMonth.objects.select_related("accounting_year"),
        pk=month_id,
        accounting_year_id=year.pk,
    )
    return year, month


def require_active_month(month):
    if month.state != AccountingMonthState.ACTIVE:
        raise IncomePeriodConflict()


def _recipient_snapshot(*, household, member):
    if member is None:
        return {"kind": "household", "id": None, "label": household.name}
    return {"kind": "member", "id": str(member.pk), "label": member.display_name}


def _contract_snapshot(source):
    if source.kind != IncomeKind.CONTRACT:
        return None
    contract = source.contract
    other_type_name = contract.other_type_name or None
    return {
        "company_id": str(contract.company_id),
        "company_name": contract.company.name,
        "contract_type": contract.contract_type,
        "other_type_name": other_type_name,
    }


def _source_snapshot(source):
    return {
        "id": str(source.pk),
        "name": source.name,
        "kind": source.kind,
        "version": source.version,
        "contract": _contract_snapshot(source),
    }


def _income_response(record):
    return {
        "id": str(record.pk),
        "household_id": str(record.household_id),
        "month_id": str(record.accounting_month_id),
        "member_id": str(record.member_id) if record.member_id else None,
        "source_id": str(record.income_source_id),
        "amount": format(record.amount, ".2f"),
        "currency": record.currency,
        "receipt_date": record.receipt_date.isoformat(),
        "version": record.version,
        "recipient_snapshot": record.recipient_snapshot,
        "source_snapshot": record.source_snapshot,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def _income_audit_snapshot(record):
    return {
        "household_id": str(record.household_id),
        "month_id": str(record.accounting_month_id),
        "member_id": str(record.member_id) if record.member_id else None,
        "source_id": str(record.income_source_id),
        "amount": format(record.amount, ".2f"),
        "currency": record.currency,
        "receipt_date": record.receipt_date.isoformat(),
        "version": record.version,
        "recipient_snapshot": record.recipient_snapshot,
        "source_snapshot": record.source_snapshot,
        "deleted_at": record.deleted_at.isoformat() if record.deleted_at else None,
    }


def _eligible_income_sources(*, household_id, month, member_id):
    return IncomeSource.objects.filter(
        household_id=household_id,
        member_id=member_id,
        is_active=True,
        start_date__lte=month.month_end,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=month.month_start))


def _resolve_assignment(*, household_id, month, member_id, source_id):
    member = None
    if member_id is not None:
        member = HouseholdMember.objects.filter(
            household_id=household_id, pk=member_id, is_active=True
        ).first()
        if member is None:
            raise NotFound()

    source = (
        IncomeSource.objects.select_related("contract__company")
        .filter(household_id=household_id, pk=source_id)
        .first()
    )
    if source is None:
        raise NotFound()
    if (
        not _eligible_income_sources(
            household_id=household_id,
            month=month,
            member_id=member_id,
        )
        .filter(pk=source.pk)
        .exists()
    ):
        raise ValidationError(
            {
                "source_id": "Źródło musi być aktywne, przypisane do odbiorcy i obejmować wybrany miesiąc."
            }
        )
    return member, source


def _fingerprint(*, year_id, month_id, data):
    canonical_data = {
        "member_id": str(data.get("member_id")) if data.get("member_id") else None,
        "source_id": str(data["source_id"]),
        "amount": format(data["amount"], ".2f"),
        "currency": data["currency"],
        "receipt_date": data["receipt_date"].isoformat(),
    }
    canonical_request = {
        "operation": "income.create",
        "year_id": str(year_id),
        "month_id": str(month_id),
        "body": canonical_data,
    }
    encoded = json.dumps(canonical_request, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def create_income_record(*, user, household_id, year_id, month_id, data, idempotency_key: UUID):
    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        household = get_object_or_404(Household.objects.filter(pk=household_id))
        year, month = resolve_income_period(
            household_id=household_id, year_id=year_id, month_id=month_id
        )
        fingerprint = _fingerprint(year_id=year.pk, month_id=month.pk, data=data)
        existing = IncomeCreateIdempotency.objects.filter(
            household_id=household_id,
            actor_id=user.pk,
            operation="income.create",
            client_key=idempotency_key,
        ).first()
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise IdempotencyConflict()
            return IncomeCreateResult(existing.response_status, existing.response_body)

        _, month = resolve_income_period(
            household_id=household_id, year_id=year.pk, month_id=month.pk, lock_year=True
        )
        require_active_month(month)
        member, source = _resolve_assignment(
            household_id=household_id,
            month=month,
            member_id=data.get("member_id"),
            source_id=data["source_id"],
        )
        record = IncomeRecord.objects.create(
            household_id=household_id,
            accounting_month=month,
            member=member,
            income_source=source,
            amount=data["amount"],
            currency=data["currency"],
            receipt_date=data["receipt_date"],
            recipient_snapshot=_recipient_snapshot(household=household, member=member),
            source_snapshot=_source_snapshot(source),
        )
        response_body = _income_response(record)
        write_audit(
            user=user,
            household_id=household_id,
            action="created",
            object_type="income_record",
            object_id=record.pk,
            before=None,
            after=_income_audit_snapshot(record),
        )
        IncomeCreateIdempotency.objects.create(
            household_id=household_id,
            actor=user,
            operation="income.create",
            client_key=idempotency_key,
            fingerprint=fingerprint,
            income_record=record,
            response_status=201,
            response_body=response_body,
        )
        return IncomeCreateResult(201, response_body)


def update_income_record(*, user, household_id, year_id, month_id, income_id, data):
    data = dict(data)
    expected_version = data.pop("expected_version")
    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        year, month = resolve_income_period(
            household_id=household_id, year_id=year_id, month_id=month_id
        )
        _, month = resolve_income_period(
            household_id=household_id, year_id=year.pk, month_id=month.pk, lock_year=True
        )
        record = get_object_or_404(
            IncomeRecord.objects.select_for_update(),
            household_id=household_id,
            accounting_month_id=month.pk,
            pk=income_id,
            deleted_at__isnull=True,
        )
        require_active_month(month)
        if record.version != expected_version:
            raise IncomeVersionConflict()

        effective_member_id = data.get("member_id", record.member_id)
        effective_source_id = data.get("source_id", record.income_source_id)
        member_changed = effective_member_id != record.member_id
        source_changed = effective_source_id != record.income_source_id
        if member_changed or source_changed:
            member, source = _resolve_assignment(
                household_id=household_id,
                month=month,
                member_id=effective_member_id,
                source_id=effective_source_id,
            )
        else:
            member = record.member
            source = record.income_source

        before = _income_audit_snapshot(record)
        fields_changed = False
        if member_changed:
            record.member = member
            record.recipient_snapshot = _recipient_snapshot(
                household=record.household, member=member
            )
            fields_changed = True
        if source_changed:
            record.income_source = source
            record.source_snapshot = _source_snapshot(source)
            fields_changed = True
        for field in ("amount", "currency", "receipt_date"):
            if field in data and getattr(record, field) != data[field]:
                setattr(record, field, data[field])
                fields_changed = True

        if not fields_changed:
            return record
        record.version += 1
        record.save(
            update_fields=[
                "member",
                "income_source",
                "amount",
                "currency",
                "receipt_date",
                "recipient_snapshot",
                "source_snapshot",
                "version",
                "updated_at",
            ]
        )
        write_audit(
            user=user,
            household_id=household_id,
            action="updated",
            object_type="income_record",
            object_id=record.pk,
            before=before,
            after=_income_audit_snapshot(record),
        )
        return record


def delete_income_record(*, user, household_id, year_id, month_id, income_id, expected_version):
    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        year, month = resolve_income_period(
            household_id=household_id, year_id=year_id, month_id=month_id
        )
        _, month = resolve_income_period(
            household_id=household_id, year_id=year.pk, month_id=month.pk, lock_year=True
        )
        record = get_object_or_404(
            IncomeRecord.objects.select_for_update(),
            household_id=household_id,
            accounting_month_id=month.pk,
            pk=income_id,
            deleted_at__isnull=True,
        )
        require_active_month(month)
        if record.version != expected_version:
            raise IncomeVersionConflict()

        before = _income_audit_snapshot(record)
        record.deleted_at = timezone.now()
        record.deleted_by = user
        record.version += 1
        record.save(update_fields=["deleted_at", "deleted_by", "version", "updated_at"])
        write_audit(
            user=user,
            household_id=household_id,
            action="deleted",
            object_type="income_record",
            object_id=record.pk,
            before=before,
            after=_income_audit_snapshot(record),
        )
        return record


def income_queryset(*, household_id, month_id):
    return (
        IncomeRecord.objects.filter(
            household_id=household_id,
            accounting_month_id=month_id,
            deleted_at__isnull=True,
        )
        .select_related(
            "household",
            "accounting_month__accounting_year",
            "member",
            "income_source__contract__company",
        )
        .order_by("receipt_date", "created_at", "id")
    )


def income_source_options(*, user, household_id, year_id, month_id, member_id):
    require_access(user=user, household_id=household_id)
    _, month = resolve_income_period(household_id=household_id, year_id=year_id, month_id=month_id)
    require_active_month(month)
    if member_id is not None:
        member_exists = HouseholdMember.objects.filter(
            household_id=household_id, pk=member_id, is_active=True
        ).exists()
        if not member_exists:
            raise NotFound()

    return (
        _eligible_income_sources(household_id=household_id, month=month, member_id=member_id)
        .select_related("contract__company")
        .order_by("name", "id")
    )


def month_income_totals(*, user, household_id, year_id, month_id):
    require_access(user=user, household_id=household_id)
    _, month = resolve_income_period(household_id=household_id, year_id=year_id, month_id=month_id)
    totals = (
        IncomeRecord.objects.filter(
            household_id=household_id,
            accounting_month_id=month.pk,
            deleted_at__isnull=True,
        )
        .values("currency")
        .annotate(amount=Sum("amount"))
        .order_by("currency")
    )
    return [{"currency": item["currency"], "amount": item["amount"]} for item in totals]


def year_income_totals(*, user, household_id, year_id):
    require_access(user=user, household_id=household_id)
    year = get_object_or_404(AccountingYear.objects.filter(household_id=household_id), pk=year_id)
    totals = (
        IncomeRecord.objects.filter(
            household_id=household_id,
            accounting_month__accounting_year_id=year.pk,
            deleted_at__isnull=True,
        )
        .values("currency")
        .annotate(amount=Sum("amount"))
        .order_by("currency")
    )
    return [{"currency": item["currency"], "amount": item["amount"]} for item in totals]


def source_option_data(source):
    contract_data = _contract_snapshot(source)
    return {
        "id": source.pk,
        "name": source.name,
        "kind": source.kind,
        "start_date": source.start_date,
        "end_date": source.end_date,
        "currency": source.currency,
        "contract": contract_data,
    }
