"""THINK Trigger — auto-detect reasoning profile injection.

Auto-detects reasoning profiles from keyword signals in user prompts.
Strong keywords (unambiguous) trigger on 1 match; weak keywords need 2+.
Code spans (`...`) are stripped before matching to avoid false positives.
Stemming patterns catch all word forms automatically.

Examples:
    "this keeps breaking in production, the test is flaky" -> debug_rca
    "should we use Redis or Memcached for caching?" -> tradeoff_decision
    "can you verify whether this is actually implemented?" -> evidence_audit
    "deploying the migration to prod tonight" -> pre_commit_risk
    "split into microservice or keep the monolith?" -> architecture

Profiles:
    debug_rca          -> 5-Whys root cause analysis
    tradeoff_decision  -> Tradeoff decision framework
    evidence_audit     -> Verification / proof check
    architecture       -> Architecture evaluation
    pre_commit_risk    -> Pre-commit risk assessment
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import re
from dataclasses import dataclass

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.reasoning_contract import (
    append_reasoning_contract,
    mark_reasoning_contract_applied,
)
from UserPromptSubmit_modules.registry import register_hook
from UserPromptSubmit_modules.unified_detection import (
    UnifiedDetectionResult,
    ensure_unified_detection_result,
)

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
_THINK_PREFIX_RE = re.compile(
    r"^\s*THINK(?:\s+(?P<alias>[A-Z][A-Z0-9_-]*))?(?:\s*:\s*|\s+)?(?P<remainder>.*)$",
    re.IGNORECASE,
)

def _stem(root: str, suffixes: str = "ed|ing|s|es") -> str:
    """Build a stemming regex pattern from a root word.

    _stem("crash") -> r"crash(?:ed|ing|s|es)?"
    _stem("fail", "ed|ing|s|ure|ures") -> r"fail(?:ed|ing|s|ure|ures)?"
    """
    return re.escape(root) + r"(?:" + suffixes + r")?"

# Self-referential prompt patterns: questions about the model's own reasoning/decisions.
# These should NOT trigger debug_rca — the model knows its own mind, it's not an external bug.
_SELF_REFERENTIAL_PROMPT_RE = re.compile(
    r"(?i)^\s*(?:"
    r"why\s+(?:did\s+you|does\s+(?:the\s+)?model|is|did|are|do)\s+|"
    r"what\s+(?:did\s+you|does\s+(?:the\s+)?model|did)\s+|"
    r"how\s+(?:did\s+you|does\s+(?:the\s+)?model)\s+|"
    r"explain\s+your\s+|"
    r"(?:are\s+you\s+)?sure\s+(?:why|that\s+I|what\s+I)|"
    r"(?:are\s+you\s+)?certain\s+(?:why|that\s+I)|"
    r"did\s+you\s+(?:know|understand|realize|mean)\s+|"
    r"can\s+you\s+explain\s+your\s+"
    r")",
    re.MULTILINE,
)

# Meta-prompts about the /think mechanism itself, rather than the user's substantive topic.
# These should fall back to quick triage instead of being reinterpreted as debugging or RCA.
_META_THINK_CONTEXT_RE = re.compile(
    r"(?i)\b(?:subject|topic|context|command|tool|skill|mechanism|invocation|target|prompt|mode|reasoning)\b"
)
_META_THINK_DIRECT_RE = re.compile(
    r"(?i)\b(?:why|what|how|when|where|should|did|does|is|are|can|would)\b.*?/think\b|/think\b.*?\b(?:why|what|how|when|where|should|did|does|is|are|can|would)\b"
)
_THINK_COMMAND_MENTION_RE = re.compile(r"(?i)(?:^|[\s`'\"(])/(?:think)\b")

def _is_self_referential_prompt(prompt: str) -> bool:
    """Detect prompts that ask the model to explain its own prior decisions/reasoning.

    These are not external investigations — the model has direct access to its own
    reasoning chain. Applying debug_rca's [UNVERIFIED] framing to self-knowledge is
    epistemically wrong and produces the verbose hedging observed in the transcript.
    """
    return bool(_SELF_REFERENTIAL_PROMPT_RE.search(prompt))

def _is_meta_think_prompt(prompt: str) -> bool:
    """Detect prompts that are about the /think mechanism instead of the real subject.

    The goal is to keep `/think` focused on the user's substantive question while
    still allowing explicit `/think ...` commands to resolve normally.
    """
    prompt_clean = _CODE_SPAN_RE.sub("", prompt)
    if not _THINK_COMMAND_MENTION_RE.search(prompt_clean):
        return False

    if _META_THINK_DIRECT_RE.search(prompt_clean):
        return True

    return bool(_META_THINK_CONTEXT_RE.search(prompt_clean))

# Strong keywords: unambiguous signals, 1 match is enough.
# Each entry is a raw regex pattern with word boundaries added at compile time.
_PROFILE_DEFINITIONS: dict[str, ThinkProfile] = {
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
    "evidence_audit": ThinkProfile(
        name="evidence_audit",
        template="""\
