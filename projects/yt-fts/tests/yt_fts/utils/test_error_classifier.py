"""
Unit tests for ErrorClassifier - rate limit detection.

Tests the error classification logic for detecting YouTube rate limit errors
and ensuring proper user messages are returned.
"""

import pytest

from yt_fts.utils.error_classifier import ErrorCategory, ErrorClassifier


class TestRateLimitDetection:
    """Test suite for rate limit error detection."""

    def test_detect_rate_limit_with_429_error(self) -> None:
        """Test detection of HTTP 429 Too Many Requests error."""
        stderr = "ERROR: [youtube] HTTP Error 429: Too Many Requests"
        category, user_msg = ErrorClassifier.classify(stderr)

        assert category == ErrorCategory.RATE_LIMITED
        assert "rate limited" in user_msg.lower()

    def test_detect_rate_limit_with_quota_exceeded(self) -> None:
        """Test detection of quota exceeded message."""
        stderr = "ERROR: RATE_LIMIT_EXCEEDED"
        category, user_msg = ErrorClassifier.classify(stderr)

        assert category == ErrorCategory.RATE_LIMITED
        assert "rate limited" in user_msg.lower()

    def test_detect_rate_limit_with_rate_limited_phrase(self) -> None:
        """Test detection of 'rate-limited' phrase in error."""
        stderr = "ERROR: Your account has been rate-limited by YouTube for up to an hour"
        category, user_msg = ErrorClassifier.classify(stderr)

        assert category == ErrorCategory.RATE_LIMITED
        assert "rate limited" in user_msg.lower()

    def test_detect_rate_limit_with_try_again_later(self) -> None:
        """Test detection of 'try again later' phrase."""
        stderr = "Video unavailable. This content isn't available, try again later"
        category, user_msg = ErrorClassifier.classify(stderr)

        assert category == ErrorCategory.RATE_LIMITED

    def test_detect_rate_limit_case_insensitive(self) -> None:
        """Test that rate limit detection is case-insensitive."""
        stderr = "ERROR: RATE-LIMITED by YouTube"
        category, _ = ErrorClassifier.classify(stderr)

        assert category == ErrorCategory.RATE_LIMITED

    def test_detect_rate_limit_with_mixed_message(self) -> None:
        """Test detection in a complex error message."""
        stderr = """
        ERROR: [youtube] oWaJimncyjM: Video unavailable.
        This content isn't available, try again later.
        Your account has been rate-limited by YouTube for up to an hour.
        """
        category, user_msg = ErrorClassifier.classify(stderr)

        assert category == ErrorCategory.RATE_LIMITED

    def test_non_rate_limit_errors(self) -> None:
        """Test that non-rate-limit errors are correctly classified."""
        test_cases = [
            ("HTTP Error 404: Not Found", ErrorCategory.CHANNEL_NOT_FOUND),
            ("socket.timeout: timed out", ErrorCategory.TIMEOUT),
            ("Connection reset by peer", ErrorCategory.NETWORK_ERROR),
        ]

        for stderr, expected_category in test_cases:
            category, _ = ErrorClassifier.classify(stderr)
            assert category == expected_category, f"Failed for: {stderr}"

    def test_empty_stderr_returns_unknown(self) -> None:
        """Test that empty stderr returns UNKNOWN category."""
        category, user_msg = ErrorClassifier.classify("")

        assert category == ErrorCategory.UNKNOWN
        assert "unknown" in user_msg.lower()

    def test_rate_limit_user_message(self) -> None:
        """Test that rate limit returns appropriate user message."""
        stderr = "ERROR: HTTP Error 429: Too Many Requests"
        _, user_msg = ErrorClassifier.classify(stderr)

        # The message should indicate waiting
        assert "waiting" in user_msg.lower() or "retry" in user_msg.lower()


class TestErrorClassifierIntegration:
    """Integration tests for error classifier patterns."""

    def test_all_rate_limit_patterns(self) -> None:
        """Test all rate limit patterns are detected."""
        patterns = ErrorClassifier.PATTERNS[ErrorCategory.RATE_LIMITED]

        # Verify patterns include the new ones
        pattern_strings = " ".join(patterns)
        assert "rate-limited" in pattern_strings
        assert "has been rate-limited" in pattern_strings
        assert "try again later" in pattern_strings

    def test_youtube_rate_limit_message_variations(self) -> None:
        """Test various forms of YouTube's rate limit message."""
        variations = [
            "Your account has been rate-limited by YouTube",
            "has been rate-limited by YouTube for up to an hour",
            "try again later",
            "HTTP Error 429",
            "Too many requests",
        ]

        for variation in variations:
            category, _ = ErrorClassifier.classify(variation)
            assert category == ErrorCategory.RATE_LIMITED, f"Failed to detect: {variation}"
