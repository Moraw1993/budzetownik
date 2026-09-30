"""Prepare and verify the isolated family-income acceptance installation."""

import argparse
import json
import os
import subprocess

from acceptance_common import ROOT, compose, load_run
from acceptance_flow import expect_denied, income_data, resource_path
from acceptance_http import ApiSession
from acceptance_stack import up, wait_for_stack


def database_action(run_id, action):
    run_dir, manifest = load_run(run_id)
    os.environ["FAMILY_ACCEPTANCE_PASSWORD"] = manifest["user_password"]
    compose(
        run_id,
        "source",
        "run",
        "--rm",
        "--no-deps",
        "-T",
        "-v",
        f"{ROOT / 'scripts'}:/acceptance:ro",
        "-v",
        f"{run_dir}:/evidence",
        "-e",
        f"FAMILY_ACCEPTANCE_ACTION={action}",
        "-e",
        f"FAMILY_ACCEPTANCE_RUN={run_id}",
        "-e",
        "FAMILY_ACCEPTANCE_PASSWORD",
        "backend",
        "python",
        "manage.py",
        "shell",
        "-c",
        "import runpy; runpy.run_path('/acceptance/family_acceptance_data.py', run_name='__main__')",
    )


def prepare(run_id):
    run_dir, _ = load_run(run_id)
    if (run_dir / "family-fixture.json").exists():
        raise ValueError("Family fixture already exists; use a fresh run")
    compose(run_id, "source", "build", "backend")
    compose(run_id, "source", "up", "-d", "--wait", "db")
    database_action(run_id, "seed")
    up(run_id, "source")
    database_action(run_id, "migration")


def session(run_id, role):
    run_dir, manifest = load_run(run_id)
    fixture = json.loads((run_dir / "family-fixture.json").read_text(encoding="utf-8"))
    client = ApiSession(run_id, "source")
    client.login(fixture["users"][role], manifest["user_password"])
    return client, fixture


def all_rows(client, path):
    """Follow the API's numbered pagination so comparisons include every row."""
    result = []
    page = 1
    while True:
        payload = client.request("GET", f"{path}?page={page}")[0]
        result.extend(payload["results"])
        if not payload["next"]:
            return sorted(result, key=lambda row: row["id"])
        page += 1


def api_snapshot(client, households):
    return {
        home: {
            resource: all_rows(client, resource_path(home, resource))
            for resource in ("members", "companies", "contracts", "income-sources", "audit-logs")
        }
        for home in households
    }


def contract_data(member, company, name="Umowa HTTP"):
    return {
        "member_id": member,
        "company_id": company,
        "name": name,
        "contract_type": "employment",
        "position": "Specjalista",
        "gross_amount": "8500.25",
        "gross_basis": "monthly",
        "currency": "PLN",
        "start_date": "2026-01-01",
        "end_date": None,
    }


