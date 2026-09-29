from unittest.mock import patch
from uuid import uuid4

from accounts.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from households.access import Capability, require_access
from households.models import Household, Membership, Role
from households.services import create_household

PASSWORD = "Household-Strong-Password-984!"
TEST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=TEST_HASHERS)
class HouseholdAPITests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password=PASSWORD)
        self.other = User.objects.create_user(username="other", password=PASSWORD)
        self.owner_access = create_household(user=self.owner, name="Dom")
        self.household = self.owner_access.household
        self.base = f"/api/households/{self.household.pk}/"
        self.other_access = Membership.objects.create(
            household=self.household, user=self.other, role=Role.MEMBER
        )
        self.target = f"{self.base}memberships/{self.other_access.pk}/"
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.owner)

    def request(self, method, path, data=None, *, client=None, csrf=True):
        client = client or self.client
        headers = {"secure": True, "HTTP_HOST": "localhost:8443"}
        if method != "get":
            headers["HTTP_ORIGIN"] = "https://localhost:8443"
            if csrf:
                token = client.get("/api/auth/setup/", **headers).data["csrf_token"]
                headers["HTTP_X_CSRFTOKEN"] = token
        return getattr(client, method)(path, data, format="json", **headers)

    def set_role(self, role):
        self.other_access.role = role
        self.other_access.save(update_fields=["role"])

    def test_create_defaults_to_pln_and_owner_and_survives_relogin(self):
        response = self.request("post", "/api/households/", {"name": " Drugi dom "})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Drugi dom")
        self.assertEqual(response.data["currency"], "PLN")
        self.assertEqual(response.data["role"], Role.OWNER)
        self.client.logout()
        self.client.force_login(self.owner)
        response = self.request("get", "/api/households/")
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_membership_failure_rolls_back_creation(self):
        count = Household.objects.count()
        with (
            patch("households.services.Membership.objects.create", side_effect=IntegrityError),
            self.assertRaises(IntegrityError),
        ):
            self.request("post", "/api/households/", {"name": "Wycofany"})
        self.assertEqual(Household.objects.count(), count)

    def test_create_validates_name_currency_and_rejects_injected_fields(self):
        for data in [
            {"name": ""},
            {"name": "   "},
            {"name": "a" * 181},
            {"name": "Dom", "currency": "pln"},
            {"name": "Dom", "currency": "PLNN"},
            {"name": "Dom", "role": "owner"},
            {"name": "Dom", "user_id": self.other.pk},
        ]:
            with self.subTest(data=data):
                self.assertEqual(self.request("post", "/api/households/", data).status_code, 400)
        self.assertEqual(Household.objects.count(), 1)
        response = self.request("post", "/api/households/", {"name": "Euro", "currency": "EUR"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["currency"], "EUR")

    def test_anonymous_access_is_denied_for_every_endpoint(self):
        self.client.logout()
        for method, path, data in [
            ("get", "/api/households/", None),
            ("post", "/api/households/", {"name": "Dom"}),
            ("get", self.base, None),
            ("patch", self.base, {"name": "Dom"}),
            ("get", self.base + "memberships/", None),
            ("patch", self.target, {"role": "owner"}),
            ("delete", self.target, None),
            (
                "post",
                self.base + "transfer-ownership/",
                {"membership_id": str(self.other_access.pk)},
            ),
        ]:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.request(method, path, data).status_code, 403)

    def test_writes_require_csrf(self):
        for method, path, data in [
            ("post", "/api/households/", {"name": "Dom"}),
            ("patch", self.base, {"name": "Nowa"}),
            ("patch", self.target, {"role": "viewer"}),
            ("delete", self.target, None),
            (
                "post",
                self.base + "transfer-ownership/",
                {"membership_id": str(self.other_access.pk)},
            ),
        ]:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.request(method, path, data, csrf=False).status_code, 403)
        self.other_access.refresh_from_db()
        self.assertEqual(self.other_access.role, Role.MEMBER)

    def test_all_roles_can_read_but_only_owner_and_admin_can_edit(self):
        self.client.force_login(self.other)
        for role in Role.values:
            self.set_role(role)
            with self.subTest(role=role):
                self.assertEqual(self.request("get", self.base).status_code, 200)
                listing = self.request("get", self.base + "memberships/")
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(len(listing.data), 2)
                self.assertEqual(set(listing.data[0]), {"id", "user_id", "username", "role"})
                response = self.request("patch", self.base, {"name": role})
                expected = 200 if role in {Role.OWNER, Role.ADMINISTRATOR} else 403
                self.assertEqual(response.status_code, expected)

    def test_capability_matrix_for_future_member_income_and_invitation_services(self):
        for role in Role.values:
            self.set_role(role)
            for capability in Capability:
                allowed = (
                    capability == Capability.READ
                    or role == Role.OWNER
                    or (role == Role.ADMINISTRATOR and capability == Capability.EDIT_DATA)
                )
                with self.subTest(role=role, capability=capability):
                    if allowed:
                        access = require_access(
                            user=self.other, household_id=self.household.pk, capability=capability
                        )
                        self.assertEqual(access.role, role)
                    else:
                        with self.assertRaises(PermissionDenied):
                            require_access(
                                user=self.other,
                                household_id=self.household.pk,
                                capability=capability,
                            )
        with self.assertRaises(PermissionDenied):
            require_access(user=self.owner, household_id=self.household.pk, capability="unknown")

    def test_non_owners_cannot_manage_access(self):
        self.client.force_login(self.other)
        owner_path = f"{self.base}memberships/{self.owner_access.pk}/"
        for role in [Role.ADMINISTRATOR, Role.MEMBER, Role.VIEWER]:
            self.set_role(role)
            for method, path, data in [
                ("patch", owner_path, {"role": "member"}),
                ("delete", owner_path, None),
                (
                    "post",
                    self.base + "transfer-ownership/",
                    {"membership_id": str(self.owner_access.pk)},
                ),
            ]:
                with self.subTest(role=role, method=method):
                    self.assertEqual(self.request(method, path, data).status_code, 403)
        self.owner_access.refresh_from_db()
        self.assertEqual(self.owner_access.role, Role.OWNER)

    def test_owner_changes_role_and_new_role_applies_to_existing_session(self):
        other_client = APIClient(enforce_csrf_checks=True)
        other_client.force_login(self.other)
        response = self.request("patch", self.target, {"role": "administrator"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.request("patch", self.base, {"name": "Nowa"}, client=other_client).status_code, 200
        )
        self.request("patch", self.target, {"role": "viewer"})
        self.assertEqual(
            self.request(
                "patch", self.base, {"name": "Odrzucona"}, client=other_client
            ).status_code,
            403,
        )

    def test_revoke_blocks_existing_session_but_keeps_account_and_other_household(self):
        other_household = create_household(user=self.other, name="Własny")
        other_client = APIClient(enforce_csrf_checks=True)
        other_client.force_login(self.other)
        self.assertEqual(self.request("get", self.base, client=other_client).status_code, 200)
        self.assertEqual(self.request("delete", self.target).status_code, 204)
        self.assertEqual(self.request("get", self.base, client=other_client).status_code, 404)
        self.assertEqual(
            self.request(
                "patch", self.base, {"name": "Odrzucona"}, client=other_client
            ).status_code,
            404,
        )
        self.assertEqual(self.request("get", "/api/auth/me/", client=other_client).status_code, 200)
        listing = self.request("get", "/api/households/", client=other_client)
        self.assertEqual([item["id"] for item in listing.data], [str(other_household.household_id)])
        self.assertTrue(User.objects.filter(pk=self.other.pk).exists())

    def test_last_owner_cannot_be_removed_or_demoted(self):
        path = f"{self.base}memberships/{self.owner_access.pk}/"
        for method, data in [("delete", None), ("patch", {"role": "administrator"})]:
            with self.subTest(method=method):
                response = self.request(method, path, data)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.data["code"], "last_owner")
        self.assertEqual(self.request("patch", path, {"role": "owner"}).status_code, 200)
        self.owner_access.refresh_from_db()
        self.assertEqual(self.owner_access.role, Role.OWNER)

    def test_inactive_owner_cannot_replace_last_active_owner(self):
        self.other.is_active = False
        self.other.save(update_fields=["is_active"])
        self.assertEqual(self.request("patch", self.target, {"role": "owner"}).status_code, 400)
        self.other_access.refresh_from_db()
        self.assertEqual(self.other_access.role, Role.MEMBER)
        self.other_access.role = Role.OWNER
        self.other_access.save(update_fields=["role"])
        owner_path = f"{self.base}memberships/{self.owner_access.pk}/"
        self.assertEqual(
            self.request("patch", owner_path, {"role": "administrator"}).status_code,
            409,
        )
        self.owner_access.refresh_from_db()
        self.assertEqual(self.owner_access.role, Role.OWNER)

    def test_transfer_ownership_is_atomic_and_keeps_both_accounts(self):
        response = self.request(
            "post", self.base + "transfer-ownership/", {"membership_id": str(self.other_access.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], Role.ADMINISTRATOR)
        self.owner_access.refresh_from_db()
        self.other_access.refresh_from_db()
        self.assertEqual(self.owner_access.role, Role.ADMINISTRATOR)
        self.assertEqual(self.other_access.role, Role.OWNER)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.request("patch", self.target, {"role": "viewer"}).status_code, 403)

    def test_transfer_failure_rolls_back_both_roles(self):
        original_save = Membership.save

        def fail_actor_save(instance, *args, **kwargs):
            if instance.pk == self.owner_access.pk:
                raise IntegrityError("Simulated failure")
            return original_save(instance, *args, **kwargs)

        with patch.object(Membership, "save", fail_actor_save), self.assertRaises(IntegrityError):
            self.request(
                "post",
                self.base + "transfer-ownership/",
                {"membership_id": str(self.other_access.pk)},
            )
        self.owner_access.refresh_from_db()
        self.other_access.refresh_from_db()
        self.assertEqual(self.owner_access.role, Role.OWNER)
        self.assertEqual(self.other_access.role, Role.MEMBER)

    def test_transfer_rejects_self_inactive_and_unknown_target(self):
        path = self.base + "transfer-ownership/"
        self.assertEqual(
            self.request("post", path, {"membership_id": str(self.owner_access.pk)}).status_code,
            400,
        )
        self.other.is_active = False
        self.other.save(update_fields=["is_active"])
        self.assertEqual(
            self.request("post", path, {"membership_id": str(self.other_access.pk)}).status_code,
            400,
        )
        self.assertEqual(
            self.request("post", path, {"membership_id": str(uuid4())}).status_code, 404
        )

    def test_invalid_updates_do_not_change_data(self):
        for path, data in [
            (self.target, {"role": "superuser"}),
            (self.target, {"role": "owner", "user_id": self.owner.pk}),
            (self.target, {"role": None}),
            (self.base, {"currency": "EUR"}),
            (self.base, {"name": ""}),
            (self.base, {}),
        ]:
            with self.subTest(data=data):
                self.assertEqual(self.request("patch", path, data).status_code, 400)
        self.other_access.refresh_from_db()
        self.household.refresh_from_db()
        self.assertEqual(self.other_access.role, Role.MEMBER)
        self.assertEqual(self.household.name, "Dom")

    def test_other_household_ids_are_hidden_for_reads_and_writes(self):
        outsider = User.objects.create_user(username="outsider")
        foreign = create_household(user=outsider, name="Secret")
        base = f"/api/households/{foreign.household_id}/"
        member_path = base + f"memberships/{foreign.pk}/"
        for method, path, data in [
            ("get", base, None),
            ("patch", base, {"name": "Changed"}),
            ("get", base + "memberships/", None),
            ("patch", member_path, {"role": "member"}),
            ("delete", member_path, None),
            ("post", base + "transfer-ownership/", {"membership_id": str(self.owner_access.pk)}),
        ]:
            with self.subTest(method=method, path=path):
                response = self.request(method, path, data)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("Secret", str(response.data))
                self.assertEqual(response["Cache-Control"], "no-store")
        known = self.request("get", base)
        missing = self.request("get", f"/api/households/{uuid4()}/")
        self.assertEqual(known.data, missing.data)
        listing = self.request("get", "/api/households/")
        self.assertEqual([row["id"] for row in listing.data], [str(self.household.pk)])
        foreign.household.refresh_from_db()
        self.assertEqual(foreign.household.name, "Secret")

    def test_resource_ids_cannot_cross_household_boundary(self):
        foreign = create_household(user=self.owner, name="Second")
        path = f"{self.base}memberships/{foreign.pk}/"
        for method, data in [("patch", {"role": "viewer"}), ("delete", None)]:
            self.assertEqual(self.request(method, path, data).status_code, 404)
        response = self.request(
            "post", self.base + "transfer-ownership/", {"membership_id": str(foreign.pk)}
        )
        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.role, Role.OWNER)
        response = self.request("get", f"/api/households/{foreign.household_id}/memberships/")
        self.assertEqual([row["id"] for row in response.data], [str(foreign.pk)])

    def test_owner_in_one_household_does_not_override_viewer_in_another(self):
        foreign = create_household(user=self.other, name="Other")
        Membership.objects.create(household=foreign.household, user=self.owner, role=Role.VIEWER)
        response = self.request(
            "patch", f"/api/households/{foreign.household_id}/", {"name": "Rejected"}
        )
        self.assertEqual(response.status_code, 403)
        listing = self.request("get", "/api/households/")
        self.assertEqual({row["role"] for row in listing.data}, {Role.OWNER, Role.VIEWER})

    def test_superuser_has_no_implicit_household_access(self):
        operator = User.objects.create_superuser(username="operator", password=PASSWORD)
        self.client.force_login(operator)
        self.assertEqual(self.request("get", self.base).status_code, 404)
        self.assertEqual(self.request("patch", self.base, {"name": "Rejected"}).status_code, 404)
        self.assertEqual(self.request("get", "/api/households/").data, [])

    def test_database_prevents_duplicate_membership_and_invalid_role(self):
        for user, role in [
            (self.owner, Role.MEMBER),
            (User.objects.create_user("third"), "invalid"),
        ]:
            with self.subTest(role=role), self.assertRaises(IntegrityError), transaction.atomic():
                Membership.objects.create(household=self.household, user=user, role=role)

    def test_security_events_appear_only_after_commit_and_contain_no_names(self):
        with self.assertLogs("households.security", level="INFO") as captured:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.request("patch", self.target, {"role": "viewer"})
            self.assertEqual(response.status_code, 200)
        output = " ".join(captured.output)
        self.assertIn("membership_role_changed", output)
        self.assertIn("role_before=member role_after=viewer", output)
        self.assertIn(str(self.owner.pk), output)
        self.assertNotIn(PASSWORD, output)
        self.assertNotIn("Dom", output)
        with (
            self.assertNoLogs("households.security", level="INFO"),
            self.captureOnCommitCallbacks(execute=True),
        ):
            path = f"{self.base}memberships/{self.owner_access.pk}/"
            self.assertEqual(self.request("delete", path).status_code, 409)
