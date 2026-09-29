import logging
import secrets
from datetime import timedelta
from functools import partial

from accounts.services import create_invited_account
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from rest_framework.exceptions import ValidationError

from .access import Capability, locked_access
from .exceptions import LastOwnerError
from .models import Household, Invitation, Membership, Role

security_log = logging.getLogger("households.security")


def record_access_event(event, *, actor_id, household_id, membership_id, role, previous_role=None):
    transaction.on_commit(
        partial(
            security_log.info,
            "%s actor_id=%s household_id=%s membership_id=%s role_before=%s role_after=%s",
            event,
            actor_id,
            household_id,
            membership_id,
            previous_role,
            role,
        )
    )


def record_invitation_event(event, *, actor_id, household_id, invitation_id, role):
    transaction.on_commit(
        partial(
            security_log.info,
            "%s actor_id=%s household_id=%s invitation_id=%s role=%s",
            event,
            actor_id,
            household_id,
            invitation_id,
            role,
        )
    )


def token_digest(token):
    return salted_hmac("households.invitation", token).hexdigest()


@transaction.atomic
def create_household(*, user, name, currency="PLN"):
    household = Household.objects.create(name=name, currency=currency)
    membership = Membership.objects.create(household=household, user=user, role=Role.OWNER)
    record_access_event(
        "household_created",
        actor_id=user.pk,
        household_id=household.pk,
        membership_id=membership.pk,
        role=membership.role,
    )
    return membership


def rename_household(*, user, household_id, name):
    with locked_access(
        user=user, household_id=household_id, capability=Capability.EDIT_DATA
    ) as actor:
        actor.household.name = name
        actor.household.save(update_fields=["name"])
        return actor


def ensure_owner_remains(membership):
    if (
        membership.role == Role.OWNER
        and not Membership.objects.filter(
            household_id=membership.household_id, role=Role.OWNER, user__is_active=True
        )
        .exclude(pk=membership.pk)
        .exists()
    ):
        raise LastOwnerError()


def change_membership(*, user, household_id, membership_id, role=None):
    """None revokes access; otherwise change the role under the aggregate lock."""
    if role is not None and role not in Role.values:
        raise ValidationError({"role": "Nieprawidłowa rola."})
    with locked_access(user=user, household_id=household_id, capability=Capability.MANAGE_ACCESS):
        target = get_object_or_404(
            Membership.objects.select_related("user"),
            pk=membership_id,
            household_id=household_id,
        )
        if role == Role.OWNER and not target.user.is_active:
            raise ValidationError({"role": "Konto Ownera musi być aktywne."})
        if role != Role.OWNER:
            ensure_owner_remains(target)
        record_access_event(
            "membership_removed" if role is None else "membership_role_changed",
            actor_id=user.pk,
            household_id=household_id,
            membership_id=target.pk,
            role=role,
            previous_role=target.role,
        )
        if role is None:
            target.delete()
            return None
        target.role = role
        target.save(update_fields=["role"])
        return target


def transfer_ownership(*, user, household_id, membership_id):
    with locked_access(
        user=user, household_id=household_id, capability=Capability.MANAGE_ACCESS
    ) as actor:
        target = get_object_or_404(
            Membership.objects.select_related("user"),
            pk=membership_id,
            household_id=household_id,
        )
        if target.pk == actor.pk:
            raise ValidationError({"membership_id": "Wybierz inną osobę."})
        if not target.user.is_active:
            raise ValidationError({"membership_id": "Konto musi być aktywne."})
        previous_target_role = target.role
        target.role = Role.OWNER
        target.save(update_fields=["role"])
        actor.role = Role.ADMINISTRATOR
        actor.save(update_fields=["role"])
        record_access_event(
            "ownership_transferred",
            actor_id=user.pk,
            household_id=household_id,
            membership_id=target.pk,
            role=target.role,
            previous_role=previous_target_role,
        )
        record_access_event(
            "ownership_transferred",
            actor_id=user.pk,
            household_id=household_id,
            membership_id=actor.pk,
            role=actor.role,
            previous_role=Role.OWNER,
        )
        return actor


def issue_invitation(*, user, household_id, role):
    with locked_access(
        user=user, household_id=household_id, capability=Capability.MANAGE_ACCESS
    ) as actor:
        token = secrets.token_urlsafe(32)
        invitation = Invitation.objects.create(
            household=actor.household,
            issued_by=user,
            role=role,
            token_hash=token_digest(token),
            expires_at=timezone.now() + timedelta(days=7),
        )
        record_invitation_event(
            "invitation_issued",
            actor_id=user.pk,
            household_id=actor.household_id,
            invitation_id=invitation.pk,
            role=invitation.role,
        )
        return invitation, token


def revoke_invitation(*, user, household_id, invitation_id):
    with locked_access(
        user=user, household_id=household_id, capability=Capability.MANAGE_ACCESS
    ) as actor:
        invitation = get_object_or_404(
            Invitation.objects.select_for_update(), pk=invitation_id, household_id=household_id
        )
        if invitation.accepted_at is not None:
            raise ValidationError({"detail": "Nie można odwołać przyjętego zaproszenia."})
        if invitation.revoked_at is None:
            invitation.revoked_at = timezone.now()
            invitation.save(update_fields=["revoked_at"])
            record_invitation_event(
                "invitation_revoked",
                actor_id=user.pk,
                household_id=actor.household_id,
                invitation_id=invitation.pk,
                role=invitation.role,
            )


def invalid_invitation():
    raise ValidationError({"detail": "Zaproszenie jest nieprawidłowe lub niedostępne."})


@transaction.atomic
def accept_invitation(*, user, token, username=None, password=None):
    digest = token_digest(token)
    candidate = Invitation.objects.filter(token_hash=digest).values("id", "household_id").first()
    if candidate is None:
        invalid_invitation()

    household = Household.objects.select_for_update().filter(pk=candidate["household_id"]).first()
    if household is None:
        invalid_invitation()
    invitation = Invitation.objects.select_for_update().filter(pk=candidate["id"]).first()
    if invitation is None or not constant_time_compare(invitation.token_hash, digest):
        invalid_invitation()
    if (
        invitation.revoked_at is not None
        or invitation.accepted_at is not None
        or invitation.expires_at <= timezone.now()
    ):
        invalid_invitation()

    created_account = False
    if not getattr(user, "is_authenticated", False):
        if username is None or password is None:
            raise ValidationError({"detail": "Podaj dane nowego konta albo zaloguj się."})
        try:
            with transaction.atomic():
                user = create_invited_account(username=username, password=password)
        except IntegrityError as exc:
            raise ValidationError({"username": "Taki login jest już zajęty."}) from exc
        created_account = True

    membership = Membership.objects.filter(household=household, user=user).first()
    if membership is None:
        membership = Membership.objects.create(household=household, user=user, role=invitation.role)

    invitation.accepted_at = timezone.now()
    invitation.accepted_by = user
    invitation.save(update_fields=["accepted_at", "accepted_by"])
    record_invitation_event(
        "invitation_accepted",
        actor_id=user.pk,
        household_id=household.pk,
        invitation_id=invitation.pk,
        role=membership.role,
    )
    return membership, user, created_account
