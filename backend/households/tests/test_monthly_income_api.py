from datetime import date
from uuid import uuid4

from accounts.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from households.models import (
    AuditLog,
    HouseholdMember,
    IncomeCreateIdempotency,
    IncomeFrequency,
    IncomeRecord,
    IncomeSource,
    Membership,
    Role,
)
from households.period_services import create_accounting_year, transition_accounting_month
from households.services import create_household


class MonthlyIncomeApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="monthly-income-owner")
        self.viewer = User.objects.create_user(username="monthly-income-viewer")
        self.household = create_household(user=self.owner, name="Dom").household
        Membership.objects.create(household=self.household, user=self.viewer, role=Role.VIEWER)
        self.member = HouseholdMember.objects.create(household=self.household, display_name="Arek")
        self.year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2042
        )
        self.month = self.year.months.get(month_number=1)
        self.other_month = self.year.months.get(month_number=2)
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="activate",
        )
        self.source = self.create_source(member=self.member)
        self.client = APIClient()
        self.path = (
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/"
            f"months/{self.month.pk}/incomes/"
        )

    def create_source(self, *, member=None, name="Wynagrodzenie", start_date=date(2041, 1, 1)):
        return IncomeSource.objects.create(
            household=self.household,
            member=member,
            name=name,
            category="salary",
            payer="",
            start_date=start_date,
            currency="PLN",
            frequency=IncomeFrequency.MONTHLY,
            is_regular=True,
        )

    def request(self, method, path, data=None, *, user=None, key=None):
        self.client.force_login(self.owner if user is None else user)
        headers = {"HTTP_HOST": "localhost"}
        if key is not None:
            headers["HTTP_IDEMPOTENCY_KEY"] = str(key)
        return getattr(self.client, method)(path, data, format="json", secure=True, **headers)

    def income_data(self, **overrides):
        return {
            "member_id": str(self.member.pk),
            "source_id": str(self.source.pk),
            "amount": "8000",
            "currency": "PLN",
            "receipt_date": "2041-12-31",
            **overrides,
        }

    def test_create_is_idempotent_across_close_and_keeps_snapshot(self):
        key = uuid4()
        created = self.request("post", self.path, self.income_data(), key=key)
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["amount"], "8000.00")
        self.assertEqual(created.data["recipient_snapshot"]["label"], "Arek")
        self.assertEqual(created.data["source_snapshot"]["name"], "Wynagrodzenie")
        self.source.name = "Nowa nazwa"
        self.source.save(update_fields=["name"])
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )

        replay = self.request("post", self.path, self.income_data(), key=key)

        self.assertEqual(replay.status_code, 201)
        self.assertEqual(replay.data, created.data)
        self.assertEqual(IncomeRecord.objects.count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 1)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record", action="created").count(), 1
        )

    def test_same_key_cannot_replay_under_another_month(self):
        key = uuid4()
        first = self.request("post", self.path, self.income_data(), key=key)
        other_path = self.path.replace(str(self.month.pk), str(self.other_month.pk))

        conflict = self.request("post", other_path, self.income_data(), key=key)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.data["code"], "idempotency_conflict")
        self.assertEqual(set(conflict.data), {"detail", "code"})
        self.assertEqual(IncomeRecord.objects.count(), 1)

    def test_create_rejects_non_string_decimal_and_inactive_period(self):
        key = uuid4()
        for amount in (8000, " 8000.00", "8e3", "0", "1.001"):
            with self.subTest(amount=amount):
                response = self.request("post", self.path, self.income_data(amount=amount), key=key)
                self.assertEqual(response.status_code, 400)
        inactive_path = self.path.replace(str(self.month.pk), str(self.other_month.pk))
        response = self.request("post", inactive_path, self.income_data(), key=uuid4())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "income_period_not_active")
        self.assertEqual(set(response.data), {"detail", "code"})
        self.assertEqual(IncomeRecord.objects.count(), 0)

    def test_patch_noop_version_conflict_soft_delete_and_totals(self):
        created = self.request("post", self.path, self.income_data(), key=uuid4()).data
        detail = f"{self.path}{created['id']}/"
        before_audits = AuditLog.objects.filter(object_type="income_record").count()

        no_op = self.request(
            "patch",
            detail,
            {"amount": "8000.00", "expected_version": created["version"]},
        )
        self.assertEqual(no_op.status_code, 200)
        self.assertEqual(no_op.data["version"], created["version"])
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), before_audits
        )
        changed = self.request(
            "patch",
            detail,
            {"amount": "9000", "expected_version": created["version"]},
        )
        stale = self.request(
            "patch",
            detail,
            {"amount": "10000", "expected_version": created["version"]},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.data["version"], created["version"] + 1)
        self.assertEqual(changed.data["amount"], "9000.00")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.data["code"], "income_version_conflict")
        self.assertEqual(set(stale.data), {"detail", "code"})
        totals_path = self.path.replace("incomes/", "income-totals/")
        self.assertEqual(
            self.request("get", totals_path).data,
            {"totals": [{"currency": "PLN", "amount": "9000.00"}]},
        )
        deleted = self.request(
            "delete",
            detail,
            {"expected_version": changed.data["version"]},
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNotNone(IncomeRecord.objects.get(pk=created["id"]).deleted_at)
        self.assertEqual(self.request("get", totals_path).data, {"totals": []})

    def test_viewer_can_read_but_cannot_create(self):
        response = self.request(
            "post", self.path, self.income_data(), user=self.viewer, key=uuid4()
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(IncomeRecord.objects.count(), 0)

    def test_source_options_are_recipient_and_period_scoped(self):
        self.create_source(member=None, name="Świadczenie")
        options_path = self.path.replace("incomes/", "income-source-options/")
        member_options = self.request("get", f"{options_path}?member_id={self.member.pk}")
        household_options = self.request("get", options_path)
        self.assertEqual(member_options.status_code, 200)
        self.assertEqual(member_options.data["count"], 1)
        self.assertEqual(member_options.data["results"][0]["name"], "Wynagrodzenie")
        self.assertEqual(household_options.data["count"], 1)
        self.assertEqual(household_options.data["results"][0]["name"], "Świadczenie")

    def test_unknown_fields_and_missing_idempotency_key_are_rejected(self):
        without_key = self.request("post", self.path, self.income_data())
        unknown = self.request(
            "post", self.path, {**self.income_data(), "actor_id": 1}, key=uuid4()
        )
        self.assertEqual(without_key.status_code, 400)
        self.assertEqual(unknown.status_code, 400)
        self.assertEqual(IncomeRecord.objects.count(), 0)
