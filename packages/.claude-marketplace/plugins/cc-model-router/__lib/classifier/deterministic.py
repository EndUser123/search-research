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
    r"^(continue|go on|next|done|stop|quit|exit)$",
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
MECHANICAL_EDIT_PATTERNS = [
    r"^(rename|move|copy|delete|remove|insert|replace|add)\s+\w+",
    r"^(extract|inline|convert|wrap|unwrap)\s+\w+",
    r"^(update|change|set)\s+(the\s+)?\w+\s+(to|in|on)\s+\w+",
    r"^(sort|reorder|alphabetize)\s+\w+",
    r"^(strip|trim|clean|dedupe|dedup)\s+\w+",
]


def check_overrides(prompt: str) -> str | None:
    """Check high-precision deterministic overrides.

    Returns taskType ("background" or "local-coding") if an override matches,
    or None if no override fires (prompt should proceed to semantic scoring).
    """
    prompt_lower = prompt.lower().strip()
    word_count = len(prompt.split())

    # Background: git/build/lint commands
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

    Used by the pipeline to distinguish trivial-coding from general-coding.
    """
    prompt_lower = prompt.lower().strip()
    return any(re.search(p, prompt_lower) for p in MECHANICAL_EDIT_PATTERNS)
