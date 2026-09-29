from collections.abc import Mapping

from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    """Reject fields outside the write contract instead of silently ignoring them."""

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {field: "Nieznane pole." for field in sorted(unknown)}
                )
        return super().to_internal_value(data)
