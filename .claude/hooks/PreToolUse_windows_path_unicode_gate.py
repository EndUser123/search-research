#!/usr/bin/env python3
r"""PreToolUse hook: detect Unicode escape errors in Windows paths within -c commands.

Detects: python -c "..." with C:\Users-style paths in non-raw strings.
Trigger: backslash-U followed by 8 hex digits (Python unicode escape) inside a -c string.

Fix: Use r"..." (raw string) or forward slashes C:/Users/...
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Add shared utils to path
_HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(_HOOKS_DIR / "__lib"))

from shared_utils import log_hook_event

_HOOK_NAME = "PreToolUse_windows_path_unicode_gate"
_ENABLED = os.environ.get("WINDOWS_PATH_UNICODE_GATE_ENABLED", "true").lower() == "true"

# Python unicode escape: \U followed by exactly 8 hex digits (valid)
# This catches the problematic case where \U is NOT followed by 8 hex digits
# (e.g., \Users, \Ubuntu) - Python treats \U as start of unicode codepoint
_UNICODE_ESCAPE = re.compile(r"\\U(?![0-9A-Fa-f]{8})")
# Windows drive letter + backslash
_WINDOWS_DRIVE = re.compile(r"[A-Za-z]:\\")
# python -c "..." or python -c '...'
_PYTHON_C_CMD = re.compile(r"python\s+-c\s+", re.IGNORECASE)


def _has_unicode_escape(problematic_part: str) -> bool:
    """Check if a string segment contains a Python unicode escape sequence."""
    return bool(_UNICODE_ESCAPE.search(problematic_part))


def _extract_c_string_body(command: str) -> list[str]:
    """Extract the body of -c string arguments from a command.

    Returns list of string contents (stripped of surrounding quotes).
    Handles both single and double quoted strings.
    """
    results: list[str] = []

    # Find all -c occurrences
    for match in re.finditer(r"-c\s+", command, re.IGNORECASE):
        rest = command[match.end() :]
        if not rest:
            continue

        # Get first string-like argument
        first_char = rest[0]
        if first_char not in ('"', "'"):
            continue

        # Find matching closing quote (not escaped)
        body = rest[1:]
        for i, char in enumerate(body):
            if char == first_char and (i == 0 or body[i - 1] != "\\"):
                content = body[:i]
                results.append(content)
                break

    return results


def _is_windows_path_unicode_issue(command: str) -> tuple[bool, str]:
    """Detect Python -c command with Windows path causing Unicode escape error.

    Returns (is_problem, extracted_string_for_display).
    """
    if not _PYTHON_C_CMD.search(command):
        return False, ""

    string_bodies = _extract_c_string_body(command)
    for body in string_bodies:
        # Check for Windows drive path AND unicode escape in the same string
        if _WINDOWS_DRIVE.search(body) and _has_unicode_escape(body):
            return True, body[:100]  # Truncate for display

    return False, ""


def process(data: dict) -> dict | None:
    """PreToolUse hook entry point."""
    if not _ENABLED:
        return None

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return None

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return None

    # Fail-open: if detection raises exception, allow command with warning logged
    try:
        is_problem, snippet = _is_windows_path_unicode_issue(command)
    except Exception as e:
        log_hook_event(
            _HOOK_NAME,
            "detection_exception",
            {"command_length": len(command), "error": str(e)},
        )
        return None

    if not is_problem:
        return None

    log_hook_event(
        _HOOK_NAME,
        "windows_unicode_path",
        {"command_snippet": snippet},
    )

    return {
        "continue": False,
        "reason": f"""WINDOWS PATH UNICODE ESCAPE ERROR

Your command contains a Python -c string with a Windows path that will fail:
  {snippet[:80]}

Python interprets backslash-U as a Unicode escape (8 hex digits required).
C:\\Users becomes invalid because \\U starts a Unicode codepoint.

FIX -- choose one:
1. Use raw string:     python -c r"..." (keeps backslashes)
2. Use forward slashes: python -c "..." (Python accepts C:/Users on Windows)
3. Escape backslashes:  python -c "C:\\\\Users..."

Retry your command with one of the above fixes.""",
    }


if __name__ == "__main__":
    import json

    data = json.loads(input())
    result = process(data)
    if result:
        print(json.dumps(result), file=sys.stderr)
    sys.exit(0)
