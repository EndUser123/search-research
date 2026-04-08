#!/usr/bin/env python3
"""
Stop Hook: Git-Diff Re-grounding

Injects a warning when files touched during investigation have changed from git HEAD.
This prevents reasoning on stale assumptions after the codebase changes underneath.

Addresses: "does not always re-ground after the codebase changes underneath it"
GLM/MiniMax failure mode #3.

Configuration:
- GIT_DIFF_REGROUND_ENABLED (default: true)
- GIT_DIFF_REGROUND_MIN_FILES (default: 3) — minimum touched files to check
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

try:
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    SCOPE_SESSION_FRESH = ""
    load_scoped_tool_events = None  # type: ignore

GIT_DIFF_REGROUND_ENABLED = os.environ.get("GIT_DIFF_REGROUND_ENABLED", "true").lower() == "true"
GIT_DIFF_REGROUND_MIN_FILES = int(os.environ.get("GIT_DIFF_REGROUND_MIN_FILES", "3"))


def load_tool_events(*, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Compatibility wrapper for recent session evidence."""
    if load_scoped_tool_events is None:
        raise ImportError("evidence_scope unavailable")
    return load_scoped_tool_events(
        session_id=session_id,
        scope=SCOPE_SESSION_FRESH,
        limit=limit,
    )


def _get_git_diff_names() -> set[str]:
    """Get files that differ from HEAD in current working tree."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=HOOKS_DIR.parent,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except Exception:
        return set()


def _get_recent_file_touches(session_id: str, limit: int = 50) -> list[str]:
    """Get file paths from recent Read/Edit/Write tool events."""
    try:
        events = load_tool_events(session_id=session_id, limit=limit)
    except Exception:
        return []

    files = set()
    for event in events:
        tool_name = event.get("name", "")
        tool_input = event.get("input", {}) or {}

        if tool_name in ("Read", "Edit", "Write"):
            path = tool_input.get("file_path") or tool_input.get("path", "")
            if path:
                # Normalize to forward slashes for comparison
                normalized = str(Path(path).as_posix())
                files.add(normalized)

        elif tool_name == "Bash":
            command = event.get("command", "") or ""
            # Extract file paths from common commands
            # e.g., "python test.py" -> extract "test.py"
            # e.g., "pytest tests/" -> extract "tests/"
            if command:
                parts = command.split()
                for part in parts[1:]:  # Skip command name
                    if part and not part.startswith("-") and not part.startswith("$"):
                        if "." in part or "/" in part or "\\" in part:
                            normalized = str(Path(part).as_posix())
                            files.add(normalized)

    return list(files)


def check_git_diff_reground(data: dict) -> dict | None:
    """Check if investigation files have changed from git HEAD.

    Returns:
        dict with systemMessage if re-grounding needed, None otherwise
    """
    if not GIT_DIFF_REGROUND_ENABLED:
        return None

    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or os.environ.get("CLAUDE_SESSION_ID", "")
    )
    if not session_id:
        return None

    # Get files touched during investigation
    touched = _get_recent_file_touches(session_id, limit=50)
    if len(touched) < GIT_DIFF_REGROUND_MIN_FILES:
        return None  # Not enough files to warrant check

    # Get files that differ from HEAD
    changed_files = _get_git_diff_names()
    if not changed_files:
        return None  # No changes

    # Find intersection: files we touched that have changed
    touched_set = {str(Path(f).as_posix()) for f in touched}
    intersection = touched_set & changed_files

    if not intersection:
        return None  # Our touched files haven't changed

    # Files have changed — inject warning
    changed_list = sorted(intersection)[:10]  # Limit to 10 for readability
    changed_str = ", ".join(f"`{f}`" for f in changed_list)
    if len(intersection) > 10:
        changed_str += f" ... and {len(intersection) - 10} more"

    message = (
        f"**Git-diff re-grounding**: The following files you investigated have changed since your last read: {changed_str}.\n"
        "Your current hypothesis may be stale. Verify the change doesn't invalidate your analysis."
    )

    return {"systemMessage": message}


def main() -> int:
    """Main hook entry point."""
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    result = check_git_diff_reground(data)
    if result:
        print(json.dumps(result))
    else:
        print("{}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
