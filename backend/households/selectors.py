from .access import Capability, require_access
from .models import Invitation, Membership


def households_for_user(user):
    return Membership.objects.filter(user=user).select_related("household")


def memberships_for_household(*, user, household_id):
    require_access(user=user, household_id=household_id)
    return Membership.objects.filter(household_id=household_id).select_related("user")


def invitations_for_household(*, user, household_id):
    require_access(user=user, household_id=household_id, capability=Capability.MANAGE_ACCESS)
    return Invitation.objects.filter(household_id=household_id)
