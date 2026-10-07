import hashlib
import logging
import os
import time
from uuid import uuid4

from django.core.files.uploadedfile import UploadedFile
from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import MultiPartParser

from .attachment_storage import cleanup_claim, create_claim, release_batch_lock
from .attachment_validation import AttachmentValidationError, normalize_filename
from .exceptions import AttachmentUploadAborted
from .models import IncomeRecord, Membership, Role

logger = logging.getLogger("households.security")
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_BATCH_BYTES = 25 * 1024 * 1024
MAX_FILES_PER_BATCH = 5
MAX_UPLOAD_SECONDS = 10 * 60


class ClaimedUploadedFile(UploadedFile):
    pass


class ClaimedAttachmentUploadHandler(FileUploadHandler):
    chunk_size = 64 * 1024

    def __init__(self, request, *, batch_id, directory, lock_descriptor):
        super().__init__(request)
        self.batch_id = batch_id
        self.directory = directory
        self.lock_descriptor = lock_descriptor
        self.started_at = time.monotonic()
        self.total_bytes = 0
        self.file_count = 0
        self.current_descriptor = None
        self.current_path = None
        self.current_bytes = 0
        self.current_hash = None
        self.current_original_name = None
        self.completed_files = []
        self._settled = False
        self.preserve_claim = False

    def _abort(self, code="attachment_upload_limit_exceeded"):
        self.request.attachment_upload_error = code
        self._close_current()
        raise StopUpload(connection_reset=True)

    def _close_current(self):
        if self.current_descriptor is None:
            return
        try:
            os.fsync(self.current_descriptor)
        finally:
            os.close(self.current_descriptor)
            self.current_descriptor = None

    def new_file(
        self, field_name, file_name, content_type, content_length, charset, content_type_extra
    ):
        if field_name != "files":
            self._abort("invalid_multipart_field")
        self.file_count += 1
        if self.file_count > MAX_FILES_PER_BATCH:
            self._abort()
        try:
            safe_name = normalize_filename(file_name)
        except AttachmentValidationError:
            self._abort("invalid_filename")
        super().new_file(
            field_name, safe_name, content_type, content_length, charset, content_type_extra
        )
        self.current_path = self.directory / f"{self.file_count}-{uuid4()}.part"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        self.current_descriptor = os.open(self.current_path, flags, 0o600)
        self.current_bytes = 0
        self.current_hash = hashlib.sha256()
        self.current_original_name = safe_name

    def receive_data_chunk(self, raw_data, start):
        if time.monotonic() - self.started_at > MAX_UPLOAD_SECONDS:
            self._abort("attachment_upload_timeout")
        size = len(raw_data)
        if self.current_bytes + size > MAX_FILE_BYTES or self.total_bytes + size > MAX_BATCH_BYTES:
            self._abort()
        view = memoryview(raw_data)
        while view:
            written = os.write(self.current_descriptor, view)
            view = view[written:]
        self.current_bytes += size
        self.total_bytes += size
        self.current_hash.update(raw_data)
        return None

    def file_complete(self, file_size):
        self._close_current()
        descriptor = self.current_path.open("rb")
        uploaded = ClaimedUploadedFile(
            descriptor,
            name=self.file_name,
            content_type=self.content_type,
            size=self.current_bytes,
            charset=self.charset,
        )
        uploaded.attachment_staged_path = self.current_path
        uploaded.attachment_original_name = self.current_original_name
        uploaded.attachment_sha256 = self.current_hash.hexdigest()
        uploaded.attachment_batch_id = self.batch_id
        self.completed_files.append(uploaded)
        self.current_descriptor = None
        return uploaded

    def upload_interrupted(self):
        if not hasattr(self.request, "attachment_upload_error"):
            self.request.attachment_upload_error = "attachment_upload_interrupted"
        self._close_current()

    def close_files(self):
        self._close_current()
        for uploaded in self.completed_files:
            uploaded.close()

    def finish_success(self):
        self.close_files()
        try:
            cleanup_claim(self.batch_id)
        except OSError:
            logger.exception("income_attachment_claim_cleanup_failed")
        finally:
            self._settled = True
            release_batch_lock(self.lock_descriptor)
            self.lock_descriptor = None

    def finish_request(self):
        if self._settled:
            return
        self.close_files()
        try:
            if not self.preserve_claim:
                cleanup_claim(self.batch_id)
        except OSError:
            logger.exception("income_attachment_claim_cleanup_failed")
        finally:
            self._settled = True
            release_batch_lock(self.lock_descriptor)
            self.lock_descriptor = None


class AttachmentUploadSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception:
            handler = getattr(request, "attachment_upload_handler", None)
            if handler is not None:
                handler.finish_request()
            raise
        handler = getattr(request, "attachment_upload_handler", None)
        if handler is not None:
            handler.finish_request()
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != "POST" or request.resolver_match.url_name != "income-attachment-list":
            return None
        household_id = view_kwargs["household_id"]
        if not getattr(request.user, "is_authenticated", False) or not request.user.is_active:
            return JsonResponse({"detail": "Uwierzytelnienie jest wymagane."}, status=403)
        membership = (
            Membership.objects.filter(household_id=household_id, user_id=request.user.pk)
            .values_list("role", flat=True)
            .first()
        )
        if membership is None:
            return JsonResponse({"detail": "Nie znaleziono zasobu."}, status=404)
        if membership not in {Role.OWNER, Role.ADMINISTRATOR}:
            return JsonResponse({"detail": "Brak uprawnień do tej operacji."}, status=403)
        parent_exists = IncomeRecord.objects.filter(
            household_id=household_id,
            accounting_month_id=view_kwargs["month_id"],
            accounting_month__accounting_year_id=view_kwargs["year_id"],
            pk=view_kwargs["income_id"],
            deleted_at__isnull=True,
        ).exists()
        if not parent_exists:
            return JsonResponse({"detail": "Nie znaleziono zasobu."}, status=404)
        batch_id = uuid4()
        try:
            directory, lock_descriptor = create_claim(batch_id)
        except OSError:
            logger.exception("income_attachment_claim_unavailable")
            return JsonResponse({"detail": "Storage jest chwilowo niedostępny."}, status=503)
        handler = ClaimedAttachmentUploadHandler(
            request,
            batch_id=batch_id,
            directory=directory,
            lock_descriptor=lock_descriptor,
        )
        request.attachment_upload_handler = handler
        request.upload_handlers = [handler]
        return None


class AttachmentUploadAbortGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(request, "attachment_upload_error", None):
            return self.error_response(request)
        return None

    @staticmethod
    def error_response(request):
        code = getattr(request, "attachment_upload_error", "attachment_upload_interrupted")
        detail = (
            "Przesyłanie plików przekroczyło dopuszczalny czas."
            if code == "attachment_upload_timeout"
            else "Cała partia załączników została odrzucona. Sprawdź pliki i spróbuj ponownie."
        )
        return JsonResponse({"detail": detail, "code": code}, status=400)


class AttachmentMultipartParser(MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            result = super().parse(stream, media_type, parser_context)
        except Exception:
            raise
        request = parser_context["request"]._request
        if getattr(request, "attachment_upload_error", None):
            raise AttachmentUploadAborted()
        return result


class AttachmentSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if getattr(request._request, "attachment_upload_error", None):
            raise AttachmentUploadAborted()
        return result


def raise_if_upload_aborted(request):
    original_request = getattr(request, "_request", request)
    if getattr(original_request, "attachment_upload_error", None):
        raise AttachmentUploadAborted()
