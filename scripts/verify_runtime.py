"""Verify local runtime without trusting its CA globally or touching user records."""

import json
import os
import ssl
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def docker(*args, capture=False):
    result = subprocess.run(
        ["docker", "compose", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else None


def backend(code):
    return docker(
        "exec",
        "-T",
        "backend",
        "python",
        "-c",
        "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); "
        "import django; django.setup(); " + code,
        capture=True,
    )


def health(expected=200, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                "https://localhost:8443/api/health/", context=context, timeout=20
            ) as response:
                status = response.status
                payload = json.load(response)
                if status == expected and payload == {"status": "ok"}:
                    return
        except urllib.error.HTTPError as exc:
            if exc.code == expected:
                assert json.load(exc) == {"status": "unavailable"}
                return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(1)
    raise AssertionError(f"Health did not reach {expected}")


docker("config", "--quiet")
(ROOT / ".runtime").mkdir(exist_ok=True)
docker("cp", "proxy:/data/caddy/pki/authorities/local/root.crt", ".runtime/localhost-root.crt")
context = ssl.create_default_context(cafile=str(ROOT / ".runtime/localhost-root.crt"))
health()
with urllib.request.urlopen("https://localhost:8443/", context=context, timeout=10) as response:
    assert response.status == 200
    homepage = response.read().decode()
    assert "Domowe Finanse" in homepage
    assert "Sprawdzanie dostępu" in homepage
print("PASS: verified HTTPS certificate, API and application shell", flush=True)

probe = "p" + uuid.uuid4().hex
create = (
    "from django.contrib.contenttypes.models import ContentType; from pathlib import Path; "
    f"ContentType.objects.create(app_label='runtime_probe', model='{probe}'); "
    f"Path('/app/media/{probe}.txt').write_text('{probe}'); print('probe created')"
)
check = (
    "from django.contrib.contenttypes.models import ContentType; from pathlib import Path; "
    f"assert ContentType.objects.filter(app_label='runtime_probe', model='{probe}').exists(); "
    f"assert Path('/app/media/{probe}.txt').read_text() == '{probe}'; print('probe preserved')"
)
cleanup = (
    "from django.contrib.contenttypes.models import ContentType; from pathlib import Path; "
    f"ContentType.objects.filter(app_label='runtime_probe', model='{probe}').delete(); "
    f"Path('/app/media/{probe}.txt').unlink(missing_ok=True)"
)
backend(create)
try:
    docker("up", "-d", "--force-recreate", "db", "migrate", "backend")
    health()
    backend(check)
    print("PASS: record and file survived recreation of DB and backend containers", flush=True)
    try:
        docker("stop", "db")
        health(expected=503, seconds=30)
        print("PASS: database outage returns 503 without details", flush=True)
    finally:
        docker("up", "-d", "db")
        health(seconds=60)
    backend(check)
    print("PASS: database recovery and persistence", flush=True)
finally:
    # Remove only this run's unique probe, not existing application records.
    backend(cleanup)

before = (ROOT / ".env").read_bytes()
subprocess.run(["powershell", "-File", "scripts/configure.ps1"], check=True)
assert (ROOT / ".env").read_bytes() == before
print("PASS: configuring twice does not replace secrets", flush=True)

env = os.environ.copy()
env["POSTGRES_PASSWORD"] = ""
invalid = subprocess.run(
    ["docker", "compose", "config", "--quiet"], env=env, capture_output=True, text=True
)
assert invalid.returncode != 0
assert "POSTGRES_PASSWORD" in invalid.stderr
assert "Run scripts/configure.ps1 first" in invalid.stderr
print("PASS: missing configuration fails with clear message", flush=True)
print("Runtime verification complete.", flush=True)
