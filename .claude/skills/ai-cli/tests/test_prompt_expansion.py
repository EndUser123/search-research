"""Tests for prompt expansion function in ask_cli.py.

These tests verify that the expand_prompt function transforms simple queries
into detailed, structured prompts with specific requirements.

Run with: pytest P:/.claude/skills/ai-cli/tests/test_prompt_expansion.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from io import StringIO

from ai_cli import expand_prompt, prompt_with_expansion_option, show_prompt_options


class TestPromptExpansionBasic:
    """Tests for basic prompt expansion behavior."""

    def test_expand_prompt_transforms_simple_query(self):
        """
        Test that expand_prompt transforms a simple query into a detailed expanded prompt.

        Given: A simple query like "review the plan for gaps"
        When: expand_prompt is called with the query
        Then: The result should be an expanded prompt containing specific keywords
              - "citation" (for requiring citations)
              - "actionable" (for actionable items)
              - "specific" (for specific recommendations)
        """
        # Arrange
        simple_query = "review the plan for gaps"

        # Act
        expanded_prompt = expand_prompt(simple_query)

        # Assert - Verify the prompt is expanded (not just the original query)
        assert (
            expanded_prompt != simple_query
        ), "Expanded prompt should be different from the original query"

        # Assert - Verify the prompt contains the original query
        assert (
            simple_query.lower() in expanded_prompt.lower()
        ), f"Expanded prompt should contain the original query '{simple_query}'"

        # Assert - Verify expansion contains required keywords
        assert (
            "citation" in expanded_prompt.lower()
        ), "Expanded prompt should contain 'citation' for requiring source citations"
        assert (
            "actionable" in expanded_prompt.lower()
        ), "Expanded prompt should contain 'actionable' for actionable recommendations"
        assert (
            "specific" in expanded_prompt.lower()
        ), "Expanded prompt should contain 'specific' for specific recommendations"

    def test_expand_prompt_adds_format_requirements(self):
        """
        Test that expanded prompt includes format requirements.

        Given: A simple query
        When: expand_prompt is called
        Then: The result should include format/structure requirements
        """
        # Arrange
        simple_query = "explain the architecture"

        # Act
        expanded_prompt = expand_prompt(simple_query)

        # Assert - Verify format requirements are included
        # Check for common format-related keywords
        format_keywords = ["format", "structure", "output", "organized"]
        has_format_requirement = any(
            keyword in expanded_prompt.lower() for keyword in format_keywords
        )
        assert has_format_requirement, (
            f"Expanded prompt should include format/structure requirements. "
            f"Checked for: {format_keywords}"
        )

    def test_expand_prompt_includes_focus_areas(self):
        """
        Test that expanded prompt includes focus areas or guidance.

        Given: A simple query
        When: expand_prompt is called
        Then: The result should include focus areas for the LLM to consider
        """
        # Arrange
        simple_query = "analyze the code"

        # Act
        expanded_prompt = expand_prompt(simple_query)

        # Assert - Verify focus areas are included
        # Check for focus-related keywords
        focus_keywords = ["focus", "consider", "ensure", "address", "emphasize"]
        has_focus_area = any(keyword in expanded_prompt.lower() for keyword in focus_keywords)
        assert has_focus_area, (
            f"Expanded prompt should include focus areas. " f"Checked for: {focus_keywords}"
        )

    def test_expand_prompt_different_queries(self):
        """
        Test that expand_prompt works with various simple queries.

        Given: Different types of simple queries
        When: expand_prompt is called with each
        Then: Each should be expanded with the required keywords
        """
        # Arrange - Different query types
        test_queries = [
            "summarize the document",
            "find bugs in this code",
            "suggest improvements",
            "compare the approaches",
        ]

        required_keywords = ["citation", "actionable", "specific"]

        for query in test_queries:
            # Act
            expanded_prompt = expand_prompt(query)

            # Assert - Verify each required keyword is present
            for keyword in required_keywords:
                assert keyword in expanded_prompt.lower(), (
                    f"Query '{query}' expansion should contain '{keyword}'. "
                    f"Got: {expanded_prompt[:100]}..."
                )


class TestInvalidSelectionPromptsRetry:
    """Tests for invalid selection handling with retry prompt."""

    @patch("builtins.input")
    def test_invalid_selection_prompts_retry(self, mock_input):
        """
        Test that invalid selection (like "5" or "x") is rejected with retry.

        Given: An original query string
        When: User enters invalid choice ("5") then valid choice ("1")
        Then: Function should prompt for retry and return the expanded prompt
        """
        # Arrange
        original_query = "review the plan for gaps"

        # Mock input to return "5" (invalid), then "1" (valid)
        mock_input.side_effect = ["5", "1"]

        # Capture stdout to verify retry prompt
        from io import StringIO

        captured_output = StringIO()

        # Act
        with patch("sys.stdout", captured_output):
            result = prompt_with_expansion_option(original_query)

        # Assert - Verify the result is the expanded prompt (not original)
        assert result != original_query, (
            f"Should return expanded prompt after selecting '1', not original query. "
            f"Got: {result}"
        )

        # Assert - Verify the result contains expansion keywords
        assert "citation" in result.lower(), "Result should contain 'citation'"
        assert "actionable" in result.lower(), "Result should contain 'actionable'"

        # Assert - Verify input was called twice (once for invalid, once for valid)
        assert mock_input.call_count == 2, (
            f"input() should be called twice: first for invalid '5', "
            f"then for valid '1'. Got {mock_input.call_count} calls."
        )

        # Assert - Verify retry prompt was shown
        output = captured_output.getvalue()
        assert (
            "invalid" in output.lower()
            or "retry" in output.lower()
            or "try again" in output.lower()
        ), f"Should show retry prompt after invalid selection. " f"Output was: {output}"


class TestPromptExpansionSelection:
    """Tests for prompt expansion with user selection."""

    @patch("builtins.input", return_value="1")
    def test_select_expanded_prompt_uses_expanded_version(self, mock_input):
        """
        Test that when user selects option 1, expanded prompt is used.

        Given: A simple query and user is presented with a choice
        When: User selects option 1 (use expanded prompt)
        Then: The returned prompt should be the expanded version with detailed instructions,
              not just the original query.
        """
        # Arrange
        original_query = "review the plan for gaps"

        # Act
        # Assuming there's a function that prompts user and returns selected prompt
        # This test verifies the behavior when user selects option 1
        result_prompt = prompt_with_expansion_option(original_query)

        # Assert - Verify expanded prompt is returned
        assert result_prompt is not None, "Result prompt should not be None"
        assert (
            result_prompt != original_query
        ), "Result should be expanded prompt, not original query"

        # Assert - Verify it contains the detailed instructions
        # The expanded prompt should have more content than just the query
        assert len(result_prompt) > len(
            original_query
        ), "Expanded prompt should be longer than original query"

        # Assert - Verify it contains detailed instruction keywords
        detail_keywords = ["citation", "actionable", "specific"]
        for keyword in detail_keywords:
            assert (
                keyword in result_prompt.lower()
            ), f"Expanded prompt should contain '{keyword}' as detailed instruction"

        # Assert - Verify input was called for user selection
        mock_input.assert_called_once()


class TestShowPromptOptionsMenuDisplay:
    """Tests for show_prompt_options menu display and user selection."""

    @patch("builtins.input", return_value="1")
    def test_show_prompt_options_displays_menu(self, mock_input):
        """
        Test that show_prompt_options displays a numbered menu and returns selected prompt.

        Given: Two prompt options (expanded and original)
        When: show_prompt_options is called
        Then: Menu should be displayed with numbered options:
              - Option 1: expanded prompt
              - Option 2: original prompt
              - Option 3: custom prompt
              And: Should return the selected prompt based on user input
        """
        # Arrange
        expanded_prompt = (
            "Expanded: Please review the plan for gaps with citations and actionable items."
        )
        original_prompt = "review the plan for gaps"

        # Act
        with patch("sys.stdout", new=StringIO()) as fake_out:
            selected = show_prompt_options(expanded_prompt, original_prompt)
            output = fake_out.getvalue()

        # Assert - Verify menu was displayed with numbered options
        assert "1" in output, "Menu should display option 1"
        assert "2" in output, "Menu should display option 2"
        assert "3" in output, "Menu should display option 3"

        # Assert - Verify menu contains the prompts
        assert expanded_prompt in output, "Menu should display the expanded prompt"
        assert original_prompt in output, "Menu should display the original prompt"

        # Assert - Verify user input was called
        mock_input.assert_called_once()

        # Assert - Verify correct prompt was returned for choice '1'
        assert (
            selected == expanded_prompt
        ), f"Should return expanded prompt when user selects option 1, got: {selected}"

    @patch("builtins.input", return_value="2")
    def test_show_prompt_options_selects_original(self, mock_input):
        """
        Test that selecting option 2 returns the original prompt.

        Given: Two prompt options
        When: User enters '2' to select the original prompt
        Then: Function should return the original prompt
        """
        # Arrange
        expanded_prompt = "Expanded: detailed prompt with requirements"
        original_prompt = "simple query"

        # Act
        selected = show_prompt_options(expanded_prompt, original_prompt)

        # Assert
        assert (
            selected == original_prompt
        ), f"Should return original prompt when user selects option 2, got: {selected}"

    @patch("builtins.input")
    def test_show_prompt_options_selects_custom(self, mock_input):
        """
        Test that selecting option 3 prompts for custom input.

        Given: Two prompt options
        When: User enters '3' to enter a custom prompt
        Then: Function should prompt for custom input and return it
        """
        # Arrange
        expanded_prompt = "Expanded: detailed prompt"
        original_prompt = "simple query"
        custom_prompt = "my custom prompt"

        # Act - First call selects option 3, second call provides custom prompt
        mock_input.side_effect = ["3", custom_prompt]
        selected = show_prompt_options(expanded_prompt, original_prompt)

        # Assert
        assert (
            selected == custom_prompt
        ), f"Should return custom prompt when user selects option 3, got: {selected}"
        assert mock_input.call_count == 2, "input() should be called twice for option 3"

    @patch("builtins.input", return_value="invalid")
    def test_show_prompt_options_handles_invalid_input(self, mock_input):
        """
        Test that invalid input is handled gracefully.

        Given: Two prompt options
        When: User enters invalid input (not 1, 2, or 3)
        Then: Function should handle the error or prompt again
        """
        # Arrange
        expanded_prompt = "Expanded: detailed prompt"
        original_prompt = "simple query"

        # Act & Assert - This test documents expected behavior for invalid input
        # The current implementation should handle this case
        with pytest.raises((ValueError, KeyError, IndexError)):
            selected = show_prompt_options(expanded_prompt, original_prompt)


class TestPromptExpansionUserSelection:
    """Tests for user selection between expanded and original prompt."""

    @patch("builtins.input")
    def test_select_original_prompt_uses_simple_version(self, mock_input):
        """
        Test that when user selects option 2, the original (unexpanded) prompt is used.

        Given: A simple query like "explain recursion"
        When: User is prompted to choose and selects option "2"
        Then: The original (unexpanded) prompt is returned
              - The returned prompt should equal the original query
              - The returned prompt should NOT contain expansion keywords (citation, actionable, specific)
        """
        # Arrange
        original_prompt = "explain recursion"
        mock_input.return_value = "2"

        # Act
        result = prompt_with_expansion_option(original_prompt)

        # Assert - Verify original prompt is returned unchanged
        assert (
            result == original_prompt
        ), f"Expected original prompt '{original_prompt}', but got: '{result}'"

        # Assert - Verify the result does NOT contain expansion keywords
        expansion_keywords = ["citation", "actionable", "specific"]
        for keyword in expansion_keywords:
            assert (
                keyword.lower() not in result.lower()
            ), f"Original prompt should NOT contain expansion keyword '{keyword}'"
