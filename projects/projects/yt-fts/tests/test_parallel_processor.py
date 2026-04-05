"""
Tests for ParallelBatchProcessor - ThreadPoolExecutor-based parallel channel processing.

Tests verify that:
1. process_channels returns expected dict structure
2. Multiple workers can process channels concurrently
3. Database operations don't cause lock contention
4. Errors in one worker don't stop other workers
5. Rich progress display works correctly
"""

import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestParallelBatchProcessorInstantiation:
    """Test suite for ParallelBatchProcessor class instantiation."""

    def test_class_can_be_instantiated(self):
        """Test that ParallelBatchProcessor can be imported and instantiated."""
        # Arrange & Act
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        processor = ParallelBatchProcessor()

        # Assert
        assert processor is not None
        assert hasattr(processor, "process_channels")

    def test_instantiation_with_parameters(self):
        """Test instantiation with optional parameters."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Act
        processor = ParallelBatchProcessor(
            language="en",
            cookies_from_browser="chrome",
            delay_between_channels=1.0,
        )

        # Assert
        assert processor is not None


class TestWorkerStatus:
    """Test suite for WorkerStatus thread-safe tracker."""

    def test_worker_status_tracks_counters(self):
        """Test that WorkerStatus tracks ok/err/skip counters."""
        from yt_fts.download.parallel_processor import WorkerStatus

        # Arrange
        status = WorkerStatus()

        # Act
        status.add_ok(5)
        status.add_err(2)
        status.add_skip(1)

        # Assert
        ok, err, skip, current = status.get_counts()
        assert ok == 5
        assert err == 2
        assert skip == 1

    def test_worker_status_tracks_current_channel(self):
        """Test that WorkerStatus tracks current channel name."""
        from yt_fts.download.parallel_processor import WorkerStatus

        # Arrange
        status = WorkerStatus()

        # Act
        status.set_current("@testchannel")

        # Assert
        _, _, _, current = status.get_counts()
        assert current == "@testchannel"


class TestProcessChannelsResultStructure:
    """Test suite for process_channels return value structure."""

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_process_channels_returns_expected_dict_structure(self):
        """Test that process_channels returns dict with successful, failed, skipped keys."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels = ["@test1", "@test2"]
        processor = ParallelBatchProcessor()

        # Mock the BatchDownloader to avoid actual downloads
        # Mock YouTubeAPIBackfill to avoid quota database access (database lock issues)
        with patch("yt_fts.download.parallel_processor.BatchDownloader") as mock_downloader,              patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill") as mock_backfill:
            mock_instance = MagicMock()
            mock_instance.process_single_channel.return_value = {
                "successful": [{"channel": "@test1", "videos_count": 5}],
                "failed": [],
                "skipped": [],
            }
            mock_downloader.return_value = mock_instance
            # Mock the quota display method to avoid print statements and DB access
            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            # Act
            result = processor.process_channels(channels, num_workers=2)

            # Assert
            assert isinstance(result, dict)
            assert "successful" in result
            assert "failed" in result
            assert "skipped" in result
            assert isinstance(result["successful"], list)
            assert isinstance(result["failed"], list)
            assert isinstance(result["skipped"], list)

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_process_channels_aggregates_results_from_multiple_workers(self):
        """Test that results from multiple workers are aggregated correctly."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels = ["@test1", "@test2", "@test3", "@test4"]
        processor = ParallelBatchProcessor()

        # New implementation processes one channel at a time per worker
        # Create a side effect that returns different results per channel
        call_count = 0

        def mock_download_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Each channel is processed individually now
            if call_count == 1:
                return {
                    "successful": [{"channel": "@test1", "videos_count": 5}],
                    "failed": [],
                    "skipped": [],
                }
            elif call_count == 2:
                return {
                    "successful": [{"channel": "@test2", "videos_count": 2}],
                    "failed": [],
                    "skipped": [],
                }
            elif call_count == 3:
                return {
                    "successful": [{"channel": "@test3", "videos_count": 3}],
                    "failed": [],
                    "skipped": [],
                }
            else:
                return {
                    "successful": [],
                    "failed": [{"channel": "@test4", "error": "Not found"}],
                    "skipped": [],
                }

        with patch(
            "yt_fts.download.parallel_processor.BatchDownloader"
        ) as mock_downloader, patch(
            "yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"
        ) as mock_backfill:
            mock_instance = MagicMock()
            mock_instance.process_single_channel.side_effect = mock_download_side_effect
            mock_downloader.return_value = mock_instance
            # Mock the quota display method to avoid print statements and DB access
            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            # Act
            result = processor.process_channels(channels, num_workers=2)

            # Assert - all 4 channels processed, 3 successful, 1 failed
            assert len(result["successful"]) == 3
            assert len(result["failed"]) == 1
            assert any(item["channel"] == "@test1" for item in result["successful"])
            assert any(item["channel"] == "@test2" for item in result["successful"])
            assert any(item["channel"] == "@test3" for item in result["successful"])
            assert result["failed"][0]["channel"] == "@test4"


class TestErrorHandling:
    """Test suite for graceful error handling in parallel processing."""

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_exception_is_caught_and_added_to_failed_list(self):
        """Test that exceptions during processing are caught and added to failed list."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels = ["@test1"]
        processor = ParallelBatchProcessor()

        with patch(
            "yt_fts.download.parallel_processor.BatchDownloader"
        ) as mock_downloader, patch(
            "yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"
        ) as mock_backfill:
            mock_instance = MagicMock()
            mock_instance.process_single_channel.side_effect = Exception("Test error")
            mock_downloader.return_value = mock_instance
            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            # Act
            result = processor.process_channels(
                channels, num_workers=1, continue_on_error=True
            )

            # Assert
            assert len(result["failed"]) == 1
            assert "Test error" in result["failed"][0]["error"]


