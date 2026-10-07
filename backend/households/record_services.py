from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .access import Capability, locked_access
from .exceptions import SourceConflict
from .models import (
    AuditLog,
    HouseholdMember,
    IncomeFrequency,
    IncomeKind,
    IncomeSource,
    Membership,
    RelationType,
)

# Explicit allowlists keep new model fields out of writes and audit snapshots by default.
WRITE_FIELDS = {
    HouseholdMember: frozenset({"display_name", "account_id", "relation_type_id"}),
    RelationType: frozenset({"name"}),
    IncomeSource: frozenset(
        {
            "member_id",
            "name",
            "category",
            "payer",
            "start_date",
            "end_date",
            "default_monthly_amount",
            "currency",
            "frequency",
            "is_regular",
            "description",
        }
    ),
}
AUDIT_FIELDS = (*sorted(WRITE_FIELDS[IncomeSource]), "is_active", "deactivated_at")


def income_snapshot(source):
    snapshot = {}
    for field in AUDIT_FIELDS:
        value = getattr(source, field)
        if isinstance(value, Decimal):
            value = format(value, ".2f")
        elif isinstance(value, date | datetime):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        snapshot[field] = value
    return snapshot


def validate_links(record, data):
    """Only newly assigned links must be active; archived historical links remain valid."""
    if isinstance(record, HouseholdMember):
        if (
            data.get("account_id") is not None
            and not Membership.objects.filter(
                household_id=record.household_id, user_id=data["account_id"], user__is_active=True
            ).exists()
        ):
            raise ValidationError({"account_id": "Konto musi należeć do tego gospodarstwa."})
        linked_fields = {"relation_type_id": RelationType}
    elif isinstance(record, IncomeSource):
        linked_fields = {"member_id": HouseholdMember}
    else:
        linked_fields = {}
    for field, model in linked_fields.items():
        value = data.get(field)
        unchanged_income_owner = (
            isinstance(record, IncomeSource) and record.pk is not None and value == record.member_id
        )
        if value is None:
            continue
        related_records = model.objects.filter(pk=value, household_id=record.household_id)
        if not unchanged_income_owner:
            related_records = related_records.filter(is_active=True)
        if not related_records.exists():
            raise ValidationError({field: "Wybierz aktywny obiekt z tego gospodarstwa."})


def save_validated(record):
    try:
        record.full_clean()
    except ModelValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    record.save()


def write_audit(*, user, household_id, action, object_type, object_id, before, after):
    return AuditLog.objects.create(
        household_id=household_id,
        actor=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        before=before,
        after=after,
    )


def write_record(*, user, household_id, model, data, record_id=None, deactivate=False):
    """Shared write lifecycle for the three archivable household records."""
    data = dict(data)
    expected_version = data.pop("expected_version", None) if model is IncomeSource else None
    if (
        model is IncomeSource
        and "kind" in data
        and (record_id is not None or data.pop("kind") != IncomeKind.OTHER)
    ):
        raise ValidationError({"kind": "Umowy wymagają osobnego endpointu."})
    unknown = set(data) - WRITE_FIELDS[model]
    if unknown:
        raise ValidationError({field: "Nieznane pole." for field in sorted(unknown)})
    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        record = (
            get_object_or_404(
                model.objects.select_for_update(), household_id=household_id, pk=record_id
            )
            if record_id is not None
            else model(household_id=household_id)
        )
        if model is IncomeSource and record.kind != IncomeKind.OTHER:
            raise SourceConflict("Umowę zmień przez endpoint umów.")
        if model is IncomeSource:
            if record_id is not None and not deactivate:
                if expected_version is None:
                    raise ValidationError({"expected_version": "Podaj wersję źródła."})
                if record.version != expected_version:
                    raise SourceConflict(
                        "Źródło zostało zmienione. Odśwież dane i spróbuj ponownie."
                    )
            elif expected_version is not None:
                raise ValidationError({"expected_version": "Wersja dotyczy wyłącznie edycji."})
        before = income_snapshot(record) if model is IncomeSource and record_id else None
        if deactivate:
            if not record.is_active:
                return record
            record.is_active = False
            record.deactivated_at = timezone.now()
        else:
            if not record.is_active:
                raise ValidationError({"detail": "Nie można edytować nieaktywnego obiektu."})
            validate_links(record, data)
            for field, value in data.items():
                setattr(record, field, value)
            if (
                model is IncomeSource
                and record.frequency == IncomeFrequency.ONE_OFF
                and record.is_regular
            ):
                raise ValidationError({"is_regular": "Źródło jednorazowe nie może być regularne."})
        if model is IncomeSource and record_id is not None:
            record.version += 1
        save_validated(record)
        if model is IncomeSource:
            write_audit(
                user=user,
                household_id=household_id,
                action="deactivated" if deactivate else "updated" if record_id else "created",
                object_type="income_source",
                object_id=record.pk,
                before=before,
                after=income_snapshot(record),
            )
        return record
