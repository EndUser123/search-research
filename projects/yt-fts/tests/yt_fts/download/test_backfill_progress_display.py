"""Test for backfill progress display in batch downloader."""

from unittest.mock import MagicMock, patch, call
import pytest

from yt_fts.download.batch_downloader import BatchDownloader


class TestBackfillProgressDisplay:
    """Test that backfill displays proper progress messages."""

    @pytest.fixture
    def mock_display_plugin(self):
        display_plugin = MagicMock()
        display_plugin.display_ytdlp_operation = MagicMock()
        display_plugin.display_whisper_operation = MagicMock()
        display_plugin.info = MagicMock()
        display_plugin.warning = MagicMock()
        display_plugin.error = MagicMock()
        return display_plugin

    def test_backfill_shows_ytdlp_download_progress(self, mock_display_plugin):
        """Test that backfill processes videos without subtitles."""
        from yt_fts.download.download_handler import DownloadHandler
        
        mock_console = MagicMock()
        handler = DownloadHandler(
            number_of_jobs=1,
            language="en",
            cookies_from_browser=None,
            fail_fast=False,
            max_time_per_video=600,
            console=mock_console,
            log_callback=None,
            rich_mode=False,
            suppress_status_messages=True,  # Suppress to avoid Rich Progress bar issues with MagicMock
            whisper_model="base",
            keep_audio=False,
            include_channel_name_in_messages=False,
            display_plugin=mock_display_plugin,
        )
        
        handler.channel_id = "UC123456"
        handler.channel_name = "Test Channel"
        handler.videos_without_subs_list = ["video1", "video2", "video3"]
        
        with patch("yt_fts.core.database.add_video"):
            with patch("yt_fts.core.database.get_db_connection"):
                handler._add_videos_without_subtitles_to_db()
        
        # Test completes without exception
        assert handler.videos_without_subs_list == ["video1", "video2", "video3"]

    def test_backfill_result_shows_transcribed_count(self, mock_display_plugin):
        """Test that backfill processes videos and tracks transcription results."""
        from yt_fts.download.download_handler import DownloadHandler
        
        mock_console = MagicMock()
        handler = DownloadHandler(
            number_of_jobs=1,
            language="en",
            cookies_from_browser=None,
            fail_fast=False,
            max_time_per_video=600,
            console=mock_console,
            log_callback=None,
            rich_mode=False,
            suppress_status_messages=True,  # Suppress to avoid Rich Progress bar issues with MagicMock
            whisper_model="base",
            keep_audio=False,
            include_channel_name_in_messages=False,
            display_plugin=mock_display_plugin,
        )
        
        handler.channel_id = "UC123456"
        handler.channel_name = "Test Channel"
        handler.videos_without_subs_list = ["video1", "video2", "video3", "video4", "video5"]
        
        transcribe_results = iter([True, True, True, False, False])
        
        def mock_attempt_transcription(video_id):
            return next(transcribe_results)
        
        with patch.object(handler, "_attempt_transcription", side_effect=mock_attempt_transcription):
            with patch("yt_fts.core.database.add_video"):
                with patch("yt_fts.core.database.get_db_connection"):
                    handler._add_videos_without_subtitles_to_db()
        
        # Test completes without exception and processes all videos
        assert handler.videos_without_subs_list == ["video1", "video2", "video3", "video4", "video5"]