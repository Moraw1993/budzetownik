"""Django-side synthetic fixtures; invoked only by the isolated acceptance runner."""

import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.hashers import make_password
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

OLD_TARGET = ("households", "0003_relationtype_householdmember_auditlog_incomesource_and_more")
EVIDENCE = Path("/evidence")


def write_json(name, value):
    (EVIDENCE / name).write_text(
        json.dumps(value, cls=DjangoJSONEncoder, indent=2) + "\n", encoding="utf-8"
    )


def seed_legacy(run_id, password):
    """Require a fresh database and save every legacy field before upgrading."""
    executor = MigrationExecutor(connection)
    if executor.loader.applied_migrations:
        raise ValueError("Legacy seed requires a fresh isolated database")
    executor.migrate([OLD_TARGET])
    apps = executor.loader.project_state([OLD_TARGET]).apps
    User = apps.get_model("accounts", "User")
    Household = apps.get_model("households", "Household")
    Membership = apps.get_model("households", "Membership")
    Member = apps.get_model("households", "HouseholdMember")
    Source = apps.get_model("households", "IncomeSource")
    Audit = apps.get_model("households", "AuditLog")
    users = {
        role: User.objects.create(
            username=f"family_{role}_{run_id}", password=make_password(password)
        )
        for role in ("owner", "administrator", "member", "viewer")
    }
    homes = [
        Household.objects.create(name=f"Odbiór rodziny {label} {run_id}") for label in ("A", "B")
    ]
    for role, user in users.items():
        Membership.objects.create(household=homes[0], user=user, role=role)
    Membership.objects.create(household=homes[1], user=users["owner"], role="owner")
    members = [
        Member.objects.create(household=home, display_name=f"Osoba historyczna {label} {run_id}")
        for home, label in zip(homes, ("A", "B"), strict=True)
    ]
    salary = Source.objects.create(
        household=homes[0],
        member=members[0],
        name="Wynagrodzenie",
        category="salary",
        payer="Firma historyczna",
        start_date=date(2025, 1, 1),
        default_monthly_amount=Decimal("1234.56"),
        currency="PLN",
        frequency="monthly",
        is_regular=True,
        description="Historyczny opis",
    )
    Source.objects.create(
        household=homes[0],
        name="Archiwalny najem",
        category="rent",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        default_monthly_amount=Decimal("99.00"),
        currency="EUR",
        frequency="monthly",
        is_regular=True,
        is_active=False,
        deactivated_at=timezone.now(),
    )
    foreign = Source.objects.create(
        household=homes[1],
        member=members[1],
        name="Obce źródło",
        category="other",
        start_date=date(2025, 1, 1),
        default_monthly_amount=Decimal("33.77"),
        currency="PLN",
        frequency="monthly",
        is_regular=True,
    )
    Audit.objects.create(
        household=homes[0],
        actor=users["owner"],
        action="created",
        object_type="income_source",
        object_id=salary.id,
        before=None,
        after={"name": salary.name, "default_monthly_amount": "1234.56"},
    )
    write_json(
        "family-legacy.json",
        {
            "sources": list(Source.objects.order_by("pk").values()),
            "audit": list(Audit.objects.order_by("pk").values()),
        },
    )
    write_json(
        "family-fixture.json",
        {
            "run_id": run_id,
            "users": {role: user.username for role, user in users.items()},
            "households": [str(home.id) for home in homes],
            "members": [str(person.id) for person in members],
            "salary": str(salary.id),
            "foreign_source": str(foreign.id),
        },
    )


def verify_migration():
    from households.models import AuditLog, Company, Contract, IncomeSource

    old = json.loads((EVIDENCE / "family-legacy.json").read_text(encoding="utf-8"))
    fields = list(old["sources"][0])
    actual = list(IncomeSource.objects.order_by("pk").values(*fields))
    normalized = json.loads(json.dumps(actual, cls=DjangoJSONEncoder))
    assert normalized == old["sources"], "Legacy source fields changed during migration"
    audits = list(AuditLog.objects.order_by("pk").values())
    assert json.loads(json.dumps(audits, cls=DjangoJSONEncoder)) == old["audit"]
    assert set(IncomeSource.objects.values_list("kind", flat=True)) == {"other"}
    assert not Company.objects.exists() and not Contract.objects.exists()
    write_json(
        "family-migration-result.json",
        {"sources_preserved": len(actual), "audit_preserved": len(audits), "inferred_contracts": 0},
    )


def snapshot():
    """Capture all household domain tables, including fields absent from the API."""
    from django.apps import apps

    result = {}
    for model in apps.get_app_config("households").get_models():
        result[model._meta.label] = list(model.objects.order_by("pk").values())
    return json.loads(json.dumps(result, cls=DjangoJSONEncoder))


def main():
    action = os.environ["FAMILY_ACCEPTANCE_ACTION"]
    if action == "seed":
        seed_legacy(os.environ["FAMILY_ACCEPTANCE_RUN"], os.environ["FAMILY_ACCEPTANCE_PASSWORD"])
    elif action == "migration":
        verify_migration()
    elif action == "snapshot":
        write_json("family-db-snapshot.json", snapshot())
    elif action == "verify":
        expected = json.loads((EVIDENCE / "family-db-snapshot.json").read_text(encoding="utf-8"))
        assert snapshot() == expected, "Domain database records changed after restart"
    else:
        raise ValueError("Unknown family acceptance action")
    print(f"Family database check passed: {action}")


if __name__ == "__main__":
    main()
