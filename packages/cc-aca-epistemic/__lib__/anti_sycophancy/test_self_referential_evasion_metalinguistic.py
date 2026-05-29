#!/usr/bin/env python3
"""
Tests that self_referential_evasion patterns exempt metalinguistic usage.

ALLOW (metalinguistic/analytical context):
    - "The detector matched `hedge` in the transcript"
    - "[UNVERIFIED] claim at line 5"
    - "Pattern `hedge` triggers false positives"
    - "W2 verdict: matched [hedge] pattern"

BLOCK (actual self-referential evasion):
    - "This is somewhat of a hedge, but..."
    - "The claim remains unverified despite testing"
    - "I'm hedging here because I didn't check"
"""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_DIR))

from anti_sycophancy.lazy_closure_detector import detect_lazy_closure

# Tool usage marker to trigger self_referential_evasion scope guard
_TOOL_MARKER = "\nI edited the file and wrote the changes.\n"


class TestHedgeMetalinguisticExemption:
    """Backtick and bracket contexts exempt `hedge` from self_referential_evasion."""

    def test_backtick_hedge_allowed(self):
        result = detect_lazy_closure(
            "The detector matched `hedge` in the transcript." + _TOOL_MARKER
        )
        assert result is None, f"Backtick-wrapped 'hedge' should be exempt, got {result}"

    def test_bracket_hedge_allowed(self):
        result = detect_lazy_closure(
            "Pattern classification: [hedge] matched at line 405." + _TOOL_MARKER
        )
        assert result is None, f"Bracket-wrapped 'hedge' should be exempt, got {result}"

    def test_bare_hedge_blocked(self):
        result = detect_lazy_closure(
            "This is somewhat of a hedge, but the fix looks correct." + _TOOL_MARKER
        )
        assert result is not None, "Bare 'hedge' should still trigger evasion detection"
        assert result.pattern_type == "self_referential_evasion"

    def test_bare_hedges_blocked(self):
        result = detect_lazy_closure(
            "I have some hedges about this conclusion." + _TOOL_MARKER
        )
        assert result is not None, "'hedges' should still trigger evasion detection"
        assert result.pattern_type == "self_referential_evasion"


class TestUnverifiedMetalinguisticExemption:
    """Bracket context exempts `unverified` from self_referential_evasion."""

    def test_bracket_unverified_allowed(self):
        result = detect_lazy_closure(
            "[UNVERIFIED] claim at line 5, needs checking." + _TOOL_MARKER
        )
        assert result is None, f"[UNVERIFIED] evidence tag should be exempt, got {result}"

    def test_backtick_unverified_allowed(self):
        result = detect_lazy_closure(
            "The `unverified` pattern at line 406 matches too broadly." + _TOOL_MARKER
        )
        assert result is None, f"Backtick-wrapped 'unverified' should be exempt, got {result}"

    def test_bare_unverified_blocked(self):
        result = detect_lazy_closure(
            "The claim remains unverified despite running the tests." + _TOOL_MARKER
        )
        assert result is not None, "Bare 'unverified' should still trigger evasion detection"
        assert result.pattern_type == "self_referential_evasion"

    def test_sentence_unverified_blocked(self):
        result = detect_lazy_closure(
            "I should note that my analysis is unverified at this point." + _TOOL_MARKER
        )
        assert result is not None, "'is unverified' self-assessment should trigger"
        assert result.pattern_type == "self_referential_evasion"


class TestNoToolMarkerNoBlock:
    """Without tool usage marker, self_referential_evasion should not fire."""

    def test_bare_hedge_no_tools_allowed(self):
        result = detect_lazy_closure(
            "This is somewhat of a hedge, but the fix looks correct."
        )
        # Without tool marker, self_referential_evasion scope guard prevents firing
        assert result is None or result.pattern_type != "self_referential_evasion", (
            "Without tool marker, evasion should not fire"
        )
