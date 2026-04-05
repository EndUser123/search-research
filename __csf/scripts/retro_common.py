#!/usr/bin/env python3
"""Shared utilities for retrospective lesson detection."""

import re
from typing import List

# Word lists by category - single words are weak, combos are strong
CAUSALITY = ["because", "due to", "caused by", "since", "reason", "why"]
PROBLEM_STATEMENT = ["root cause", "problem was", "issue was", "cause was", "the cause", "error was"]
RESOLUTION = ["fixed", "solved", "resolved", "solution", "worked", "the fix"]
DISCOVERY = ["found", "learned", "discovered", "realized", "turns out", "actually"]
CORRECTION = ["was wrong", "mistake", "my bad", "but it", "not what"]
ANTI_PATTERN = ["don't", "avoid", "never", "not recommended", "bad idea"]

# New categories for enhanced lesson detection
CONFIGURATION = [
    "requires", "required", "needs", "must set", "environment variable",
    "env var", "config", "setting", "flag", "option", "does not support"
]
TRADEOFF = [
    "but", "however", "trade-off", "tradeoff", "versus", "vs", "alternative",
    "faster but", "slower but", "instead of", "rather than"
]
PERFORMANCE = [
    "speedup", "faster", "slower", "overhead", "latency", "throughput",
    "benchmark", "x speedup", "1.1x", "1.5x", "2x", "10x"
]
EDGE_CASE = [
    "empty string", "null", "none", "zero", "0 value", "boundary",
    "edge case", "when empty", "when null", "fails when", "breaks when"
]

# Semantic patterns - common lesson structures
SEMANTIC_PATTERNS = [
    r"\bi (found|learned|discovered|realized) (that|the)\b",
    r"\b(the )?(fix|solution) (was|is)\b",
    r"\b(error|issue|problem) (was|is) caused by\b",
    r"\b(root )?cause (was|is)\b",
    r"\b(problem|issue) (was|is) that\b",
    r"\b(problem|issue|error|cause) (was|is)\b",  # Without requiring "that"
    r"\bturns out\b",
    r"\b(actually|in fact)\b.+\b(not|wrong|different)\b",
    r"\b(don't|avoid|never)\b.+\b(use|do|try)\b",
    # Configuration patterns (allow multiple words between)
    r"\b(requires|required|needs)\s+.+?\s+(for|to|when)\b",
    r"\bmust\s+(set|use|have|configure)\b",
    # Trade-off patterns
    r"\b\w+\s+(is|was)\s+\w+er,\s+but\b",
    r"\bhowever\b.+\b(slower|less)\b",
    # Performance patterns
    r"\bspeedup\s+of\b",
    # Edge case patterns
    r"\b(fails|breaks|errors)\s+when\b",
    r"\bempty\s+(string|array|null)\b",
    r"\bzero\s+(value|length)\b",
    # Version constraint patterns
    r"\bdoes\s+not\s+support\b",
    r"\bonly\s+available\s+in\b",
    r"\bno\s+(build|version)\s+for\b",
]

# Fragment patterns - require 6+ words (don't bypass word count threshold)
FRAGMENT_PATTERNS = [
    r"\bfaster\s+but\b",  # Incomplete comparison
    r"\bslower\s+but\b",  # Incomplete comparison
    r"\b\d+\.?\d*x\b",    # Just a multiplier, needs context
]


def _is_fix(text_lower: str) -> bool:
    """Check if text describes a fix/resolution."""
    return any(w in text_lower for w in RESOLUTION + ["fixed", "resolved"])


def _is_problem(text_lower: str) -> bool:
    """Check if text describes a problem."""
    return any(w in text_lower for w in PROBLEM_STATEMENT)


def _is_anti_pattern(text_lower: str) -> bool:
    """Check if text describes an anti-pattern."""
    return any(w in text_lower for w in ANTI_PATTERN)


def _is_tradeoff_special_case(text_lower: str) -> bool:
    """Check for special tradeoff phrases."""
    return any(phrase in text_lower for phrase in
               ["faster but", "slower but", "speedup but", "however"])


def _is_perf(text_lower: str) -> bool:
    """Check if text relates to performance."""
    return (any(w in text_lower for w in PERFORMANCE) or
            re.search(r"\b\d+\.?\d*x\b", text_lower))


