#!/usr/bin/env python3
"""Stop hook for Fix Verification Enforcer.

Blocks topic transitions without explicit fix verification evidence.

From ADR-20260325-reasoning-hygiene-hooks.md

Gate 3: Command hook (regex) detection.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Matches topic transition phrases
_TOPIC_TRANSITION_PATTERNS = [
    re.compile(r"(?i)\bmoving\s+on\b", re.IGNORECASE),
    re.compile(r"(?i)\bnext\s+issue\b", re.IGNORECASE),
    re.compile(r"(?i)\blet'?s\s+(?:talk\s+about|move\s+to)\b", re.IGNORECASE),
    re.compile(r"(?i)\bchanging\s+subject\b", re.IGNORECASE),
]

# Patterns that indicate verification evidence
_VERIFICATION_EVIDENCE_PATTERNS = [
    re.compile(r"(?i)\b(?:tool\s+)?output[:\s]", re.IGNORECASE),
    re.compile(r"(?i)\b(?:test\s+)?result[s]?[:\s]", re.IGNORECASE),
    re.compile(
        r"(?i)\bfrom\s+(?:the\s+)?(?:above\s+)?(?:tool\s+)?(?:output|execution|running)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?i)\b(pytest|test|bash|grep|read|ls|glob)\s+(?:shows?|shows|output|result)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?i)```", re.IGNORECASE),  # Code block indicating tool output
    re.compile(
        r"(?i)\bfile\s*[:\(]", re.IGNORECASE
    ),  # "file:" or "file (" indicating read evidence
    re.compile(r"(?i)\b(?:error|exception|traceback)[:\s]", re.IGNORECASE),
    re.compile(r"(?i)\bpASS(?:ed|ing)?\b", re.IGNORECASE),  # test passed
    re.compile(r"(?i)\bfail(?:ed|ing)?\b", re.IGNORECASE),  # test failed
]


def _is_gate_enabled() -> bool:
    """Check if this gate is enabled via environment variable."""
    return os.environ.get("FIX_VERIFICATION_ENFORCER_ENABLED", "true").lower() == "true"


def _has_verification_evidence(text: str) -> bool:
    """Check if text contains verification evidence patterns."""
    for pattern in _VERIFICATION_EVIDENCE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _find_last_transition_index(response_text: str) -> int | None:
    """Find the index of the last topic transition phrase in response.

    Returns the index of the first character after the transition phrase,
    or None if no transition found.
    """
    last_pos = -1
    for pattern in _TOPIC_TRANSITION_PATTERNS:
        match = pattern.search(response_text)
        if match:
            # Use the end of the match as the transition point
            if match.end() > last_pos:
                last_pos = match.end()

    return last_pos if last_pos >= 0 else None


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate if response contains topic transition without verification.

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

    # Find topic transition in response
    transition_pos = _find_last_transition_index(response_text)
    if transition_pos is None:
        return {"allow": True, "reason": "No topic transition detected"}

    # Get text before the transition - this is where verification should appear
    text_before_transition = response_text[:transition_pos]

    # Check if there's verification evidence before the transition
    if _has_verification_evidence(text_before_transition):
        return {"allow": True, "reason": "Verification evidence found before transition"}

    # Increment circuit breaker on block
    if session_id:
        from __lib.circuit_breaker import increment_iteration

        increment_iteration(session_id)

    return {
        "allow": False,
        "reason": (
            "TOPIC TRANSITION WITHOUT VERIFICATION\n\n"
            "You're moving to a new topic without verifying the fix for the previous issue.\n\n"
            "Before transitioning:\n"
            "1. Show evidence the fix works: tool output, test results\n"
            "2. State what was verified\n"
            "3. Then transition\n\n"
            "Examples of verification evidence:\n"
            "  'Test output shows all 12 tests passed'\n"
            "  'Running the script shows: [...]'\n"
            "  'File read confirms the fix is in place'\n\n"
            "To disable: export FIX_VERIFICATION_ENFORCER_ENABLED=false"
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
