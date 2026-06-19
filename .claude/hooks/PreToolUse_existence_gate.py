"""PreToolUse hook: Block Write/Edit to existing files unless Read occurred this session.

Purpose: Prevent accidental overwrites by enforcing discovery-before-implementation.
Tracks Read events per-session and blocks subsequent Write/Edit if file exists
but wasn't read.

Bypass: Add --allow-overwrite to your message to override.

State tracking: .claude/state/read_files_{session_id}.json
"""

import json
import sys
from pathlib import Path

# Session state directory
STATE_DIR = Path.home() / ".claude" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _get_state_file(session_id: str) -> Path:
    """Get session-scoped state file for tracking read files."""
    return STATE_DIR / f"read_files_{session_id}.json"


def _load_read_files(session_id: str) -> set[str]:
    """Load set of files read this session."""
    state_file = _get_state_file(session_id)
    if not state_file.exists():
        return set()
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("read_files", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def _record_read_file(session_id: str, file_path: str) -> None:
    """Record that a file was read this session."""
    state_file = _get_state_file(session_id)
    read_files = _load_read_files(session_id)
    read_files.add(file_path)
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"read_files": sorted(list(read_files))}, f, indent=2)
    except OSError:
        pass  # Fail open - if we can't record, just don't block


def run(data: dict) -> dict | None:
    """Hook entry point."""
    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return None

    # Extract session_id from data
    session_id = data.get("session_id", "")
    if not session_id:
        return None  # Can't track without session_id

    # Extract file path(s)
    tool_input = data.get("tool_input", {})

    # Handle different tools
    if tool_name == "MultiEdit":
        # MultiEdit has multiple file paths
        # The tool_input format varies, so we need to handle it
        file_paths = []
        if isinstance(tool_input, dict):
            # MultiEdit structure is complex, skip for now
            return None
    else:
        # Write and Edit have single file_path
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return None
        file_paths = [file_path]

    # Check for bypass flag in user message
    # data.get("message") is the full user prompt
    message = data.get("message", "")
    if "--allow-overwrite" in message:
        return None  # Bypassed

    blocked_files = []
    for file_path in file_paths:
        # Check if file exists
        if Path(file_path).exists():
            # Check if read this session
            read_files = _load_read_files(session_id)
            if file_path not in read_files:
                blocked_files.append(file_path)

    if blocked_files:
        print(
            f"\n⛔ EXISTENCE CHECK REQUIRED\n\n",
            file=sys.stderr
        )
        if len(blocked_files) == 1:
            print(
                f"File exists but hasn't been read this session:\n"
                f"  {blocked_files[0]}\n\n"
                f"Before modifying, you MUST:\n"
                f"1. Read the file to understand current state\n"
                f"2. Then proceed with Write/Edit\n\n"
                f"Bypass: Add --allow-overwrite to your message",
                file=sys.stderr,
            )
        else:
            print(
                f"Files exist but haven't been read this session:\n",
                file=sys.stderr,
            )
            for fp in blocked_files:
                print(f"  - {fp}\n", file=sys.stderr)
            print(
                f"\nBefore modifying, you MUST:\n"
                f"1. Read each file to understand current state\n"
                f"2. Then proceed with Write/Edit\n\n"
                f"Bypass: Add --allow-overwrite to your message",
                file=sys.stderr,
            )
        sys.exit(2)

    return None


def run_read_tracker(data: dict) -> dict | None:
    """Track Read operations for session-scoped existence checking.

    This function is called after successful Read operations to record
    which files have been read, so subsequent Write/Edit operations
    know discovery occurred.

    To use this, add it to PostToolUse hooks.json or run it after Read tool calls.
    """
    tool_name = data.get("tool_name", "")
    if tool_name != "Read":
        return None

    session_id = data.get("session_id", "")
    if not session_id:
        return None

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    _record_read_file(session_id, file_path)
    return None