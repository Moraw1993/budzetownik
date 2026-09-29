from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch

from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.exceptions import SetupClosedError
from accounts.models import LoginThrottle, User
from accounts.services import create_initial_account

PASSWORD = "Strong-Local-Password-984!"
NEW_PASSWORD = "Changed-Local-Password-761!"
TEST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=TEST_HASHERS)
class AccountAPITests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def get(self, path):
        return self.client.get(path, secure=True, HTTP_HOST="localhost:8443")

    def post(self, path, data=None):
        csrf = self.get("/api/auth/setup/").data["csrf_token"]
        return self.client.post(
            path,
            data or {},
            format="json",
            secure=True,
            HTTP_HOST="localhost:8443",
            HTTP_ORIGIN="https://localhost:8443",
            HTTP_X_CSRFTOKEN=csrf,
        )

    def create_user(self):
        return User.objects.create_user(username="arek", password=PASSWORD)

    def test_setup_creates_hashed_non_admin_account_and_session(self):
        response = self.post(
            "/api/auth/setup/",
            {"username": "arek", "password": PASSWORD, "is_superuser": True},
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get()
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertEqual(set(response.data), {"id", "username"})
        self.assertEqual(self.get("/api/auth/me/").status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_setup_is_closed_after_first_account(self):
        self.create_user()
        response = self.post("/api/auth/setup/", {"username": "other", "password": PASSWORD})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(self.get("/api/auth/setup/").data["setup_required"])

    def test_setup_rejects_weak_password(self):
        response = self.post("/api/auth/setup/", {"username": "arek", "password": "123"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_anonymous_setup_and_login_require_csrf(self):
        for path in ["/api/auth/setup/", "/api/auth/login/"]:
            with self.subTest(path=path):
                response = self.client.post(
                    path,
                    {"username": "arek", "password": PASSWORD},
                    format="json",
                    secure=True,
                    HTTP_HOST="localhost:8443",
                )
                self.assertEqual(response.status_code, 403)

    def test_login_and_logout_invalidate_previous_session(self):
        self.create_user()
        response = self.post("/api/auth/login/", {"username": "arek", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        session_id = self.client.cookies["sessionid"].value
        self.assertTrue(response.cookies["sessionid"]["secure"])
        self.assertTrue(response.cookies["sessionid"]["httponly"])
        self.assertEqual(self.post("/api/auth/logout/").status_code, 204)
        self.assertFalse(Session.objects.filter(session_key=session_id).exists())
        self.client.cookies["sessionid"] = session_id
        self.assertEqual(self.get("/api/auth/me/").status_code, 403)

    def test_invalid_and_unknown_logins_have_same_response(self):
        self.create_user()
        invalid = self.post("/api/auth/login/", {"username": "arek", "password": "bad"})
        missing = self.post("/api/auth/login/", {"username": "missing", "password": "bad"})
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(invalid.data, missing.data)
        self.assertEqual(self.get("/api/auth/me/").status_code, 403)

    def test_inactive_user_cannot_log_in(self):
        user = self.create_user()
        user.is_active = False
        user.save()
        response = self.post("/api/auth/login/", {"username": "arek", "password": PASSWORD})
        self.assertEqual(response.status_code, 401)

    def test_sixth_failed_attempt_is_limited(self):
        self.create_user()
        for _attempt in range(5):
            self.assertEqual(
                self.post("/api/auth/login/", {"username": "arek", "password": "bad"}).status_code,
                401,
            )
        response = self.post("/api/auth/login/", {"username": "arek", "password": PASSWORD})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "900")
        self.assertEqual(self.get("/api/auth/me/").status_code, 403)

    def test_expired_throttle_window_allows_login(self):
        self.create_user()
        for _attempt in range(5):
            self.post("/api/auth/login/", {"username": "arek", "password": "bad"})
        LoginThrottle.objects.update(window_started=timezone.now() - timedelta(minutes=16))
        response = self.post("/api/auth/login/", {"username": "arek", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)

    def test_source_limit_blocks_username_spraying(self):
        for number in range(30):
            self.post("/api/auth/login/", {"username": f"missing{number}", "password": "bad"})
        response = self.post("/api/auth/login/", {"username": "another", "password": "bad"})
        self.assertEqual(response.status_code, 429)

    def test_logs_do_not_contain_credentials(self):
        self.create_user()
        with self.assertLogs("accounts.security") as captured:
            self.post("/api/auth/login/", {"username": "arek", "password": PASSWORD})
        text = " ".join(captured.output)
        self.assertNotIn(PASSWORD, text)
        self.assertNotIn(self.client.cookies["sessionid"].value, text)

    def test_recovery_invalidates_sessions_without_changing_roles(self):
        user = self.create_user()
        self.post("/api/auth/login/", {"username": user.username, "password": PASSWORD})
        output = StringIO()
        with patch(
            "accounts.management.commands.recover_account.getpass",
            side_effect=[NEW_PASSWORD, NEW_PASSWORD],
        ):
            call_command("recover_account", user.username, stdout=output)
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(self.get("/api/auth/me/").status_code, 403)
        self.assertNotIn(NEW_PASSWORD, output.getvalue())

    def test_recovery_does_not_create_missing_account(self):
        with self.assertRaises(CommandError):
            call_command("recover_account", "missing")
        self.assertFalse(User.objects.exists())

    def test_recovery_rejects_mismatched_passwords(self):
        user = self.create_user()
        with (
            patch(
                "accounts.management.commands.recover_account.getpass",
                side_effect=[NEW_PASSWORD, "different"],
            ),
            self.assertRaises(CommandError),
        ):
            call_command("recover_account", user.username)
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))

    def test_logout_rejects_missing_csrf_even_when_authenticated(self):
        self.create_user()
        self.post("/api/auth/login/", {"username": "arek", "password": PASSWORD})
        response = self.client.post(
            "/api/auth/logout/", {}, format="json", secure=True, HTTP_HOST="localhost:8443"
        )
        self.assertEqual(response.status_code, 403)


@override_settings(PASSWORD_HASHERS=TEST_HASHERS)
class ConcurrentSetupTests(TransactionTestCase):
    def test_only_one_concurrent_setup_succeeds(self):
        barrier = Barrier(2)

        def create(username):
            connections.close_all()
            barrier.wait(timeout=10)
            try:
                create_initial_account(username=username, password=PASSWORD)
                return "created"
            except SetupClosedError:
                return "closed"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(create, ["first", "second"]))

        self.assertCountEqual(results, ["created", "closed"])
        self.assertEqual(User.objects.count(), 1)
