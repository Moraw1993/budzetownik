"""Shared paths and guarded Compose calls for isolated acceptance runs."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / ".runtime" / "acceptance"
RUN_ID = re.compile(r"[0-9a-f]{8}\Z")
PROJECT_PREFIX = "myhomebudget-acceptance-"


def load_run(run_id):
    """Load only a run created under the dedicated ignored workspace directory."""
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("Run ID must contain exactly eight lowercase hex digits")
    run_dir = RUNS / run_id
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    for role in ("source", "target"):
        expected = f"{PROJECT_PREFIX}{run_id}-{role}"
        if manifest[role]["project"] != expected:
            raise ValueError(f"Unexpected Compose project for {role}")
        if not (run_dir / f"{role}.env").is_file():
            raise ValueError(f"Missing isolated environment for {role}")
    return run_dir, manifest


def compose(run_id, role, *args, stdin=None, stdout=None, capture_output=False):
    """Run Compose with an explicit isolated project and environment file."""
    run_dir, manifest = load_run(run_id)
    if role not in ("source", "target"):
        raise ValueError("Role must be source or target")
    command = [
        "docker",
        "compose",
        "--env-file",
        str(run_dir / f"{role}.env"),
        "-p",
        manifest[role]["project"],
        "-f",
        str(ROOT / "compose.yaml"),
        "-f",
        str(ROOT / "compose.acceptance.yaml"),
        *args,
    ]
    return subprocess.run(
        command,
        check=True,
        cwd=ROOT,
        stdin=stdin,
        stdout=stdout,
        capture_output=capture_output,
    )


def base_url(manifest, role):
    return f"https://localhost:{manifest[role]['port']}"
