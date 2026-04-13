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
from UserPromptSubmit_modules.reasoning_contract import (
    build_reasoning_contract,
    mark_reasoning_contract_applied,
    reasoning_contract_already_applied,
)
from UserPromptSubmit_modules.unified_detection import (
    UnifiedDetectionResult,
    detect_prompt,
    ensure_unified_detection_result,
)

# Add reasoning package and hooks to path
REASONING_PKG = Path("P:/packages/reasoning")
REASONING_HOOKS = REASONING_PKG / "hooks"
if str(REASONING_PKG) not in sys.path:
    sys.path.insert(0, str(REASONING_PKG))
if str(REASONING_HOOKS) not in sys.path:
    sys.path.insert(0, str(REASONING_HOOKS))


def _map_unified_result_to_legacy_format(
    unified_result: UnifiedDetectionResult,
) -> dict[str, object]:
    """Map unified detection output back to the legacy selector shape."""
    matched_modes = list(unified_result.matched_modes or [])
    mode = matched_modes[0] if matched_modes else "sequential"
    confidence = getattr(unified_result, "confidence", None)
    if confidence is None:
        confidence = min(len(matched_modes), 4)
    reasoning_required = bool(matched_modes and confidence > 0)
    return {
        "mode": mode,
        "confidence": confidence,
        "reasoning_required": reasoning_required,
    }


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

        shared_result = ensure_unified_detection_result(context)
        fallback_used = False
        if shared_result is not None and shared_result.matched_modes:
            analysis = _map_unified_result_to_legacy_format(shared_result)
        else:
            fallback_used = True
            # Prefer unified detection as the shared source of truth.
            unified_result = detect_prompt(prompt)
            if unified_result.matched_modes:
                analysis = _map_unified_result_to_legacy_format(unified_result)
            else:
                fallback_used = True
                # Fall back to the legacy analyzer for any remaining edge cases.
                analysis = analyze_query(prompt)

        if not analysis.get("reasoning_required"):
            # No complex reasoning needed
            return HookResult.empty()

        # Build context with selected mode
        mode_name = analysis["mode"]
        confidence = analysis["confidence"]

        # System context for AI
        contract_active = reasoning_contract_already_applied(context)
        system_context = f"Reasoning mode: {mode_name} ({confidence}/4). Start here, then widen depth if uncertainty remains."
        if contract_active:
            system_context += "\n\nShared reasoning contract already applied upstream; keep the mode-specific guidance concise."
        else:
            system_context += (
                "\n\n"
                + build_reasoning_contract(
                    include_discovery=False,
                    include_rollback=False,
                    include_verification=True,
                    include_counterexample=True,
                    include_evidence=True,
                )
            )
            mark_reasoning_contract_applied(context, "reasoning_mode_selector")

        # User-facing message
        mode_display = {
            "sequential": "🔄 Sequential",
            "multi_agent": "🤖 Multi-Agent",
            "graph": "🌳 Graph",
            "two_stage": "⚡ Two-Stage",
        }.get(mode_name, mode_name)

        user_message = (
            f"**{mode_display} Reasoning** ({confidence}/4) - "
            f"base mode: {mode_name.replace('_', ' ')}."
        )

        # Log selection for observability (fail-safe - errors never break hook)
        # Estimate tokens from both contexts
        system_tokens = len(system_context) // 4
        user_tokens = len(user_message) // 4
        total_tokens = system_tokens + user_tokens

        log_reasoning_mode(
            mode=mode_name,
            confidence=confidence,
            fallback=fallback_used,
            tokens=total_tokens,
        )

        # Return both system context and user-facing message
        return HookResult(
            context={
                "systemContext": system_context,  # For AI
                "additionalContext": user_message,  # For user
                "suppress": [
                    "operating_rules",
                ],
            }
        )

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
