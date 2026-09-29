"""Exercise the foundation API and compare an isolated restored installation."""

import argparse
import hashlib
import json
import sys
from urllib.parse import urlsplit

from acceptance_common import compose, load_run
from acceptance_http import ApiSession


def resource_path(household_id, resource):
    return f"/api/households/{household_id}/{resource}/"


def collect_snapshot(client, households):
    """Collect the resources that must survive backup and recreation."""
    snapshot = {"households": client.request("GET", "/api/households/")[0]}
    for household_id in households:
        snapshot[household_id] = {}
        for resource in ("memberships", "members", "income-sources", "audit-logs"):
            payload = client.request("GET", resource_path(household_id, resource))[0]
            rows = payload["results"] if isinstance(payload, dict) else payload
            snapshot[household_id][resource] = sorted(rows, key=lambda row: row["id"])
    snapshot["households"].sort(key=lambda row: row["id"])
    return snapshot


def income_data(name, member_id=None):
    return {
        "member_id": member_id,
        "name": name,
        "category": "praca" if member_id else "inne",
        "start_date": "2026-01-01",
        "default_monthly_amount": "1234.56",
        "currency": "PLN",
        "frequency": "monthly",
    }


def create_income(client, household_id, name, member_id=None):
    return client.request(
        "POST",
        resource_path(household_id, "income-sources"),
        income_data(name, member_id),
        expected=(201,),
    )[0]


def invite_account(owner, run_id, household_id, role, username, password):
    invitation = owner.request(
        "POST",
        resource_path(household_id, "invitations"),
        {"role": role},
        expected=(201,),
    )[0]
    token = urlsplit(invitation["invitation_url"]).fragment
    assert token, "Invitation token is missing"
    invited = ApiSession(run_id, "source")
    invited.prepare_csrf()
    membership = invited.request(
        "POST",
        "/api/invitations/accept/",
        {"token": token, "username": username, "password": password},
        expected=(201,),
    )[0]
    invited.prepare_csrf()
    return invited, membership


def expect_denied(client, method, path, payload=None):
    result, _, status = client.request(method, path, payload, expected=(401, 403, 404))
    assert status in (401, 403, 404), result


def seed_media(run_id):
    code = (
        "from pathlib import Path; "
        f"Path('/app/media/acceptance-{run_id}.txt').write_text('{run_id}')"
    )
    compose(run_id, "source", "exec", "-T", "backend", "python", "-c", code)


def media_hash(run_id, role):
    code = (
        "from pathlib import Path; import hashlib; "
        f"print(hashlib.sha256(Path('/app/media/acceptance-{run_id}.txt').read_bytes()).hexdigest())"
    )
    result = compose(
        run_id,
        role,
        "exec",
        "-T",
        "backend",
        "python",
        "-c",
        code,
        capture_output=True,
    )
    return result.stdout.decode().strip()


