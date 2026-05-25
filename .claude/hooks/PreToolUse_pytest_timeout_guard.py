#!/usr/bin/env python3
"""
PreToolUse: Pytest Timeout Guard

Enforces --timeout flag on pytest commands to prevent tests from hanging
the entire computer. This is a CRITICAL protection for Windows 11 environments.

BLOCKING by default because the LLM doesn't pay attention to advisory messages.
Bypass with --allow-no-timeout flag in the command.

Configuration:
    PYTEST_TIMEOUT_GUARD_ENABLED: Enable/disable this hook (default: true)
    PYTEST_GUARD_MODE: "block" (default) or "warn"

Exit Code Protocol:
    0: Allow (pytest command has --timeout or is exempt)
    2: Block (pytest command missing --timeout)

THREAT MODEL (SOLO DEV):
This hook operates in a solo development environment where the "attacker" is the
developer themselves. Security findings about command injection or path traversal are
LOW severity in this context because:
1. The hook validates the developer's own commands before execution
2. subprocess.run() uses list arguments (not shell=True), preventing actual injection
3. The worst case is the developer blocking their own commits, not external compromise

In multi-user or CI/CD environments, additional hardening would be required.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

import logging as _li
_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)



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
    r"pytest\s+--version",  # Version query (not -v which means verbose)
    r"pytest\s+(--help|-h)",  # Help query
    r"pytest\s+--collect-only",  # Collection only (no execution)
    r"python\s+-m\s+pytest\s+--version",  # python -m pytest --version
    r"python\d*\s+-m\s+pytest\s+(--help|-h)",  # python -m pytest --help
    r"python\d*\s+-m\s+pytest\s+--collect-only",  # python -m pytest --collect-only
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
    # Check for --timeout flag (catches all cases including -t=30 variants)
    if "--timeout" in command:
        return True
    # Check for short -t flag (only checks positions 1-2 for common usage)
    # Note: This is intentionally limited to positions 1-2 for common patterns.
    # The --timeout substring check above catches all realistic usage patterns.
    # Edge case: 'pytest --verbose -t' would miss -t, but pytest itself
    # requires '-t SECONDS' value, so '-t' without value is invalid anyway.
    if command and "-t" in command.split()[1:3]:
        return True
    return False


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
    if not _is_enabled():
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
            _logger.debug(message,)        return {"continue": False, "reason": "Missing --timeout flag"}
    else:  # warn mode
            _logger.debug(message,)        return {"continue": True, "reason": "Warning issued (advisory mode)"}


if __name__ == "__main__":
    # Hook entry point when called as subprocess
    # NOTE: sys.stdin.read() timeout is handled by Claude Code hook framework.
    # The hook_runner.py provides timeout guarantees for all hook stdin reads.
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)
    print(json.dumps(result))

    # Exit code protocol: 0 = allow, 2 = block
    # If continue is False, exit with code 2 to signal blocking
    if not result.get("continue", True):
        sys.exit(2)
