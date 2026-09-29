from contextlib import contextmanager
from enum import StrEnum

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Household, Membership, Role


class Capability(StrEnum):
    READ = "read"
    EDIT_DATA = "edit_data"
    MANAGE_ACCESS = "manage_access"


ROLE_CAPABILITIES = {
    Role.OWNER: frozenset(Capability),
    Role.ADMINISTRATOR: frozenset({Capability.READ, Capability.EDIT_DATA}),
    Role.MEMBER: frozenset({Capability.READ}),
    Role.VIEWER: frozenset({Capability.READ}),
}


def require_access(*, user, household_id, capability=Capability.READ):
    if not user.is_authenticated or not user.is_active:
        raise NotFound()
    membership = get_object_or_404(
        Membership.objects.select_related("household"),
        user_id=user.pk,
        household_id=household_id,
    )
    if capability not in ROLE_CAPABILITIES.get(membership.role, frozenset()):
        raise PermissionDenied("Nie masz uprawnień do tej operacji.")
    return membership


@contextmanager
def locked_access(*, user, household_id, capability):
    """All aggregate writes must use this lock, including future invitation acceptance."""
    with transaction.atomic():
        require_access(user=user, household_id=household_id)
        get_object_or_404(Household.objects.select_for_update(), pk=household_id)
        # The role may have changed while waiting for another transaction to commit.
        membership = require_access(user=user, household_id=household_id, capability=capability)
        yield membership
