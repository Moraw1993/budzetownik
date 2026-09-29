from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from accounts.models import User
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from households.models import (
    AuditLog,
    Company,
    Contract,
    HouseholdMember,
    IncomeKind,
    IncomeSource,
    Membership,
    Role,
)
from households.services import create_household


class FamilyIncomeApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="family-owner")
        self.admin = User.objects.create_user(username="family-admin")
        self.member_user = User.objects.create_user(username="family-member")
        self.viewer = User.objects.create_user(username="family-viewer")
        self.outsider = User.objects.create_user(username="family-outsider")
        self.household = create_household(user=self.owner, name="Dom").household
        self.foreign = create_household(user=self.owner, name="Drugi dom").household
        for user, role in (
            (self.admin, Role.ADMINISTRATOR),
            (self.member_user, Role.MEMBER),
            (self.viewer, Role.VIEWER),
        ):
            Membership.objects.create(household=self.household, user=user, role=role)
        self.member = HouseholdMember.objects.create(household=self.household, display_name="Osoba")
        self.foreign_member = HouseholdMember.objects.create(
            household=self.foreign, display_name="Obca osoba"
        )
        self.company = Company.objects.create(household=self.household, name="Firma")
        self.foreign_company = Company.objects.create(household=self.foreign, name="Obca firma")
        self.base = f"/api/households/{self.household.pk}/"
        self.client = APIClient()
        self.contract_data = {
            "member_id": str(self.member.pk),
            "company_id": str(self.company.pk),
            "name": "Umowa pierwsza",
            "contract_type": "employment",
            "position": "Specjalista",
            "gross_amount": "8500.25",
            "gross_basis": "monthly",
            "currency": "PLN",
            "start_date": "2026-01-01",
            "end_date": None,
        }
        self.other_data = {
            "name": "Świadczenie",
            "category": "benefit",
            "start_date": "2026-01-01",
            "currency": "PLN",
            "frequency": "monthly",
            "is_regular": True,
            "default_monthly_amount": "100.50",
        }

    def request(self, method, path, data=None, *, user=None):
        self.client.force_login(self.owner if user is None else user)
        return getattr(self.client, method)(
            self.base + path, data, format="json", HTTP_HOST="localhost", secure=True
        )

    def create(self, path, data):
        response = self.request("post", path, data)
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_company_dictionary_reuse_archival_and_audit(self):
        company = self.create("companies/", {"name": "Dostawca"})
        self.assertNotEqual(company["id"], str(self.company.pk))
        self.assertEqual(str(company["household_id"]), str(self.household.pk))
        self.assertEqual(
            self.request(
                "patch", f"companies/{company['id']}/", {"name": "Nowa nazwa"}
            ).status_code,
            200,
        )
        self.assertEqual(self.request("get", "companies/?is_active=true").data["count"], 2)
        self.assertEqual(
            self.request("post", f"companies/{company['id']}/archive/", {}).status_code,
            200,
        )
        archived = self.request("get", f"companies/{company['id']}/").data
        self.assertFalse(archived["is_active"])
        self.assertIsNotNone(archived["archived_at"])
        self.assertEqual(self.request("get", "companies/?is_active=false").data["count"], 1)
        self.assertEqual(
            self.request("post", f"companies/{company['id']}/archive/", {}).status_code,
            200,
        )
        self.assertEqual(AuditLog.objects.filter(object_type="company").count(), 3)
        self.assertEqual(
            self.request("patch", f"companies/{company['id']}/", {"name": "Odrzucona"}).status_code,
            400,
        )
        self.assertEqual(self.request("patch", f"companies/{company['id']}/", {}).status_code, 400)
        self.assertEqual(self.request("delete", f"companies/{company['id']}/").status_code, 405)

    def test_contracts_share_company_and_keep_gross_separate(self):
        first = self.create("contracts/", self.contract_data)
        second = self.create("contracts/", {**self.contract_data, "name": "Umowa druga"})
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(first["company"]["id"], str(self.company.pk))
        self.assertEqual(first["gross_amount"], "8500.25")
        self.assertEqual(first["gross_basis"], "monthly")
        source = IncomeSource.objects.get(pk=first["id"])
        self.assertEqual(source.kind, IncomeKind.CONTRACT)
        self.assertIsNone(source.default_monthly_amount)
        self.assertEqual(source.member_id, self.member.pk)
        self.assertEqual(Contract.objects.filter(company=self.company).count(), 2)
        self.assertEqual(self.request("get", "income-sources/").data["count"], 2)
        self.assertEqual(self.request("get", "contracts/").data["count"], 2)
        self.assertEqual(
            self.request("get", f"contracts/?member_id={self.member.pk}").data["count"], 2
        )
        self.assertEqual(self.request("get", "contracts/?member_id=bad").status_code, 400)
        self.assertEqual(AuditLog.objects.filter(object_type="income_source").count(), 2)
        self.assertEqual(
            self.request("patch", f"income-sources/{first['id']}/", {"name": "Błąd"}).status_code,
            409,
        )
        self.assertEqual(
            self.request("post", f"income-sources/{first['id']}/deactivate/", {}).status_code,
            409,
        )

    def test_contract_types_dates_and_amount_validation(self):
        for values in (
            {"contract_type": "other", "other_type_name": "Kontrakt autorski", "position": ""},
            {"contract_type": "mandate", "position": "Konsultant"},
            {"contract_type": "specific_work", "position": "", "gross_basis": "total"},
        ):
            with self.subTest(values=values):
                self.create("contracts/", {**self.contract_data, **values})
        for values in (
            {"contract_type": "other", "other_type_name": ""},
            {"contract_type": "specific_work", "position": "Niedozwolone"},
            {"gross_amount": "-0.01"},
            {"gross_amount": "1.001"},
            {"gross_amount": "NaN"},
            {"gross_basis": "weekly"},
            {"end_date": "2025-01-01"},
            {"currency": "pln"},
            {"company_id": str(self.foreign_company.pk)},
            {"member_id": str(self.foreign_member.pk)},
            {"password": "sekret"},
        ):
            with self.subTest(values=values):
                response = self.request("post", "contracts/", {**self.contract_data, **values})
                self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Contract.objects.count(), 3)
        self.assertEqual(AuditLog.objects.count(), 3)

    def test_contract_edit_requires_current_version(self):
        created = self.create("contracts/", self.contract_data)
        path = f"contracts/{created['id']}/"
        self.assertEqual(self.request("patch", path, {"name": "Bez wersji"}).status_code, 400)
        updated = self.request(
            "patch", path, {"name": "Pierwsza zmiana", "expected_version": created["version"]}
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["version"], created["version"] + 1)
        audit_count = AuditLog.objects.count()
        self.assertEqual(
            self.request(
                "patch", path, {"name": "Stara zmiana", "expected_version": created["version"]}
            ).status_code,
            409,
        )
        self.assertEqual(IncomeSource.objects.get(pk=created["id"]).name, "Pierwsza zmiana")
        self.assertEqual(AuditLog.objects.count(), audit_count)

    def test_other_source_optional_amount_and_one_off_rule(self):
        household_source = self.create(
            "income-sources/", {**self.other_data, "default_monthly_amount": None}
        )
        member_source = self.create(
            "income-sources/", {**self.other_data, "member_id": str(self.member.pk)}
        )
        self.assertIsNone(household_source["member_id"])
        self.assertIsNone(household_source["default_monthly_amount"])
        self.assertEqual(member_source["default_monthly_amount"], "100.50")
        self.assertEqual(member_source["kind"], "other")
        self.assertFalse(Contract.objects.exists())
        self.create(
            "income-sources/",
            {**self.other_data, "frequency": "one_off", "is_regular": False},
        )
        self.assertEqual(
            self.request(
                "post", "income-sources/", {**self.other_data, "frequency": "one_off"}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.request(
                "post", "income-sources/", {**self.other_data, "kind": "contract"}
            ).status_code,
            400,
        )

    def test_conversion_preserves_id_and_audits_previous_value(self):
        old = self.create("income-sources/", self.other_data)
        response = self.request(
            "post",
            f"income-sources/{old['id']}/convert-to-contract/",
            {**self.contract_data, "expected_version": old["version"]},
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], old["id"])
        source = IncomeSource.objects.get(pk=old["id"])
        self.assertEqual(source.kind, IncomeKind.CONTRACT)
        self.assertEqual(source.version, old["version"] + 1)
        self.assertIsNone(source.default_monthly_amount)
        self.assertEqual(source.category, "")
        self.assertEqual(Contract.objects.get(source=source).gross_amount, Decimal("8500.25"))
        entry = AuditLog.objects.filter(action="converted").get()
        self.assertEqual(entry.before["default_monthly_amount"], "100.50")
        self.assertEqual(entry.before["kind"], "other")
        self.assertEqual(entry.after["kind"], "contract")
        self.assertEqual(entry.after["gross_amount"], "8500.25")
        self.assertEqual(
            self.request(
                "post",
                f"income-sources/{old['id']}/convert-to-contract/",
                {**self.contract_data, "expected_version": old["version"]},
            ).status_code,
            409,
        )
        self.assertEqual(IncomeSource.objects.count(), 1)
        self.assertEqual(Contract.objects.count(), 1)

    def test_stale_version_and_failed_conversion_leave_other_intact(self):
        old = self.create("income-sources/", self.other_data)
        path = f"income-sources/{old['id']}/convert-to-contract/"
        self.assertEqual(
            self.request(
                "patch",
                f"income-sources/{old['id']}/",
                {"name": "Nowa", "expected_version": old["version"]},
            ).data["version"],
            old["version"] + 1,
        )
        before_count = AuditLog.objects.count()
        self.assertEqual(
            self.request("post", path, {**self.contract_data, "expected_version": 1}).status_code,
            409,
        )
        self.assertEqual(
            self.request(
                "post",
                path,
                {**self.contract_data, "expected_version": 2, "company_id": str(uuid4())},
            ).status_code,
            400,
        )
        self.assertEqual(AuditLog.objects.count(), before_count)
        self.assertEqual(IncomeSource.objects.get(pk=old["id"]).kind, IncomeKind.OTHER)
        self.assertFalse(Contract.objects.exists())

    def test_archived_links_remain_readable_but_cannot_be_new(self):
        first = self.create("contracts/", self.contract_data)
        self.assertEqual(
            self.request("post", f"companies/{self.company.pk}/archive/", {}).status_code,
            200,
        )
        self.assertEqual(
            self.request("post", f"members/{self.member.pk}/deactivate/", {}).status_code,
            200,
        )
        self.assertEqual(self.request("get", f"contracts/{first['id']}/").status_code, 200)
        self.assertEqual(self.request("post", "contracts/", self.contract_data).status_code, 400)
        self.assertEqual(
            self.request(
                "patch",
                f"contracts/{first['id']}/",
                {"name": "Nowa nazwa", "expected_version": first["version"]},
            ).status_code,
            200,
        )
        path = f"contracts/{first['id']}/archive/"
        self.assertEqual(self.request("post", path, {}).status_code, 200)
        count = AuditLog.objects.count()
        self.assertEqual(self.request("post", path, {}).status_code, 200)
        self.assertEqual(AuditLog.objects.count(), count)
        self.assertEqual(
            self.request(
                "patch",
                f"contracts/{first['id']}/",
                {"name": "Błąd", "expected_version": first["version"] + 2},
            ).status_code,
            400,
        )

    def test_roles_foreign_ids_anonymous_and_csrf(self):
        foreign_path = f"companies/{self.foreign_company.pk}/"
        old = self.create("income-sources/", self.other_data)
        for user in (self.member_user, self.viewer):
            self.assertEqual(self.request("get", "companies/", user=user).status_code, 200)
            self.assertEqual(self.request("get", "contracts/", user=user).status_code, 200)
            self.assertEqual(
                self.request("post", "companies/", {"name": "Nie"}, user=user).status_code,
                403,
            )
            self.assertEqual(
                self.request("post", "contracts/", self.contract_data, user=user).status_code,
                403,
            )
            self.assertEqual(
                self.request(
                    "post",
                    f"income-sources/{old['id']}/convert-to-contract/",
                    {**self.contract_data, "expected_version": old["version"]},
                    user=user,
                ).status_code,
                403,
            )
        self.assertEqual(
            self.request("post", "companies/", {"name": "Tak"}, user=self.admin).status_code,
            201,
        )
        self.assertEqual(
            self.request("post", "contracts/", self.contract_data, user=self.admin).status_code,
            201,
        )
        self.assertEqual(self.request("get", foreign_path).status_code, 404)
        self.assertEqual(self.request("patch", foreign_path, {"name": "Nie"}).status_code, 404)
        self.assertEqual(
            self.request(
                "post",
                "contracts/",
                {**self.contract_data, "company_id": str(self.foreign_company.pk)},
            ).status_code,
            400,
        )
        foreign_contract = Contract.objects.create(
            source=IncomeSource.objects.create(
                household=self.foreign,
                member=self.foreign_member,
                name="Obca umowa",
                kind=IncomeKind.CONTRACT,
                category="",
                frequency="",
                is_regular=None,
                start_date="2026-01-01",
                currency="PLN",
            ),
            company=self.foreign_company,
            contract_type="employment",
            gross_amount=Decimal("10.00"),
            gross_basis="monthly",
        )
        self.assertEqual(self.request("get", f"contracts/{foreign_contract.pk}/").status_code, 404)
        self.assertEqual(
            self.request("patch", f"contracts/{foreign_contract.pk}/", {"name": "Nie"}).status_code,
            404,
        )
        self.client.force_login(self.outsider)
        self.assertEqual(
            self.client.get(self.base + "companies/", HTTP_HOST="localhost").status_code, 404
        )
        anonymous = APIClient()
        self.assertEqual(
            anonymous.get(self.base + "companies/", HTTP_HOST="localhost").status_code, 403
        )
        csrf_client = APIClient(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        self.assertEqual(
            csrf_client.post(
                self.base + "companies/",
                {"name": "Brak CSRF"},
                format="json",
                HTTP_HOST="localhost",
                secure=True,
            ).status_code,
            403,
        )

    def test_audit_failure_rolls_back_company_contract_and_conversion(self):
        old = self.create("income-sources/", self.other_data)
        attempts = (
            ("companies/", {"name": "Niepowodzenie"}),
            ("contracts/", self.contract_data),
            (
                f"income-sources/{old['id']}/convert-to-contract/",
                {**self.contract_data, "expected_version": old["version"]},
            ),
        )
        for path, payload in attempts:
            with (
                self.subTest(path=path),
                patch(
                    "households.record_services.AuditLog.objects.create", side_effect=IntegrityError
                ),
                self.assertRaises(IntegrityError),
            ):
                self.request("post", path, payload)
        self.assertEqual(Company.objects.count(), 2)
        self.assertEqual(Contract.objects.count(), 0)
        self.assertEqual(IncomeSource.objects.get(pk=old["id"]).kind, IncomeKind.OTHER)
        self.assertEqual(AuditLog.objects.count(), 1)
