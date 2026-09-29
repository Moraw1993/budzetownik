from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .exceptions import LoginRateLimitError
from .models import LoginThrottle

WINDOW = timedelta(minutes=15)


def _key(scope: str, value: str) -> str:
    return salted_hmac(f"accounts.{scope}", value, algorithm="sha256").hexdigest()


@transaction.atomic
def _consume(key: str, limit: int) -> bool:
    LoginThrottle.objects.get_or_create(key=key)
    bucket = LoginThrottle.objects.select_for_update().get(pk=key)
    now = timezone.now()

    if now - bucket.window_started >= WINDOW:
        bucket.window_started = now
        bucket.attempts = 0

    if bucket.attempts >= limit:
        return False

    bucket.attempts += 1
    bucket.save(update_fields=["attempts", "window_started"])
    return True


def reserve_login_attempt(username: str, source: str) -> None:
    if not _consume(_key("source", source), 30):
        raise LoginRateLimitError

    if not _consume(_key("username", username.casefold()), 5):
        raise LoginRateLimitError


def reset_user_attempts(username: str) -> None:
    LoginThrottle.objects.filter(key=_key("username", username.casefold())).update(attempts=0)
