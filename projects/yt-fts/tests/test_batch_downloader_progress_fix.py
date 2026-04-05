"""
Test for progress bar flashing bug fix in _execute_ytdlp_download_for_channel.

These tests verify that coordinator.add_task() is ONLY called when there are videos
to download, preventing visual flashing from creating and immediately removing progress tasks.

Bug: The function creates a progress bar task via coordinator.add_task() even when
     rss_video_ids_for_download is empty or None, causing a visual flash when the
     task is removed immediately after the download completes (or skips).

Fix: The coordinator.add_task() call should ONLY be executed when there are videos
     to download (rss_video_ids_for_download is not empty).

Run with: pytest tests/test_batch_downloader_progress_fix.py -v
"""

from unittest.mock import MagicMock, patch, call
import pytest

from yt_fts.download.batch_downloader import BatchDownloader


class TestExecuteYtdlpDownloadProgressTaskCreation:
    """Tests for progress bar task creation in _execute_ytdlp_download_for_channel."""

    @pytest.fixture
    def downloader(self):
        """Create BatchDownloader instance for testing."""
        return BatchDownloader(
            channels=["@testchannel"],
            suppress_quota_print=True,
            suppress_verbose=True,
        )

    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator to track method calls."""
        coordinator = MagicMock()
        coordinator.add_task = MagicMock()
        coordinator.remove_task_sync = MagicMock()
        return coordinator

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor."""
        executor = MagicMock()
        return executor

    @patch("yt_fts.download.batch_downloader.time")
    def test_add_task_not_called_when_video_list_is_empty(
        self,
        mock_time,
        downloader,
        mock_coordinator,
        mock_executor,
    ):
        """
        Test that coordinator.add_task() is NOT called when video list is empty.

        Given: rss_video_ids_for_download is an empty list
        When: _execute_ytdlp_download_for_channel is called
        Then: coordinator.add_task() should NOT be called

        This test FAILS with the current code because add_task() is called
        even when there are no videos to download, causing visual flashing.
        """
        # Arrange
        original_channel = "@testchannel"
        resolved_url = "https://youtube.com/@testchannel"
        channel_id = "UC_test123"
        rss_video_ids_for_download = []  # Empty list - no videos to download
        suppress_verbose = True
        target = 100
        successful_downloads = 0
        total_videos_saved = 0
        results = {"successful": [], "skipped": [], "errors": []}

        # Mock time for timeout logic
        mock_time.time.return_value = 1000
        downloader.batch_start_time = 0

        # Mock the future result
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 0,
            "total_videos": 0,
        }
        mock_executor.submit.return_value = mock_future

        # Act
        try:
            downloader._execute_ytdlp_download_for_channel(
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=mock_coordinator,
                executor=mock_executor,
                rss_video_ids_for_download=rss_video_ids_for_download,
                suppress_verbose=suppress_verbose,
                target=target,
                successful_downloads=successful_downloads,
                total_videos_saved=total_videos_saved,
                results=results,
            )
        except Exception as e:
            # We don't care about other failures, just the add_task call
            pass

        # Assert - add_task should NOT be called when video list is empty
        assert not mock_coordinator.add_task.called, (
            "coordinator.add_task() should NOT be called when rss_video_ids_for_download is empty. "
            "This prevents visual flashing from creating and immediately removing progress tasks."
        )

    @patch("yt_fts.download.batch_downloader.time")
    def test_add_task_not_called_when_video_list_is_none(
        self,
        mock_time,
        downloader,
        mock_coordinator,
        mock_executor,
    ):
        """
        Test that coordinator.add_task() is NOT called when video list is None.

        Given: rss_video_ids_for_download is None
        When: _execute_ytdlp_download_for_channel is called
        Then: coordinator.add_task() should NOT be called

        This test FAILS with the current code because add_task() is called
        even when there are no videos to download, causing visual flashing.
        """
        # Arrange
        original_channel = "@testchannel"
        resolved_url = "https://youtube.com/@testchannel"
        channel_id = "UC_test123"
        rss_video_ids_for_download = None  # None - no videos to download
        suppress_verbose = True
        target = 100
        successful_downloads = 0
        total_videos_saved = 0
        results = {"successful": [], "skipped": [], "errors": []}

        # Mock time for timeout logic
        mock_time.time.return_value = 1000
        downloader.batch_start_time = 0

        # Mock the future result
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 0,
            "total_videos": 0,
        }
        mock_executor.submit.return_value = mock_future

        # Act
        try:
            downloader._execute_ytdlp_download_for_channel(
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=mock_coordinator,
                executor=mock_executor,
                rss_video_ids_for_download=rss_video_ids_for_download,
                suppress_verbose=suppress_verbose,
                target=target,
                successful_downloads=successful_downloads,
                total_videos_saved=total_videos_saved,
                results=results,
            )
        except Exception as e:
            # We don't care about other failures, just the add_task call
            pass

        # Assert - add_task should NOT be called when video list is None
        assert not mock_coordinator.add_task.called, (
            "coordinator.add_task() should NOT be called when rss_video_ids_for_download is None. "
            "This prevents visual flashing from creating and immediately removing progress tasks."
        )

    @patch("yt_fts.download.batch_downloader.time")
    def test_add_task_called_when_video_list_has_videos(
        self,
        mock_time,
        downloader,
        mock_coordinator,
        mock_executor,
    ):
        """
        Test that coordinator.add_task() IS called when there are videos to download.

        Given: rss_video_ids_for_download contains video IDs
        When: _execute_ytdlp_download_for_channel is called
        Then: coordinator.add_task() SHOULD be called with correct parameters

        This test should PASS with the current code, verifying that the normal
        download flow still works correctly.
        """
        # Arrange
        original_channel = "@testchannel"
        resolved_url = "https://youtube.com/@testchannel"
        channel_id = "UC_test123"
        rss_video_ids_for_download = ["vid1", "vid2", "vid3"]  # Has videos
        suppress_verbose = True
        target = 100
        successful_downloads = 0
        total_videos_saved = 0
        results = {"successful": [], "skipped": [], "errors": []}

        # Mock time for timeout logic
        mock_time.time.return_value = 1000
        downloader.batch_start_time = 0

        # Mock the future result
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 3,
            "total_videos": 3,
        }
        mock_executor.submit.return_value = mock_future

        # Act
        try:
            downloader._execute_ytdlp_download_for_channel(
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=mock_coordinator,
                executor=mock_executor,
                rss_video_ids_for_download=rss_video_ids_for_download,
                suppress_verbose=suppress_verbose,
                target=target,
                successful_downloads=successful_downloads,
                total_videos_saved=total_videos_saved,
                results=results,
            )
        except Exception as e:
            # We don't care about other failures, just the add_task call
            pass

        # Assert - add_task SHOULD be called when there are videos
        assert mock_coordinator.add_task.called, (
            "coordinator.add_task() SHOULD be called when rss_video_ids_for_download has videos"
        )

        # Verify the call was made with correct parameters
        mock_coordinator.add_task.assert_called_once()
        call_kwargs = mock_coordinator.add_task.call_args.kwargs
        assert call_kwargs["channel_name"] == original_channel
        assert call_kwargs["total"] == 100
        assert call_kwargs["visible"] is True


