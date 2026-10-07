from common.views import PrivateAPIView
from django.http import FileResponse
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .attachment_serializers import IncomeAttachmentOutput, IncomeAttachmentUploadInput
from .attachment_services import (
    add_income_attachments,
    get_income_attachment,
    list_income_attachments,
    remove_income_attachment,
)
from .attachment_storage import open_key
from .attachment_upload import (
    AttachmentMultipartParser,
    AttachmentSessionAuthentication,
    raise_if_upload_aborted,
)


class IncomeAttachmentListView(PrivateAPIView):
    authentication_classes = [AttachmentSessionAuthentication]
    parser_classes = [AttachmentMultipartParser, JSONParser]

    def get(self, request, household_id, year_id, month_id, income_id):
        attachments = list_income_attachments(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
        )
        return Response({"results": IncomeAttachmentOutput(attachments, many=True).data})

    def post(self, request, household_id, year_id, month_id, income_id):
        raise_if_upload_aborted(request)
        serializer = IncomeAttachmentUploadInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = add_income_attachments(
            request=request,
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
            files=serializer.validated_data["files"],
        )
        return Response(
            {"results": IncomeAttachmentOutput(attachments, many=True).data}, status=201
        )


class IncomeAttachmentDetailView(PrivateAPIView):
    authentication_classes = [AttachmentSessionAuthentication]
    parser_classes = [AttachmentMultipartParser, JSONParser]

    def delete(self, request, household_id, year_id, month_id, income_id, attachment_id):
        remove_income_attachment(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
            attachment_id=attachment_id,
        )
        return Response(status=204)


class IncomeAttachmentDownloadView(PrivateAPIView):
    authentication_classes = [AttachmentSessionAuthentication]

    def get(self, request, household_id, year_id, month_id, income_id, attachment_id):
        attachment = get_income_attachment(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
            attachment_id=attachment_id,
        )
        response = FileResponse(
            open_key(attachment.storage_key),
            as_attachment=True,
            filename=attachment.original_name,
            content_type=attachment.media_type,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