THINK PROFILE: EVIDENCE AUDIT

Evidence-first check:
- Identify the exact claim to verify.
- Separate proof, counterexample, and remaining uncertainty.
- Check the smallest relevant source of truth: code, tests, docs, or runtime output.
- State verdict: verified, refuted, or still uncertain.
- Name the evidence that would change the answer.""",
        strong_patterns=[
            r"verify(?:\s+(?:this|that|whether))?",
            r"prove(?:\s+(?:this|that|it))?",
            r"fact[- ]?check(?:ing)?",
            r"cross[- ]?check(?:ing)?",
            r"double[- ]?check(?:ing)?",
            r"is this actually",
            r"can you confirm",
            r"confirm(?:\s+(?:this|that|whether))?",
            r"validate(?:\s+(?:this|that|whether))?",
        ],
        weak_patterns=[
            r"\bcheck(?:ing)?\b",
            r"\bverified\b",
            r"\bproof\b",
            r"\bevidence\b",
            r"\baccurate\b",
            r"\btrue\b",
            r"\breally\b",
            r"\bactually\b",
        ],
    ),
    "tradeoff_decision": ThinkProfile(
        name="tradeoff_decision",
        template="""\
THINK PROFILE: DECISION / TRADEOFF (LIGHT PRECHECK)

