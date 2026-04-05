#!/usr/bin/env python3
"""Stop hook for Optimality Check.

Blocks solution recommendations without optimality tier assessment.

From ADR-20260325-reasoning-hygiene-hooks.md

Gate 4: Command hook (regex) detection.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Matches solution recommendation phrases
_SOLUTION_RECOMMENDATION_PATTERNS = [
    re.compile(r"(?i)\bwe\s+should\b", re.IGNORECASE),
    re.compile(r"(?i)\bi\s+recommend\b", re.IGNORECASE),
    re.compile(r"(?i)\bthe\s+(?:best|correct)\s+approach\b", re.IGNORECASE),
]

# Patterns that indicate optimality tier assessment
_OPTIMALITY_ASSESSMENT_PATTERNS = [
    re.compile(r"(?i)\bimmediate(?:ly)?\s+(?:solution|fix|answer)\b", re.IGNORECASE),
    re.compile(r"(?i)\boptimal(?:\s+enough)?\b", re.IGNORECASE),
    re.compile(r"(?i)\blong[- ]term\b", re.IGNORECASE),
    re.compile(r"(?i)\btrade[- ]off\b", re.IGNORECASE),
    re.compile(r"(?i)\balternative[s]?\b", re.IGNORECASE),
    re.compile(r"(?i)\bminimum\s+(?:acceptable|solution)\b", re.IGNORECASE),
    re.compile(r"(?i)\bquick(?:ly)?\s+fix\b", re.IGNORECASE),
    re.compile(r"(?i)\btemporary\b", re.IGNORECASE),
    re.compile(r"(?i)\bpermanent(?:ly)?\b", re.IGNORECASE),
    re.compile(r"(?i)\bnow\b.*\b(later|eventually|ultimately)\b", re.IGNORECASE),
    re.compile(r"(?i)\bvs\.?\b", re.IGNORECASE),  # "X vs Y"
]


def _is_gate_enabled() -> bool:
    """Check if this gate is enabled via environment variable."""
    return os.environ.get("OPTIMALITY_CHECK_ENABLED", "true").lower() == "true"


def _has_recommendation(text: str) -> bool:
    """Check if text contains solution recommendation phrases."""
    for pattern in _SOLUTION_RECOMMENDATION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _has_optimality_assessment(text: str) -> bool:
    """Check if text contains optimality tier assessment."""
    for pattern in _OPTIMALITY_ASSESSMENT_PATTERNS:
        if pattern.search(text):
            return True
    return False


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate if response contains recommendation without optimality assessment.

    Args:
        data: Hook data containing response_text

    Returns:
        Dictionary with 'allow' (bool) and 'reason' (str)
    """
    if not _is_gate_enabled():
        return {"allow": True, "reason": "Gate disabled"}

    # Circuit breaker integration: check for acceptance phrases and threshold
    session_id = str(data.get("session_id", ""))
    user_message = str(data.get("prompt", "") or data.get("user_message", ""))

    if session_id:
        from __lib.circuit_breaker import check_and_reset_on_acceptance

        # Reset circuit breaker if user sent acceptance phrase
        check_and_reset_on_acceptance(session_id, user_message)

        from __lib.circuit_breaker import should_allow_continue

        if should_allow_continue(session_id, stop_hook_active=True):
            return {"allow": True, "reason": "Circuit breaker tripped"}

    response_text = data.get("response_text", "")

    if not response_text or len(response_text.strip()) < 10:
        return {"allow": True, "reason": "Response too short to analyze"}

    # Check if there's a recommendation
    if not _has_recommendation(response_text):
        return {"allow": True, "reason": "No solution recommendation detected"}

    # Check if optimality assessment is present
    if _has_optimality_assessment(response_text):
        return {"allow": True, "reason": "Optimality assessment found"}

    # Increment circuit breaker on block
    if session_id:
        from __lib.circuit_breaker import increment_iteration

        increment_iteration(session_id)

    return {
        "allow": False,
        "reason": (
            "OPTIMALITY ASSESSMENT REQUIRED\n\n"
            "When recommending a solution, assess alternatives:\n\n"
            "Immediate: 'do X' (works now, may not scale)\n"
            "Optimal: 'do Y' (better long-term, trade-offs documented)\n"
            "Minimum: 'do Z' (acceptable, known limitations)\n\n"
            "Your recommendation must include:\n"
            "- Which category (immediate/optimal/minimum)\n"
            "- Key trade-offs vs alternatives\n"
            "- Why this is 'optimal enough' for the current context\n\n"
            "Examples:\n"
            "  'Use dict for now (quick), but consider WeakValueDictionary for long-term'\n"
            "  'Immediate: cache invalidation; Optimal: event-driven updates'\n\n"
            "To disable: export OPTIMALITY_CHECK_ENABLED=false"
        ),
    }


if __name__ == "__main__":
    import json
    import sys

    try:
        raw = sys.stdin.read().strip()
        input_data = json.loads(raw) if raw else {}
    except Exception:
        input_data = {}

    result = run(input_data)
    print(json.dumps(result))
