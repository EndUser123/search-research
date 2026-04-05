"""Stop hook for question marking — supports one-question-max enforcement.

Detects when LLM response contains a question mark and increments a counter
in a marker file. Consumed by PreToolUse_skill_question_gate.py.

From ADR-20260329-llm-consultation-pattern-fix.md — CHANGE-003
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add __lib to path for FileLock import
_HOOKS_LIB = os.path.join(os.path.dirname(__file__), "__lib")
if _HOOKS_LIB not in sys.path:
    sys.path.insert(0, _HOOKS_LIB)

from __lib.file_lock import FileLock

# State directory
_STATE_DIR = Path.home() / ".claude" / "hooks" / "state"

# Question marker file pattern
_QUESTION_MARKER = "question_asked_{session_id}.json"

# Skill invocation marker (set by PreToolUse_skill_question_gate.py)
_SKILL_MARKER = "skill_invoked_{session_id}.json"


def _get_marker_path(session_id: str, prefix: str) -> Path:
    if not session_id:
        return Path("/dev/null")
    return _STATE_DIR / prefix.format(session_id=session_id)


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    lock = FileLock(lock_path, timeout=5.0)
    with lock:
        path.write_text(json.dumps(data), encoding="utf-8")


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Detect question marks in LLM response and update question counter.

    Design:
    - Only tracks questions when a skill has been invoked (PreToolUse set the skill marker)
    - PreToolUse_skill_question_gate.py consumes and resets this counter on tool execution
    - This hook runs in the Stop phase where we have access to response_text

    Args:
        data: Hook data containing response_text, session_id, etc.

    Returns:
        Dictionary with 'allow' (bool) and optional 'reason' (str)
    """
    if os.environ.get("STOP_QUESTION_MARKER_ENABLED", "true").lower() != "true":
        return {"allow": True, "reason": "Stop question marker disabled"}

    session_id = str(data.get("session_id", ""))
    response_text = str(data.get("response_text", ""))

    if not session_id:
        return {"allow": True, "reason": "No session_id"}

    skill_marker = _get_marker_path(session_id, _SKILL_MARKER)
    question_marker = _get_marker_path(session_id, _QUESTION_MARKER)

    # Only track questions if a skill was actually invoked
    if not skill_marker.exists():
        return {"allow": True, "reason": "No skill invoked, not tracking questions"}

    if not response_text:
        return {"allow": True, "reason": "No response text"}

    # Count question marks in the response
    question_count = response_text.count("?")

    if question_count == 0:
        return {"allow": True, "reason": "No question detected"}

    # Load existing state
    state = _load_json(question_marker)
    current_count = state.get("count", 0)
    new_count = current_count + question_count

    # Save updated count
    _save_json(question_marker, {
        "count": new_count,
        "questions_seen": state.get("questions_seen", 0) + 1,
    })

    return {
        "allow": True,
        "reason": f"Question marker updated: count={new_count}",
    }


if __name__ == "__main__":
    try:
        raw = sys.stdin.read().strip()
        input_data = json.loads(raw) if raw else {}
    except Exception:
        input_data = {}

    result = run(input_data)
    print(json.dumps(result))