Use this for a quick comparison, not the full decision-tree scaffold.

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
    "explicit_think": ThinkProfile(
        name="explicit_think",
        template="",  # Unused — detection is special-cased in _detect_profile
        strong_patterns=[],
        weak_patterns=None,
    ),
    "quick": ThinkProfile(
        name="quick",
        template="""\
THINK PROFILE: QUICK TRIAGE

Use this for an explicit but lightweight THINK prompt.

1. Restate the problem in one sentence
2. Identify the smallest safe next step
3. Ask at most one clarifying question if needed""",
        strong_patterns=[],
        weak_patterns=[],
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

# Backward-compat alias for older tests/imports.
_THINK_PROFILES = _PROFILE_DEFINITIONS

_PROFILE_ALIASES: dict[str, str] = {
    "verify": "evidence_audit",
    "audit": "evidence_audit",
    "prove": "evidence_audit",
    "confirm": "evidence_audit",
    "validate": "evidence_audit",
    "quick": "quick",
    "why": "debug_rca",
    "debug": "debug_rca",
    "rca": "debug_rca",
    "decide": "tradeoff_decision",
    "decision": "tradeoff_decision",
    "tradeoff": "tradeoff_decision",
    "arch": "architecture",
    "architecture": "architecture",
    "risk": "pre_commit_risk",
    "premortem": "pre_commit_risk",
}

# ---------------------------------------------------------------------------
# Derived dictionaries (backward compatibility)
# ---------------------------------------------------------------------------

# Extract pattern dictionaries from dataclass definitions for backward compat
_STRONG_PATTERNS: dict[str, list[str]] = {
    name: profile.strong_patterns for name, profile in _PROFILE_DEFINITIONS.items()
}

_WEAK_PATTERNS: dict[str, list[str]] = {
    name: (profile.weak_patterns or []) for name, profile in _PROFILE_DEFINITIONS.items()
}

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
__all__ = [
    "ThinkProfile",
    "_PROFILE_DEFINITIONS",
    "_THINK_PROFILES",
    "_PROFILES",
    "_STRONG_PATTERNS",
    "_WEAK_PATTERNS",
]

def _detect_profile(
    prompt: str,
    *,
    unified_result: UnifiedDetectionResult | None = None,
) -> str | None:
    """Auto-detect a reasoning profile from keyword signals.

    Strong keywords trigger on 1 match (unambiguous signals).
    Weak keywords need 2+ matches (ambiguous alone).
    Strips inline code (`...`) before matching.
    """
    explicit_profile, _ = _parse_think(prompt)
    if explicit_profile is not None:
        return explicit_profile

    # Uppercase THINK keyword — intentional explicit reasoning request (case-sensitive)
    if re.search(r"\bTHINK\b", prompt):
        return "explicit_think"

    shared_profile = _select_profile_from_unified_result(unified_result)
    if shared_profile is not None:
        return shared_profile

    # Self-referential prompt guard: questions about the model's own prior decisions
    # should NOT trigger debug_rca (which forces [UNVERIFIED] labeling on self-knowledge).
    # The model knows its own reasoning — it is not an external phenomenon requiring 5-Whys.
    if _is_self_referential_prompt(prompt):
        return "quick"

    # Meta prompts about the /think mechanism itself should not be reinterpreted as
    # debugging or root-cause analysis of the command name.
    if _is_meta_think_prompt(prompt):
        return "quick"

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

5 Whys: symptom -> mechanism -> upstream condition -> process gap -> detection gap.
State the root-cause candidate as [UNVERIFIED], list evidence needed, and end with a minimal fix + regression test.""",
    "evidence_audit": """\
THINK PROFILE: EVIDENCE AUDIT

Treat the claim as provisional. Verify against the smallest relevant source of truth, separate proof from uncertainty, state whether it is verified, refuted, or still uncertain, and return the evidence that would change it.""",
    "tradeoff_decision": """\
THINK PROFILE: DECISION / TRADEOFF (LIGHT PRECHECK)

Use this for a quick comparison, not the full decision-tree scaffold.

Compare 2 options plus the simplest fallback. State tradeoffs, one failure mode, your recommendation, and how to verify it.""",
    "architecture": """\
THINK PROFILE: ARCHITECTURE

Check the domain, preserve existing boundaries, name failure modes and rollback, then recommend one path with a counterargument.""",
    "pre_commit_risk": """\
THINK PROFILE: PRE-COMMIT RISK

Assume this fails in 48 hours. Check breakage, migration risk, side effects, hotfix risk, and reversibility before shipping.""",
    "security_review": """\
THINK PROFILE: SECURITY REVIEW

Model assets, adversaries, and attack paths. Check the obvious OWASP risks, then verify with review, static analysis, and dependency scanning.""",
    "performance_analysis": """\
THINK PROFILE: PERFORMANCE ANALYSIS

Identify the slow symptom, measure the bottleneck, test likely causes, and verify the fix with before/after metrics.""",
    "multi_file_refactor": """\
THINK PROFILE: MULTI-FILE REFACTOR

Map the change, find all references, update definition and callers in order, test each step, and keep a rollback path.""",
    "explicit_think": """\
THINK PROFILE: DELIBERATE REASONING

Explicit reasoning mode (THINK keyword detected).

1. Restate the problem in one sentence
2. Consider at least 2 plausible approaches internally; do not stop at the first plausible answer
3. Surface key assumptions — mark each [ASSUMED] or [VERIFIED]
4. Recommend one path and name the main alternative you rejected
5. State what evidence would change the answer""",
    "quick": """\
THINK PROFILE: QUICK TRIAGE

Use this for an explicit but lightweight THINK prompt.

1. Restate the problem in one sentence
2. Identify the smallest safe next step
3. Ask at most one clarifying question if needed""",
}

def _parse_think(prompt: str) -> tuple[str | None, str]:
    """Parse explicit THINK-style prompts into a profile and remainder."""
    stripped = prompt.strip()
    if not stripped:
        return None, ""

    match = _THINK_PREFIX_RE.match(stripped)
    if not match:
        return None, prompt

    alias = (match.group("alias") or "").lower()
    remainder = (match.group("remainder") or "").strip()

    if not alias:
        return "quick", remainder

    profile = _PROFILE_ALIASES.get(alias)
    if profile is None:
        return "quick", remainder
    return profile, remainder

def _select_profile_from_unified_result(
    unified_result: UnifiedDetectionResult | None,
) -> str | None:
    """Select the first think profile reported by unified detection."""
    if unified_result is None:
        return None

    for profile in unified_result.matched_profiles:
        if profile in _PROFILES:
            return profile

    return None

def _build_think_alignment_block(
    profile: str,
    unified_result: UnifiedDetectionResult | None,
) -> str:
    """Prepend the /think-specific reasoning contract overlay."""
    shared_parts: list[str] = []
    if unified_result is not None:
        if unified_result.intent_classification:
            shared_parts.append(f"intent={unified_result.intent_classification}")
        if unified_result.matched_modes:
            shared_parts.append(
                "modes=" + ", ".join(unified_result.matched_modes[:3])
            )
        if unified_result.matched_profiles:
            shared_parts.append(
                "profiles=" + ", ".join(unified_result.matched_profiles[:3])
            )

    lines = [
        "THINK ALIGNMENT:",
        "- Infer the subject from the user's actual request and surrounding conversation; the /think command only selects a reasoning mode.",
        "- Label material claims as Verified / Inferred / Unproven.",
        "- If the answer depends on repo state, tests, or runtime behavior, keep it Unproven until checked.",
        "- Name the primary reasoning frame and the fallback frame when more than one applies.",
        "- Chain frames only when the second frame changes the answer; otherwise stay with one frame.",
        "- State the smallest discriminating check that would resolve remaining uncertainty.",
        f"- Active frame: {profile}.",
    ]
    if shared_parts:
        lines.append("- Shared detection: " + "; ".join(shared_parts) + ".")

    return "\n".join(lines)

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
    unified_result = ensure_unified_detection_result(context)
    profile = _detect_profile(context.prompt, unified_result=unified_result)

    if profile is None:
        return HookResult.empty()

    alignment_block = _build_think_alignment_block(profile, unified_result)
    template = append_reasoning_contract(
        f"[THINK:{profile}]\n\n{alignment_block}\n\n{_PROFILES[profile]}",
        include_verification=True,
        include_counterexample=True,
        include_discovery=True,
        include_rollback=True,
        include_evidence=True,
    )
    mark_reasoning_contract_applied(context, "think_trigger")
    suppression = [
        "operating_rules",
    ]
    return HookResult(
        context={
            "additionalContext": template,
            "suppress": suppression,
        },
        tokens=len(template) // 4,
        priority=6.0,
    )