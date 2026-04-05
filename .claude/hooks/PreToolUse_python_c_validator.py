"""
PreToolUse Python -c Syntax Validator

Validates Python code syntax in `python -c` commands before execution.
Uses ast.parse() to catch syntax errors early.

Environment Variable:
    PYTHON_C_VALIDATOR_ENABLED: Enable/disable this hook (default: true)
    PYTHON_C_VALIDATOR_MODE: 'warn' (default), 'block', or 'off'

Exit Code Protocol:
    0: Allow (command passes validation)
    2: Block (syntax error detected)
"""

from __future__ import annotations

import ast
import json
import os
import sys

# Import auto-logging decorator
from __lib.hook_base import hook_main

ENABLED = os.environ.get("PYTHON_C_VALIDATOR_ENABLED", "true").lower() in ("1", "true")


def _validator_mode() -> str:
    mode = os.environ.get("PYTHON_C_VALIDATOR_MODE", "warn").strip().lower()
    if mode not in ("warn", "block", "off"):
        return "warn"
    return mode

def _extract_python_c_code(command: str) -> tuple[str, str] | tuple[None, None]:
    """Extract python -c code payload and outer quote char."""
    import re

    m = re.search(r"python(?:3)?\s+-c\s+([\"'])", command)
    if not m:
        return None, None
    outer_quote = m.group(1)
    start = m.end()
    i = start
    while i < len(command):
        ch = command[i]
        if ch == "\\":
            i += 2
            continue
        if ch == outer_quote:
            return command[start:i], outer_quote
        i += 1
    return command[start:], outer_quote


def _normalize_shell_escaped_code(code: str, outer_quote: str) -> str:
    normalized = code.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    if outer_quote == '"':
        normalized = normalized.replace('\\"', '"')
        normalized = normalized.replace('`"', '"')  # PowerShell-style escape
    if outer_quote == "'":
        normalized = normalized.replace("\\'", "'")
    return normalized


@hook_main
def main() -> None:
    """Hook entry point."""
    if not ENABLED:
        sys.exit(0)
    mode = _validator_mode()
    if mode == "off":
        sys.exit(0)

    # Read input from stdin
    input_data = json.loads(sys.stdin.read())
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    code, outer_quote = _extract_python_c_code(command)
    if not code:
        sys.exit(0)  # Not a python -c command, allow
    normalized_code = _normalize_shell_escaped_code(code, outer_quote or '"')

    # Validate Python syntax
    try:
        ast.parse(code)
        sys.exit(0)  # Syntax is valid, allow
    except SyntaxError as e:
        # Safe rewrite/normalization pass: allow when normalized form parses.
        if normalized_code != code:
            try:
                ast.parse(normalized_code)
                sys.exit(0)
            except SyntaxError:
                pass

        if mode != "block":
            # Warn mode: do not halt command execution.
            sys.exit(0)

        # Block with detailed error message showing the problematic line
        lines = code.split('\n')
        error_line = lines[e.lineno - 1] if 0 < e.lineno <= len(lines) else ''

        # Show pointer to error column
        pointer = ' ' * (e.offset - 1) + '^' if e.offset and e.offset <= len(error_line) else ''

        error_msg = f"""Python syntax error in -c command:

{e.msg}
Line {e.lineno}, Column {e.offset}

{error_line}
{pointer}

Full code:
{code}

The command was not executed. Please fix the syntax and retry."""

        # Claude Code treats stderr as hook error - reason is in exit code
        # print(error_msg, file=sys.stderr)
        sys.exit(2)  # Block (exit code 2 = permission denial)


if __name__ == "__main__":
    main()

