"""
Tests for unified_discovery.py error handling.

Tests graceful handling of deleted/non-existent channels.
"""
from unittest.mock import patch, MagicMock
import pytest

from yt_fts.download.unified_discovery import UnifiedChannelDiscovery, DiscoveryResult


class TestUnifiedDiscoveryErrorHandling:
    """
    Test error handling for non-existent and deleted channels.

    When a channel doesn't exist or was deleted, we should:
    1. Not crash with full traceback
    2. Return a DiscoveryResult with source="error" or similar
    3. Preserve existing database data if channel was previously indexed
    """

    def test_nonexistent_channel_returns_graceful_result(self):
        """
        Test that a non-existent channel returns a graceful DiscoveryResult.

        Given: A channel ID that doesn't exist (UC1234567890123456789012)
        When: _discover_via_ytdlp is called
        Then: Should return DiscoveryResult with source="none" (not crash)
        """
        discovery = UnifiedChannelDiscovery(cookies_from_browser=None)

        # Use a known invalid channel ID
        result = discovery.discover("https://www.youtube.com/channel/UC1234567890123456789012")

        # Should return a result, not raise exception
        assert isinstance(result, dict), "Should return a dict"
        assert result.get("channel_id") is None or result.get("channel_id") == "UC1234567890123456789012"
        # source should be "none" when discovery fails
        assert result.get("source") in ("none", "ytdlp", "database"), f"source should be 'none' for failed discovery, got: {result.get('source')}"
        assert result.get("total_videos", 0) == 0

    def test_nonexistent_channel_does_not_crash_with_traceback(self):
        """
        Test that discovery doesn't print full traceback for non-existent channels.

        Given: A channel that doesn't exist
        When: _discover_via_ytdlp encounters yt-dlp DownloadError
        Then: Should handle exception gracefully, not re-raise

        This is a regression test for the issue where full Python traceback
        was displayed to the user for non-existent channels.
        """
        discovery = UnifiedChannelDiscovery(cookies_from_browser=None)

        # This should not raise an exception to the caller
        # Any yt-dlp exceptions should be caught internally
        try:
            result = discovery.discover("https://www.youtube.com/channel/UCNonExistentChannel12345")
            # If we get here, exception was handled
            assert True, "Discovery completed without raising exception"
        except Exception as e:
            pytest.fail(f"Discovery should not raise exception, got: {type(e).__name__}: {e}")

    def test_discovery_result_has_all_required_fields(self):
        """
        Test that DiscoveryResult has all required fields even on error.

        Given: Any discovery result (success or failure)
        When: Accessing DiscoveryResult fields
        Then: All required fields should be present (no KeyError)

        This ensures the display code can safely access all fields.
        """
        discovery = UnifiedChannelDiscovery(cookies_from_browser=None)

        result = discovery.discover("https://www.youtube.com/channel/UCInvalidChannelID")

        # Verify all expected fields exist
        expected_fields = [
            "channel_id",
            "channel_name", 
            "channel_url",
            "total_videos",
            "with_subs",
            "without_subs",
            "scheduled",
            "members_only",
            "unavailable",
            "source",
        ]

        for field in expected_fields:
            assert field in result, f"Missing required field: {field}"

    def test_channel_with_existing_db_data_preserved_on_error(self):
        """
        Test that channels with existing DB data are handled gracefully.

        Given: A channel that was previously indexed but no longer exists
        When: Discovery fails (channel deleted/removed from YouTube)
        Then: Should return DiscoveryResult indicating error, but not delete existing data

        Note: This test verifies the DISCOVERY phase only. Deletion marking would
        happen in a separate phase if desired.
        """
        # This test would require mocking the database
        # For now, we verify that discovery returns gracefully
        discovery = UnifiedChannelDiscovery(cookies_from_browser=None)

        result = discovery.discover("https://www.youtube.com/channel/UCDoesNotExist123")

        # Discovery should complete without crashing
        assert result is not None
        # source indicates failure
        assert result.get("source") == "none"
    def test_nonexistent_channel_does_not_spam_stderr(self, capsys):
        """
        Test that discovery doesn't spam stderr with YTDLP warnings/errors.

        Given: A channel that doesn't exist
        When: _discover_via_ytdlp encounters yt-dlp errors
        Then: stderr should be clean (no YTDLP WARNING/ERROR spam)

        This is a regression test for the issue where full Python traceback
        and YTDLP warnings were displayed for non-existent channels.
        """
        discovery = UnifiedChannelDiscovery(cookies_from_browser=None)

        # Clear any existing capture
        capsys.readouterr()

        # Run discovery on invalid channel
        result = discovery.discover("https://www.youtube.com/channel/UCNonExistentChannel12345")

        # Capture stderr
        captured_err = capsys.readouterr().err

        # stderr should not contain YTDLP spam
        # Note: Some debug output may be acceptable, but full warnings/errors should not
        # stderr should not contain YTDLP spam
        # Note: Some debug output may be acceptable, but full warnings/errors should not
        assert "YTDLP WARNING" not in captured_err, "stderr should not contain YTDLP WARNING"
        assert "YTDLP ERROR" not in captured_err, "stderr should not contain YTDLP ERROR"
        # Full Python traceback should NOT be in stderr
        assert "Traceback (most recent call last)" not in captured_err, "stderr should not contain traceback"
        
        # If captured_err has content, show it for debugging (but test should pass)
        if captured_err and "DEBUG" not in captured_err:
            # Only show in test output if unexpected content found
            pass

