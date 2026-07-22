#!/usr/bin/env python3
"""adopt — take ownership of a check run's pointer (force / non-force modes).

Module-level public entry: ``adopt_run(run_id, force=False)``.
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


def adopt_run(run_id: str, force: bool = False) -> str:
    if not run_id:
        return "adopt:error:missing-run-id"
    POINTER_DIR.mkdir(parents=True, exist_ok=True)
    pointer = POINTER_DIR / f"{run_id}.json"
    existing = pointer.exists() and json.loads(pointer.read_text(encoding="utf-8"))
    if existing and not force:
        return f"adopt:blocked:{existing.get('owner_status', 'UNKNOWN')}"
    payload = {
        "run_id": run_id,
        "owner_status": "CHECK_ACTIVE",
        "adopted_at": _iso_now(),
        "force": force,
    }
    pointer.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return f"adopt:ok:{run_id}"


def main() -> int:
    run_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RUN_ID", "")
    force = (sys.argv[2].lower() == "force") if len(sys.argv) > 2 else False
    msg = adopt_run(run_id, force)
    print(msg)
    return 0 if msg.startswith("adopt:ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
