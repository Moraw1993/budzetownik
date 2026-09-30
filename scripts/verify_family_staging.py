"""Verify only the guarded target installation restored from family acceptance data."""

import argparse
import json

from acceptance_common import ROOT, compose, load_run
from acceptance_flow import expect_denied, resource_path
from acceptance_http import ApiSession
from acceptance_perf import PersistentApi, measure
from family_acceptance import api_snapshot


def verify(run_id):
    run_dir, manifest = load_run(run_id)
    fixture = json.loads((run_dir / "family-fixture.json").read_text(encoding="utf-8"))
    expected = json.loads((run_dir / "family-api-snapshot.json").read_text(encoding="utf-8"))
    owner = ApiSession(run_id, "target")
    owner.login(fixture["users"]["owner"], manifest["user_password"])
    assert api_snapshot(owner, fixture["households"]) == expected, "Restored API data differs"
    compose(
        run_id,
        "target",
        "run",
        "--rm",
        "--no-deps",
        "-T",
        "-v",
        f"{ROOT / 'scripts'}:/acceptance:ro",
        "-v",
        f"{run_dir}:/evidence:ro",
        "-e",
        "FAMILY_ACCEPTANCE_ACTION=verify",
        "backend",
        "python",
        "manage.py",
        "shell",
        "-c",
        "import runpy; runpy.run_path('/acceptance/family_acceptance_data.py', run_name='__main__')",
    )
    print("Restored API and all domain database tables match dev")
    home, foreign = fixture["households"]
    path = resource_path(home, "companies")
    company = owner.request("POST", path, {"name": "Staging smoke company"}, expected=(201,))[0]
    detail = path + company["id"] + "/"
    edited = owner.request("PATCH", detail, {"name": "Staging smoke edited"})[0]
    assert edited["name"] == "Staging smoke edited"
    owner.request("POST", detail + "archive/", {})
    owner.request("GET", detail)
    for role in ("administrator", "member", "viewer"):
        client = ApiSession(run_id, "target")
        client.login(fixture["users"][role], manifest["user_password"])
        client.request("GET", path)
        expect_denied(client, "GET", resource_path(foreign, "companies"))
        if role != "administrator":
            expect_denied(client, "POST", path, {"name": "Denied staging write"})
    owner.request("POST", path, {"name": ""}, expected=(400,))
    print("CRUD, validation, roles and foreign household denial passed")

    client = PersistentApi(run_id, owner, "target")

    def staging_session(_run_id, auth):
        return client

    try:
        results = [
            measure(run_id, owner, home, name, 10, 100, 1, client_factory=staging_session)
            for name in ("list_households", "list_members", "list_income")
        ]
    finally:
        client.connection.close()
    report = {"run_id": run_id, "environment": "staging", "results": results}
    (run_dir / "staging-verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    for result in results:
        print(f"{result['operation']}: P95={result['p95_ms']} ms, errors={result['errors']}")
    assert all(result["target_met"] for result in results), "Staging P95 target missed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    verify(parser.parse_args().run_id)
