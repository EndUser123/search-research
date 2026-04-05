#!/usr/bin/env python3
"""Stop hook for Good Question Gate — blocks consultation pattern deflections.

Blocks responses that lead with permission-request or self-directed question
patterns instead of executing. Examples: 'Did you want me to...', 'Good question...'.

Allows mid-sentence usage like 'Good question — the answer is X'.

From ADR-20260325-reasoning-hygiene-hooks.md
Extended in ADR-20260329-llm-consultation-pattern-fix.md

Gate 1: Command hook (regex) detection.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Matches "Good question" at the START of response, not mid-sentence
# Negative lookahead ensures it's not followed by em-dash or comma (legitimate usage)
_GOOD_QUESTION_PATTERN = re.compile(
    r"^Good question\b(?!\s*—)(?!\s*,\s*)",
    re.IGNORECASE | re.MULTILINE,
)

# Additional deflection patterns: start-of-response only, case-insensitive
# Each pattern is a permission request or self-directed question that deflects execution
_DEFLECTION_PATTERNS = [
    # "Did you want me to..." — leading permission request
    re.compile(r"^Did\s+you\s+want\s+me\s+to\b", re.IGNORECASE | re.MULTILINE),
    # "Would you like me to..." — leading permission request
    re.compile(r"^Would\s+you\s+like\s+me\s+to\b", re.IGNORECASE | re.MULTILINE),
    # "Should I..." — leading self-directed question
    re.compile(r"^Should\s+I\s+", re.IGNORECASE | re.MULTILINE),
]


def _check_deflections(response_text: str) -> re.Match | None:
    """Check response against all deflection patterns.

    Returns the first match found, or None if no deflection detected.
    """
    for pattern in _DEFLECTION_PATTERNS:
        match = pattern.search(response_text)
        if match:
            return match
    return None


def _is_gate_enabled() -> bool:
    """Check if this gate is enabled via environment variable."""
    return os.environ.get("STOP_GOOD_QUESTION_GATE_ENABLED", "true").lower() == "true"


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate if response contains leading 'Good question' deflection.

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

    if not response_text or len(response_text.strip()) < 5:
        return {"allow": True, "reason": "Response too short to analyze"}

    # Check for "Good question" deflection
    gq_match = _GOOD_QUESTION_PATTERN.search(response_text)
    # Check for other deflection patterns
    deflection_match = _check_deflections(response_text)

    if not gq_match and not deflection_match:
        return {"allow": True, "reason": "No leading deflection detected"}

    # Determine which pattern matched for targeted error message
    if gq_match:
        pattern_name = "'Good question'"
    else:
        assert deflection_match is not None
        matched_text = deflection_match.group(0)
        pattern_name = f"'{matched_text}'"

    # Increment circuit breaker on block
    if session_id:
        from __lib.circuit_breaker import increment_iteration

        increment_iteration(session_id)

    return {
        "allow": False,
        "reason": (
            f"DEFLECTION DETECTED: {pattern_name}\n\n"
            "Your response starts with a deflection pattern rather than executing.\n"
            "When a skill is invoked with sufficient context, execute directly.\n\n"
            "WRONG: 'Did you want me to plan that?' [asks permission instead of planning]\n"
            "RIGHT: [executes the skill immediately]\n\n"
            "WRONG: 'Good question. Let me explain...' [explains instead of answering]\n"
            "RIGHT: [direct answer, then context if needed]\n\n"
            "To disable: export STOP_GOOD_QUESTION_GATE_ENABLED=false"
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
