#!/usr/bin/env python3
"""FrameGuard Classifier - UserPromptSubmit hook.

Detects systemic queries and records FrameGuard state.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

# Add hooks directory to path
HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HOOKS_DIR)

from evidence_store import (
    get_or_create_turn,
    record_frameguard_trigger,
)
from shared_utils import resolve_session_id
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Metrics tracking
try:
    from csftracker import frameguard_triggers_inc
except ImportError:

    def frameguard_triggers_inc() -> None:
        pass  # No-op if csftracker not available


# Configuration
FRAMEGUARD_ENABLED = os.environ.get("FRAMEGUARD_ENABLED", "true").lower() == "true"
FRAMEGUARD_MODE = os.environ.get("FRAMEGUARD_MODE", "warn").lower()

# Systemic query patterns - detect narrow-frame compliance issues
# IMPORTANT: Patterns are limited to .{0,200}? to prevent ReDoS (catastrophic backtracking)
SYSTEMIC_PATTERNS = [
    # "X in Y" style, where Y is likely a system
    r"(?i)\b(do we have|is there|exists|configured in|used in|part of)\b.{0,200}?\b(agent|hook|workflow|plan|config|service|registry)\b",
    r"(?i)\bthought we (had|have)\b.{0,200}?\b(agent|hook|feature)\b",
    r"(?i)\b(there's|there is|we have)\s+(a|an|no)\s+(hook|agent|skill|workflow|service)\b",
]

# Latent question templates for systemic frame
LATENT_TEMPLATES = {
    "systemic-coverage": "What is the relationship/coverage between the referenced element(s) and the larger system?",
    "neighbor-elements": "What other elements in the same system are relevant to this question?",
    "architectural-context": "What is the broader architectural context for this element?",
}


@register_hook("frameguard_classifier", priority=7.0)
def frameguard_classifier(context: HookContext) -> HookResult:
    """
    Classify user prompt for systemic framing requirements.

    Records FrameGuard state when systemic query detected.

    Args:
        context: HookContext with prompt, data, session_id, terminal_id

    Returns:
        HookResult with additional context injection if systemic pattern detected
    """
    if not FRAMEGUARD_ENABLED:
        return HookResult.empty()

    # Extract data from HookContext
    user_query = str(context.data.get("prompt", "") or context.data.get("message", ""))
    session_id = context.session_id or resolve_session_id(context.data)
    terminal_id = context.terminal_id or ""

    # Get or create turn_id
    turn_id = context.data.get("turn_id") or get_or_create_turn(session_id, terminal_id)

    # Check for systemic patterns
    needs_systemic = False
    trigger_reason = ""
    latent_questions = []

    for pattern in SYSTEMIC_PATTERNS:
        if re.search(pattern, user_query):
            needs_systemic = True
            trigger_reason = "Local existence/usage question inside an explicit system context."
            latent_questions = [
                {"id": key, "question": value} for key, value in LATENT_TEMPLATES.items()
            ]
            break

    # Record state if systemic frame needed
    if needs_systemic:
        # Track metrics
        frameguard_triggers_inc()

        record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=trigger_reason,
            latent_questions=latent_questions,
        )

        # Return injection context
        injection = (
            "FRAMEGUARD: SYSTEMIC FRAME DETECTED.\n"
            "Before answering, you MUST:\n"
            "1) State at least one broader structural question this query raises.\n"
            "2) Either address it explicitly OR say 'I am not addressing the broader structural question because ...'."
        )
        return HookResult(context={"additionalContext": injection})

    return HookResult.empty()


# For direct invocation (legacy compatibility)
def process_prompt(data: dict[str, Any]) -> dict[str, Any]:
    """Legacy entry point for direct invocation."""
    # Convert legacy dict to HookContext
    context = HookContext(
        prompt=data.get("prompt", "") or data.get("message", ""),
        data=data,
        session_id=data.get("session_id") or data.get("sessionId") or "",
        terminal_id=data.get("terminal_id") or data.get("terminalId") or "",
    )

    result = frameguard_classifier(context)

    if (
        result.context
        and isinstance(result.context, dict)
        and "additionalContext" in result.context
    ):
        return {"additionalContext": result.context["additionalContext"]}
    return {}


if __name__ == "__main__":
    # Direct invocation for testing
    input_text = sys.stdin.read()
    try:
        data = json.loads(input_text) if input_text else {}
    except json.JSONDecodeError:
        data = {}

    result = process_prompt(data)
    print(json.dumps(result))
