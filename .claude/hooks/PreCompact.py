#!/usr/bin/env python3
"""PreCompact hook — capture unresolved state before compaction."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from utils.reminder_state import (
    artifacts_dir,
    extract_recent_messages,
    read_memory_md,
    write_compaction_state,
)
from utils.question_extractor import extract_pending_questions
from utils.correction_ranker import rank_corrections


def capture_state(data: dict) -> dict:
    """Extract session state for compaction recovery."""
    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")
    transcript_path = data.get("transcript_path")
    ctx = data.get("context", {})

    recent_msgs = extract_recent_messages(transcript_path, n=5)
    last_user = ctx.get("last_user_message", "")
    recent_tools = ctx.get("recent_tool_calls", [])

    # Derive goal from last user message
    goal = ""
    if last_user:
        goal = last_user[:120].strip()
    elif recent_msgs:
        goal = recent_msgs[-1][:120].strip()

    # Last meaningful action from recent tool calls
    last_action = ""
    active_files: list[str] = []
    pending_work: list[str] = []

    if recent_tools:
        for tool_call in reversed(recent_tools):
            if isinstance(tool_call, dict) and tool_call.get("result"):
                tool_name = tool_call.get("tool", "")
                tool_input = tool_call.get("input", {})
                result = str(tool_call["result"])[:200]
                last_action = f"{tool_name}: {result}"
                # Extract file paths from tool input
                fp = tool_input.get("file_path", "")
                if fp:
                    active_files.append(str(fp))
                break

    # Recent corrections from MEMORY.md — ranked by relevance
    memory_corrections = read_memory_md()
    recent_corrections = rank_corrections(
        memory_corrections,
        goal=goal,
        active_files=active_files,
        last_action=last_action,
        pending_work=pending_work,
        top_n=3,
    )

    # Extract pending questions from transcript
    openquestions = extract_pending_questions(transcript_path, max_questions=3)

    # Load existing state to preserve reminder hashes
    from utils.reminder_state import read_compaction_state
    existing = read_compaction_state(terminal_id) or {}
    existing_hashes = existing.get("reminder_hashes", [])

    state = {
        "session_id": session_id,
        "goal": goal,
        "last_action": last_action,
        "pending_work": pending_work,
        "active_files": list(dict.fromkeys(active_files))[:10],
        "recent_corrections": recent_corrections,
        "reminder_hashes": existing_hashes,
        "openquestions": openquestions,
    }
    write_compaction_state(terminal_id, state)
    return {"status": "success", "message": "Captured state before compaction"}


if __name__ == "__main__":
    stdin_text = sys.stdin.read()
    try:
        data = json.loads(stdin_text)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Invalid JSON"}))
        sys.exit(1)

    result = capture_state(data)
    print(json.dumps(result))
