"""THINK Trigger — auto-detect reasoning profile injection.

Auto-detects reasoning profiles from keyword signals in user prompts.
Strong keywords (unambiguous) trigger on 1 match; weak keywords need 2+.
Code spans (`...`) are stripped before matching to avoid false positives.
Stemming patterns catch all word forms automatically.

Examples:
    "this keeps breaking in production, the test is flaky" -> debug_rca
    "should we use Redis or Memcached for caching?" -> tradeoff_decision
    "deploying the migration to prod tonight" -> pre_commit_risk
    "split into microservice or keep the monolith?" -> architecture

Profiles:
    debug_rca          -> 5-Whys root cause analysis
    tradeoff_decision  -> Tradeoff decision framework
    architecture       -> Architecture evaluation
    pre_commit_risk    -> Pre-commit risk assessment
"""
from __future__ import annotations

import re

from .base import HookContext, HookResult
from .registry import register_hook

# ---------------------------------------------------------------------------
# Keyword-based auto-detection (strong=1 match, weak=2+ matches)
# ---------------------------------------------------------------------------

# Regex to strip inline code spans before keyword matching
_CODE_SPAN_RE = re.compile(r"`[^`]+`")


def _stem(root: str, suffixes: str = "ed|ing|s|es") -> str:
    """Build a stemming regex pattern from a root word.

    _stem("crash") -> r"crash(?:ed|ing|s|es)?"
    _stem("fail", "ed|ing|s|ure|ures") -> r"fail(?:ed|ing|s|ure|ures)?"
    """
    return re.escape(root) + r"(?:" + suffixes + r")?"


# Strong keywords: unambiguous signals, 1 match is enough.
# Each entry is a raw regex pattern with word boundaries added at compile time.
_STRONG_PATTERNS: dict[str, list[str]] = {
    "debug_rca": [
        r"flaky",
        r"intermittent(?:ly)?",
        r"race condition",
        r"root cause",
        r"stack trace",
        r"traceback",
        _stem("regress", "ed|ing|ion|ions"),
        r"not working",
        r"stopped working",
        r"keeps? (?:happening|failing|crashing|breaking)",
        r"why (?:does|is|did|isn't|won't|can't|doesn't)",
    ],
    "tradeoff_decision": [
        r"option [ab]",
        r"pros and cons",
        r"pick between",
        r"which is better",
        r"should (?:we|i) use",
        r"trade-?off",
        r"versus",
        r"\bvs\b",
    ],
    "architecture": [
        r"microservices?",
        r"monolith(?:ic)?",
        r"service boundar(?:y|ies)",
        r"domain model",
        r"design pattern",
        r"system design",
        r"extract(?:ing)? (?:a )?service",
        r"separate? concerns?",
        _stem("decompos", "e|ed|ing|ition"),
        _stem("decoupl", "e|ed|ing"),
    ],
    "pre_commit_risk": [
        r"about to deploy",
        r"before (?:merging|pushing|shipping)",
        r"break(?:ing)? production",
        r"breaking changes?",
        r"push(?:ing)? to (?:main|master)",
        r"go(?:ing)? live",
        r"pre-merge",
        r"ship it",
        _stem("rollback", "ed|ing|s"),
    ],
}

# Weak keywords: ambiguous alone, need 2+ matches.
_WEAK_PATTERNS: dict[str, list[str]] = {
    "debug_rca": [
        _stem("bug", "s|gy"),
        _stem("break", "s|ing"),
        _stem("broke", "n|d"),
        _stem("crash", "ed|ing|es"),
        _stem("error", "s|ed"),
        _stem("exception", "s"),
        _stem("fail", "ed|ing|s|ure|ures"),
    ],
    "tradeoff_decision": [
        _stem("alternative", "s"),
        r"choos(?:e|ing)",
        _stem("compar", "e|ed|ing|ison"),
        _stem("decision", "s"),
        r"either",
        _stem("evaluat", "e|ed|ing|ion"),
        r"or should",
        r"which one",
        r"what approach",
        r"better approach",
    ],
    "architecture": [
        _stem("architect", "s|ure|ural"),
        r"boundar(?:y|ies)",
        _stem("component", "s"),
        _stem("coupl", "e|ed|ing"),
        _stem("layer", "s|ed|ing"),
        r"modular(?:ize|ization)?",
        r"refactor(?:ing)? into",
        _stem("restructur", "e|ed|ing"),
        r"split(?:ting)? into",
    ],
    "pre_commit_risk": [
        _stem("deploy", "ed|ing|s|ment|ments"),
        _stem("migrat", "e|ed|ing|ion|ions"),
        r"production",
        _stem("releas", "e|ed|ing|es"),
        r"risky",
        _stem("ship", "ped|ping|s"),
    ],
}

