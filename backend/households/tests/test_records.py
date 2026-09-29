from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from accounts.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from households.models import (
    AuditLog,
    HouseholdMember,
    IncomeSource,
    Membership,
    RelationType,
    Role,
)
from households.services import create_household


class HouseholdRecordTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="records-owner")
        self.reader = User.objects.create_user(username="records-reader")
        self.household = create_household(user=self.owner, name="Dom").household
        self.membership = Membership.objects.create(
            household=self.household, user=self.reader, role=Role.MEMBER
        )
        self.foreign = create_household(user=self.reader, name="Obcy").household
        self.base = f"/api/households/{self.household.pk}/"
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.income = {
            "name": "Świadczenie rodzinne",
            "category": "family_benefit",
            "payer": "Płatnik",
            "start_date": "2026-01-01",
            "end_date": None,
            "default_monthly_amount": "1234.56",
            "currency": "PLN",
            "frequency": "monthly",
            "is_regular": True,
            "description": "Opis",
        }

    def request(self, method, suffix, data=None, *, csrf=True):
        headers = {"secure": True, "HTTP_HOST": "localhost:8443"}
        if method != "get":
            headers["HTTP_ORIGIN"] = "https://localhost:8443"
            if csrf:
                headers["HTTP_X_CSRFTOKEN"] = self.client.get("/api/auth/setup/", **headers).data[
                    "csrf_token"
                ]
        path = suffix if suffix.startswith("/api/") else self.base + suffix
        return getattr(self.client, method)(path, data, format="json", **headers)

    def create(self, resource, data):
        response = self.request("post", resource + "/", data)
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_members_relations_and_archival_preserve_links_without_roles(self):
        relation = self.create("relation-types", {"name": "Rodzic"})
        member = self.create(
            "members", {"display_name": "Osoba", "relation_type_id": relation["id"]}
        )
        self.assertIsNone(member["account_id"])
        source = self.create("income-sources", {**self.income, "member_id": member["id"]})
        self.assertEqual(
            self.request("post", f"relation-types/{relation['id']}/deactivate/", {}).status_code,
            200,
        )
        self.assertEqual(
            self.request("patch", f"members/{member['id']}/", {"display_name": "Nowa"}).status_code,
            200,
        )
        self.assertEqual(
            self.request("post", f"members/{member['id']}/deactivate/", {}).status_code, 200
        )
        self.assertEqual(
            IncomeSource.objects.get(pk=source["id"]).member_id,
            HouseholdMember.objects.get().pk,
        )
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(Membership.objects.get(pk=self.membership.pk).role, Role.MEMBER)
        archived = self.request("get", "members/").data["results"][0]
        self.assertFalse(archived["is_active"])
        self.assertIsNotNone(archived["deactivated_at"])
        self.assertEqual(
            self.request(
                "post", "income-sources/", {**self.income, "member_id": member["id"]}
            ).status_code,
            400,
        )

    def test_account_links_unique_per_household_and_reject_outsiders(self):
        outsider = User.objects.create_user(username="outside")
        member = self.create("members", {"display_name": "Osoba", "account_id": self.owner.pk})
        self.assertEqual(
            self.request(
                "post", "members/", {"display_name": "Duplikat", "account_id": self.owner.pk}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.request(
                "patch", f"members/{member['id']}/", {"account_id": outsider.pk}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.request("patch", f"members/{member['id']}/", {"account_id": None}).status_code, 200
        )
        self.create("members", {"display_name": "Inna", "account_id": self.owner.pk})
        other_household = create_household(user=self.owner, name="Drugi").household
        response = self.request(
            "post",
            f"/api/households/{other_household.pk}/members/",
            {"display_name": "Ta sama", "account_id": self.owner.pk},
        )
        self.assertEqual(response.status_code, 201)

    def test_income_round_trip_and_audit_creation_update_deactivation(self):
        source = self.create("income-sources", self.income)
        for field, value in self.income.items():
            self.assertEqual(source[field], value)
        self.assertEqual(IncomeSource.objects.get().default_monthly_amount, Decimal("1234.56"))
        path = f"income-sources/{source['id']}/"
        self.assertEqual(
            self.request(
                "patch",
                path,
                {
                    "name": "Nowe świadczenie",
                    "default_monthly_amount": "999.99",
                    "expected_version": source["version"],
                },
            ).status_code,
            200,
        )
        self.assertEqual(self.request("post", path + "deactivate/", {}).status_code, 200)
        self.assertEqual(self.request("post", path + "deactivate/", {}).status_code, 200)
        entries = list(AuditLog.objects.order_by("occurred_at"))
        self.assertEqual([entry.action for entry in entries], ["created", "updated", "deactivated"])
        self.assertIsNone(entries[0].before)
        self.assertEqual(entries[1].before, entries[0].after)
        self.assertEqual(entries[2].before, entries[1].after)
        self.assertFalse(entries[2].after["is_active"])
        self.assertTrue(
            all(
                entry.actor == self.owner and entry.household == self.household for entry in entries
            )
        )
        self.assertEqual(self.request("patch", path, {"name": "Odrzucona"}).status_code, 400)
        self.assertEqual(self.request("delete", path).status_code, 405)
        self.assertEqual(AuditLog.objects.count(), 3)

    def test_source_edit_requires_current_version(self):
        source = self.create("income-sources", self.income)
        path = f"income-sources/{source['id']}/"
        self.assertEqual(self.request("patch", path, {"name": "Bez wersji"}).status_code, 400)
        updated = self.request(
            "patch", path, {"name": "Pierwsza zmiana", "expected_version": source["version"]}
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["version"], source["version"] + 1)
        audit_count = AuditLog.objects.count()
        conflict = self.request(
            "patch", path, {"name": "Stara zmiana", "expected_version": source["version"]}
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.data["code"], "source_conflict")
        self.assertEqual(IncomeSource.objects.get(pk=source["id"]).name, "Pierwsza zmiana")
        self.assertEqual(AuditLog.objects.count(), audit_count)

    def test_roles_for_each_resource_and_owner_only_audit(self):
        for resource, data in [
            ("members", {"display_name": "Osoba"}),
            ("relation-types", {"name": "Relacja"}),
            ("income-sources", self.income),
        ]:
            self.client.force_login(self.owner)
            record = self.create(resource, data)
            path = f"{resource}/{record['id']}/"
            self.client.force_login(self.reader)
            for role in Role.values:
                self.membership.role = role
                self.membership.save()
                allowed = role in (Role.OWNER, Role.ADMINISTRATOR)
                with self.subTest(resource=resource, role=role):
                    self.assertEqual(self.request("get", resource + "/").status_code, 200)
                    detail = self.request("get", path)
                    self.assertEqual(detail.status_code, 200)
                    patch_data = (
                        {**data, "expected_version": detail.data["version"]}
                        if resource == "income-sources"
                        else data
                    )
                    self.assertEqual(
                        self.request("patch", path, patch_data).status_code,
                        200 if allowed else 403,
                    )
                    self.assertEqual(
                        self.request("get", "audit-logs/").status_code,
                        200 if role == Role.OWNER else 403,
                    )
                    if not allowed:
                        self.assertEqual(
                            self.request("post", resource + "/", data).status_code, 403
                        )
                        self.assertEqual(
                            self.request("post", path + "deactivate/", {}).status_code, 403
                        )

    def test_foreign_ids_are_hidden_and_cross_household_links_rejected(self):
        foreign_relation = RelationType.objects.create(household=self.foreign, name="Sekret")
        foreign_member = HouseholdMember.objects.create(
            household=self.foreign, display_name="Sekret"
        )
        for resource, data, obj in [
            ("members", {"display_name": "Zmieniona"}, foreign_member),
            ("relation-types", {"name": "Zmieniona"}, foreign_relation),
        ]:
            self.assertEqual(self.request("get", f"{resource}/{obj.pk}/").status_code, 404)
            self.assertEqual(self.request("patch", f"{resource}/{obj.pk}/", data).status_code, 404)
            self.assertEqual(
                self.request("post", f"{resource}/{obj.pk}/deactivate/", {}).status_code, 404
            )
            self.assertEqual(
                self.request("get", f"/api/households/{self.foreign.pk}/{resource}/").status_code,
                404,
            )
        self.assertEqual(
            self.request(
                "post",
                "members/",
                {"display_name": "X", "relation_type_id": str(foreign_relation.pk)},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.request(
                "post", "income-sources/", {**self.income, "member_id": str(foreign_member.pk)}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.request("get", f"/api/households/{self.foreign.pk}/audit-logs/").status_code, 404
        )
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_invalid_income_and_injected_fields_do_not_write_audit(self):
        for values in [
            {"default_monthly_amount": "NaN"},
            {"default_monthly_amount": "-1.00"},
            {"default_monthly_amount": "1.001"},
            {"currency": "pln"},
            {"frequency": "invalid"},
            {"end_date": "2025-01-01"},
            {"password": "secret"},
            {"token": "secret"},
            {"household_id": str(self.foreign.pk)},
            {"is_active": False},
            {"actor_id": self.reader.pk},
        ]:
            with self.subTest(values=values):
                self.assertEqual(
                    self.request("post", "income-sources/", {**self.income, **values}).status_code,
                    400,
                )
        self.assertEqual(IncomeSource.objects.count(), 0)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_audit_failure_rolls_back_create_update_and_deactivation(self):
        source = self.create("income-sources", self.income)
        for method, path, data in [
            ("post", "income-sources/", self.income),
            (
                "patch",
                f"income-sources/{source['id']}/",
                {"name": "Wycofana", "expected_version": source["version"]},
            ),
            ("post", f"income-sources/{source['id']}/deactivate/", {}),
        ]:
            with (
                self.subTest(method=method, path=path),
                patch(
                    "households.record_services.AuditLog.objects.create", side_effect=IntegrityError
                ),
                self.assertRaises(IntegrityError),
            ):
                self.request(method, path, data)
            self.assertEqual(IncomeSource.objects.count(), 1)
            self.assertEqual(IncomeSource.objects.get().name, self.income["name"])
            self.assertTrue(IncomeSource.objects.get().is_active)
            self.assertEqual(AuditLog.objects.count(), 1)

    def test_audit_is_filtered_readonly_and_contains_only_allowed_fields(self):
        source = self.create("income-sources", self.income)
        response = self.request("get", f"audit-logs/?object_id={source['id']}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(self.request("get", f"audit-logs/?object_id={uuid4()}").data["count"], 0)
        self.assertEqual(self.request("get", "audit-logs/?since=bad").status_code, 400)
        self.assertEqual(
            self.request(
                "get", "audit-logs/?since=2026-02-01T00:00:00Z&until=2026-01-01T00:00:00Z"
            ).status_code,
            400,
        )
        for method in ("post", "patch", "delete"):
            self.assertEqual(self.request(method, "audit-logs/", {}).status_code, 405)
        after = response.data["results"][0]["after"]
        self.assertEqual(
            set(after), set(self.income) | {"member_id", "is_active", "deactivated_at"}
        )

    def test_anonymous_and_csrf_protection(self):
        for resource, data in [
            ("members", {"display_name": "Osoba"}),
            ("relation-types", {"name": "Relacja"}),
            ("income-sources", self.income),
        ]:
            self.assertEqual(
                self.request("post", resource + "/", data, csrf=False).status_code, 403
            )
        self.client.logout()
        for resource in ("members", "relation-types", "income-sources", "audit-logs"):
            self.assertEqual(self.request("get", resource + "/").status_code, 403)

    def test_database_uniqueness_and_archive_constraints(self):
        HouseholdMember.objects.create(
            household=self.household, display_name="A", account=self.owner
        )
        for values in [{"account": self.owner}, {"is_active": False}]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                HouseholdMember.objects.create(household=self.household, display_name="B", **values)

    def test_lists_are_paginated_and_include_archived_records(self):
        HouseholdMember.objects.bulk_create(
            [
                HouseholdMember(household=self.household, display_name=f"Osoba {i}")
                for i in range(51)
            ]
        )
        page = self.request("get", "members/").data
        self.assertEqual(page["count"], 51)
        self.assertEqual(len(page["results"]), 50)
        self.assertIsNotNone(page["next"])
        self.assertEqual(len(self.request("get", "members/?page=2").data["results"]), 1)

    def test_income_ids_cannot_cross_households_even_for_shared_owner(self):
        self.client.force_login(self.reader)
        original_base = self.base
        self.base = f"/api/households/{self.foreign.pk}/"
        source = self.create("income-sources", self.income)
        self.base = original_base
        self.client.force_login(self.owner)
        Membership.objects.create(household=self.foreign, user=self.owner, role=Role.OWNER)
        path = f"income-sources/{source['id']}/"
        for method, suffix, data in [
            ("get", path, None),
            ("patch", path, {"name": "Odrzucona"}),
            ("post", path + "deactivate/", {}),
        ]:
            with self.subTest(method=method):
                self.assertEqual(self.request(method, suffix, data).status_code, 404)
        self.assertEqual(self.request("get", "income-sources/").data["count"], 0)
        self.assertEqual(self.request("get", "audit-logs/").data["count"], 0)
        self.assertEqual(IncomeSource.objects.get().name, self.income["name"])
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_admin_creates_and_deactivates_and_revocation_takes_effect(self):
        self.membership.role = Role.ADMINISTRATOR
        self.membership.save()
        self.client.force_login(self.reader)
        for resource, data in [
            ("members", {"display_name": "Osoba"}),
            ("relation-types", {"name": "Relacja"}),
            ("income-sources", self.income),
        ]:
            record = self.create(resource, data)
            path = f"{resource}/{record['id']}/deactivate/"
            self.assertEqual(self.request("post", path, {}, csrf=False).status_code, 403)
            self.assertEqual(self.request("post", path, {}).status_code, 200)
        self.membership.delete()
        self.assertEqual(self.request("get", "members/").status_code, 404)
        self.assertEqual(self.request("post", "income-sources/", self.income).status_code, 404)

    def test_invalid_partial_update_preserves_source_and_audit(self):
        source = self.create("income-sources", self.income)
        path = f"income-sources/{source['id']}/"
        self.assertEqual(
            self.request(
                "patch", path, {"end_date": "2025-01-01", "expected_version": source["version"]}
            ).status_code,
            400,
        )
        self.assertEqual(self.request("patch", path, {"name": "Nowa"}, csrf=False).status_code, 403)
        self.assertIsNone(IncomeSource.objects.get().end_date)
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_relation_name_uniqueness_preserves_archived_references(self):
        relation = self.create("relation-types", {"name": "Rodzic"})
        self.assertEqual(
            self.request("post", "relation-types/", {"name": "Rodzic"}).status_code, 400
        )
        self.request("post", f"relation-types/{relation['id']}/deactivate/", {})
        replacement = self.create("relation-types", {"name": "Rodzic"})
        self.assertNotEqual(relation["id"], replacement["id"])
        self.assertEqual(RelationType.objects.count(), 2)