def _check_remaining_types(text_lower: str) -> str:
    """Check remaining lesson types in priority order."""
    # Simple string inclusion checks
    type_checks = [
        (CONFIGURATION, "CONFIG"),
        (TRADEOFF, "TRADEOFF"),
        (EDGE_CASE, "EDGE_CASE"),
        (DISCOVERY, "DISCOVERY"),
        (CORRECTION, "CORRECTION"),
    ]
    for category, name in type_checks:
        if any(w in text_lower for w in category):
            return name
    return "PATTERN"


def classify_lesson_type(text: str) -> str:
    """
    Classify what type of lesson this is for better SKILL.md formatting.

    Priority order: FIX > PROBLEM > ANTI_PATTERN > PERF > CONFIG > TRADEOFF >
    EDGE_CASE > DISCOVERY > CORRECTION > PATTERN
    """
    text_lower = text.lower()

    # Priority order checking - special cases first
    if _is_fix(text_lower):
        return "FIX"
    if _is_problem(text_lower):
        return "PROBLEM"
    if _is_anti_pattern(text_lower):
        return "ANTI_PATTERN"
    if _is_tradeoff_special_case(text_lower):
        return "TRADEOFF"
    if _is_perf(text_lower):
        return "PERF"

    # Remaining types via grouped check
    return _check_remaining_types(text_lower)


def _matches_semantic_pattern(text_lower: str) -> bool:
    """Check if text matches any semantic pattern."""
    for pattern in SEMANTIC_PATTERNS:
        if re.search(pattern, text_lower):
            if not any(re.search(fp, text_lower) for fp in FRAGMENT_PATTERNS):
                return True
    return False


def _score_categories(text_lower: str) -> int:
    """Score how many lesson categories are present in text."""
    score = 0
    categories = [CAUSALITY, PROBLEM_STATEMENT, RESOLUTION, DISCOVERY,
                  CORRECTION, ANTI_PATTERN, CONFIGURATION, TRADEOFF,
                  PERFORMANCE, EDGE_CASE]
    for category in categories:
        if any(w in text_lower for w in category):
            score += 1
    return score


def _matches_fragment_pattern(text_lower: str) -> bool:
    """Check if text matches any fragment pattern."""
    for pattern in FRAGMENT_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def has_lesson_structure(text: str) -> bool:
    """
    Check for lesson-worthy structural combinations.

    Lesson-worthy = multiple categories present (causality + resolution,
    discovery + insight, etc.). Single words aren't enough.

    Enhanced to include CONFIGURATION, TRADEOFF, PERFORMANCE, EDGE_CASE.
    Extended semantic patterns bypass minimum word count (if >= 4 words).
    Fragment patterns require 6+ words.
    """
    word_count = len(text.split())
    text_lower = text.lower()

    # Check semantic patterns with relaxed word count
    if word_count >= 4 and _matches_semantic_pattern(text_lower):
        return True

    # Require minimum words for score-based detection
    if word_count < 6:
        return False

    # Score categories and require combo
    if _score_categories(text_lower) >= 2:
        return True

    # Check fragment patterns
    if _matches_fragment_pattern(text_lower):
        return True

    return False


def is_actionable_lesson(text: str) -> tuple[bool, str]:
    """
    Check if lesson follows actionable format: If X then Y.

    Returns:
        (is_actionable, reason_if_not)

    Actionable patterns:
    - "If [situation], then [action]" - explicit conditional
    - "When [happens], do [action]" - trigger-action format
    - "Use X for Y" - prescriptive
    - "Don't X because Y" - anti-pattern with reason
    - "X requires Y" - dependency pattern

    Non-actionable patterns (observations):
    - "Found that X" - just discovery
    - "X is Y" - descriptive statement
    - "Created X files" - changelog entry
    """
    text_lower = text.lower()

    # Actionable patterns (explicit conditionals)
    # Simplified: check for keywords that imply prescriptive content
    actionable_indicators = [
        "if ", "when ", "use ", "try ", "avoid ", "call ", "run ",
        "don't ", "do not ", "never ", "must ", "requires ", "required ",
        "instead of ", "rather than "
    ]

    # But also require some action/prescriptive element
    action_indicators = [
        "use", "run", "call", "set", "configure", "avoid", "try",
        "check", "verify", "add", "remove", "delete", "install",
        "rm ", "rm -", "git ", "python ", "npm ", "pip ",
        "then ", " to ", " for ", " instead", " rather",
        "first", "instead", "before", "after"
    ]

    # Observation-only patterns (non-actionable)
    observation_patterns = [
        r"^(i )?(found|discovered|learned|realized)\s+(that|the)\b",
        r"^(there is|there was|it is)\b",
        r"^(created|added|wrote|updated|removed)\s+\d+\s+",  # "Created 4 files"
        r"^(output|result|returned)\s*:",
    ]

    # Check for actionable patterns
    has_trigger = any(ind in text_lower for ind in actionable_indicators)
    has_action = any(ind in text_lower for ind in action_indicators)

    if has_trigger and has_action:
        return True, ""

    # Check if it's just an observation
    for pattern in observation_patterns:
        if re.search(pattern, text_lower):
            return False, "Observation format (e.g., 'Found that X', 'Created 4 files')"

    return False, "Missing clear trigger-action format (e.g., 'If X then Y')"


