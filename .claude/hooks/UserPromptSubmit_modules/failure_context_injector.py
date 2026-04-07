#!/usr/bin/env python3
"""
Failure Context Injector - UserPromptSubmit Hook
=================================================

Reads the enriched failure signal written by PostToolUse.py
and injects the actual stderr/stdout evidence into the next
reasoning turn via additionalContext.

Two-hook pattern (PostToolUse + UserPromptSubmit):
- PostToolUse captures failed Bash evidence → last_tool_error.json
- UserPromptSubmit re-injects it before next reasoning turn

This closes the feedback loop: failed command output is visible
to the model before it proposes the next fix.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

HOOKS_ROOT = Path(__file__).resolve().parent.parent.parent
SIGNAL_DIR = HOOKS_ROOT / "state" / "signals"
FAIL_FILE = SIGNAL_DIR / "last_tool_error.json"

# Max age for unresolved failure signal (seconds)
_MAX_AGE_SECONDS = 300  # 5 minutes


def _tail_lines(value: str, limit: int) -> str:
    """Return last `limit` lines of value, preserving stack trace structure."""
    if not value:
        return ""
    lines = value.splitlines()
    if len(lines) <= limit:
        return value
    return "\n".join(lines[-limit:])


@register_hook("failure_context_injector", priority=7.0)
def failure_context_injector(context: HookContext) -> HookResult:
    """Inject unresolved failure evidence into the next reasoning turn."""
    if not FAIL_FILE.exists():
        return HookResult.empty()

    try:
        record = json.loads(FAIL_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return HookResult.empty()

    # Check TTL — support both old timestamp field and new dual-timestamp fields
    ts = record.get("timestamp") or record.get("wall_written_at") or 0
    age = time.monotonic() - ts if ts else float("inf")
    if age > _MAX_AGE_SECONDS:
        try:
            FAIL_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        return HookResult.empty()

    # Build evidence string
    tool_name = record.get("tool_name", "?")
    command = record.get("command", "")
    exit_code = record.get("exit_code")
    stderr = record.get("stderr", "")
    stdout = record.get("stdout", "")

    # Skip if no actual error evidence to inject
    if not stderr and not stdout:
        return HookResult.empty()

    # Prefer stderr, fall back to stdout
    evidence = stderr or stdout
    evidence_source = "stderr" if stderr else "stdout"
    evidence_tail = _tail_lines(evidence, 30)  # Last 30 lines preserves stack traces

    lines = [
        "**Unresolved tool failure from previous turn**",
        f"- tool: `{tool_name}`",
        f"- exit code: `{exit_code}`",
        f"- command: `{command}`",
        f"- {evidence_source} (last 30 lines):",
        "```",
        evidence_tail,
        "```",
        "Before proposing the next fix, verify your plan directly explains this failure.",
    ]

    context_text = "\n".join(lines)
    return HookResult(context=context_text, tokens=len(evidence_tail) // 4 + 30)
