#!/usr/bin/env python3
"""PostCompact hook — restore session state after compaction."""

from __future__ import annotations

import json
import sys
from typing import Any

from utils.reminder_state import (
    artifacts_dir,
    hash_reminder,
    is_state_fresh,
    read_compaction_state,
    write_compaction_state,
)


def _build_context(state: dict[str, Any]) -> str:
    """Build RESUME context string from state."""
    lines: list[str] = []

    goal = state.get("goal", "unknown task")
    lines.append(f"RESUME: {goal}")

    # Pending questions (S1.5)
    questions = state.get("openquestions", [])
    if questions:
        lines.append("PENDING QUESTIONS:")
        for q in questions[:3]:
            q_text = q.get("question", "")
            ctx = q.get("context", "")
            if ctx:
                lines.append(f"- {q_text}")
                lines.append(f"  Context: {ctx}")
            else:
                lines.append(f"- {q_text}")

    last_action = state.get("last_action", "")
    if last_action:
        lines.append(f"Last action: {last_action}")

    pending = state.get("pending_work", [])
    if pending:
        lines.append("Pending work:")
        for item in pending[:5]:
            lines.append(f"  - {item}")

    active = state.get("active_files", [])
    if active:
        files_str = ", ".join(active[:5])
        lines.append(f"Active files: {files_str}")

    corrections = state.get("recent_corrections", [])
    if corrections:
        lines.append(f"Recent correction: {corrections[0]}")
        if len(corrections) > 1:
            lines.append(f"Also: {corrections[1]}")

    # Cap at 25 lines
    return "\n".join(lines[:25])


def restore_state(data: dict) -> dict:
    """Read compaction state and inject recovery context."""
    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")
    transcript_path = data.get("transcript_path")

    state = read_compaction_state(terminal_id)
    if not state:
        return {"status": "success"}  # No state = SessionStart will handle

    # Freshness check: < 10 minutes
    ts = state.get("timestamp")
    if not is_state_fresh(ts, max_age_minutes=10):
        return {"status": "success"}  # Stale = skip

    # Deduplication: don't re-inject already-shown reminders
    existing_hashes = set(state.get("reminder_hashes", []))
    corrections = state.get("recent_corrections", [])
    new_hashes: list[str] = []

    filtered_corrections: list[str] = []
    for corr in corrections:
        h = hash_reminder(corr)
        if h not in existing_hashes:
            filtered_corrections.append(corr)
            new_hashes.append(h)

    # Also deduplicate against last 3-5 turns from transcript
    # (simplified: trust the hash tracking)
    state["reminder_hashes"] = list(existing_hashes | set(new_hashes))

    # Build context with deduplicated corrections
    state["recent_corrections"] = filtered_corrections[:2]
    context = _build_context(state)

    # Update state with new hashes
    write_compaction_state(terminal_id, state)

    return {"status": "success", "additionalContext": context}


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    try:
        data = json.loads(stdin_text)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Invalid JSON"}))
        sys.exit(1)

    result = restore_state(data)
    print(json.dumps(result))
