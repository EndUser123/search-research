#!/usr/bin/env python3
"""Tests for is_non_substantive_turn in shared_helpers.py"""

import sys
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from __lib.shared_helpers import is_non_substantive_turn


class TestIsNonSubstantive:
    """Test is_non_substantive_turn helper function."""

    # === TRUE CASES (non-substantive) ===

    def test_simple_greeting(self):
        assert is_non_substantive_turn("Hello! What are we working on today?") is True

    def test_hey_greeting(self):
        assert is_non_substantive_turn("Hey there! Ready when you are.") is True

    def test_got_it_short(self):
        assert is_non_substantive_turn("Got it, thanks!") is True

    def test_understood_short(self):
        assert is_non_substantive_turn("Understood. Let me know if you need anything.") is True

    def test_ok_alright(self):
        assert is_non_substantive_turn("Okay, sounds good!") is True

    def test_ready_phrase(self):
        assert is_non_substantive_turn("Ready when you are.") is True

    def test_hi_there(self):
        assert is_non_substantive_turn("Hi there! How can I help?") is True

    def test_greetings(self):
        assert is_non_substantive_turn("Greetings! What task shall we tackle?") is True

    def test_no_problem(self):
        assert is_non_substantive_turn("No problem, happy to help!") is True

    def test_perfect(self):
        assert is_non_substantive_turn("Perfect, let's get started!") is True

    # === FALSE CASES (substantive) ===

    def test_long_response(self):
        # > 20 words = substantive
        result = is_non_substantive_turn(
            "I analyzed the code and found several issues. The primary problem is "
            "a race condition in the thread pool initialization. This causes intermittent "
            "failures under heavy load. The fix requires restructuring the singleton pattern."
        )
        assert result is False

    def test_with_digits(self):
        # Digits suggest factual/technical content
        result = is_non_substantive_turn(
            "The error occurs on line 42 when processing null values."
        )
        assert result is False

    def test_with_because(self):
        # "because" = epistemic/causal marker
        result = is_non_substantive_turn(
            "This fails because the config file is missing the required API key."
        )
        assert result is False

    def test_with_should(self):
        # "should" = recommendation language
        result = is_non_substantive_turn(
            "You should add input validation before processing the request."
        )
        assert result is False

    def test_with_i_found(self):
        result = is_non_substantive_turn(
            "I found the issue in the authentication middleware."
        )
        assert result is False

    def test_with_tests_passed(self):
        result = is_non_substantive_turn(
            "The tests passed, which confirms the fix works correctly."
        )
        assert result is False

    def test_with_recommend(self):
        result = is_non_substantive_turn(
            "I recommend we use a more robust caching strategy."
        )
        assert result is False

    def test_with_caused_by(self):
        result = is_non_substantive_turn(
            "The crash was caused by an unhandled exception in the main loop."
        )
        assert result is False

    def test_with_indicates(self):
        result = is_non_substantive_turn(
            "The pattern indicates a deeper architectural issue that needs attention."
        )
        assert result is False

    def test_actual_code_analysis(self):
        # Real analytical response with mechanism
        result = is_non_substantive_turn(
            "The root cause is a deadlock in the connection pool when threads wait "
            "for available connections and the pool size is smaller than the number "
            "of concurrent requests. The fix is to increase the pool size or add "
            "a timeout with graceful degradation."
        )
        assert result is False

    def test_empty_string(self):
        assert is_non_substantive_turn("") is False

    def test_none_input(self):
        assert is_non_substantive_turn(None) is False

    def test_blockquote_stripped(self):
        # Blockquote markers mean it's a reply, not phatic
        result = is_non_substantive_turn("> Hello! What are we working on?")
        assert result is False

    def test_fifteen_words(self):
        # Exactly at boundary - should NOT be non-substantive (needs >=20 for exclusion)
        result = is_non_substantive_turn(
            "Hi there, thanks for the update. I will look into the issue now."
        )
        # At <20 words, must also match phatic pattern
        assert result is True  # "Hi there" matches greeting pattern

    def test_exactly_twenty_words(self):
        # 20 words = exclusion zone, not non-substantive
        words = "The " * 19 + "issue."
        assert len(words.split()) == 20
        result = is_non_substantive_turn(words)
        assert result is False  # 20 words = excluded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])