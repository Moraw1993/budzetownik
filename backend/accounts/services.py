import logging

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import connection, transaction

from .exceptions import SetupClosedError
from .models import User
from .throttling import reserve_login_attempt, reset_user_attempts

security_log = logging.getLogger("accounts.security")


@transaction.atomic
def create_initial_account(*, username: str, password: str) -> User:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(724613093)")

    if User.objects.exists():
        raise SetupClosedError

    user = User(username=username)
    validate_password(password, user=user)
    user.set_password(password)
    user.save()
    security_log.info("account_created user_id=%s", user.pk)
    return user


def create_invited_account(*, username: str, password: str) -> User:
    user = User(username=username)
    validate_password(password, user=user)
    user.set_password(password)
    user.save()
    security_log.info("invited_account_created user_id=%s", user.pk)
    return user


def authenticate_account(*, request, username: str, password: str) -> User | None:
    reserve_login_attempt(username, request.META.get("REMOTE_ADDR", "local"))
    user = authenticate(request=request, username=username, password=password)

    if user is None:
        security_log.warning("login_failed")
        return None

    reset_user_attempts(username)
    security_log.info("login_succeeded user_id=%s", user.pk)
    return user


def replace_password(*, user: User, password: str) -> None:
    validate_password(password, user=user)
    user.set_password(password)
    user.save(update_fields=["password"])
    reset_user_attempts(user.username)
    security_log.info("password_recovered user_id=%s", user.pk)
