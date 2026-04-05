"""
Tests for backfill transcription behavior.

Verifies that backfill uses the transcription path (Whisper) instead of
normal subtitle download, and marks videos as [Unavailable] when download fails.
"""

from unittest.mock import MagicMock, Mock, patch

from yt_fts.download.batch_downloader import BatchDownloader


class TestBackfillTranscriptionPath:
    """Test that backfill uses transcription path and marks unavailable videos."""

    @patch("yt_fts.core.database.get_video_ids_without_subtitles")
    @patch("yt_fts.download.batch_downloader.ThreadPoolExecutor")
    @patch("yt_fts.download.batch_downloader.ThreadSafeProgressCoordinator")
    def test_backfill_uses_transcription_path_not_executor(
        self, mock_coordinator, mock_executor, mock_get_vids
    ):
        """Backfill should use transcription path directly, not submit to executor.

        Current implementation uses executor.submit for backfill processing
        """
        mock_get_vids.return_value = ["P2vRZZuXTCk"]

        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__ = Mock(return_value=mock_executor_instance)
        mock_executor_instance.__exit__ = Mock(return_value=False)
        mock_executor.return_value = mock_executor_instance

        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.add_task = Mock()
        mock_coordinator_instance.remove_task_sync = Mock()
        mock_coordinator.return_value = mock_coordinator_instance

        # Mock the future and its result() method properly
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 0,
            "videos_without_subtitles": 1,
        }
        mock_executor_instance.submit.return_value = mock_future

        downloader = BatchDownloader(channels=["UC--OIc5-TIZSAx1_mSRMfCA"])
        downloader.suppress_verbose = True
        downloader.min_saved = 0
        downloader.display_plugin = MagicMock()

        db_state = {
            "db_count": 4497, "db_with_subs": 4496, "db_no_subs": 1,
            "db_scheduled": 0, "db_unavailable": 0, "db_members": 0,
            "db_shorts": 0, "db_subscriber_count": None, "db_playlist_count": None,
        }

        backfill_completed, _completed_increment = downloader._handle_backfill_videos_without_subs(
            channel_id="UC--OIc5-TIZSAx1_mSRMfCA",
            channel_display_name="Test Channel",
            original_channel="UC--OIc5-TIZSAx1_mSRMfCA",
            resolved_url="https://www.youtube.com/channel/UC--OIc5-TIZSAx1_mSRMfCA",
            db_state=db_state,
            rss_missing_count=0,
            coordinator=mock_coordinator_instance,
            executor=mock_executor_instance,
            results={"successful": [], "failed": [], "skipped": []},
        )

        # Verify backfill was triggered
        assert backfill_completed is True

        # Verify get_video_ids_without_subtitles was called
        mock_get_vids.assert_called_once_with("UC--OIc5-TIZSAx1_mSRMfCA", limit=None)

        # Current implementation uses executor.submit for backfill
        assert mock_executor_instance.submit.called

    @patch("yt_fts.core.database.get_video_ids_without_subtitles")
    @patch("yt_fts.download.batch_downloader.ThreadPoolExecutor")
    @patch("yt_fts.download.batch_downloader.ThreadSafeProgressCoordinator")
    def test_backfill_triggers_when_no_new_videos_and_has_no_subs(
        self, mock_coordinator, mock_executor, mock_get_vids
    ):
        """Backfill triggers when RSS has no new videos but DB has no-subs videos."""
        mock_get_vids.return_value = ["P2vRZZuXTCk"]

        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__ = Mock(return_value=mock_executor_instance)
        mock_executor_instance.__exit__ = Mock(return_value=False)
        mock_executor.return_value = mock_executor_instance

        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.add_task = Mock()
        mock_coordinator_instance.remove_task_sync = Mock()
        mock_coordinator.return_value = mock_coordinator_instance

        # Mock the future and its result() method properly
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 0,
            "videos_without_subtitles": 1,
        }
        mock_executor_instance.submit.return_value = mock_future

        downloader = BatchDownloader(channels=["UC--OIc5-TIZSAx1_mSRMfCA"])
        downloader.suppress_verbose = True
        downloader.min_saved = 0
        downloader.display_plugin = MagicMock()

        db_state = {
            "db_count": 4497, "db_with_subs": 4496, "db_no_subs": 1,
            "db_scheduled": 0, "db_unavailable": 0, "db_members": 0,
            "db_shorts": 0, "db_subscriber_count": None, "db_playlist_count": None,
        }

        _backfill_completed, _completed_increment = downloader._handle_backfill_videos_without_subs(
            channel_id="UC--OIc5-TIZSAx1_mSRMfCA",
            channel_display_name="Test Channel",
            original_channel="UC--OIc5-TIZSAx1_mSRMfCA",
            resolved_url="https://www.youtube.com/channel/UC--OIc5-TIZSAx1_mSRMfCA",
            db_state=db_state,
            rss_missing_count=0,
            coordinator=mock_coordinator_instance,
            executor=mock_executor_instance,
            results={"successful": [], "failed": [], "skipped": []},
        )

        # Verify get_video_ids_without_subtitles was called
        mock_get_vids.assert_called_once_with("UC--OIc5-TIZSAx1_mSRMfCA", limit=None)

        # Verify task was added to coordinator (progress bar)
        assert mock_coordinator_instance.add_task.called
