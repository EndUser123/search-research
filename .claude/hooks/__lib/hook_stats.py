#!/usr/bin/env python3
"""Hook firing telemetry - record(hook_name, outcome) -> JSONL append log.

Used by the top-level hook dispatchers to count hook firings AND outcomes
(fire/block; warn/override are a refinement). NOT the ~1100 individual hooks.

Outcome is determined by each DISPATCHER at its return path, where it already
knows the result (e.g. hook_runner maps exit code 2 -> "block"). Passive loggers
that do not gate (log_hook) record "fire" only - they cannot observe a block.

Concurrency: writes go through file_lock.append_jsonl_safe (cross-process lock +
dropped-trace on contention). Rotation caps growth at MAX_BYTES.

Storage: $STATE_DIR/hook_stats.jsonl. Schema:
    {"ts": "...", "hook": "<name>", "outcome": "fire|block", "session_id": "..."}
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

OUTCOMES = frozenset({"fire", "block", "warn", "override"})

STATE_DIR = Path(os.environ.get("CLAUDE_STATE_DIR") or "P:/.claude/state")
LOG_PATH = STATE_DIR / "hook_stats.jsonl"

# ponytail: fixed 5 MB ceiling + keep-tail rotation; revisit if telemetry volume
# grows enough that rotating on the hook hot path shows in a profile.
MAX_BYTES = 5 * 1024 * 1024
KEEP_TAIL_LINES = 5000

try:
    from file_lock import append_jsonl_safe, FileLock
except ImportError:
    from __lib.file_lock import append_jsonl_safe, FileLock


def _maybe_rotate() -> None:
    """Cap log growth: when over MAX_BYTES, keep only the tail lines."""
    try:
        if not LOG_PATH.exists() or LOG_PATH.stat().st_size < MAX_BYTES:
            return
        with FileLock(LOG_PATH.with_suffix(".lock")):
            if not LOG_PATH.exists() or LOG_PATH.stat().st_size < MAX_BYTES:
                return
            lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
            LOG_PATH.write_text("\n".join(lines[-KEEP_TAIL_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def record(hook_name: str, outcome: str, *, session_id: str | None = None) -> None:
    """Append one telemetry event. Failures are swallowed (never crash a hook)."""
    try:
        if outcome not in OUTCOMES:
            outcome = "fire"
        evt = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "hook": str(hook_name),
            "outcome": outcome,
            "session_id": session_id,
        }
        _maybe_rotate()
        append_jsonl_safe(LOG_PATH, evt)
    except Exception:
        return


if __name__ == "__main__":
    # Smoke:
    #   python __lib/hook_stats.py                      -> record a smoke fire
    #   python __lib/hook_stats.py record HookName fire -> record one event
    if len(sys.argv) >= 4 and sys.argv[1] == "record":
        record(sys.argv[2], sys.argv[3])
    else:
        record("hook_stats.smoke", "fire")
    print(f"ok: {LOG_PATH}")
