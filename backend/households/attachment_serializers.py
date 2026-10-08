from common.serializers import StrictSerializer
from rest_framework import serializers


class IncomeAttachmentUploadInput(StrictSerializer):
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False), min_length=1, max_length=5
    )


class IncomeAttachmentOutput(serializers.Serializer):
    id = serializers.UUIDField()
    original_name = serializers.CharField()
    media_type = serializers.CharField()
    size_bytes = serializers.IntegerField()
    created_at = serializers.DateTimeField()
