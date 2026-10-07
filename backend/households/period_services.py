from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .access import Capability, locked_access
from .exceptions import AccountingPeriodConflict
from .models import AccountingMonth, AccountingMonthState, AccountingYear
from .record_services import write_audit

STATE_TRANSITIONS = {
    "activate": (AccountingMonthState.INACTIVE, AccountingMonthState.ACTIVE, "activated"),
    "close": (AccountingMonthState.ACTIVE, AccountingMonthState.CLOSED, "closed"),
    "reopen": (AccountingMonthState.CLOSED, AccountingMonthState.ACTIVE, "reopened"),
}


def create_accounting_year(*, user, household_id, calendar_year):
    try:
        with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
            if AccountingYear.objects.filter(
                household_id=household_id, calendar_year=calendar_year
            ).exists():
                raise AccountingPeriodConflict("Ten rok rozliczeniowy już istnieje.")

            year = AccountingYear.objects.create(
                household_id=household_id, calendar_year=calendar_year
            )
            months = AccountingMonth.objects.bulk_create(
                [
                    AccountingMonth(accounting_year=year, month_number=month_number)
                    for month_number in range(1, 13)
                ]
            )
            write_audit(
                user=user,
                household_id=household_id,
                action="created",
                object_type="accounting_year",
                object_id=year.pk,
                before=None,
                after={
                    "calendar_year": calendar_year,
                    "month_ids": [str(month.pk) for month in months],
                    "initial_month_state": AccountingMonthState.INACTIVE,
                },
            )
            return year
    except IntegrityError as exc:
        if AccountingYear.objects.filter(
            household_id=household_id, calendar_year=calendar_year
        ).exists():
            raise AccountingPeriodConflict("Ten rok rozliczeniowy już istnieje.") from exc
        raise


def transition_accounting_month(*, user, household_id, year_id, month_id, operation):
    try:
        expected_state, target_state, action = STATE_TRANSITIONS[operation]
    except KeyError as exc:
        raise ValueError(f"Unsupported accounting month operation: {operation}") from exc

    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        year = get_object_or_404(
            AccountingYear.objects.select_for_update(),
            household_id=household_id,
            pk=year_id,
        )
        month = get_object_or_404(
            AccountingMonth.objects.select_for_update(),
            accounting_year_id=year.pk,
            pk=month_id,
        )
        if month.state == target_state:
            return month
        if month.state != expected_state:
            raise AccountingPeriodConflict()

        before = {"state": month.state}
        occurred_at = timezone.now()
        month.state = target_state
        if operation in {"activate", "reopen"}:
            month.activated_at = occurred_at
            update_fields = ["state", "activated_at", "updated_at"]
        else:
            month.closed_at = occurred_at
            update_fields = ["state", "closed_at", "updated_at"]
        month.save(update_fields=update_fields)
        write_audit(
            user=user,
            household_id=household_id,
            action=action,
            object_type="accounting_month",
            object_id=month.pk,
            before=before,
            after={"state": month.state},
        )
        return month
