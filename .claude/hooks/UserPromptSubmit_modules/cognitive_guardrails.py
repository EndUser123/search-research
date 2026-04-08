#!/usr/bin/env python3
"""Cognitive Guardrails - UserPromptSubmit hook.

Detects design/implementation intent and injects discovery and generalization constraints.
Addresses two systemic LLM reasoning failures:
1. Discovery failure — proposing new implementations without searching for existing ones
2. Instance-class confusion — solving symptoms without checking broader problem class
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any

# Add hooks directory to path
HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HOOKS_DIR)

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Configuration
# COGNITIVE_GUARDRAILS_ENABLED: Strict boolean parsing - only accepts "true" (case-insensitive)
# Design intent: Explicit opt-in prevents accidental activation via ambiguous values like "1" or "yes"
# To disable: Set COGNITIVE_GUARDRAILS_ENABLED=false (exact string match required)
COGNITIVE_GUARDRAILS_ENABLED = os.environ.get("COGNITIVE_GUARDRAILS_ENABLED", "true").lower() == "true"

# Input length limit to prevent memory exhaustion from extreme prompts
MAX_QUERY_LENGTH = 10000

# Detection patterns for design/implementation intent
# IMPORTANT: Patterns are limited to .{0,50}? to prevent ReDoS (catastrophic backtracking)
# Patterns are precompiled at module load for performance
DESIGN_INTENT_PATTERNS = [
    # Action verbs + implementation objects
    re.compile(r"(?i)\b(design|architect|build|create|implement|add|make|develop)\b.{0,50}?\b(hook|skill|feature|solution|system|module|package|function|class|tool|service|command)\b"),
    # Planning/approach framing
    re.compile(r"(?i)\b(how should (we|i)|what'?s the (approach|solution|best way)|we need to (build|create|implement|design|add))\b"),
    # Explicit design skill invocations
    re.compile(r"(?:^|\s)/(arch|code|planning|adf|prd|tdd|feature-dev)\b"),
]

# Injection text when triggered
COGNITIVE_GUARDRAILS_INJECTION = """COGNITIVE GUARDRAILS ACTIVE

Before proposing any implementation or solution:

1. DISCOVERY MANDATE: Search for existing implementations first. State what you found — or explicitly confirm you searched and found nothing — before designing anything new.

2. GENERALIZATION CHECK: After identifying a solution, explicitly state:
   (a) What problem CLASS this covers (not just the presenting instance)
   (b) What other instances of this problem exist that your solution does NOT cover
   (c) Whether those uncovered instances require a separate solution or are acceptable gaps"""


@register_hook("cognitive_guardrails", priority=2.0)
def cognitive_guardrails(context: HookContext) -> HookResult:
    """
    Detect design/implementation intent and inject cognitive guardrails.

    Addresses discovery failure and instance-class confusion by injecting
    mandatory constraints when design intent is detected.

    Args:
        context: HookContext with prompt, data, session_id, terminal_id

    Returns:
        HookResult with additional context injection if design intent detected
    """
    if not COGNITIVE_GUARDRAILS_ENABLED:
        return HookResult.empty()

    # Extract data from HookContext with length limit
    user_query = str(context.data.get("prompt", "") or context.data.get("message", ""))
    if len(user_query) > MAX_QUERY_LENGTH:
        user_query = user_query[:MAX_QUERY_LENGTH]

    # Check for design intent patterns
    for pattern in DESIGN_INTENT_PATTERNS:
        if re.search(pattern, user_query):
            return HookResult(context={"additionalContext": COGNITIVE_GUARDRAILS_INJECTION})

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

    result = cognitive_guardrails(context)

    if (
        result.context
        and isinstance(result.context, dict)
        and "additionalContext" in result.context
    ):
        return {"additionalContext": result.context["additionalContext"]}
    return {}


if __name__ == "__main__":
    # Direct invocation for testing
    import json

    input_text = sys.stdin.read()
    try:
        data = json.loads(input_text) if input_text else {}
    except json.JSONDecodeError:
        data = {}

    result = process_prompt(data)
    print(json.dumps(result))
