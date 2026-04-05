r"""Questioning pattern integration for cognitive & reasoning systems.

Loads meta-cognitive questioning patterns from memory and matches them against
user prompts to detect potential reasoning flaws before implementation.

Patterns from: C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md

Patterns detected:
1. "Why this specific value?" - Arbitrary threshold detection
2. "Are you sure about concurrency?" - Shared state detection
3. "Is this necessary?" - Over-engineering detection
4. "What happens at scale?" - Swiss cheese maintenance detection
5. "What does the error actually say?" - Debugging cognition (H1/H2/H3)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass(frozen=True)
class QuestioningPattern:
    """A questioning pattern for meta-cognitive bug detection.

    Attributes:
        name: Pattern identifier (e.g., "arbitrary_threshold")
        question: The core question to ask (e.g., "Why this specific value?")
        description: What flaw this pattern detects
        triggers: List of regex patterns that trigger this question
        reference: Line reference in questioning_patterns.md
    """

    name: str
    question: str
    description: str
    triggers: list[str]
    reference: str


@dataclass(frozen=True)
class DebuggingHeuristic:
    """A debugging cognition heuristic from Pattern 5.

    Attributes:
        code: H1, H2, or H3
        name: Heuristic name (e.g., "Entry Point First Rule")
        description: What the heuristic checks for
        triggers: List of regex patterns that indicate this should be applied
    """

    code: str  # H1, H2, or H3
    name: str
    description: str
    triggers: list[str]


@dataclass(frozen=True)
class QuestioningMatch:
    """Result from questioning pattern detection.

    Attributes:
        patterns: List of questioning pattern names matched
        debugging_heuristics: List of debugging heuristic codes matched (H1/H2/H3)
        triggers: Dictionary mapping pattern names to triggering text
        reference: Path to questioning_patterns.md for context
    """

    patterns: list[str] = field(default_factory=list)
    debugging_heuristics: list[str] = field(default_factory=list)
    triggers: dict[str, str] = field(default_factory=dict)
    reference: str = r"C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md"


# =============================================================================
# QUESTIONING PATTERNS (5 total)
# =============================================================================#

_QUESTIONING_PATTERNS: list[QuestioningPattern] = [
    QuestioningPattern(
        name="arbitrary_threshold",
        question="Why this specific value?",
        description="Detects arbitrary thresholds, timeouts, and magic numbers without empirical basis",
        triggers=[
            r"\b\d+\s*(?:second|minute|hour|day|week|month)s?\b",
            r"\btimeout\b",
            r"\bretry\b",
            r"\bmax\b",
            r"\bthreshold\b",
            r"\blimit\b",
            r"\bttl\b",
            r"\bcache\s+expiry\b",
            r"\bexpires?\b",
            r"\bwait\b",
            r"\bMax\b",
            r"\bThreshold\b",
            r"\bLimit\b",
            r"\bTTL\b",
        ],
        reference="Line 17-34: Pattern 1 - Arbitrary Threshold Detection",
    ),
    QuestioningPattern(
        name="shared_state_concurrency",
        question="Are you sure about concurrency?",
        description="Detects shared state (git, files, databases) that may have race conditions in multi-terminal environments",
        triggers=[
            r"\bgit\s+(?:status|log|diff)\b",
            r"\bfile\s+mtime\b",
            r"\blast\s+modified\b",
            r"\bshared\s+state\b",
            r"\bglobal\s+(?:variable|state|config)\b",
            r"\bcentralized?\s+(?:cache|state|database)\b",
            r"\brace\s+condition\b",
            r"\bconcurrent\s+(?:access|write|read)\b",
            r"\bmulti.?terminal\b",
            r"\bsession\s+isolation\b",
        ],
        reference="Line 38-57: Pattern 2 - Shared State Detection",
    ),
    QuestioningPattern(
        name="over_engineering",
        question="Is this necessary?",
        description="Detects over-engineering with nice-to-have features vs. critical fixes",
        triggers=[
            r"\bdashboard\b",
            r"\bsurvey\b",
            r"\banalytics\b",
            r"\bmetrics?\b",
            r"\breport\b",
            r"\bgenerate\b",
            r"\bcreate\s+separate\b",
            r"\bcreate\s+individual\b",
            r"\bcreate\s+multiple\b",
            r"\bseparate\s+\w+\s+handlers?\b",
            r"\bindividual\s+processors?\b",
            r"\bdedicated\s+manager\b",
            r"\babstract\s+(?:layer|factory|builder)\b",
            r"\bimplement\s+(?:logging|monitoring|observability)\b",
            r"\bconsolidat(?:e|ion)\b",
            r"\brefactor\s+multiple\b",
            r"\bsplit\s+into\s+multiple\b",
            r"\bextract\s+into\s+multiple\b",
            r"\bpre.?mort\b",
        ],
        reference="Line 60-79: Pattern 3 - Over-Engineering Detection",
    ),
    QuestioningPattern(
        name="swiss_cheese_maintenance",
        question="What happens at scale?",
        description="Detects Swiss cheese maintenance patterns (updating many files vs. single source of truth)",
        triggers=[
            r"\bupdate\s+each\b",
            r"\bupdate\s+every\b",
            r"\bupdate\s+all\b",
            r"\bmodify\s+all\b",
            r"\bchange\s+across\b",
            r"\b(?:across|in)\s+multiple\s+files?\b",
            r"\bmodify\s+\d+\s+components?\b",
            r"\bcreates?\s+multiple\b",
            r"\bmaintenance\s+(?:point|burden|overhead)\b",
            r"\bsingle\s+source\s+of\s+truth\b",
            r"\bcentralize?\b",
            r"\bduplication\b",
            r"\bmultiple\s+(?:sources?|files?|locations?)\s+to\s+maintain\b",
            r"\bscale\s+to\s+\d+\s+components?\b",
        ],
        reference="Line 150-177: Pattern 4 - Swiss Cheese Maintenance Detection",
    ),
    QuestioningPattern(
        name="debugging_cognition",
        question="What does the error actually say?",
        description="Detects debugging scenarios requiring meta-cognitive checks",
        triggers=[
            r"\bdebug\b",
            r"\binvestigate\b",
            r"\bdiagnose\b",
            r"\broot\s+cause\b",
            r"\bwhy\s+(?:is|does|did)\b",
            r"\berror\s+stack\s+trace\b",
            r"\bstack\s+trace\b",
            r"\bfailed\b",
            r"\btest\b",
            r"\bcommand\b",
            r"\bnot\s+working\b",
            r"\b(?:crash|exception|error)\b",
            r"\bthink\b",
            r"\bmight\b",
            r"\bcaused\s+by\b",
            r"\bfirst\b",
            r"\bthen\b",
            r"\bnext\b",
            r"\bcheck\b",
        ],
        reference="Line 197-262: Pattern 5 - Debugging Cognition",
    ),
]

# =============================================================================
# DEBUGGING HEURISTICS (Pattern 5: H1, H2, H3)
# =============================================================================#

_DEBUGGING_HEURISTICS: list[DebuggingHeuristic] = [
    DebuggingHeuristic(
        code="H1",
        name="Entry Point First Rule",
        description="Run failing code directly before hypothesis generation",
        triggers=[
            r"\bthink\b",
            r"\bmight\s+(?:be\s+)?caused\b",
            r"\bmight\b",
            r"\bcould\s+be\b",
            r"\bmaybe\b",
            r"\bperhaps\b",
            r"\bguess\b",
            r"\bhypothes(?:is|es)\b",
            r"\bcaused\s+by\b",
        ],
    ),
    DebuggingHeuristic(
        code="H2",
        name="Parallel Diagnostic Testing",
        description="Test multiple hypotheses simultaneously instead of sequentially",
        triggers=[
            r"\bfirst\b",
            r"\bthen\b",
            r"\bnext\b",
            r"\b(?:after|when)\s+that\b",
            r"\bstep\b",
            r"\bphase\b",
            r"\bsequentially\b",
            r"\b(?:one|another)\s+at\s+a\s+time\b",
            r"\bcheck\b",
        ],
    ),
    DebuggingHeuristic(
        code="H3",
        name="Meta-Cognitive Pre-Flight Check",
        description="Ask 'What does the error actually say?' before proposing solutions",
        triggers=[
            r"\bguess\b",
            r"\blikely\b",
            r"\bprobably\b",
            r"\b(?:looks|seems)(?:\s+like)?\b",
            r"\binterpret\b",
            r"\bbased\s+on\b",
            r"\bmodel\b",
            r"\bmy\b",
        ],
    ),
]

# =============================================================================
# PATTERN COMPILATION (module load time, once)
# =============================================================================#

_COMPILED_PATTERNS: list[tuple[QuestioningPattern, list[re.Pattern]]] = [
    (pattern, [re.compile(trigger, re.IGNORECASE) for trigger in pattern.triggers])
    for pattern in _QUESTIONING_PATTERNS
]

_COMPILED_DEBUGGING: list[tuple[DebuggingHeuristic, list[re.Pattern]]] = [
    (heuristic, [re.compile(trigger, re.IGNORECASE) for trigger in heuristic.triggers])
    for heuristic in _DEBUGGING_HEURISTICS
]


# =============================================================================
# MAIN DETECTION FUNCTION
# =============================================================================#


def detect_questioning_patterns(prompt: str) -> QuestioningMatch:
    """Detect questioning patterns in user prompt.

    Args:
        prompt: User prompt text to analyze

    Returns:
        QuestioningMatch with matched patterns and heuristics
    """
    matched_patterns = []
    matched_heuristics = []
    triggers_found = {}

    # Check each questioning pattern
    for pattern, compiled_triggers in _COMPILED_PATTERNS:
        for trigger in compiled_triggers:
            if trigger.search(prompt):
                if pattern.name not in matched_patterns:
                    matched_patterns.append(pattern.name)
                    # Store first matching trigger for reference
                    if pattern.name not in triggers_found:
                        match = trigger.search(prompt)
                        if match:
                            triggers_found[pattern.name] = match.group(0)
                break  # One match is enough per pattern

    # If debugging_cognition matched, check for specific heuristics
    if "debugging_cognition" in matched_patterns:
        for heuristic, compiled_triggers in _COMPILED_DEBUGGING:
            for trigger in compiled_triggers:
                if trigger.search(prompt):
                    if heuristic.code not in matched_heuristics:
                        matched_heuristics.append(heuristic.code)
                        if heuristic.code not in triggers_found:
                            match = trigger.search(prompt)
                            if match:
                                triggers_found[f"{heuristic.code}_{heuristic.name}"] = match.group(
                                    0
                                )
                    break  # One match is enough per heuristic

    return QuestioningMatch(
        patterns=matched_patterns,
        debugging_heuristics=matched_heuristics,
        triggers=triggers_found,
    )


def get_pattern_context(pattern_name: str) -> str | None:
    """Get context description for a matched pattern.

    Args:
        pattern_name: Name of the pattern (e.g., "arbitrary_threshold")

    Returns:
        Description of what to ask about, or None if pattern not found
    """
    for pattern in _QUESTIONING_PATTERNS:
        if pattern.name == pattern_name:
            return (
                f"**{pattern.question}**\n\n{pattern.description}\n\nReference: {pattern.reference}"
            )
    return None


def get_debugging_guidance(heuristic_code: str) -> str | None:
    """Get guidance for a debugging heuristic.

    Args:
        heuristic_code: H1, H2, or H3

    Returns:
        Description of the heuristic and what to check, or None if not found
    """
    for heuristic in _DEBUGGING_HEURISTICS:
        if heuristic.code == heuristic_code:
            return f"**{heuristic.code}: {heuristic.name}**\n\n{heuristic.description}"
    return None


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================#

# Verify patterns compiled at module load
assert (
    len(_COMPILED_PATTERNS) == 5
), f"Expected 5 questioning patterns, got {len(_COMPILED_PATTERNS)}"
assert (
    len(_COMPILED_DEBUGGING) == 3
), f"Expected 3 debugging heuristics, got {len(_COMPILED_DEBUGGING)}"