def run_scenario(run_id):
    """Create synthetic accounts and assert roles, isolation and audit behavior."""
    run_dir, manifest = load_run(run_id)
    fixture_path = run_dir / "fixture.json"
    if fixture_path.exists():
        raise ValueError("Scenario has already been created for this run")
    password = manifest["user_password"]
    owner_name = f"owner_{run_id}"
    owner = ApiSession(run_id, "source")
    owner.prepare_csrf()
    assert owner.request("GET", "/api/auth/setup/")[0]["setup_required"]
    owner.request(
        "POST",
        "/api/auth/setup/",
        {"username": owner_name, "password": password},
        expected=(201,),
    )
    owner.prepare_csrf()
    assert owner.request("GET", "/api/households/")[0] == []

    first = owner.request("POST", "/api/households/", {"name": f"Dom A {run_id}"}, expected=(201,))[
        0
    ]
    second = owner.request(
        "POST", "/api/households/", {"name": f"Dom B {run_id}"}, expected=(201,)
    )[0]
    first_id, second_id = first["id"], second["id"]
    member = owner.request(
        "POST",
        resource_path(first_id, "members"),
        {"display_name": f"Osoba {run_id}"},
        expected=(201,),
    )[0]
    foreign_member = owner.request(
        "POST",
        resource_path(second_id, "members"),
        {"display_name": f"Obca osoba {run_id}"},
        expected=(201,),
    )[0]
    for index in range(2):
        create_income(owner, first_id, f"Dochód osoby {index} {run_id}", member["id"])
        create_income(owner, first_id, f"Dochód domu {index} {run_id}")
    foreign_income = create_income(owner, second_id, f"Obcy dochód {run_id}")

    viewer, viewer_membership = invite_account(
        owner, run_id, first_id, "viewer", f"viewer_{run_id}", password
    )
    member_client, _ = invite_account(
        owner, run_id, first_id, "member", f"member_{run_id}", password
    )
    administrator, _ = invite_account(
        owner, run_id, first_id, "administrator", f"admin_{run_id}", password
    )
    administrator.request(
        "POST",
        resource_path(first_id, "members"),
        {"display_name": f"Dodana przez admina {run_id}"},
        expected=(201,),
    )
    create_income(administrator, first_id, f"Dochód admina {run_id}")

    baseline_members = owner.request("GET", resource_path(first_id, "members"))[0]["count"]
    baseline_income = owner.request("GET", resource_path(first_id, "income-sources"))[0]["count"]
    anonymous = ApiSession(run_id, "source")
    expect_denied(anonymous, "GET", resource_path(first_id, "members"))
    for client in (viewer, member_client, anonymous):
        expect_denied(
            client,
            "POST",
            resource_path(first_id, "members"),
            {"display_name": "Zabroniony zapis"},
        )
        expect_denied(
            client,
            "POST",
            resource_path(first_id, "income-sources"),
            income_data("Zabroniony dochód"),
        )
    assert owner.request("GET", resource_path(first_id, "members"))[0]["count"] == baseline_members
    assert (
        owner.request("GET", resource_path(first_id, "income-sources"))[0]["count"]
        == baseline_income
    )

    for client in (viewer, member_client, administrator):
        assert (
            client.request("GET", resource_path(first_id, "members"))[0]["count"]
            == baseline_members
        )
        expect_denied(client, "GET", resource_path(second_id, "members"))
        expect_denied(
            client,
            "POST",
            resource_path(second_id, "members"),
            {"display_name": "Obcy zapis"},
        )
        expect_denied(
            client,
            "GET",
            resource_path(first_id, "members") + foreign_member["id"] + "/",
        )
        expect_denied(
            client,
            "GET",
            resource_path(first_id, "income-sources") + foreign_income["id"] + "/",
        )
    assert owner.request("GET", resource_path(second_id, "members"))[0]["count"] == 1
    assert owner.request("GET", resource_path(first_id, "income-sources"))[0]["count"] == 5
    assert owner.request("GET", resource_path(second_id, "income-sources"))[0]["count"] == 1
    assert owner.request("GET", resource_path(first_id, "audit-logs"))[0]["count"] >= 4
    expect_denied(viewer, "GET", resource_path(first_id, "audit-logs"))

    owner.request(
        "DELETE",
        resource_path(first_id, "memberships") + viewer_membership["id"] + "/",
        expected=(204,),
    )
    expect_denied(viewer, "GET", resource_path(first_id, "members"))

    seed_media(run_id)
    expected_media_hash = hashlib.sha256(run_id.encode()).hexdigest()
    assert media_hash(run_id, "source") == expected_media_hash
    snapshot = collect_snapshot(owner, (first_id, second_id))
    fixture = {
        "owner": owner_name,
        "households": [first_id, second_id],
        "media_hash": expected_media_hash,
        "snapshot": snapshot,
    }
    fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("Six-step synthetic setup and role/isolation API checks passed")
    print(f"Fixture and database snapshot: {fixture_path}")


def verify_persistence(run_id, role):
    """Compare the source after recreation or the target after restoration."""
    run_dir, manifest = load_run(run_id)
    fixture = json.loads((run_dir / "fixture.json").read_text(encoding="utf-8"))
    client = ApiSession(run_id, role)
    client.login(fixture["owner"], manifest["user_password"])
    assert client.request("GET", "/api/auth/setup/")[0]["setup_required"] is False
    actual = collect_snapshot(client, fixture["households"])
    assert actual == fixture["snapshot"], "Restored API records differ from source snapshot"
    assert media_hash(run_id, role) == fixture["media_hash"]
    print(f"{role}: household, membership, member, income, audit and media match")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "verify"))
    parser.add_argument("run_id")
    parser.add_argument("--role", choices=("source", "target"), default="source")
    args = parser.parse_args()
    if args.action == "run":
        if args.role != "source":
            parser.error("Synthetic setup runs only on source")
        run_scenario(args.run_id)
    else:
        verify_persistence(args.run_id, args.role)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AssertionError) as exc:
        print(f"Acceptance flow failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
