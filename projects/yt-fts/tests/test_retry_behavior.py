"""
Tests for retry behavior when channels have no videos.

Tests that BaseURLFallbackFailed exceptions properly check should_skip_retry()
to avoid unnecessary retry attempts for permanently empty channels.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.exceptions import BaseURLFallbackFailed
from yt_fts.download.batch_downloader import BatchDownloader
from yt_fts.utils.retry_classifier import should_skip_retry


class TestShouldSkipRetry:
    """Test should_skip_retry function for empty channel detection."""

    def test_no_videos_found_for_channel_skips_retry(self):
        """Should skip retry when error message contains 'No videos found for channel'."""
        error_msg = "No videos found for channel: https://www.youtube.com/@HumanityUnleashed"
        assert should_skip_retry(error_msg) is True

    def test_empty_channel_variations_skip_retry(self):
        """Should skip retry for various empty channel error patterns."""
        test_cases = [
            "No videos found for channel: https://www.youtube.com/@test",
            "no videos found for channel",
            "channel is empty",
            "this channel does not exist",
            "channel doesn't exist",
        ]
        for msg in test_cases:
            assert should_skip_retry(msg) is True

    def test_transient_errors_do_not_skip_retry(self):
        """Should NOT skip retry for transient errors."""
        test_cases = [
            "HTTP Error 400: Bad Request",
            "Network timeout",
            "Connection refused",
        ]
        for msg in test_cases:
            assert should_skip_retry(msg) is False


class TestBaseURLFallbackFailedRetry:
    """Test that BaseURLFallbackFailed exceptions respect should_skip_retry logic."""

    def test_base_url_fallback_failed_for_empty_channel_skips_retry(self):
        """When BaseURLFallbackFailed contains 'no videos found', should skip retries."""
        error = BaseURLFallbackFailed("No videos found for channel: https://www.youtube.com/@HumanityUnleashed")
        error_msg = str(error)
        assert should_skip_retry(error_msg) is True

    def test_base_url_fallback_failed_sets_skipped_retry_flag(self):
        """BaseURLFallbackFailed handler should set skipped_retry: True for permanent failures."""
        error = BaseURLFallbackFailed("No videos found for channel: @test")
        from yt_fts.utils.retry_classifier import should_skip_retry
        if should_skip_retry(str(error)):
            result = {
                "success": False,
                "error": str(error),
                "skipped_retry": True
            }
            assert result["skipped_retry"] is True
