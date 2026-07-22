#!/usr/bin/env python3
"""start_check — initialize a check run's manifest + ownership pointer.

Module-level public entry: ``start_check(session_id, workspace_id, go_state_dir=None, go_run_id=None)``.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
_PROJECT = str(_HERE)
if _PROJECT not in sys.path:
    sys.path.insert(0, _PROJECT)

ARTIFACTS_ROOT = Path(os.environ.get("ARTIFACTS_ROOT", "P:/.claude/.artifacts"))
RUNS_DIR = ARTIFACTS_ROOT / "check-runs"
POINTER_DIR = ARTIFACTS_ROOT / "check-pointers"

MANIFEST_SCHEMA_VERSION = "check.manifest.v1"
STABLE_KEYS = frozenset({
    "MANIFEST_SCHEMA_VERSION", "run_id", "session_id", "workspace_id",
    "commit_hash", "diff_hash", "created_at", "owner_status",
})


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_hash(ref: str) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", ref],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _diff_hash(ref: str) -> str:
    try:
        out = subprocess.run(
            ["git", "diff", ref, "--unified=0"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            return ""
        h = hashlib.sha256()
        body = False
        for line in out.stdout.splitlines():
            if line.startswith("@@"):
                body = True
                continue
            if line.startswith("+++") or line.startswith("---") or line.startswith("diff --git"):
                body = False
                continue
            if body and (line.startswith("+") or line.startswith("-")):
                h.update((line[1:] + "\n").encode("utf-8"))
        return h.hexdigest()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _workspace_id() -> str:
    return os.environ.get("WORKSPACE_ID", "P:/") or "P:/"


def _generate_run_id(session_id: str, workspace_id: str) -> str:
    raw = (session_id + ":" + workspace_id).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _find_active_run(session_id: str, workspace_id: str):
    if not POINTER_DIR.exists():
        return None
    for path in sorted(POINTER_DIR.glob(f"{session_id}*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (
            payload.get("session_id") == session_id
            and payload.get("workspace_id") == workspace_id
            and payload.get("owner_status") == "CHECK_ACTIVE"
        ):
            return payload
    return None


def start_check(
    session_id: str,
    workspace_id: str,
    go_state_dir: Optional[str] = None,
    go_run_id: Optional[str] = None,
):
    existing = _find_active_run(session_id, workspace_id)
    if existing is not None:
        return {"ok": False, "reason": "active_run_exists", "existing": existing}

    run_id = _generate_run_id(session_id, workspace_id)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    POINTER_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "MANIFEST_SCHEMA_VERSION": MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "session_id": session_id,
        "workspace_id": workspace_id,
        "commit_hash": _git_hash("HEAD"),
        "diff_hash": _diff_hash("HEAD"),
        "created_at": _iso_now(),
        "owner_status": "CHECK_ACTIVE",
        "go_state_dir": go_state_dir or "",
        "go_run_id": go_run_id or "",
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    pointer = POINTER_DIR / f"{run_id}.json"
    pointer.write_text(json.dumps({**manifest, "last_seen": _iso_now()}, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "run_id": run_id,
        "manifest_path": str(manifest_path),
        "pointer_path": str(pointer),
        "run_dir": str(run_dir),
    }


def main() -> int:
    session_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SESSION_ID", "")
    workspace_id = sys.argv[2] if len(sys.argv) > 2 else _workspace_id()
    result = start_check(session_id, workspace_id)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
