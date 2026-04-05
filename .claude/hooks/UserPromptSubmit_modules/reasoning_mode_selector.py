#!/usr/bin/env python3
"""Reasoning mode selector hook for UserPromptSubmit router.

Integrates Start_reasoning_mode_selector.py from the reasoning package
into the UserPromptSubmit hook system.

This hook analyzes user queries to determine optimal reasoning mode:
- Sequential: Step-by-step analysis
- Multi-Agent: Multiple perspectives for complex decisions
- Graph: Branching exploration of alternatives
- Two-Stage: Separate reasoning and implementation phases
"""

from __future__ import annotations

import sys
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.observability import log_reasoning_mode

# Add reasoning package and hooks to path
REASONING_PKG = Path("P:/packages/reasoning")
REASONING_HOOKS = REASONING_PKG / "hooks"
if str(REASONING_PKG) not in sys.path:
    sys.path.insert(0, str(REASONING_PKG))
if str(REASONING_HOOKS) not in sys.path:
    sys.path.insert(0, str(REASONING_HOOKS))


def reasoning_mode_selector(context: HookContext) -> HookResult:
    """Select optimal reasoning mode based on query analysis.

    Args:
        context: Hook context with prompt/data

    Returns:
        HookResult with reasoning mode context or empty result
    """
    try:
        # Import the reasoning mode selector
        # Path: P:/packages/reasoning/hooks/Start_reasoning_mode_selector.py
        import Start_reasoning_mode_selector as selector_module
        analyze_query = selector_module.analyze_query

        prompt = context.prompt
        if not prompt or len(prompt.strip()) < 20:
            # Skip very short prompts
            return HookResult.empty()

        # Analyze query for optimal reasoning mode
        analysis = analyze_query(prompt)

        if not analysis.get("reasoning_required"):
            # No complex reasoning needed
            return HookResult.empty()

        # Build context with selected mode
        mode_name = analysis["mode"]
        confidence = analysis["confidence"]

        # System context for AI
        system_context = (
            f"Reasoning mode: {mode_name}\n"
            f"Confidence: {confidence}/4\n"
            f"Using {mode_name} reasoning approach for this query."
        )

        # User-facing message
        mode_display = {
            "sequential": "🔄 Sequential",
            "multi_agent": "🤖 Multi-Agent",
            "graph": "🌳 Graph",
            "two_stage": "⚡ Two-Stage",
        }.get(mode_name, mode_name)

        user_message = (
            f"**{mode_display} Reasoning** (confidence: {confidence}/4)\n"
            f"This query will use {mode_name.replace('_', ' ')} reasoning."
        )

        # Log selection for observability (fail-safe - errors never break hook)
        # Estimate tokens from both contexts
        system_tokens = len(system_context) // 4
        user_tokens = len(user_message) // 4
        total_tokens = system_tokens + user_tokens

        log_reasoning_mode(
            mode=mode_name,
            confidence=confidence,
            fallback=False,  # Not a fallback selection
            tokens=total_tokens,
        )

        # Return both system context and user-facing message
        return HookResult(context={
            "systemContext": system_context,  # For AI
            "additionalContext": user_message,  # For user
        })

    except Exception as e:
        # Fail open - don't break on errors
        # Log error for debugging
        print(f"[reasoning_mode_selector] Error: {e}", file=sys.stdout)
        import traceback
        traceback.print_exc(file=sys.stdout)
        return HookResult.empty()


# Register with UserPromptSubmit registry
from UserPromptSubmit_modules.registry import register_hook

register_hook("reasoning_mode_selector", priority=8.0)(reasoning_mode_selector)
