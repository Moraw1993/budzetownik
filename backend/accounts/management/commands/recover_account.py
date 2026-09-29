from getpass import getpass

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError

from accounts.models import User
from accounts.services import replace_password


class Command(BaseCommand):
    help = "Change an existing account password locally without email."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("Konto nie istnieje.") from exc

        password = getpass("Nowe hasło: ")
        confirmation = getpass("Powtórz hasło: ")

        if password != confirmation:
            raise CommandError("Hasła muszą być identyczne.")

        if len(password) > 128:
            raise CommandError("Hasło może mieć maksymalnie 128 znaków.")

        try:
            replace_password(user=user, password=password)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc

        self.stdout.write(self.style.SUCCESS("Hasło zmienione. Poprzednie sesje utraciły dostęp."))
