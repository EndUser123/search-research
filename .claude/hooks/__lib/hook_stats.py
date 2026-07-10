#!/usr/bin/env python3
"""Hook firing telemetry - record(hook_name, outcome) -> JSONL append log.

Used by the small number of top-level hook dispatchers (settings.json entry points
and plugin __lib/router.py files) to count how often each hook fires, blocks,
warns, or is overridden. NOT used by the ~1100 individual hook files.

Concurrency: hooks may be invoked from many terminals simultaneously. We append
one line per event in O_APPEND mode, which is atomic for a single write() of a
small line on both POSIX and Windows. No temp+os.replace here - that clobbers an
append log; append is the spec-sanctioned path.

Storage: $STATE_DIR/hook_stats.jsonl (one JSON object per line). Schema:
    {"ts": "2026-07-09T12:34:56+00:00", "hook": "<name>",
     "outcome": "fire|block|warn|override", "session_id": "..."}

Outcome vocabulary:
  - fire:     dispatcher entered
  - block:    hook returned a deny/block decision
  - warn:     hook returned a non-blocking advisory
  - override: an external layer (e.g. allowlist) overrode the hook
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

OUTCOMES = frozenset({"fire", "block", "warn", "override"})

# State dir resolution: prefer explicit override, then P:/.claude/state.
STATE_DIR = Path(os.environ.get("CLAUDE_STATE_DIR") or "P:/.claude/state")
LOG_PATH = STATE_DIR / "hook_stats.jsonl"


def record(hook_name: str, outcome: str, *, session_id: str | None = None) -> None:
    """Append one telemetry event. Failures are swallowed (never crash a hook).

    Telemetry is best-effort: if the state dir is unwritable we skip silently.
    """
    try:
        if outcome not in OUTCOMES:
            outcome = "fire"  # unknown outcome -> coerce so the counter stays useful
        evt = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "hook": str(hook_name),
            "outcome": outcome,
            "session_id": session_id,
        }
        line = json.dumps(evt, ensure_ascii=False, separators=(",", ":")) + "\n"
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        # O_APPEND: single write() of one line is atomic across processes.
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        return  # telemetry must never break a hook


if __name__ == "__main__":
    # Smoke entrypoints:
    #   python __lib/hook_stats.py                      -> record a smoke fire
    #   python __lib/hook_stats.py record HookName fire -> record one event
    if len(sys.argv) >= 4 and sys.argv[1] == "record":
        record(sys.argv[2], sys.argv[3])
    else:
        record("hook_stats.smoke", "fire")
    print(f"ok: {LOG_PATH}")
