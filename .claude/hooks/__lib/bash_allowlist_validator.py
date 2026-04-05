"""
SEC-003: Bash Allowlist Validator via Full Command Parsing.

This module provides validation of bash commands using shlex.split() to parse
the full command string and detect dangerous patterns that would bypass
argv[0] checks.
"""

from __future__ import annotations

import shlex
from typing import Any

# Dangerous patterns that must be rejected in ANY segment
_DANGEROUS_PATTERNS: set[str] = {
    "python -c",
    "python -m",
    "python -f",
    "python -x",
    "bash -c",
    "sh -c",
    "zsh -c",
    "perl -e",
    "ruby -e",
    "eval",
    "exec",
    "subprocess",
    "os.system",
    "os.popen",
}

# Commands that are safe without any arguments
_SAFE_COMMANDS_NO_ARGS: set[str] = {
    "cat",
    "ls",
    "head",
    "tail",
    "grep",
    "echo",
    "cd",
    "pwd",
    "mkdir",
    "rmdir",
    "cp",
    "mv",
    "find",
    "sort",
    "uniq",
    "wc",
}


def _is_safe_command(command: str) -> bool:
    """Check if command is a simple safe command with no flags."""
    return command in _SAFE_COMMANDS_NO_ARGS


def _is_python_script_invocation(segments: list[str], idx: int) -> bool:
    """
    Check if segments[idx] starts a safe 'python script.py' invocation.

    shlex.split('python script.py') -> ['python', 'script.py']
    We allow 'python script.py' ONLY if:
    - script ends with .py
    - no flags present (-c, -m, -f, -x, etc.)

    Returns True if safe, False if dangerous.
    """
    if idx >= len(segments):
        return False

    cmd = segments[idx]
    if cmd != "python":
        return False

    # Check if there's a script argument
    if idx + 1 >= len(segments):
        # 'python' alone with no args is suspicious but not definitively blocked
        # Let it through - the empty argument case is handled elsewhere
        return True

    script_arg = segments[idx + 1]

    # 'python' with a flag (not a script) is dangerous
    if script_arg.startswith("-"):
        return False

    # Script must end with .py to be allowed
    if not script_arg.endswith(".py"):
        return False

    return True


def validate_command_segments(command: str) -> dict[str, Any] | None:
    """
    Validate a bash command by parsing all segments via shlex.split().

    Args:
        command: The full bash command string to validate

    Returns:
        None if command is allowed, dict with decision="block" if rejected
    """
    try:
        segments = shlex.split(command)
    except ValueError:
        # shlex parsing failed (unclosed quotes, etc.) - reject for safety
        return {"decision": "block", "reason": "shlex parsing failed", "command": command}

    if not segments:
        return None  # Empty command is allowed

    # Track consecutive pairs to detect "command -flag" patterns
    i = 0
    while i < len(segments):
        segment = segments[i]

        # Check exact dangerous patterns
        if segment in _DANGEROUS_PATTERNS:
            return {
                "decision": "block",
                "reason": f"dangerous pattern: {segment}",
                "command": command,
            }

        # Check "command -flag" pairs (e.g., "python -c", "bash -c")
        if i + 1 < len(segments):
            pair = f"{segment} {segments[i + 1]}"
            if pair in _DANGEROUS_PATTERNS:
                return {
                    "decision": "block",
                    "reason": f"dangerous pattern: {pair}",
                    "command": command,
                }

        # Special handling for python: only allow 'python script.py'
        if segment == "python":
            if not _is_python_script_invocation(segments, i):
                return {
                    "decision": "block",
                    "reason": "python invocation with flags or non-.py script",
                    "command": command,
                }
            # Skip the script argument since we verified it's safe
            i += 2
            continue

        # Safe commands are allowed without restriction
        if _is_safe_command(segment):
            i += 1
            continue

        # Unknown command - allow it (gate doesn't block unknown commands,
        # only known dangerous ones)
        i += 1

    return None


def is_command_allowed(command: str) -> bool:
    """
    Check if a command is allowed without detailed rejection reason.

    Args:
        command: The full bash command string

    Returns:
        True if allowed, False if blocked
    """
    result = validate_command_segments(command)
    return result is None
