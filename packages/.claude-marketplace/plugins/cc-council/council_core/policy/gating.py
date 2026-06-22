"""Gating and classification policy.

Determines when to use council vs single-model execution.

Simple heuristics for v1:
- Explicit @council prefix
- Keyword triggers
- Length threshold
"""

from typing import Any


# Keyword triggers that suggest complex deliberation
_GATING_KEYWORDS = {
    "compare",
    "analyze",
    "evaluate",
    "review",
    "assess",
    "debate",
    "critique",
    "recommend",
    "design",
    "architecture",
    "trade-off",
    "tradeoff",
}


def classify_task(prompt: str, *, force_council: bool = False) -> tuple[bool, str]:
    """Classify whether task requires council deliberation.

    Args:
        prompt: User's original prompt
        force_council: Skip gating and always use council

    Returns:
        Tuple of (should_use_council: bool, reason: str)
    """
    if force_council:
        return True, "explicit force-council flag"

    prompt_stripped = prompt.strip()

    # Explicit council prefix
    if prompt_stripped.startswith("@council"):
        return True, "explicit @council prefix"

    # Check for gating keywords
    prompt_lower = prompt_lowered = prompt_stripped.lower()
    matched_keywords = [kw for kw in _GATING_KEYWORDS if kw in prompt_lower]
    if matched_keywords:
        return True, f"keyword match: {', '.join(matched_keywords)}"

    # Length threshold - complex tasks tend to be longer
    if len(prompt_stripped) > 200:
        return True, "prompt complexity (length > 200 chars)"

    return False, "simple task - single model sufficient"


def should_bypass_council(prompt: str, *, force_council: bool = False) -> bool:
    """Convenience function to check if council should be bypassed.

    Args:
        prompt: User's original prompt
        force_council: Skip gating and always use council

    Returns:
        True if council should be bypassed (single-model is sufficient)
    """
    should_use, _ = classify_task(prompt, force_council=force_council)
    return not should_use