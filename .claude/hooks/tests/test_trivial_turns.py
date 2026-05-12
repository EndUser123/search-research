#!/usr/bin/env python3
"""Tests for trivial_turns.py — trivial exchange detection for gate softening."""
from __future__ import annotations

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))

from trivial_turns import is_trivial_exchange, _NUMERIC_RESPONSE_RE, _BOOL_RESPONSE_RE, _SHORT_ACK_RE, _SMOKE_TEST_RE


class TestTrivialSignals:
    """Signal-level unit tests."""

    def test_numeric_pattern_matches_integer(self):
        assert _NUMERIC_RESPONSE_RE.match("4")
        assert _NUMERIC_RESPONSE_RE.match("  42  ")

    def test_numeric_pattern_rejects_text(self):
        assert not _NUMERIC_RESPONSE_RE.match("4 files")
        assert not _NUMERIC_RESPONSE_RE.match("the answer is 4")

    def test_bool_pattern_matches(self):
        assert _BOOL_RESPONSE_RE.match("true")
        assert _BOOL_RESPONSE_RE.match("True")
        assert _BOOL_RESPONSE_RE.match("yes")
        assert _BOOL_RESPONSE_RE.match("y")
        assert _BOOL_RESPONSE_RE.match("no")
        assert _BOOL_RESPONSE_RE.match("off")

    def test_short_ack_pattern_matches(self):
        assert _SHORT_ACK_RE.match("ok")
        assert _SHORT_ACK_RE.match("OK")
        assert _SHORT_ACK_RE.match("done")
        assert _SHORT_ACK_RE.match("thanks")
        assert _SHORT_ACK_RE.match("sure")
        assert _SHORT_ACK_RE.match("yep")
        assert _SHORT_ACK_RE.match("lgtm")
        # Extended patterns
        assert _SHORT_ACK_RE.match("ty")
        assert _SHORT_ACK_RE.match("thx")
        assert _SHORT_ACK_RE.match("cheers")
        assert _SHORT_ACK_RE.match("noted")
        assert _SHORT_ACK_RE.match("got it")
        assert _SHORT_ACK_RE.match("understood")
        assert _SHORT_ACK_RE.match("makes sense")

    def test_smoke_test_pattern_matches(self):
        assert _SMOKE_TEST_RE.search("test m27")
        assert _SMOKE_TEST_RE.search("Test M27")
        assert _SMOKE_TEST_RE.search("prove you're working")
        assert _SMOKE_TEST_RE.search("smoke test")
        assert _SMOKE_TEST_RE.search("are you there")
        assert _SMOKE_TEST_RE.search("health check")

    def test_smoke_test_pattern_no_false_positives(self):
        # Smoke test RE is applied only to user_prompt[:40] in the function.
        # Here we test the RE itself against strings that shouldn't match.
        # (no smoke test signal words anywhere)
        assert not _SMOKE_TEST_RE.search("what is the weather today")
        assert not _SMOKE_TEST_RE.search("please ping the server later")
        assert not _SMOKE_TEST_RE.search("the health status is good")
        # "test" but wrong continuation (not m27/glm/claude/haiku/opus/sonnet)
        assert not _SMOKE_TEST_RE.search("test the integration fully")
        assert not _SMOKE_TEST_RE.search("test m27x")  # "m27" not m27


