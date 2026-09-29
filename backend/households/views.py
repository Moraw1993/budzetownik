from common.views import PrivateAPIView
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .access import require_access
from .selectors import households_for_user, invitations_for_household, memberships_for_household
from .serializers import (
    HouseholdCreateSerializer,
    HouseholdRenameSerializer,
    HouseholdSerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MembershipSerializer,
    OwnershipTransferSerializer,
    RoleChangeSerializer,
)
from .services import (
    accept_invitation,
    change_membership,
    create_household,
    issue_invitation,
    rename_household,
    revoke_invitation,
    transfer_ownership,
)


class HouseholdListView(PrivateAPIView):
    def get(self, request):
        memberships = households_for_user(request.user)
        return Response(HouseholdSerializer(memberships, many=True).data)

    def post(self, request):
        serializer = HouseholdCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = create_household(user=request.user, **serializer.validated_data)
        return Response(HouseholdSerializer(membership).data, status=201)


class HouseholdDetailView(PrivateAPIView):
    def get(self, request, household_id):
        membership = require_access(user=request.user, household_id=household_id)
        return Response(HouseholdSerializer(membership).data)

    def patch(self, request, household_id):
        serializer = HouseholdRenameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = rename_household(
            user=request.user, household_id=household_id, **serializer.validated_data
        )
        return Response(HouseholdSerializer(membership).data)


class MembershipListView(PrivateAPIView):
    def get(self, request, household_id):
        memberships = memberships_for_household(user=request.user, household_id=household_id)
        return Response(MembershipSerializer(memberships, many=True).data)


class MembershipDetailView(PrivateAPIView):
    def patch(self, request, household_id, membership_id):
        serializer = RoleChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = change_membership(
            user=request.user,
            household_id=household_id,
            membership_id=membership_id,
            **serializer.validated_data,
        )
        return Response(MembershipSerializer(membership).data)

    def delete(self, request, household_id, membership_id):
        change_membership(user=request.user, household_id=household_id, membership_id=membership_id)
        return Response(status=204)


class OwnershipTransferView(PrivateAPIView):
    def post(self, request, household_id):
        serializer = OwnershipTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = transfer_ownership(
            user=request.user, household_id=household_id, **serializer.validated_data
        )
        return Response(HouseholdSerializer(membership).data)


class InvitationListView(PrivateAPIView):
    def get(self, request, household_id):
        invitations = invitations_for_household(user=request.user, household_id=household_id)
        return Response(InvitationSerializer(invitations, many=True).data)

    def post(self, request, household_id):
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, token = issue_invitation(
            user=request.user, household_id=household_id, **serializer.validated_data
        )
        response = InvitationSerializer(invitation).data
        response["invitation_url"] = f"{request.build_absolute_uri('/accept-invitation')}#{token}"
        return Response(response, status=201)


class InvitationDetailView(PrivateAPIView):
    def delete(self, request, household_id, invitation_id):
        revoke_invitation(user=request.user, household_id=household_id, invitation_id=invitation_id)
        return Response(status=204)


@method_decorator(csrf_protect, name="dispatch")
class InvitationAcceptView(PrivateAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership, user, created_account = accept_invitation(
            user=request.user, **serializer.validated_data
        )
        if created_account:
            login(request, user)
        return Response(
            MembershipSerializer(membership).data, status=201 if created_account else 200
        )
