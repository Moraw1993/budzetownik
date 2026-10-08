import hashlib
import json
import multiprocessing
import os
import struct
import tempfile
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadhandler import StopUpload
from django.db import DatabaseError, connections
from django.db.models.query import QuerySet
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient

from households.attachment_services import remove_income_attachment
from households.attachment_storage import (
    create_claim,
    release_batch_lock,
    storage_path,
    write_manifest,
)
from households.attachment_upload import (
    MAX_BATCH_BYTES,
    MAX_FILE_BYTES,
    ClaimedAttachmentUploadHandler,
)
from households.attachment_validation import AttachmentValidationError, validate_attachment
from households.income_services import create_income_record, delete_income_record
from households.management.commands import reconcile_income_attachment_storage
from households.management.commands.reconcile_income_attachment_storage import BaseReconciler
from households.models import (
    AuditLog,
    HouseholdMember,
    IncomeAttachment,
    IncomeAttachmentAvailability,
    IncomeFrequency,
    IncomeRecord,
    IncomeSource,
    Membership,
    Role,
)
from households.period_services import create_accounting_year, transition_accounting_month
from households.services import create_household


def png_chunk(chunk_type, data):
    body = chunk_type + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def valid_png(width=1, height=1):
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", b"not-decoded-by-structural-validator")
        + png_chunk(b"IEND", b"")
    )


def valid_jpeg(width=1, height=1):
    frame = (
        b"\x08" + struct.pack(">HH", height, width) + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    )
    scan = b"\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00"
    return (
        b"\xff\xd8\xff\xc0"
        + struct.pack(">H", len(frame) + 2)
        + frame
        + b"\xff\xda"
        + struct.pack(">H", len(scan) + 2)
        + scan
        + b"\x00\xff\xd9"
    )


def _probe_batch_lock(batch_id, inherited_descriptor, result_queue):
    if inherited_descriptor is not None:
        os.close(inherited_descriptor)
    from households.attachment_storage import acquire_batch_lock, release_batch_lock

    descriptor = acquire_batch_lock(batch_id, blocking=False)
    result_queue.put(descriptor is not None)
    release_batch_lock(descriptor)


class AttachmentValidationTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def validate(self, filename, content):
        path = Path(self.temp_dir.name) / "upload"
        path.write_bytes(content)
        return validate_attachment(path, filename)

    def test_accepts_structurally_valid_png_and_pdf(self):
        pdf = b"%PDF-1.7\nbody\n%%EOF\n"

        self.assertEqual(
            self.validate("rachunek.png", valid_png()), ("image/png", len(valid_png()))
        )
        self.assertEqual(self.validate("rachunek.pdf", pdf), ("application/pdf", len(pdf)))

    def test_accepts_structurally_valid_jpeg_extensions(self):
        content = valid_jpeg()

        self.assertEqual(self.validate("rachunek.jpg", content), ("image/jpeg", len(content)))
        self.assertEqual(self.validate("rachunek.jpeg", content), ("image/jpeg", len(content)))

    def test_rejects_jpeg_without_valid_frame_scan_or_end_marker(self):
        frame_end = 23
        malformed = (
            b"\xff\xd8\xff\xc0\x00\x07\x08\x00\x01\x00\x01\xff\xd9",
            valid_jpeg().replace(b"\xff\xda", b"\xff\xdb", 1),
            valid_jpeg()[:-2],
            valid_jpeg()[:frame_end] + b"\xff\xda\x00\x05\x01\x01\x00\xff\xd9",
            valid_jpeg()[:frame_end] + b"\xff\xda\x00\x0c\x01",
            valid_jpeg(width=12_001),
        )

        for content in malformed:
            with (
                self.subTest(size=len(content)),
                self.assertRaises(AttachmentValidationError),
            ):
                self.validate("broken.jpg", content)

    def test_rejects_corrupt_png_extension_mismatch_and_excessive_dimensions(self):
        corrupt_png = valid_png()[:-1] + b"x"

        for filename, content, code in (
            ("rachunek.png", corrupt_png, "invalid_file"),
            ("rachunek.jpg", valid_png(), "file_extension_mismatch"),
            ("rachunek.png", valid_png(width=12_001), "invalid_dimensions"),
        ):
            with self.subTest(filename=filename, code=code):
                with self.assertRaises(AttachmentValidationError) as raised:
                    self.validate(filename, content)
                self.assertEqual(raised.exception.code, code)

    def test_rejects_pdf_without_terminal_eof(self):
        with self.assertRaises(AttachmentValidationError) as raised:
            self.validate("rachunek.pdf", b"%PDF-1.7\nbody without trailer")

        self.assertEqual(raised.exception.code, "invalid_file")


