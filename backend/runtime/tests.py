from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class ReadinessTests(TestCase):
    def test_ready_after_migrations(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_database_failure_returns_service_unavailable_without_details(self):
        with patch("runtime.views.connection.cursor", side_effect=OperationalError("private-host")):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-host", response.content.decode())

    def test_pending_migrations_are_not_ready(self):
        with patch("runtime.views.MigrationExecutor") as executor:
            executor.return_value.migration_plan.return_value = [object()]
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)

    def test_write_method_is_rejected(self):
        self.assertEqual(self.client.post(reverse("health")).status_code, 405)
