#!/usr/bin/env python3
"""detect_context — locate the active /go session that owns this check run.

Module-level public entry: ``detect_context(session_id)``.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT = str(_HERE)
if _PROJECT not in sys.path:
    sys.path.insert(0, _PROJECT)

STALE_TTL_SECONDS = int(os.environ.get("STALE_TTL_SECONDS", "3600"))
ARTIFACTS_ROOT = Path(os.environ.get("ARTIFACTS_ROOT", "P:/.claude/.artifacts"))
GO_SESSIONS_DIR = ARTIFACTS_ROOT / "go-sessions"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_go_pointer(session_id: str):
    pointer = GO_SESSIONS_DIR / f"{session_id}.json"
    if not pointer.exists():
        return None, None
    try:
        return pointer, json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return pointer, None


def _parse_iso_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def detect_context(session_id: str) -> dict:
    pointer, payload = _read_go_pointer(session_id)
    if pointer is None:
        return {
            "session_id": session_id,
            "pointer_path": "",
            "run_id": "",
            "workspace_id": "",
            "owner_status": "MISSING",
            "last_seen": "",
            "is_stale": True,
            "pointer_age_seconds": float("inf"),
            "source": "missing",
            "detected_at": _iso_now(),
            "notes": ["go_pointer_absent"],
        }
    if payload is None:
        return {
            "session_id": session_id,
            "pointer_path": str(pointer),
            "run_id": "",
            "workspace_id": "",
            "owner_status": "UNREADABLE",
            "last_seen": "",
            "is_stale": True,
            "pointer_age_seconds": float("inf"),
            "source": "unreadable",
            "detected_at": _iso_now(),
            "notes": ["pointer_unreadable"],
        }
    last_seen = payload.get("last_seen") or payload.get("updated_at", "")
    last_dt = _parse_iso_timestamp(last_seen)
    age = (time.time() - last_dt.timestamp()) if last_dt else float("inf")
    return {
        "session_id": session_id,
        "pointer_path": str(pointer),
        "run_id": payload.get("run_id", ""),
        "workspace_id": payload.get("workspace_id", ""),
        "owner_status": payload.get("owner_status", "UNKNOWN"),
        "last_seen": last_seen,
        "is_stale": age > STALE_TTL_SECONDS,
        "pointer_age_seconds": age,
        "source": "go_pointer",
        "detected_at": _iso_now(),
        "notes": [],
    }


def main() -> int:
    session_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SESSION_ID", "")
    result = detect_context(session_id)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
