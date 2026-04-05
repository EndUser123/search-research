#!/usr/bin/env python3
"""Stop hook for Symptom Map.

Blocks fixes for multiple symptoms without shared cause mapping.

From ADR-20260325-reasoning-hygiene-hooks.md

Gate 5: Command hook (regex) detection.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Patterns that indicate addressing multiple symptoms
_MULTI_SYMPTOM_PATTERNS = [
    re.compile(r"(?i)\bfix(?:ing|ed|es)?\s+(?:both|all|these)\b", re.IGNORECASE),
    re.compile(r"(?i)\bissue[sz]?\s*[:]\s*\d+\b", re.IGNORECASE),  # "issues: 1, 2, 3"
    re.compile(r"(?i)\bproblems?\s*[:]\s*\d+\b", re.IGNORECASE),
    re.compile(r"(?i)\bseveral\s+issues?\b", re.IGNORECASE),
    re.compile(r"(?i)\bmultiple\s+(?:problems?|issues?|bugs?)\b", re.IGNORECASE),
    re.compile(r"(?i)\bsymptom[s]?\b", re.IGNORECASE),  # Explicit mention of symptoms
]

# Patterns that indicate identifying shared cause
_CAUSE_MAPPING_PATTERNS = [
    re.compile(r"(?i)\bshared\s+cause\b", re.IGNORECASE),
    re.compile(r"(?i)\bsymptom[s]?\s+(?:of|point(?:s|ing)?\s+to)\s+\w+\b", re.IGNORECASE),
    re.compile(r"(?i)\b(may|might|likely)\s+be\s+(?:caused|related|due)\s+to\b", re.IGNORECASE),
    re.compile(r"(?i)\broot\s+cause\b", re.IGNORECASE),
    re.compile(
        r"(?i)\ball\s+(?:of\s+)?(?:these|the)\s+(?:issues?|problems?|bugs?)\s+share\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?i)\bcommon\s+source\b", re.IGNORECASE),
    re.compile(r"(?i)\bthe\s+same\s+(?:cause|issue|problem)\b", re.IGNORECASE),
    re.compile(r"(?i)\btraced\s+to\b", re.IGNORECASE),
    re.compile(r"(?i)\bisolated\s+to\b", re.IGNORECASE),
    re.compile(r"(?i)\bdown\s+to\b", re.IGNORECASE),  # "narrowed down to"
]

# Patterns that indicate fixing symptoms separately without cause mapping
_FIX_PATTERNS = [
    re.compile(r"(?i)\bfix(?:ed|es|ing)?\b", re.IGNORECASE),
    re.compile(r"(?i)\bresolv(?:ed|es|ing)\b", re.IGNORECASE),
    re.compile(r"(?i)\baddress(?:ed|es|ing)?\b", re.IGNORECASE),
]


def _is_gate_enabled() -> bool:
    """Check if this gate is enabled via environment variable."""
    return os.environ.get("SYMPTOM_MAP_ENABLED", "true").lower() == "true"


def _has_multi_symptom(text: str) -> bool:
    """Check if text describes multiple symptoms."""
    for pattern in _MULTI_SYMPTOM_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _has_cause_mapping(text: str) -> bool:
    """Check if text maps symptoms to shared cause."""
    for pattern in _CAUSE_MAPPING_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _has_fix(text: str) -> bool:
    """Check if text contains fix language."""
    for pattern in _FIX_PATTERNS:
        if pattern.search(text):
            return True
    return False


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate if response fixes multiple symptoms without cause mapping.

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

    if not response_text or len(response_text.strip()) < 20:
        return {"allow": True, "reason": "Response too short to analyze"}

    # Check if response addresses multiple symptoms
    if not _has_multi_symptom(response_text):
        return {"allow": True, "reason": "No multi-symptom pattern detected"}

    # Check if there's fix language (actually trying to fix something)
    if not _has_fix(response_text):
        return {"allow": True, "reason": "No fix language detected"}

    # Check if cause mapping is present
    if _has_cause_mapping(response_text):
        return {"allow": True, "reason": "Cause mapping found"}

    # Increment circuit breaker on block
    if session_id:
        from __lib.circuit_breaker import increment_iteration

        increment_iteration(session_id)

    return {
        "allow": False,
        "reason": (
            "SYMPTOM MAPPING REQUIRED\n\n"
            "You described fixing multiple issues without mapping them to a shared cause.\n\n"
            "Before treating symptoms:\n"
            "1. Identify: Are these N issues manifestations of ONE root cause?\n"
            "2. State: 'These symptoms all point to X'\n"
            "3. Fix: Address X, not individual symptoms\n\n"
            "If no shared cause exists, explain why these are independent issues.\n\n"
            "Examples:\n"
            "  WRONG: 'Fix the timeout. Fix the memory leak. Fix the error.'\n"
            "  RIGHT: 'Both issues are symptoms of the same resource leak. Fix the leak.'\n\n"
            "To disable: export SYMPTOM_MAP_ENABLED=false"
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
