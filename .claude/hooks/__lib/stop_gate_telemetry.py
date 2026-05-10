"""
Stop gate-level telemetry — lightweight structured logging.

EXPERIMENTAL: Provides visibility into which gates fire with what decisions.
wired: false (off by default)
review: TBD

Usage:
    STOP_TELEMETRY=1  # Enable telemetry to .state/stop_gate_telemetry.jsonl

Log format (one JSON object per line):
    {
        "ts": "<ISO8601>",
        "gate": "<gate_name>",
        "class": "policy|quality",
        "profile": "<critic_profile or context>",
        "decision": "block|warn|allow",
        "session_id": "...",
        "terminal_id": "..."
    }

Failures are silent — logging errors never propagate.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TELEMETRY_ENABLED = os.environ.get("STOP_TELEMETRY", "0") not in {"0", "false", "no", "off"}
_STATE_DIR = Path(__file__).resolve().parent.parent / ".state"
_LOG_FILE = _STATE_DIR / "stop_gate_telemetry.jsonl"


def log_gate_event(
    gate_name: str,
    classification: str,
    profile: str | None,
    decision: str,
    session_id: str | None = None,
    terminal_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Log a single gate invocation. Never raises."""
    if not _TELEMETRY_ENABLED:
        return

    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "gate": gate_name,
        "class": classification,
        "profile": profile,
        "decision": decision,
    }
    if session_id:
        record["session_id"] = session_id
    if terminal_id:
        record["terminal_id"] = terminal_id
    if extra:
        record["extra"] = extra

    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass  # Fail silent — telemetry errors must not disrupt Stop


def clear_test_telemetry() -> None:
    """Remove telemetry log. For use in tests only."""
    try:
        if _LOG_FILE.exists():
            _LOG_FILE.unlink()
    except Exception:
        pass


def read_telemetry() -> list[dict[str, Any]]:
    """Read all telemetry records. For use in tests only."""
    try:
        if not _LOG_FILE.exists():
            return []
        return [json.loads(line) for line in _LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return []