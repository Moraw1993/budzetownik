import logging
from uuid import uuid4

from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .access import Capability, locked_access, require_access
from .attachment_storage import (
    locked_batch,
    promote_file,
    storage_key,
    unlink_key,
    write_manifest,
)
from .attachment_upload import raise_if_upload_aborted
from .attachment_validation import AttachmentValidationError, validate_attachment
from .exceptions import AttachmentUploadAborted
from .income_services import require_active_month, resolve_income_period
from .models import (
    IncomeAttachment,
    IncomeAttachmentAvailability,
    IncomeRecord,
)
from .record_services import write_audit

logger = logging.getLogger("households.security")
MAX_FILES_PER_INCOME = 20
MAX_BYTES_PER_INCOME = 50 * 1024 * 1024


def attachment_snapshot(attachment):
    return {
        "household_id": str(attachment.household_id),
        "income_id": str(attachment.income_record_id),
        "attachment_id": str(attachment.pk),
        "original_name": attachment.original_name,
        "media_type": attachment.media_type,
        "size_bytes": attachment.size_bytes,
        "availability_state": attachment.availability_state,
    }


def _scoped_income(*, household_id, year_id, month_id, income_id, lock=False):
    year, month = resolve_income_period(
        household_id=household_id, year_id=year_id, month_id=month_id, lock_year=lock
    )
    records = IncomeRecord.objects
    if lock:
        records = records.select_for_update()
    income = get_object_or_404(
        records,
        household_id=household_id,
        accounting_month_id=month.pk,
        pk=income_id,
        deleted_at__isnull=True,
    )
    return year, month, income


def list_income_attachments(*, user, household_id, year_id, month_id, income_id):
    require_access(user=user, household_id=household_id)
    _, _, income = _scoped_income(
        household_id=household_id,
        year_id=year_id,
        month_id=month_id,
        income_id=income_id,
    )
    return list(
        IncomeAttachment.objects.filter(
            household_id=household_id,
            income_record_id=income.pk,
            availability_state=IncomeAttachmentAvailability.AVAILABLE,
        ).order_by("created_at", "id")[:MAX_FILES_PER_INCOME]
    )


def _enforce_income_capacity(income, new_files):
    current = IncomeAttachment.objects.filter(
        household_id=income.household_id,
        income_record_id=income.pk,
        availability_state=IncomeAttachmentAvailability.AVAILABLE,
    ).aggregate(count=Count("id"), size=Sum("size_bytes"))
    new_count = len(new_files)
    new_size = sum(item["size"] for item in new_files)
    if (current["count"] or 0) + new_count > MAX_FILES_PER_INCOME:
        raise ValidationError(
            {"code": "attachment_count_limit", "detail": "Limit to 20 załączników."}
        )
    if (current["size"] or 0) + new_size > MAX_BYTES_PER_INCOME:
        raise ValidationError(
            {
                "code": "attachment_total_limit",
                "detail": "Łączny rozmiar załączników przekracza 50 MiB.",
            }
        )


def _new_attachments(*, household_id, income_id, user, batch_id, files):
    rows = []
    for uploaded in files:
        try:
            media_type, actual_size = validate_attachment(
                uploaded.attachment_staged_path, uploaded.attachment_original_name
            )
        except AttachmentValidationError as exc:
            raise ValidationError({"code": exc.code, "detail": str(exc)}) from exc
        rows.append(
            {
                "row": IncomeAttachment(
                    household_id=household_id,
                    income_record_id=income_id,
                    upload_batch_id=batch_id,
                    original_name=uploaded.attachment_original_name,
                    media_type=media_type,
                    size_bytes=actual_size,
                    storage_key=storage_key(household_id, batch_id, uuid4()),
                    content_sha256=uploaded.attachment_sha256,
                    created_by=user,
                ),
                "path": uploaded.attachment_staged_path,
                "size": actual_size,
            }
        )
    if not rows:
        raise ValidationError({"files": "Dodaj co najmniej jeden plik."})
    return rows


