from common.serializers import StrictSerializer
from rest_framework import serializers

from .models import AccountingMonth, AccountingYear


class AccountingYearInput(StrictSerializer):
    calendar_year = serializers.IntegerField(min_value=1, max_value=9999)


class AccountingYearOutput(serializers.ModelSerializer):
    class Meta:
        model = AccountingYear
        fields = ["id", "household_id", "calendar_year", "created_at"]


class AccountingMonthOutput(serializers.ModelSerializer):
    month_start = serializers.DateField(read_only=True)
    month_end = serializers.DateField(read_only=True)

    class Meta:
        model = AccountingMonth
        fields = [
            "id",
            "accounting_year_id",
            "month_number",
            "state",
            "month_start",
            "month_end",
            "activated_at",
            "closed_at",
            "created_at",
            "updated_at",
        ]


class AccountingYearCreatedOutput(serializers.ModelSerializer):
    months = AccountingMonthOutput(many=True, read_only=True)

    class Meta:
        model = AccountingYear
        fields = ["id", "household_id", "calendar_year", "created_at", "months"]
