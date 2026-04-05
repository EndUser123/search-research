#!/usr/bin/env python3
"""
Breadcrumb Initialization Hook
==============================

⚠️  DEPRECATED 2026-03-11: Superseded by workflow_tier_tagging.py

The new approach:
- workflow_tier_tagging.py injects directive requesting step headers in output
- StopHook_step_header_verifier.py verifies step headers are present
- No hidden state files needed

This module is kept for backward compatibility but should not be used.

Original documentation:

Integrates with UserPromptSubmit router to initialize breadcrumb trails
when skills are invoked via /skill-name pattern.

This module wraps the implementation from the skill-guard package.

Configuration:
- BREADCRUMB_INITIALIZATION_ENABLED (default: true) - Enable/disable auto-initialization

Author: Skill Enforcement v2.0
Date: 2026-03-10
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add skill-guard to path
SKILL_GUARD = Path("P:/packages/skill-guard/src")
if SKILL_GUARD.exists():
    sys.path.insert(0, str(SKILL_GUARD))

# Import registry base classes
# Import the actual breadcrumb initialization logic
from skill_guard.breadcrumb.hooks.UserPromptSubmit_breadcrumb_init import (
    process_prompt_for_breadcrumbs,
)
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook


@register_hook("breadcrumb_init", priority=7.0)
def breadcrumb_init_hook(context: HookContext) -> HookResult:
    """Initialize breadcrumb trail when skill invocation detected.

    Args:
        context: Hook context with prompt, session info, etc.

    Returns:
        HookResult with context injection if breadcrumbs initialized
    """
    # Extract prompt from context
    prompt = context.prompt

    # Process for breadcrumb initialization
    result = process_prompt_for_breadcrumbs(prompt, context.data)

    if result:
        return HookResult(context={"additionalContext": result}, tokens=0)

    return HookResult.empty()
