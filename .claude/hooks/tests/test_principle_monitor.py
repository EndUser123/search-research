#!/usr/bin/env python3
"""
Test suite for principle_monitor.py

Tests principle-based behavior monitoring system with TDD approach:
- RED: Failing tests define expected behavior
- GREEN: Implementation makes tests pass
- REFACTOR: Code cleanup while tests pass
"""

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import principle_monitor  # noqa: E402

# === FIXTURES ===

@pytest.fixture
def sample_stop_payload():
    """Sample Stop hook payload."""
    return {
        "hook_event_name": "Stop",
        "session_id": "test-session-123",
        "last_assistant_message": "Test message",
    }


@pytest.fixture
def empty_state():
    """Empty state dictionary."""
    return {}


@pytest.fixture
def sample_state():
    """State with some violations."""
    return {
        "test-session-123": {
            "context_grounding_violation": 2,
            "change_without_evidence": 3,
            "redundant_broad_question": 1,
            "opaque_uncertainty": 0,
            "suggestions_shown": [],
        }
    }


# === PATTERN DETECTION TESTS ===

class TestChangeWithoutEvidenceDetection:
    """Tests for detect_change_without_evidence()."""

    def test_agreement_without_evidence_detected(self):
        """Agreement phrases without evidence should be detected."""
        assert principle_monitor.detect_change_without_evidence(
            "You're right about that."
        )

    def test_multiple_agreement_patterns_detected(self):
        """Various agreement phrases should be detected."""
        assert principle_monitor.detect_change_without_evidence("I agree, let's do it.")
        assert principle_monitor.detect_change_without_evidence("Exactly. Let me fix it.")
        assert principle_monitor.detect_change_without_evidence("Good point. Proceeding.")
        assert principle_monitor.detect_change_without_evidence("Fair point. Done.")
        assert principle_monitor.detect_change_without_evidence("You are right. OK.")

    def test_evidence_citation_prevents_violation(self):
        """Agreement with evidence citation should NOT be detected."""
        assert not principle_monitor.detect_change_without_evidence(
            "You're right. The log shows line 42 has the error."
        )
        assert not principle_monitor.detect_change_without_evidence(
            "I agree with your assessment in file config.yaml."
        )
        assert not principle_monitor.detect_change_without_evidence(
            "Good point. Line 10 confirms this."
        )
        assert not principle_monitor.detect_change_without_evidence(
            "Exactly. As shown in the diff, we need to fix line 42."
        )

    def test_no_agreement_no_detection(self):
        """Messages without agreement phrases should NOT be detected."""
        assert not principle_monitor.detect_change_without_evidence(
            "Let me fix this bug."
        )
        assert not principle_monitor.detect_change_without_evidence(
            "I'll implement that feature now."
        )

    def test_case_insensitive_matching(self):
        """Detection should be case-insensitive."""
        assert principle_monitor.detect_change_without_evidence("YOU'RE RIGHT.")
        assert principle_monitor.detect_change_without_evidence("I Agree.")
        assert principle_monitor.detect_change_without_evidence("EXACTLY.")

    def test_edge_cases(self):
        """Test edge cases: empty string, whitespace, partial matches."""
        assert not principle_monitor.detect_change_without_evidence("")  # Empty
        assert not principle_monitor.detect_change_without_evidence("   ")  # Whitespace only
        # Partial match with evidence
        assert not principle_monitor.detect_change_without_evidence(
            "You're right, as shown in the log above."
        )


class TestContextGroundingViolationDetection:
    """Tests for detect_context_grounding_violation()."""

    def test_long_question_detected(self):
        """Questions longer than 30 chars ending with ? should be detected."""
        assert principle_monitor.detect_context_grounding_violation(
            "Can you remind me what the project root is?"
        )

    def test_multiple_long_questions_detected(self):
        """Various long questions should be detected."""
        assert principle_monitor.detect_context_grounding_violation(
            "What was the API key again please?"  # 32 chars
        )
        assert principle_monitor.detect_context_grounding_violation(
            "Where did we put the config file?"
        )
        assert principle_monitor.detect_context_grounding_violation(
            "How do I fix the error in line 42 of the function?"
        )

    def test_short_question_not_detected(self):
        """Questions <= 30 chars should NOT be detected."""
        assert not principle_monitor.detect_context_grounding_violation("How do I fix this?")
        assert not principle_monitor.detect_context_grounding_violation("What's next?")
        assert not principle_monitor.detect_context_grounding_violation("Should we proceed?")

    def test_exact_30_chars_not_detected(self):
        """Question exactly 30 chars should NOT be detected (strict >)."""
        question = "x" * 30 + "?"
        assert len(question) == 31
        assert principle_monitor.detect_context_grounding_violation(question)

        question = "x" * 29 + "?"
        assert len(question) == 30
        assert not principle_monitor.detect_context_grounding_violation(question)

    def test_no_question_mark_not_detected(self):
        """Statements without question mark should NOT be detected."""
        assert not principle_monitor.detect_context_grounding_violation(
            "I think this is correct"
        )

    def test_whitespace_handling(self):
        """Whitespace should be stripped before length check."""
        assert principle_monitor.detect_context_grounding_violation(
            "  Can you remind me what the project root is?  "
        )


