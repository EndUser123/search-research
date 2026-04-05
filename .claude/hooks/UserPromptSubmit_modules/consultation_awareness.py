"""Consultation awareness injection for UserPromptSubmit.

Injects directive-recognition context when:
1. Prior LLM response ended with a question
2. Current prompt matches a directive seen in the same session
3. Tool calls do NOT exist for the directive (not yet acted upon)

This is advisory-only - does NOT block prompt processing.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Final

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Detection patterns
DIRECTIVE_PATTERNS: Final[list[re.Pattern]] = [
    re.compile(r"(?i)\b(?:consider all|implement|do|execute|start|begin|proceed)\b"),
    re.compile(r"(?i)\b(?:save the? |write an? )\b"),
    re.compile(r"(?i)\b(?:which (?:should |has )?(?:we|i) )\b"),
]

QUESTION_RESPONSE_PATTERNS: Final[list[re.Pattern]] = [
    re.compile(r"\?\s*$"),
    re.compile(r"which (?:would you|do you|should I|should we|i)\b"),
]

# State file for per-session tracking
_STATE_DIR: Final = Path(__file__).resolve().parent.parent / "state"


def _get_state_file(terminal_id: str, session_id: str) -> Path:
    """Get path to consultation awareness state file."""
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(terminal_id))
    safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(session_id))
    return _STATE_DIR / f"consultation_aware_{safe_terminal}_{safe_session}.json"


def _load_state(terminal_id: str, session_id: str) -> dict:
    """Load consultation awareness state for session."""
    state_file = _get_state_file(terminal_id, session_id)
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "prior_directives": [],  # directives seen in session
        "prior_llm_ended_with_question": False,
        "injected_directives": [],  # rate limiting
    }


def _save_state(terminal_id: str, session_id: str, state: dict) -> None:
    """Save consultation awareness state for session."""
    state_file = _get_state_file(terminal_id, session_id)
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # Fail open


def _is_directive(text: str) -> bool:
    """Check if text matches directive patterns."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in DIRECTIVE_PATTERNS)


def _is_question_response(text: str) -> bool:
    """Check if text matches question response patterns."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in QUESTION_RESPONSE_PATTERNS)


def _near_match(a: str, b: str) -> bool:
    """Check if two strings are near-matches (directive repetition)."""
    # Simple length + prefix check
    if not a or not b:
        return False
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()
    # Length check BEFORE exact match — short strings return False even if identical
    if len(a_lower) > 5 and len(b_lower) > 5:
        if a_lower == b_lower:
            return True
        if a_lower.startswith(b_lower[:20]) or b_lower.startswith(a_lower[:20]):
            return True
    return False


def _has_tool_calls(context: HookContext) -> bool:
    """Check if the current turn has tool calls (directive already acted upon)."""
    # Check data for tool_use or toolUse indicators
    data = context.data
    if isinstance(data, dict):
        # Check for tools_used list
        tools_used = data.get("tools_used", [])
        if tools_used and len(tools_used) > 0:
            return True
        # Check for toolUse list
        tool_use = data.get("toolUse", [])
        if tool_use and len(tool_use) > 0:
            return True
        # Check for tool_events
        tool_events = data.get("tool_events", [])
        if tool_events and len(tool_events) > 0:
            return True
    return False


@register_hook("consultation_awareness", priority=8.0)
def process_prompt(context: HookContext) -> HookResult:
    """Detect directive repeat with prior LLM question and inject awareness.

    Args:
        context: Hook context with prompt and data.

    Returns:
        HookResult with directive-recognition injection, or empty result.
    """
    prompt = context.prompt
    if not prompt:
        return HookResult.empty()

    terminal_id = context.terminal_id or ""
    session_id = context.session_id or ""

    # Extract terminal_id and session_id from data if not in context
    if not terminal_id:
        terminal_id = (
            context.data.get("terminal_id")
            or context.data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID")
            or "default"
        )
    if not session_id:
        session_id = (
            context.data.get("session_id")
            or context.data.get("sessionId")
            or os.environ.get("CLAUDE_SESSION_ID")
            or "default"
        )

    state = _load_state(terminal_id, session_id)
    prior_directives: list[str] = state.get("prior_directives", [])
    prior_llm_ended_with_question: bool = state.get("prior_llm_ended_with_question", False)
    injected_directives: list[str] = state.get("injected_directives", [])

    # Check if current prompt is a directive
    is_current_directive = _is_directive(prompt)

    # Check if prior LLM response ended with question
    # This info comes from the prior turn's transcript entry
    # We track it via state from the prior turn
    prior_ended_with_question = prior_llm_ended_with_question

    # Update state: record current directive if it's a directive
    if is_current_directive:
        # Normalize and store
        norm = prompt[:200].strip()
        if norm not in prior_directives:
            prior_directives.append(norm)
        state["prior_directives"] = prior_directives

    # Awareness injection threshold:
    # 1. Prior LLM ended with question AND
    # 2. Current prompt matches a prior directive (exact or near-match) AND
    # 3. No tool calls for this directive (not yet acted upon)
    directive_near_match = any(
        _near_match(prompt[:200].strip(), prior) for prior in prior_directives
    )
    if (
        prior_ended_with_question
        and is_current_directive
        and directive_near_match
        and not _has_tool_calls(context)
    ):
        # Check if this directive was already injected
        norm = prompt[:200].strip()
        if norm not in injected_directives:
            injected_directives.append(norm)
            state["injected_directives"] = injected_directives
            _save_state(terminal_id, session_id, state)

            injection = """DIRECTIVE-RECOGNITION: The user appears to be repeating a prior directive.
This is a DELEGATION signal — the decision was already made.
Proceed with execution immediately. Do not re-present options.

Begin with the highest-priority item from the prior analysis."""
            return HookResult(context=injection, priority=8.0)

    # Update prior_llm_ended_with_question for next turn
    # We detect this by checking if the last assistant message in transcript ends with ?
    # For now, track based on prompt pattern (prompt with ? at end suggests LLM asked)
    # Actually we need to check the PRIOR assistant response, not current prompt
    # The prior assistant response info comes from the transcript in data
    transcript = context.data.get("transcript", [])
    if isinstance(transcript, list) and len(transcript) >= 2:
        # Find last assistant message
        for entry in reversed(transcript):
            if entry.get("role") == "assistant":
                content = entry.get("content", "")
                if isinstance(content, list):
                    text = " ".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    )
                else:
                    text = str(content)
                state["prior_llm_ended_with_question"] = _is_question_response(text)
                break

    _save_state(terminal_id, session_id, state)
    return HookResult.empty()
