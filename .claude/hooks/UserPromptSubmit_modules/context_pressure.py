"""Bounded prompt/context pressure advisory for UserPromptSubmit.

This is deliberately an estimate. Claude Code's authoritative context usage is
available to the status line, not to UserPromptSubmit. The hook warns about
large inputs and accumulated transcript size; it never rewrites the prompt.
"""

from __future__ import annotations

import os
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

PROMPT_WARNING_CHARS = int(os.environ.get("CONTEXT_PROMPT_WARNING_CHARS", "12000"))
TRANSCRIPT_WARNING_TOKENS = int(
    os.environ.get("CONTEXT_TRANSCRIPT_WARNING_TOKENS", "60000")
)
CHARS_PER_TOKEN_ESTIMATE = 4


def _estimate_transcript_tokens(transcript_path: str | None) -> int:
    if not transcript_path:
        return 0
    try:
        return Path(transcript_path).stat().st_size // CHARS_PER_TOKEN_ESTIMATE
    except (OSError, ValueError):
        return 0


@register_hook("context_pressure", priority=1.5)
def context_pressure_hook(context: HookContext) -> HookResult:
    """Warn only when the current input or accumulated transcript is large."""
    if os.environ.get("CONTEXT_PRESSURE_WARNING_ENABLED", "true").lower() not in {
        "1",
        "true",
        "yes",
    }:
        return HookResult.empty()

    prompt_chars = len(context.prompt or "")
    transcript_tokens = _estimate_transcript_tokens(
        context.data.get("transcript_path")
    )
    reasons: list[str] = []
    if prompt_chars >= PROMPT_WARNING_CHARS:
        reasons.append(f"current prompt is ~{prompt_chars:,} characters")
    if transcript_tokens >= TRANSCRIPT_WARNING_TOKENS:
        reasons.append(f"transcript is ~{transcript_tokens:,} tokens on disk")
    if not reasons:
        return HookResult.empty()

    return HookResult(
        context=(
            "[CONTEXT PRESSURE] "
            + "; ".join(reasons)
            + ". Preserve the goal, decisions, active files, blockers, and next "
            "step; consider /compact before starting another large phase."
        ),
        tokens=45,
        priority=1.5,
    )