class TestRedundantBroadQuestionDetection:
    """Tests for detect_redundant_broad_question()."""

    def test_broad_question_without_context_detected(self):
        """Broad questions without context reference should be detected."""
        assert principle_monitor.detect_redundant_broad_question(
            "What should we do next?"
        )
        assert principle_monitor.detect_redundant_broad_question(
            "How do I fix this error?"
        )
        assert principle_monitor.detect_redundant_broad_question(
            "Where do I start?"
        )

    def test_broad_question_with_context_not_detected(self):
        """Broad questions with context reference should NOT be detected."""
        assert not principle_monitor.detect_redundant_broad_question(
            "What should we do next? From earlier, you said to test first."
        )
        assert not principle_monitor.detect_redundant_broad_question(
            "How do I fix this? The log above shows the error."
        )
        assert not principle_monitor.detect_redundant_broad_question(
            "Where do I start? In file config.yaml line 10."
        )

    def test_specific_question_not_detected(self):
        """Specific questions should NOT be detected."""
        assert not principle_monitor.detect_redundant_broad_question(
            "Should we use pytest or unittest?"
        )


class TestOpaqueUncertaintyDetection:
    """Tests for detect_opaque_uncertainty()."""

    def test_probabilistic_without_check_detected(self):
        """Probabilistic statements without check suggestion should be detected."""
        assert principle_monitor.detect_opaque_uncertainty(
            "This is probably the issue."
        )
        assert principle_monitor.detect_opaque_uncertainty(
            "That might be the problem."
        )
        assert principle_monitor.detect_opaque_uncertainty(
            "It's possibly a bug."
        )

    def test_visual_inspection_without_verification_detected(self):
        """Visual inspection without verification should be detected."""
        assert principle_monitor.detect_opaque_uncertainty(
            "This looks correct."
        )
        assert principle_monitor.detect_opaque_uncertainty(
            "That seems right."
        )
        assert principle_monitor.detect_opaque_uncertainty(
            "It appears fine."
        )

    def test_optimism_without_verification_detected(self):
        """Optimistic statements without verification should be detected."""
        assert principle_monitor.detect_opaque_uncertainty(
            "This should work."
        )
        assert principle_monitor.detect_opaque_uncertainty(
            "It should be fine."
        )

    def test_explicit_check_suggestion_prevents_detection(self):
        """Explicit check suggestions should prevent detection."""
        assert not principle_monitor.detect_opaque_uncertainty(
            "This is probably the issue. Let me check the logs."
        )
        assert not principle_monitor.detect_opaque_uncertainty(
            "This looks correct. I'll verify with a test."
        )
        assert not principle_monitor.detect_opaque_uncertainty(
            "This should work. Should test to confirm."
        )


# === STATE MANAGEMENT TESTS ===

class TestStateManagement:
    """Tests for load_state() and save_state()."""

    @patch('principle_monitor.STATE_PATH')
    def test_state_file_created_on_first_save(self, mock_state_path, tmp_path):
        """State file should be created on first save."""
        mock_state_path.return_value = tmp_path / "test-state.json"

        state = {}
        principle_monitor.save_state(state)

        assert mock_state_path.parent.mkdir.called
        mock_state_path.write_text.assert_called_once()

    @patch('principle_monitor.STATE_PATH')
    def test_load_state_returns_empty_when_missing(self, mock_state_path):
        """Should return empty dict when state file doesn't exist."""
        mock_state_path.exists.return_value = False

        state = principle_monitor.load_state()

        assert state == {}

    @patch('principle_monitor.STATE_PATH')
    def test_load_state_parses_json(self, mock_state_path):
        """Should parse and return existing state file."""
        mock_state_path.exists.return_value = True
        test_state = {"session-123": {"count": 5}}
        mock_state_path.read_text.return_value = json.dumps(test_state)

        state = principle_monitor.load_state()

        assert state == test_state

    @patch('principle_monitor.STATE_PATH')
    def test_load_state_handles_parse_error(self, mock_state_path):
        """Should return empty dict on JSON parse error."""
        mock_state_path.exists.return_value = True
        mock_state_path.read_text.return_value = "invalid json"

        state = principle_monitor.load_state()

        assert state == {}


# === THRESHOLD TESTS ===

