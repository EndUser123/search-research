#!/usr/bin/env python3
"""
PreToolUse Hook: Session ID Capture for Git Integration

Captures session_id from hook stdin JSON and writes to a tempfile inside .git/
so the prepare-commit-msg git hook can read it.

Run: PreToolUse (before any tool execution)
Timeout: 2 seconds
Exit Codes:
  - 0: Always allow (capture is non-blocking)

Author: Claude Code
Date: 2026-03-26
Related: temporal-honking-bubble.md (AIR Auditor plan)
"""

import json
import os
import sys
from pathlib import Path

# Add hooks lib to path
hooks_dir = Path(__file__).resolve().parent
hooks_lib = hooks_dir / "__lib"
sys.path.insert(0, str(hooks_lib))

from pre_tool_use_logic import resolve_session_id

# Tempfile location: inside .git/ so git hook can reach it
GIT_DIR = Path(os.environ.get("GIT_DIR", ".git")).resolve()
SESSION_FILE_PREFIX = ".claude_session_"


def _write_session_file(session_id: str) -> bool:
    """Write session_id to tempfile inside .git/ directory.

    Returns True if written successfully, False otherwise.
    """
    if not session_id or not session_id.strip():
        return False

    try:
        session_file = GIT_DIR / f"{SESSION_FILE_PREFIX}{session_id}.tmp"
        session_file.write_text(session_id.strip(), encoding="utf-8")
        return True
    except OSError:
        return False


def _main() -> None:
    """Read stdin JSON, extract session_id, write to tempfile."""
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)  # Fail open — never block tool execution

    session_id = resolve_session_id(data)
    if session_id:
        _write_session_file(session_id)

    sys.exit(0)


if __name__ == "__main__":
    _main()
