"""Helpers for turn-scoped evidence loading with test-mode spool fallback.

This centralizes the two-mode behavior used by some Stop guards:
- Real Claude sessions: use shared evidence-scope `turn_strict`
- Test-mode/non-UUID sessions: read spool files directly
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from evidence_scope import SCOPE_TURN_STRICT, load_scoped_tool_events
from evidence_store import _load_turn_start_event_id

HOOKS_DIR = Path(__file__).resolve().parent
TURN_MARKER_DIR = HOOKS_DIR / "state" / "turn_markers"
EVIDENCE_SPOOL_DIR = HOOKS_DIR / "session_data" / "evidence_spool"
UUID_RE = re.compile(r"^[a-f0-9\-]{36}$", re.IGNORECASE)


def is_uuid_session_id(session_id: str) -> bool:
    return bool(UUID_RE.match((session_id or "").strip()))


def safe_scope_key(session_id: str, terminal_id: str) -> str:
    def _safe(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", (value or "unknown").strip())

    return f"{_safe(session_id)}__{_safe(terminal_id)}"


def read_turn_marker(session_id: str, terminal_id: str) -> int | None:
    """Return turn_start_event_id from evidence_store, with marker fallback."""
    value = _load_turn_start_event_id(session_id, terminal_id)
    if value is not None:
        return value

    path = TURN_MARKER_DIR / f"turn_start_{safe_scope_key(session_id, terminal_id)}.json"
    try:
        data = json.loads(path.read_text())
        value = data.get("turn_start_event_id")
        if value is not None:
            return int(value)
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def load_spool_events_for_turn(session_id: str, terminal_id: str) -> list[dict[str, Any]] | None:
    """Load turn-scoped tool events from spool files directly for test sessions."""
    try:
        spool_files = sorted(EVIDENCE_SPOOL_DIR.glob(f"{session_id}_*.json"))
    except (FileNotFoundError, OSError):
        return None

    if not spool_files:
        return None

    min_id = read_turn_marker(session_id, terminal_id)
    events: list[dict[str, Any]] = []
    for spool_file in spool_files:
        try:
            event_data = json.loads(spool_file.read_text(encoding="utf-8"))
            event_id = int(event_data.get("id", 0))
            if min_id is not None and event_id <= min_id:
                continue
            events.append(event_data)
        except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return events


def load_turn_scoped_events(
    *, session_id: str, terminal_id: str, limit: int
) -> list[dict[str, Any]] | None:
    """Load turn-scoped evidence with spool fallback for non-UUID test sessions."""
    if not session_id:
        return None

    if not is_uuid_session_id(session_id):
        return load_spool_events_for_turn(session_id, terminal_id)

    try:
        return load_scoped_tool_events(
            session_id=session_id,
            terminal_id=terminal_id,
            scope=SCOPE_TURN_STRICT,
            limit=limit,
        )
    except Exception:
        return None
