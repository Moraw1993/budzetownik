from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from accounts.models import User
from django.db import connections
from django.test import TransactionTestCase

from households.exceptions import AccountingPeriodConflict
from households.models import AccountingMonth, AccountingMonthState, AccountingYear, AuditLog
from households.period_services import create_accounting_year, transition_accounting_month
from households.services import create_household


class AccountingPeriodConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="period-concurrent-owner")
        self.household = create_household(user=self.owner, name="Dom").household

    def run_parallel(self, first, second):
        barrier = Barrier(2)

        def execute(operation):
            try:
                barrier.wait(timeout=10)
                return operation()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(execute, operation) for operation in (first, second)]
            return [future.result(timeout=20) for future in futures]

    def test_simultaneous_duplicate_year_creation_keeps_one_complete_year(self):
        def create():
            try:
                year = create_accounting_year(
                    user=self.owner,
                    household_id=self.household.pk,
                    calendar_year=2040,
                )
                return "created", year.pk
            except AccountingPeriodConflict:
                return "conflict", None

        outcomes = self.run_parallel(create, create)

        self.assertEqual([result[0] for result in outcomes].count("created"), 1)
        self.assertEqual([result[0] for result in outcomes].count("conflict"), 1)
        year = AccountingYear.objects.get(household=self.household, calendar_year=2040)
        months = AccountingMonth.objects.filter(accounting_year=year)
        self.assertEqual(months.count(), 12)
        self.assertEqual(set(months.values_list("month_number", flat=True)), set(range(1, 13)))
        self.assertEqual(
            set(months.values_list("state", flat=True)), {AccountingMonthState.INACTIVE}
        )
        self.assertEqual(
            AuditLog.objects.filter(object_type="accounting_year", object_id=year.pk).count(),
            1,
        )

    def test_simultaneous_activation_is_idempotent_and_audited_once(self):
        year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2041
        )
        month = year.months.get(month_number=1)

        def activate():
            result = transition_accounting_month(
                user=self.owner,
                household_id=self.household.pk,
                year_id=year.pk,
                month_id=month.pk,
                operation="activate",
            )
            return result.state

        outcomes = self.run_parallel(activate, activate)

        self.assertEqual(outcomes, [AccountingMonthState.ACTIVE, AccountingMonthState.ACTIVE])
        self.assertEqual(
            AuditLog.objects.filter(
                object_type="accounting_month", object_id=month.pk, action="activated"
            ).count(),
            1,
        )
