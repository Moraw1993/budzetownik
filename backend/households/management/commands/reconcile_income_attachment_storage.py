import json
import logging
from datetime import UTC, datetime, timedelta
from itertools import islice
from pathlib import Path
from uuid import UUID

from django.core.management.base import BaseCommand
from django.utils import timezone

from households.attachment_storage import (
    CLAIM_DIRECTORY,
    cleanup_claim,
    locked_batch,
    storage_path,
    unlink_key,
)
from households.models import IncomeAttachment, IncomeAttachmentAvailability

logger = logging.getLogger("households.security")
GRACE_PERIOD = timedelta(hours=24)


class BaseReconciler:
    def __init__(self, *, execute, limit):
        self.execute = execute
        self.limit = limit
        self.now = timezone.now()
        self.report = {"pending": 0, "claims": 0, "orphans": 0, "missing": 0, "skipped": 0}

    def older_than_grace(self, path):
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return self.now - modified >= GRACE_PERIOD

    def handle_pending(self):
        batch_ids = (
            IncomeAttachment.objects.filter(
                availability_state=IncomeAttachmentAvailability.REMOVED,
                storage_deleted_at__isnull=True,
            )
            .values_list("upload_batch_id", flat=True)
            .distinct()[: self.limit]
        )
        for batch_id in batch_ids:
            with locked_batch(batch_id, blocking=False) as descriptor:
                if descriptor is None:
                    self.report["skipped"] += 1
                    continue
                attachments = IncomeAttachment.objects.filter(
                    upload_batch_id=batch_id,
                    availability_state=IncomeAttachmentAvailability.REMOVED,
                    storage_deleted_at__isnull=True,
                )
                for attachment in attachments:
                    self.report["pending"] += 1
                    if self.execute:
                        unlink_key(attachment.storage_key)
                        IncomeAttachment.objects.filter(
                            pk=attachment.pk,
                            availability_state=IncomeAttachmentAvailability.REMOVED,
                            storage_deleted_at__isnull=True,
                        ).update(storage_deleted_at=timezone.now())

    def handle_stale_claims(self):
        from django.conf import settings

        root = Path(settings.MEDIA_ROOT) / CLAIM_DIRECTORY
        if not root.exists():
            return
        directories = [
            item
            for item in root.iterdir()
            if item.is_dir() and not item.is_symlink() and item.name != "locks"
        ][: self.limit]
        for directory in directories:
            try:
                batch_id = UUID(directory.name)
            except ValueError:
                self.report["skipped"] += 1
                continue
            if not self.older_than_grace(directory):
                continue
            with locked_batch(batch_id, blocking=False) as descriptor:
                if descriptor is None:
                    self.report["skipped"] += 1
                    continue
                manifest_path = directory / "manifest.json"
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    keys = manifest.get("final_keys", [])
                except (OSError, ValueError, AttributeError):
                    keys = []
                for key in keys:
                    self.reconcile_key(key)
                self.report["claims"] += 1
                if self.execute:
                    cleanup_claim(batch_id)

    def reconcile_key(self, key, *, orphan=False):
        attachment = IncomeAttachment.objects.filter(storage_key=key).first()
        path = storage_path(key)
        exists = path.exists()
        if attachment and attachment.availability_state == IncomeAttachmentAvailability.AVAILABLE:
            if not exists:
                self.report["missing"] += 1
                logger.error("income_attachment_storage_missing")
            return
        if attachment and attachment.availability_state == IncomeAttachmentAvailability.REMOVED:
            if attachment.storage_deleted_at is None:
                self.report["pending"] += 1
                if self.execute:
                    unlink_key(key)
                    IncomeAttachment.objects.filter(
                        pk=attachment.pk,
                        availability_state=IncomeAttachmentAvailability.REMOVED,
                        storage_deleted_at__isnull=True,
                    ).update(storage_deleted_at=timezone.now())
                return
            if not orphan or not exists:
                return
        if not exists:
            return
        self.report["orphans"] += 1
        if self.execute:
            unlink_key(key)

    def handle_orphan_objects(self):
        from django.conf import settings

        root = Path(settings.MEDIA_ROOT) / "income-attachments"
        if not root.exists():
            return
        candidates = (
            path
            for path in islice(root.rglob("*"), self.limit * 10)
            if path.is_file() and not path.is_symlink() and self.older_than_grace(path)
        )
        for path in candidates:
            try:
                relative = path.relative_to(Path(settings.MEDIA_ROOT)).as_posix()
                segments = relative.split("/")
                if len(segments) != 4:
                    self.report["skipped"] += 1
                    continue
                batch_id = UUID(segments[2])
            except (ValueError, OSError):
                self.report["skipped"] += 1
                continue
            with locked_batch(batch_id, blocking=False) as descriptor:
                if descriptor is None:
                    self.report["skipped"] += 1
                    continue
                self.reconcile_key(relative, orphan=True)


class Command(BaseCommand):
    help = "Reconcile private income attachment cleanup and stale claims. Defaults to dry-run."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true", help="Apply cleanup changes.")
        parser.add_argument(
            "--limit", type=int, default=100, help="Maximum batches/items to inspect."
        )

    def handle(self, *args, **options):
        if options["limit"] < 1:
            self.stderr.write("--limit must be positive.")
            return
        reconciler = BaseReconciler(execute=options["execute"], limit=options["limit"])
        try:
            reconciler.handle_pending()
            reconciler.handle_stale_claims()
            reconciler.handle_orphan_objects()
        except OSError:
            logger.exception("income_attachment_reconciliation_failed")
            raise
        mode = "executed" if options["execute"] else "dry-run"
        self.stdout.write(f"{mode}: {json.dumps(reconciler.report, sort_keys=True)}")
