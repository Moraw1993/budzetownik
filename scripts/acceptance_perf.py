"""Measure P95 for representative local HTTPS API operations."""

import argparse
import http.client
import json
import math
import os
import platform
import secrets
import ssl
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from acceptance_common import load_run
from acceptance_flow import create_income, resource_path
from acceptance_http import ApiSession

THREAD_SESSION = threading.local()


class PersistentApi:
    """Measure API responses over an authenticated reusable HTTPS connection."""

    def __init__(self, run_id, auth, role="source"):
        run_dir, manifest = load_run(run_id)
        context = ssl.create_default_context(cafile=run_dir / f"{role}-root.crt")
        self.connection = http.client.HTTPSConnection(
            "localhost", manifest[role]["port"], context=context, timeout=30
        )
        self.origin = auth.base
        self.cookie = "; ".join(f"{cookie.name}={cookie.value}" for cookie in auth.cookies)
        self.csrf_token = auth.csrf_token

    def request(self, method, path, payload=None, expected=(200,)):
        headers = {"Accept": "application/json", "Cookie": self.cookie}
        body = None
        if method != "GET":
            headers.update(
                {
                    "Origin": self.origin,
                    "Content-Type": "application/json",
                    "X-CSRFToken": self.csrf_token,
                }
            )
            body = json.dumps(payload).encode("utf-8")
        started = time.perf_counter()
        self.connection.request(method, path, body=body, headers=headers)
        response = self.connection.getresponse()
        content = response.read()
        elapsed_ms = (time.perf_counter() - started) * 1000
        result = json.loads(content) if content else None
        if response.status not in expected:
            raise AssertionError(f"{method} {path}: HTTP {response.status}; {result}")
        return result, elapsed_ms, response.status


def host_details():
    result = subprocess.run(
        ["docker", "info", "--format", "{{json .}}"],
        check=True,
        capture_output=True,
        text=True,
    )
    docker = json.loads(result.stdout)
    return {
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "docker_cpus": docker.get("NCPU"),
        "docker_memory_bytes": docker.get("MemTotal"),
        "docker_os": docker.get("OperatingSystem"),
        "docker_server": docker.get("ServerVersion"),
    }


def session(run_id, auth):
    client = getattr(THREAD_SESSION, "client", None)
    if client is None:
        client = PersistentApi(run_id, auth)
        THREAD_SESSION.client = client
    return client


def operation(client, name, household_id, index):
    if name == "list_households":
        return client.request("GET", "/api/households/")[1]
    if name == "list_members":
        return client.request("GET", resource_path(household_id, "members"))[1]
    if name == "list_income":
        return client.request("GET", resource_path(household_id, "income-sources"))[1]
    if name == "create_member":
        return client.request(
            "POST",
            resource_path(household_id, "members"),
            {"display_name": f"Pomiar {index} {secrets.token_hex(3)}"},
            expected=(201,),
        )[1]
    if name == "create_income":
        return client.request(
            "POST",
            resource_path(household_id, "income-sources"),
            {
                "name": f"Pomiar {index} {secrets.token_hex(3)}",
                "category": "test",
                "start_date": "2026-01-01",
                "default_monthly_amount": "12.34",
                "currency": "PLN",
                "frequency": "monthly",
            },
            expected=(201,),
        )[1]
    raise ValueError(f"Unknown operation: {name}")


def measure(run_id, auth, household_id, name, warmup, samples, concurrency, client_factory=session):
    def one(index):
        try:
            client = client_factory(run_id, auth)
            return {"ms": operation(client, name, household_id, index)}
        except (OSError, AssertionError, ValueError) as exc:
            return {"error": str(exc)}

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for result in pool.map(one, range(-warmup, 0)):
            if "error" in result:
                raise AssertionError(f"Warmup failed for {name}: {result['error']}")
        results = list(pool.map(one, range(samples)))
    timings = sorted(row["ms"] for row in results if "ms" in row)
    errors = [row["error"] for row in results if "error" in row]
    p95 = timings[math.ceil(len(timings) * 0.95) - 1] if timings else None
    return {
        "operation": name,
        "concurrency": concurrency,
        "warmup": warmup,
        "samples": samples,
        "successes": len(timings),
        "errors": len(errors),
        "error_examples": errors[:3],
        "p95_ms": round(p95, 2) if p95 is not None else None,
        "target_met": not errors and p95 is not None and p95 < 500,
    }


def run_benchmark(run_id, warmup, samples):
    run_dir, manifest = load_run(run_id)
    fixture = json.loads((run_dir / "fixture.json").read_text(encoding="utf-8"))
    username = fixture["owner"]
    password = manifest["user_password"]
    household_id = fixture["households"][0]
    auth = ApiSession(run_id, "source")
    auth.login(username, password)
    client = PersistentApi(run_id, auth)

    # Fix the initial dataset before measuring either read or write requests.
    for index in range(20):
        client.request(
            "POST",
            resource_path(household_id, "members"),
            {"display_name": f"Dane pomiarowe {index}"},
            expected=(201,),
        )
    for index in range(40):
        create_income(client, household_id, f"Źródło pomiarowe {index}")

    initial_counts = {
        resource: client.request("GET", resource_path(household_id, resource))[0]["count"]
        for resource in ("members", "income-sources")
    }
    results = []
    for concurrency in (1, 5):
        for name in (
            "list_households",
            "list_members",
            "list_income",
            "create_member",
            "create_income",
        ):
            result = measure(run_id, auth, household_id, name, warmup, samples, concurrency)
            results.append(result)
            print(
                f"{name}, concurrency {concurrency}: "
                f"P95={result['p95_ms']} ms, errors={result['errors']}"
            )
    final_counts = {
        resource: client.request("GET", resource_path(household_id, resource))[0]["count"]
        for resource in ("members", "income-sources")
    }
    report = {
        "host": host_details(),
        "dataset_before": initial_counts,
        "dataset_after": final_counts,
        "method": "HTTPS from localhost; P95 nearest rank; 20 warmups and 200 samples by default",
        "results": results,
    }
    output = run_dir / "performance.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Performance evidence: {output}")
    if any(not item["target_met"] for item in results):
        raise AssertionError("One or more operations missed the strict P95 < 500 ms target")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--samples", type=int, default=200)
    args = parser.parse_args()
    if args.warmup < 1 or args.samples < 1:
        parser.error("warmup and samples must be positive")
    run_benchmark(args.run_id, args.warmup, args.samples)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AssertionError, subprocess.CalledProcessError) as exc:
        print(f"Performance check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
