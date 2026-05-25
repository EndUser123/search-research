#!/usr/bin/env python3
"""
PreToolUse Hook: File Existence Guard

Prevents redundant documentation writes by checking if files already exist
with identical content. Blocks no-op writes and requests justification for
overwrites.

Performance target: <100ms for most operations
"""
from __future__ import annotations



# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Import shared utilities for session ID resolution
from shared_utils import resolve_session_id

# Constants
MAX_SAMPLE_SIZE = 4096  # 4KB sample for large files
LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB
HOOK_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOK_DIR / "state"

# Tools that write files
WRITE_TOOLS = {"Write", "Edit"}


def parse_stdin() -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Parse stdin JSON to extract full data, tool_name and tool_input."""
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        return data, tool_name, tool_input
    except json.JSONDecodeError:
        # If we can't parse, allow the operation
        return {}, "", {}
    except Exception:
        # Any other error, allow the operation
        return {}, "", {}


def extract_file_path(tool_input: dict[str, Any]) -> str | None:
    """Extract file_path from tool_input."""
    if not isinstance(tool_input, dict):
        return None

    # Common parameter names for file paths
    for key in ["file_path", "path", "filepath"]:
        if key in tool_input:
            path = tool_input[key]
            if isinstance(path, str):
                return path

    return None


def file_exists(file_path: str) -> bool:
    """Check if file exists using pathlib for Windows compatibility."""
    try:
        return Path(file_path).exists()
    except (OSError, ValueError):
        # Path too long or invalid characters on Windows
        return False


def read_file_content(file_path: str) -> str | None:
    """Read file content with Windows compatibility and performance optimization."""
    try:
        path = Path(file_path)

        # Check file size for performance optimization
        file_size = path.stat().st_size

        # For large files, only read sample
        if file_size > LARGE_FILE_THRESHOLD:
            with open(path, encoding="utf-8", errors="ignore") as f:
                return f.read(MAX_SAMPLE_SIZE)

        # Small files, read completely
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()

    except (OSError, UnicodeDecodeError):
        # Can't read file - allow operation
        return None


def extract_new_content(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    """Extract new content from tool_input."""
    if tool_name == "Write":
        return tool_input.get("content")
    elif tool_name == "Edit":
        # For Edit, we can't easily predict final result
        # Just allow it - the guard is mainly for Write
        return None
    return None


def content_matches(existing: str, new: str) -> bool:
    """Compare content efficiently."""
    if not existing or not new:
        return False

    # Quick length check
    if len(existing) != len(new):
        # If lengths differ, still check if it's a sample vs full content
        # by comparing the sample portion
        if len(existing) < len(new):
            # existing is sample, check if it matches start of new
            return new[: len(existing)] == existing
        else:
            # new is sample, check if it matches start of existing
            return existing[: len(new)] == new

    # Full comparison for reasonable sizes
    if len(existing) < MAX_SAMPLE_SIZE * 2:
        return existing == new

    # For large content, compare hashes
    return hashlib.md5(existing.encode()).hexdigest() == hashlib.md5(new.encode()).hexdigest()


def write_state_file(session_id: str, file_path: str, decision: str, reason: str) -> None:
    """Write state file for coordination with other hooks."""
    try:
        STATE_DIR.mkdir(exist_ok=True)

        state_file = STATE_DIR / f"file_existence_decision_{session_id}.json"

        state_data = {
            "session_id": session_id,
            "file_path": file_path,
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

    except (OSError, json.JSONEncodeError):
        # State file failure shouldn't block the hook
        pass


def get_session_id(hook_data: dict[str, Any]) -> str:
    """Extract session ID from hook data using shared utils."""
    return resolve_session_id(hook_data)


def main() -> None:
    """Main hook logic."""
    # Parse input
    hook_data, tool_name, tool_input = parse_stdin()

    # Guard: Only check write operations
    if tool_name not in WRITE_TOOLS:
        # Allow non-write operations
        print(json.dumps({}))
        return

    # Extract file path
    file_path = extract_file_path(tool_input)
    if not file_path:
        # Can't determine file path, allow
        print(json.dumps({}))
        return

    # Get session ID from hook data
    session_id = get_session_id(hook_data)

    # Check if file exists
    if not file_exists(file_path):
        # New file, allow
        write_state_file(
            session_id, file_path, "allow_new", "File does not exist, allowing creation"
        )
        print(json.dumps({}))
        return

    # File exists - read existing content
    existing_content = read_file_content(file_path)
    if existing_content is None:
        # Couldn't read file, allow operation
        print(json.dumps({}))
        return

    # Extract new content
    new_content = extract_new_content(tool_name, tool_input)
    if new_content is None:
        # Can't determine new content (e.g., Edit tool), allow
        print(json.dumps({}))
        return

    # Compare content
    if content_matches(existing_content, new_content):
        # Identical content - DENY
        reason = "File already exists with identical content. Treat as 'docs already exist and are complete'."

        write_state_file(session_id, file_path, "deny", reason)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(_normalize_stdout(output)))
        return

    # Different content - ALLOW with justification request
    reason = "File exists with different content. State why previous documentation is insufficient and summarize what is changing."

    write_state_file(session_id, file_path, "allow_with_justification", reason)

    # For different content, we allow but show an advisory
    # This is done via the ask decision to show message to user
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(_normalize_stdout(output)))


if __name__ == "__main__":
    main()
