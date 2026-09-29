from accounts.models import User
from common.serializers import StrictSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Role


class HouseholdCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=180)
    currency = serializers.RegexField(r"^[A-Z]{3}$", default="PLN", max_length=3)


class HouseholdRenameSerializer(StrictSerializer):
    name = serializers.CharField(max_length=180)


class RoleChangeSerializer(StrictSerializer):
    role = serializers.ChoiceField(choices=Role.choices)


class OwnershipTransferSerializer(StrictSerializer):
    membership_id = serializers.UUIDField()


class InvitationCreateSerializer(StrictSerializer):
    role = serializers.ChoiceField(choices=Role.choices)


class InvitationAcceptSerializer(StrictSerializer):
    token = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(
        max_length=128, required=False, trim_whitespace=False, write_only=True
    )

    def validate(self, attrs):
        has_username = "username" in attrs
        has_password = "password" in attrs
        if has_username != has_password:
            raise serializers.ValidationError("Podaj login i hasło razem.")
        if has_username:
            try:
                validate_password(attrs["password"], user=User(username=attrs["username"]))
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs


class HouseholdSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="household_id")
    name = serializers.CharField(source="household.name")
    currency = serializers.CharField(source="household.currency")
    role = serializers.CharField()
    membership_id = serializers.UUIDField(source="id")


class MembershipSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    username = serializers.CharField(source="user.username")
    role = serializers.CharField()


class InvitationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    revoked_at = serializers.DateTimeField()
    accepted_at = serializers.DateTimeField()
