#!/usr/bin/env python3
"""
Stop_task_completion_gate.py - Task Self-Documentation Completion Gate
====================================================================

Blocks TaskUpdate to status=completed when the task lacks self-documentation.

Self-documentation Schema:
- Subject: 10+ characters
- Description: 50+ characters with at least one indicator from each category:
  - Problem: fix, bug, issue, error, crash, broken, fails
  - Situation: when, during, while, after, in, on
  - Symptom: shows, returns, throws, produces, outputs, error, exception

LIFECYCLE: Stop (blocking gate -- exits with code 2 to block)
ACTIVATION: Fires on TaskUpdate to status=completed
STATE: Reads task state file but maintains no durable state
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
HOOKS_LIB_DIR = HOOKS_DIR / "__lib"

for path in (str(HOOKS_DIR), str(HOOKS_LIB_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from task_self_doc_validator import self_documentation_check
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(HOOKS_LIB_DIR))
    from task_self_doc_validator import self_documentation_check

# State directory for task tracker
STATE_DIR = Path(
    os.environ.get(
        "TASK_TRACKER_STATE_DIR", str(HOOKS_DIR.parent / ".claude" / "state" / "task_tracker")
    )
)

def _get_task_state_path(terminal_id: str | None = None) -> Path | None:
    """Get the path to the task state file for a terminal.

    Args:
        terminal_id: Terminal ID. If None, attempts to detect from environment.

    Returns:
        Path to the task state file, or None if not found.
    """
    # Re-compute STATE_DIR each call to respect environment variable changes
    state_dir = Path(
        os.environ.get(
            "TASK_TRACKER_STATE_DIR",
            str(HOOKS_DIR.parent / ".claude" / "state" / "task_tracker"),
        )
    )

    if terminal_id is None:
        terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")

    if not terminal_id:
        # Try to find any task state file
        if state_dir.exists():
            candidates = list(state_dir.glob("*_tasks.json"))
            if candidates:
                return candidates[0]
        return None

    safe_id = terminal_id.replace(":", "_").replace("/", "_")
    state_file = state_dir / f"{safe_id}_tasks.json"

    if state_file.exists():
        return state_file

    # Try without normalization
    state_file = state_dir / f"{terminal_id}_tasks.json"
    if state_file.exists():
        return state_file

    return None

def _load_task_data(task_id: str | int) -> dict[str, Any] | None:
    """Load task data from the task state file.

    Args:
        task_id: The task ID to look up.

    Returns:
        Task data dict or None if not found.
    """
    state_path = _get_task_state_path()
    if not state_path or not state_path.exists():
        return None

    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)

        tasks = state.get("tasks", {})
        task_id_str = str(task_id)

        # Handle both string and int task IDs
        if task_id_str in tasks:
            return tasks[task_id_str]

        # Try as integer key
        try:
            task_id_int = int(task_id)
            if str(task_id_int) in tasks:
                return tasks[str(task_id_int)]
            if task_id_int in tasks:
                return tasks[task_id_int]
        except (ValueError, TypeError):
            pass

        return None
    except (json.JSONDecodeError, OSError):
        return None

def _is_task_completion(tool_events: list[dict]) -> tuple[bool, dict | None, str | None]:
    """Check if any tool event is a TaskUpdate to completed status.

    Args:
        tool_events: List of tool events from the Stop hook input.

    Returns:
        Tuple of (is_completion, tool_input, task_id)
    """
    for event in tool_events:
        name = event.get("name", "") or event.get("tool_name", "")
        if name != "TaskUpdate":
            continue

        input_data = event.get("input", {}) or {}
        status = input_data.get("status", "")

        if status == "completed":
            task_id = input_data.get("taskId") or input_data.get("task_id")
            return True, input_data, task_id

    return False, None, None

def check(data: dict) -> dict | None:
    """Core guard logic. Returns block dict or None (allow).

    Args:
        data: Stop hook input data.

    Returns:
        Block dict if task completion should be blocked, None to allow.
    """
    # Check if self-documentation enforcement is enabled
    if os.environ.get("TASK_SELF_DOC_ENABLED", "true").lower() in ("0", "false", "no", "off"):
        return None

    # Check if advisory-only mode (don't block at completion)
    advisory_only = os.environ.get("TASK_SELF_DOC_ADVISORY_ONLY", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if advisory_only:
        return None

    # Get tool events
    tool_events = data.get("tool_events", [])
    if not tool_events:
        return None

    # Check if this is a task completion
    is_completion, tool_input, task_id = _is_task_completion(tool_events)

    if not is_completion or not task_id:
        return None

    # Load task data
    task_data = _load_task_data(task_id)

    if task_data is None:
        # Task not found in state - allow (might have been created in a different session)
        return None

    # Get subject and description
    subject = task_data.get("subject", "") or ""
    description = task_data.get("description", "") or ""

    # Validate self-documentation
    result = self_documentation_check(subject, description)

    if result.is_valid:
        return None

    # Build block message
    missing = ", ".join(result.missing_categories) if result.missing_categories else "unknown"

    reason_lines = [
        "TASK SELF-DOCUMENTATION REQUIRED",
        "",
        f"Task #{task_id} cannot be marked as completed because it lacks self-documentation.",
        "",
        f"Subject ({result.subject_length}/10 chars): {subject or '(empty)'[:50]}",
        f"Description ({result.desc_length}/50 chars): {description or '(empty)'[:50]}",
        "",
        "Missing categories:",
        f"  {missing}",
        "",
        "A self-documenting task explains:",
        "  • Problem: what issue is this fixing? (e.g., 'fix', 'bug', 'error')",
        "  • Situation: when/where does it occur? (e.g., 'when', 'during', 'while')",
        "  • Symptom: what observable behavior? (e.g., 'shows', 'returns', 'throws')",
        "",
        "Add a description that includes at least one indicator from each category.",
    ]

    # Add warnings if any
    if result.warnings:
        reason_lines.append("")
        reason_lines.append("Warnings:")
        for warning in result.warnings:
            reason_lines.append(f"  • {warning}")

    return {
        "decision": "block",
        "reason": "\n".join(reason_lines),
        "blocking_hook": "Stop_task_completion_gate",
    }

def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router.

    Args:
        data: Stop hook input data.

    Returns:
        Block dict if blocking, None to allow.
    """
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_task_completion_gate"),
        }
    return result

# --- Main (subprocess mode) ---

def main() -> None:
    """Entry point for subprocess mode."""
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = check(data)
    if result:
        print(json.dumps(result))
        if result.get("decision") == "block":
            sys.exit(2)
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()