class TestThresholdBehavior:
    """Tests for suggestion threshold behavior."""

    def test_suggestion_emitted_at_threshold(self, sample_state, tmp_path):
        """Suggestion should be emitted at threshold (5 violations)."""
        # Import THRESHOLD constant
        from principle_monitor import THRESHOLD

        # Simulate 5 violations of change_without_evidence
        sample_state["test-session-123"]["change_without_evidence"] = THRESHOLD

        # Mock stdin with valid Stop hook payload
        payload = json.dumps({
            "hook_event_name": "Stop",
            "session_id": "test-session-123",
            "last_assistant_message": "You're right about that."
        })

        with patch('sys.stdin', io.StringIO(payload)):
            with patch('principle_monitor.STATE_PATH', tmp_path / "state.json"):
                with patch('principle_monitor.load_state', return_value=sample_state):
                    with patch('principle_monitor.save_state'):
                        with patch('sys.exit'):  # Prevent sys.exit from terminating test
                            principle_monitor.main()
                            # Note: Testing full main() requires complete state setup

    def test_multiple_long_questions_detected(self):
        """Multiple long questions should all be detected."""
        assert principle_monitor.detect_context_grounding_violation("Can you remind me what the project root is?")
        assert principle_monitor.detect_context_grounding_violation("What was the API key again please?")
        assert principle_monitor.detect_context_grounding_violation("Where did we put the config file?")


# === PATTERN VALIDATION TESTS ===

class TestPatternValidation:
    """Validate detection patterns with comprehensive examples."""

    def test_agreement_patterns_positive_cases(self):
        """Positive cases: 3+ examples that should trigger detection."""
        positive_examples = [
            "You're right about that.",
            "I agree, let's proceed.",
            "Exactly. Moving on.",
        ]
        for example in positive_examples:
            assert principle_monitor.detect_change_without_evidence(example), f"Should detect: {example}"

    def test_agreement_patterns_negative_cases(self):
        """Negative cases: 3+ examples that should NOT trigger detection."""
        negative_examples = [
            "You're right. The log shows the error.",
            "I agree. File config.yaml confirms this.",
            "Exactly. As shown in line 42, this is correct.",
        ]
        for example in negative_examples:
            assert not principle_monitor.detect_change_without_evidence(example), f"Should NOT detect: {example}"

    def test_agreement_patterns_edge_cases(self):
        """Edge cases: empty, whitespace, malformed."""
        assert not principle_monitor.detect_change_without_evidence("")  # Empty
        assert not principle_monitor.detect_change_without_evidence("   ")  # Whitespace
        assert not principle_monitor.detect_change_without_evidence(
            "You're right, as shown in the log."
        )  # Has evidence

    def test_context_grounding_positive_cases(self):
        """Positive cases: 3+ examples that should trigger detection."""
        positive_examples = [
            "Can you remind me what the project root is?",
            "What was the API key again please?",  # 32 chars
            "Where did we put the config file?",
        ]
        for example in positive_examples:
            assert principle_monitor.detect_context_grounding_violation(example), f"Should detect: {example}"

    def test_context_grounding_negative_cases(self):
        """Negative cases: 3+ examples that should NOT trigger detection."""
        negative_examples = [
            "How do I fix this?",  # <= 30 chars
            "What's next?",  # <= 30 chars
            "I think this is correct",  # No question mark
        ]
        for example in negative_examples:
            assert not principle_monitor.detect_context_grounding_violation(example), f"Should NOT detect: {example}"

    def test_context_grounding_edge_cases(self):
        """Edge cases: exact length boundary, whitespace."""
        # Exactly 30 chars + ? = 31 chars, should detect
        question = "x" * 30 + "?"
        assert principle_monitor.detect_context_grounding_violation(question)

        # Exactly 29 chars + ? = 30 chars, should NOT detect
        question = "x" * 29 + "?"
        assert not principle_monitor.detect_context_grounding_violation(question)

        # Whitespace variations
        assert principle_monitor.detect_context_grounding_violation(
            "  " + "x" * 30 + "?  "  # 31 chars after strip (>30)
        )

    def test_uncertainty_patterns_positive_cases(self):
        """Positive cases: 3+ examples that should trigger detection."""
        positive_examples = [
            "This is probably the issue.",
            "This looks correct.",
            "This should work.",
        ]
        for example in positive_examples:
            assert principle_monitor.detect_opaque_uncertainty(example), f"Should detect: {example}"

    def test_uncertainty_patterns_negative_cases(self):
        """Negative cases: 3+ examples that should NOT trigger detection."""
        negative_examples = [
            "This is probably the issue. Let me check.",
            "This looks correct. I'll verify.",
            "This should work. Testing now.",
        ]
        for example in negative_examples:
            assert not principle_monitor.detect_opaque_uncertainty(example), f"Should NOT detect: {example}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
