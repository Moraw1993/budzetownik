from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from accounts.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from households.family_income_services import write_contract
from households.income_services import create_income_record
from households.models import (
    AuditLog,
    Company,
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


class MonthlyIncomeAcceptanceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="income-acceptance-owner")
        self.admin = User.objects.create_user(username="income-acceptance-admin")
        self.member_user = User.objects.create_user(username="income-acceptance-member")
        self.viewer = User.objects.create_user(username="income-acceptance-viewer")
        self.household = create_household(user=self.owner, name="Dom").household
        Membership.objects.create(
            household=self.household, user=self.admin, role=Role.ADMINISTRATOR
        )
        Membership.objects.create(household=self.household, user=self.member_user, role=Role.MEMBER)
        Membership.objects.create(household=self.household, user=self.viewer, role=Role.VIEWER)
        self.member = HouseholdMember.objects.create(household=self.household, display_name="Arek")
        self.year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2042
        )
        self.month = self.year.months.get(month_number=1)
        self.inactive_month = self.year.months.get(month_number=2)
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="activate",
        )
        self.source = self.create_source(member=self.member)
        self.path = (
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/"
            f"months/{self.month.pk}/incomes/"
        )

    def create_source(
        self,
        *,
        household=None,
        member=None,
        name="Wynagrodzenie",
        start_date=date(2040, 1, 1),
        end_date=None,
        frequency=IncomeFrequency.MONTHLY,
        is_regular=True,
    ):
        return IncomeSource.objects.create(
            household=household or self.household,
            member=member,
            name=name,
            category="salary",
            payer="",
            start_date=start_date,
            end_date=end_date,
            currency="PLN",
            frequency=frequency,
            is_regular=is_regular,
        )

    def request(self, method, path, data=None, *, user=None, key=None, client=None, **headers):
        client = self.client_for(self.owner if user is None else user) if client is None else client
        request_headers = {"HTTP_HOST": "localhost", **headers}
        if key is not None:
            request_headers["HTTP_IDEMPOTENCY_KEY"] = str(key)
        return getattr(client, method)(path, data, format="json", secure=True, **request_headers)

    def client_for(self, user=None, *, enforce_csrf_checks=False):
        client = APIClient(enforce_csrf_checks=enforce_csrf_checks)
        if user is not None:
            client.force_login(user)
        return client

    def income_data(self, **overrides):
        return {
            "member_id": str(self.member.pk),
            "source_id": str(self.source.pk),
            "amount": "8000",
            "currency": "PLN",
            "receipt_date": "2041-12-31",
            **overrides,
        }

    def create_foreign_income(self):
        foreign_owner = User.objects.create_user(username="foreign-income-owner")
        foreign_household = create_household(user=foreign_owner, name="Obcy dom").household
        foreign_member = HouseholdMember.objects.create(
            household=foreign_household, display_name="Obca osoba"
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
        foreign_source = self.create_source(
            household=foreign_household,
            member=foreign_member,
            name="Obce źródło",
        )
        result = create_income_record(
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
        return foreign_owner, foreign_household, foreign_year, foreign_month, result.body

    def test_dictionary_owner_change_and_conversion_preserve_historical_income_links(self):
        second_member = HouseholdMember.objects.create(
            household=self.household, display_name="Dominika"
        )
        created = self.request("post", self.path, self.income_data(), key=uuid4())
        expected_recipient = {"kind": "member", "id": str(self.member.pk), "label": "Arek"}
        expected_source = {
            "id": str(self.source.pk),
            "name": "Wynagrodzenie",
            "kind": IncomeKind.OTHER,
            "version": 1,
            "contract": None,
        }
        self.assertEqual(created.status_code, 201, created.data)

        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=IncomeSource,
            record_id=self.source.pk,
            data={
                "member_id": second_member.pk,
                "name": "Wynagrodzenie Dominiki",
                "expected_version": 1,
            },
        )
        record_audit_count = AuditLog.objects.filter(object_type="income_record").count()
        mismatched_source_assignment = self.request(
            "post", self.path, self.income_data(), key=uuid4()
        )
        self.assertEqual(mismatched_source_assignment.status_code, 400)
        self.assertEqual(IncomeRecord.objects.count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), 1)
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_record").count(), record_audit_count
        )
        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=HouseholdMember,
            record_id=self.member.pk,
            data={},
            deactivate=True,
        )
        historical_detail = f"{self.path}{created.data['id']}/"
        historical_patch = self.request(
            "patch",
            historical_detail,
            {"amount": "8100", "expected_version": 1},
        )
        historical_get = self.request("get", historical_detail)
        update_audit = AuditLog.objects.get(
            object_type="income_record", object_id=created.data["id"], action="updated"
        )

        self.assertEqual(historical_patch.status_code, 200, historical_patch.data)
        self.assertEqual(historical_get.status_code, 200)
        self.assertEqual(historical_patch.data["recipient_snapshot"], expected_recipient)
        self.assertEqual(historical_patch.data["source_snapshot"], expected_source)
        self.assertEqual(historical_get.data["recipient_snapshot"], expected_recipient)
        self.assertEqual(historical_get.data["source_snapshot"], expected_source)
        self.assertEqual(update_audit.before["recipient_snapshot"], expected_recipient)
        self.assertEqual(update_audit.after["recipient_snapshot"], expected_recipient)
        self.assertEqual(update_audit.before["source_snapshot"], expected_source)
        self.assertEqual(update_audit.after["source_snapshot"], expected_source)
        self.assertEqual(IncomeSource.objects.get(pk=self.source.pk).member_id, second_member.pk)
        self.assertFalse(HouseholdMember.objects.get(pk=self.member.pk).is_active)

        company = Company.objects.create(household=self.household, name="Nowy pracodawca")
        write_contract(
            user=self.owner,
            household_id=self.household.pk,
            source_id=self.source.pk,
            conversion=True,
            data={
                "expected_version": 2,
                "member_id": second_member.pk,
                "name": "Umowa przekształcona",
                "start_date": date(2040, 1, 1),
                "currency": "PLN",
                "company_id": company.pk,
                "contract_type": ContractType.EMPLOYMENT,
                "gross_amount": Decimal("10000.00"),
                "gross_basis": GrossBasis.MONTHLY,
            },
        )
        converted_source = IncomeSource.objects.get(pk=self.source.pk)
        after_conversion = self.request("get", historical_detail)

        self.assertEqual(converted_source.kind, IncomeKind.CONTRACT)
        self.assertEqual(converted_source.pk, self.source.pk)
        self.assertEqual(after_conversion.data["source_snapshot"], expected_source)
        self.assertEqual(after_conversion.data["recipient_snapshot"], expected_recipient)

        replacement_source = self.create_source(member=second_member, name="Drugie źródło")
        audit_count = AuditLog.objects.filter(object_type="income_record").count()
        archived_recipient_change = self.request(
            "patch",
            historical_detail,
            {"source_id": str(replacement_source.pk), "expected_version": 2},
        )
        new_assignment_to_archived_recipient = self.request(
            "post",
            self.path,
            self.income_data(member_id=str(self.member.pk), source_id=str(converted_source.pk)),
            key=uuid4(),
        )
        record = IncomeRecord.objects.get(pk=created.data["id"])

        self.assertEqual(archived_recipient_change.status_code, 404)
        self.assertEqual(new_assignment_to_archived_recipient.status_code, 404)
        self.assertEqual(record.member_id, self.member.pk)
        self.assertEqual(record.income_source_id, self.source.pk)
        self.assertEqual(record.amount, Decimal("8100.00"))
        self.assertEqual(record.version, 2)
        self.assertIsNone(record.deleted_at)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), audit_count)
        self.assertEqual(IncomeRecord.objects.count(), 1)

    def test_anonymous_requests_and_missing_or_invalid_csrf_block_all_income_mutations(self):
        created = self.request("post", self.path, self.income_data(), key=uuid4())
        detail = f"{self.path}{created.data['id']}/"
        options_path = self.path.replace("incomes/", "income-source-options/")
        month_totals_path = self.path.replace("incomes/", "income-totals/")
        year_totals_path = (
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/income-totals/"
        )
        record_count = IncomeRecord.objects.count()
        audit_count = AuditLog.objects.filter(object_type="income_record").count()
        key_count = IncomeCreateIdempotency.objects.count()
        anonymous = self.client_for()
        anonymous_responses = (
            self.request("get", self.path, client=anonymous),
            self.request("get", detail, client=anonymous),
            self.request("get", f"{options_path}?member_id={self.member.pk}", client=anonymous),
            self.request("get", month_totals_path, client=anonymous),
            self.request("get", year_totals_path, client=anonymous),
            self.request("post", self.path, self.income_data(), key=uuid4(), client=anonymous),
            self.request(
                "patch", detail, {"amount": "9000", "expected_version": 1}, client=anonymous
            ),
            self.request("delete", detail, {"expected_version": 1}, client=anonymous),
        )
        self.assertTrue(all(response.status_code == 403 for response in anonymous_responses))
        self.assertEqual(IncomeRecord.objects.count(), record_count)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), audit_count)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), key_count)

        csrf_client = self.client_for(self.owner, enforce_csrf_checks=True)
        missing_patch = self.request(
            "patch", detail, {"amount": "9000", "expected_version": 1}, client=csrf_client
        )
        csrf_client.cookies["csrftoken"] = "a" * 32
        invalid_delete = self.request(
            "delete",
            detail,
            {"expected_version": 1},
            client=csrf_client,
            HTTP_X_CSRFTOKEN="b" * 32,
            HTTP_REFERER="https://localhost/",
        )
        record = IncomeRecord.objects.get(pk=created.data["id"])

        self.assertEqual(missing_patch.status_code, 403)
        self.assertEqual(invalid_delete.status_code, 403)
        self.assertEqual(record.amount, Decimal("8000.00"))
        self.assertEqual(record.version, 1)
        self.assertIsNone(record.deleted_at)
        self.assertEqual(AuditLog.objects.filter(object_type="income_record").count(), audit_count)
        self.assertEqual(IncomeCreateIdempotency.objects.count(), key_count)
        self.assertEqual(IncomeRecord.objects.count(), record_count)

    def test_roles_and_tenant_scope_cover_source_options_and_month_year_totals(self):
        self.create_source(member=None, name="Świadczenie")
        options_path = self.path.replace("incomes/", "income-source-options/")
        month_totals_path = self.path.replace("incomes/", "income-totals/")
        year_totals_path = (
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/income-totals/"
        )

        for user in (self.owner, self.admin, self.member_user, self.viewer):
            with self.subTest(role=Membership.objects.get(user=user).role):
                options = self.request(
                    "get", f"{options_path}?member_id={self.member.pk}", user=user
                )
                month_totals = self.request("get", month_totals_path, user=user)
                year_totals = self.request("get", year_totals_path, user=user)
                self.assertEqual(options.status_code, 200)
                self.assertEqual(month_totals.status_code, 200)
                self.assertEqual(year_totals.status_code, 200)

        foreign_owner = User.objects.create_user(username="auxiliary-foreign-owner")
        foreign_household = create_household(user=foreign_owner, name="Obcy dom").household
        foreign_member = HouseholdMember.objects.create(
            household=foreign_household, display_name="Obca osoba"
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
        mixed_responses = (
            self.request("get", f"{options_path}?member_id={foreign_member.pk}"),
            self.request("get", f"{options_path}?member_id={uuid4()}"),
            self.request(
                "get", month_totals_path.replace(str(self.month.pk), str(foreign_month.pk))
            ),
            self.request("get", year_totals_path.replace(str(self.year.pk), str(foreign_year.pk))),
            self.request(
                "get",
                f"/api/households/{foreign_household.pk}/accounting-years/{foreign_year.pk}/"
                f"months/{foreign_month.pk}/income-totals/",
            ),
        )

        for response in mixed_responses:
            with self.subTest(status=response.status_code, data=response.data):
                self.assertEqual(response.status_code, 404)

    def test_foreign_income_ids_stay_hidden_under_inactive_and_closed_period_paths(self):
        _, _, _, _, foreign_income = self.create_foreign_income()
        foreign_id = foreign_income["id"]
        inactive_path = self.path.replace(str(self.month.pk), str(self.inactive_month.pk))
        own_closed_path = self.path
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )
        own_audit_count = AuditLog.objects.filter(household=self.household).count()
        foreign_audit_count = AuditLog.objects.exclude(household=self.household).count()

        for path in (inactive_path, own_closed_path):
            for method, data in (
                ("get", None),
                ("patch", {"amount": "9000", "expected_version": 1}),
                ("delete", {"expected_version": 1}),
            ):
                response = self.request(method, f"{path}{foreign_id}/", data)
                with self.subTest(path=path, method=method):
                    self.assertEqual(response.status_code, 404, response.data)

        self.assertEqual(AuditLog.objects.filter(household=self.household).count(), own_audit_count)
        self.assertEqual(
            AuditLog.objects.exclude(household=self.household).count(), foreign_audit_count
        )
        foreign_record = IncomeRecord.objects.get(pk=foreign_id)
        self.assertEqual(foreign_record.amount, Decimal("8000.00"))
        self.assertEqual(foreign_record.version, 1)
        self.assertIsNone(foreign_record.deleted_at)

    def test_canonical_retry_changed_payload_and_actor_scoped_key(self):
        household_source = self.create_source(member=None, name="Odsetki")
        key = uuid4()
        first_payload = {
            "source_id": str(household_source.pk).upper(),
            "amount": "8000",
            "currency": "PLN",
            "receipt_date": "2041-12-31",
        }
        first = self.request("post", self.path, first_payload, key=key)
        canonical_replay = self.request(
            "post",
            self.path,
            {
                **first_payload,
                "source_id": str(household_source.pk),
                "member_id": None,
                "amount": "8000.00",
            },
            key=key,
        )
        changed_payload = self.request(
            "post", self.path, {**first_payload, "amount": "9000"}, key=key
        )
        actor_scoped = self.request("post", self.path, first_payload, user=self.admin, key=key)
        audits = AuditLog.objects.filter(object_type="income_record", action="created")

        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(canonical_replay.status_code, 201)
        self.assertEqual(canonical_replay.data, first.data)
        self.assertEqual(changed_payload.status_code, 409)
        self.assertEqual(changed_payload.data["code"], "idempotency_conflict")
        self.assertTrue(changed_payload.data["detail"])
        self.assertEqual(actor_scoped.status_code, 201, actor_scoped.data)
        self.assertNotEqual(actor_scoped.data["id"], first.data["id"])
        self.assertEqual(IncomeRecord.objects.count(), 2)
        self.assertEqual(IncomeCreateIdempotency.objects.filter(client_key=key).count(), 2)
        self.assertEqual(audits.count(), 2)

    def test_source_options_empty_archived_member_and_two_one_off_receipts(self):
        empty_member = HouseholdMember.objects.create(
            household=self.household, display_name="Bez źródła"
        )
        options_path = self.path.replace("incomes/", "income-source-options/")
        empty_options = self.request("get", f"{options_path}?member_id={empty_member.pk}")
        inactive_options_path = options_path.replace(
            str(self.month.pk), str(self.inactive_month.pk)
        )
        inactive_options = self.request(
            "get", f"{inactive_options_path}?member_id={self.member.pk}"
        )
        write_record(
            user=self.owner,
            household_id=self.household.pk,
            model=HouseholdMember,
            record_id=empty_member.pk,
            data={},
            deactivate=True,
        )
        archived_member_options = self.request("get", f"{options_path}?member_id={empty_member.pk}")
        one_off = self.create_source(
            member=self.member,
            name="Praca jednorazowa",
            frequency=IncomeFrequency.ONE_OFF,
            is_regular=False,
        )
        first = self.request(
            "post", self.path, self.income_data(source_id=str(one_off.pk), amount="35"), key=uuid4()
        )
        second = self.request(
            "post", self.path, self.income_data(source_id=str(one_off.pk), amount="45"), key=uuid4()
        )

        self.assertEqual(empty_options.status_code, 200)
        self.assertEqual(empty_options.data["count"], 0)
        self.assertEqual(archived_member_options.status_code, 404)
        self.assertEqual(inactive_options.status_code, 409)
        self.assertEqual(inactive_options.data["code"], "income_period_not_active")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)
        self.assertEqual(IncomeRecord.objects.filter(income_source=one_off).count(), 2)

    def test_income_list_paginates_orders_excludes_deleted_and_remains_readable_when_closed(self):
        records = []
        for index in range(52):
            records.append(
                IncomeRecord(
                    household=self.household,
                    accounting_month=self.month,
                    member=self.member,
                    income_source=self.source,
                    amount=Decimal("0.01"),
                    currency="PLN",
                    receipt_date=date(2042, 1, index % 31 + 1),
                    recipient_snapshot={
                        "kind": "member",
                        "id": str(self.member.pk),
                        "label": "Arek",
                    },
                    source_snapshot={
                        "id": str(self.source.pk),
                        "name": self.source.name,
                        "kind": IncomeKind.OTHER,
                        "version": 1,
                        "contract": None,
                    },
                    deleted_at=timezone.now() if index == 0 else None,
                    deleted_by=self.owner if index == 0 else None,
                    version=2 if index == 0 else 1,
                )
            )
        IncomeRecord.objects.bulk_create(records)
        tied_records = list(
            IncomeRecord.objects.filter(
                household=self.household,
                accounting_month=self.month,
                deleted_at__isnull=True,
            ).order_by("id")[:2]
        )
        tied_ids = [record.pk for record in tied_records]
        tied_created_at = timezone.now() - timedelta(days=1)
        IncomeRecord.objects.filter(pk__in=tied_ids).update(
            receipt_date=date(2042, 1, 1),
            created_at=tied_created_at,
        )
        active_records = list(
            IncomeRecord.objects.filter(
                household=self.household,
                accounting_month=self.month,
                deleted_at__isnull=True,
            ).order_by("receipt_date", "created_at", "id")
        )
        tied_active_ids = [record.pk for record in active_records if record.pk in tied_ids]

        first_page = self.request("get", self.path)
        second_page = self.request("get", f"{self.path}?page=2")
        deleted = IncomeRecord.objects.get(
            household=self.household, accounting_month=self.month, deleted_at__isnull=False
        )
        deleted_detail = self.request("get", f"{self.path}{deleted.pk}/")
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )
        closed_list = self.request("get", self.path)
        closed_totals = self.request("get", self.path.replace("incomes/", "income-totals/"))

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 51)
        self.assertEqual(len(first_page.data["results"]), 50)
        self.assertIsNotNone(first_page.data["next"])
        self.assertEqual(len(second_page.data["results"]), 1)
        returned_ids = [
            item["id"] for item in first_page.data["results"] + second_page.data["results"]
        ]
        self.assertEqual(returned_ids, [str(record.pk) for record in active_records])
        self.assertEqual(tied_active_ids, tied_ids)
        self.assertEqual(deleted_detail.status_code, 404)
        self.assertEqual(closed_list.status_code, 200)
        self.assertEqual(closed_list.data["count"], 51)
        self.assertEqual(closed_totals.data, {"totals": [{"currency": "PLN", "amount": "0.51"}]})

    def test_decimal_date_and_currency_boundaries_report_exact_fields(self):
        minimum = self.request("post", self.path, self.income_data(amount="0.01"), key=uuid4())
        future_date = timezone.localdate() + timedelta(days=1)
        future_receipt = self.request(
            "post",
            self.path,
            self.income_data(receipt_date=future_date.isoformat()),
            key=uuid4(),
        )
        invalid_inputs = (
            ("amount", {"amount": "0"}),
            ("amount", {"amount": "-1"}),
            ("amount", {"amount": "0.001"}),
            ("amount", {"amount": "10000000000000000.00"}),
            ("currency", {"currency": "pln"}),
            ("currency", {"currency": "PL"}),
            ("currency", {"currency": "1$!"}),
            ("receipt_date", {"receipt_date": "2044-02-30"}),
        )
        responses = [
            (field, self.request("post", self.path, self.income_data(**override), key=uuid4()))
            for field, override in invalid_inputs
        ]

        self.assertEqual(minimum.status_code, 201, minimum.data)
        self.assertEqual(future_receipt.status_code, 201, future_receipt.data)
        self.assertEqual(future_receipt.data["receipt_date"], future_date.isoformat())
        for field, response in responses:
            with self.subTest(field=field, data=response.data):
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
