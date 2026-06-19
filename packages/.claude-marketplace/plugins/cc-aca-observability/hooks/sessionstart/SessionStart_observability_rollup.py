#!/usr/bin/env python3
"""SessionStart Observability Rollup

Runs hook_observability_rollup.py ingest --reset once per day to rebuild
the unified hook_events_rollup table from all telemetry sources.

Throttled to at most once per 24 hours to avoid SessionStart overhead.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- plugin bootstrap ---
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; HOOKS_DIR = bootstrap(__file__)
# --- end bootstrap ---

_THROTTLE_FILE = HOOKS_DIR / "state" / "last_observability_rollup.txt"
_ROLLUP_SCRIPT = HOOKS_DIR / "hook_observability_rollup.py"

ENABLED = os.environ.get("OBSERVABILITY_ROLLUP_ENABLED", "true").lower() in ("1", "true", "yes")


def _should_run() -> bool:
    if not _ROLLUP_SCRIPT.exists():
        return False
    if not _THROTTLE_FILE.exists():
        return True
    try:
        last = datetime.fromisoformat(_THROTTLE_FILE.read_text().strip())
        return (datetime.now(timezone.utc) - last) > timedelta(hours=24)
    except Exception:
        return True


def _update_throttle() -> None:
    try:
        _THROTTLE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _THROTTLE_FILE.write_text(datetime.now(timezone.utc).isoformat())
    except Exception:
        pass


def main() -> None:
    if not ENABLED or not _should_run():
        return
    try:
        result = subprocess.run(
            [sys.executable, str(_ROLLUP_SCRIPT), "ingest", "--reset"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            _update_throttle()
    except Exception:
        pass


if __name__ == "__main__":
    main()
