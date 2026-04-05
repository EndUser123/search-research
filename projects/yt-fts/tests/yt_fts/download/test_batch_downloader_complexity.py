"""
Characterization tests for P2-002: Reduce cyclomatic complexity in batch_downloader.py

Phase 1 (RED): Write characterization tests for 4 critical functions.
"""

from unittest.mock import MagicMock, Mock, patch
from concurrent.futures import ThreadPoolExecutor
import pytest
import time

from yt_fts.download.batch_downloader import BatchDownloader
from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator


class TestDownloadAllCharacterization:
    """Characterization tests for download_all (CC=73)."""

    @pytest.fixture
    def downloader(self):
        return BatchDownloader(
            channels=["@testchannel"],
            suppress_quota_print=True,
            suppress_verbose=True,
            rich_mode=False,
        )

    def test_download_all_returns_empty_results_for_dry_run(self, downloader):
        """Characterization: dry_run mode returns early with empty results."""
        downloader.dry_run = True
        result = downloader.download_all()
        assert "successful" in result
        assert result["successful"] == []
        assert result["failed"] == []

    @patch("yt_fts.download.batch_downloader.load_checkpoint")
    def test_download_all_resumes_from_checkpoint(self, mock_load_checkpoint, downloader):
        """Characterization: Loads checkpoint and skips already processed channels."""
        mock_load_checkpoint.return_value = 2
        channel_list = [("@ch1", "url1", "id1"), ("@ch2", "url2", "id2"), ("@ch3", "url3", "id3")]
        with patch.object(downloader, "_resolve_and_validate_channels", return_value=(channel_list, [])):
            with patch.object(downloader, "_initialize_batch_download", return_value=({}, 0)):
                with patch("yt_fts.download.batch_downloader.Progress"):
                    with patch("yt_fts.download.batch_downloader.ThreadSafeProgressCoordinator"):
                        result = downloader.download_all()
        mock_load_checkpoint.assert_called_once()
        assert len(result.get("skipped", [])) >= 2


class TestDownloadSingleChannelOptimizedCharacterization:
    """Characterization tests for _download_single_channel_optimized (CC=40)."""

    @pytest.fixture
    def downloader(self):
        return BatchDownloader(channels=["@testchannel"], suppress_verbose=True)

    @pytest.fixture
    def mock_coordinator(self):
        return MagicMock(spec=ThreadSafeProgressCoordinator)

    def test_returns_success_with_no_new_videos_from_rss(self, downloader, mock_coordinator):
        """Characterization: Returns success early when RSS found no new videos."""
        result = downloader._download_single_channel_optimized(
            original_channel="@test",
            resolved_url="https://youtube.com/@test",
            channel_id="UC123",
            coordinator=mock_coordinator,
            video_ids=[],
        )
        assert result["success"] is True
        assert result["videos_count"] == 0
        assert result["message"] == "No new subtitles"


class TestPerformRssCheckAndDetermineStatusCharacterization:
    """Characterization tests for _perform_rss_check_and_determine_status (CC=39)."""

    @pytest.fixture
    def downloader(self):
        return BatchDownloader(channels=["@testchannel"], suppress_verbose=True)

    @pytest.fixture
    def mock_rss_checker(self):
        return MagicMock()

    @pytest.fixture
    def db_state(self):
        return {"db_count": 10, "db_with_subs": 8, "db_no_subs": 2, "db_scheduled": 0}

    def test_returns_rss_skip_when_no_new_videos(self, downloader, mock_rss_checker, db_state):
        """Characterization: Returns rss_skip=True when RSS finds no new videos."""
        mock_rss_checker.check.return_value = MagicMock(has_new_videos=False, video_ids=[])
        status, message, rss_skip, missing_count, video_ids, skipped, result = (
            downloader._perform_rss_check_and_determine_status(
                channel_id="UC123",
                handle="@test",
                resolved_url="https://youtube.com/@test",
                db_state=db_state,
                original_channel="@test",
                suppress_verbose=True,
                rss_checker=mock_rss_checker,
            )
        )
        assert rss_skip is True
        assert video_ids == []


class TestExecuteYtdlpDownloadForChannelCharacterization:
    """Characterization tests for _execute_ytdlp_download_for_channel (CC=32)."""

    @pytest.fixture
    def downloader(self):
        return BatchDownloader(channels=["@testchannel"], suppress_verbose=True)

    @pytest.fixture
    def mock_coordinator(self):
        return MagicMock(spec=ThreadSafeProgressCoordinator)

    @pytest.fixture
    def mock_executor(self):
        return MagicMock(spec=ThreadPoolExecutor)

    def test_creates_progress_task_when_videos_to_download(self, downloader, mock_coordinator, mock_executor):
        """Characterization: Creates progress task when video_ids list is not empty."""
        video_ids = ["vid1", "vid2"]
        mock_future = MagicMock()
        mock_future.result.return_value = {"success": True, "videos_count": 2}
        mock_executor.submit.return_value = mock_future
        downloader._execute_ytdlp_download_for_channel(
            original_channel="@test",
            resolved_url="https://youtube.com/@test",
            channel_id="UC123",
            coordinator=mock_coordinator,
            executor=mock_executor,
            rss_video_ids_for_download=video_ids,
            suppress_verbose=True,
            target=1,
            successful_downloads=0,
            total_videos_saved=0,
            results={"successful": [], "failed": [], "skipped": []},
        )
        mock_coordinator.add_task.assert_called_once()