def check_access(run_id):
    """Real CSRF/session requests, state and audit comparisons after rejected writes."""
    owner, fixture = session(run_id, "owner")
    first, second = fixture["households"]
    companies = []
    for home in (first, second):
        company = owner.request(
            "POST",
            resource_path(home, "companies"),
            {"name": f"Firma HTTP {home}"},
            expected=(201,),
        )[0]
        companies.append(company["id"])
    agreement = owner.request(
        "POST",
        resource_path(second, "contracts"),
        contract_data(fixture["members"][1], companies[1]),
        expected=(201,),
    )[0]
    local_agreement = owner.request(
        "POST",
        resource_path(first, "contracts"),
        contract_data(fixture["members"][0], companies[0]),
        expected=(201,),
    )[0]
    local_source = owner.request(
        "POST",
        resource_path(first, "income-sources"),
        income_data("Źródło kontroli HTTP"),
        expected=(201,),
    )[0]
    baseline = api_snapshot(owner, (first, second))
    valid = contract_data(fixture["members"][0], companies[0])
    for role in ("member", "viewer"):
        reader, _ = session(run_id, role)
        for resource in ("members", "companies", "contracts", "income-sources"):
            assert reader.request("GET", resource_path(first, resource))[2] == 200
        for resource, payload in (
            ("members", {"display_name": "Odrzucona osoba"}),
            ("companies", {"name": "Odrzucona firma"}),
            ("contracts", valid),
            ("income-sources", income_data("Odrzucone")),
        ):
            expect_denied(reader, "POST", resource_path(first, resource), payload)
        for resource, record, payload, archive in (
            ("companies", companies[0], {"name": "Odrzucona edycja"}, "archive"),
            (
                "contracts",
                local_agreement["id"],
                {"name": "Odrzucona", "expected_version": 1},
                "archive",
            ),
            (
                "income-sources",
                local_source["id"],
                {"name": "Odrzucona", "expected_version": 1},
                "deactivate",
            ),
        ):
            detail = resource_path(first, resource) + record + "/"
            expect_denied(reader, "PATCH", detail, payload)
            expect_denied(reader, "POST", detail + archive + "/", {})
        expect_denied(
            reader,
            "POST",
            resource_path(first, "income-sources") + local_source["id"] + "/convert-to-contract/",
            {**valid, "expected_version": 1},
        )
        assert api_snapshot(owner, (first, second)) == baseline, (
            f"Denied {role} writes changed state/audit"
        )
    for role in ("owner", "administrator", "member", "viewer"):
        client, _ = session(run_id, role)
        for resource, record in (
            ("companies", companies[1]),
            ("members", fixture["members"][1]),
            ("income-sources", fixture["foreign_source"]),
            ("contracts", agreement["id"]),
        ):
            expect_denied(client, "GET", resource_path(first, resource) + record + "/")
            if role != "owner":
                expect_denied(client, "GET", resource_path(second, resource))
    for values in ({"member_id": fixture["members"][1]}, {"company_id": companies[1]}):
        owner.request(
            "POST", resource_path(first, "contracts"), {**valid, **values}, expected=(400,)
        )
        owner.request(
            "POST",
            resource_path(first, "income-sources") + local_source["id"] + "/convert-to-contract/",
            {**valid, **values, "expected_version": 1},
            expected=(400,),
        )
    owner.request(
        "POST",
        resource_path(first, "income-sources"),
        income_data("Obce powiązanie", fixture["members"][1]),
        expected=(400,),
    )
    assert api_snapshot(owner, (first, second)) == baseline, "Foreign links changed state or audit"
    (load_run(run_id)[0] / "family-access-result.json").write_text(
        json.dumps(
            {
                "roles": ["owner", "administrator", "member", "viewer"],
                "state_and_audit_unchanged": True,
                "foreign_snapshot": baseline[second],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Family roles, foreign IDs/links and unchanged data/audit verified")


def checkpoint(run_id):
    owner, fixture = session(run_id, "owner")
    run_dir, _ = load_run(run_id)
    snapshot = api_snapshot(owner, fixture["households"])
    access = json.loads((run_dir / "family-access-result.json").read_text(encoding="utf-8"))
    assert snapshot[fixture["households"][1]] == access["foreign_snapshot"], (
        "UI operations changed the foreign household"
    )
    (run_dir / "family-api-snapshot.json").write_text(
        json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
    )
    database_action(run_id, "snapshot")


def verify_restart(run_id):
    run_dir, _ = load_run(run_id)
    if not (run_dir / "family-api-snapshot.json").exists():
        raise ValueError("Create a checkpoint after UI tests before restarting")
    compose(run_id, "source", "restart", "db", "backend", "frontend", "proxy")
    wait_for_stack(run_id, "source")
    owner, fixture = session(run_id, "owner")
    expected = json.loads((run_dir / "family-api-snapshot.json").read_text(encoding="utf-8"))
    assert api_snapshot(owner, fixture["households"]) == expected, (
        "API snapshot changed after restart"
    )
    database_action(run_id, "verify")
    print("API and all domain database tables preserved after restart")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "access", "checkpoint", "restart"))
    parser.add_argument("run_id")
    args = parser.parse_args()
    {
        "prepare": prepare,
        "access": check_access,
        "checkpoint": checkpoint,
        "restart": verify_restart,
    }[args.action](args.run_id)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AssertionError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Family acceptance failed: {exc}") from exc
