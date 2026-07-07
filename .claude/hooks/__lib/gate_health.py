"""Runtime gate-fault log — the dead-gate channel.

When a hook/gate crashes at runtime and is swallowed by an `except Exception`
wrapper, the failure is invisible: the gate is dead but nobody knows. This
module records those faults to one JSONL file so SessionStart can surface them.

Why this exists (transcript 2026-06-22): `_run_gate_safe` in Stop.py caught
every gate exception but only printed to stderr (a one-second UI flicker then
gone). The fake-done detector and others were effectively dead across a whole
session and the human couldn't tell. A persistent log + a SessionStart read
makes dead gates visible at the next session start.

Design:
- record_fault(): append one JSONL line. Best-effort, never raises.
- read_recent_faults(): return faults within `since_hours`, deduped by
  (event, gate, error_type) keeping the most recent.
- No throttle, no rotation by default. Faults are exceptional events, not
  per-turn telemetry, so the file grows slowly. session_data_retention.cleanup
- is expected to handle long-term rotation.

# ponytail: ceiling — unbounded append if a gate faults every turn (e.g. a
# broken gate run on every PreToolUse). Upgrade path: cap at N lines with head
# trim if the file exceeds 2*N, or add a (gate, error_type) hourly throttle.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = _HOOKS_DIR / "logs" / "diagnostics" / "gate_faults.jsonl"


def record_fault(event: str, gate: str, error: str, *, terminal_id: str = "") -> None:
    """Append a gate fault. Best-effort: never raises.

    Args:
        event: Hook event ("PreToolUse" | "Stop" | "PostToolUse" | ...).
        gate: Gate/hook name (e.g. "fake_done", "investigation_gate").
        error: Short error string (repr(e) or str(e)).
        terminal_id: Optional terminal scoping for context.
    """
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "epoch": int(time.time()),
            "event": str(event),
            "gate": str(gate),
            "error": str(error)[:300],
            "terminal_id": str(terminal_id or ""),
        }
        from file_lock import append_jsonl_safe
        append_jsonl_safe(LOG_PATH, entry, ensure_ascii=False)
    except OSError:
        # Logging must never break the hook. Fail truly silently here — the
        # alternative (raising) would turn the dead-gate alarm into a new
        # source of dead gates.
        pass


def read_recent_faults(since_hours: float = 24.0) -> list[dict]:
    """Return faults newer than since_hours, deduped by (event, gate, error_type).

    Keeps the most recent entry per dedup key. Sorted newest-first. Never raises.
    """
    try:
        if not LOG_PATH.exists():
            return []
        cutoff = int(time.time()) - int(since_hours * 3600)
        seen: dict[tuple, dict] = {}
        with open(LOG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                if entry.get("epoch", 0) < cutoff:
                    continue
                # Dedup key: (event, gate, error_type-class prefix).
                # Group by error family so 100 identical NameErrors collapse to 1.
                err = str(entry.get("error", ""))
                err_family = err.split(":")[0] if ":" in err else err[:40]
                key = (entry.get("event", ""), entry.get("gate", ""), err_family)
                seen[key] = entry
        result = sorted(
            seen.values(),
            key=lambda e: e.get("epoch", 0),
            reverse=True,
        )
        return result
    except Exception:
        return []


if __name__ == "__main__":
    # Self-check: record one fault, read it back.
    record_fault("Stop", "gate_health_selftest", "SelftestError: smoke")
    recent = read_recent_faults(since_hours=1.0)
    assert any(
        e.get("gate") == "gate_health_selftest" for e in recent
    ), f"selftest fault not read back: {recent}"
    print(f"gate_health OK — {len(recent)} recent fault(s) visible")
    sys.exit(0)
