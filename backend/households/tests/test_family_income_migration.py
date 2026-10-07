from datetime import date
from decimal import Decimal
from uuid import uuid4

from accounts.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from households.models import AuditLog, Company, Contract, IncomeSource


class FamilyIncomeMigrationTests(TransactionTestCase):
    old_target = ("households", "0003_relationtype_householdmember_auditlog_incomesource_and_more")

    def restore_current_schema(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_legacy_sources_and_audit_survive_without_inferred_contracts(self):
        owner = User.objects.create_user(username="legacy-owner")
        executor = MigrationExecutor(connection)
        executor.migrate([self.old_target])
        self.addCleanup(self.restore_current_schema)
        old_apps = executor.loader.project_state([self.old_target]).apps
        Household = old_apps.get_model("households", "Household")
        Membership = old_apps.get_model("households", "Membership")
        HouseholdMember = old_apps.get_model("households", "HouseholdMember")
        OldSource = old_apps.get_model("households", "IncomeSource")
        OldAudit = old_apps.get_model("households", "AuditLog")

        household = Household.objects.create(name="Dom przed migracją", currency="PLN")
        Membership.objects.create(household=household, user_id=owner.pk, role="owner")
        member = HouseholdMember.objects.create(household=household, display_name="Osoba")
        salary_id = uuid4()
        archived_id = uuid4()
        salary = OldSource.objects.create(
            id=salary_id,
            household=household,
            member=member,
            name="Wynagrodzenie",
            category="salary",
            payer="Stara firma",
            start_date=date(2025, 1, 1),
            end_date=None,
            default_monthly_amount=Decimal("1234.56"),
            currency="PLN",
            frequency="monthly",
            is_regular=True,
            description="Historyczny opis",
        )
        OldSource.objects.create(
            id=archived_id,
            household=household,
            name="Najem",
            category="rent",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 12, 31),
            default_monthly_amount=Decimal("99.00"),
            currency="EUR",
            frequency="monthly",
            is_regular=True,
            is_active=False,
            deactivated_at=timezone.now(),
        )
        audit_id = uuid4()
        OldAudit.objects.create(
            id=audit_id,
            household=household,
            actor_id=owner.pk,
            action="created",
            object_type="income_source",
            object_id=salary_id,
            before=None,
            after={"name": salary.name, "default_monthly_amount": "1234.56"},
        )

        self.restore_current_schema()

        self.assertCountEqual(
            IncomeSource.objects.values_list("pk", flat=True), [salary_id, archived_id]
        )
        migrated = IncomeSource.objects.get(pk=salary_id)
        self.assertEqual(migrated.household_id, household.pk)
        self.assertEqual(migrated.member_id, member.pk)
        self.assertEqual(migrated.kind, "other")
        self.assertEqual(migrated.version, 1)
        self.assertEqual(migrated.default_monthly_amount, Decimal("1234.56"))
        self.assertEqual(migrated.start_date, date(2025, 1, 1))
        self.assertEqual(migrated.currency, "PLN")
        self.assertEqual(migrated.description, "Historyczny opis")
        archived = IncomeSource.objects.get(pk=archived_id)
        self.assertFalse(archived.is_active)
        self.assertIsNotNone(archived.deactivated_at)
        self.assertEqual(archived.end_date, date(2024, 12, 31))
        self.assertEqual(archived.default_monthly_amount, Decimal("99.00"))
        self.assertEqual(archived.kind, "other")
        self.assertEqual(
            AuditLog.objects.get(pk=audit_id).after["default_monthly_amount"], "1234.56"
        )
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertFalse(Company.objects.exists())
        self.assertFalse(Contract.objects.exists())

        client = APIClient()
        client.force_login(owner)
        response = client.get(
            f"/api/households/{household.pk}/income-sources/", HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual({row["kind"] for row in response.data["results"]}, {"other"})
