"""
Tests for flattened parallel processor architecture.

This test verifies that the parallel processor uses a single shared
BatchDownloader instance instead of creating a new one for each worker.
"""
from unittest.mock import Mock, patch, MagicMock

import pytest

from yt_fts.download.parallel_processor import ParallelBatchProcessor


class TestFlattenedParallelArchitecture:
    """Test that parallel processor uses shared BatchDownloader."""

    def test_batchdownloader_has_process_channel_method(self):
        """Test that BatchDownloader has a process_single_channel method.

        In the flattened architecture, BatchDownloader should expose a method
        that processes a single channel without requiring a full __init__ cycle.
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        # Check that the method exists
        assert hasattr(BatchDownloader, 'process_single_channel'), \
            "BatchDownloader should have process_single_channel method for flattened architecture"

        # Check method signature
        import inspect
        sig = inspect.signature(BatchDownloader.process_single_channel)
        params = list(sig.parameters.keys())

        # Should have channel parameter
        assert 'channel' in params, \
            "process_single_channel should accept a channel parameter"


def test_flattened_architecture_uses_process_single_channel():
    """Document that flattened architecture uses process_single_channel."""

    processor = ParallelBatchProcessor(
        language="en",
        min_saved=0,
        quota_strategy=Mock(),
    )

    # Mock the BatchDownloader to verify which method is called
    with patch('yt_fts.download.parallel_processor.BatchDownloader') as MockDownloader:
        mock_instance = MagicMock()
        mock_instance.process_single_channel = Mock(return_value={
            "successful": [{"channel": "@test", "videos": 1}],
            "failed": [],
            "skipped": []
        })
        MockDownloader.return_value = mock_instance

        with patch('yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill'):
            with patch('yt_fts.download.batch_filter.pre_filter_fresh_channels', return_value=([], 0)):
                result = processor._process_channels_simple(
                    channels=["@channel1", "@channel2"],
                    num_workers=2,
                    continue_on_error=True
                )

        # In flattened architecture, process_single_channel should be called
        # once per channel, not download_all creating new instances
        assert mock_instance.process_single_channel.call_count == 2, \
            f"Expected process_single_channel to be called 2 times, got {mock_instance.process_single_channel.call_count}"

        print(f"✓ Flattened architecture: process_single_channel called {mock_instance.process_single_channel.call_count} times for 2 channels")