class IncomeAttachmentApiTests(TransactionTestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.owner = User.objects.create_user(username="attachment-owner")
        self.viewer = User.objects.create_user(username="attachment-viewer")
        self.household = create_household(user=self.owner, name="Dom").household
        Membership.objects.create(household=self.household, user=self.viewer, role=Role.VIEWER)
        self.member = HouseholdMember.objects.create(household=self.household, display_name="Arek")
        self.year = create_accounting_year(
            user=self.owner, household_id=self.household.pk, calendar_year=2045
        )
        self.month = self.year.months.get(month_number=1)
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="activate",
        )
        self.source = IncomeSource.objects.create(
            household=self.household,
            member=self.member,
            name="Pensja",
            category="salary",
            start_date=date(2044, 1, 1),
            currency="PLN",
            frequency=IncomeFrequency.MONTHLY,
            is_regular=True,
        )
        income_result = create_income_record(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            data={
                "member_id": self.member.pk,
                "source_id": self.source.pk,
                "amount": Decimal("8000.00"),
                "currency": "PLN",
                "receipt_date": date(2044, 12, 31),
            },
            idempotency_key=uuid4(),
        )
        self.income = IncomeRecord.objects.get(pk=income_result.body["id"])
        self.path = (
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/"
            f"months/{self.month.pk}/incomes/{self.income.pk}/attachments/"
        )
        self.client = APIClient()

    def request(self, method, path=None, data=None, *, user=None, format="json"):
        self.client.force_login(self.owner if user is None else user)
        return getattr(self.client, method)(
            path or self.path,
            data,
            format=format,
            HTTP_HOST="localhost",
            secure=True,
        )

    def run_parallel(self, operations):
        barrier = threading.Barrier(len(operations))

        def execute(operation):
            try:
                barrier.wait(timeout=10)
                return operation()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            futures = [pool.submit(execute, operation) for operation in operations]
            return [future.result(timeout=30) for future in futures]

    def wait_for_database_lock(self, blocker_pid):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    "SELECT pid FROM pg_stat_activity "
                    "WHERE wait_event_type = 'Lock' AND %s = ANY(pg_blocking_pids(pid))",
                    [blocker_pid],
                )
                rows = cursor.fetchall()
            if rows:
                return [row[0] for row in rows]
            time.sleep(0.05)
        self.fail(f"No PostgreSQL backend waited on a lock held by {blocker_pid}")

    def test_valid_csrf_upload_rejects_oversized_second_file_atomically(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        token = "a" * 32
        client.cookies["csrftoken"] = token
        files = [
            SimpleUploadedFile("first.png", valid_png()),
            SimpleUploadedFile("too-large.png", b"x" * (10 * 1024 * 1024 + 1)),
        ]

        response = client.post(
            self.path,
            {"files": files},
            format="multipart",
            secure=True,
            HTTP_HOST="localhost",
            HTTP_X_CSRFTOKEN=token,
            HTTP_REFERER="https://localhost/",
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 0)
        storage_root = Path(self.media_dir.name) / "income-attachments"
        self.assertFalse(
            storage_root.exists() and any(path.is_file() for path in storage_root.rglob("*"))
        )

    def test_csrf_rejection_cleans_staged_upload_without_persisting(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.post(
            self.path,
            {"files": [SimpleUploadedFile("first.png", valid_png())]},
            format="multipart",
            secure=True,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertFalse(
            any(
                path.is_dir() and path.name != "locks"
                for path in (Path(self.media_dir.name) / ".incoming").iterdir()
            )
        )

    def test_upload_timeout_aborts_before_promotion(self):
        uploaded = SimpleUploadedFile("first.png", valid_png())

        with patch("households.attachment_upload.MAX_UPLOAD_SECONDS", -1):
            response = self.request("post", data={"files": [uploaded]}, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        storage_root = Path(self.media_dir.name) / "income-attachments"
        self.assertFalse(
            storage_root.exists() and any(path.is_file() for path in storage_root.rglob("*"))
        )

    def test_upload_handler_uses_actual_chunk_bytes_not_content_length(self):
        batch_id = uuid4()
        claim, descriptor = create_claim(batch_id)
        request = SimpleNamespace()
        handler = ClaimedAttachmentUploadHandler(
            request,
            batch_id=batch_id,
            directory=claim,
            lock_descriptor=descriptor,
        )

        def receive_file(name, size):
            handler.new_file("files", name, "application/octet-stream", 1, None, {})
            remaining = size
            while remaining:
                chunk = b"x" * min(handler.chunk_size, remaining)
                handler.receive_data_chunk(chunk, 0)
                remaining -= len(chunk)
            return handler.file_complete(size)

        try:
            first = receive_file("first.png", MAX_FILE_BYTES)
            second = receive_file("second.png", MAX_FILE_BYTES)
            self.assertEqual(first.size, MAX_FILE_BYTES)
            self.assertEqual(second.size, MAX_FILE_BYTES)
            self.assertEqual(first.attachment_staged_path.parent, claim)
            self.assertEqual(handler.total_bytes, 2 * MAX_FILE_BYTES)

            handler.new_file("files", "third.png", "application/octet-stream", 1, None, {})
            remaining = MAX_BATCH_BYTES - handler.total_bytes + 1
            with self.assertRaises(StopUpload):
                while remaining:
                    chunk = b"x" * min(handler.chunk_size, remaining)
                    handler.receive_data_chunk(chunk, 0)
                    remaining -= len(chunk)
        finally:
            handler.finish_request()

        self.assertEqual(handler.total_bytes, MAX_BATCH_BYTES)
        self.assertEqual(request.attachment_upload_error, "attachment_upload_limit_exceeded")

    def test_audit_failure_rolls_back_every_attachment_and_promoted_file(self):
        self.client.raise_request_exception = False
        files = [
            SimpleUploadedFile("first.png", valid_png()),
            SimpleUploadedFile("second.png", valid_png()),
        ]
        audit_calls = 0
        from households.record_services import write_audit as original_write_audit

        def fail_second_attachment_audit(**kwargs):
            nonlocal audit_calls
            if kwargs.get("object_type") == "income_attachment":
                audit_calls += 1
                if audit_calls == 2:
                    raise RuntimeError("simulated audit outage")
            return original_write_audit(**kwargs)

        with patch("households.attachment_services.write_audit", fail_second_attachment_audit):
            response = self.request("post", data={"files": files}, format="multipart")

        self.assertEqual(response.status_code, 500)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 0)
        storage_root = Path(self.media_dir.name) / "income-attachments"
        self.assertFalse(
            storage_root.exists() and any(path.is_file() for path in storage_root.rglob("*"))
        )

    def test_failed_cleanup_retries_without_duplicate_delete_audit(self):
        response = self.request(
            "post",
            data={"files": [SimpleUploadedFile("first.png", valid_png())]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get()
        path = storage_path(attachment.storage_key)

        with patch("households.attachment_services.unlink_key", side_effect=OSError("offline")):
            removed = self.request("delete", f"{self.path}{attachment.pk}/")

        self.assertEqual(removed.status_code, 204)
        attachment.refresh_from_db()
        self.assertEqual(attachment.availability_state, IncomeAttachmentAvailability.REMOVED)
        self.assertIsNone(attachment.storage_deleted_at)
        self.assertTrue(path.exists())

        retry = BaseReconciler(execute=True, limit=10)
        retry.handle_pending()
        attachment.refresh_from_db()

        self.assertEqual(retry.report["pending"], 1)
        self.assertIsNotNone(attachment.storage_deleted_at)
        self.assertFalse(path.exists())
        self.assertEqual(
            AuditLog.objects.filter(
                object_type="income_attachment", action="deleted", object_id=attachment.pk
            ).count(),
            1,
        )

    def test_database_update_failure_after_unlink_is_retried_idempotently(self):
        response = self.request(
            "post",
            data={"files": [SimpleUploadedFile("first.png", valid_png())]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get()
        path = storage_path(attachment.storage_key)
        original_update = QuerySet.update
        failed_once = False

        def fail_cleanup_update(queryset, **kwargs):
            nonlocal failed_once
            if "storage_deleted_at" in kwargs and not failed_once:
                failed_once = True
                raise DatabaseError("simulated acknowledgement failure")
            return original_update(queryset, **kwargs)

        with patch.object(QuerySet, "update", fail_cleanup_update):
            removed = self.request("delete", f"{self.path}{attachment.pk}/")

        self.assertEqual(removed.status_code, 204)
        self.assertFalse(path.exists())
        attachment.refresh_from_db()
        self.assertEqual(attachment.availability_state, IncomeAttachmentAvailability.REMOVED)
        self.assertIsNone(attachment.storage_deleted_at)

        retry = BaseReconciler(execute=True, limit=10)
        retry.handle_pending()
        attachment.refresh_from_db()

        self.assertEqual(retry.report["pending"], 1)
        self.assertIsNotNone(attachment.storage_deleted_at)
        self.assertEqual(
            AuditLog.objects.filter(
                object_type="income_attachment", action="deleted", object_id=attachment.pk
            ).count(),
            1,
        )

    def test_batch_flock_excludes_an_independent_process_after_grace_period(self):
        batch_id = uuid4()
        claim, descriptor = create_claim(batch_id)
        os.utime(claim, (1, 1))
        context = multiprocessing.get_context("fork")

        def probe(inherited_descriptor):
            result_queue = context.Queue()
            process = context.Process(
                target=_probe_batch_lock,
                args=(batch_id, inherited_descriptor, result_queue),
            )
            process.start()
            result = result_queue.get(timeout=10)
            process.join(timeout=10)
            self.assertEqual(process.exitcode, 0)
            return result

        try:
            self.assertFalse(probe(descriptor))
        finally:
            release_batch_lock(descriptor)

        self.assertTrue(probe(None))

    def test_month_close_races_final_upload_without_partial_storage(self):
        def close_month():
            transition_accounting_month(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=self.month.pk,
                operation="close",
            )
            return "closed"

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("race.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        close_result, upload_result = self.run_parallel([close_month, upload])
        attachment_count = (
            IncomeRecord.objects.get(pk=self.income.pk)
            .attachments.filter(availability_state=IncomeAttachmentAvailability.AVAILABLE)
            .count()
        )

        self.assertEqual(close_result, "closed")
        self.assertIn(upload_result.status_code, {201, 409})
        self.assertEqual(attachment_count, 1 if upload_result.status_code == 201 else 0)

    def test_income_delete_races_final_upload_without_exposing_orphaned_child(self):
        def delete_income():
            delete_income_record(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=self.month.pk,
                income_id=self.income.pk,
                expected_version=1,
            )
            return "deleted"

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("race.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        delete_result, upload_result = self.run_parallel([delete_income, upload])
        income = IncomeRecord.objects.get(pk=self.income.pk)
        attachments = list(income.attachments.all())

        self.assertEqual(delete_result, "deleted")
        self.assertIn(upload_result.status_code, {201, 404})
        self.assertIsNotNone(income.deleted_at)
        if upload_result.status_code == 201:
            self.assertEqual(len(attachments), 1)
            self.assertEqual(
                attachments[0].availability_state, IncomeAttachmentAvailability.REMOVED
            )
            self.assertIsNotNone(attachments[0].storage_deleted_at)
        else:
            self.assertEqual(attachments, [])

    def test_close_first_after_promotion_rolls_back_upload_and_bytes(self):
        promoted = threading.Event()
        allow_database_write = threading.Event()
        keys = []
        original_promote = __import__(
            "households.attachment_services", fromlist=["promote_file"]
        ).promote_file

        def pause_after_promotion(source, key):
            self.assertFalse(connections["default"].in_atomic_block)
            original_promote(source, key)
            keys.append(key)
            promoted.set()
            if not allow_database_write.wait(timeout=10):
                raise TimeoutError("test did not release the promoted upload")

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("close-first.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            patch("households.attachment_services.promote_file", pause_after_promotion),
        ):
            future = pool.submit(upload)
            self.assertTrue(promoted.wait(timeout=10))
            self.assertTrue(storage_path(keys[0]).is_file())
            transition_accounting_month(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=self.month.pk,
                operation="close",
            )
            allow_database_write.set()
            response = future.result(timeout=20)

        self.assertEqual(response.status_code, 409, response.content)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertFalse(storage_path(keys[0]).exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 0)

    def test_upload_commit_first_holds_real_household_lock_before_month_close(self):
        inside_upload_transaction = threading.Event()
        allow_upload_commit = threading.Event()
        close_started = threading.Event()
        upload_pid = []
        upload_transaction_state = []
        from households.record_services import write_audit as original_write_audit

        def pause_after_attachment_audit(**kwargs):
            result = original_write_audit(**kwargs)
            if kwargs.get("object_type") == "income_attachment":
                upload_transaction_state.append(connections["default"].in_atomic_block)
                upload_pid.append(connections["default"].connection.info.backend_pid)
                inside_upload_transaction.set()
                if not allow_upload_commit.wait(timeout=10):
                    raise TimeoutError("test did not release the upload transaction")
            return result

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("upload-first.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        def close_month():
            close_started.set()
            try:
                return transition_accounting_month(
                    user=self.owner,
                    household_id=self.household.pk,
                    year_id=self.year.pk,
                    month_id=self.month.pk,
                    operation="close",
                )
            finally:
                connections.close_all()

        with (
            ThreadPoolExecutor(max_workers=2) as pool,
            patch("households.attachment_services.write_audit", pause_after_attachment_audit),
        ):
            upload_future = pool.submit(upload)
            if not inside_upload_transaction.wait(timeout=10):
                allow_upload_commit.set()
                upload_future.result(timeout=20)
                self.fail("upload did not reach its transactional attachment audit")
            close_future = pool.submit(close_month)
            self.assertTrue(close_started.wait(timeout=10))
            blockers = self.wait_for_database_lock(upload_pid[0])
            allow_upload_commit.set()
            upload_response = upload_future.result(timeout=20)
            close_future.result(timeout=20)

        self.assertTrue(blockers)
        self.assertTrue(upload_transaction_state[0])
        self.assertEqual(upload_response.status_code, 201, upload_response.content)
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get()
        self.assertEqual(attachment.availability_state, IncomeAttachmentAvailability.AVAILABLE)
        self.assertTrue(storage_path(attachment.storage_key).is_file())
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_attachment", action="created").count(),
            1,
        )

    def test_parent_delete_first_after_promotion_leaves_no_attachment_or_final_bytes(self):
        promoted = threading.Event()
        allow_database_write = threading.Event()
        keys = []
        original_promote = __import__(
            "households.attachment_services", fromlist=["promote_file"]
        ).promote_file

        def pause_after_promotion(source, key):
            self.assertFalse(connections["default"].in_atomic_block)
            original_promote(source, key)
            keys.append(key)
            promoted.set()
            if not allow_database_write.wait(timeout=10):
                raise TimeoutError("test did not release the promoted upload")

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("delete-first.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            patch("households.attachment_services.promote_file", pause_after_promotion),
        ):
            future = pool.submit(upload)
            self.assertTrue(promoted.wait(timeout=10))
            self.assertTrue(storage_path(keys[0]).is_file())
            delete_income_record(
                user=self.owner,
                household_id=self.household.pk,
                year_id=self.year.pk,
                month_id=self.month.pk,
                income_id=self.income.pk,
                expected_version=1,
            )
            allow_database_write.set()
            response = future.result(timeout=20)

        self.assertEqual(response.status_code, 404, response.content)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertFalse(storage_path(keys[0]).exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 0)

    def test_upload_commit_first_holds_real_household_lock_before_parent_delete(self):
        inside_upload_transaction = threading.Event()
        allow_upload_commit = threading.Event()
        delete_started = threading.Event()
        upload_pid = []
        upload_transaction_state = []
        from households.record_services import write_audit as original_write_audit

        def pause_after_attachment_audit(**kwargs):
            result = original_write_audit(**kwargs)
            if kwargs.get("object_type") == "income_attachment":
                upload_transaction_state.append(connections["default"].in_atomic_block)
                upload_pid.append(connections["default"].connection.info.backend_pid)
                inside_upload_transaction.set()
                if not allow_upload_commit.wait(timeout=10):
                    raise TimeoutError("test did not release the upload transaction")
            return result

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("upload-before-delete.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        def delete_income():
            delete_started.set()
            try:
                return delete_income_record(
                    user=self.owner,
                    household_id=self.household.pk,
                    year_id=self.year.pk,
                    month_id=self.month.pk,
                    income_id=self.income.pk,
                    expected_version=1,
                )
            finally:
                connections.close_all()

        with (
            ThreadPoolExecutor(max_workers=2) as pool,
            patch("households.attachment_services.write_audit", pause_after_attachment_audit),
        ):
            upload_future = pool.submit(upload)
            if not inside_upload_transaction.wait(timeout=10):
                allow_upload_commit.set()
                upload_future.result(timeout=20)
                self.fail("upload did not reach its transactional attachment audit")
            delete_future = pool.submit(delete_income)
            self.assertTrue(delete_started.wait(timeout=10))
            blockers = self.wait_for_database_lock(upload_pid[0])
            allow_upload_commit.set()
            upload_response = upload_future.result(timeout=20)
            delete_future.result(timeout=20)

        self.assertTrue(blockers)
        self.assertTrue(upload_transaction_state[0])
        self.assertEqual(upload_response.status_code, 201, upload_response.content)
        attachment = IncomeAttachment.objects.get(income_record=self.income)
        self.assertEqual(attachment.availability_state, IncomeAttachmentAvailability.REMOVED)
        self.assertIsNotNone(attachment.storage_deleted_at)
        self.assertFalse(storage_path(attachment.storage_key).exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 2)

    def test_cleanup_cannot_remove_promoted_bytes_while_upload_holds_claim_lock(self):
        promoted = threading.Event()
        allow_database_write = threading.Event()
        keys = []
        batch_ids = []
        original_promote = __import__(
            "households.attachment_services", fromlist=["promote_file"]
        ).promote_file

        def pause_after_promotion(source, key):
            self.assertFalse(connections["default"].in_atomic_block)
            original_promote(source, key)
            keys.append(key)
            batch_ids.append(UUID(key.split("/")[2]))
            promoted.set()
            if not allow_database_write.wait(timeout=10):
                raise TimeoutError("test did not release the promoted upload")

        def upload():
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {"files": [SimpleUploadedFile("protected.png", valid_png())]},
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            patch("households.attachment_services.promote_file", pause_after_promotion),
        ):
            future = pool.submit(upload)
            self.assertTrue(promoted.wait(timeout=10))
            claim = Path(self.media_dir.name) / ".incoming" / str(batch_ids[0])
            os.utime(claim, (1, 1))
            reconciler = BaseReconciler(execute=True, limit=10)
            reconciler.handle_stale_claims()
            self.assertEqual(reconciler.report["claims"], 0)
            self.assertGreaterEqual(reconciler.report["skipped"], 1)
            self.assertTrue(storage_path(keys[0]).is_file())
            self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
            allow_database_write.set()
            response = future.result(timeout=20)

        self.assertEqual(response.status_code, 201, response.content)
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get()
        self.assertTrue(storage_path(attachment.storage_key).is_file())
        self.assertEqual(storage_path(attachment.storage_key).read_bytes(), valid_png())
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_attachment", action="created").count(),
            1,
        )

    def test_parallel_uploads_serialize_the_income_attachment_capacity(self):
        initial_files = [
            SimpleUploadedFile(f"initial-{index}.png", valid_png()) for index in range(16)
        ]
        for start in range(0, 16, 4):
            response = self.request(
                "post", data={"files": initial_files[start : start + 4]}, format="multipart"
            )
            self.assertEqual(response.status_code, 201, response.content)

        def upload_batch(prefix):
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {
                    "files": [
                        SimpleUploadedFile(f"{prefix}-{index}.png", valid_png())
                        for index in range(3)
                    ]
                },
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        responses = self.run_parallel([lambda: upload_batch("left"), lambda: upload_batch("right")])
        self.assertEqual(sorted(response.status_code for response in responses), [201, 400])
        self.assertEqual(
            IncomeRecord.objects.get(pk=self.income.pk)
            .attachments.filter(availability_state=IncomeAttachmentAvailability.AVAILABLE)
            .count(),
            19,
        )

    def test_capacity_upload_waits_on_real_postgres_lock_and_rechecks_after_commit(self):
        for start in range(0, 16, 4):
            files = [
                SimpleUploadedFile(f"capacity-{index}.png", valid_png())
                for index in range(start, start + 4)
            ]
            response = self.request("post", data={"files": files}, format="multipart")
            self.assertEqual(response.status_code, 201, response.content)

        inside_first_transaction = threading.Event()
        allow_first_commit = threading.Event()
        second_started = threading.Event()
        first_pid = []
        first_transaction_state = []
        from households.record_services import write_audit as original_write_audit

        def pause_first_batch(**kwargs):
            result = original_write_audit(**kwargs)
            if (
                kwargs.get("object_type") == "income_attachment"
                and not inside_first_transaction.is_set()
            ):
                first_transaction_state.append(connections["default"].in_atomic_block)
                first_pid.append(connections["default"].connection.info.backend_pid)
                inside_first_transaction.set()
                if not allow_first_commit.wait(timeout=10):
                    raise TimeoutError("test did not release capacity reservation")
            return result

        def upload_batch(prefix):
            client = APIClient()
            client.force_login(self.owner)
            return client.post(
                self.path,
                {
                    "files": [
                        SimpleUploadedFile(f"{prefix}-{index}.png", valid_png())
                        for index in range(3)
                    ]
                },
                format="multipart",
                secure=True,
                HTTP_HOST="localhost",
            )

        def second_upload():
            second_started.set()
            try:
                return upload_batch("second")
            finally:
                connections.close_all()

        with (
            ThreadPoolExecutor(max_workers=2) as pool,
            patch("households.attachment_services.write_audit", pause_first_batch),
        ):
            first_future = pool.submit(upload_batch, "first")
            if not inside_first_transaction.wait(timeout=10):
                allow_first_commit.set()
                first_future.result(timeout=20)
                self.fail("first capacity upload did not reach its transactional audit")
            second_future = pool.submit(second_upload)
            self.assertTrue(second_started.wait(timeout=10))
            blockers = self.wait_for_database_lock(first_pid[0])
            allow_first_commit.set()
            first_response = first_future.result(timeout=20)
            second_response = second_future.result(timeout=20)

        self.assertTrue(blockers)
        self.assertTrue(first_transaction_state[0])
        self.assertEqual(first_response.status_code, 201, first_response.content)
        self.assertEqual(second_response.status_code, 400, second_response.content)
        available = list(
            IncomeRecord.objects.get(pk=self.income.pk).attachments.filter(
                availability_state=IncomeAttachmentAvailability.AVAILABLE
            )
        )
        self.assertEqual(len(available), 19)
        self.assertTrue(all(storage_path(item.storage_key).is_file() for item in available))
        self.assertEqual(
            AuditLog.objects.filter(object_type="income_attachment", action="created").count(),
            19,
        )

    def test_upload_list_download_and_remove_private_attachment(self):
        content = valid_png()
        uploaded = SimpleUploadedFile("paragon.png", content, content_type="image/png")
        response = self.request("post", data={"files": [uploaded]}, format="multipart")

        self.assertEqual(response.status_code, 201, response.data)
        item = response.data["results"][0]
        self.assertEqual(item["original_name"], "paragon.png")
        self.assertEqual(item["media_type"], "image/png")
        self.assertEqual(item["size_bytes"], len(content))
        self.assertNotIn("storage_key", item)
        self.assertEqual(self.request("get").data["results"], response.data["results"])

        download = self.request("get", f"{self.path}{item['id']}/download/")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download["X-Content-Type-Options"], "nosniff")
        self.assertEqual(download["Cache-Control"], "no-store")
        self.assertEqual(b"".join(download.streaming_content), content)

        removed = self.request("delete", f"{self.path}{item['id']}/")
        self.assertEqual(removed.status_code, 204)
        self.assertEqual(self.request("get").data["results"], [])
        self.assertEqual(self.request("get", f"{self.path}{item['id']}/download/").status_code, 404)
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 2)

    def test_member_and_viewer_can_read_but_cannot_mutate_attachments(self):
        uploaded = SimpleUploadedFile("paragon.png", valid_png())
        response = self.request("post", data={"files": [uploaded]}, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        attachment_id = response.data["results"][0]["id"]
        member = User.objects.create_user(username="attachment-member")
        Membership.objects.create(household=self.household, user=member, role=Role.MEMBER)

        for user in (self.viewer, member):
            with self.subTest(role=Membership.objects.get(user=user).role):
                self.assertEqual(self.request("get", user=user).status_code, 200)
                download = self.request("get", f"{self.path}{attachment_id}/download/", user=user)
                self.assertEqual(download.status_code, 200)
                self.assertEqual(b"".join(download.streaming_content), valid_png())
                denied_upload = self.request(
                    "post",
                    data={"files": [SimpleUploadedFile("kolejny.png", valid_png())]},
                    user=user,
                    format="multipart",
                )
                self.assertEqual(denied_upload.status_code, 403)
                self.assertEqual(
                    self.request("delete", f"{self.path}{attachment_id}/", user=user).status_code,
                    403,
                )

        self.assertEqual(IncomeRecord.objects.get(pk=self.income.pk).attachments.count(), 1)
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 1)

    def test_administrator_can_upload_and_delete_attachments(self):
        administrator = User.objects.create_user(username="attachment-admin")
        Membership.objects.create(
            household=self.household, user=administrator, role=Role.ADMINISTRATOR
        )
        response = self.request(
            "post",
            data={"files": [SimpleUploadedFile("admin.png", valid_png())]},
            user=administrator,
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        attachment_id = response.data["results"][0]["id"]
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get(pk=attachment_id)
        self.assertTrue(storage_path(attachment.storage_key).is_file())

        deleted = self.request("delete", f"{self.path}{attachment_id}/", user=administrator)

        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(storage_path(attachment.storage_key).exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 2)

    def test_foreign_and_cross_parent_attachment_ids_are_not_disclosed(self):
        uploaded = self.request(
            "post",
            data={"files": [SimpleUploadedFile("private.png", valid_png())]},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.content)
        attachment_id = uploaded.data["results"][0]["id"]
        other_income = create_income_record(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            data={
                "member_id": self.member.pk,
                "source_id": self.source.pk,
                "amount": Decimal("125.00"),
                "currency": "PLN",
                "receipt_date": date(2044, 12, 30),
            },
            idempotency_key=uuid4(),
        )
        other_income_path = (
            f"/api/households/{self.household.pk}/accounting-years/{self.year.pk}/"
            f"months/{self.month.pk}/incomes/{other_income.body['id']}/attachments/"
        )
        foreign_owner = User.objects.create_user(username="foreign-attachment-owner")
        foreign_household = create_household(user=foreign_owner, name="Inny dom").household
        foreign_member = HouseholdMember.objects.create(
            household=foreign_household, display_name="Inna osoba"
        )
        foreign_year = create_accounting_year(
            user=foreign_owner, household_id=foreign_household.pk, calendar_year=2046
        )
        foreign_month = foreign_year.months.get(month_number=1)
        transition_accounting_month(
            user=foreign_owner,
            household_id=foreign_household.pk,
            year_id=foreign_year.pk,
            month_id=foreign_month.pk,
            operation="activate",
        )
        foreign_source = IncomeSource.objects.create(
            household=foreign_household,
            member=foreign_member,
            name="Foreign salary",
            category="salary",
            start_date=date(2045, 1, 1),
            currency="PLN",
            frequency=IncomeFrequency.MONTHLY,
            is_regular=True,
        )
        foreign_income = create_income_record(
            user=foreign_owner,
            household_id=foreign_household.pk,
            year_id=foreign_year.pk,
            month_id=foreign_month.pk,
            data={
                "member_id": foreign_member.pk,
                "source_id": foreign_source.pk,
                "amount": Decimal("100.00"),
                "currency": "PLN",
                "receipt_date": date(2046, 1, 1),
            },
            idempotency_key=uuid4(),
        )
        foreign_path = (
            f"/api/households/{foreign_household.pk}/accounting-years/{foreign_year.pk}/"
            f"months/{foreign_month.pk}/incomes/{foreign_income.body['id']}/attachments/"
        )
        foreign_upload = self.request(
            "post",
            foreign_path,
            {"files": [SimpleUploadedFile("foreign.png", valid_png())]},
            user=foreign_owner,
            format="multipart",
        )
        self.assertEqual(foreign_upload.status_code, 201, foreign_upload.content)
        foreign_attachment_id = foreign_upload.data["results"][0]["id"]

        self.assertEqual(
            self.request("get", f"{other_income_path}{attachment_id}/download/").status_code,
            404,
        )
        self.assertEqual(self.request("get", other_income_path).data["results"], [])
        self.assertEqual(
            self.request("delete", f"{other_income_path}{attachment_id}/").status_code, 404
        )
        foreign_path_for_current_user = (
            f"/api/households/{foreign_household.pk}/accounting-years/{foreign_year.pk}/"
            f"months/{foreign_month.pk}/incomes/{foreign_income.body['id']}/attachments/"
        )
        self.assertEqual(self.request("get", foreign_path_for_current_user).status_code, 404)
        self.assertEqual(
            self.request(
                "get",
                f"{foreign_path_for_current_user}{foreign_attachment_id}/download/",
            ).status_code,
            404,
        )
        self.assertEqual(
            self.request(
                "delete", f"{foreign_path_for_current_user}{foreign_attachment_id}/"
            ).status_code,
            404,
        )

    def test_closed_month_allows_read_but_rejects_attachment_mutations(self):
        uploaded = self.request(
            "post",
            data={"files": [SimpleUploadedFile("history.png", valid_png())]},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.content)
        attachment_id = uploaded.data["results"][0]["id"]
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )

        self.assertEqual(self.request("get").status_code, 200)
        self.assertEqual(
            self.request("get", f"{self.path}{attachment_id}/download/").status_code, 200
        )
        self.assertEqual(
            self.request(
                "post",
                data={"files": [SimpleUploadedFile("new.png", valid_png())]},
                format="multipart",
            ).status_code,
            409,
        )
        self.assertEqual(self.request("delete", f"{self.path}{attachment_id}/").status_code, 409)
        self.assertEqual(
            IncomeRecord.objects.get(pk=self.income.pk)
            .attachments.filter(availability_state=IncomeAttachmentAvailability.AVAILABLE)
            .count(),
            1,
        )

    def test_missing_parent_is_not_found_before_closed_period_conflict(self):
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )
        missing_path = self.path.replace(str(self.income.pk), str(uuid4()))

        self.assertEqual(self.request("get", missing_path).status_code, 404)
        self.assertEqual(
            self.request("delete", f"{missing_path}{uuid4()}/").status_code,
            404,
        )

    def test_soft_deleted_parent_hides_attachment_list_and_download(self):
        uploaded = self.request(
            "post",
            data={"files": [SimpleUploadedFile("parent.png", valid_png())]},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.content)
        attachment_id = uploaded.data["results"][0]["id"]
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get(pk=attachment_id)

        delete_income_record(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            income_id=self.income.pk,
            expected_version=1,
        )

        self.assertEqual(self.request("get").status_code, 404)
        self.assertEqual(
            self.request("get", f"{self.path}{attachment_id}/download/").status_code,
            404,
        )
        attachment.refresh_from_db()
        self.assertEqual(attachment.availability_state, IncomeAttachmentAvailability.REMOVED)
        self.assertIsNotNone(attachment.storage_deleted_at)

    def test_post_commit_handle_close_failure_keeps_available_storage_bytes(self):
        content = valid_png()
        uploaded = SimpleUploadedFile("paragon.png", content, content_type="image/png")
        original_close_files = ClaimedAttachmentUploadHandler.close_files

        def close_then_fail(handler):
            original_close_files(handler)
            raise OSError("simulated descriptor close failure")

        with patch.object(ClaimedAttachmentUploadHandler, "close_files", close_then_fail):
            response = self.request("post", data={"files": [uploaded]}, format="multipart")

        self.assertEqual(response.status_code, 201, response.content)
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get()
        self.assertEqual(attachment.availability_state, "available")
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 1)
        self.assertEqual(storage_path(attachment.storage_key).read_bytes(), content)

    def test_reconciliation_reports_missing_available_file_after_manifest_cleanup(self):
        uploaded = SimpleUploadedFile("paragon.png", valid_png())
        response = self.request("post", data={"files": [uploaded]}, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get()
        storage_path(attachment.storage_key).unlink()

        dry_run = BaseReconciler(execute=False, limit=10)
        dry_run.handle_stale_claims()
        dry_run.handle_orphan_objects()
        dry_run.handle_available()
        execute = BaseReconciler(execute=True, limit=10)
        execute.handle_stale_claims()
        execute.handle_orphan_objects()
        execute.handle_available()

        self.assertEqual(dry_run.report["missing"], 1)
        self.assertEqual(execute.report["missing"], 1)
        attachment.refresh_from_db()
        self.assertEqual(attachment.availability_state, IncomeAttachmentAvailability.AVAILABLE)
        self.assertIsNone(attachment.storage_deleted_at)

        path = storage_path(attachment.storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"tampered content")
        integrity = BaseReconciler(execute=False, limit=10)
        integrity.handle_available()
        self.assertEqual(integrity.report["corrupt"], 1)
        self.assertEqual(path.read_bytes(), b"tampered content")

    def test_integrity_scan_rechecks_state_after_acquiring_batch_lock(self):
        original_locked_batch = reconcile_income_attachment_storage.locked_batch

        for execute in (False, True):
            with self.subTest(execute=execute):
                uploaded = SimpleUploadedFile("paragon.png", valid_png())
                response = self.request("post", data={"files": [uploaded]}, format="multipart")
                self.assertEqual(response.status_code, 201, response.content)
                attachment = IncomeRecord.objects.get(pk=self.income.pk).attachments.get(
                    pk=response.data["results"][0]["id"]
                )

                @contextmanager
                def delete_before_lock(batch_id, selected_attachment_id=attachment.pk, **kwargs):
                    remove_income_attachment(
                        user=self.owner,
                        household_id=self.household.pk,
                        year_id=self.year.pk,
                        month_id=self.month.pk,
                        income_id=self.income.pk,
                        attachment_id=selected_attachment_id,
                    )
                    with original_locked_batch(batch_id, **kwargs) as descriptor:
                        yield descriptor

                reconciler = BaseReconciler(execute=execute, limit=10)
                with patch(
                    "households.management.commands.reconcile_income_attachment_storage.locked_batch",
                    delete_before_lock,
                ):
                    reconciler.handle_available()

                self.assertEqual(reconciler.report["missing"], 0)
                self.assertEqual(reconciler.report["corrupt"], 0)
                attachment.refresh_from_db()
                self.assertEqual(
                    attachment.availability_state, IncomeAttachmentAvailability.REMOVED
                )

    def test_orphan_scan_cursor_progresses_past_protected_files(self):
        old_timestamp = 1
        owned_batch = UUID(int=1)
        orphan_batch = UUID(int=2)
        owned_key = f"income-attachments/{self.household.pk}/{owned_batch}/{UUID(int=1)}"
        orphan_key = f"income-attachments/{self.household.pk}/{orphan_batch}/{UUID(int=2)}"
        owned_path = storage_path(owned_key)
        orphan_path = storage_path(orphan_key)
        owned_path.parent.mkdir(parents=True, mode=0o700)
        orphan_path.parent.mkdir(parents=True, mode=0o700)
        owned_path.write_bytes(valid_png())
        orphan_path.write_bytes(valid_png())
        os.utime(owned_path, (old_timestamp, old_timestamp))
        os.utime(orphan_path, (old_timestamp, old_timestamp))
        IncomeAttachment.objects.create(
            id=UUID(int=1),
            household=self.household,
            income_record=self.income,
            upload_batch_id=owned_batch,
            original_name="owned.png",
            media_type="image/png",
            size_bytes=owned_path.stat().st_size,
            storage_key=owned_key,
            content_sha256=hashlib.sha256(owned_path.read_bytes()).hexdigest(),
            created_by=self.owner,
        )

        first = BaseReconciler(execute=True, limit=1)
        first.handle_orphan_objects()
        first.save_cursors()
        second = BaseReconciler(execute=True, limit=1)
        second.load_cursors()
        second.handle_orphan_objects()

        self.assertEqual(first.report["orphans"], 0)
        self.assertEqual(second.report["orphans"], 1)
        self.assertTrue(owned_path.exists())
        self.assertFalse(orphan_path.exists())

    def test_stale_claim_scan_cursor_progresses_past_fresh_claims(self):
        fresh_batch = UUID(int=1)
        stale_batch = UUID(int=2)
        fresh_path, fresh_lock = create_claim(fresh_batch)
        release_batch_lock(fresh_lock)
        stale_path, stale_lock = create_claim(stale_batch)
        release_batch_lock(stale_lock)
        write_manifest(
            stale_batch, {"batch_id": str(stale_batch), "state": "promoting", "final_keys": []}
        )
        old_timestamp = 1
        os.utime(stale_path, (old_timestamp, old_timestamp))

        first = BaseReconciler(execute=True, limit=1)
        first.handle_stale_claims()
        first.save_cursors()
        second = BaseReconciler(execute=True, limit=1)
        second.load_cursors()
        second.handle_stale_claims()

        self.assertEqual(first.report["claims"], 0)
        self.assertEqual(second.report["claims"], 1)
        self.assertTrue(fresh_path.exists())
        self.assertFalse(stale_path.exists())

    def test_reconciliation_resets_only_malformed_uuid_cursors(self):
        cursor_path = Path(self.media_dir.name) / ".incoming" / "reconciliation-cursors.json"
        cursor_path.parent.mkdir(parents=True)
        cursor_path.write_text(
            json.dumps(
                {
                    "pending": "not-a-uuid",
                    "available": str(UUID(int=4)),
                    "claims": "claim-directory",
                    "orphans": "income-attachments/path",
                }
            ),
            encoding="utf-8",
        )
        reconciler = BaseReconciler(execute=False, limit=1)

        reconciler.load_cursors()

        self.assertIsNone(reconciler.cursors["pending"])
        self.assertEqual(reconciler.cursors["available"], str(UUID(int=4)))
        self.assertEqual(reconciler.cursors["claims"], "claim-directory")
        self.assertEqual(reconciler.cursors["orphans"], "income-attachments/path")

    def test_rejects_invalid_file_and_read_only_role_without_persisting(self):
        invalid = SimpleUploadedFile("notes.txt", b"plain text", content_type="text/plain")
        response = self.request("post", data={"files": [invalid]}, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertEqual(
            self.request(
                "post",
                data={"files": [SimpleUploadedFile("valid.png", valid_png())]},
                user=self.viewer,
                format="multipart",
            ).status_code,
            403,
        )
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())

    def test_batch_over_file_count_is_rejected_without_partial_persistence(self):
        files = [SimpleUploadedFile(f"plik-{index}.png", valid_png()) for index in range(6)]

        response = self.request("post", data={"files": files}, format="multipart")

        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 0)

    def test_closed_month_rejects_upload_without_persisting(self):
        transition_accounting_month(
            user=self.owner,
            household_id=self.household.pk,
            year_id=self.year.pk,
            month_id=self.month.pk,
            operation="close",
        )
        uploaded = SimpleUploadedFile("paragon.png", valid_png())

        response = self.request("post", data={"files": [uploaded]}, format="multipart")

        self.assertEqual(response.status_code, 409, response.data)
        self.assertFalse(IncomeRecord.objects.get(pk=self.income.pk).attachments.exists())
