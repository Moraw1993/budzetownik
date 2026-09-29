from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, current_thread, main_thread
from unittest.mock import patch

from accounts.models import User
from django.contrib.auth.models import AnonymousUser
from django.db import connections, transaction
from django.test import TransactionTestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from households.access import require_access
from households.exceptions import SourceConflict
from households.models import (
    AuditLog,
    Household,
    HouseholdMember,
    IncomeSource,
    Invitation,
    Membership,
    Role,
)
from households.record_services import write_record
from households.services import (
    accept_invitation,
    create_household,
    issue_invitation,
    rename_household,
)

PASSWORD = "Household-Strong-Password-984!"


class HouseholdConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.first = User.objects.create_user(username="first")
        self.second = User.objects.create_user(username="second")
        self.first_access = create_household(user=self.first, name="Dom")
        self.household = self.first_access.household
        self.second_access = Membership.objects.create(
            user=self.second, household=self.household, role=Role.OWNER
        )

    def run_parallel_owner_changes(self, methods):
        barrier = Barrier(2)

        def change(user, membership, method):
            try:
                client = APIClient()
                client.force_authenticate(user=user)
                barrier.wait(timeout=10)
                path = f"/api/households/{self.household.pk}/memberships/{membership.pk}/"
                response = getattr(client, method)(
                    path, {"role": "administrator"}, format="json", HTTP_HOST="localhost"
                )
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(change, self.first, self.first_access, methods[0])
            second = executor.submit(change, self.second, self.second_access, methods[1])
            statuses = [first.result(timeout=20), second.result(timeout=20)]
        self.assertIn(409, statuses)
        self.assertEqual(sum(status in (200, 204) for status in statuses), 1)
        self.assertEqual(
            Membership.objects.filter(household=self.household, role=Role.OWNER).count(), 1
        )
        self.assertEqual(User.objects.count(), 2)

    def test_simultaneous_owner_demotions_keep_one_owner(self):
        self.run_parallel_owner_changes(("patch", "patch"))

    def test_simultaneous_owner_removals_keep_one_owner(self):
        self.run_parallel_owner_changes(("delete", "delete"))

    def test_simultaneous_removal_and_demotion_keep_one_owner(self):
        self.run_parallel_owner_changes(("delete", "patch"))

    def test_role_is_rechecked_after_waiting_for_household_lock(self):
        checked = Event()

        def observe_access(**kwargs):
            result = require_access(**kwargs)
            if current_thread() is not main_thread():
                checked.set()
            return result

        def rename():
            try:
                rename_household(user=self.second, household_id=self.household.pk, name="Rejected")
            finally:
                connections.close_all()

        with (
            patch("households.access.require_access", side_effect=observe_access),
            ThreadPoolExecutor(max_workers=1) as executor,
        ):
            with transaction.atomic():
                Household.objects.select_for_update().get(pk=self.household.pk)
                future = executor.submit(rename)
                self.assertTrue(checked.wait(timeout=10))
                self.second_access.role = Role.VIEWER
                self.second_access.save(update_fields=["role"])
            with self.assertRaises(PermissionDenied):
                future.result(timeout=20)
        self.household.refresh_from_db()
        self.assertEqual(self.household.name, "Dom")

    def test_simultaneous_invitation_acceptance_creates_one_membership(self):
        _, token = issue_invitation(
            user=self.first, household_id=self.household.pk, role=Role.MEMBER
        )
        barrier = Barrier(2)

        def accept(username):
            try:
                barrier.wait(timeout=10)
                accept_invitation(
                    user=AnonymousUser(), token=token, username=username, password=PASSWORD
                )
                return "accepted"
            except ValidationError:
                return "rejected"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(accept, username) for username in ("invite-first", "invite-second")
            ]
            outcomes = [future.result(timeout=20) for future in futures]

        self.assertEqual(outcomes.count("accepted"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)
        invitation = Invitation.objects.get()
        self.assertIsNotNone(invitation.accepted_at)
        self.assertEqual(Membership.objects.filter(household=self.household).count(), 3)

    def test_concurrent_account_linking_allows_one_member(self):
        barrier = Barrier(2)

        def link(name):
            try:
                barrier.wait(timeout=10)
                write_record(
                    user=self.first,
                    household_id=self.household.pk,
                    model=HouseholdMember,
                    data={"display_name": name, "account_id": self.first.pk},
                )
                return "created"
            except ValidationError:
                return "rejected"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(link, name) for name in ("A", "B")]
            outcomes = [future.result(timeout=20) for future in futures]
        self.assertCountEqual(outcomes, ["created", "rejected"])
        self.assertEqual(HouseholdMember.objects.count(), 1)

    def test_concurrent_income_edits_reject_stale_version(self):
        source = write_record(
            user=self.first,
            household_id=self.household.pk,
            model=IncomeSource,
            data={
                "name": "Initial",
                "category": "salary",
                "start_date": "2026-01-01",
                "default_monthly_amount": "10.00",
                "currency": "PLN",
                "frequency": "monthly",
            },
        )
        barrier = Barrier(2)

        def rename(name):
            try:
                barrier.wait(timeout=10)
                write_record(
                    user=self.first,
                    household_id=self.household.pk,
                    model=IncomeSource,
                    record_id=source.pk,
                    data={"name": name, "expected_version": source.version},
                )
                return "edited"
            except SourceConflict:
                return "conflict"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(rename, name) for name in ("First", "Second")]
            outcomes = [future.result(timeout=20) for future in futures]
        self.assertCountEqual(outcomes, ["edited", "conflict"])
        history = list(AuditLog.objects.order_by("occurred_at"))
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1].before, history[0].after)
        source.refresh_from_db()
        self.assertEqual(source.version, 2)
        self.assertEqual(source.name, history[1].after["name"])
