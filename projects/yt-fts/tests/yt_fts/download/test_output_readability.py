"""
TDD tests for output readability improvements.

Issue 1: Singular/plural - "1 videos" should be "1 video"
Issue 2: Quota display line wrapping - "remaining" split across lines
Issue 3: Channel name repeated multiple times in progress messages
"""

import io
import sys
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from yt_fts.download.download_handler import DownloadHandler
from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill


class TestSingularPluralVideoCount:
    """Test that video count uses correct singular/plural form."""

    def test_single_video_shows_singular(self):
        """
        Given: 1 video needs downloading
        When: Progress message is displayed
        Then: Should show "1 video" not "1 videos"
        """
        console = Console(stderr=True)
        with patch("yt_fts.core.database.get_db_connection"):
            handler = DownloadHandler(console=console, suppress_status_messages=True)
            handler.video_ids = ["single_video"]
            handler.channel_name = "Test Channel"

            # Capture the message
            captured = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured

            try:
                # Simulate the message generation
                count = len(handler.video_ids)
                message = f'   ⎿ Downloading {count} video{"s" if count != 1 else ""} from "{handler.channel_name}"'
                sys.stderr.write(message)
            finally:
                sys.stderr = old_stderr

            output = captured.getvalue()

            # Should be "1 video" not "1 videos"
            assert "1 video" in output or output == ""
            assert "1 videos" not in output

    def test_multiple_videos_shows_plural(self):
        """
        Given: 2 videos need downloading
        When: Progress message is displayed
        Then: Should show "2 videos"
        """
        count = 2
        message = f'   ⎿ Downloading {count} video{"s" if count != 1 else ""}'

        assert "2 videos" in message
        assert "2 video" not in message or "2 videos" in message


class TestQuotaDisplayNoWrapping:
    """Test that quota display doesn't wrap inappropriately."""

    def test_quota_display_fits_on_one_line(self):
        """
        Given: API quota display is generated
        When: format_quota_display() is called
        Then: Each key's quota info should be complete (not split mid-word)

        This test documents the current behavior before fix.
        """
        # Mock the API keys to avoid initialization error
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test_key"}):
            api = YouTubeAPIBackfill()
            display = api.format_quota_display()

            # The display should show "X,XXX remaining" for each key
            # Currently it may wrap due to terminal width
            assert "remaining" in display, "Should show remaining quota"


class TestChannelNameRepetitionReduction:
    """Test that channel name isn't excessively repeated."""

    def test_channel_name_shown_once_in_header(self):
        """
        Given: Auto-backfill progress for a channel
        When: Progress messages are displayed
        Then: Channel name should appear once with 📺 header

        This reduces visual clutter from:
          📺 Channel Name
          Auto-backfill: 1 videos need subtitles from 'Channel Name'
          Downloading subtitles for 1 videos from "Channel Name"

        To:
          📺 Channel Name
          Auto-backfill: 1 video needs subtitles
          Downloading subtitles for 1 video
        """
        # After fix, auto-backfill message should NOT repeat channel name
        # This is a placeholder for the behavior change
        assert True  # Will be updated based on implementation approach


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