# Pre-compile all patterns with word boundaries
_COMPILED_STRONG: dict[str, list[re.Pattern]] = {}
_COMPILED_WEAK: dict[str, list[re.Pattern]] = {}

for _profile in _STRONG_PATTERNS:
    _COMPILED_STRONG[_profile] = [
        re.compile(r"\b(?:" + pat + r")\b", re.IGNORECASE)
        for pat in _STRONG_PATTERNS[_profile]
    ]
    _COMPILED_WEAK[_profile] = [
        re.compile(r"\b(?:" + pat + r")\b", re.IGNORECASE)
        for pat in _WEAK_PATTERNS.get(_profile, [])
    ]

# Backward-compat aliases for tests
_STRONG_KEYWORDS = _STRONG_PATTERNS
_WEAK_KEYWORDS = _WEAK_PATTERNS
_PROFILE_KEYWORDS: dict[str, list[str]] = {
    p: list(_STRONG_PATTERNS.get(p, [])) + list(_WEAK_PATTERNS.get(p, []))
    for p in set(list(_STRONG_PATTERNS) + list(_WEAK_PATTERNS))
}


def _detect_profile(prompt: str) -> str | None:
    """Auto-detect a reasoning profile from keyword signals.

    Strong keywords trigger on 1 match (unambiguous signals).
    Weak keywords need 2+ matches (ambiguous alone).
    Strips inline code (`...`) before matching.
    """
    # Strip code spans so `handle_error()` doesn't count as "error"
    prompt_clean = _CODE_SPAN_RE.sub("", prompt).lower()

    # Quick reject: very short prompts unlikely to contain signals
    if len(prompt_clean) < 10:
        return None

    best_profile: str | None = None
    best_score = 0

    for profile in _COMPILED_STRONG:
        strong_count = sum(1 for p in _COMPILED_STRONG[profile] if p.search(prompt_clean))
        weak_count = sum(1 for p in _COMPILED_WEAK.get(profile, []) if p.search(prompt_clean))

        # Strong keyword = instant trigger; weak keywords need 2+
        triggered = strong_count >= 1 or weak_count >= 2
        score = strong_count * 2 + weak_count  # weight strong higher for ranking

        if triggered and score > best_score:
            best_score = score
            best_profile = profile

    return best_profile


# ---------------------------------------------------------------------------
# Reasoning profile templates
# ---------------------------------------------------------------------------

_PROFILES: dict[str, str] = {
    "debug_rca": """\
THINK PROFILE: DEBUG / ROOT CAUSE ANALYSIS

Apply the 5 Whys:
1) Symptom — What failed? (observable behavior)
2) Why #1 — Immediate mechanism (the direct cause)
3) Why #2 — Upstream condition (what allowed #1)
4) Why #3 — Process/design gap (why #2 existed)
5) Why #4/#5 — Detection gap (why wasn't this caught earlier?)

Output discipline:
- Root cause candidate: explicitly [UNVERIFIED] until checked
- Evidence needed to confirm or refute
- Minimal fix + regression test target""",

    "tradeoff_decision": """\
THINK PROFILE: DECISION / TRADEOFF

Decision frame:
- Option A vs Option B (always include simplest fallback)
- Tradeoffs: speed, correctness, reversibility, maintenance cost
- Inversion: what would make each option fail?
- Recommendation with one counterargument
- Verification plan: what to measure/check after choosing""",

    "architecture": """\
THINK PROFILE: ARCHITECTURE

Architecture checks:
- Cynefin: is this clear, complicated, or complex?
- Chesterton's Fence: why does the current structure exist?
- Boundary/invariant impact of the proposed change
- Failure modes + rollback path
- Recommendation + strongest counterargument + verification plan""",

    "pre_commit_risk": """\
THINK PROFILE: PRE-COMMIT RISK

Pre-mortem: Assume this fails in 48 hours. What likely failed and why?

Immediate (0-30 min):
- Will this break existing functionality?
- Are there data migration issues?
- Any unintended side effects?

Short-term (1-3 days):
- Will this create technical debt?
- Dependency cascades?
- Will this need hotfixes?

Medium-term (1-4 weeks):
- Will this limit future flexibility?
- Does this need refactoring soon?

Reversibility check:
- Can git revert fix it?
- Any breaking interface changes?
- Can this ship incrementally?

If reversibility is low: consider a more conservative approach or document a rollback plan.""",
}


@register_hook("think_trigger", priority=6.0)
def think_trigger(context: HookContext) -> HookResult:
    """Inject reasoning framework via auto-detection."""
    profile = _detect_profile(context.prompt)

    if profile is None:
        return HookResult.empty()

    template = _PROFILES[profile]
    return HookResult(context=template, tokens=len(template) // 4, priority=6.0)
