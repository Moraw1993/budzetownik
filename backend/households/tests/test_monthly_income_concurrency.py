from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from datetime import date
from decimal import Decimal
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch
from uuid import uuid4

from accounts.models import User
from django.db import connection, connections
from django.test import TransactionTestCase

from households import income_services, period_services
from households.exceptions import IdempotencyConflict, IncomePeriodConflict
from households.income_services import (
    create_income_record,
    delete_income_record,
    update_income_record,
)
from households.models import (
    AuditLog,
    HouseholdMember,
    IncomeCreateIdempotency,
    IncomeFrequency,
    IncomeRecord,
    IncomeSource,
)
from households.period_services import create_accounting_year, transition_accounting_month
from households.services import create_household


class MonthlyIncomeConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="income-concurrent-owner")
        self.household = create_household(user=self.owner, name="Dom").household
        self.member = HouseholdMember.objects.create(household=self.household, display_name="Arek")
        self.year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2044
        )
        self.source = IncomeSource.objects.create(
            household=self.household,
            member=self.member,
            name="Wynagrodzenie",
            category="salary",
            payer="",
            start_date=date(2040, 1, 1),
            currency="PLN",
            frequency=IncomeFrequency.MONTHLY,
            is_regular=True,
        )

    def activate_month(self, number):
        month = self.year.months.get(month_number=number)
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=month.pk,
            operation="activate",
        )
        return month

    def create_income(self, month):
        result = create_income_record(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=month.pk,
            data={
                "member_id": self.member.pk,
                "source_id": self.source.pk,
                "amount": Decimal("8000.00"),
                "currency": "PLN",
                "receipt_date": date(2044, month.month_number, 15),
            },
            idempotency_key=uuid4(),
        )
        return IncomeRecord.objects.get(pk=result.body["id"])

    @staticmethod
    def thread_operation(operation):
        try:
            return operation()
        finally:
            connections.close_all()

    def assert_backend_waiting_on_lock(self, backend_pid):
        deadline = monotonic() + 10
        while monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s",
                    [backend_pid],
                )
                row = cursor.fetchone()
            if row is not None and row[0] == "Lock":
                return
            sleep(0.01)
        self.fail(f"PostgreSQL backend {backend_pid} never waited on a lock")

    def run_idempotency_race(self, first_amount, second_amount):
        month = self.activate_month(7 if first_amount == second_amount else 8)
        key = uuid4()
        first_paused = Event()
        allow_first = Event()
        second_attempted = Event()
        second_backend_pid = []
        original_audit = income_services.write_audit
        original_lock = income_services.locked_access

        def pause_first_audit(**kwargs):
            first_paused.set()
            if not allow_first.wait(timeout=10):
                raise TimeoutError("Timed out waiting to release the first create transaction")
            return original_audit(**kwargs)

        @contextmanager
        def observe_second_lock(**kwargs):
            if first_paused.is_set():
                with connections["default"].cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    second_backend_pid.append(cursor.fetchone()[0])
                second_attempted.set()
            with original_lock(**kwargs) as membership:
                yield membership

        def create(amount):
            try:
                return create_income_record(
                    user=self.owner,
                    household_id=self.household.pk,
                    year_id=self.year.pk,
                    month_id=month.pk,
                    data={
                        "member_id": self.member.pk,
                        "source_id": self.source.pk,
                        "amount": Decimal(amount),
                        "currency": "PLN",
                        "receipt_date": date(2044, month.month_number, 15),
                    },
                    idempotency_key=key,
                )
            except IdempotencyConflict:
                return "idempotency_conflict"

        with ExitStack() as stack:
            stack.enter_context(
                patch("households.income_services.write_audit", side_effect=pause_first_audit)
            )
            stack.enter_context(
                patch("households.income_services.locked_access", side_effect=observe_second_lock)
            )
            pool = stack.enter_context(ThreadPoolExecutor(max_workers=2))
            first_future = pool.submit(self.thread_operation, lambda: create(first_amount))
            self.assertTrue(first_paused.wait(timeout=10))
            second_future = pool.submit(self.thread_operation, lambda: create(second_amount))
            self.assertTrue(second_attempted.wait(timeout=10))
            self.assert_backend_waiting_on_lock(second_backend_pid[0])
            allow_first.set()
            results = [first_future.result(timeout=20), second_future.result(timeout=20)]
        return month, key, results

    def write_operation(self, action, month, record=None):
        if action == "create":
            return lambda: create_income_record(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=month.pk,
                data={
                    "member_id": self.member.pk,
                    "source_id": self.source.pk,
                    "amount": Decimal("8000.00"),
                    "currency": "PLN",
                    "receipt_date": date(2044, month.month_number, 15),
                },
                idempotency_key=uuid4(),
            )
        if action == "patch":
            return lambda: update_income_record(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=month.pk,
                income_id=record.pk,
                data={"expected_version": 1, "amount": Decimal("9000.00")},
            )
        return lambda: delete_income_record(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=month.pk,
            income_id=record.pk,
            expected_version=1,
        )

    def run_close_first(self, action, month, record):
        close_paused = Event()
        allow_close = Event()
        write_attempted = Event()
        write_backend_pid = []
        original_audit = period_services.write_audit
        original_lock = income_services.locked_access

        def pause_close_audit(**kwargs):
            close_paused.set()
            if not allow_close.wait(timeout=10):
                raise TimeoutError("Timed out waiting to release the close transaction")
            return original_audit(**kwargs)

        @contextmanager
        def observe_income_lock(**kwargs):
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                write_backend_pid.append(cursor.fetchone()[0])
            write_attempted.set()
            with original_lock(**kwargs) as membership:
                yield membership

        def close_month():
            return transition_accounting_month(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=month.pk,
                operation="close",
            )

        def write_income():
            try:
                return self.write_operation(action, month, record)()
            except IncomePeriodConflict:
                return "period_conflict"

        with ExitStack() as stack:
            stack.enter_context(
                patch("households.period_services.write_audit", side_effect=pause_close_audit)
            )
            stack.enter_context(
                patch("households.income_services.locked_access", side_effect=observe_income_lock)
            )
            pool = stack.enter_context(ThreadPoolExecutor(max_workers=2))
            close_future = pool.submit(self.thread_operation, close_month)
            self.assertTrue(close_paused.wait(timeout=10))
            write_future = pool.submit(self.thread_operation, write_income)
            self.assertTrue(write_attempted.wait(timeout=10))
            self.assert_backend_waiting_on_lock(write_backend_pid[0])
            allow_close.set()
            close_future.result(timeout=20)
            write_result = write_future.result(timeout=20)
        self.assertEqual(write_result, "period_conflict")

    def run_write_first(self, action, month, record):
        write_paused = Event()
        allow_write = Event()
        close_attempted = Event()
        close_backend_pid = []
        original_audit = income_services.write_audit
        original_lock = period_services.locked_access

        def pause_write_audit(**kwargs):
            write_paused.set()
            if not allow_write.wait(timeout=10):
                raise TimeoutError("Timed out waiting to release the income transaction")
            return original_audit(**kwargs)

        @contextmanager
        def observe_close_lock(**kwargs):
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                close_backend_pid.append(cursor.fetchone()[0])
            close_attempted.set()
            with original_lock(**kwargs) as membership:
                yield membership

        def write_income():
            return self.write_operation(action, month, record)()

        def close_month():
            return transition_accounting_month(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=month.pk,
                operation="close",
            )

        with ExitStack() as stack:
            stack.enter_context(
                patch("households.income_services.write_audit", side_effect=pause_write_audit)
            )
            stack.enter_context(
                patch("households.period_services.locked_access", side_effect=observe_close_lock)
            )
            pool = stack.enter_context(ThreadPoolExecutor(max_workers=2))
            write_future = pool.submit(self.thread_operation, write_income)
            self.assertTrue(write_paused.wait(timeout=10))
            close_future = pool.submit(self.thread_operation, close_month)
            self.assertTrue(close_attempted.wait(timeout=10))
            self.assert_backend_waiting_on_lock(close_backend_pid[0])
            allow_write.set()
            write_result = write_future.result(timeout=20)
            close_future.result(timeout=20)
        return write_result

    def test_close_first_rejects_create_patch_and_delete_after_waiting(self):
        for number, action in enumerate(("create", "patch", "delete"), start=1):
            with self.subTest(action=action):
                month = self.activate_month(number)
                record = None if action == "create" else self.create_income(month)
                self.run_close_first(action, month, record)
                self.assertEqual(month.__class__.objects.get(pk=month.pk).state, "closed")
                if action == "create":
                    self.assertFalse(IncomeRecord.objects.filter(accounting_month=month).exists())
                    self.assertTrue(
                        AuditLog.objects.filter(
                            object_type="accounting_month", object_id=month.pk, action="closed"
                        ).exists()
                    )
                else:
                    record.refresh_from_db()
                    self.assertEqual(record.version, 1)
                    self.assertIsNone(record.deleted_at)

    def test_write_first_commits_create_patch_and_delete_before_close(self):
        for number, action in enumerate(("create", "patch", "delete"), start=4):
            with self.subTest(action=action):
                month = self.activate_month(number)
                record = None if action == "create" else self.create_income(month)
                result = self.run_write_first(action, month, record)
                self.assertEqual(month.__class__.objects.get(pk=month.pk).state, "closed")
                if action == "create":
                    self.assertTrue(
                        IncomeRecord.objects.filter(
                            accounting_month=month, version=1, deleted_at__isnull=True
                        ).exists()
                    )
                elif action == "patch":
                    result.refresh_from_db()
                    self.assertEqual(result.amount, Decimal("9000.00"))
                    self.assertEqual(result.version, 2)
                else:
                    result.refresh_from_db()
                    self.assertIsNotNone(result.deleted_at)
                    self.assertEqual(result.version, 2)

    def test_concurrent_same_key_same_payload_replays_one_created_response(self):
        month, key, results = self.run_idempotency_race("8000.00", "8000.00")
        record = IncomeRecord.objects.get(accounting_month=month)
        key_record = IncomeCreateIdempotency.objects.get(
            household=self.household,
            actor=self.owner,
            operation="income.create",
            client_key=key,
        )
        created_audit = AuditLog.objects.get(
            household=self.household,
            object_type="income_record",
            object_id=record.pk,
            action="created",
        )

        self.assertEqual([result.status_code for result in results], [201, 201])
        self.assertEqual(results[0].body, results[1].body)
        self.assertEqual(IncomeRecord.objects.filter(accounting_month=month).count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.filter(client_key=key).count(), 1)
        self.assertEqual(created_audit.before, None)
        self.assertEqual(created_audit.after["amount"], "8000.00")
        self.assertEqual(key_record.income_record_id, record.pk)
        self.assertEqual(key_record.response_status, 201)
        self.assertEqual(key_record.response_body, results[0].body)
        self.assertEqual(record.version, 1)

    def test_concurrent_same_key_different_payload_conflicts_without_partial_write(self):
        month, key, results = self.run_idempotency_race("8000.00", "9000.00")
        record = IncomeRecord.objects.get(accounting_month=month)
        key_record = IncomeCreateIdempotency.objects.get(
            household=self.household,
            actor=self.owner,
            operation="income.create",
            client_key=key,
        )
        created_audit = AuditLog.objects.get(
            household=self.household,
            object_type="income_record",
            object_id=record.pk,
            action="created",
        )

        self.assertEqual(results[0].status_code, 201)
        self.assertEqual(results[1], "idempotency_conflict")
        self.assertEqual(IncomeRecord.objects.filter(accounting_month=month).count(), 1)
        self.assertEqual(IncomeCreateIdempotency.objects.filter(client_key=key).count(), 1)
        self.assertEqual(record.amount, Decimal("8000.00"))
        self.assertEqual(key_record.income_record_id, record.pk)
        self.assertEqual(key_record.response_status, 201)
        self.assertEqual(key_record.response_body, results[0].body)
        self.assertEqual(record.version, 1)
        self.assertEqual(key_record.response_body["amount"], "8000.00")
        self.assertEqual(created_audit.after["amount"], "8000.00")
        self.assertEqual(
            AuditLog.objects.filter(
                household=self.household,
                object_type="income_record",
                action="created",
            ).count(),
            1,
        )
