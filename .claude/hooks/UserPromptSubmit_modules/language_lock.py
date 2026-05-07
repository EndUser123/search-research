"""Language lock injector for UserPromptSubmit.

Prevents CJK drift from Chinese-trained models (GLM-5.1, etc.) by injecting
a hard language constraint at every turn. Runs at high priority (2.0) so the
constraint is visible early in the injected context.

This is the pre-generation fix — the Stop-hook cjk_drift_detector.py is the
post-generation backstop.
"""

from __future__ import annotations

import os
import sys

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

_ENABLED_ENV = "LANGUAGE_LOCK_ENABLED"

_INJECTION = (
    "SESSION CONSTRAINT (active until revoked): Output must be in English only. "
    "Do not use any other language in your response."
)


def _is_enabled() -> bool:
    return os.environ.get(_ENABLED_ENV, "true").lower() in ("1", "true", "yes")


@register_hook("language_lock", priority=2.0)
def language_lock(context: HookContext) -> HookResult:
    """Inject English-only constraint to prevent CJK drift."""
    if not _is_enabled():
        return HookResult.empty()

    prompt = context.prompt or ""
    stripped = prompt.strip().lower()

    # Skip empty prompts and slash commands
    if not stripped:
        return HookResult.empty()
    if stripped.startswith("/"):
        return HookResult.empty()

    # Skip for casual/short responses where injection is noise
    casual = {"ok", "okay", "thanks", "yes", "no", "got it", "done", "continue", "go ahead", "proceed"}
    if stripped in casual:
        return HookResult.empty()

    # Skip for slash commands (skill invocations)
    if stripped.startswith("/"):
        return HookResult.empty()

    return HookResult(context=_INJECTION, tokens=len(_INJECTION) // 4, priority=2.0)
