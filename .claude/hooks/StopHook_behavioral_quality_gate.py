#!/usr/bin/env python3
"""
StopHook_behavioral_quality_gate.py - Response Quality Gate

Catches two behavioral anti-patterns that other hooks don't cover:

1. Question-type mismatch: User asks a binary yes/no question but gets a
   verbose essay response. Binary questions deserve direct yes/no + brief context.

2. Narration without action: Response says "I'll run X" / "Let me check Y" but
   no tool execution followed. Either do it or drop the narration.

Note: lazy_closure and overconfidence are handled by StopHook_unverified_stance
and StopHook_overconfidence_detector respectively. This hook covers what remains.

Environment:
  BEHAVIORAL_QUALITY_GATE_ENABLED  (default: true)
  BEHAVIORAL_QUALITY_GATE_MODE     (default: warn, options: warn|block)
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

ENABLED = os.environ.get("BEHAVIORAL_QUALITY_GATE_ENABLED", "true").lower() == "true"
MODE = os.environ.get("BEHAVIORAL_QUALITY_GATE_MODE", "warn").lower()

# Binary question: starts with a yes/no question word and ends with "?"
_BINARY_STARTERS = re.compile(
    r"^(?:is|are|was|were|did|do|does|can|could|should|would|will|has|have|had)" r"\s+\S",
    re.IGNORECASE,
)

# Verbose threshold: responses over this word count for a binary question are flagged
_VERBOSE_THRESHOLD = 250

# Narration-without-action: "I'll X" / "I will X" / "Let me X" + execution verb
_NARRATION_PATTERN = re.compile(
    r"\b(?:I(?:'ll| will| am going to)|[Ll]et me)\s+"
    r"(?:run|execute|test|verify|check|look at|read|search for|grep|find|inspect|open)\b",
    re.IGNORECASE,
)

# Evidence that actual execution happened (code blocks, test markers, command output)
_EXECUTION_EVIDENCE = re.compile(
    r"(?:```[\s\S]*?```"
    r"|(?:PASSED|FAILED|ERROR)\s"
    r"|✓|✗"
    r"|\$ (?:python|pytest|npm|ruff|mypy)"
    r"|\bpytest\b.*\bpassed\b"
    r"|\btest output\b"
    r"|\bOutput:\b)",
    re.IGNORECASE,
)

# Execution tool names that count as evidence
_EXECUTION_TOOLS = frozenset({"Bash", "Read", "Grep", "Glob", "Write", "Edit"})


def _check_question_type_mismatch(prompt: str, response: str) -> str | None:
    """Flag binary questions that receive overly verbose responses."""
    if not prompt or not response:
        return None

    # Look at the first sentence/question of the prompt
    stripped = prompt.strip()
    q_pos = stripped.find("?")
    first_q = stripped[: q_pos + 1].strip() if q_pos >= 0 else stripped

    # Must end with "?" and start with a binary question word
    if not first_q.endswith("?"):
        return None
    if not _BINARY_STARTERS.match(first_q):
        return None

    word_count = len(response.split())
    if word_count < _VERBOSE_THRESHOLD:
        return None

    preview = first_q[:80] + ("..." if len(first_q) > 80 else "")
    return (
        f"Binary question got a {word_count}-word response. "
        f'Question: "{preview}". '
        f"Start with a direct yes/no answer, then add context."
    )


def _check_narration_without_action(response: str, tool_events: list[dict[str, Any]]) -> str | None:
    """Flag 'I'll X' / 'Let me X' narrations with no follow-through evidence."""
    if not response:
        return None

    narration = _NARRATION_PATTERN.search(response)
    if not narration:
        return None

    # Tool events are the strongest evidence of execution
    for event in tool_events:
        if isinstance(event, dict) and event.get("name", "") in _EXECUTION_TOOLS:
            return None

    # Code blocks / test output in the response also count
    if _EXECUTION_EVIDENCE.search(response):
        return None

    phrase = narration.group(0)
    return (
        f'Narration without execution: "{phrase}". '
        f"Either run the action with tools or remove the narration."
    )


def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """In-process validator protocol for Stop_router."""
    if not ENABLED:
        return None

    response = str(data.get("assistant_response") or data.get("response") or "")
    if not response:
        return None

    prompt = str(data.get("user_prompt") or data.get("prompt") or "")
    tool_events: list[dict[str, Any]] = data.get("tool_events") or []

    messages: list[str] = []

    q_msg = _check_question_type_mismatch(prompt, response)
    if q_msg:
        messages.append(f"**Question-type mismatch**: {q_msg}")

    n_msg = _check_narration_without_action(response, tool_events)
    if n_msg:
        messages.append(f"**Narration without action**: {n_msg}")

    if not messages:
        return None

    note = "⚠️ Response quality issue:\n\n" + "\n\n".join(messages)

    if MODE == "block":
        return {
            "block": True,
            "reason": note,
            "blocking_hook": "StopHook_behavioral_quality_gate.py",
        }
    return {"allow": True, "note": note}
