import time

from django.core.management import BaseCommand, CommandError, call_command
from django.db import OperationalError, connection


class Command(BaseCommand):
    help = "Wait for PostgreSQL and serialize migrations with an advisory lock."
    requires_system_checks = []

    def handle(self, *args, **options):
        for _attempt in range(30):
            try:
                connection.ensure_connection()
                break
            except OperationalError:
                connection.close()
                self.stdout.write("Waiting for PostgreSQL...")
                time.sleep(2)
        else:
            raise CommandError("PostgreSQL unavailable after 30 attempts.")

        # Same connection holds the session lock while Django performs migrations.
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(724613092)")
            try:
                call_command("migrate", interactive=False)
            finally:
                cursor.execute("SELECT pg_advisory_unlock(724613092)")
        self.stdout.write(self.style.SUCCESS("Migrations ready."))
