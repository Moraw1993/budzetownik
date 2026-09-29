"""Create, back up, and restore isolated Compose acceptance installations."""

import argparse
import json
import secrets
import shutil
import socket
import sys
import time

from acceptance_common import PROJECT_PREFIX, RUNS, compose, load_run

DATABASE = "myhomebudget"
MEDIA_EXPORT = """
import sys
import tarfile
from pathlib import Path

root = Path('/app/media')
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
    for entry in sorted(root.rglob('*')):
        archive.add(entry, arcname=str(entry.relative_to(root)), recursive=False)
"""
MEDIA_IMPORT = """
import sys
import tarfile

with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as archive:
    for entry in archive:
        if not (entry.isfile() or entry.isdir()):
            raise ValueError('Unexpected media archive entry')
        archive.extract(entry, path='/app/media', filter='data')
"""


def unused_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def init_run():
    """Create private synthetic credentials and two distinct Compose projects."""
    RUNS.mkdir(parents=True, exist_ok=True)
    while True:
        run_id = secrets.token_hex(4)
        run_dir = RUNS / run_id
        try:
            run_dir.mkdir()
            break
        except FileExistsError:
            continue

    database_password = secrets.token_urlsafe(48)
    django_key = secrets.token_urlsafe(48)
    user_password = f"Acceptance-{secrets.token_urlsafe(24)}!"
    ports = (unused_port(), unused_port())
    while ports[0] == ports[1]:
        ports = (ports[0], unused_port())
    manifest = {"run_id": run_id, "user_password": user_password}
    for role, port in zip(("source", "target"), ports, strict=True):
        manifest[role] = {
            "project": f"{PROJECT_PREFIX}{run_id}-{role}",
            "port": port,
        }
        values = {
            "POSTGRES_DB": DATABASE,
            "POSTGRES_USER": DATABASE,
            "POSTGRES_PASSWORD": database_password,
            "DJANGO_SECRET_KEY": django_key,
            "ACCEPTANCE_HTTPS_PORT": str(port),
        }
        (run_dir / f"{role}.env").write_text(
            "".join(f"{key}={value}\n" for key, value in values.items()),
            encoding="utf-8",
        )
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Acceptance run: {run_id}")
    print(f"Isolated HTTPS ports: source={ports[0]}, target={ports[1]}")


def wait_for_stack(run_id, role):
    """Wait for migrations and the three application services to become ready."""
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        result = compose(run_id, role, "ps", "-a", "--format", "json", capture_output=True)
        records = [json.loads(line) for line in result.stdout.splitlines() if line]
        services = {item["Service"]: item for item in records}
        healthy = all(
            services.get(name, {}).get("Health") == "healthy"
            for name in ("db", "backend", "frontend")
        )
        migrated = services.get("migrate", {}).get("ExitCode") == 0
        proxy = services.get("proxy", {}).get("State") == "running"
        if healthy and migrated and proxy:
            return
        time.sleep(2)
    raise TimeoutError(f"Isolated {role} stack did not become healthy")


def up(run_id, role, *, recreate=False):
    options = ["up", "-d", "--build"]
    if recreate:
        options.append("--force-recreate")
    compose(run_id, role, *options)
    wait_for_stack(run_id, role)
    run_dir, _ = load_run(run_id)
    compose(
        run_id,
        role,
        "cp",
        "proxy:/data/caddy/pki/authorities/local/root.crt",
        str(run_dir / f"{role}-root.crt"),
    )
    print(f"Isolated {role} stack is healthy")


def backup(run_id):
    """Capture database, media and configuration while source writes are stopped."""
    run_dir, _ = load_run(run_id)
    destination = run_dir / "backup"
    destination.mkdir(exist_ok=False)
    compose(run_id, "source", "stop", "backend", "frontend", "proxy")
    try:
        with (destination / "database.dump").open("wb") as stream:
            compose(
                run_id,
                "source",
                "exec",
                "-T",
                "db",
                "pg_dump",
                "-U",
                DATABASE,
                "-d",
                DATABASE,
                "-Fc",
                stdout=stream,
            )
        with (destination / "media.tar").open("wb") as stream:
            compose(
                run_id,
                "source",
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "backend",
                "python",
                "-c",
                MEDIA_EXPORT,
                stdout=stream,
            )
        shutil.copyfile(run_dir / "source.env", destination / "config.env")
    finally:
        compose(run_id, "source", "up", "-d", "backend", "frontend", "proxy")
        wait_for_stack(run_id, "source")
    print(f"Backup created under {destination}")


def restore(run_id):
    """Restore only into the matching fresh target project."""
    run_dir, _ = load_run(run_id)
    backup_dir = run_dir / "backup"
    for name in ("database.dump", "media.tar", "config.env"):
        if not (backup_dir / name).is_file():
            raise FileNotFoundError(backup_dir / name)
    source_config = (backup_dir / "config.env").read_text(encoding="utf-8")
    target_config = (run_dir / "target.env").read_text(encoding="utf-8")
    for line in source_config.splitlines():
        if not line.startswith("ACCEPTANCE_HTTPS_PORT=") and line not in target_config:
            raise ValueError("Target configuration does not match backup")

    up(run_id, "target")
    compose(run_id, "target", "stop", "backend", "frontend", "proxy")
    with (backup_dir / "database.dump").open("rb") as stream:
        compose(
            run_id,
            "target",
            "exec",
            "-T",
            "db",
            "pg_restore",
            "--exit-on-error",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "-U",
            DATABASE,
            "-d",
            DATABASE,
            stdin=stream,
        )
    with (backup_dir / "media.tar").open("rb") as stream:
        compose(
            run_id,
            "target",
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "backend",
            "python",
            "-c",
            MEDIA_IMPORT,
            stdin=stream,
        )
    compose(run_id, "target", "up", "-d", "backend", "frontend", "proxy")
    wait_for_stack(run_id, "target")
    print("Backup restored into the isolated target project")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "up", "recreate", "backup", "restore", "stop"))
    parser.add_argument("run_id", nargs="?")
    parser.add_argument("--role", choices=("source", "target"), default="source")
    args = parser.parse_args()
    if args.action == "init":
        init_run()
        return
    if args.run_id is None:
        parser.error("run_id is required after init")
    if args.action == "up":
        up(args.run_id, args.role)
    elif args.action == "recreate":
        up(args.run_id, args.role, recreate=True)
    elif args.action == "backup":
        backup(args.run_id)
    elif args.action == "restore":
        restore(args.run_id)
    else:
        compose(args.run_id, args.role, "stop")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TimeoutError) as exc:
        print(f"Acceptance stack failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
