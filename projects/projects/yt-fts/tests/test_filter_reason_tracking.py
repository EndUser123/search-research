"""
Tests for filter reason tracking when videos are filtered during download.

Tracks why videos fail to download (Shorts, no subtitles, scheduled, unavailable)
to provide better user feedback.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestFilterReasonTracking:
    """Test tracking of why videos are filtered during download."""

    def test_filter_reason_accumulator_initializes_empty(self):
        """Test that filter reasons start with zero counts."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()

        assert handler.filter_reasons["no_subtitles"] == 0
        assert handler.filter_reasons["shorts"] == 0
        assert handler.filter_reasons["scheduled"] == 0
        assert handler.filter_reasons["unavailable"] == 0
        assert handler.filter_reasons["members_only"] == 0

    def test_track_no_subtitles_filter_reason(self):
        """Test tracking when video has no subtitles."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()

        # Simulate video with no subtitles
        handler._track_filter_reason("no_subtitles", "video123")

        assert handler.filter_reasons["no_subtitles"] == 1
        assert handler.filter_reasons["shorts"] == 0

    def test_track_multiple_filter_reasons(self):
        """Test tracking multiple different filter reasons."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()

        handler._track_filter_reason("no_subtitles", "video1")
        handler._track_filter_reason("shorts", "video2")
        handler._track_filter_reason("shorts", "video3")
        handler._track_filter_reason("scheduled", "video4")

        assert handler.filter_reasons["no_subtitles"] == 1
        assert handler.filter_reasons["shorts"] == 2
        assert handler.filter_reasons["scheduled"] == 1

    def test_get_filter_summary_message_all_filtered(self):
        """Test generating summary message when all videos are filtered."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()
        handler._track_filter_reason("no_subtitles", "video1")
        handler._track_filter_reason("shorts", "video2")
        handler._track_filter_reason("scheduled", "video3")

        summary = handler._get_filter_summary()

        # "no_subtitles" is displayed as "no transcript"
        assert "transcript" in summary.lower() or "subtitles" in summary.lower()
        assert "short" in summary.lower()
        assert "scheduled" in summary.lower()

    def test_get_filter_summary_message_empty(self):
        """Test summary message when no videos were filtered."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()

        summary = handler._get_filter_summary()

        assert summary == "" or "no filters" in summary.lower()

    def test_classify_short_from_video_url(self):
        """Test detecting Shorts from video URL."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")

        # Shorts URL
        short_url = "https://www.youtube.com/shorts/abc123"
        assert handler._is_short_video(short_url) is True

        # Regular video URL
        regular_url = "https://www.youtube.com/watch?v=abc123"
        assert handler._is_short_video(regular_url) is False

    def test_classify_scheduled_from_info(self):
        """Test detecting scheduled/upcoming videos from yt-dlp info."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")

        # Scheduled video info
        scheduled_info = {"live_status": "is_upcoming"}
        assert handler._is_scheduled_video(scheduled_info) is True

        # Regular video info
        regular_info = {"live_status": "none"}
        assert handler._is_scheduled_video(regular_info) is False

        # Video with release_timestamp in future
        from datetime import datetime, timedelta
        future_time = datetime.now() + timedelta(days=1)
        future_info = {"release_timestamp": future_time.isoformat()}
        assert handler._is_scheduled_video(future_info) is True

    def test_classify_no_subtitles_from_info(self):
        """Test detecting videos with no subtitles."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")

        # Video with no subtitles
        no_subs_info = {"subtitles": {}, "automatic_captions": {}}
        assert handler._has_no_subtitles(no_subs_info) is True

        # Video with manual subtitles
        with_subs_info = {"subtitles": {"en": []}, "automatic_captions": {}}
        assert handler._has_no_subtitles(with_subs_info) is False

        # Video with auto captions
        with_auto_info = {"subtitles": {}, "automatic_captions": {"en": []}}
        assert handler._has_no_subtitles(with_auto_info) is False


class TestFilterReasonDisplayMessages:
    """Test display messages for filtered videos."""

    def test_no_videos_message_with_filter_reasons(self):
        """Test 'No videos to download' message includes specific reasons."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()
        handler._track_filter_reason("no_subtitles", "video1")
        handler.video_ids = ["video1"]

        message = handler._get_no_videos_message()

        # Should mention the specific reason, not just generic "filtered"
        assert "subtitles" in message.lower() or "transcript" in message.lower()

    def test_result_message_no_transcript_to_store(self):
        """Test result message when no transcript is available."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()
        handler._track_filter_reason("no_subtitles", "video1")
        handler.videos_saved_to_db = 0

        message = handler._get_result_message()

        # Should say something about no transcript
        assert "transcript" in message.lower() or "subtitles" in message.lower()

    def test_result_message_shorts_only(self):
        """Test result message when only Shorts were found."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1, language="en")
        handler._initialize_filter_reasons()
        handler._track_filter_reason("shorts", "video1")
        handler._track_filter_reason("shorts", "video2")
        handler.videos_saved_to_db = 0

        message = handler._get_result_message()

        # Should mention Shorts specifically
        assert "short" in message.lower()
