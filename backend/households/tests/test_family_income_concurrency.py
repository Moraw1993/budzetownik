from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from threading import Barrier, local
from unittest.mock import patch

from accounts.models import User
from django.db import connections
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError

from households import family_income_services
from households.exceptions import SourceConflict
from households.family_income_services import write_company, write_contract
from households.models import (
    AuditLog,
    Company,
    Contract,
    HouseholdMember,
    IncomeKind,
    IncomeSource,
)
from households.record_services import write_record
from households.services import create_household


class FamilyIncomeConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="parallel-owner")
        self.household = create_household(user=self.owner, name="Dom").household
        self.member = HouseholdMember.objects.create(household=self.household, display_name="Osoba")
        self.company = Company.objects.create(household=self.household, name="Firma")
        self.contract_data = {
            "member_id": self.member.pk,
            "company_id": self.company.pk,
            "name": "Umowa",
            "contract_type": "employment",
            "position": "Specjalista",
            "gross_amount": Decimal("100.00"),
            "gross_basis": "monthly",
            "currency": "PLN",
            "start_date": date(2026, 1, 1),
        }

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

    def test_edit_and_conversion_cannot_overwrite_each_other(self):
        source = IncomeSource.objects.create(
            household=self.household,
            name="Dawne źródło",
            category="salary",
            start_date=date(2026, 1, 1),
            default_monthly_amount=Decimal("100.00"),
            currency="PLN",
            frequency="monthly",
        )

        def edit():
            try:
                write_record(
                    user=self.owner,
                    household_id=self.household.pk,
                    model=IncomeSource,
                    record_id=source.pk,
                    data={"name": "Zmienione", "expected_version": source.version},
                )
                return "edited"
            except SourceConflict:
                return "conflict"

        def convert():
            try:
                write_contract(
                    user=self.owner,
                    household_id=self.household.pk,
                    source_id=source.pk,
                    data={**self.contract_data, "expected_version": 1},
                    conversion=True,
                )
                return "converted"
            except SourceConflict:
                return "conflict"

        outcomes = self.run_parallel(edit, convert)
        self.assertEqual(outcomes.count("conflict"), 1)
        self.assertEqual(IncomeSource.objects.get(pk=source.pk).version, 2)
        self.assertEqual(AuditLog.objects.filter(object_id=source.pk).count(), 1)
        source.refresh_from_db()
        self.assertEqual(
            Contract.objects.filter(source=source).exists(), source.kind == IncomeKind.CONTRACT
        )
        if source.kind == IncomeKind.OTHER:
            self.assertEqual(source.name, "Zmienione")
            self.assertEqual(source.default_monthly_amount, Decimal("100.00"))
        else:
            self.assertIsNone(source.default_monthly_amount)

    def test_archival_and_new_contract_use_same_household_lock(self):
        operation = local()
        lock_order = []
        original_locked_access = family_income_services.locked_access

        @contextmanager
        def observe_locked_access(**kwargs):
            with original_locked_access(**kwargs) as membership:
                lock_order.append(operation.name)
                yield membership

        def archive():
            operation.name = "archive"
            write_company(
                user=self.owner,
                household_id=self.household.pk,
                company_id=self.company.pk,
                data={},
                archive=True,
            )
            return "archived"

        def create():
            operation.name = "create"
            try:
                write_contract(
                    user=self.owner,
                    household_id=self.household.pk,
                    data=self.contract_data,
                )
                return "created"
            except ValidationError:
                return "rejected"

        with patch("households.family_income_services.locked_access", new=observe_locked_access):
            outcomes = self.run_parallel(archive, create)

        self.assertIn("archived", outcomes)
        self.assertIn(outcomes[1], {"created", "rejected"})
        self.assertCountEqual(lock_order, ["archive", "create"])
        expected_create_result = "rejected" if lock_order[0] == "archive" else "created"
        self.assertEqual(outcomes[1], expected_create_result)
        self.company.refresh_from_db()
        self.assertFalse(self.company.is_active)
        self.assertEqual(Contract.objects.count(), int(outcomes[1] == "created"))
        if outcomes[1] == "created":
            contract = Contract.objects.get()
            self.assertEqual(contract.company_id, self.company.pk)
