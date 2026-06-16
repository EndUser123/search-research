"""UserPromptSubmit hook: inject the pending recommendation-rubric correction (closed loop).

This is the injection side of the recommendation closed-loop system. The Stop side
(recommendation_loop.record_at_stop, dispatched from Stop.py) judges the previous turn with
an LLM and, if a genuine recommendation missed the rubric, persists a one-line correction to
a terminal-scoped state file. This hook reads + clears that correction next turn and injects
it as a specific, escalated reminder.

Design history: replaced the prior static regex-triggered reminder. A MiniMax-judged base
rate of 48% non-compliance (2026-06-01) showed the static reminder was not producing
compliant comparative recommendations; a specific post-hoc correction is the actual lift.
The baseline rubric remains always-on in CLAUDE.md ("Recommendation Rule").
"""

from __future__ import annotations

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook


@register_hook("recommendation_rubric_injector", priority=5.0)
def recommendation_rubric_injector(context: HookContext) -> HookResult:
    """Inject a pending rubric correction from the prior recommendation turn, if any."""
    # Local import keeps module load cheap and avoids import-time coupling.
    from UserPromptSubmit_modules.recommendation_loop import consume_pending_correction, scope_key

    # Scope the lookup to THIS conversation/terminal (payload session_id), so a correction
    # produced by one terminal can never be injected into another, and a prior session's
    # correction is never read by a new one (different key -> different file).
    correction = consume_pending_correction(scope_key(context.data))
    if correction:
        return HookResult(
            context=correction,
            tokens=len(correction.split()),
            priority=5.0,
        )
    return HookResult.empty()
