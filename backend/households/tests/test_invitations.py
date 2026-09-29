from datetime import timedelta
from urllib.parse import urlsplit

from accounts.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from households.models import Invitation, Membership, Role
from households.services import create_household

PASSWORD = "Household-Strong-Password-984!"
TEST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=TEST_HASHERS)
class InvitationAPITests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password=PASSWORD)
        self.owner_access = create_household(user=self.owner, name="Dom")
        self.household = self.owner_access.household
        self.base = f"/api/households/{self.household.pk}/invitations/"
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

    def create_invitation(self, role=Role.MEMBER):
        response = self.request("post", self.base, {"role": role})
        self.assertEqual(response.status_code, 201)
        return response, urlsplit(response.data["invitation_url"]).fragment

    def test_owner_issues_lists_and_revokes_invitation_without_exposing_token(self):
        response, token = self.create_invitation(Role.VIEWER)
        self.assertTrue(response.data["invitation_url"].startswith("https://localhost:8443/"))
        self.assertTrue(token)
        self.assertNotIn("token", response.data)
        invitation = Invitation.objects.get(pk=response.data["id"])
        self.assertNotEqual(invitation.token_hash, token)
        self.assertEqual(invitation.role, Role.VIEWER)
        self.assertAlmostEqual(
            invitation.expires_at,
            timezone.now() + timedelta(days=7),
            delta=timedelta(seconds=2),
        )

        listing = self.request("get", self.base)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(
            set(listing.data[0]),
            {"id", "role", "created_at", "expires_at", "revoked_at", "accepted_at"},
        )
        self.assertNotIn(token, str(listing.data))

        self.assertEqual(self.request("delete", f"{self.base}{invitation.pk}/").status_code, 204)
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.revoked_at)

    def test_only_owner_can_manage_invitations_and_foreign_households_stay_hidden(self):
        member = User.objects.create_user(username="member", password=PASSWORD)
        membership = Membership.objects.create(
            household=self.household, user=member, role=Role.MEMBER
        )
        member_client = APIClient(enforce_csrf_checks=True)
        member_client.force_login(member)
        for method, path, data in [
            ("get", self.base, None),
            ("post", self.base, {"role": Role.VIEWER}),
        ]:
            with self.subTest(method=method):
                self.assertEqual(
                    self.request(method, path, data, client=member_client).status_code,
                    403,
                )

        outsider = User.objects.create_user(username="outsider", password=PASSWORD)
        foreign = create_household(user=outsider, name="Tajne")
        foreign_path = f"/api/households/{foreign.household_id}/invitations/"
        response = self.request("get", foreign_path)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Tajne", str(response.data))
        self.assertEqual(membership.role, Role.MEMBER)

    def test_valid_link_creates_account_and_membership_then_starts_session(self):
        _, token = self.create_invitation(Role.ADMINISTRATOR)
        anonymous = APIClient(enforce_csrf_checks=True)
        response = self.request(
            "post",
            "/api/invitations/accept/",
            {"token": token, "username": "new-user", "password": PASSWORD},
            client=anonymous,
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        membership = Membership.objects.get(household=self.household, user=user)
        self.assertEqual(membership.role, Role.ADMINISTRATOR)
        self.assertEqual(response.data["id"], str(membership.pk))
        self.assertEqual(self.request("get", "/api/auth/me/", client=anonymous).status_code, 200)

    def test_existing_member_acceptance_does_not_duplicate_or_change_role(self):
        user = User.objects.create_user(username="existing", password=PASSWORD)
        original = Membership.objects.create(household=self.household, user=user, role=Role.VIEWER)
        _, token = self.create_invitation(Role.ADMINISTRATOR)
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(user)

        response = self.request("post", "/api/invitations/accept/", {"token": token}, client=client)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Membership.objects.filter(household=self.household, user=user).count(), 1)
        original.refresh_from_db()
        self.assertEqual(original.role, Role.VIEWER)

    def test_revoked_expired_and_reused_links_make_no_changes(self):
        response, revoked_token = self.create_invitation()
        self.request("delete", f"{self.base}{response.data['id']}/")
        response = self.request(
            "post",
            "/api/invitations/accept/",
            {"token": revoked_token, "username": "revoked", "password": PASSWORD},
            client=APIClient(enforce_csrf_checks=True),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="revoked").exists())

        response, expired_token = self.create_invitation()
        invitation = Invitation.objects.get(pk=response.data["id"])
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])
        response = self.request(
            "post",
            "/api/invitations/accept/",
            {"token": expired_token, "username": "expired", "password": PASSWORD},
            client=APIClient(enforce_csrf_checks=True),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="expired").exists())

        _, valid_token = self.create_invitation()
        client = APIClient(enforce_csrf_checks=True)
        response = self.request(
            "post",
            "/api/invitations/accept/",
            {"token": valid_token, "username": "once", "password": PASSWORD},
            client=client,
        )
        self.assertEqual(response.status_code, 201)
        response = self.request(
            "post", "/api/invitations/accept/", {"token": valid_token}, client=client
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(username="once").count(), 1)
