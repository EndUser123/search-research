#!/usr/bin/env python3
"""stop_gate — Stop hook that gates continuation based on /go/check ownership.

Module-level public entry: ``check_continuation(payload)``.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ARTIFACTS_ROOT = Path(os.environ.get("ARTIFACTS_ROOT", "P:/.claude/.artifacts"))
RUNS_DIR = ARTIFACTS_ROOT / "check-runs"
POINTER_DIR = ARTIFACTS_ROOT / "check-pointers"
GO_SESSIONS_DIR = ARTIFACTS_ROOT / "go-sessions"

STALE_TTL_SECONDS = int(os.environ.get("STALE_TTL_SECONDS", "3600"))
OWN_STALE_TTL_SECONDS = int(os.environ.get("OWN_STALE_TTL_SECONDS", "1800"))


def _parse_payload() -> dict:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def _payload_session_id(payload: dict) -> str:
    for key in ("session_id", "sessionId", "dc_session_id", "session"):
        v = payload.get(key)
        if isinstance(v, str) and v:
            return v
    return ""


def _read_check_pointer(session_id: str):
    if not session_id:
        return None
    if not POINTER_DIR.exists():
        return None
    for path in sorted(POINTER_DIR.glob("*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("session_id") == session_id:
            return payload
    return None


def _read_manifest(run_id: str):
    if not run_id:
        return None
    path = RUNS_DIR / run_id / "manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _update_pointer_timestamp(session_id: str) -> None:
    if not POINTER_DIR.exists():
        return
    for path in POINTER_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("session_id") != session_id:
            continue
        payload["last_seen"] = _iso_now()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return


def _go_pointer_valid(session_id: str) -> bool:
    if not session_id or not GO_SESSIONS_DIR.exists():
        return False
    path = GO_SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return payload.get("owner_status") in ("GO_ACTIVE", "GO_PENDING")


def _pointer_stale(pointer: dict) -> bool:
    last_seen = pointer.get("last_seen") or pointer.get("updated_at", "")
    if not last_seen:
        return True
    try:
        dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - dt).total_seconds() > STALE_TTL_SECONDS


def _own_pointer_stale(pointer: dict) -> bool:
    last_seen = pointer.get("last_seen") or pointer.get("updated_at", "")
    if not last_seen:
        return True
    try:
        dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - dt).total_seconds() > OWN_STALE_TTL_SECONDS


def _transition_owner_lost(manifest: dict, _run_id: str) -> bool:
    if not manifest:
        return False
    owner_session = manifest.get("session_id", "")
    if not owner_session:
        return False
    return not _go_pointer_valid(owner_session)


def _run_validator(run_id: str):
    manifest = _read_manifest(run_id)
    if manifest is None:
        return (False, "manifest_missing", None)
    if _pointer_stale(manifest):
        return (False, "pointer_stale", manifest)
    if _transition_owner_lost(manifest, run_id):
        return (False, "owner_lost", manifest)
    return (True, "ok", manifest)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def check_continuation(payload: dict) -> dict:
    session_id = _payload_session_id(payload)
    if not session_id:
        return {"decision": "approve", "reason": "no_session_id"}

    pointer = _read_check_pointer(session_id)
    if pointer is None:
        return {"decision": "approve", "reason": "no_check_pointer"}

    run_id = pointer.get("run_id", "")
    if _own_pointer_stale(pointer):
        return {"decision": "block", "reason": "own_pointer_stale", "run_id": run_id}

    ok, reason, _manifest = _run_validator(run_id)
    if not ok:
        return {"decision": "block", "reason": reason, "run_id": run_id}

    _update_pointer_timestamp(session_id)
    return {"decision": "approve", "reason": "ok", "run_id": run_id}


def main() -> int:
    payload = _parse_payload()
    result = check_continuation(payload)
    print(json.dumps(result, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
