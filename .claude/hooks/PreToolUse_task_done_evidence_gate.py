#!/usr/bin/env python3
"""
PreToolUse task done-evidence ADVISORY.

Fires on TaskUpdate(status="completed"). Checks whether a durable completion
receipt exists for the task and, if not, prints a non-blocking advisory to stderr
nudging the agent to record evidence via `/task done <id>`.

DESIGN — why advisory (non-blocking), not blocking:
  The native TaskUpdate tool schema does NOT support custom evidence fields.
  An earlier version of this gate checked `commit_hash` / `evidence_file` /
  `skip_evidence` — fields the native tool never accepted, so the gate could
  only ever block every completion (and it was dead-dispatched under the
  non-existent tool name "Task" anyway). Completion receipts are written by
  `/task done` ALONGSIDE the TaskUpdate call, so blocking completion here
  creates a chicken-and-egg. Deletion safety is enforced deterministically by
  the receipt-based verifier (`/task clean` only deletes VERIFIED-receipt
  tasks); this gate never authorizes or blocks anything.

Receipts live in: {CSF_STATE_DIR or P:/.claude/state}/task_receipts/{task_id}.json
  (configurable via TASK_RECEIPT_DIR env var, kept in sync with task_receipt.py)

Exit codes:
  0 = allow (always — this gate never blocks)

Env vars:
  TASK_DONE_EVIDENCE_ENABLED=true (default: true)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_ENABLED = os.environ.get("TASK_DONE_EVIDENCE_ENABLED", "true").lower() == "true"
_STATE_ROOT = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
_RECEIPT_DIR = Path(
    os.environ.get(
        "TASK_RECEIPT_DIR",
        str(_STATE_ROOT / "task_receipts"),
    )
)


def _safe_task_id(task_id: str) -> str:
    """Sanitize a task id for use as a filename (defense against path traversal)."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(task_id)) or "unknown"


def receipt_path_for(task_id: str) -> Path:
    """Terminal-scoped receipt path, matching task_receipt.py (SR-1 fix)."""
    tid = os.environ.get("CLAUDE_TERMINAL_ID") or os.environ.get("WT_SESSION", "unknown")
    safe_tid = _safe_task_id(tid)
    return _RECEIPT_DIR / safe_tid / f"{_safe_task_id(task_id)}.json"


def has_receipt(task_id: str) -> bool:
    p = receipt_path_for(task_id)
    try:
        return p.is_file()
    except OSError:
        return False


def check(tool_input: dict) -> tuple[bool, str]:
    """Return (has_receipt, task_id). Only meaningful when status == "completed"."""
    status = str(tool_input.get("status", "")).lower()
    if status != "completed":
        return True, ""

    task_id = str(tool_input.get("taskId") or tool_input.get("task_id") or "?")
    if not _ENABLED:
        return True, task_id
    return has_receipt(task_id), task_id


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return  # malformed — fail open, no advisory
    if not isinstance(data, dict):
        return
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return

    has, task_id = check(tool_input)
    # Advisory only: never exit non-zero. Print a nudge only when completing
    # without a receipt.
    if not has and task_id:
        print(
            f"[task-done-evidence] No completion receipt for task #{task_id}. "
            f"Run `/task done {task_id}` to record durable evidence; "
            f"this task will NOT be eligible for `/task clean` without a VERIFIED receipt.",
            file=sys.stderr,
        )
    # Always allow.


if __name__ == "__main__":
    main()
