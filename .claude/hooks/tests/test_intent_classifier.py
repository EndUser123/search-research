#!/usr/bin/env python3
"""Tests for intent_classifier hook.

These tests verify the intent_classifier's ability to distinguish between:
1. Topic inquiry: "tell me about /s" → returns True
2. Command invocation: "/s" → returns False

The intent_classifier hook is part of the UserPromptSubmit event system.
"""

import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest


class TestTopicInquiryDetection:
    """Tests for detecting topic inquiry about slash commands."""

    def test_tell_me_about_pattern(self):
        """Test that 'tell me about /s' is detected as topic inquiry.

        Given: A prompt asking about a slash command
        When: The prompt contains "tell me about /s"
        Then: is_topic_inquiry() returns True
        """
        # This will fail because intent_classifier doesn't exist yet
        from UserPromptSubmit import intent_classifier

        prompt = "tell me about /s"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for topic inquiry pattern, got {result}"

    def test_what_is_pattern(self):
        """Test that 'what is /s' is detected as topic inquiry.

        Given: A prompt asking what a slash command is
        When: The prompt contains "what is /s"
        Then: is_topic_inquiry() returns True
        """
        from UserPromptSubmit import intent_classifier

        prompt = "what is /s"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for 'what is' pattern, got {result}"

    def test_find_information_about_pattern(self):
        """Test that 'find information about /s' is detected as topic inquiry.

        Given: A prompt asking to find information about a slash command
        When: The prompt contains "find information about /s"
        Then: is_topic_inquiry() returns True
        """
        from UserPromptSubmit import intent_classifier

        prompt = "find information about /s"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for 'find information about' pattern, got {result}"

    def test_usage_and_frictions_pattern(self):
        """Test that '/s usage and frictions' is detected as topic inquiry.

        Given: A prompt asking about usage and frictions
        When: The prompt contains "/s usage and frictions"
        Then: is_topic_inquiry() returns True
        """
        from UserPromptSubmit import intent_classifier

        prompt = "/s usage and frictions"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for 'usage and frictions' pattern, got {result}"

    def test_errors_regarding_pattern(self):
        """Test that 'errors from today regarding /s' is detected as topic inquiry.

        Given: A prompt asking about errors related to a slash command
        When: The prompt contains "errors from today regarding /s"
        Then: is_topic_inquiry() returns True
        """
        from UserPromptSubmit import intent_classifier

        prompt = "errors from today regarding /s"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for 'errors regarding' pattern, got {result}"


class TestCommandDetection:
    """Tests for detecting command invocation vs topic inquiry."""

    def test_bare_slash_command(self):
        """Test that '/s' alone is NOT a topic inquiry.

        Given: A prompt that is just a slash command
        When: The prompt is "/s"
        Then: is_topic_inquiry() returns False
        """
        from UserPromptSubmit import intent_classifier

        prompt = "/s"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False for bare slash command, got {result}"

    def test_slash_command_with_args(self):
        """Test that '/s args' is NOT a topic inquiry.

        Given: A prompt invoking a slash command with arguments
        When: The prompt is "/s args"
        Then: is_topic_inquiry() returns False
        """
        from UserPromptSubmit import intent_classifier

        prompt = "/s args"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False for slash command with args, got {result}"

    def test_run_slash_command(self):
        """Test that 'run /s' is NOT a topic inquiry.

        Given: A prompt explicitly asking to run a slash command
        When: The prompt is "run /s"
        Then: is_topic_inquiry() returns False
        """
        from UserPromptSubmit import intent_classifier

        prompt = "run /s"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False for 'run /s' pattern, got {result}"


class TestCaseInsensitivity:
    """Tests for case-insensitive pattern matching."""

    def test_uppercase_about_pattern(self):
        """Test that 'ABOUT /S' is detected as topic inquiry.

        Given: A prompt with uppercase inquiry keywords
        When: The prompt is "ABOUT /S"
        Then: is_topic_inquiry() returns True
        """
        from UserPromptSubmit import intent_classifier

        prompt = "ABOUT /S"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for uppercase pattern, got {result}"

    def test_mixed_case_regarding_pattern(self):
        """Test that 'Regarding /S' is detected as topic inquiry.

        Given: A prompt with mixed case inquiry keywords
        When: The prompt is "Regarding /S"
        Then: is_topic_inquiry() returns True
        """
        from UserPromptSubmit import intent_classifier

        prompt = "Regarding /S"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is True, \
            f"Expected True for mixed case pattern, got {result}"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string(self):
        """Test behavior with empty string.

        Given: An empty prompt
        When: The prompt is ""
        Then: is_topic_inquiry() returns False (no inquiry pattern)
        """
        from UserPromptSubmit import intent_classifier

        prompt = ""
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False for empty string, got {result}"

    def test_none_input(self):
        """Test behavior with None input.

        Given: A None prompt
        When: The prompt is None
        Then: is_topic_inquiry() returns False (handles gracefully)
        """
        from UserPromptSubmit import intent_classifier

        prompt = None
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False for None input, got {result}"

    def test_no_slash_command_reference(self):
        """Test behavior when no slash command is referenced.

        Given: A prompt without slash commands
        When: The prompt is "tell me about python"
        Then: is_topic_inquiry() returns False (no /s reference)
        """
        from UserPromptSubmit import intent_classifier

        prompt = "tell me about python"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False when no slash command referenced, got {result}"

    def test_inquiry_without_slash_command(self):
        """Test that inquiry patterns without /s don't match.

        Given: A prompt with inquiry words but no slash command
        When: The prompt is "tell me about that"
        Then: is_topic_inquiry() returns False (requires /s reference)
        """
        from UserPromptSubmit import intent_classifier

        prompt = "tell me about that"
        result = intent_classifier.is_topic_inquiry(prompt)

        assert result is False, \
            f"Expected False for inquiry without /s, got {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
