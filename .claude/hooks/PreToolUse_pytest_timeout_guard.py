#!/usr/bin/env python3
"""
PreToolUse: Pytest Timeout Guard

Enforces --timeout flag on pytest commands to prevent tests from hanging
the entire computer. This is a CRITICAL protection for Windows 11 environments.

BLOCKING by default because the LLM doesn't pay attention to advisory messages.
Bypass with --allow-no-timeout flag in the command.

Configuration:
    PYTEST_TIMEOUT_GUARD_ENABLED: Enable/disable this hook (default: true)
    PYTEST_TIMEOUT_GUARD_MODE: "block" (default) or "warn"

Exit Code Protocol:
    0: Allow (pytest command has --timeout or is exempt)
    2: Block (pytest command missing --timeout)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

def _is_enabled() -> bool:
    """Check if the hook is enabled (runtime evaluation, not module load time)."""
    return os.environ.get("PYTEST_TIMEOUT_GUARD_ENABLED", "true").lower() in ("1", "true")

def _guard_mode() -> str:
    mode = os.environ.get("PYTEST_TIMEOUT_GUARD_MODE", "block").strip().lower()
    if mode not in ("warn", "block"):
        return "block"
    return mode


# Patterns that should NOT trigger the guard (exemptions)
EXEMPT_PATTERNS = [
    r"pytest\s+(--version|-v|--help|-h)",
    r"pytest\s+--collect-only",
    r"python\s+-m\s+pytest\s+(--version|-v|--help|-h)",
    r"python\d*\s+-m\s+pytest\s+--collect-only",
    # Allow bypass flag
    r"--allow-no-timeout",
]

# Patterns that indicate pytest is being called (with or without python -m)
PYTEST_PATTERNS = [
    r"\bpytest\b",  # pytest command
    r"python\d*\s+-m\s+pytest",  # python -m pytest
    r"\bpy\.test\b",  # py.test (legacy)
]


def _is_exempt_command(command: str) -> bool:
    """Check if command matches an exemption pattern."""
    for pattern in EXEMPT_PATTERNS:
        if re.search(pattern, command):
            return True
    return False


def _is_pytest_command(command: str) -> bool:
    """Check if command is calling pytest."""
    for pattern in PYTEST_PATTERNS:
        if re.search(pattern, command):
            return True
    return False


def _has_timeout_flag(command: str) -> bool:
    """Check if pytest command includes --timeout flag."""
    return "--timeout" in command or "-t" in command.split()[1:3] if command else False


def _generate_block_message(mode: str) -> str:
    """Generate the block/warning message."""
    if mode == "block":
        return """⛔ PYTEST TIMEOUT REQUIRED

This pytest command is missing the --timeout flag, which can cause tests to hang
your entire computer (Windows 11 issue).

Required: pytest --timeout=30 [other_args]

To bypass this check (only if you know what you're doing): Add --allow-no-timeout to your command

Why this matters:
- Tests without timeout can hang indefinitely on Windows 11
- This can make your entire computer unusable
- The pytest-timeout plugin is thread-based and Windows-safe

Fix: Add --timeout=30 to your pytest command"""
    else:  # warn mode
        return """⚠️  PYTEST TIMEOUT WARNING

This pytest command is missing the --timeout flag. While not blocked, this is
strongly discouraged as tests can hang indefinitely on Windows 11.

Recommended: pytest --timeout=30 [other_args]"""


@hook_main
def run(data: dict) -> dict:
    """Main hook entry point."""
    if not ENABLED:
        return {"continue": True, "reason": "Hook disabled"}

    command = data.get("command", "")
    tool_name = data.get("tool_name", "")

    # Only check Bash tool
    if tool_name != "Bash":
        return {"continue": True, "reason": "Not a Bash command"}

    # Check if this is a pytest command
    if not _is_pytest_command(command):
        return {"continue": True, "reason": "Not a pytest command"}

    # Check for exemptions
    if _is_exempt_command(command):
        return {"continue": True, "reason": "Command exempt (version/help/collect-only/bypass)"}

    # Check if timeout flag is present
    if _has_timeout_flag(command):
        return {"continue": True, "reason": "Pytest command has timeout flag"}

    # No timeout flag - block or warn based on mode
    mode = _guard_mode()
    message = _generate_block_message(mode)

    if mode == "block":
        print(message, file=sys.stderr)
        return {"continue": False, "reason": "Missing --timeout flag"}
    else:  # warn mode
        print(message, file=sys.stderr)
        return {"continue": True, "reason": "Warning issued (advisory mode)"}


if __name__ == "__main__":
    # Hook entry point when called as subprocess
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)
    print(json.dumps(result))

    # Exit code protocol: 0 = allow, 2 = block
    # If continue is False, exit with code 2 to signal blocking
    if not result.get("continue", True):
        sys.exit(2)
