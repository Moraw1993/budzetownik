import struct
import tempfile
import zlib
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from households.attachment_validation import AttachmentValidationError, validate_attachment
from households.income_services import create_income_record
from households.models import (
    AuditLog,
    HouseholdMember,
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


class IncomeAttachmentApiTests(TestCase):
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

        with self.captureOnCommitCallbacks(execute=True):
            removed = self.request("delete", f"{self.path}{item['id']}/")
        self.assertEqual(removed.status_code, 204)
        self.assertEqual(self.request("get").data["results"], [])
        self.assertEqual(AuditLog.objects.filter(object_type="income_attachment").count(), 2)

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
