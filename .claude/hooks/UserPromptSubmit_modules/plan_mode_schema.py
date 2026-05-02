"""Plan mode schema injector.

Detects planning-style prompts and injects [PLAN]/[RATIONALE] schema guidance,
preventing epistemic 4-section format from being enforced on planning turns.
"""

from __future__ import annotations

import re

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

_PLANNING_PROMPT_RE = re.compile(
    r"(?i)"
    r"(?:what(?:'s| is) (?:the )?next|next steps?|what should we|"
    r"prioritized? list|plan for|roadmap|action items|what to work on|"
    r"what are the next|top \d+ (?:things|tasks|items|priorities)|"
    r"give me \d+|what \d+ things|recommend \d+|list \d+)"
)

_PLAN_SCHEMA = (
    "PLAN MODE: Use this schema for your response:\n"
    "[PLAN]\n"
    "1. ...\n"
    "2. ...\n"
    "[RATIONALE]\n"
    "- ...\n"
    "Do NOT use [FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION] sections."
)


@register_hook("plan_mode_schema", priority=4.0)
def plan_mode_schema(context: HookContext) -> HookResult:
    """Inject [PLAN]/[RATIONALE] schema for planning-style prompts."""
    prompt = context.prompt or ""
    if not prompt or not _PLANNING_PROMPT_RE.search(prompt):
        return HookResult.empty()
    return HookResult(context=_PLAN_SCHEMA)
