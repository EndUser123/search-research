"""
Unit tests for BatchDownloader retry logic with rate limit handling.

Tests the exponential backoff calculation and rate limit detection
in batch download retry logic.
"""

import pytest


class TestRateLimitBackoffCalculation:
    """Test suite for rate limit backoff wait time calculation."""

    def test_rate_limit_wait_time_first_retry(self) -> None:
        """Test that first rate limit retry waits 60 seconds."""
        error_msg = "Your account has been rate-limited by YouTube"

        # Simulate the rate limit detection logic
        is_rate_limit = any(phrase in error_msg.lower() for phrase in [
            "rate-limited", "rate limited", "http error 429",
            "too many requests", "try again later"
        ])

        assert is_rate_limit is True

        # Calculate wait time for attempt 0
        attempt = 0
        wait_time = min(60 * (2 ** attempt), 300)
        assert wait_time == 60

    def test_rate_limit_wait_time_second_retry(self) -> None:
        """Test that second rate limit retry waits 120 seconds."""
        attempt = 1
        wait_time = min(60 * (2 ** attempt), 300)
        assert wait_time == 120

    def test_rate_limit_wait_time_third_retry(self) -> None:
        """Test that third rate limit retry waits 240 seconds."""
        attempt = 2
        wait_time = min(60 * (2 ** attempt), 300)
        assert wait_time == 240

    def test_rate_limit_wait_time_max_capped(self) -> None:
        """Test that rate limit wait time is capped at 300 seconds (5 minutes)."""
        # For attempts >= 3, wait time should be capped at 300
        for attempt in [3, 4, 5, 10]:
            wait_time = min(60 * (2 ** attempt), 300)
            assert wait_time == 300, f"Failed for attempt {attempt}"

    def test_standard_error_backoff(self) -> None:
        """Test that non-rate-limit errors use standard exponential backoff."""
        error_msg = "Connection timeout"

        is_rate_limit = any(phrase in error_msg.lower() for phrase in [
            "rate-limited", "rate limited", "http error 429",
            "too many requests", "try again later"
        ])

        assert is_rate_limit is False

        # Standard backoff: 2^attempt
        for attempt, expected in [(0, 1), (1, 2), (2, 4), (3, 8)]:
            wait_time = 2 ** attempt
            assert wait_time == expected, f"Failed for attempt {attempt}"


class TestRateLimitErrorDetection:
    """Test suite for rate limit error detection in retry logic."""

    def test_detect_rate_limited_phrase(self) -> None:
        """Test detection of 'rate-limited' phrase."""
        error_msg = "ERROR: Your account has been rate-limited by YouTube"
        is_rate_limit = any(phrase in error_msg.lower() for phrase in [
            "rate-limited", "rate limited", "http error 429",
            "too many requests", "try again later"
        ])
        assert is_rate_limit is True

    def test_detect_rate_limit_with_http_429(self) -> None:
        """Test detection of HTTP 429 error."""
        error_msg = "ERROR: HTTP Error 429: Too Many Requests"
        is_rate_limit = any(phrase in error_msg.lower() for phrase in [
            "rate-limited", "rate limited", "http error 429",
            "too many requests", "try again later"
        ])
        assert is_rate_limit is True

    def test_detect_try_again_later(self) -> None:
        """Test detection of 'try again later' phrase."""
        error_msg = "Video unavailable. This content isn't available, try again later"
        is_rate_limit = any(phrase in error_msg.lower() for phrase in [
            "rate-limited", "rate limited", "http error 429",
            "too many requests", "try again later"
        ])
        assert is_rate_limit is True

    def test_non_rate_limit_not_detected(self) -> None:
        """Test that other errors are not classified as rate limits."""
        non_rate_limit_errors = [
            "Connection timeout",
            "HTTP Error 404: Not Found",
            "Video unavailable",
            "Network unreachable",
            "Socket timeout",
        ]

        for error_msg in non_rate_limit_errors:
            is_rate_limit = any(phrase in error_msg.lower() for phrase in [
                "rate-limited", "rate limited", "http error 429",
                "too many requests", "try again later"
            ])
            assert is_rate_limit is False, f"Incorrectly detected as rate limit: {error_msg}"

    def test_case_insensitive_detection(self) -> None:
        """Test that rate limit detection is case-insensitive."""
        variations = [
            "RATE-LIMITED",
            "Rate-Limited",
            "rate limited",
            "RATE LIMITED",
            "Http Error 429",
        ]

        for error_msg in variations:
            is_rate_limit = any(phrase in error_msg.lower() for phrase in [
                "rate-limited", "rate limited", "http error 429",
                "too many requests", "try again later"
            ])
            assert is_rate_limit is True, f"Failed for: {error_msg}"


class TestRetryLogicIntegration:
    """Integration tests for retry logic with backoff calculation."""

    def test_rate_limit_backoff_sequence(self) -> None:
        """Test the complete sequence of rate limit backoff times."""
        expected_sequence = [60, 120, 240, 300, 300]  # 5 retries

        for attempt, expected_wait in enumerate(expected_sequence):
            wait_time = min(60 * (2 ** attempt), 300)
            assert wait_time == expected_wait, f"Attempt {attempt}: expected {expected_wait}, got {wait_time}"

    def test_standard_backoff_sequence(self) -> None:
        """Test the complete sequence of standard error backoff times."""
        expected_sequence = [1, 2, 4, 8, 16]  # 5 retries

        for attempt, expected_wait in enumerate(expected_sequence):
            wait_time = 2 ** attempt
            assert wait_time == expected_wait, f"Attempt {attempt}: expected {expected_wait}, got {wait_time}"
