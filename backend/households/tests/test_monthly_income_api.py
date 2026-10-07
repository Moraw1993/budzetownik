from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from accounts.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from households.family_income_services import write_company, write_contract
from households.income_services import create_income_record
from households.models import (
    AuditLog,
    Company,
    Contract,
    ContractType,
    GrossBasis,
    HouseholdMember,
    IncomeCreateIdempotency,
    IncomeFrequency,
    IncomeKind,
    IncomeRecord,
    IncomeSource,
    Membership,
    Role,
)
from households.period_services import create_accounting_year, transition_accounting_month
from households.record_services import write_record
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

    def create_source(
        self,
        *,
        member=None,
        name="Wynagrodzenie",
        start_date=date(2041, 1, 1),
        end_date=None,
    ):
        return IncomeSource.objects.create(
            household=self.household,
            member=member,
            name=name,
            category="salary",
            payer="",
            start_date=start_date,
            end_date=end_date,
            currency="PLN",
            frequency=IncomeFrequency.MONTHLY,
            is_regular=True,
        )

    def create_contract_source(self):
        company = Company.objects.create(
            household=self.household,
            name="Archived employer",
            is_active=False,
            deactivated_at=timezone.now(),
        )
        source = IncomeSource.objects.create(
            household=self.household,
            member=self.member,
            name="Employment contract",
            kind=IncomeKind.CONTRACT,
            start_date=date(2041, 1, 1),
            currency="PLN",
            frequency="",
            is_regular=None,
        )
        Contract.objects.create(
            source=source,
            company=company,
            contract_type=ContractType.EMPLOYMENT,
            gross_amount="12345.67",
            gross_basis=GrossBasis.MONTHLY,
        )
        return source, company

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
        listed = self.request("get", self.path, user=self.viewer)
        response = self.request(
            "post", self.path, self.income_data(), user=self.viewer, key=uuid4()
        )
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(IncomeRecord.objects.count(), 0)

    def test_owner_admin_member_viewer_read_and_write_capabilities(self):
        admin = User.objects.create_user(username="monthly-income-admin")
        member = User.objects.create_user(username="monthly-income-member")
        Membership.objects.create(household=self.household, user=admin, role=Role.ADMINISTRATOR)
        Membership.objects.create(household=self.household, user=member, role=Role.MEMBER)

        for user, can_write in (
            (self.owner, True),
            (admin, True),
            (member, False),
            (self.viewer, False),
        ):
            with self.subTest(role=Membership.objects.get(user=user).role):
                record = self.request("post", self.path, self.income_data(), key=uuid4())
                detail = f"{self.path}{record.data['id']}/"
                listed = self.request("get", self.path, user=user)
                created = self.request(
                    "post", self.path, self.income_data(), user=user, key=uuid4()
                )
                retrieved = self.request("get", detail, user=user)
                updated = self.request(
                    "patch",
                    detail,
                    {"amount": "9000", "expected_version": 1},
                    user=user,
                )
                deleted = self.request(
                    "delete",
                    detail,
                    {"expected_version": 2 if can_write else 1},
                    user=user,
                )
                self.assertEqual(listed.status_code, 200)
                self.assertEqual(retrieved.status_code, 200)
                self.assertEqual(created.status_code, 201 if can_write else 403)
                self.assertEqual(updated.status_code, 200 if can_write else 403)
                self.assertEqual(deleted.status_code, 204 if can_write else 403)

    def test_session_writes_require_csrf_and_accept_a_valid_token(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        headers = {"HTTP_HOST": "localhost"}
        missing_token = client.post(
            self.path,
            {**self.income_data(), "amount": "8000"},
            format="json",
            secure=True,
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
            **headers,
        )
        self.assertEqual(missing_token.status_code, 403)

        token = "a" * 32
        client.cookies["csrftoken"] = token
        accepted = client.post(
            self.path,
            self.income_data(),
            format="json",
            secure=True,
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
            HTTP_X_CSRFTOKEN=token,
            HTTP_REFERER="https://localhost/",
            **headers,
        )
        self.assertEqual(accepted.status_code, 201, accepted.data)

    def test_foreign_household_year_month_member_source_and_income_ids_are_hidden(self):
        foreign_owner = User.objects.create_user(username="other-income-owner")
        foreign_household = create_household(user=foreign_owner, name="Inny dom").household
        foreign_member = HouseholdMember.objects.create(
            household=foreign_household, display_name="Inna osoba"
        )
        foreign_year = create_accounting_year(
            user=foreign_owner, household_id=foreign_household.pk, calendar_year=2043
        )
        foreign_month = foreign_year.months.get(month_number=1)
        transition_accounting_month(
            user=foreign_owner,
            household_id=foreign_household.pk,
            year_id=foreign_year.pk,
            month_id=foreign_month.pk,
            operation="activate",
        )
        foreign_source = IncomeSource.objects.create(
            household=foreign_household,
            member=foreign_member,
            name="Obce źródło",
            category="salary",
            payer="",
            start_date=date(2040, 1, 1),
            currency="PLN",
            frequency=IncomeFrequency.MONTHLY,
            is_regular=True,
        )
        foreign_income = create_income_record(
            user=foreign_owner,
            household_id=foreign_household.pk,
            year_id=foreign_year.pk,
            month_id=foreign_month.pk,
            data={
                "member_id": foreign_member.pk,
                "source_id": foreign_source.pk,
                "amount": Decimal("8000.00"),
                "currency": "PLN",
                "receipt_date": date(2043, 1, 15),
            },
            idempotency_key=uuid4(),
        )
        foreign_income_id = foreign_income.body["id"]
        foreign_path = (
            f"/api/households/{foreign_household.pk}/accounting-years/{foreign_year.pk}/"
            f"months/{foreign_month.pk}/incomes/"
        )

        foreign_household_read = self.request("get", foreign_path)
        foreign_year_read = self.request(
            "get", self.path.replace(str(self.year.pk), str(foreign_year.pk))
        )
        foreign_month_read = self.request(
            "get", self.path.replace(str(self.month.pk), str(foreign_month.pk))
        )
        foreign_source_write = self.request(
            "post",
            self.path,
            self.income_data(source_id=str(foreign_source.pk)),
            key=uuid4(),
        )
        foreign_member_write = self.request(
            "post",
            self.path,
            self.income_data(member_id=str(foreign_member.pk)),
            key=uuid4(),
        )
        foreign_income_read = self.request("get", f"{self.path}{foreign_income_id}/")
        foreign_income_patch = self.request(
            "patch",
            f"{self.path}{foreign_income_id}/",
            {"amount": "9000", "expected_version": 1},
        )
        foreign_income_delete = self.request(
            "delete", f"{self.path}{foreign_income_id}/", {"expected_version": 1}
        )

        for response in (
            foreign_household_read,
            foreign_year_read,
            foreign_month_read,
            foreign_source_write,
            foreign_member_write,
            foreign_income_read,
            foreign_income_patch,
            foreign_income_delete,
        ):
            with self.subTest(response=response.status_code, data=response.data):
                self.assertEqual(response.status_code, 404)

    def test_income_audit_and_idempotency_failures_roll_back_the_whole_create(self):
        with (
            patch(
                "households.income_services.IncomeRecord.objects.create",
                side_effect=IntegrityError("injected income persistence failure"),
            ),
            self.assertRaises(IntegrityError),
        ):
            self.request("post", self.path, self.income_data(), key=uuid4())
        self.assertEqual(IncomeRecord.objects.count(), 0)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 0)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), 0)

        with (
            patch("households.income_services.write_audit", side_effect=RuntimeError("audit")),
            self.assertRaisesMessage(RuntimeError, "audit"),
        ):
            self.request("post", self.path, self.income_data(), key=uuid4())
        self.assertEqual(IncomeRecord.objects.count(), 0)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 0)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), 0)

        with (
            patch(
                "households.income_services.IncomeCreateIdempotency.objects.create",
                side_effect=IntegrityError("injected uniqueness conflict"),
            ),
            self.assertRaises(IntegrityError),
        ):
            self.request("post", self.path, self.income_data(), key=uuid4())
        self.assertEqual(IncomeRecord.objects.count(), 0)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 0)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), 0)

    def test_update_and_delete_audit_failures_roll_back_income_and_versions(self):
        created = self.request("post", self.path, self.income_data(), key=uuid4())
        detail = f"{self.path}{created.data['id']}/"
        audit_count = AuditLog.objects.filter(object_type="income_record").count()

        with (
            patch("households.income_services.write_audit", side_effect=RuntimeError("audit")),
            self.assertRaisesMessage(RuntimeError, "audit"),
        ):
            self.request("patch", detail, {"amount": "9000", "expected_version": 1})
        record = IncomeRecord.objects.get(pk=created.data["id"])
        self.assertEqual(record.amount, Decimal("8000.00"))
        self.assertEqual(record.version, 1)
        self.assertIsNone(record.deleted_at)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), audit_count)

        with (
            patch("households.income_services.write_audit", side_effect=RuntimeError("audit")),
            self.assertRaisesMessage(RuntimeError, "audit"),
        ):
            self.request("delete", detail, {"expected_version": 1})
        record.refresh_from_db()
        self.assertEqual(record.version, 1)
        self.assertIsNone(record.deleted_at)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), audit_count)

    def test_leap_day_source_and_receipt_are_valid_for_february_period(self):
        leap_year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2044
        )
        february = leap_year.months.get(month_number=2)
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=leap_year.pk,
            month_id=february.pk,
            operation="activate",
        )
        leap_source = self.create_source(
            member=self.member,
            name="Dochód od końca lutego",
            start_date=date(2044, 2, 29),
            end_date=date(2044, 2, 29),
        )
        february_path = (
            f"/api/households/{self.household.pk}/accounting-years/{leap_year.pk}/"
            f"months/{february.pk}/incomes/"
        )
        options = self.request(
            "get",
            february_path.replace("incomes/", "income-source-options/")
            + f"?member_id={self.member.pk}",
        )
        created = self.request(
            "post",
            february_path,
            self.income_data(
                source_id=str(leap_source.pk),
                amount="27.45",
                receipt_date="2044-02-29",
            ),
            key=uuid4(),
        )

        self.assertEqual(options.status_code, 200)
        self.assertIn(str(leap_source.pk), {item["id"] for item in options.data["results"]})
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["receipt_date"], "2044-02-29")

    def test_maximum_income_amounts_and_currency_totals_are_exact(self):
        maximum = "9999999999999999.99"
        first = self.request("post", self.path, self.income_data(amount=maximum), key=uuid4())
        second = self.request(
            "post", self.path, self.income_data(amount=maximum, currency="EUR"), key=uuid4()
        )
        third = self.request("post", self.path, self.income_data(amount=maximum), key=uuid4())
        over_limit = self.request(
            "post",
            self.path,
            self.income_data(amount="10000000000000000.00"),
            key=uuid4(),
        )
        totals = self.request("get", self.path.replace("incomes/", "income-totals/"))

        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)
        self.assertEqual(third.status_code, 201, third.data)
        self.assertEqual(over_limit.status_code, 400)
        self.assertEqual(
            totals.data,
            {
                "totals": [
                    {"currency": "EUR", "amount": maximum},
                    {"currency": "PLN", "amount": "19999999999999999.98"},
                ]
            },
        )

    def test_year_totals_use_assigned_month_and_exclude_soft_deleted_records(self):
        february = self.year.months.get(month_number=2)
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=february.pk,
            operation="activate",
        )
        assigned_to_january = self.request(
            "post",
            self.path,
            self.income_data(amount="125.25", receipt_date="2043-12-31"),
            key=uuid4(),
        )
        assigned_to_february = self.request(
            "post",
            self.path.replace(str(self.month.pk), str(february.pk)),
            self.income_data(amount="75.50", receipt_date="2044-03-01"),
            key=uuid4(),
        )
        deleted = self.request(
            "delete",
            f"{self.path}{assigned_to_january.data['id']}/",
            {"expected_version": 1},
        )
        totals = self.request(
            "get",
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/income-totals/",
        )

        self.assertEqual(assigned_to_january.status_code, 201, assigned_to_january.data)
        self.assertEqual(assigned_to_february.status_code, 201, assigned_to_february.data)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(totals.data, {"totals": [{"currency": "PLN", "amount": "75.50"}]})

    def test_missing_or_deleted_income_is_hidden_before_period_state_conflicts(self):
        missing_id = uuid4()
        inactive_path = self.path.replace(str(self.month.pk), str(self.other_month.pk))
        for path in (self.path, inactive_path):
            with self.subTest(state_path=path):
                self.assert_missing_income_operations(path, missing_id)

        created = self.request("post", self.path, self.income_data(), key=uuid4())
        deleted = self.request(
            "delete",
            f"{self.path}{created.data['id']}/",
            {"expected_version": 1},
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(deleted.status_code, 204)
        self.assert_missing_income_operations(self.path, uuid4())
        self.assert_missing_income_operations(self.path, created.data["id"])

        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )
        self.assert_missing_income_operations(self.path, missing_id)
        self.assert_missing_income_operations(self.path, created.data["id"])

    def assert_missing_income_operations(self, path, income_id):
        detail = f"{path}{income_id}/"
        responses = (
            self.request("get", detail),
            self.request("patch", detail, {"amount": "9000", "expected_version": 1}),
            self.request("delete", detail, {"expected_version": 1}),
        )
        for response in responses:
            self.assertEqual(response.status_code, 404, response.data)

    def test_empty_patch_and_non_integer_expected_versions_are_rejected(self):
        created = self.request("post", self.path, self.income_data(), key=uuid4())
        detail = f"{self.path}{created.data['id']}/"
        empty_patch = self.request("patch", detail, {"expected_version": 1})
        invalid_versions = [
            self.request("patch", detail, {"amount": "9000", "expected_version": True}),
            self.request("patch", detail, {"amount": "9000", "expected_version": "1"}),
            self.request("patch", detail, {"amount": "9000", "expected_version": 1.0}),
        ]

        self.assertEqual(empty_patch.status_code, 400)
        self.assertTrue(all(response.status_code == 400 for response in invalid_versions))
        self.assertEqual(IncomeRecord.objects.get(pk=created.data["id"]).version, 1)

    def test_patch_relationship_matrix_preserves_and_refreshes_snapshots_correctly(self):
        created = self.request("post", self.path, self.income_data(), key=uuid4())
        record = IncomeRecord.objects.get(pk=created.data["id"])
        original_recipient = record.recipient_snapshot
        original_source = record.source_snapshot
        same_relationships = self.request(
            "patch",
            f"{self.path}{record.pk}/",
            {
                "member_id": str(self.member.pk),
                "source_id": str(self.source.pk),
                "expected_version": 1,
            },
        )
        self.assertEqual(same_relationships.status_code, 200)
        self.assertEqual(same_relationships.data["version"], 1)

        second_source = self.create_source(member=self.member, name="Premia")
        source_only = self.request(
            "patch",
            f"{self.path}{record.pk}/",
            {"source_id": str(second_source.pk), "expected_version": 1},
        )
        self.assertEqual(source_only.status_code, 200, source_only.data)
        self.assertEqual(source_only.data["recipient_snapshot"], original_recipient)
        self.assertEqual(source_only.data["source_snapshot"]["name"], "Premia")

        second_member = HouseholdMember.objects.create(
            household=self.household, display_name="Dominika"
        )
        second_member_source = self.create_source(member=second_member, name="Umowa Dominiki")
        both_changed = self.request(
            "patch",
            f"{self.path}{record.pk}/",
            {
                "member_id": str(second_member.pk),
                "source_id": str(second_member_source.pk),
                "expected_version": 2,
            },
        )
        self.assertEqual(both_changed.status_code, 200, both_changed.data)
        self.assertEqual(both_changed.data["recipient_snapshot"]["label"], "Dominika")
        self.assertEqual(both_changed.data["source_snapshot"]["name"], "Umowa Dominiki")
        relationship_audit = (
            AuditLog.objects.filter(
                object_type="income_record",
                object_id=record.pk,
                action="updated",
            )
            .order_by("-occurred_at", "-id")
            .first()
        )
        self.assertEqual(relationship_audit.before["recipient_snapshot"], original_recipient)
        self.assertEqual(relationship_audit.before["source_snapshot"]["name"], "Premia")
        self.assertEqual(relationship_audit.before["version"], 2)
        self.assertEqual(relationship_audit.after["recipient_snapshot"]["label"], "Dominika")
        self.assertEqual(relationship_audit.after["source_snapshot"]["name"], "Umowa Dominiki")
        self.assertEqual(relationship_audit.after["version"], 3)

        member_only = self.request(
            "patch",
            f"{self.path}{record.pk}/",
            {"member_id": str(self.member.pk), "expected_version": 3},
        )
        self.assertEqual(member_only.status_code, 400)
        record.refresh_from_db()
        self.assertEqual(record.member_id, second_member.pk)
        self.assertEqual(record.source_snapshot["name"], "Umowa Dominiki")
        self.assertNotEqual(record.source_snapshot, original_source)

        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=IncomeSource,
            record_id=second_member_source.pk,
            data={},
            deactivate=True,
        )
        archived_source_history = self.request(
            "patch",
            f"{self.path}{record.pk}/",
            {"amount": "8500", "expected_version": 3},
        )
        self.assertEqual(archived_source_history.status_code, 200)
        self.assertEqual(archived_source_history.data["source_snapshot"]["name"], "Umowa Dominiki")

    def test_create_retry_after_edit_delete_source_archive_and_close_is_unchanged(self):
        key = uuid4()
        created = self.request("post", self.path, self.income_data(), key=key)
        edited = self.request(
            "patch",
            f"{self.path}{created.data['id']}/",
            {"amount": "9000", "expected_version": 1},
        )
        edited_audit_count = AuditLog.objects.filter(object_type="income_record").count()
        replay_after_edit = self.request("post", self.path, self.income_data(), key=key)
        self.assertEqual(replay_after_edit.status_code, 201)
        self.assertEqual(replay_after_edit.data, created.data)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), edited_audit_count
        )
        deleted = self.request(
            "delete",
            f"{self.path}{created.data['id']}/",
            {"expected_version": 2},
        )
        deleted_audit_count = AuditLog.objects.filter(object_type="income_record").count()
        replay_after_delete = self.request("post", self.path, self.income_data(), key=key)
        self.assertEqual(replay_after_delete.status_code, 201)
        self.assertEqual(replay_after_delete.data, created.data)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), deleted_audit_count
        )
        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=IncomeSource,
            record_id=self.source.pk,
            data={},
            deactivate=True,
        )
        archived_audit_count = AuditLog.objects.filter(object_type="income_record").count()
        replay_after_archive = self.request("post", self.path, self.income_data(), key=key)
        self.assertEqual(replay_after_archive.status_code, 201)
        self.assertEqual(replay_after_archive.data, created.data)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), archived_audit_count
        )
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )
        before_audits = AuditLog.objects.filter(object_type="income_record").count()

        replay = self.request("post", self.path, self.income_data(), key=key)

        self.assertEqual(created.status_code, 201)
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(replay.status_code, 201)
        self.assertEqual(replay.data, created.data)
        self.assertEqual(IncomeRecord.objects.count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 1)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), before_audits
        )

    def test_create_retry_after_access_revocation_is_denied_without_changes(self):
        admin = User.objects.create_user(username="revoked-income-admin")
        membership = Membership.objects.create(
            household=self.household, user=admin, role=Role.ADMINISTRATOR
        )
        key = uuid4()
        created = self.request("post", self.path, self.income_data(), user=admin, key=key)
        before_audits = AuditLog.objects.filter(object_type="income_record").count()
        membership.role = Role.VIEWER
        membership.save(update_fields=["role"])

        downgraded_replay = self.request("post", self.path, self.income_data(), user=admin, key=key)
        self.assertEqual(downgraded_replay.status_code, 403)
        self.assertEqual(IncomeRecord.objects.count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 1)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), before_audits
        )

        membership.delete()

        replay = self.request("post", self.path, self.income_data(), user=admin, key=key)

        self.assertEqual(created.status_code, 201)
        self.assertEqual(replay.status_code, 404)
        self.assertEqual(IncomeRecord.objects.count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 1)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), before_audits
        )

    def test_contract_company_and_income_snapshots_survive_company_and_contract_archival(self):
        company = Company.objects.create(household=self.household, name="Pracodawca")
        contract_source = IncomeSource.objects.create(
            household=self.household,
            member=self.member,
            name="Umowa o pracę",
            kind=IncomeKind.CONTRACT,
            start_date=date(2041, 1, 1),
            currency="PLN",
            frequency="",
            is_regular=None,
        )
        Contract.objects.create(
            source=contract_source,
            company=company,
            contract_type=ContractType.EMPLOYMENT,
            gross_amount="12345.67",
            gross_basis=GrossBasis.MONTHLY,
        )
        created = self.request(
            "post",
            self.path,
            self.income_data(source_id=str(contract_source.pk), amount="1234.56"),
            key=uuid4(),
        )
        original_recipient_snapshot = {
            "kind": "member",
            "id": str(self.member.pk),
            "label": "Arek",
        }
        original_source_snapshot = {
            "id": str(contract_source.pk),
            "name": "Umowa o pracę",
            "kind": IncomeKind.CONTRACT,
            "version": 1,
            "contract": {
                "company_id": str(company.pk),
                "company_name": "Pracodawca",
                "contract_type": ContractType.EMPLOYMENT,
                "other_type_name": None,
            },
        }
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["recipient_snapshot"], original_recipient_snapshot)
        self.assertEqual(created.data["source_snapshot"], original_source_snapshot)

        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=HouseholdMember,
            record_id=self.member.pk,
            data={"display_name": "Arek po zmianie"},
        )
        write_company(
            user=self.owner,
            household_id=self.household.pk,
            company_id=company.pk,
            data={"name": "Pracodawca po zmianie"},
        )
        write_contract(
            user=self.owner,
            household_id=self.household.pk,
            source_id=contract_source.pk,
            data={
                "expected_version": 1,
                "name": "Umowa zmieniona",
                "contract_type": ContractType.OTHER,
                "other_type_name": "Umowa partnerska",
            },
        )
        changed_source_snapshot = {
            "id": str(contract_source.pk),
            "name": "Umowa zmieniona",
            "kind": IncomeKind.CONTRACT,
            "version": 2,
            "contract": {
                "company_id": str(company.pk),
                "company_name": "Pracodawca po zmianie",
                "contract_type": ContractType.OTHER,
                "other_type_name": "Umowa partnerska",
            },
        }
        changed = self.request(
            "post",
            self.path,
            self.income_data(source_id=str(contract_source.pk), amount="2345.67"),
            key=uuid4(),
        )
        self.assertEqual(changed.status_code, 201, changed.data)
        self.assertEqual(changed.data["source_snapshot"], changed_source_snapshot)

        write_company(
            user=self.owner,
            household_id=self.household.pk,
            company_id=company.pk,
            data={},
            archive=True,
        )
        write_contract(
            user=self.owner,
            household_id=self.household.pk,
            source_id=contract_source.pk,
            data={},
            archive=True,
        )
        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=HouseholdMember,
            record_id=self.member.pk,
            data={},
            deactivate=True,
        )
        original_detail = f"{self.path}{created.data['id']}/"
        changed_detail = f"{self.path}{changed.data['id']}/"
        original_get = self.request("get", original_detail)
        changed_get = self.request("get", changed_detail)
        original_patch = self.request(
            "patch", original_detail, {"amount": "1300.00", "expected_version": 1}
        )
        changed_patch = self.request(
            "patch", changed_detail, {"amount": "2400.00", "expected_version": 1}
        )
        original_audit = AuditLog.objects.get(
            object_type="income_record", object_id=created.data["id"], action="updated"
        )
        changed_audit = AuditLog.objects.get(
            object_type="income_record", object_id=changed.data["id"], action="updated"
        )

        self.assertEqual(original_get.status_code, 200)
        self.assertEqual(changed_get.status_code, 200)
        self.assertEqual(original_get.data["recipient_snapshot"], original_recipient_snapshot)
        self.assertEqual(original_get.data["source_snapshot"], original_source_snapshot)
        self.assertEqual(changed_get.data["source_snapshot"], changed_source_snapshot)
        self.assertEqual(original_patch.status_code, 200, original_patch.data)
        self.assertEqual(changed_patch.status_code, 200, changed_patch.data)
        self.assertEqual(original_patch.data["recipient_snapshot"], original_recipient_snapshot)
        self.assertEqual(original_patch.data["source_snapshot"], original_source_snapshot)
        self.assertEqual(changed_patch.data["source_snapshot"], changed_source_snapshot)
        self.assertEqual(original_audit.before["recipient_snapshot"], original_recipient_snapshot)
        self.assertEqual(original_audit.before["source_snapshot"], original_source_snapshot)
        self.assertEqual(original_audit.after["recipient_snapshot"], original_recipient_snapshot)
        self.assertEqual(original_audit.after["source_snapshot"], original_source_snapshot)
        self.assertEqual(original_audit.before["amount"], "1234.56")
        self.assertEqual(original_audit.after["amount"], "1300.00")
        self.assertEqual(changed_audit.before["source_snapshot"], changed_source_snapshot)
        self.assertEqual(changed_audit.after["source_snapshot"], changed_source_snapshot)
        self.assertEqual(changed_audit.before["amount"], "2345.67")
        self.assertEqual(changed_audit.after["amount"], "2400.00")
        self.assertNotIn("gross_amount", original_patch.data["source_snapshot"]["contract"])
        self.assertNotIn("gross_basis", changed_patch.data["source_snapshot"]["contract"])
        self.assertFalse(Company.objects.get(pk=company.pk).is_active)
        self.assertFalse(IncomeSource.objects.get(pk=contract_source.pk).is_active)
        self.assertFalse(HouseholdMember.objects.get(pk=self.member.pk).is_active)

    def test_source_options_render_contract_and_other_with_whitelisted_data(self):
        contract_source, company = self.create_contract_source()
        other_source = self.source
        options_path = self.path.replace("incomes/", "income-source-options/")

        response = self.request("get", f"{options_path}?member_id={self.member.pk}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.data["count"], 2)
        options = {item["id"]: item for item in response.data["results"]}
        contract_option = options[str(contract_source.pk)]
        other_option = options[str(other_source.pk)]
        self.assertEqual(
            contract_option["contract"],
            {
                "company_id": str(company.pk),
                "company_name": company.name,
                "contract_type": ContractType.EMPLOYMENT,
                "other_type_name": None,
            },
        )
        self.assertEqual(other_option["contract"], None)
        self.assertEqual(
            set(contract_option["contract"]),
            {"company_id", "company_name", "contract_type", "other_type_name"},
        )
        self.assertNotIn("gross_amount", contract_option)
        self.assertNotIn("gross_basis", contract_option)

    def test_source_options_match_income_assignment_at_period_boundaries(self):
        starts_on_month_end = self.create_source(
            member=self.member,
            name="Starts on month end",
            start_date=self.month.month_end,
        )
        ends_on_month_start = self.create_source(
            member=self.member,
            name="Ends on month start",
            end_date=self.month.month_start,
        )
        starts_after_month = self.create_source(
            member=self.member,
            name="Starts after month",
            start_date=self.month.month_end + timedelta(days=1),
        )
        ends_before_month = self.create_source(
            member=self.member,
            name="Ends before month",
            end_date=self.month.month_start - timedelta(days=1),
        )
        options_path = self.path.replace("incomes/", "income-source-options/")
        response = self.request("get", f"{options_path}?member_id={self.member.pk}")

        self.assertEqual(response.status_code, 200)
        offered_ids = {item["id"] for item in response.data["results"]}
        eligible_sources = {self.source, starts_on_month_end, ends_on_month_start}
        excluded_sources = {starts_after_month, ends_before_month}
        self.assertEqual(offered_ids, {str(source.pk) for source in eligible_sources})

        for source in eligible_sources:
            with self.subTest(source=source.name):
                created = self.request(
                    "post",
                    self.path,
                    self.income_data(source_id=str(source.pk)),
                    key=uuid4(),
                )
                self.assertEqual(created.status_code, 201, created.data)

        for source in excluded_sources:
            with self.subTest(source=source.name):
                rejected = self.request(
                    "post",
                    self.path,
                    self.income_data(source_id=str(source.pk)),
                    key=uuid4(),
                )
                self.assertEqual(rejected.status_code, 400)

        self.assertEqual(IncomeRecord.objects.count(), len(eligible_sources))

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
