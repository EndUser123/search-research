"""
Tests for video_jobs parameter in ParallelBatchProcessor.

Tests verify that:
1. ParallelBatchProcessor accepts video_jobs parameter
2. video_jobs is correctly passed to BatchDownloader initialization
3. Default value is 1 (sequential video processing)
"""

from unittest.mock import MagicMock, patch

import pytest


class TestVideoJobsParameter:
    """Test suite for video_jobs parameter on ParallelBatchProcessor."""

    def test_parallel_processor_accepts_video_jobs_parameter(self):
        """
        Test that ParallelBatchProcessor can be instantiated with video_jobs parameter.

        Given: A ParallelBatchProcessor class
        When: Instantiated with video_jobs parameter
        Then: The processor should be created successfully and store the video_jobs value
        """
        # Arrange & Act
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        processor = ParallelBatchProcessor(video_jobs=4)

        # Assert
        assert processor is not None
        assert hasattr(processor, "video_jobs")
        assert processor.video_jobs == 4

    def test_parallel_processor_video_jobs_default_value_is_1(self):
        """
        Test that video_jobs defaults to 1 when not provided.

        Given: A ParallelBatchProcessor class
        When: Instantiated without video_jobs parameter
        Then: The video_jobs attribute should default to 1 (sequential processing)
        """
        # Arrange & Act
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        processor = ParallelBatchProcessor()

        # Assert
        assert hasattr(processor, "video_jobs")
        assert processor.video_jobs == 1

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    @patch("yt_fts.download.parallel_processor.BatchDownloader")
    def test_video_jobs_passed_to_batch_downloader_in_simple_mode(
        self, mock_downloader, mock_backfill
    ):
        """
        Test that video_jobs is passed to BatchDownloader when using simple mode.

        Given: A ParallelBatchProcessor with video_jobs=3
        When: process_channels is called (simple output mode)
        Then: BatchDownloader should be initialized with jobs=3
        """
        # Arrange
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        channels = ["@test1", "@test2"]
        processor = ParallelBatchProcessor(video_jobs=3)

        mock_instance = MagicMock()
        mock_instance.process_single_channel.return_value = {
            "successful": [{"channel": "@test1", "videos_count": 5}],
            "failed": [],
            "skipped": [],
        }
        mock_downloader.return_value = mock_instance
        mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

        # Act
        processor.process_channels(channels, num_workers=1)

        # Assert
        # BatchDownloader should be called with jobs=video_jobs (3 in this case)
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert "jobs" in call_kwargs
        assert call_kwargs["jobs"] == 3

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    @patch("yt_fts.download.parallel_processor.BatchDownloader")
    def test_video_jobs_default_1_passed_to_batch_downloader(
        self, mock_downloader, mock_backfill
    ):
        """
        Test that default video_jobs=1 is passed to BatchDownloader.

        Given: A ParallelBatchProcessor without explicit video_jobs
        When: process_channels is called
        Then: BatchDownloader should be initialized with jobs=1 (default)
        """
        # Arrange
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        channels = ["@test1"]
        processor = ParallelBatchProcessor()  # No video_jobs specified

        mock_instance = MagicMock()
        mock_instance.process_single_channel.return_value = {
            "successful": [],
            "failed": [],
            "skipped": [],
        }
        mock_downloader.return_value = mock_instance
        mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

        # Act
        processor.process_channels(channels, num_workers=1)

        # Assert
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert "jobs" in call_kwargs
        assert call_kwargs["jobs"] == 1

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    @patch("yt_fts.download.parallel_processor.BatchDownloader")
    @pytest.mark.skip(reason="Rich mode threading mock needs fixing - deadlocks on as_completed")
    def test_video_jobs_passed_to_batch_downloader_in_rich_mode(
        self, mock_downloader, mock_backfill
    ):
        """
        Test that video_jobs is passed to BatchDownloader when using Rich progress mode.

        Given: A ParallelBatchProcessor with video_jobs=2 and use_rich_progress=True
        When: process_channels is called (Rich progress mode)
        Then: BatchDownloader should be initialized with jobs=2
        """
        # Arrange
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        channels = ["@test1"]
        processor = ParallelBatchProcessor(
            video_jobs=2, use_rich_progress=True
        )

        mock_instance = MagicMock()
        mock_instance.process_single_channel.return_value = {
            "successful": [],
            "failed": [],
            "skipped": [],
        }
        mock_downloader.return_value = mock_instance
        mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

        # Act
        with patch("yt_fts.download.parallel_processor.RICH_AVAILABLE", True):
            with patch("yt_fts.download.parallel_processor.RichParallelProgress"):
                processor.process_channels(channels, num_workers=1)

        # Assert
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert "jobs" in call_kwargs
        assert call_kwargs["jobs"] == 2

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    @patch("yt_fts.download.parallel_processor.BatchDownloader")
    def test_video_jobs_passed_to_batch_downloader_in_json_mode(
        self, mock_downloader, mock_backfill
    ):
        """
        Test that video_jobs is passed to BatchDownloader when using JSON output mode.

        Given: A ParallelBatchProcessor with video_jobs=5 and use_json=True
        When: process_channels is called (JSON output mode)
        Then: BatchDownloader should be initialized with jobs=5
        """
        # Arrange
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        channels = ["@test1"]
        processor = ParallelBatchProcessor(
            video_jobs=5, use_json=True
        )

        mock_instance = MagicMock()
        mock_instance.process_single_channel.return_value = {
            "successful": [],
            "failed": [],
            "skipped": [],
        }
        mock_downloader.return_value = mock_instance
        mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

        # Act
        processor.process_channels(channels, num_workers=1)

        # Assert
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert "jobs" in call_kwargs
        assert call_kwargs["jobs"] == 5

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    @patch("yt_fts.download.parallel_processor.BatchDownloader")
    def test_video_jobs_passed_to_batch_downloader_in_fzf_mode(
        self, mock_downloader, mock_backfill
    ):
        """
        Test that video_jobs is passed to BatchDownloader when using fzf output mode.

        Given: A ParallelBatchProcessor with video_jobs=4 and use_fzf=True
        When: process_channels is called (fzf output mode)
        Then: BatchDownloader should be initialized with jobs=4
        """
        # Arrange
        from yt_fts.download.parallel_processor import ParallelBatchProcessor

        channels = ["@test1"]
        processor = ParallelBatchProcessor(
            video_jobs=4, use_fzf=True
        )

        mock_instance = MagicMock()
        mock_instance.process_single_channel.return_value = {
            "successful": [],
            "failed": [],
            "skipped": [],
        }
        mock_downloader.return_value = mock_instance
        mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

        # Act
        processor.process_channels(channels, num_workers=1)

        # Assert
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert "jobs" in call_kwargs
        assert call_kwargs["jobs"] == 4
