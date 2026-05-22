#!/usr/bin/env python3
"""
First-Query Judge Advisory - Injects advisory on first user query if judge patterns indicate problems.

This module is called during UserPromptSubmit to check if:
1. We have recent judge data showing issues
2. We haven't already shown this advisory for this session
3. The trigger conditions are met (block rate >= 15%, avg score < 0.72, or same issue >= 3x)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add hooks lib to path for judge_feedback imports
_HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS_DIR / "__lib"))

from UserPromptSubmit_modules.base import HookContext, HookResult

try:
    from judge_feedback import (
        load_recent_judge_verdicts,
        summarize_judge_activity,
        should_inject_first_query_advisory,
        build_first_query_advisory,
        mark_advisory_shown,
    )
except ImportError:
    # Module not available - fail silently
    def load_recent_judge_verdicts(hours=24):
        return []

    def summarize_judge_activity(verdicts):
        return {}

    def should_inject_first_query_advisory(summary, session_id):
        return False

    def build_first_query_advisory(summary):
        return None

    def mark_advisory_shown(session_id):
        pass


def _process_prompt_impl(context: HookContext) -> HookResult:
    """Process first-query for judge advisory conditions.

    Args:
        context: HookContext with session info and prompt

    Returns:
        HookResult with additionalContext if advisory should be shown
    """
    # Get session ID from context data
    session_id = context.session_id or ""

    # Check if this is the first query (no message history)
    # We check if there's meaningful conversation context already
    messages = context.data.get("messages", [])
    user_messages = [m for m in messages if m.get("role") == "user"]

    # Only inject on first user message
    if len(user_messages) > 1:
        return HookResult.empty()

    # Load recent judge data and check trigger conditions
    verdicts = load_recent_judge_verdicts(hours=24)
    summary = summarize_judge_activity(verdicts)

    if should_inject_first_query_advisory(summary, session_id):
        advisory = build_first_query_advisory(summary)
        if advisory:
            # Mark that we've shown this advisory
            mark_advisory_shown(session_id)
            return HookResult(context=advisory, tokens=_estimate_tokens(advisory))

    return HookResult.empty()


def _estimate_tokens(text: str) -> int:
    """Estimate token count for advisory text."""
    return len(text) // 4  # Rough approximation


# Register with registry using correct signature
from UserPromptSubmit_modules.registry import register_hook

register_hook("judge_first_query_advisory", priority=7.0)(_process_prompt_impl)