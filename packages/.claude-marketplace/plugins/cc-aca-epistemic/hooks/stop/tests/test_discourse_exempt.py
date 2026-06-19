"""Regression test: discourse/hypothetical exemption in StopHook_unverified_stance.

Falsification conditionals and meta-commentary about the dialogue/contract must NOT
be gated as ungrounded confident claims, while genuine factual claims still are.
"""
import re

# Pattern mirrors _DISCOURSE_EXEMPT in StopHook_unverified_stance.py
_DISCOURSE_EXEMPT = re.compile(
    r"\b(?:would|could|might)\s+be\s+(?:wrong|incorrect|a\s+mistake|false|invalid)\s+if\b"
    r"|\bwhat\s+would\s+(?:invalidate|falsify|change|disprove)\b"
    r"|\bby\s+design\b"
    r"|\bhypothetical(?:ly)?\b"
    r"|\bthe\s+(?:contract|rubric|protocol|instruction|guideline|spec)s?\s+(?:asks?|require|say|want)"
    r"|\bfor\s+the\s+record\b",
    re.IGNORECASE,
)


def _exempt(text: str) -> bool:
    return bool(text and _DISCOURSE_EXEMPT.search(text))


# The two real false positives observed this session — must now be exempt.
FALSE_POSITIVES = [
    "This would be wrong if you'd rather consolidate to a single layer and are "
    "willing to re-encode your routes",
    "It is hypothetical by design (the contract asks me to name what would "
    "invalidate the recommendation)",
]

# Genuine ungrounded factual claims — must remain gated (not exempt).
GENUINE_CLAIMS = [
    "The file has 3 consumers",
    "bifrost_tool_shim.js line 214 pipes the response through unchanged",
    "CCR supports passthrough forwarding to an upstream gateway",
    "The hook fires on every Stop event",
]


def test_false_positives_now_exempt():
    for t in FALSE_POSITIVES:
        assert _exempt(t), f"should be exempt: {t!r}"


def test_genuine_claims_still_gated():
    for t in GENUINE_CLAIMS:
        assert not _exempt(t), f"should NOT be exempt: {t!r}"


if __name__ == "__main__":
    test_false_positives_now_exempt()
    test_genuine_claims_still_gated()
    print("PASS: discourse exemption precise (2 FPs exempt, 4 genuine claims gated)")
