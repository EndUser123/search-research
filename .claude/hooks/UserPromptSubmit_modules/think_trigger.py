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
from dataclasses import dataclass

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# ---------------------------------------------------------------------------
# Single-source profile definition (dataclass pattern)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ThinkProfile:
    """Single-source definition for a reasoning profile.

    This dataclass co-locates all profile data to prevent the bug class where
    pattern definitions and template definitions drift apart (see KeyError: 'security_review').

    The frozen=True modifier makes instances immutable, preventing accidental mutation
    and ensuring thread-safety for the compiled pattern cache.
    """

    name: str
    """Profile identifier (e.g., "debug_rca")."""

    template: str
    """Reasoning framework template to inject on match."""

    strong_patterns: list[str]
    """Unambiguous keyword patterns (1 match triggers)."""

    weak_patterns: list[str] | None
    """Ambiguous keyword patterns (2+ matches trigger), or None if not applicable."""


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
_THINK_PROFILES: dict[str, ThinkProfile] = {
    "debug_rca": ThinkProfile(
        name="debug_rca",
        template="""\
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
        strong_patterns=[
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
        weak_patterns=[
            _stem("bug", "s|gy"),
            _stem("break", "s|ing"),
            _stem("broke", "n|d"),
            _stem("crash", "ed|ing|es"),
            _stem("error", "s|ed"),
            _stem("exception", "s"),
            _stem("fail", "ed|ing|s|ure|ures"),
        ],
    ),
    "tradeoff_decision": ThinkProfile(
        name="tradeoff_decision",
        template="""\
THINK PROFILE: DECISION / TRADEOFF

Decision frame:
- Option A vs Option B (always include simplest fallback)
- Tradeoffs: speed, correctness, reversibility, maintenance cost
- Inversion: what would make each option fail?
- Recommendation with one counterargument
- Verification plan: what to measure/check after choosing""",
        strong_patterns=[
            r"option [ab]",
            r"pros and cons",
            r"pick between",
            r"which is better",
            r"should (?:we|i) use",
            r"trade-?off",
            r"versus",
            r"\bvs\b",
        ],
        weak_patterns=[
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
    ),
    "architecture": ThinkProfile(
        name="architecture",
        template="""\
THINK PROFILE: ARCHITECTURE

Architecture checks:
- Cynefin: is this clear, complicated, or complex?
- Chesterton's Fence: why does the current structure exist?
- Boundary/invariant impact of the proposed change
- Failure modes + rollback path
- Recommendation + strongest counterargument + verification plan""",
        strong_patterns=[
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
        weak_patterns=[
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
    ),
    "pre_commit_risk": ThinkProfile(
        name="pre_commit_risk",
        template="""\
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
        strong_patterns=[
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
        weak_patterns=[
            _stem("deploy", "ed|ing|s|ment|ments"),
            _stem("migrat", "e|ed|ing|ion|ions"),
            r"production",
            _stem("releas", "e|ed|ing|es"),
            r"risky",
            _stem("ship", "ped|ping|s"),
        ],
    ),
    "security_review": ThinkProfile(
        name="security_review",
        template="""\
THINK PROFILE: SECURITY REVIEW

Security threat modeling:
- What assets are being protected? (data, credentials, access)
- Who are the adversaries? (unauthenticated users, privileged insiders, external attackers)
- What are the attack vectors? (injection, XSS, CSRF, auth bypass, data exposure)

OWASP Top 10 checks:
- Injection (SQL, NoSQL, OS command, LDAP)
- Broken authentication (session management, credential handling)
- Sensitive data exposure (encryption at rest/transit)
- XML external entities (XXE)
- Broken access control (horizontal/vertical privilege escalation)
- Security misconfiguration (default keys, verbose error messages)
- Cross-site scripting (XSS)
- Insecure deserialization
- Using components with known vulnerabilities
- Insufficient logging & monitoring

Verification:
- Manual threat modeling review
- Static analysis for security patterns
- Dependency vulnerability scan""",
        strong_patterns=[
            r"SQL injection",
            r"XSS",
            r"cross-site",
            r"CSRF",
            r"auth(?:entication|orization)\s+(?:bug|issue|flaw|bypass|vuln)",
            r"secret(?:s)?\s+(?:leak|expos|hardcod)",
            r"OWASP",
            r"CVE-\d+",
            r"privilege\s+escalation",
            r"injection\s+(?:attack|vuln)",
        ],
        weak_patterns=[
            r"auth(?:entication|orization)?",
            r"(?:input\s+)?(?:validat|sanitiz)",
            r"encrypt",
            r"hash(?:ing)?",
            r"token",
            r"permission",
            _stem("vulnerab", "le|ility|ilities"),
            r"security",
            r"(?:data\s+)?exposure",
        ],
    ),
    "performance_analysis": ThinkProfile(
        name="performance_analysis",
        template="""\
THINK PROFILE: PERFORMANCE ANALYSIS

Performance investigation:
1) Symptom — What's slow? (endpoint, query, operation)
2) Baseline — What's expected? (previous performance, SLA)
3) Measurement — Quantify the bottleneck (CPU, memory, I/O, network)
4) Root cause — Algorithmic complexity, N+1 queries, lock contention, missing index?
5) Hypothesis — What will improve it? (caching, indexing, query optimization)
6) Verification — Measure after fix, confirm improvement

Common bottlenecks:
- Algorithmic: O(n²) where O(n) possible
- Database: Missing indexes, N+1 queries, full table scans
- I/O: Synchronous operations, excessive network calls
- Memory: Leaks, large object allocations, inefficient data structures
- Concurrency: Lock contention, thread pool exhaustion, blocking calls

Big-O analysis:
- Current complexity: ?
- Target complexity: ?
- Can we use a more efficient data structure or algorithm?""",
        strong_patterns=[
            r"(?:is|runs?|seems?)\s+(?:really\s+)?slow",
            r"latency\s+(?:spike|issue|problem)",
            r"throughput\s+(?:drop|issue|problem)",
            r"memory\s+leak",
            r"O\(n[²2³3]\)",
            r"big-?O",
            r"bottleneck",
            r"(?:CPU|memory|disk)\s+(?:usage|bound|intensive)",
            r"load\s+test",
        ],
        weak_patterns=[
            _stem("optimiz", "e|ed|ing|ation|ations"),
            r"profil(?:e|ing)",
            r"cach(?:e|ing)",
            r"slow\s+query",
            r"(?:query|database)\s+(?:slow|performance|optimization)",
            _stem("benchmark", "s|ing|ed"),
            r"(?:time|space)\s+complexity",
            r"N\+1",
            r"lazy\s+load",
        ],
    ),
    "multi_file_refactor": ThinkProfile(
        name="multi_file_refactor",
        template="""\
THINK PROFILE: MULTI-FILE REFACTOR

Refactoring strategy:
1) Scope — What's changing? (class name, function signature, directory structure)
2) Impact analysis — Which files are affected? (use ripgrep/grep to find all references)
3) Order of operations — What's the dependency chain? (avoid breaking intermediate state)
4) Testing strategy — How to verify each step? (unit tests, integration tests, manual smoke test)
5) Rollback plan — What if something breaks? (git revert, revert individual files)

Execution checklist:
- Identify all files that reference the changed symbol
- Update the definition first (if signature changed)
- Update all callers
- Run tests at each step
- Verify no remaining references to old symbol
- Update documentation

Common pitfalls:
- Missing references (greedy search patterns)
- Breaking intermediate state (partial updates)
- Forgetting test files
- Forgetting documentation
- Assuming all references are in one language (check config files, templates, etc.)""",
        strong_patterns=[
            r"refactor(?:\s+\w+){0,2}\s+across\s+(?:multiple|several|all)\s+files",
            r"rename\s+(?:across|everywhere|globally)",
            r"extract\s+(?:into|to)\s+(?:a\s+)?(?:new\s+)?(?:module|package|file|class)",
            r"split\s+(?:into|this into)\s+(?:multiple|separate)",
            r"move\s+(?:all|every)\s+",
            r"restructure\s+(?:the\s+)?(?:module|package|directory|project)",
            r"restructure\s+across\s+(?:the\s+)?codebase",
        ],
        weak_patterns=[
            _stem("refactor", "s|ed|ing"),
            r"(?:re)?structur",
            r"reorganiz",
            _stem("consolidat", "e|ed|ing|ion"),
            r"(?:break|split)\s+(?:up|out|apart)",
            r"modulariz",
            r"(?:merge|combine)\s+(?:into|files)",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Derived dictionaries (backward compatibility)
# ---------------------------------------------------------------------------


# Extract pattern dictionaries from dataclass for backward compat
_STRONG_PATTERNS: dict[str, list[str]] = {
    name: profile.strong_patterns for name, profile in _THINK_PROFILES.items()
}

_WEAK_PATTERNS: dict[str, list[str]] = {
    name: (profile.weak_patterns or []) for name, profile in _THINK_PROFILES.items()
}

# Extract templates for backward compat
_PROFILES: dict[str, str] = {name: profile.template for name, profile in _THINK_PROFILES.items()}

# Pre-compile all patterns with word boundaries
_COMPILED_STRONG: dict[str, list[re.Pattern]] = {}
_COMPILED_WEAK: dict[str, list[re.Pattern]] = {}


for _profile in _STRONG_PATTERNS:
    _COMPILED_STRONG[_profile] = [
        re.compile(r"\b(?:" + pat + r")\b", re.IGNORECASE) for pat in _STRONG_PATTERNS[_profile]
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

# Export ThinkProfile for testing and type annotations
__all__ = ["ThinkProfile", "_THINK_PROFILES", "_PROFILES", "_STRONG_PATTERNS", "_WEAK_PATTERNS"]


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
    "security_review": """\
THINK PROFILE: SECURITY REVIEW

Security threat modeling:
- What assets are being protected? (data, credentials, access)
- Who are the adversaries? (unauthenticated users, privileged insiders, external attackers)
- What are the attack vectors? (injection, XSS, CSRF, auth bypass, data exposure)

OWASP Top 10 checks:
- Injection (SQL, NoSQL, OS command, LDAP)
- Broken authentication (session management, credential handling)
- Sensitive data exposure (encryption at rest/transit)
- XML external entities (XXE)
- Broken access control (horizontal/vertical privilege escalation)
- Security misconfiguration (default keys, verbose error messages)
- Cross-site scripting (XSS)
- Insecure deserialization
- Using components with known vulnerabilities
- Insufficient logging & monitoring

Verification:
- Manual threat modeling review
- Static analysis for security patterns
- Dependency vulnerability scan""",
    "performance_analysis": """\
THINK PROFILE: PERFORMANCE ANALYSIS

Performance investigation:
1) Symptom — What's slow? (endpoint, query, operation)
2) Baseline — What's expected? (previous performance, SLA)
3) Measurement — Quantify the bottleneck (CPU, memory, I/O, network)
4) Root cause — Algorithmic complexity, N+1 queries, lock contention, missing index?
5) Hypothesis — What will improve it? (caching, indexing, query optimization)
6) Verification — Measure after fix, confirm improvement

Common bottlenecks:
- Algorithmic: O(n²) where O(n) possible
- Database: Missing indexes, N+1 queries, full table scans
- I/O: Synchronous operations, excessive network calls
- Memory: Leaks, large object allocations, inefficient data structures
- Concurrency: Lock contention, thread pool exhaustion, blocking calls

Big-O analysis:
- Current complexity: ?
- Target complexity: ?
- Can we use a more efficient data structure or algorithm?""",
    "multi_file_refactor": """\
THINK PROFILE: MULTI-FILE REFACTOR

Refactoring strategy:
1) Scope — What's changing? (class name, function signature, directory structure)
2) Impact analysis — Which files are affected? (use ripgrep/grep to find all references)
3) Order of operations — What's the dependency chain? (avoid breaking intermediate state)
4) Testing strategy — How to verify each step? (unit tests, integration tests, manual smoke test)
5) Rollback plan — What if something breaks? (git revert, revert individual files)

Execution checklist:
- Identify all files that reference the changed symbol
- Update the definition first (if signature changed)
- Update all callers
- Run tests at each step
- Verify no remaining references to old symbol
- Update documentation

Common pitfalls:
- Missing references (greedy search patterns)
- Breaking intermediate state (partial updates)
- Forgetting test files
- Forgetting documentation
- Assuming all references are in one language (check config files, templates, etc.)""",
}

# Module-level invariant check (runs on import)
if __debug__:  # Only runs in dev/test, optimized out in production
    missing_templates = set(_COMPILED_STRONG.keys()) - set(_PROFILES.keys())
    missing_patterns = set(_PROFILES.keys()) - set(_COMPILED_STRONG.keys())

    if missing_templates or missing_patterns:
        raise AssertionError(
            f"Profile configuration mismatch in think_trigger.py:\n"
            f"  Missing templates: {missing_templates}\n"
            f"  Missing patterns: {missing_patterns}\n"
            f"  _PROFILES has {len(_PROFILES)} profiles, _COMPILED_STRONG has {len(_COMPILED_STRONG)}"
        )


@register_hook("think_trigger", priority=6.0)
def think_trigger(context: HookContext) -> HookResult:
    """Inject reasoning framework via auto-detection."""
    profile = _detect_profile(context.prompt)

    if profile is None:
        return HookResult.empty()

    template = f"[THINK:{profile}]\n\n" + _PROFILES[profile]
    return HookResult(context=template, tokens=len(template) // 4, priority=6.0)
