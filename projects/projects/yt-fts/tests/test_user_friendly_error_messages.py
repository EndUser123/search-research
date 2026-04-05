"""
Tests for user-friendly error messages in retry_classifier.py.

TDD Phase: RED - Tests verify that technical errors are mapped to user-friendly messages.
"""

import pytest

from yt_fts.utils.retry_classifier import get_user_friendly_message


class TestUserFriendlyMessages:
    """Tests for user-friendly error message mapping."""

    def test_403_rate_limit_message(self):
        """
        Test that HTTP 403 errors get a user-friendly rate limit message.

        Given: A 403 Forbidden error occurs
        When: get_user_friendly_message is called
        Then: Should return "Rate limited" message with wait time suggestion
        """
        error_msg = "HTTP Error 403: Forbidden"

        result = get_user_friendly_message(error_msg)

        assert "rate limit" in result.lower() or "too many requests" in result.lower()
        assert "wait" in result.lower() or "minutes" in result.lower()

    def test_404_not_found_message(self):
        """
        Test that HTTP 404 errors get a helpful not found message.

        Given: A 404 Not Found error occurs
        When: get_user_friendly_message is called
        Then: Should return channel/video not found message with suggestion
        """
        error_msg = "HTTP Error 404: Not Found"

        result = get_user_friendly_message(error_msg)

        assert "not found" in result.lower() or "404" in result.lower()
        assert "check" in result.lower() or "verify" in result.lower()

    def test_429_too_many_requests_message(self):
        """
        Test that HTTP 429 errors get rate limit message.

        Given: A 429 Too Many Requests error occurs
        When: get_user_friendly_message is called
        Then: Should return rate limit message with backoff suggestion
        """
        error_msg = "HTTP Error 429: Too Many Requests"

        result = get_user_friendly_message(error_msg)

        # Message should mention too many requests, rate limiting, or waiting
        assert (
            "rate limit" in result.lower()
            or "429" in result.lower()
            or "too many requests" in result.lower()
        )
        assert "wait" in result.lower() or "minutes" in result.lower()

    def test_network_error_message(self):
        """
        Test that network errors get connection check suggestion.

        Given: A connection/network error occurs
        When: get_user_friendly_message is called
        Then: Should return internet connection check message
        """
        error_msg = "Connection refused"

        result = get_user_friendly_message(error_msg)

        assert "connection" in result.lower() or "network" in result.lower() or "internet" in result.lower()

    def test_timeout_error_message(self):
        """
        Test that timeout errors get retry suggestion.

        Given: A timeout error occurs
        When: get_user_friendly_message is called
        Then: Should return timeout message with retry suggestion
        """
        error_msg = "Request timed out"

        result = get_user_friendly_message(error_msg)

        # "try again" is equivalent to "retry" for user-friendly messaging
        assert "retry" in result.lower() or "try again" in result.lower()

    def test_unknown_error_message(self):
        """
        Test that unknown errors return generic helpful message.

        Given: An unrecognized error occurs
        When: get_user_friendly_message is called
        Then: Should return generic error message
        """
        error_msg = "Unknown error: something broke"

        result = get_user_friendly_message(error_msg)

        assert len(result) > 0  # Should return some message

    def test_empty_error_message(self):
        """
        Test that empty error messages return generic message.

        Given: An empty error message
        When: get_user_friendly_message is called
        Then: Should return generic error message
        """
        error_msg = ""

        result = get_user_friendly_message(error_msg)

        assert len(result) > 0  # Should return some message
