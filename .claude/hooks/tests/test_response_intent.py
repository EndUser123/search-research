#!/usr/bin/env python3
"""Tests for response_intent - Gate coordination for meta/debug discussion."""
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib.response_intent import (
    IntentClass,
    classify_response_intent,
    is_meta_or_quoted_context,
    _strip_quoted,
)


class TestQuoteStripping:
    """Test that quoted/metadata regions are stripped before commitment detection."""

    def test_strips_inline_code(self):
        text = "The phrase `proceeding to implement` triggered the gate"
        stripped = _strip_quoted(text)
        assert "proceeding" not in stripped

    def test_strips_fenced_code_blocks(self):
        text = "```\nProceeding to implement\n```\nThis is normal text"
        stripped = _strip_quoted(text)
        assert "Proceeding" not in stripped
        assert "normal" in stripped

    def test_strips_double_quoted_strings(self):
        text = 'He said "Proceeding to implement" and left'
        stripped = _strip_quoted(text)
        assert "proceeding" not in stripped

    def test_strips_single_quoted_strings(self):
        text = "She said 'proceeding to execute' in the doc"
        stripped = _strip_quoted(text)
        assert "proceeding" not in stripped

    def test_strips_blockquote_lines(self):
        text = "> proceeding to implement\nNormal response here"
        stripped = _strip_quoted(text)
        assert "proceeding" not in stripped

    def test_strips_bullet_lines(self):
        text = "- proceeding to implement\nNow I'll actually do it"
        stripped = _strip_quoted(text)
        # Bullet line stripped, but "Now I'll actually do it" remains
        assert "actually" in stripped

    def test_strips_unicode_curly_double_quotes(self):
        text = 'He said "Proceeding to implement" and left'
        stripped = _strip_quoted(text)
        assert "Proceeding" not in stripped

    def test_strips_unicode_curly_single_quotes(self):
        text = "She said 'proceeding to execute' in the doc"
        stripped = _strip_quoted(text)
        assert "proceeding" not in stripped

    def test_strips_dollar_quoted_strings(self):
        text = "The pattern $Proceeding to implement$ matches"
        stripped = _strip_quoted(text)
        assert "Proceeding" not in stripped

    def test_strips_html_entity_double_quote(self):
        text = "The phrase &quot;Proceeding to implement&quot; was used"
        stripped = _strip_quoted(text)
        assert "Proceeding" not in stripped

    def test_strips_html_entity_apos(self):
        text = "The phrase &apos;Proceeding to implement&apos; was used"
        stripped = _strip_quoted(text)
        assert "Proceeding" not in stripped

    def test_strips_html_entity_hash39(self):
        text = "The phrase &#39;Proceeding to implement&#39; was used"
        stripped = _strip_quoted(text)
        assert "Proceeding" not in stripped


class TestMetaPatterns:
    """Test meta/debug discussion detection."""

    def test_detects_trigger_phrase_discussion(self):
        text = "The phrase 'want me to implement' triggered the gate"
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.GATE_DEBUG_META

    def test_detects_approval_gate_discussion(self):
        text = "I was blocked by IMPLEMENTATION WITHOUT APPROVAL"
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.GATE_DEBUG_META

    def test_detects_stop_hook_feedback(self):
        text = "Stop hook feedback:\nIMPLEMENTATION WITHOUT APPROVAL"
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.GATE_DEBUG_META

    def test_detects_trigger_analysis_question(self):
        text = "Can you show what text triggered the approval gate?"
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.GATE_DEBUG_META

    def test_detects_gate_debug_context(self):
        text = "The approval gate is blocking my response"
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.GATE_DEBUG_META

    def test_is_meta_returns_true_for_gate_discussion(self):
        text = "Which phrase triggered the approval gate?"
        assert is_meta_or_quoted_context(text) is True


class TestCommitmentPatterns:
    """Test that actual commitments are detected."""

    def test_detects_first_person_will_implement(self):
        text = "I will implement the fix."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.IMPLEMENTATION_COMMITMENT

    def test_detects_first_person_going_to_implement(self):
        text = "I am going to implement the solution now."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.IMPLEMENTATION_COMMITMENT

    def test_detects_let_me_implement(self):
        text = "Let me implement the changes."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.IMPLEMENTATION_COMMITMENT

    def test_detects_first_person_commit(self):
        text = "I will commit these changes now."
        result = classify_response_intent(text, "commit")
        assert result == IntentClass.COMMIT_COMMITMENT


class TestNeutralAnalysis:
    """Test that neutral responses pass through."""

    def test_neutral_architecture_discussion(self):
        text = "The architecture consists of three layers."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.NEUTRAL_ANALYSIS

    def test_neutral_implement_word_usage(self):
        text = "This implements the specification correctly."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.NEUTRAL_ANALYSIS

    def test_neutral_question_about_pattern(self):
        text = "What pattern should I use for this implementation?"
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.NEUTRAL_ANALYSIS

    def test_empty_response_is_neutral(self):
        result = classify_response_intent("")
        assert result == IntentClass.NEUTRAL_ANALYSIS


class TestCompletionReport:
    """Test completion report detection."""

    def test_detects_tests_passed(self):
        text = "All tests passed. Implementation complete."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.COMPLETION_REPORT

    def test_detects_verification_complete(self):
        text = "Verification complete - all checks pass."
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.COMPLETION_REPORT


class TestMixedContext:
    """Test mixed contexts with both quoted triggers and real commitments."""

    def test_quoted_trigger_only_no_commitment(self):
        text = 'The phrase "proceeding to implement" triggered the gate'
        result = classify_response_intent(text, "approval")
        assert result == IntentClass.GATE_DEBUG_META

    def test_quoted_trigger_plus_real_commitment(self):
        # Real commitment outside quote should still trigger
        text = 'The phrase "proceeding to implement" was in the text. Now I will implement the fix.'
        result = classify_response_intent(text, "approval")
        # The first-person "I will implement" in non-quoted text should detect commitment
        assert result == IntentClass.IMPLEMENTATION_COMMITMENT


class TestIsMetaOrQuotedContext:
    """Test the quick-check helper."""

    def test_returns_true_for_meta(self):
        text = "I was blocked by the approval gate"
        assert is_meta_or_quoted_context(text) is True

    def test_returns_false_for_commitment(self):
        text = "Proceeding to implement the changes now."
        assert is_meta_or_quoted_context(text) is False

    def test_returns_false_for_neutral(self):
        text = "The architecture is complete."
        assert is_meta_or_quoted_context(text) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
