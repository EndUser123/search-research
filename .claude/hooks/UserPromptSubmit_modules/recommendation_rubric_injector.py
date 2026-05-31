"""UserPromptSubmit hook: injects recommendation rubric reminder when recommendation prompt detected.

This hook is the UPS-side injector for the recommendation-rubric enforcement system.

Pattern:
  - is_recommendation_request(prompt)  <- from recommendation_intent
  - If True: inject reminder text via HookResult
  - If False: return HookResult.empty()

The companion Stop-side shadow (recommendation_compliance_recorder.py) observes
whether the response actually follows the rubric, but NEVER blocks.
"""

from __future__ import annotations

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Single source of truth for the injected reminder text.
# Kept here (not in recommendation_intent.py) so the injector stays self-contained.
_RECOMMENDATION_RUBRIC = (
    "Reminder: when recommending, name at least 2 viable options, the selection "
    "criterion, and why the chosen option wins on that axis. 'Optimal' is a claim "
    "about a comparison — show the comparison."
)


@register_hook("recommendation_rubric_injector", priority=5.0)
def recommendation_rubric_injector(context: HookContext) -> HookResult:
    """Inject recommendation rubric reminder when prompt asks for a recommendation."""
    # Local import to avoid circular dependency at module load time.
    from recommendation_intent import is_recommendation_request

    if is_recommendation_request(context.prompt):
        return HookResult(
            context=_RECOMMENDATION_RUBRIC,
            tokens=len(_RECOMMENDATION_RUBRIC.split()),
            priority=5.0,
        )
    return HookResult.empty()
