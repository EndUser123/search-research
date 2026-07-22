#!/usr/bin/env python3
"""abandon — release a check run's ownership pointer (mark as abandoned).

Module-level public entry: ``abandon_run(run_id, reason)``.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ARTIFACTS_ROOT = Path(os.environ.get("ARTIFACTS_ROOT", "P:/.claude/.artifacts"))
POINTER_DIR = ARTIFACTS_ROOT / "check-pointers"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def abandon_run(run_id: str, reason: str) -> str:
    if not run_id:
        return "abandon:error:missing-run-id"
    POINTER_DIR.mkdir(parents=True, exist_ok=True)
    pointer = POINTER_DIR / f"{run_id}.json"
    payload = {
        "run_id": run_id,
        "owner_status": "ABANDONED",
        "reason": reason,
        "abandoned_at": _iso_now(),
    }
    pointer.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return f"abandon:ok:{run_id}"


def main() -> int:
    run_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RUN_ID", "")
    reason = sys.argv[2] if len(sys.argv) > 2 else "manual"
    msg = abandon_run(run_id, reason)
    print(msg)
    return 0 if msg.startswith("abandon:ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
