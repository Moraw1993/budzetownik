from unittest.mock import patch

from accounts.models import User
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from households.models import (
    AccountingMonth,
    AccountingMonthState,
    AccountingYear,
    AuditLog,
    Membership,
    Role,
)
from households.period_services import create_accounting_year, transition_accounting_month
from households.services import create_household


class AccountingPeriodApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="period-owner")
        self.admin = User.objects.create_user(username="period-admin")
        self.member = User.objects.create_user(username="period-member")
        self.viewer = User.objects.create_user(username="period-viewer")
        self.outsider = User.objects.create_user(username="period-outsider")
        self.household = create_household(user=self.owner, name="Dom").household
        Membership.objects.create(
            household=self.household, user=self.admin, role=Role.ADMINISTRATOR
        )
        Membership.objects.create(household=self.household, user=self.member, role=Role.MEMBER)
        Membership.objects.create(household=self.household, user=self.viewer, role=Role.VIEWER)
        self.foreign_household = create_household(user=self.outsider, name="Obcy dom").household
        self.base = f"/api/households/{self.household.pk}/"
        self.client = APIClient()

    def request(self, method, path, data=None, *, user=None):
        self.client.force_login(self.owner if user is None else user)
        return getattr(self.client, method)(
            self.base + path,
            data,
            format="json",
            HTTP_HOST="localhost",
            secure=True,
        )

    def create_year(self, calendar_year=2028, *, user=None):
        response = self.request(
            "post", "accounting-years/", {"calendar_year": calendar_year}, user=user
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_create_year_returns_twelve_inactive_calendar_months_and_audit(self):
        result = self.create_year()

        self.assertEqual(result["calendar_year"], 2028)
        self.assertEqual(len(result["months"]), 12)
        self.assertEqual([month["month_number"] for month in result["months"]], list(range(1, 13)))
        self.assertEqual({month["state"] for month in result["months"]}, {"inactive"})
        self.assertEqual(result["months"][1]["month_start"], "2028-02-01")
        self.assertEqual(result["months"][1]["month_end"], "2028-02-29")
        year = AccountingYear.objects.get(pk=result["id"])
        self.assertEqual(year.household_id, self.household.pk)
        audit = AuditLog.objects.get(object_type="accounting_year", object_id=year.pk)
        self.assertEqual(audit.actor, self.owner)
        self.assertEqual(audit.after["calendar_year"], 2028)
        self.assertEqual(len(audit.after["month_ids"]), 12)

    def test_duplicate_invalid_and_unknown_year_fields_are_rejected(self):
        self.create_year(2027)
        duplicate = self.request("post", "accounting-years/", {"calendar_year": 2027})
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data["code"], "accounting_period_conflict")

        for payload in (
            {"calendar_year": 0},
            {"calendar_year": 10000},
            {"calendar_year": 2027, "household_id": str(self.household.pk)},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.request("post", "accounting-years/", payload).status_code, 400
                )
        self.assertEqual(AccountingYear.objects.count(), 1)
        self.assertEqual(AccountingMonth.objects.count(), 12)
        self.assertEqual(AuditLog.objects.filter(object_type="accounting_year").count(), 1)

    def test_year_list_and_month_list_enforce_household_scope(self):
        year = self.create_year(2026)
        years_response = self.request("get", "accounting-years/", user=self.member)
        self.assertEqual(years_response.status_code, 200)
        self.assertEqual(years_response.data["count"], 1)

        months_response = self.request(
            "get", f"accounting-years/{year['id']}/months/", user=self.viewer
        )
        self.assertEqual(months_response.status_code, 200)
        self.assertEqual(len(months_response.data), 12)
        self.assertEqual(
            self.request(
                "get",
                f"accounting-years/{year['id']}/months/",
                user=self.outsider,
            ).status_code,
            404,
        )

        foreign_year = create_accounting_year(
            user=self.outsider, household_id=self.foreign_household.pk, calendar_year=2026
        )
        self.assertEqual(
            self.request("get", f"accounting-years/{foreign_year.pk}/months/").status_code,
            404,
        )

    def test_only_owner_and_admin_can_create_and_change_months(self):
        owner_year = self.create_year(2024)
        admin_year = self.create_year(2025, user=self.admin)
        for user in (self.member, self.viewer):
            with self.subTest(user=user.username):
                self.assertEqual(
                    self.request(
                        "post",
                        "accounting-years/",
                        {"calendar_year": 2023},
                        user=user,
                    ).status_code,
                    403,
                )
                self.assertEqual(
                    self.request(
                        "post",
                        f"accounting-years/{owner_year['id']}/months/"
                        f"{owner_year['months'][0]['id']}/activate/",
                        {},
                        user=user,
                    ).status_code,
                    403,
                )

        response = self.request(
            "post",
            f"accounting-years/{admin_year['id']}/months/{admin_year['months'][0]['id']}/activate/",
            {},
            user=self.admin,
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["state"], AccountingMonthState.ACTIVE)

    def test_month_transitions_are_independent_idempotent_and_audited(self):
        year = self.create_year(2024)
        first, second = year["months"][:2]
        first_path = f"accounting-years/{year['id']}/months/{first['id']}"
        second_path = f"accounting-years/{year['id']}/months/{second['id']}"

        invalid = self.request("post", f"{first_path}/close/", {})
        self.assertEqual(invalid.status_code, 409)
        self.assertEqual(invalid.data["code"], "accounting_period_conflict")

        activated = self.request("post", f"{first_path}/activate/", {})
        self.assertEqual(activated.status_code, 200, activated.data)
        self.assertEqual(activated.data["state"], "active")
        self.assertIsNotNone(activated.data["activated_at"])
        self.assertEqual(self.request("post", f"{first_path}/activate/", {}).status_code, 200)
        self.assertEqual(self.request("post", f"{second_path}/activate/", {}).status_code, 200)

        closed = self.request("post", f"{first_path}/close/", {})
        self.assertEqual(closed.status_code, 200, closed.data)
        self.assertEqual(closed.data["state"], "closed")
        self.assertIsNotNone(closed.data["closed_at"])
        self.assertEqual(self.request("post", f"{first_path}/close/", {}).status_code, 200)

        reopened = self.request("post", f"{first_path}/reopen/", {})
        self.assertEqual(reopened.status_code, 200, reopened.data)
        self.assertEqual(reopened.data["state"], "active")
        self.assertEqual(self.request("post", f"{first_path}/reopen/", {}).status_code, 200)

        months = self.request("get", f"accounting-years/{year['id']}/months/").data
        self.assertEqual([month["state"] for month in months[:2]], ["active", "active"])
        month_audits = AuditLog.objects.filter(object_type="accounting_month").order_by(
            "occurred_at"
        )
        self.assertEqual(month_audits.count(), 4)
        self.assertEqual(
            list(month_audits.values_list("action", flat=True)),
            ["activated", "activated", "closed", "reopened"],
        )
        audit_response = self.request("get", "audit-logs/?object_type=accounting_month")
        self.assertEqual(audit_response.status_code, 200)
        self.assertEqual(audit_response.data["count"], 4)

    def test_month_transition_state_action_matrix_preserves_timestamps_and_audit(self):
        cases = (
            ("inactive", "activate", 200, "active", "activated"),
            ("inactive", "close", 409, "inactive", None),
            ("inactive", "reopen", 409, "inactive", None),
            ("active", "activate", 200, "active", None),
            ("active", "close", 200, "closed", "closed"),
            ("active", "reopen", 200, "active", None),
            ("closed", "activate", 409, "closed", None),
            ("closed", "close", 200, "closed", None),
            ("closed", "reopen", 200, "active", "reopened"),
        )

        for index, (initial_state, operation, status, target_state, audit_action) in enumerate(
            cases
        ):
            with self.subTest(initial_state=initial_state, operation=operation):
                year = create_accounting_year(
                    user=self.owner,
                    household_id=self.household.pk,
                    calendar_year=2040 + index,
                )
                month = year.months.get(month_number=1)
                month_path = f"accounting-years/{year.pk}/months/{month.pk}"
                if initial_state in {"active", "closed"}:
                    self.assertEqual(
                        self.request("post", f"{month_path}/activate/", {}).status_code,
                        200,
                    )
                if initial_state == "closed":
                    self.assertEqual(
                        self.request("post", f"{month_path}/close/", {}).status_code,
                        200,
                    )

                month.refresh_from_db()
                previous_activated_at = month.activated_at
                previous_closed_at = month.closed_at
                audit_query = AuditLog.objects.filter(
                    object_type="accounting_month", object_id=month.pk
                )
                previous_audit_count = audit_query.count()

                response = self.request("post", f"{month_path}/{operation}/", {})
                self.assertEqual(response.status_code, status, response.data)
                if status == 409:
                    self.assertEqual(response.data["code"], "accounting_period_conflict")
                else:
                    self.assertEqual(response.data["state"], target_state)

                month.refresh_from_db()
                self.assertEqual(month.state, target_state)
                if audit_action is None:
                    self.assertEqual(audit_query.count(), previous_audit_count)
                    self.assertEqual(month.activated_at, previous_activated_at)
                    self.assertEqual(month.closed_at, previous_closed_at)
                    continue

                self.assertEqual(audit_query.count(), previous_audit_count + 1)
                event = audit_query.get(action=audit_action)
                self.assertEqual(event.actor, self.owner)
                self.assertEqual(event.before, {"state": initial_state})
                self.assertEqual(event.after, {"state": target_state})
                self.assertIsNotNone(event.occurred_at)
                if operation in {"activate", "reopen"}:
                    self.assertIsNotNone(month.activated_at)
                    if operation == "reopen":
                        self.assertGreater(month.activated_at, previous_activated_at)
                        self.assertEqual(month.closed_at, previous_closed_at)
                if operation == "close":
                    self.assertIsNotNone(month.closed_at)
                    self.assertGreater(month.closed_at, previous_closed_at or previous_activated_at)

    def test_audit_failure_rolls_back_year_creation_and_month_transition(self):
        with (
            patch("households.record_services.AuditLog.objects.create", side_effect=IntegrityError),
            self.assertRaises(IntegrityError),
        ):
            create_accounting_year(
                user=self.owner, household_id=self.household.pk, calendar_year=2030
            )
        self.assertFalse(AccountingYear.objects.filter(calendar_year=2030).exists())
        self.assertFalse(AccountingMonth.objects.exists())

        year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2031
        )
        month = year.months.get(month_number=1)
        with (
            patch("households.record_services.AuditLog.objects.create", side_effect=IntegrityError),
            self.assertRaises(IntegrityError),
        ):
            transition_accounting_month(
                user=self.owner,
                household_id=self.household.pk,
                year_id=year.pk,
                month_id=month.pk,
                operation="activate",
            )
        month.refresh_from_db()
        self.assertEqual(month.state, AccountingMonthState.INACTIVE)
