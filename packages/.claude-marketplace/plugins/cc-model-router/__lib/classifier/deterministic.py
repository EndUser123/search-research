"""Deterministic override patterns for high-precision classification.

These run BEFORE semantic scoring. If a pattern matches, the prompt is
classified immediately without invoking the TF-IDF scorer.

Patterns extracted from the original model_router_classify.py and reorganized
into a clean function. The original regex lists are preserved for backward compat.
"""
from __future__ import annotations

import re

# Background: git/build/lint commands — high precision, never ambiguous
BACKGROUND_PATTERNS = [
    r"\bgit\s+(commit|push|pull|status|log|diff|add|stash|branch|merge|rebase|checkout)\b",
    r"\bcommit\b.*\b(change|push|all)\b",
    r"\bpush\s+(to|the|remote|origin)\b",
    r"\bformat\b(?!\s+(a|the|new|component|page|function))",
    r"\blint\b",
    r"\bprettier\b",
    r"\beslint\b",
    r"\bremove\s+(unused|dead)\b",
    r"\bupdate\s+(version|package)\b",
    r"\bnpm\s+(install|run|build|test)\b",
    r"\bpip\s+install\b",
    r"\bbuild\s+(the|this|project)\b",
    r"\brestart\s+(the|dev)\s*server\b",
    r"\bclear\s+(the\s+)?(terminal|console|screen)\b",
]

# Local/trivial: short mechanical edits — checked only when word_count <= 12
LOCAL_PATTERNS = [
    r"^(yes|no|ok|okay|sure|yep|nope|y|n)$",
    r"^(thanks|thank you|thx|ty)$",
    # Session-control words (genuinely trivial acknowledgements - cheap model fine).
    # NOTE: continuation words (continue, go on, next) deliberately REMOVED - they
    # inherit the previous task's tier via the semantic classifier + followup boost,
    # since "continue" could be continuing coding, architecture, or research.
    r"^(done|stop|quit|exit)$",
    r"^(show|print|list|tell me about|what is|where is)\s+\w{0,20}$",
    r"^(format|lint|check)\s+\w+$",
    r"^~\s+\w{0,20}$",
    r"^(rename|move|copy|delete|remove|insert|replace|add)\s+(?:the\s+)?\w+$",
    r"^(extract|inline|convert|wrap|unwrap)\s+(?:the\s+)?\w+$",
    r"^(update|change|set)\s+(the\s+)?\w+\s+(to|in|on)\s+\w+$",
    r"^(sort|reorder|alphabetize)\s+(?:the\s+)?\w+$",
    r"^(strip|trim|clean|dedupe|dedup)\s+(?:the\s+)?\w+$",
]

# Mechanical edit patterns for trivial-coding detection (Stage C)
# These match the "shape" of a trivial edit (verb + noun phrase).
# However, many of these also match non-trivial tasks — Stage C applies
# a NON_TRIVIALITY_EXCLUSIONS blacklist AND a word-count gate to filter.
MECHANICAL_EDIT_PATTERNS = [
    r"^(rename|move|copy|delete|remove|insert|replace|add)\s+",
    r"^(extract|inline|convert|wrap|unwrap)\s+",
    r"^(update|change|set)\s+",
    r"^(sort|reorder|alphabetize)\s+",
    r"^(strip|trim|clean|dedupe|dedup)\s+",
]

# Verb-object combos that look mechanical but are non-trivial coding tasks.
# The Stage C heuristic fires when word_count <= threshold AND is_mechanical_edit.
# This blacklist overrides: if the prompt matches any of these, treat as non-trivial
# even if it also matches the mechanical pattern above.
NON_TRIVIALITY_EXCLUSIONS = [
    r"\b(add|create|write|implement|build)\b.*\b(test|tests|unit|spec|specification)\b",
    r"\b(replace|swap|update)\b.*\b(deprecated|legacy|old|v1|v2)\b",
    r"\b(extract|refactor)\b.*\b(into|and)\b.*\b(update|call|all)\b",
    r"\b(add|create)\b.*\b(and|then)\b",   # compound: "add X and Y" is non-trivial
    r"\b(replace|swap)\b.*\b(with|and)\b.*\b(update|all|every)\b",  # compound replace
]


def check_overrides(prompt: str) -> str | None:
    """Check high-precision deterministic overrides.

    Returns taskType ("background" or "local-coding") if an override matches,
    or None if no override fires (prompt should proceed to semantic scoring).
    """
    prompt_lower = prompt.lower().strip()
    word_count = len(prompt.split())

    # Background: git/build/lint commands — only for short command-like prompts.
    # Long prompts (>50 words) mentioning these keywords in passing are diagnostic
    # discussions, not background tasks. LOCAL_PATTERNS gate at word_count <= 12
    # establishes this pattern; BACKGROUND_PATTERNS follow suit at 50 words.
    if word_count <= 50:
        for pattern in BACKGROUND_PATTERNS:
            if re.search(pattern, prompt_lower):
                return "background"

    # Local: short mechanical edits (word_count <= 12 gate is load-bearing)
    if word_count <= 12:
        for pattern in LOCAL_PATTERNS:
            if re.search(pattern, prompt_lower):
                return "local-coding"

    return None


def is_mechanical_edit(prompt: str) -> bool:
    """Check if a coding prompt is a trivial mechanical edit (Stage C).

    Returns True only if the prompt matches a mechanical pattern AND does NOT
    match any non-triviality exclusion. Excluded prompts are real coding tasks
    (add tests, replace deprecated APIs, extract logic) despite having a
    verb+object shape.
    """
    prompt_lower = prompt.lower().strip()
    if not any(re.search(p, prompt_lower) for p in MECHANICAL_EDIT_PATTERNS):
        return False
    # Blacklist: if the prompt matches a non-trivial exclusion, it's real coding
    for excl in NON_TRIVIALITY_EXCLUSIONS:
        if re.search(excl, prompt_lower):
            return False
    return True