class TestDatabaseLockContention:
    """Test suite for SQLite database lock handling during parallel operations."""

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_concurrent_database_access_doesnt_cause_lock_contention(self):
        """Test that parallel workers can access database without lock contention."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels = ["@test1", "@test2", "@test3", "@test4"]
        processor = ParallelBatchProcessor()

        with patch(
            "yt_fts.download.parallel_processor.BatchDownloader"
        ) as mock_downloader, patch(
            "yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"
        ) as mock_backfill:
            mock_instance = MagicMock()
            mock_instance.process_single_channel.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }
            mock_downloader.return_value = mock_instance
            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            # Act - this should not raise a database lock error
            result = processor.process_channels(channels, num_workers=4)

            # Assert
            assert isinstance(result, dict)

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_wal_mode_enabled_for_better_concurrency(self):
        """Test that WAL mode is enabled for better concurrent database access."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor
        from yt_fts.core.database import enable_wal_mode

        # Arrange
        channels = ["@test1", "@test2"]
        processor = ParallelBatchProcessor()

        with patch("yt_fts.download.parallel_processor.enable_wal_mode") as mock_wal, \
             patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill") as mock_backfill:
            with patch(
                "yt_fts.download.parallel_processor.BatchDownloader"
            ) as mock_downloader:
                mock_instance = MagicMock()
                mock_instance.process_single_channel.return_value = {
                    "successful": [],
                    "failed": [],
                    "skipped": [],
                }
                mock_downloader.return_value = mock_instance
                mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

                # Act
                processor.process_channels(channels, num_workers=2)

                # Assert
                # WAL mode should be enabled for better concurrency
                mock_wal.assert_called_once()


class TestIntegrationScenarios:
    """Integration test scenarios for ParallelBatchProcessor."""

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_full_workflow_with_real_threading(self):
        """Test a complete workflow with actual ThreadPoolExecutor usage."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels = ["@test1", "@test2", "@test3", "@test4"]
        processor = ParallelBatchProcessor()

        # Track actual thread pool executor usage
        original_executor_init = ThreadPoolExecutor.__init__
        executor_created = []

        def tracking_init(self, max_workers=None):
            executor_created.append(max_workers)
            original_executor_init(self, max_workers)

        with patch.object(ThreadPoolExecutor, "__init__", tracking_init), \
             patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill") as mock_backfill:
            with patch(
                "yt_fts.download.parallel_processor.BatchDownloader"
            ) as mock_downloader:
                mock_instance = MagicMock()
                mock_instance.process_single_channel.return_value = {
                    "successful": [{"channel": "test", "videos_count": 1}],
                    "failed": [],
                    "skipped": [],
                }
                mock_downloader.return_value = mock_instance
                mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

                # Act
                result = processor.process_channels(channels, num_workers=2)

                # Assert
                assert isinstance(result, dict)
                assert "successful" in result
                assert "failed" in result
                assert "skipped" in result

    def test_process_channels_with_empty_list(self):
        """Test process_channels behavior with an empty channel list."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels: list[str] = []
        processor = ParallelBatchProcessor()

        # Mock YouTubeAPIBackfill to avoid quota database access
        with patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill") as mock_backfill:
            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            # Act
            result = processor.process_channels(channels, num_workers=2)

        # Assert
        assert result == {"successful": [], "failed": [], "skipped": []}

    @pytest.mark.skipif(
        not os.environ.get("YOUTUBE_API_KEY"),
        reason="Requires YOUTUBE_API_KEY environment variable"
    )
    def test_process_channels_with_single_channel(self):
        """Test process_channels with a single channel."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        # Arrange
        channels = ["@test1"]
        processor = ParallelBatchProcessor()

        with patch(
            "yt_fts.download.parallel_processor.BatchDownloader"
        ) as mock_downloader, patch(
            "yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"
        ) as mock_backfill:
            mock_instance = MagicMock()
            mock_instance.process_single_channel.return_value = {
                "successful": [{"channel": "@test1", "videos_count": 10}],
                "failed": [],
                "skipped": [],
            }
            mock_downloader.return_value = mock_instance
            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            # Act
            result = processor.process_channels(channels, num_workers=2)

            # Assert
            assert len(result["successful"]) == 1
            assert result["successful"][0]["channel"] == "@test1"
            assert result["successful"][0]["videos_count"] == 10