def _score_actionability(text_lower: str) -> tuple[bool, str]:
    """Check if lesson has actionable indicators."""
    actionable_indicators = [
        "if ", "when ", "use ", "try ", "avoid ", "call ", "run ",
        "don't ", "do not ", "never ", "must ", "requires ", "required ",
        "instead of ", "rather than "
    ]
    action_indicators = [
        "use", "run", "call", "set", "configure", "avoid", "try",
        "check", "verify", "add", "remove", "delete", "install",
        "rm ", "rm -", "git ", "python ", "npm ", "pip ",
        "then ", " to ", " for ", " instead", " rather",
        "first", "before", "after"
    ]
    has_trigger = any(ind in text_lower for ind in actionable_indicators)
    has_action = any(ind in text_lower for ind in action_indicators)
    return has_trigger and has_action, ""


def _score_specificity(text_lower: str) -> tuple[bool, str]:
    """Check if lesson has specific details."""
    specific_indicators = [
        "file:", "line ", "function ", "class ", "error:", "traceback",
        ".py", ".md", ".ts", ".js", "0x", "/",
        "git ", "rm ", "pip ", "npm ",
    ]
    return any(ind in text_lower for ind in specific_indicators), ""


def _score_nonobvious(text_lower: str) -> tuple[bool, str]:
    """Check if lesson is non-obvious (not generic advice)."""
    obvious_patterns = [
        "always test", "always check", "make sure", "remember to",
        "don't forget", "best practice", "it's important",
    ]
    return not any(p in text_lower for p in obvious_patterns), ""


def _score_substance(text: str, word_count: int) -> tuple[bool, str]:
    """Check if lesson has substantive content."""
    return word_count > 30, ""


def _score_discovery(text_lower: str) -> tuple[bool, str]:
    """Check if lesson contains root cause / discovery."""
    high_value_patterns = [
        "root cause", "turns out", "actually", "discovered",
        "realized", "found that", "the issue was",
    ]
    return any(p in text_lower for p in high_value_patterns), ""


def score_lesson_confidence(text: str) -> tuple[int, str]:
    """
    Score lesson quality from 1-5 on "will this actually change behavior".

    Returns:
        (score, reason)

    Scoring criteria:
    - 5: Actionable (If X then Y) + specific + non-obvious
    - 4: Actionable + specific but somewhat obvious
    - 3: Actionable but vague/general
    - 2: Observation but interesting
    - 1: Changelog entry / obvious fact
    """
    text_lower = text.lower()
    score = 3  # Start at middle
    reasons = []

    # Check each dimension via helper functions
    is_actionable, _ = _score_actionability(text_lower)
    if is_actionable:
        score += 1
    else:
        score -= 1
        reasons.append("Not actionable")

    has_specific, _ = _score_specificity(text_lower)
    if has_specific:
        score += 1
    else:
        reasons.append("Lacks specific details")

    is_nonobvious, _ = _score_nonobvious(text_lower)
    if not is_nonobvious:
        score -= 1
        reasons.append("Generic advice")

    word_count = len(text.split())
    if word_count < 10:
        score -= 1
        reasons.append("Too short")
    elif word_count > 30:
        score += 1

    has_discovery, _ = _score_discovery(text_lower)
    if has_discovery:
        score += 1

    # Clamp to 1-5 range
    score = max(1, min(5, score))

    reason_str = ", ".join(reasons) if reasons else ("Actionable" if is_actionable else "Observation")
    return score, reason_str


