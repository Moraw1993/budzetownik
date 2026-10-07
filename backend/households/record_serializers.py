from common.serializers import StrictSerializer
from rest_framework import serializers

from .models import (
    AuditLog,
    Company,
    Contract,
    ContractType,
    GrossBasis,
    HouseholdMember,
    IncomeFrequency,
    IncomeKind,
    IncomeSource,
    RelationType,
)


class MemberInput(StrictSerializer):
    display_name = serializers.CharField(max_length=180)
    account_id = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    relation_type_id = serializers.UUIDField(allow_null=True, required=False)


class RelationInput(StrictSerializer):
    name = serializers.CharField(max_length=100)


class IncomeInput(StrictSerializer):
    kind = serializers.ChoiceField(choices=[IncomeKind.OTHER], required=False)
    expected_version = serializers.IntegerField(min_value=1, required=False)
    member_id = serializers.UUIDField(allow_null=True, required=False)
    name = serializers.CharField(max_length=180)
    category = serializers.CharField(max_length=100)
    payer = serializers.CharField(max_length=180, allow_blank=True, required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True, required=False)
    default_monthly_amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=0, allow_null=True, required=False
    )
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3)
    frequency = serializers.ChoiceField(choices=IncomeFrequency.choices)
    is_regular = serializers.BooleanField(required=False)
    description = serializers.CharField(max_length=2000, allow_blank=True, required=False)


class MemberOutput(serializers.ModelSerializer):
    class Meta:
        model = HouseholdMember
        fields = [
            "id",
            "household_id",
            "display_name",
            "account_id",
            "relation_type_id",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]


class RelationOutput(serializers.ModelSerializer):
    class Meta:
        model = RelationType
        fields = [
            "id",
            "household_id",
            "name",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]


class IncomeOutput(serializers.ModelSerializer):
    class Meta:
        model = IncomeSource
        fields = [
            "id",
            "household_id",
            "member_id",
            "name",
            "kind",
            "version",
            "category",
            "payer",
            "start_date",
            "end_date",
            "default_monthly_amount",
            "currency",
            "frequency",
            "is_regular",
            "description",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]


class CompanyInput(StrictSerializer):
    name = serializers.CharField(max_length=180)


class CompanyOutput(serializers.ModelSerializer):
    archived_at = serializers.DateTimeField(source="deactivated_at", read_only=True)

    class Meta:
        model = Company
        fields = ["id", "household_id", "name", "is_active", "archived_at"]


class CompanyBriefOutput(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "is_active"]


class ContractInput(StrictSerializer):
    member_id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    name = serializers.CharField(max_length=180)
    contract_type = serializers.ChoiceField(choices=ContractType.choices)
    other_type_name = serializers.CharField(max_length=180, allow_blank=True, required=False)
    position = serializers.CharField(max_length=180, allow_blank=True, required=False)
    gross_amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
    gross_basis = serializers.ChoiceField(choices=GrossBasis.choices)
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3)
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True, required=False)
    expected_version = serializers.IntegerField(min_value=1, required=False)


class ConversionInput(ContractInput):
    expected_version = serializers.IntegerField(min_value=1)


class ContractOutput(serializers.ModelSerializer):
    id = serializers.UUIDField(source="source_id", read_only=True)
    kind = serializers.CharField(source="source.kind", read_only=True)
    member_id = serializers.UUIDField(source="source.member_id", read_only=True)
    name = serializers.CharField(source="source.name", read_only=True)
    start_date = serializers.DateField(source="source.start_date", read_only=True)
    end_date = serializers.DateField(source="source.end_date", read_only=True)
    currency = serializers.CharField(source="source.currency", read_only=True)
    is_active = serializers.BooleanField(source="source.is_active", read_only=True)
    deactivated_at = serializers.DateTimeField(source="source.deactivated_at", read_only=True)
    version = serializers.IntegerField(source="source.version", read_only=True)
    company = CompanyBriefOutput(read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "kind",
            "member_id",
            "name",
            "start_date",
            "end_date",
            "currency",
            "is_active",
            "deactivated_at",
            "version",
            "company",
            "contract_type",
            "other_type_name",
            "position",
            "gross_amount",
            "gross_basis",
        ]


class AuditOutput(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "household_id",
            "actor_id",
            "action",
            "object_type",
            "object_id",
            "occurred_at",
            "before",
            "after",
        ]


class AuditFilters(StrictSerializer):
    object_id = serializers.UUIDField(required=False)
    object_type = serializers.ChoiceField(
        choices=[
            "income_source",
            "income_record",
            "company",
            "accounting_year",
            "accounting_month",
        ],
        required=False,
    )
    since = serializers.DateTimeField(required=False)
    until = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if "since" in attrs and "until" in attrs and attrs["since"] > attrs["until"]:
            raise serializers.ValidationError(
                "Początek zakresu nie może być późniejszy niż koniec."
            )
        return attrs
