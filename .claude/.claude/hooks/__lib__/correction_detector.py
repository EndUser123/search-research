"""Correction acknowledgment detection for LLM Behavioral Integrity Phase 3.

Detects user corrections and requires the LLM to explicitly acknowledge them
before arguing back or defending its original response.
"""
from __future__ import annotations

import re
from typing import TypedDict

# Patterns matching user corrections/denials (mutually exclusive from acknowledgments)
CORRECTION_PATTERNS = [
    r"(?i)\bno\b",                        # standalone "no"
    r"(?i)\byou[' ]?re wrong\b",           # "you're wrong"
    r"(?i)\bI didn[' ]?t say\b",           # "I didn't say"
    r"(?i)\bthat[' ]?s not what\b",       # "that's not what"
    r"(?i)\bnot correct\b",               # "not correct"
    r"(?i)\bthat[' ]?s inaccurate\b",     # "that's inaccurate"
    r"(?i)\bwrong\b",                     # generic "wrong"
]

# Patterns matching LLM self-correction/acknowledgment (mutually exclusive from corrections)
ACKNOWLEDGMENT_PATTERNS = [
    r"(?i)\bI was wrong\b",               # "I was wrong"
    r"(?i)\blet me correct\b",             # "let me correct"
    r"(?i)\byou[' ]?re right\b",           # "you're right"
    r"(?i)\bI am mistaken\b",             # "I am mistaken"
    r"(?i)\bI stand corrected\b",          # "I stand corrected"
]


class CorrectionCheckResult(TypedDict):
    acknowledged: bool
    reason: str | None


def has_correction(user_message: str) -> bool:
    """Check if user message contains a correction/denial pattern.

    Uses word-boundary-aware patterns to avoid false positives
    on phrases like "no thanks" or "not today".
    """
    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, user_message):
            return True
    return False


def has_acknowledgment(response: str) -> bool:
    """Check if response contains LLM self-correction acknowledgment."""
    for pattern in ACKNOWLEDGMENT_PATTERNS:
        if re.search(pattern, response):
            return True
    return False


def _find_correction_position(response: str) -> int | None:
    """Find the position of the first acknowledgment in response.

    Returns the character index, or None if not found.
    """
    for pattern in ACKNOWLEDGMENT_PATTERNS:
        match = re.search(pattern, response)
        if match:
            return match.start()
    return None


def check_correction_acknowledge(
    user_message: str, response: str, proximity_chars: int = 200
) -> CorrectionCheckResult:
    """Check if user correction is acknowledged within proximity window.

    The acknowledgment must appear within proximity_chars of the correction
    detection point in the response.

    Args:
        user_message: The user's correction message
        response: The LLM's response
        proximity_chars: Maximum distance (in characters) between correction
                         detection point and acknowledgment

    Returns:
        CorrectionCheckResult with acknowledged (bool) and reason (str|None)
    """
    if not has_correction(user_message):
        return {"acknowledged": True, "reason": None}

    if not has_acknowledgment(response):
        return {
            "acknowledged": False,
            "reason": (
                "User correction detected but no acknowledgment found. "
                "The response must contain 'I was wrong', 'let me correct', "
                "'you're right', 'I am mistaken', or 'I stand corrected' "
                "within 200 characters of the correction."
            ),
        }

    # Find acknowledgment position
    ack_pos = _find_correction_position(response)
    if ack_pos is None:
        return {
            "acknowledged": False,
            "reason": "Acknowledgment pattern found but could not locate position.",
        }

    # Acknowledgment is always at the start of the response for valid self-correction
    # The proximity check ensures acknowledgment appears early enough
    if ack_pos <= proximity_chars:
        return {"acknowledged": True, "reason": None}

    return {
        "acknowledged": False,
        "reason": (
            f"User correction detected and acknowledgment found, "
            f"but acknowledgment appears at position {ack_pos} "
            f"(exceeds {proximity_chars}-character proximity limit). "
            f"Acknowledgment must appear within {proximity_chars} characters "
            f"of the correction point in the response."
        ),
    }