def _extract_keywords(segment: str) -> set[str]:
    """Extract significant keywords from segment for similarity matching."""
    words = set(segment.lower().split())
    stop_words = {"the", "a", "an", "is", "was", "to", "for", "in", "on", "at", "by", "of", "with"}
    return {w for w in words if w not in stop_words and len(w) > 4}


def _group_by_keywords(all_segments: List[tuple]) -> dict:
    """Group segments by shared keywords."""
    patterns = {}
    for seg_tuple in all_segments:
        segment = seg_tuple[0]
        session_file = seg_tuple[3] if len(seg_tuple) > 3 else "unknown"
        keywords = _extract_keywords(segment)

        for keyword in keywords:
            if keyword not in patterns:
                patterns[keyword] = []
            patterns[keyword].append((segment, session_file))
    return patterns


def _build_recurring_list(patterns: dict, threshold: int) -> List[dict]:
    """Build list of recurring patterns from grouped keywords."""
    import hashlib
    recurring = []
    seen_segments = set()

    for keyword, occurrences in patterns.items():
        if len(occurrences) >= threshold:
            for segment, session_file in occurrences:
                seg_hash = hashlib.md5(segment[:100].encode()).hexdigest()[:8]
                if seg_hash not in seen_segments:
                    seen_segments.add(seg_hash)
                    recurring.append({
                        "segment": segment[:200],
                        "keyword": keyword,
                        "count": len(occurrences),
                        "sessions": [occ[1] for occ in occurrences if occ[1] != "unknown"][:3]
                    })
                    break
    return recurring


def detect_recurring_patterns(all_segments: List[tuple[str, int, str]], threshold: int = 2) -> List[dict]:
    """
    Detect lessons that appear across multiple sessions (recurring patterns).

    Args:
        all_segments: List of (segment, confidence, reason, session_file) tuples
        threshold: Minimum occurrences to mark as "recurring". Default: 2.

    Returns:
        List of dicts with pattern info: {segment, count, sessions, keywords}
    """
    patterns = _group_by_keywords(all_segments)
    recurring = _build_recurring_list(patterns, threshold)
    recurring.sort(key=lambda x: x["count"], reverse=True)
    return recurring


def _is_command_doc(part_lower: str) -> bool:
    """Check if part is command documentation (should be filtered)."""
    doc_patterns = [
        "## execution directive",
        "# /",
        "command-description:",
        "what happened:",
        "**reflex**:",
        "**implementation**:",
        "**cks**:",
        "## ⚡ execution directive",
        "do not:",
        "required:",
        "mandatory:",
    ]
    return any(p in part_lower for p in doc_patterns)


def _is_skill_format(part_lower: str) -> bool:
    """Check if part looks like SKILL.md lesson format."""
    return any(x in part_lower for x in ["**what happened**:", "**reflex**:", "**implementation**:"])


def _passes_filters(part: str, min_confidence: int, require_actionable: bool) -> tuple[bool, int, str]:
    """Check if a lesson segment passes all filters."""
    if not has_lesson_structure(part):
        return False, 0, ""

    confidence, reason = score_lesson_confidence(part)
    if confidence < min_confidence:
        return False, confidence, reason

    if require_actionable:
        is_act, _ = is_actionable_lesson(part)
        if not is_act:
            return False, confidence, reason

    return True, confidence, reason


def extract_lesson_segments(text: str, require_actionable: bool = False, min_confidence: int = 1) -> List[tuple[str, int, str]]:
    """
    Extract lesson-worthy segments from text.
    Returns segments that have lesson structure.
    Filters out command documentation.

    Args:
        text: Session transcript text
        require_actionable: If True, only return segments that follow
            actionable format (If X then Y). Default: False for backward compatibility.
        min_confidence: Minimum confidence score (1-5) to include. Default: 1 (all).

    Returns:
        List of tuples (segment, confidence_score, reason).
        For backward compatibility, confidence is included but optional filtering available.
    """
    if not text or len(text.split()) < 20:
        return []

    segments = []
    parts = re.split(r"<command-message>|User:|user:", text)

    for part in parts:
        part = part.strip()
        if len(part) < 30:
            continue

        part_lower = part.lower()
        if _is_command_doc(part_lower) and _is_skill_format(part_lower):
            continue

        passes, conf, reason = _passes_filters(part, min_confidence, require_actionable)
        if passes:
            segments.append((part, conf, reason))

    return segments
