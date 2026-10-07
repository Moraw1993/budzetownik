import re
from decimal import Decimal, InvalidOperation

from common.serializers import StrictSerializer
from rest_framework import serializers

_AMOUNT_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")


class DecimalStringField(serializers.Field):
    default_error_messages = {
        "invalid": "Podaj kwotę jako tekst dziesiętny z maksymalnie dwoma miejscami.",
        "range": "Kwota musi mieścić się w zakresie 0.01–9999999999999999.99.",
    }

    def to_internal_value(self, data):
        if not isinstance(data, str) or not _AMOUNT_PATTERN.fullmatch(data):
            self.fail("invalid")
        try:
            amount = Decimal(data)
        except InvalidOperation as exc:
            raise serializers.ValidationError(self.error_messages["invalid"]) from exc
        if amount < Decimal("0.01") or amount > Decimal("9999999999999999.99"):
            self.fail("range")
        return amount

    def to_representation(self, value):
        return format(value, ".2f")


class StrictPositiveIntegerField(serializers.IntegerField):
    default_error_messages = {
        **serializers.IntegerField.default_error_messages,
        "invalid": "Oczekiwana wersja musi być dodatnią liczbą całkowitą JSON.",
    }

    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail("invalid")
        return super().to_internal_value(data)


class IncomeCreateInput(StrictSerializer):
    member_id = serializers.UUIDField(allow_null=True, required=False, default=None)
    source_id = serializers.UUIDField()
    amount = DecimalStringField()
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3)
    receipt_date = serializers.DateField()


class IncomePatchInput(StrictSerializer):
    member_id = serializers.UUIDField(allow_null=True, required=False)
    source_id = serializers.UUIDField(required=False)
    amount = DecimalStringField(required=False)
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3, required=False)
    receipt_date = serializers.DateField(required=False)
    expected_version = StrictPositiveIntegerField(min_value=1)

    def validate(self, attrs):
        if not set(attrs) - {"expected_version"}:
            raise serializers.ValidationError("Podaj co najmniej jedno pole do zmiany.")
        return attrs


class IncomeDeleteInput(StrictSerializer):
    expected_version = StrictPositiveIntegerField(min_value=1)


class IncomeSourceOptionsQuery(StrictSerializer):
    member_id = serializers.UUIDField(required=False)


class IncomeOutput(serializers.Serializer):
    id = serializers.UUIDField()
    household_id = serializers.UUIDField()
    month_id = serializers.UUIDField(source="accounting_month_id")
    member_id = serializers.UUIDField(allow_null=True)
    source_id = serializers.UUIDField(source="income_source_id")
    amount = DecimalStringField(read_only=True)
    currency = serializers.CharField()
    receipt_date = serializers.DateField()
    version = serializers.IntegerField()
    recipient_snapshot = serializers.JSONField()
    source_snapshot = serializers.JSONField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class IncomeSourceOptionOutput(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    kind = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True)
    currency = serializers.CharField()
    contract = serializers.JSONField(allow_null=True)


class CurrencyTotalOutput(serializers.Serializer):
    currency = serializers.CharField()
    amount = DecimalStringField()


class IncomeTotalsOutput(serializers.Serializer):
    totals = CurrencyTotalOutput(many=True)
