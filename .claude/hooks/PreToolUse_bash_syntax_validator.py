"""
PreToolUse Bash Syntax Validator

Validates bash command syntax including:
- Windows path syntax (missing backslashes)
- Python -c code syntax (reused from python_c_validator)

Environment Variable:
    BASH_SYNTAX_VALIDATOR_ENABLED: Enable/disable this hook (default: true)
    BASH_SYNTAX_VALIDATOR_MODE: 'warn' (default), 'block', or 'off'

Exit Code Protocol:
    0: Allow (command passes validation)
    2: Block (syntax error detected)
"""

from __future__ import annotations

import ast
import os
import re
import sys
import threading
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

ENABLED = os.environ.get("BASH_SYNTAX_VALIDATOR_ENABLED", "true").lower() in ("1", "true")

# Timeout for ast.parse() in seconds (fail-open if exceeded)
_PARSE_TIMEOUT = float(os.environ.get("BASH_SYNTAX_VALIDATOR_PARSE_TIMEOUT", "2.0"))


def _validator_mode() -> str:
    mode = os.environ.get("BASH_SYNTAX_VALIDATOR_MODE", "warn").strip().lower()
    if mode not in ("warn", "block", "off"):
        return "warn"
    return mode


def _parse_with_timeout(code: str, timeout: float) -> tuple[bool, str]:
    """Parse Python code with timeout. Returns (success, error_msg).

    Uses a background thread to interrupt ast.parse() if it hangs.
    Timeout is fail-open: on timeout, returns (True, "") to allow execution.
    """
    result = {"error": None}

    def parse_target():
        try:
            ast.parse(code)
        except SyntaxError as e:
            result["error"] = e
        except Exception as e:
            # Unexpected error during parse - re-raise to avoid silent failure
            result["error"] = e

    t = threading.Thread(target=parse_target, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        # Thread still running = timeout exceeded
        # Fail-open: allow execution with warning logged
        log_hook_event(
            "PreToolUse_bash_syntax_validator",
            "parse_timeout",
            {"code_length": len(code), "timeout": timeout},
        )
        return True, ""

    if result["error"] is None:
        return True, ""

    if isinstance(result["error"], SyntaxError):
        return False, str(result["error"])

    # Re-raise unexpected errors to surface them
    raise result["error"]


def _extract_python_c_code(command: str) -> tuple[str, str] | tuple[None, None]:
    """Extract python -c code payload and outer quote char."""
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
    """Normalize shell-escaped Python code."""
    normalized = code.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    if outer_quote == '"':
        normalized = normalized.replace('\\"', '"')
        normalized = normalized.replace('`"', '"')  # PowerShell-style escape
    if outer_quote == "'":
        normalized = normalized.replace("\\'", "'")
    return normalized


def validate_python_c(code: str, outer_quote: str) -> dict | None:
    """Validate Python -c code syntax. Returns block dict or None."""
    # Use timeout wrapper for fail-open behavior on hangs
    success, _ = _parse_with_timeout(code, _PARSE_TIMEOUT)
    if success:
        return None  # Syntax valid or timeout (fail-open)

    # Parse failed - check normalization
    normalized_code = _normalize_shell_escaped_code(code, outer_quote or '"')
    if normalized_code != code:
        norm_success, _ = _parse_with_timeout(normalized_code, _PARSE_TIMEOUT)
        if norm_success:
            return None  # Normalized form is valid

    # Real syntax error - parse to get error details
    try:
        ast.parse(code)
    except SyntaxError as e:
        syntax_error = e
    else:
        # Should not reach here - success was False
        return None

    lines = code.split("\n")
    error_line = lines[syntax_error.lineno - 1] if 0 < syntax_error.lineno <= len(lines) else ""

    # Show pointer to error column
    pointer = (
        " " * (syntax_error.offset - 1) + "^"
        if syntax_error.offset and syntax_error.offset <= len(error_line)
        else ""
    )

    error_msg = f"""Python syntax error in -c command:

{syntax_error.msg}
Line {syntax_error.lineno}, Column {syntax_error.offset}

{error_line}
{pointer}

Full code:
{code}

The command was not executed. Please fix the syntax and retry."""

    return {
        "decision": "block",
        "message": error_msg,
        "blocking_hook": "PreToolUse_bash_syntax_validator.py",
    }


def validate_bash_paths(command: str) -> tuple[bool, str | None]:
    r"""Validate Windows paths in bash commands.

    Detects malformed Windows paths like C:\Usersbrsth (missing backslashes).

    Returns:
        (is_valid, error_message)
    """
    # Quick check for obvious Windows path errors
    # Pattern: C: or P: followed by 5+ consecutive non-separator characters
    # This catches paths like "C:Usersbrsth" while allowing "C:/path" or "C:\path"
    malformed_paths = re.findall(r"[A-Za-z]:[^/\\]{5,}", command)

    # Filter out false positives (e.g., URLs, etc.)
    actual_paths = []
    for p in malformed_paths:
        # Skip URLs: http://, https://, ftp://
        if p.lower().startswith(("http:", "https:", "ftp:")):
            continue
        actual_paths.append(p)

    if actual_paths:
        return False, f"Malformed Windows path detected: {actual_paths[0]} (missing backslashes?)"

    return True, None


def _normalize_drive_paths(command: str) -> str:
    """Normalize drive-qualified paths to forward slashes for shell safety."""

    def repl(match: re.Match[str]) -> str:
        return re.sub(r"\\+", "/", match.group(0))

    return re.sub(
        r"(?<![\w/])(?:[A-Za-z]:\\[^\"'\s;&|]+(?:\\[^\"'\s;&|]+)*)",
        repl,
        command,
    )


def _extract_python_script_path(command: str) -> tuple[str | None, int]:
    """Extract a Python script path and invocation offset from a bash command."""
    match = re.search(
        r"python(?:3)?(?:\.exe)?\s+(?P<arg>\"[^\"]+\"|'[^']+'|[^\s;&|]+)",
        command,
        re.IGNORECASE,
    )
    if not match:
        return None, -1

    raw_arg = match.group("arg").strip()
    if raw_arg.startswith("-"):
        return None, match.start()

    if raw_arg[:1] in {'"', "'"} and raw_arg[-1:] == raw_arg[:1]:
        raw_arg = raw_arg[1:-1]

    return raw_arg or None, match.start()


def _is_drive_qualified(path: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", path))


def _has_prior_shell_steps(command: str, python_offset: int) -> bool:
    if python_offset <= 0:
        return False
    prefix = command[:python_offset]
    return bool(re.search(r"&&|\|\||;|\n|<<|>>|>|<", prefix))


def _resolve_script_candidate(
    script_path: str, tool_input: dict, python_offset: int, command: str
) -> Path | None:
    normalized = script_path.replace("\\", "/")

    # If there are prior shell steps, do not guess runtime effects such as cd,
    # file creation, or heredoc writes. Fail open and let Bash execute.
    if _has_prior_shell_steps(command, python_offset):
        return None

    if _is_drive_qualified(normalized) or normalized.startswith("/"):
        return Path(normalized)

    cwd = str(tool_input.get("cwd", "")).strip() if isinstance(tool_input, dict) else ""
    if not cwd:
        return None

    return Path(cwd) / normalized


def _validate_python_script_path(command: str, tool_input: dict | None = None) -> dict | None:
    """Block clearly missing local Python script paths before execution."""
    script_path, python_offset = _extract_python_script_path(command)
    if not script_path:
        return None

    normalized = script_path.replace("\\", "/")
    candidate = _resolve_script_candidate(script_path, tool_input or {}, python_offset, command)

    # Ignore module-style or flag-based invocations.
    if not normalized.lower().endswith(".py"):
        return None

    if candidate is None:
        return None

    if candidate.exists():
        return None

    details = [f"Python script path does not exist: {normalized}"]
    parent = candidate.parent
    if parent.exists():
        nearby = sorted(
            entry.name for entry in parent.iterdir() if entry.is_file() and entry.suffix == ".py"
        )[:5]
        if nearby:
            details.append(f"Available .py files in {parent}: {', '.join(nearby)}")

    return {
        "decision": "block",
        "message": "\n".join(details),
        "blocking_hook": "PreToolUse_bash_syntax_validator.py",
    }


def _is_hook_execution_command(command: str) -> bool:
    """Check if command is executing a hook (should be exempt from validation)."""
    # Exempt commands that execute hook_runner.py or other hooks
    hook_patterns = [
        "hook_runner.py",
        ".claude/hooks/",
        "PreToolUse_",
        "PostToolUse_",
        "UserPromptSubmit_",
        "Stop_hook",
    ]
    command_lower = command.lower()
    return any(pattern.lower() in command_lower for pattern in hook_patterns)


def run(data: dict) -> dict | None:
    """In-process hook entry point for bash syntax validation.

    Returns:
        None: Allow (command passes validation)
        dict: Block decision with error message
    """
    if not ENABLED:
        return None

    mode = _validator_mode()
    if mode == "off":
        return None

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return None

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return None

    # Exempt hook execution commands from validation (breaks circular dependency)
    if _is_hook_execution_command(command):
        return None

    # Check for Python -c validation first
    code, outer_quote = _extract_python_c_code(command)
    if code:
        result = validate_python_c(code, outer_quote or '"')
        if result:
            if mode != "block":
                # Warn mode: do not halt command execution
                return None
            return result
    else:
        normalized_command = _normalize_drive_paths(command)
        if normalized_command != command:
            missing_script = _validate_python_script_path(
                normalized_command, data.get("tool_input", {})
            )
            if missing_script:
                return missing_script

            tool_input = data.get("tool_input", {})
            if isinstance(tool_input, dict):
                updated_tool_input = dict(tool_input)
                updated_tool_input["command"] = normalized_command
                return {
                    "decision": "modify",
                    "tool_input": updated_tool_input,
                }

        missing_script = _validate_python_script_path(command, data.get("tool_input", {}))
        if missing_script:
            return missing_script

    # NEW: Validate bash paths
    is_valid, error = validate_bash_paths(command)
    if not is_valid:
        error_msg = f"⚠️ BASH PATH SYNTAX ERROR\n{error}\n\nCommand: {command[:100]}..."

        if mode != "block":
            # Warn mode: do not halt command execution
            return None

        return {
            "decision": "block",
            "message": error_msg,
            "blocking_hook": "PreToolUse_bash_syntax_validator.py",
        }

    return None


@hook_main
def main() -> None:
    """Hook entry point for subprocess execution (legacy compatibility)."""
    if not ENABLED:
        sys.exit(0)

    mode = _validator_mode()
    if mode == "off":
        sys.exit(0)

    # Read input from stdin
    import json

    input_data = json.loads(sys.stdin.read())

    result = run(input_data)

    if result:
        decision = result.get("decision")

        if decision == "modify":
            # Output the modified tool_input so Claude Code applies the correction.
            # Format: {"tool_input": {...}} with exit 0 — recognized by Claude Code
            # as a tool-input modification request.
            import json as _json

            print(_json.dumps({"tool_input": result["tool_input"]}))
            sys.exit(0)

        # Blocking decision
        if mode == "block" and decision == "block":
            # Claude Code shows stderr as the error reason - MUST print descriptive message
            print(result.get("message", "Bash command blocked"), file=sys.stderr)
            sys.exit(2)  # Block (exit code 2 = permission denial)

    sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