def add_income_attachments(*, request, user, household_id, year_id, month_id, income_id, files):
    raise_if_upload_aborted(request)
    original_request = request._request
    handler = getattr(original_request, "attachment_upload_handler", None)
    if handler is None or len(files) != len(handler.completed_files):
        raise AttachmentUploadAborted()
    batch_id = handler.batch_id
    promoted_keys = []
    try:
        rows = _new_attachments(
            household_id=household_id,
            income_id=income_id,
            user=user,
            batch_id=batch_id,
            files=files,
        )
        if sum(row["size"] for row in rows) > 25 * 1024 * 1024:
            raise ValidationError(
                {"code": "attachment_upload_limit_exceeded", "detail": "Partia przekracza 25 MiB."}
            )
        keys = [item["row"].storage_key for item in rows]
        write_manifest(
            batch_id,
            {"batch_id": str(batch_id), "state": "promoting", "final_keys": keys},
        )
        for item in rows:
            promote_file(item["path"], item["row"].storage_key)
            promoted_keys.append(item["row"].storage_key)
        write_manifest(
            batch_id,
            {"batch_id": str(batch_id), "state": "promoted", "final_keys": keys},
        )
        with locked_access(
            user=user, household_id=household_id, capability=Capability.EDIT_DATA
        ) as membership:
            year, month = resolve_income_period(
                household_id=household_id, year_id=year_id, month_id=month_id, lock_year=True
            )
            income = get_object_or_404(
                IncomeRecord.objects.select_for_update(),
                household_id=household_id,
                accounting_month_id=month.pk,
                pk=income_id,
                deleted_at__isnull=True,
            )
            require_active_month(month)
            _enforce_income_capacity(income, rows)
            created = []
            for item in rows:
                attachment = item["row"]
                attachment.household = membership.household
                attachment.income_record = income
                attachment.save(force_insert=True)
                write_audit(
                    user=user,
                    household_id=household_id,
                    action="created",
                    object_type="income_attachment",
                    object_id=attachment.pk,
                    before=None,
                    after=attachment_snapshot(attachment),
                )
                created.append(attachment)
        handler.finish_success()
        return created
    except Exception:
        failed_keys = []
        for key in reversed(promoted_keys):
            try:
                unlink_key(key)
            except OSError:
                failed_keys.append(key)
        if failed_keys:
            try:
                write_manifest(
                    batch_id,
                    {
                        "batch_id": str(batch_id),
                        "state": "compensation_pending",
                        "final_keys": failed_keys,
                    },
                )
            except OSError:
                logger.exception("income_attachment_claim_manifest_failed")
            handler.preserve_claim = True
        raise


def get_income_attachment(*, user, household_id, year_id, month_id, income_id, attachment_id):
    require_access(user=user, household_id=household_id)
    _, _, income = _scoped_income(
        household_id=household_id,
        year_id=year_id,
        month_id=month_id,
        income_id=income_id,
    )
    return get_object_or_404(
        IncomeAttachment.objects.filter(
            household_id=household_id,
            income_record_id=income.pk,
            availability_state=IncomeAttachmentAvailability.AVAILABLE,
        ),
        pk=attachment_id,
    )


def _cleanup_removed_batch(batch_id):
    try:
        with locked_batch(batch_id, blocking=False) as descriptor:
            if descriptor is None:
                return
            pending = list(
                IncomeAttachment.objects.filter(
                    upload_batch_id=batch_id,
                    availability_state=IncomeAttachmentAvailability.REMOVED,
                    storage_deleted_at__isnull=True,
                )
            )
            for attachment in pending:
                unlink_key(attachment.storage_key)
                with transaction.atomic():
                    IncomeAttachment.objects.filter(
                        pk=attachment.pk,
                        availability_state=IncomeAttachmentAvailability.REMOVED,
                        storage_deleted_at__isnull=True,
                    ).update(storage_deleted_at=timezone.now())
    except Exception:
        logger.exception("income_attachment_cleanup_pending")


def remove_income_attachment(*, user, household_id, year_id, month_id, income_id, attachment_id):
    with locked_access(user=user, household_id=household_id, capability=Capability.EDIT_DATA):
        year, month, income = _scoped_income(
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
            lock=True,
        )
        attachment = get_object_or_404(
            IncomeAttachment.objects.select_for_update().filter(
                household_id=household_id,
                income_record_id=income.pk,
                availability_state=IncomeAttachmentAvailability.AVAILABLE,
            ),
            pk=attachment_id,
        )
        require_active_month(month)
        before = attachment_snapshot(attachment)
        attachment.availability_state = IncomeAttachmentAvailability.REMOVED
        attachment.removed_at = timezone.now()
        attachment.removed_by = user
        attachment.save(update_fields=["availability_state", "removed_at", "removed_by"])
        write_audit(
            user=user,
            household_id=household_id,
            action="deleted",
            object_type="income_attachment",
            object_id=attachment.pk,
            before=before,
            after=attachment_snapshot(attachment),
        )
        batch_id = attachment.upload_batch_id
        transaction.on_commit(lambda: _cleanup_removed_batch(batch_id))
        return year, month, income
