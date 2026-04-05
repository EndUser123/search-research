#!/usr/bin/env python3
"""Tests for Stop_good_question_gate.py

Tests the Good Question deflection detection gate.
"""

from Stop_good_question_gate import run


class TestBlockGoodQuestionDeflection:
    """Block leading 'Good question' deflection."""

    def test_leading_good_question_blocks(self):
        """Must block when response starts with 'Good question'."""
        data = {"response_text": "Good question. Let me explain the issue."}
        result = run(data)
        assert result["allow"] is False
        assert "DEFLECTION DETECTED" in result["reason"]

    def test_leading_good_question_with_period_blocks(self):
        """Must block 'Good question.' at start."""
        data = {"response_text": "Good question. The issue is X."}
        result = run(data)
        assert result["allow"] is False

    def test_leading_good_question_lowercase_blocks(self):
        """Must block 'good question' (lowercase) at start."""
        data = {"response_text": "good question. Let me explain."}
        result = run(data)
        assert result["allow"] is False

    def test_leading_good_question_uppercase_blocks(self):
        """Must block 'GOOD QUESTION' (uppercase) at start."""
        data = {"response_text": "GOOD QUESTION. Here's the answer."}
        result = run(data)
        assert result["allow"] is False


class TestAllowMidSentenceGoodQuestion:
    """Allow mid-sentence 'Good question' usage."""

    def test_good_question_after_em_dash_allows(self):
        """Must allow 'Good question —' mid-sentence."""
        data = {"response_text": "The root cause is X. Good question — the fix is Y."}
        result = run(data)
        assert result["allow"] is True

    def test_good_question_after_comma_allows(self):
        """Must allow 'Good question,' mid-sentence."""
        data = {"response_text": "The root cause is X. Good question, here's Y."}
        result = run(data)
        assert result["allow"] is True

    def test_good_question_within_sentence_allows(self):
        """Must allow 'Good question' in middle of sentence."""
        data = {"response_text": "Addressing your concern: Good question about the timeout."}
        result = run(data)
        # This is not at the very start after stripping
        assert result["allow"] is True


class TestEdgeCases:
    """Edge cases."""

    def test_empty_response_allows(self):
        """Empty response should be allowed."""
        data = {"response_text": ""}
        result = run(data)
        assert result["allow"] is True

    def test_short_response_allows(self):
        """Very short response should be allowed."""
        data = {"response_text": "Hi"}
        result = run(data)
        assert result["allow"] is True

    def test_good_question_not_at_start_allows(self):
        """'Good question' not at start should be allowed."""
        data = {"response_text": "Let me answer. Good question about the fix."}
        result = run(data)
        assert result["allow"] is True

    def test_gate_disabled_allows(self, monkeypatch):
        """When gate is disabled, should allow everything."""
        monkeypatch.setenv("STOP_GOOD_QUESTION_GATE_ENABLED", "false")
        data = {"response_text": "Good question. Let me explain."}
        result = run(data)
        assert result["allow"] is True
        assert "Gate disabled" in result["reason"]

    def test_multiline_response_good_question_at_start_blocks(self):
        """'Good question' at start of multiline response blocks."""
        data = {"response_text": "Good question.\n\nLet me explain the issue."}
        result = run(data)
        assert result["allow"] is False
