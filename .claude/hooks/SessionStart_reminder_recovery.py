#!/usr/bin/env python3
"""SessionStart_sub_reminder_recovery — fallback recovery when resuming interrupted work."""

from __future__ import annotations

import json
import sys
from typing import Any

from utils.reminder_state import (
    is_state_fresh,
    read_compaction_state,
    read_memory_md,
)


def _build_fallback_context(state: dict[str, Any] | None) -> str:
    """Build session resume context from state or fallback."""
    lines: list[str] = []

    if state:
        goal = state.get("goal", "unknown task")
        lines.append(f"Session resume: {goal}")

        pending = state.get("pending_work", [])
        if pending:
            lines.append(f"Unresolved: {pending[0]}")

    memory_corrections = read_memory_md()
    if memory_corrections:
        lines.append("Top corrections:")
        for corr in memory_corrections[:3]:
            lines.append(f"  - {corr}")

    return "\n".join(lines) if lines else ""


def resume_session(data: dict) -> dict:
    """Provide fallback recovery context on session start."""
    terminal_id = data.get("terminal_id", "")
    is_resume = data.get("is_resume", False)

    state = read_compaction_state(terminal_id)
    fallback_ctx = ""

    if state:
        ts = state.get("timestamp")
        if is_state_fresh(ts, max_age_minutes=24 * 60):
            fallback_ctx = _build_fallback_context(state)
        elif not is_resume:
            fallback_ctx = _build_fallback_context(state)
        else:
            fallback_ctx = ""
    else:
        fallback_ctx = _build_fallback_context(None)

    if not fallback_ctx:
        return {"status": "success"}

    return {"status": "success", "additionalContext": fallback_ctx}


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    try:
        data = json.loads(stdin_text)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Invalid JSON"}))
        sys.exit(1)

    result = resume_session(data)
    print(json.dumps(result))
