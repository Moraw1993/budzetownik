import hashlib
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from django.conf import settings
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
CURSOR_LOCK_ID = UUID(int=0)
CURSOR_FILENAME = "reconciliation-cursors.json"
CURSOR_NAMES = {"pending", "claims", "orphans", "available"}


class BaseReconciler:
    def __init__(self, *, execute, limit):
        self.execute = execute
        self.limit = limit
        self.now = timezone.now()
        self.cursors = {name: None for name in CURSOR_NAMES}
        self.report = {
            "pending": 0,
            "claims": 0,
            "orphans": 0,
            "missing": 0,
            "corrupt": 0,
            "skipped": 0,
        }

    def older_than_grace(self, path):
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return self.now - modified >= GRACE_PERIOD

    def _cursor_window(self, items, name, key):
        cursor = self.cursors[name]
        candidates = []
        for item in items:
            item_key = key(item)
            if cursor is None or item_key > cursor:
                candidates.append(item)
                if len(candidates) > self.limit:
                    break
        selected = candidates[: self.limit]
        self.cursors[name] = key(selected[-1]) if len(candidates) > self.limit else None
        return selected

    def handle_pending(self):
        cursor = self.cursors["pending"]
        batches = (
            IncomeAttachment.objects.filter(
                availability_state=IncomeAttachmentAvailability.REMOVED,
                storage_deleted_at__isnull=True,
            )
            .values_list("upload_batch_id", flat=True)
            .distinct()
        )
        if cursor:
            batches = batches.filter(upload_batch_id__gt=UUID(cursor))
        batches = list(batches.order_by("upload_batch_id")[: self.limit + 1])
        selected = batches[: self.limit]
        self.cursors["pending"] = str(selected[-1]) if len(batches) > self.limit else None
        for batch_id in selected:
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
        root = Path(settings.MEDIA_ROOT) / CLAIM_DIRECTORY
        if not root.exists():
            self.cursors["claims"] = None
            return
        directories = sorted(
            (
                item
                for item in root.iterdir()
                if item.is_dir() and not item.is_symlink() and item.name != "locks"
            ),
            key=lambda item: item.name,
        )
        selected = self._cursor_window(directories, "claims", lambda item: item.name)
        for directory in selected:
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
                    if not isinstance(keys, list):
                        keys = []
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
        exists = path.is_file() and not path.is_symlink()
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
        root = Path(settings.MEDIA_ROOT) / "income-attachments"
        if not root.exists():
            self.cursors["orphans"] = None
            return
        paths = self._iter_files(root)
        selected = self._cursor_window(
            paths,
            "orphans",
            lambda path: path.relative_to(Path(settings.MEDIA_ROOT)).as_posix(),
        )
        for path in selected:
            if not self.older_than_grace(path):
                continue
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

    @classmethod
    def _iter_files(cls, directory):
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError:
            return
        for path in children:
            if path.is_symlink():
                continue
            if path.is_dir():
                yield from cls._iter_files(path)
            elif path.is_file():
                yield path

    def handle_available(self):
        cursor = self.cursors["available"]
        attachments = IncomeAttachment.objects.filter(
            availability_state=IncomeAttachmentAvailability.AVAILABLE
        )
        if cursor:
            attachments = attachments.filter(pk__gt=UUID(cursor))
        attachments = list(attachments.order_by("pk")[: self.limit + 1])
        selected = attachments[: self.limit]
        self.cursors["available"] = str(selected[-1].pk) if len(attachments) > self.limit else None
        for attachment in selected:
            with locked_batch(attachment.upload_batch_id, blocking=False) as descriptor:
                if descriptor is None:
                    self.report["skipped"] += 1
                    continue
                current = IncomeAttachment.objects.filter(pk=attachment.pk).first()
                if (
                    current is None
                    or current.availability_state != IncomeAttachmentAvailability.AVAILABLE
                ):
                    continue
                path = storage_path(current.storage_key)
                if not path.is_file() or path.is_symlink():
                    self.report["missing"] += 1
                    logger.error("income_attachment_storage_missing")
                    continue
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(64 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != current.content_sha256:
                    self.report["corrupt"] += 1
                    logger.error("income_attachment_storage_checksum_mismatch")

    def load_cursors(self):
        path = Path(settings.MEDIA_ROOT) / CLAIM_DIRECTORY / CURSOR_FILENAME
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            logger.exception("income_attachment_reconciliation_cursor_unreadable")
            return
        if not isinstance(loaded, dict):
            logger.error("income_attachment_reconciliation_cursor_invalid")
            return
        for name in CURSOR_NAMES:
            cursor = loaded.get(name)
            if not isinstance(cursor, str):
                self.cursors[name] = None
                continue
            if name in {"pending", "available"}:
                try:
                    cursor = str(UUID(cursor))
                except ValueError:
                    logger.error(
                        "income_attachment_reconciliation_cursor_invalid", extra={"category": name}
                    )
                    self.cursors[name] = None
                    continue
            self.cursors[name] = cursor

    def save_cursors(self):
        root = Path(settings.MEDIA_ROOT) / CLAIM_DIRECTORY
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if root.is_symlink():
            raise OSError("Attachment reconciliation state cannot be a symbolic link.")
        os.chmod(root, 0o700)
        path = root / CURSOR_FILENAME
        temporary = root / f"{CURSOR_FILENAME}.{uuid4()}.tmp"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", closefd=False) as stream:
                json.dump(self.cursors, stream, sort_keys=True, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        directory_descriptor = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)


class Command(BaseCommand):
    help = "Reconcile private income attachment storage. Dry-run by default; scan cursors persist."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true", help="Apply cleanup changes.")
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum items processed per category; cursor state advances between runs.",
        )

    def handle(self, *args, **options):
        if options["limit"] < 1:
            self.stderr.write("--limit must be positive.")
            return
        reconciler = BaseReconciler(execute=options["execute"], limit=options["limit"])
        try:
            with locked_batch(CURSOR_LOCK_ID, blocking=False) as descriptor:
                if descriptor is None:
                    reconciler.report["skipped"] += 1
                else:
                    reconciler.load_cursors()
                    reconciler.handle_pending()
                    reconciler.handle_stale_claims()
                    reconciler.handle_orphan_objects()
                    reconciler.handle_available()
                    reconciler.save_cursors()
        except OSError:
            logger.exception("income_attachment_reconciliation_failed")
            raise
        mode = "executed" if options["execute"] else "dry-run"
        self.stdout.write(f"{mode}: {json.dumps(reconciler.report, sort_keys=True)}")