class TestIsTrivialExchange:
    """Integration tests for the full is_trivial_exchange() function."""

    def test_epistemic_skips_trivial_numeric_answer(self):
        """Numeric answer to simple prompt → trivial, no epistemic weight."""
        ctx = {"user_prompt": "what is 2+2", "response": "4", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "4")
        assert result is True
        assert reason == "bare_numeric"

    def test_epistemic_skips_trivial_numeric_bool(self):
        """Yes/no answer → trivial, matched as short acknowledgement."""
        ctx = {"user_prompt": "is it done", "response": "yes", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "yes")
        assert result is True
        assert reason in ("short_ack", "bare_numeric")  # bool OR ack pattern

    def test_epistemic_skips_control_turn(self):
        """Control turn → trivial via turn_mode."""
        ctx = {"user_prompt": "stop", "response": "stopping"}
        result, reason = is_trivial_exchange(ctx, "stopping", turn_mode="control")
        assert result is True
        assert reason == "control_mode"

    def test_reasoning_quality_skips_trivial_ack(self):
        """Short acknowledgement → trivial for reasoning quality gate."""
        ctx = {"user_prompt": "looks good", "response": "done", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "done")
        assert result is True
        assert reason == "short_ack"

    def test_epistemic_still_applies_for_contract_completion(self):
        """Contract completion even with short response → NOT trivial."""
        ctx = {"user_prompt": "finish the task", "response": "done", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "done", contract_active=True)
        assert result is False
        assert reason == "contract_active"

    def test_non_trivial_long_response_with_format(self):
        """Response with epistemic structure → not trivial."""
        ctx = {
            "user_prompt": "explain the bug",
            "response": "[FACT]\n- The null check was missing",
            "prompt": "",
        }
        result, reason = is_trivial_exchange(ctx, "[FACT]\n- The null check was missing")
        assert result is False
        assert reason == "not_trivial"

    def test_non_trivial_inference_tag(self):
        """Response with [INFERENCE] tag → not trivial."""
        ctx = {"user_prompt": "why did it crash", "response": "[INFERENCE]\n- memory leak", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "[INFERENCE]\n- memory leak")
        assert result is False
        assert reason == "not_trivial"

    def test_non_trivial_recommendation_tag(self):
        """Response with [RECOMMENDATION] tag → not trivial."""
        ctx = {"user_prompt": "what should we do", "response": "[RECOMMENDATION]\n- add retry logic", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "[RECOMMENDATION]\n- add retry logic")
        assert result is False
        assert reason == "not_trivial"

    def test_trivial_smoke_test_mid_prompt(self):
        """Smoke test in first 80 chars (not just first 40) → trivial."""
        ctx = {"user_prompt": "also test m27 and verify you're working", "response": "I am working.", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "I am working.")
        assert result is True
        assert reason == "smoke_test"

    def test_non_trivial_short_but_not_ack(self):
        """'done' to a substantive complex request → not trivial."""
        # Prompt must be >= 15 words for 'done' to be non-trivial
        ctx = {
            "user_prompt": "Analyze and fix the concurrency bug in the task scheduler where race conditions cause duplicate execution",
            "response": "done",
            "prompt": "",
        }
        result, reason = is_trivial_exchange(ctx, "done")
        assert result is False
        assert reason == "not_trivial"

    def test_non_trivial_ack_too_long(self):
        """Verbose acknowledgement > 80 chars → not trivial."""
        long_ack = "you're welcome, let me know if you need anything else! I am happy to help."
        ctx = {"user_prompt": "thanks", "response": long_ack, "prompt": ""}
        result, reason = is_trivial_exchange(ctx, long_ack)
        assert result is False
        assert reason == "not_trivial"

    def test_trivial_smoke_test(self):
        """Smoke test prompt → trivial."""
        ctx = {"user_prompt": "test m27", "response": "I am working correctly.", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "I am working correctly.")
        assert result is True
        assert reason == "smoke_test"

    def test_trivial_empty_response(self):
        """Empty response → not trivial (no content to evaluate)."""
        ctx = {"user_prompt": "say something", "response": "", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "")
        assert result is False
        assert reason == "empty response"

    def test_trivial_whitespace_only_response(self):
        """Whitespace-only response → not trivial."""
        ctx = {"user_prompt": "say something", "response": "   \n  ", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "   \n  ")
        assert result is False
        assert reason == "empty response"

    def test_trivial_numeric_complex_prompt(self):
        """Numeric answer to complex prompt still trivial (prompt_len check)."""
        complex_prompt = "Analyze the following codebase architecture and provide a detailed summary of the main components and their relationships: " + "x" * 200
        ctx = {"user_prompt": complex_prompt, "response": "42", "prompt": ""}
        result, reason = is_trivial_exchange(ctx, "42")
        # Complex prompt but bare numeric → still trivial
        assert result is True
        assert reason == "bare_numeric_simple_prompt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
