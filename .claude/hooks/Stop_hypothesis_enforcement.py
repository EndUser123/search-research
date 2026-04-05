#!/usr/bin/env python3
"""Stop hook for hypothesis enforcement.

Blocks 'root cause:' statements without preceding 'Hypothesis:' + verification evidence.

From ADR-20260325-reasoning-hygiene-hooks.md

Phase 1 proof-of-concept implementation using regex detection.
Future phases may use Prompt hooks for more nuanced evaluation.
"""

from __future__ import annotations

import os
import re
from typing import Any

_ROOT_CAUSE_PATTERN = re.compile(r"(?i)\broot\s+cause\s*[:]", re.IGNORECASE)

_HYPOTHESIS_PATTERN = re.compile(r"(?i)\bhypothesis\s*[:]", re.IGNORECASE)

# Patterns that indicate verification evidence in the response
_VERIFICATION_EVIDENCE_PATTERNS = [
    re.compile(r"(?i)\b(?:tool\s+)?output[:\s]", re.IGNORECASE),
    re.compile(r"(?i)\b(?:test\s+)?result[s]?[:\s]", re.IGNORECASE),
    re.compile(
        r"(?i)\bfrom\s+(?:the\s+)?(?:above\s+)?(?:tool\s+)?(?:output|execution|running)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?i)\b(pytest|test|bash|grep|read|ls|glob)\s+(?:shows?|shows|output|result)",
        re.IGNORECASE,
    ),
    re.compile(r"(?i)```", re.IGNORECASE),  # Code block indicating tool output
    re.compile(
        r"(?i)\bfile\s*[:\(]", re.IGNORECASE
    ),  # "file:" or "file (" indicating read evidence
    re.compile(r"(?i)\b(error|exception|traceback)[:\s]", re.IGNORECASE),
]


def _is_gate_enabled() -> bool:
    """Check if this gate is enabled via environment variable."""
    return os.environ.get("REASONING_HYGIENE_ENABLED", "true").lower() == "true"


def _has_verification_evidence(
    response_text: str, hypothesis_pos: int, root_cause_pos: int
) -> bool:
    """Check if verification evidence exists between hypothesis and root cause.

    Args:
        response_text: Full response text
        hypothesis_pos: Position of last hypothesis before root cause
        root_cause_pos: Position of root cause statement

    Returns:
        True if evidence patterns found between hypothesis and root cause
    """
    text_between = response_text[hypothesis_pos:root_cause_pos]

    for pattern in _VERIFICATION_EVIDENCE_PATTERNS:
        if pattern.search(text_between):
            return True

    return False


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate if response contains 'root cause:' without proper hypothesis structure.

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

        # Check if circuit breaker has tripped (too many blocks)
        from __lib.circuit_breaker import should_allow_continue

        if should_allow_continue(session_id, stop_hook_active=True):
            return {"allow": True, "reason": "Circuit breaker tripped"}

    response_text = data.get("response_text", "")

    if not response_text or len(response_text.strip()) < 20:
        return {"allow": True, "reason": "Response too short to analyze"}

    root_cause_match = _ROOT_CAUSE_PATTERN.search(response_text)
    if not root_cause_match:
        return {"allow": True, "reason": "No root cause statement detected"}

    root_cause_pos = root_cause_match.start()

    hypothesis_matches = list(_HYPOTHESIS_PATTERN.finditer(response_text))

    # Find the last hypothesis BEFORE root cause
    hypothesis_before_root_cause = None
    for m in reversed(hypothesis_matches):
        if m.start() < root_cause_pos:
            hypothesis_before_root_cause = m
            break

    if not hypothesis_before_root_cause:
        # Increment circuit breaker on block
        if session_id:
            from __lib.circuit_breaker import increment_iteration

            increment_iteration(session_id)
        return {
            "allow": False,
            "reason": (
                "UNVERIFIED HYPOTHESIS DETECTED\n\n"
                "You stated 'root cause:' without:\n"
                "1. Preceding 'Hypothesis:' statement\n"
                "2. Verification evidence (tool output, test results, file read)\n\n"
                "Structure your reasoning:\n"
                "  Hypothesis: X might be broken because Y\n"
                "  Evidence: [tool output showing Y]\n"
                "  Conclusion: Confirmed — root cause is Y\n\n"
                "To disable: export REASONING_HYGIENE_ENABLED=false"
            ),
        }

    hypothesis_pos = hypothesis_before_root_cause.start()

    if not _has_verification_evidence(response_text, hypothesis_pos, root_cause_pos):
        # Increment circuit breaker on block
        if session_id:
            from __lib.circuit_breaker import increment_iteration

            increment_iteration(session_id)
        return {
            "allow": False,
            "reason": (
                "MISSING VERIFICATION EVIDENCE\n\n"
                "You stated 'Hypothesis:' but showed no verification evidence\n"
                "before stating 'root cause:'.\n\n"
                "Required structure:\n"
                "  Hypothesis: X might be broken because Y\n"
                "  Evidence: [tool output showing the issue]\n"
                "  Conclusion: Confirmed — root cause is Y\n\n"
                "Show evidence (tool output, test results, file read) between\n"
                "Hypothesis and root cause statements.\n\n"
                "To disable: export REASONING_HYGIENE_ENABLED=false"
            ),
        }

    return {"allow": True, "reason": "Hypothesis structure verified"}


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
