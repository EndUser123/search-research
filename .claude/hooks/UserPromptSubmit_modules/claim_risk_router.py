"""Claim-risk routing tree for UserPromptSubmit.

This hook reduces reliance on user pushback by proactively classifying
high-friction prompts and injecting the evidence policy needed before the
model answers, while leaving deeper reasoning layers free to stack when the
prompt warrants it.
"""

from __future__ import annotations

import re

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook
from UserPromptSubmit_modules.unified_injector import classify_intent

_MIN_PROMPT_LENGTH = 30
_SKIP_RE = re.compile(
    r"^\s*/(?:commit|push|search|help|obs|timeline|quota|bgkill)\b",
    re.IGNORECASE,
)

_DISPUTED_CLAIM_RE = re.compile(
    r"\b("
    r"you\s+(?:missed|overlooked|ignored|forgot|removed|deleted|changed)|"
    r"did\s+you\s+just\s+remove\b|"
    r"without\s+(?:even\s+)?consider(?:ing|ation)\b|"
    r"that's\s+not\s+what\s+i\s+said|"
    r"that's\s+not\s+right|"
    r"you're\s+wrong|"
    r"why\s+are\s+we\s+depending\s+so\s+much\s+on\s+pushback\s+prompts|"
    r"the\s+system\s+able\s+to\s+identify\s+its\s+own\s+problems"
    r")\b",
    re.IGNORECASE,
)

_ROOT_CAUSE_RE = re.compile(
    r"\b("
    r"root\s+cause|"
    r"what\s+caused\b|"
    r"how\s+did\s+this\s+happen\b|"
    r"why\s+did\s+(?:this|that|it|we|the\s+system)\b|"
    r"why\s+are\s+we\s+depending\s+so\s+much\s+on\s+pushback\s+prompts|"
    r"failure\s+analysis|"
    r"identify\s+its\s+own\s+problems"
    r")\b",
    re.IGNORECASE,
)

_EXISTENCE_RE = re.compile(
    r"\b("
    r"does\s+.*\bexist\b|"
    r"is\s+there\s+(?:a|an|any)\b|"
    r"are\s+there\s+(?:any|some)\b|"
    r"missing\b|"
    r"absent\b|"
    r"doesn'?t\s+exist\b|"
    r"not\s+implemented\b"
    r")",
    re.IGNORECASE,
)

_IMPLEMENTATION_RE = re.compile(
    r"\b("
    r"implemented\b|"
    r"removed\b|"
    r"delete(?:d|s|ing)?\b|"
    r"replace(?:d|s|ing)?\b|"
    r"refactor(?:ed|s|ing)?\b|"
    r"call\s+sites?\b|"
    r"exports?\b|"
    r"compatibility\b"
    r")",
    re.IGNORECASE,
)

_COMPARISON_RE = re.compile(
    r"\b("
    r"compare\b|"
    r"better\b|"
    r"best\b|"
    r"worse\b|"
    r"which\s+(?:option|approach|path|choice)\b|"
    r"trade-?off\b|"
    r"versus\b|"
    r"\bvs\b"
    r")",
    re.IGNORECASE,
)


def _should_fire(prompt: str) -> bool:
    stripped = prompt.strip()
    if len(stripped) < _MIN_PROMPT_LENGTH:
        return False
    if _SKIP_RE.match(stripped):
        return False

    intent = classify_intent(stripped)
    if intent in {"CORRECTION", "DEBUG", "RESEARCH"}:
        return True

    return bool(
        _DISPUTED_CLAIM_RE.search(stripped)
        or _ROOT_CAUSE_RE.search(stripped)
        or _EXISTENCE_RE.search(stripped)
        or _IMPLEMENTATION_RE.search(stripped)
        or _COMPARISON_RE.search(stripped)
    )


def _build_injection(prompt: str) -> str:
    sections = [
        "**EVIDENCE-FIRST ROUTING TREE**",
        "1. Identify the claim type first: disputed claim, root cause, missing behavior, implementation status, or comparison/decision.",
        "2. Verify before concluding whenever the prompt depends on code state, runtime behavior, or whether something exists.",
        "3. Keep the answer short once the claim is verified.",
        "**MINIMAL OPERATING RULES**",
        "- Verify before claiming absence, breakage, or implementation state.",
        "- Be decisive once evidence is in hand; do not ask the user to pick the path for you.",
        "- Cite the file, symbol, or tool output that supports the claim.",
    ]

    if _DISPUTED_CLAIM_RE.search(prompt):
        sections.append(
            "Disputed-claim branch: treat this as an unverified challenge to a prior answer. "
            "Do not agree or disagree yet. Verify the contested fact with tools, and if the dispute concerns removed or missing functionality, search the actual call sites, exports, and references before saying it is absent."
        )

    if _ROOT_CAUSE_RE.search(prompt):
        sections.append(
            "Root-cause branch: do not stop at the first plausible explanation. "
            "Trace the mechanism, separate symptom from cause, and keep at least one alternative hypothesis alive until evidence rules it out."
        )

    if _EXISTENCE_RE.search(prompt):
        sections.append(
            "Existence branch: never claim something is missing or unimplemented until you have searched for it in the relevant files, symbols, or tests."
        )

    if _IMPLEMENTATION_RE.search(prompt):
        sections.append(
            "Implementation branch: search existing code first, preserve compatibility unless you confirm no callers depend on it, and explain any behavior change explicitly."
        )

    if _COMPARISON_RE.search(prompt):
        sections.append(
            "Comparison branch: compare at least two viable options against explicit criteria before recommending one."
        )

    return "\n\n".join(sections)


@register_hook("claim_risk_router", priority=7.5)
def claim_risk_router(context: HookContext) -> HookResult:
    prompt = context.prompt or ""
    if not _should_fire(prompt):
        return HookResult.empty()

    injection = _build_injection(prompt)
    suppress = [
        "operating_rules",
    ]
    if _DISPUTED_CLAIM_RE.search(prompt) and not _ROOT_CAUSE_RE.search(prompt):
        suppress.append("analysis_protocol_gate")
    return HookResult(
        context={
            "additionalContext": injection,
            "suppress": suppress,
        },
        tokens=len(injection) // 4,
        priority=10.0,
    )
