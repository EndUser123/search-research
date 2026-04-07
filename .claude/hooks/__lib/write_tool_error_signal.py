#!/usr/bin/env python3
"""
Shared Tool Error Signal Writer
===============================

Single authoritative writer for `last_tool_error.json`.

Dual-writer problem this solves:
- PostToolUse.py wrote enriched {monotonic, tool_name, command, exit_code, stderr, stdout}
- PostToolUse_router.py wrote bare {time.time, tool_name, command}
- Router's bare write could clobber enriched signal before injection hook read it.

All consumers now call write_tool_error_signal() — exactly one writer, consistent schema.

Hardening features:
- Dual timestamps (monotonic + wall) for TTL robustness across process restarts
- Line-based truncation (last 40 lines stderr, last 20 stdout) preserves stack traces
- Expire-on-write: deletes stale signals before writing new ones
- session_id + terminal_id for multi-terminal debugging
- resolved_by_success flag for success-path cleanup
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Literal

HOOKS_DIR = Path(__file__).resolve().parent.parent
SIGNAL_DIR = Path("P:/.claude/state/signals")
MAX_AGE_SECONDS = 300  # 5 minutes TTL

# Line-based truncation limits (preserves stack trace structure)
MAX_STDERR_LINES = 40
MAX_STDOUT_LINES = 20


def _tail_lines(text: str, limit: int) -> str:
    """Return last `limit` lines of text, preserving structure."""
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) <= limit:
        return text
    return "\n".join(lines[-limit:])


def _resolve_session_id(data: dict) -> str:
    """Resolve session id from payload/env."""
    for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_SESSION_ID", "").strip()


def _resolve_terminal_id() -> str:
    """Resolve terminal id."""
    terminal = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if terminal:
        return terminal
    try:
        from __lib.terminal_detection import detect_terminal_id
        detected = str(detect_terminal_id() or "").strip()
        if detected:
            return detected
    except Exception:
        pass
    return ""


def _safe_filename_part(value: str) -> str:
    """Sanitize a string for use in filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _expire_on_write(signal_file: Path) -> None:
    """Delete signal file if it exceeds TTL (expire-on-write)."""
    if not signal_file.exists():
        return
    try:
        record = json.loads(signal_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        signal_file.unlink(missing_ok=True)
        return

    # Check wall clock age (safe across process restarts)
    wall_ts = record.get("wall_written_at")
    if wall_ts is not None:
        age = time.time() - wall_ts
        if age > MAX_AGE_SECONDS:
            signal_file.unlink(missing_ok=True)


def write_tool_error_signal(
    tool_name: str,
    tool_input: dict,
    tool_result: object,
    session_id: str = "",
    terminal_id: str = "",
    resolved: bool = False,
) -> None:
    """Write or clear the tool error signal file.

    Args:
        tool_name: Name of the tool (e.g., "Bash")
        tool_input: tool_input dict from hook payload
        tool_result: tool_result from hook payload
        session_id: Session ID for debugging
        terminal_id: Terminal ID for multi-terminal isolation
        resolved: If True, delete the signal (success path cleanup)
    """
    try:
        SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
        signal_file = SIGNAL_DIR / "last_tool_error.json"

        if resolved:
            if signal_file.exists():
                signal_file.unlink(missing_ok=True)
            return

        # Expire stale signals before writing new ones
        _expire_on_write(signal_file)

        command = (
            tool_input.get("command")
            or tool_input.get("content")
            or tool_input.get("path")
            or ""
        )

        # Detect failure — check both dict structure and string patterns
        is_error = False
        exit_code = None
        stderr_text = ""
        stdout_text = ""

        if isinstance(tool_result, dict):
            if "error" in tool_result:
                is_error = True
            exit_code = (
                tool_result.get("exit_code")
                or tool_result.get("returncode")
                or tool_result.get("status")
            )
            stderr_text = str(tool_result.get("stderr", ""))
            stdout_text = str(tool_result.get("stdout", ""))
            # Non-zero exit code = failure for Bash/Task
            if exit_code and exit_code != 0:
                is_error = True
        elif isinstance(tool_result, str) and tool_result.strip():
            result_lower = tool_result[:500].lower()
            if any(
                marker in result_lower
                for marker in (
                    "error:",
                    "traceback (most recent",
                    "exit code 1",
                    "exit code 2",
                    "command not found",
                    "no such file",
                    "permission denied",
                    "syntaxerror",
                    "importerror",
                )
            ):
                is_error = True

        if not is_error:
            if signal_file.exists():
                signal_file.unlink(missing_ok=True)
            return

        # Line-based truncation (preserves stack trace structure)
        stderr_tail = _tail_lines(stderr_text, MAX_STDERR_LINES)
        stdout_tail = _tail_lines(stdout_text, MAX_STDOUT_LINES)

        # Resolve IDs if not provided
        if not session_id:
            session_id = _resolve_session_id({})
        if not terminal_id:
            terminal_id = _resolve_terminal_id()

        # Build enriched record with dual timestamps
        record = {
            "wall_written_at": time.time(),  # Wall clock — survives process restarts
            "monotonic_written_at": time.monotonic(),  # Monotonic — valid within same epoch
            "tool_name": tool_name,
            "command": str(command)[:200],
            "session_id": session_id,
            "terminal_id": terminal_id,
            "resolved_by_success": False,
        }
        if exit_code is not None:
            record["exit_code"] = exit_code
        if stderr_tail:
            record["stderr"] = stderr_tail
        if stdout_tail:
            record["stdout"] = stdout_tail

        signal_file.write_text(json.dumps(record), encoding="utf-8")

    except OSError:
        pass  # Best-effort, never block


def main() -> None:
    """CLI entry point for direct testing."""
    import sys

    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("Usage: echo '{...}' | python write_tool_error_signal.py")
        sys.exit(0)

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", "") or data.get("tool_response", "")
    session_id = data.get("session_id", "") or data.get("sessionId", "")
    terminal_id = data.get("terminal_id", "")

    write_tool_error_signal(
        tool_name=tool_name,
        tool_input=tool_input,
        tool_result=tool_result,
        session_id=session_id,
        terminal_id=terminal_id,
    )


if __name__ == "__main__":
    main()