class TestExecuteYtdlpDownloadProgressTaskRemoval:
    """Tests for progress bar task removal in _execute_ytdlp_download_for_channel."""

    @pytest.fixture
    def downloader(self):
        """Create BatchDownloader instance for testing."""
        return BatchDownloader(
            channels=["@testchannel"],
            suppress_quota_print=True,
            suppress_verbose=True,
        )

    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator to track method calls."""
        coordinator = MagicMock()
        coordinator.add_task = MagicMock()
        coordinator.remove_task_sync = MagicMock()
        return coordinator

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor."""
        executor = MagicMock()
        return executor

    @patch("yt_fts.download.batch_downloader.time")
    def test_remove_task_not_called_when_video_list_is_empty(
        self,
        mock_time,
        downloader,
        mock_coordinator,
        mock_executor,
    ):
        """
        Test that coordinator.remove_task_sync() is NOT called when video list is empty.

        Given: rss_video_ids_for_download is an empty list
        When: _execute_ytdlp_download_for_channel is called
        Then: coordinator.remove_task_sync() should NOT be called

        This verifies that we don't try to remove a task that was never created.
        """
        # Arrange
        original_channel = "@testchannel"
        resolved_url = "https://youtube.com/@testchannel"
        channel_id = "UC_test123"
        rss_video_ids_for_download = []
        suppress_verbose = True
        target = 100
        successful_downloads = 0
        total_videos_saved = 0
        results = {"successful": [], "skipped": [], "errors": []}

        # Mock time for timeout logic
        mock_time.time.return_value = 1000
        downloader.batch_start_time = 0

        # Mock the future result
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 0,
            "total_videos": 0,
        }
        mock_executor.submit.return_value = mock_future

        # Act
        try:
            downloader._execute_ytdlp_download_for_channel(
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=mock_coordinator,
                executor=mock_executor,
                rss_video_ids_for_download=rss_video_ids_for_download,
                suppress_verbose=suppress_verbose,
                target=target,
                successful_downloads=successful_downloads,
                total_videos_saved=total_videos_saved,
                results=results,
            )
        except Exception as e:
            pass

        # Assert - remove_task_sync should NOT be called when no task was created
        assert not mock_coordinator.remove_task_sync.called, (
            "coordinator.remove_task_sync() should NOT be called when rss_video_ids_for_download is empty"
        )

    @patch("yt_fts.download.batch_downloader.time")
    def test_remove_task_called_when_task_was_created(
        self,
        mock_time,
        downloader,
        mock_coordinator,
        mock_executor,
    ):
        """
        Test that coordinator.remove_task_sync() IS called when a task was created.

        Given: rss_video_ids_for_download contains video IDs
        When: _execute_ytdlp_download_for_channel is called
        Then: coordinator.remove_task_sync() SHOULD be called

        This test verifies the normal cleanup flow works correctly.
        """
        # Arrange
        original_channel = "@testchannel"
        resolved_url = "https://youtube.com/@testchannel"
        channel_id = "UC_test123"
        rss_video_ids_for_download = ["vid1", "vid2"]
        suppress_verbose = True
        target = 100
        successful_downloads = 0
        total_videos_saved = 0
        results = {"successful": [], "skipped": [], "errors": []}

        # Mock time for timeout logic
        mock_time.time.return_value = 1000
        downloader.batch_start_time = 0

        # Mock the future result
        mock_future = MagicMock()
        mock_future.result.return_value = {
            "success": True,
            "videos_count": 2,
            "total_videos": 2,
        }
        mock_executor.submit.return_value = mock_future

        # Act
        try:
            downloader._execute_ytdlp_download_for_channel(
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=mock_coordinator,
                executor=mock_executor,
                rss_video_ids_for_download=rss_video_ids_for_download,
                suppress_verbose=suppress_verbose,
                target=target,
                successful_downloads=successful_downloads,
                total_videos_saved=total_videos_saved,
                results=results,
            )
        except Exception as e:
            pass

        # Assert - remove_task_sync SHOULD be called when a task was created
        assert mock_coordinator.remove_task_sync.called, (
            "coordinator.remove_task_sync() SHOULD be called when a task was created"
        )
        mock_coordinator.remove_task_sync.assert_called_once_with(original_channel)
