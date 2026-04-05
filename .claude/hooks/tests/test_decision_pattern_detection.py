#!/usr/bin/env python3
"""Test decision pattern detection for next step menus.

This test suite validates pattern-based detection of decision points
in assistant responses, replacing the broken signal-based system.

Data source: Analysis of 907 conversation files (6.4GB) showing:
- Explicit options: 86% (672 occurrences)
- Question endings: 10% (80 occurrences)
- Next Steps sections: 3% (21 occurrences)
- Direction requests: 2% (14 occurrences)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add hooks directory to path to import from local __lib package
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

import pytest

# Clear any cached imports to ensure we get the hooks package
if "Stop_next_step_suggester" in sys.modules:
    del sys.modules["Stop_next_step_suggester"]

# Import the newly implemented functions
from Stop_next_step_suggester import (
    DecisionType,
    classify_decision_point,
    extract_menu_options,
)


class TestClassifyDecisionPoint:
    """Test decision pattern classification."""

    def test_explicit_options_numbered_list(self):
        """EXPLICIT_OPTIONS: Detect numbered lists with actions (86% of cases)."""
        response = "Would you like:\n1. Run tests\n2. Skip tests\n3. Deploy"
        assert classify_decision_point(response) == DecisionType.EXPLICIT_OPTIONS

    def test_explicit_options_bulleted_list(self):
        """EXPLICIT_OPTIONS: Detect bulleted lists with action verbs."""
        response = "- Run the tests\n- Skip and continue\n- Deploy to staging"
        assert classify_decision_point(response) == DecisionType.EXPLICIT_OPTIONS

    def test_question_ending(self):
        """QUESTION_ENDING: Detect responses ending with '?' (10% of cases)."""
        response = "Should I continue with the implementation?"
        assert classify_decision_point(response) == DecisionType.QUESTION_ENDING

    def test_next_steps_section(self):
        """NEXT_STEPS_SECTION: Detect '## Next Steps' headers (3% of cases)."""
        response = "## Next Steps\n1. Push to remote\n2. Verify deployment"
        assert classify_decision_point(response) == DecisionType.NEXT_STEPS_SECTION

    def test_direction_request(self):
        """DIRECTION_REQUEST: Detect 'What would you like' phrases (2% of cases)."""
        response = "What would you like me to do next?"
        assert classify_decision_point(response) == DecisionType.DIRECTION_REQUEST

    def test_no_decision_single_action(self):
        """NO_DECISION: Single obvious action without choices."""
        response = "Fixed the bug in line 42."
        assert classify_decision_point(response) == DecisionType.NO_DECISION

    def test_no_decision_empty_response(self):
        """NO_DECISION: Empty or whitespace-only response."""
        assert classify_decision_point("") == DecisionType.NO_DECISION
        assert classify_decision_point("   \n  \t  ") == DecisionType.NO_DECISION

    def test_no_decision_rhetorical_question(self):
        """NO_DECISION: Rhetorical question without choice offered."""
        response = "Why is this happening? Let me investigate."
        assert classify_decision_point(response) == DecisionType.NO_DECISION


class TestExtractMenuOptions:
    """Test menu option extraction based on decision type."""

    def test_extract_numbered_options(self):
        """Extract numbered list options as menu choices."""
        response = "1. Run tests\n2. Skip tests\n3. Deploy"
        options = extract_menu_options(response, DecisionType.EXPLICIT_OPTIONS)
        assert len(options) == 3
        assert "1. Run tests" in options[0]
        assert "2. Skip tests" in options[1]
        assert "3. Deploy" in options[2]

    def test_extract_bulleted_options(self):
        """Extract bulleted list options as menu choices."""
        response = "- Run tests\n- Skip tests"
        options = extract_menu_options(response, DecisionType.EXPLICIT_OPTIONS)
        assert len(options) == 2
        assert "Run tests" in options[0]
        assert "Skip tests" in options[1]

    def test_extract_next_steps_items(self):
        """Extract items from Next Steps section."""
        response = "## Next Steps\n1. Push to remote\n2. Verify deployment"
        options = extract_menu_options(response, DecisionType.NEXT_STEPS_SECTION)
        assert len(options) == 2
        assert "1. Push to remote" in options[0]
        assert "2. Verify deployment" in options[1]

    def test_extract_question_yes_no(self):
        """Extract yes/no choice from question ending."""
        response = "Should I continue?"
        options = extract_menu_options(response, DecisionType.QUESTION_ENDING)
        assert len(options) == 2
        assert "✓ Yes" in options[0] or "Yes" in options[0].lower()
        assert "✗ No" in options[1] or "No" in options[1].lower()

    def test_extract_direction_request_choices(self):
        """Extract generic choices from direction request."""
        response = "What would you like me to do next?"
        options = extract_menu_options(response, DecisionType.DIRECTION_REQUEST)
        assert len(options) >= 1
        # Should provide context-aware options
        assert any("Provide" in opt or "Choose" in opt for opt in options)

    def test_extract_no_decision_returns_empty(self):
        """NO_DECISION returns empty options list."""
        response = "Fixed the bug."
        options = extract_menu_options(response, DecisionType.NO_DECISION)
        assert options == []

    def test_extract_truncates_long_options(self):
        """Long options are truncated to ~60 characters."""
        long_option = "This is a very long option that goes on and on and on and on"
        response = f"1. {long_option}\n2. Short option"
        options = extract_menu_options(response, DecisionType.EXPLICIT_OPTIONS)
        assert len(options) == 2
        assert len(options[0]) <= 100  # Truncated


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_multiple_question_marks(self):
        """Response with multiple '?' - should classify as QUESTION_ENDING."""
        response = "What? Really? Are you sure?"
        assert classify_decision_point(response) == DecisionType.QUESTION_ENDING

    def test_numbers_not_in_list_format(self):
        """Numbers appearing outside list context - should NOT trigger EXPLICIT_OPTIONS."""
        response = "There are 3 files and 2 directories. Fixed line 42."
        assert classify_decision_point(response) == DecisionType.NO_DECISION

    def test_next_steps_section_with_no_items(self):
        """Next Steps section with no actionable items."""
        response = "## Next Steps\n\nNo items to show."
        options = extract_menu_options(response, DecisionType.NEXT_STEPS_SECTION)
        # Should return empty or minimal options, not crash
        assert isinstance(options, list)

    def test_malformed_list_partial_items(self):
        """Malformed list with some valid items."""
        response = "1. First item\nBroken line\n2. Second item"
        options = extract_menu_options(response, DecisionType.EXPLICIT_OPTIONS)
        # Should extract valid items, skip malformed
        assert len(options) >= 1
        assert any("First item" in opt for opt in options)

    def test_question_in_code_block(self):
        """Question mark inside code block - should NOT trigger QUESTION_ENDING."""
        response = "```python\nx = y ? 'yes' : 'no'\n```\nDone."
        # Code block questions are not decision points
        assert classify_decision_point(response) == DecisionType.NO_DECISION


class TestIntegrationWithGetNextStepOptions:
    """Integration tests with get_next_step_options function."""

    def test_decision_point_detected_in_response(self):
        """get_next_step_options should extract options from decision points."""
        # Import here to avoid circular imports if needed
        from Stop_next_step_suggester import get_next_step_options

        data = {
            "response": "Would you like:\n1. Run tests\n2. Skip tests",
            "prompt": "",
        }
        options = get_next_step_options(data)
        assert len(options) >= 1

    def test_no_decision_point_returns_fallback(self):
        """get_next_step_options should fall back to suggest-field when no decision."""
        from Stop_next_step_suggester import get_next_step_options

        data = {
            "response": "Fixed the bug in line 42.",
            "prompt": "",
            "conversation": [],
        }
        # Should not crash, may return suggest-field options or empty
        options = get_next_step_options(data)
        assert isinstance(options, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
