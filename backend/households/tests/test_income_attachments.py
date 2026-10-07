import hashlib
import json
import os
import struct
import tempfile
import zlib
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient

from households.attachment_services import remove_income_attachment
from households.attachment_storage import (
    create_claim,
    release_batch_lock,
    storage_path,
    write_manifest,
)
from households.attachment_upload import ClaimedAttachmentUploadHandler
from households.attachment_validation import AttachmentValidationError, validate_attachment
from households.income_services import create_income_record
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
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 2)

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
