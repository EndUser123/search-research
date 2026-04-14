#!/usr/bin/env python3
"""
PostToolUse - Lean Router v2.1
==============================

Replaces monolithic PostToolUse_router.py.
Handles tool-event logging and side-effects (like auto-commit).

v2.1: Convert side-effect hooks to in-process execution (no subprocess = no flash).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from evidence_store import append_tool_event  # noqa: E402
from posttooluse import create_registry, is_block_result  # noqa: E402
from __lib.write_tool_error_signal import write_tool_error_signal  # noqa: E402

# Configure logger for PostToolUse - no stderr output (Claude Code treats stderr as hook error)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Signal directory for cross-hook communication
SIGNAL_DIR = Path("P:/.claude/state/signals")


def _resolve_session_id_for_intent(data: dict) -> str:
    """Resolve session id from nested/flat payload first, then env."""
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in (
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "CLAUDE_SESSION_ID",
    ):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_SESSION_ID", "").strip()


def _resolve_terminal_id_for_intent(data: dict) -> str:
    """Resolve terminal id, mirroring skill_enforcer._get_terminal_id."""
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


def _clear_pending_skill_intent(data: dict) -> None:
    """Clear pending_command_intent file when Skill() is called.

    This is the handshake: UserPromptSubmit sets the flag, PreToolUse blocks
    until Skill is called, and PostToolUse clears the flag here.

    Writer (skill_enforcer) uses terminal-scoped filenames. We must delete the
    same terminal-scoped file; session-scoped is kept as a legacy fallback.
    """
    import re

    session_id = _resolve_session_id_for_intent(data)
    terminal_id = _resolve_terminal_id_for_intent(data)

    state_dirs = (
        HOOKS_DIR / "state",
        Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state",
    )

    # Primary: terminal-scoped (matches what skill_enforcer writes)
    if terminal_id:
        safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
        for base_dir in state_dirs:
            intent_file = base_dir / f"pending_command_intent_{safe_terminal}.json"
            if intent_file.exists():
                intent_file.unlink(missing_ok=True)
                return

    # Legacy fallback: session-scoped (pre-terminal-scoped intent files)
    if session_id:
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        for base_dir in state_dirs:
            intent_file = base_dir / f"pending_command_intent_{safe_session}.json"
            if intent_file.exists():
                intent_file.unlink(missing_ok=True)
                return


def main():
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_result = data.get("tool_result", "")
    session_id = data.get("session_id") or data.get("sessionId", "unknown")

    # 0. Skill-first gate: clear pending intent when Skill() is called
    if tool_name == "Skill":
        _clear_pending_skill_intent(data)

    # 1. Log Event to Evidence Store (Crucial for Behavioral Proof)
    try:
        command = (
            tool_input.get("command") or tool_input.get("content") or tool_input.get("path") or ""
        )
        success = True
        if isinstance(tool_result, dict) and "error" in tool_result:
            success = False
        elif isinstance(tool_result, str) and tool_result.strip():
            # Detect common error patterns in string output
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
                success = False

        append_tool_event(
            session_id=session_id,
            terminal_id=_resolve_terminal_id_for_intent(data),
            tool_name=tool_name,
            command=str(command),
            output_excerpt=str(tool_result)[:2000],
            success=success,
        )

        # Write error signal via shared writer (unified, eliminates dual-writer conflict)
        # resolved=True clears the signal on success (success-path cleanup)
        try:
            write_tool_error_signal(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_result=tool_result,
                resolved=success,
            )
        except Exception:
            pass

    except Exception as e:
        logger.debug(f"PostToolUse Logging Error: {e}")

    # 1.5. Cognitive Injection - Give LLM micro-pause on error/empty results
    injection_message = None

    # Error case detection
    if not success:
        injection_message = (
            f"Tool `{tool_name}` returned an error. "
            "State your revised hypothesis in 1 sentence before your next action."
        )
    # Empty results case for diagnostic tools
    elif tool_name in ("Grep", "Glob"):
        result_str = str(tool_result).strip() if tool_result else ""
        if not result_str or "0 matches" in result_str or "No files found" in result_str:
            injection_message = (
                f"Tool `{tool_name}` returned no results. "
                "Your search assumption may be wrong. Revise your approach before retrying."
            )
    # Bash-specific error detection
    elif tool_name == "Bash":
        result_str = str(tool_result) if tool_result else ""
        if (
            "No such file" in result_str
            or "exit code 1" in result_str
            or "exit code 2" in result_str
        ):
            injection_message = (
                f"Tool `{tool_name}` returned an error. "
                "State your revised hypothesis in 1 sentence before your next action."
            )
    # MCP payload bloat detection
    elif isinstance(tool_name, str) and tool_name.startswith("mcp__"):
        result_str = str(tool_result) if tool_result is not None else ""
        char_count = len(result_str)
        if char_count >= 60_000:  # ~15k tokens — CRITICAL
            token_est = char_count // 4
            injection_message = (
                f"🔴 CONTEXT BLOAT [CRITICAL]: `{tool_name}` returned ~{token_est:,} tokens "
                f"({char_count:,} chars). "
                "Extract ONLY the specific fact you need. "
                "Do NOT summarize or re-expand this content in your reply. "
                "⚠️ This single response consumed significant context budget — "
                "avoid further large reads this session."
            )
            if "web-reader" in tool_name or "exa" in tool_name:
                injection_message += (
                    " For future code repo reads: prefer `mcp__aid__distill_file` "
                    "(public API only, 90–98% compression)."
                )
        elif char_count >= 20_000:  # ~5k tokens — WARNING
            token_est = char_count // 4
            injection_message = (
                f"🟡 CONTEXT BLOAT [WARNING]: `{tool_name}` returned ~{token_est:,} tokens "
                f"({char_count:,} chars). "
                "Extract ONLY the specific fact you need. "
                "Do NOT summarize or re-expand this content in your reply."
            )
            if "web-reader" in tool_name or "exa" in tool_name:
                injection_message += " For future code repo reads: prefer `mcp__aid__distill_file`."
            elif "tavily" in tool_name:
                injection_message += " For future reads: use tavily_search (snippets) instead of full-page extraction."
        elif char_count >= 4_000:  # ~1k tokens — ADVISORY
            token_est = char_count // 4
            injection_message = (
                f"🔵 CONTEXT NOTE: `{tool_name}` returned ~{token_est:,} tokens. "
                "Extract ONLY the specific fact you need."
            )

    # 2. Run PostToolUse Registry - all verification and side-effect hooks
    # Skip for read-only tools to save overhead.
    # Registry runs synchronously to capture injection output
    registry_result = {}
    if tool_name not in ("Read", "Glob", "Grep", "ls", "dir"):
        try:
            registry_result = create_registry().run_all(data)
        except Exception as e:
            logger.debug(f"Registry error: {e}")

    if is_block_result(registry_result):
        print(json.dumps(registry_result))
        sys.exit(2)

    # 1.6. Output injection if present
    # Merge cognitive injection with registry results
    additional_context_parts = []
    if injection_message:
        additional_context_parts.append(injection_message)

    # Add registry injections if present
    if registry_result and registry_result.get("hookSpecificOutput", {}).get("additionalContext"):
        additional_context_parts.append(registry_result["hookSpecificOutput"]["additionalContext"])

    if additional_context_parts:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "\\n\\n".join(additional_context_parts),
            }
        }
        print(json.dumps(output))
    else:
        print("{}")

    sys.exit(0)


if __name__ == "__main__":
    try:
        from __lib.subprocess_patch import patch_subprocess_context
    except ImportError:
        from subprocess_patch import patch_subprocess_context  # type: ignore

    # Use context manager for scoped subprocess patching
    with patch_subprocess_context():
        main()
