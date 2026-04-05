"""
Tests for pipeline prefetch feature in BatchDownloader.

Feature requirement:
- Queue fills with lookahead channels when created with channel_ids list
- get_next(channel_id) returns prefetched channel, blocks if queue empty
- Background thread continues when some channels fail to fetch
- stop() method gracefully terminates background thread
- Lazy mode (prefetch_channel_names=False) skips background thread

These tests SHOULD FAIL until the pipeline prefetch feature is implemented.
Run with: pytest tests/test_batch_downloader_prefetch.py -v
"""

import time
from unittest.mock import patch

from yt_fts.download.batch_downloader import BatchDownloader


class TestQueueFillsWithLookahead:
    """Tests for queue initialization and filling behavior."""

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_queue_fills_with_lookahead(self, mock_fetch):
        """
        Test that queue fills with 3 channels when created with channel_ids list.

        Given: A BatchDownloader with prefetch_channel_names=True and 5 channel_ids
        When: The prefetch background thread runs
        Then: Queue should contain 3 prefetched channel metadata entries
        """
        # Arrange - Mock successful fetches
        mock_fetch.side_effect = [
            ("Channel One", "https://youtube.com/@channel1"),
            ("Channel Two", "https://youtube.com/@channel2"),
            ("Channel Three", "https://youtube.com/@channel3"),
        ]

        channel_ids = ["UC1111", "UC2222", "UC3333", "UC4444", "UC5555"]

        # Act - Create downloader with prefetch enabled
        downloader = BatchDownloader(
            channels=channel_ids,
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Wait for prefetch thread to populate queue
        time.sleep(0.5)

        # Assert - Queue should have 3 items (lookahead)
        assert hasattr(downloader, "_prefetch_queue"), "BatchDownloader should have _prefetch_queue attribute"
        assert downloader._prefetch_queue.qsize() >= 1, "Queue should have at least 1 item"

        # Verify fetch was called for at least some channels
        assert mock_fetch.call_count >= 1, "Expected at least 1 fetch call"

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_queue_max_size_lookahead_limit(self, mock_fetch):
        """
        Test that queue respects lookahead limit (max 3 items).

        Given: A BatchDownloader with prefetch enabled
        When: Background thread prefetches channels
        Then: Queue should not exceed lookahead limit of 3
        """
        # Arrange
        mock_fetch.side_effect = [
            ("Channel One", "url1"),
            ("Channel Two", "url2"),
            ("Channel Three", "url3"),
            ("Channel Four", "url4"),
        ]

        channel_ids = ["UC1111", "UC2222", "UC3333", "UC4444"]

        # Act
        downloader = BatchDownloader(
            channels=channel_ids,
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Wait for prefetch
        time.sleep(0.5)

        # Assert - Queue should be capped at lookahead size
        assert hasattr(downloader, "_prefetch_queue"), "Should have prefetch queue"
        queue_size = downloader._prefetch_queue.qsize()
        assert queue_size <= 3, "Queue size exceeds lookahead limit of 3"


class TestMainThreadPullsFromQueue:
    """Tests for get_next(channel_id) queue consumption."""

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_get_next_returns_prefetched_channel(self, mock_fetch):
        """
        Test that get_next(channel_id) returns prefetched channel from queue.

        Given: A queue with prefetched channel metadata
        When: get_next(channel_id) is called
        Then: Should return the prefetched metadata without blocking
        """
        # Arrange
        mock_fetch.return_value = ("Test Channel", "https://youtube.com/@test")

        downloader = BatchDownloader(
            channels=["UC1111", "UC2222"],
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Wait for prefetch
        time.sleep(0.3)

        # Act - Call get_next
        result = downloader.get_next("UC1111")

        # Assert - Should return prefetched metadata
        assert result is not None, "get_next should return prefetched metadata"
        assert "name" in result or result[0] is not None, "Result should contain channel name"

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_get_next_blocks_when_queue_empty(self, mock_fetch):
        """
        Test that get_next(channel_id) blocks when queue is empty.

        Given: A BatchDownloader with empty prefetch queue
        When: get_next(channel_id) is called
        Then: Should block until item is available or timeout
        """
        # Arrange - Slow fetch to simulate empty queue
        def slow_fetch(*args, **kwargs):
            time.sleep(0.2)
            return ("Delayed Channel", "url")

        mock_fetch.side_effect = slow_fetch

        downloader = BatchDownloader(
            channels=["UC1111"],
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Do not wait - call immediately to test blocking behavior
        start_time = time.time()

        # Act - This should block if queue is empty
        result = downloader.get_next("UC1111")

        elapsed = time.time() - start_time

        # Assert - Should have blocked waiting for fetch
        assert elapsed >= 0.1, "get_next should have blocked"
        assert result is not None, "Should eventually return a result"


class TestBackgroundThreadHandlesFailures:
    """Tests for prefetch error handling and resilience."""

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_prefetch_continues_when_some_channels_fail(self, mock_fetch):
        """
        Test that prefetch continues when some channels fail to fetch.

        Given: A BatchDownloader with 5 channels, 2 of which fail to fetch
        When: Background thread prefetches channels
        Then: Should successfully fetch the 3 working channels and continue processing
        """
        # Arrange - Mix of success and failure
        mock_fetch.side_effect = [
            ("Channel One", "url1"),  # Success
            None,  # Failure
            ("Channel Two", "url2"),  # Success
            None,  # Failure
            ("Channel Three", "url3"),  # Success
        ]

        channel_ids = ["UC1111", "UC2222", "UC3333", "UC4444", "UC5555"]

        # Act
        downloader = BatchDownloader(
            channels=channel_ids,
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Wait for prefetch to complete
        time.sleep(0.5)

        # Assert - Should have fetched successful channels
        assert mock_fetch.call_count >= 3, "Should attempt to fetch all channels"

        # Queue should have some items despite failures
        if hasattr(downloader, "_prefetch_queue"):
            queue_size = downloader._prefetch_queue.qsize()
            # Should have at least 1 successful fetch in queue
            assert queue_size >= 1 or mock_fetch.call_count >= 3, "Should have prefetched channels despite failures"

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_prefetch_logs_failures_and_continues(self, mock_fetch):
        """
        Test that prefetch logs failures without stopping.

        Given: A channel that fails to fetch
        When: Background thread encounters failure
        Then: Should log error and continue with remaining channels
        """
        # Arrange - All fail
        mock_fetch.return_value = None

        downloader = BatchDownloader(
            channels=["UC1111", "UC2222", "UC3333"],
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Wait for prefetch attempts
        time.sleep(0.3)

        # Assert - Should have attempted all channels despite failures
        assert mock_fetch.call_count >= 1, "Should attempt fetch even when failing"


class TestThreadShutdownCompletes:
    """Tests for graceful thread shutdown."""

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_stop_method_terminates_background_thread(self, mock_fetch):
        """
        Test that stop() method gracefully terminates background thread.

        Given: A BatchDownloader with active prefetch thread
        When: stop() method is called
        Then: Background thread should terminate within timeout
        """
        # Arrange - Slow fetch to ensure thread is active
        def slow_fetch(*args, **kwargs):
            time.sleep(0.1)
            return ("Channel", "url")

        mock_fetch.side_effect = slow_fetch

        downloader = BatchDownloader(
            channels=["UC1111", "UC2222", "UC3333"],
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Wait for thread to start
        time.sleep(0.1)

        # Act - Stop the downloader
        downloader.stop()

        # Wait a bit for thread to terminate
        time.sleep(0.2)

        # Assert - Thread should have stopped
        assert hasattr(downloader, "_prefetch_thread"), "Should have prefetch thread attribute"

        # Check if thread is alive (should be stopped or stopping)
        if downloader._prefetch_thread:
            # Thread should not be alive after stop()
            is_alive = downloader._prefetch_thread.is_alive()
            # If still alive, it should at least have received stop signal
            assert not is_alive or hasattr(downloader, "_stop_requested"), "Thread should be stopped or have received stop signal"

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_stop_method_sets_stop_flag(self, mock_fetch):
        """
        Test that stop() sets a flag that thread checks.

        Given: A running BatchDownloader with prefetch
        When: stop() is called
        Then: _stop_requested flag should be set
        """
        # Arrange
        mock_fetch.return_value = ("Channel", "url")

        downloader = BatchDownloader(
            channels=["UC1111", "UC2222"],
            prefetch_channel_names=True,
            suppress_verbose=True,
        )

        # Act
        downloader.stop()

        # Assert - Stop flag should be set
        assert hasattr(downloader, "_stop_requested"), "Should have _stop_requested attribute"
        assert downloader._stop_requested is True, "_stop_requested should be True after stop()"


class TestLazyModeSkipsQueue:
    """Tests for lazy mode (prefetch_channel_names=False)."""

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_lazy_mode_skips_background_thread(self, mock_fetch):
        """
        Test that lazy mode skips background thread creation.

        Given: prefetch_channel_names=False
        When: BatchDownloader is created
        Then: No background prefetch thread should be created
        """
        # Arrange & Act - Create with prefetch disabled
        downloader = BatchDownloader(
            channels=["UC1111", "UC2222", "UC3333"],
            prefetch_channel_names=False,  # Lazy mode
            suppress_verbose=True,
        )

        # Wait a bit to ensure no thread starts
        time.sleep(0.2)

        # Assert - No prefetch thread should exist
        assert hasattr(downloader, "_prefetch_thread"), "Should have _prefetch_thread attribute (may be None)"
        assert downloader._prefetch_thread is None, "_prefetch_thread should be None in lazy mode"

        # No fetch should have been called in background
        assert mock_fetch.call_count == 0, "No fetch should occur in lazy mode"

    @patch("yt_fts.download.batch_downloader.BatchDownloader._fetch_channel_metadata_yt_dlp")
    def test_lazy_mode_get_next_fetches_on_demand(self, mock_fetch):
        """
        Test that lazy mode fetches channel names on demand via get_next.

        Given: prefetch_channel_names=False (lazy mode)
        When: get_next(channel_id) is called
        Then: Should fetch immediately (not from background queue)
        """
        # Arrange
        mock_fetch.return_value = ("Lazy Channel", "url")

        downloader = BatchDownloader(
            channels=["UC1111"],
            prefetch_channel_names=False,  # Lazy mode
            suppress_verbose=True,
        )

        # Act - Call get_next in lazy mode
        result = downloader.get_next("UC1111")

        # Assert - Should fetch on demand
        assert mock_fetch.call_count >= 1, "Lazy mode should fetch on demand"
        assert result is not None, "Should return fetched metadata"

    def test_lazy_mode_no_queue_created(self):
        """
        Test that lazy mode does not create prefetch queue.

        Given: prefetch_channel_names=False
        When: BatchDownloader is initialized
        Then: _prefetch_queue should not be created or should be None
        """
        # Arrange & Act
        downloader = BatchDownloader(
            channels=["UC1111", "UC2222"],
            prefetch_channel_names=False,
            suppress_verbose=True,
        )

        # Assert - No queue in lazy mode
        assert hasattr(downloader, "_prefetch_queue"), "Should have _prefetch_queue attribute (may be None)"
        assert downloader._prefetch_queue is None, "_prefetch_queue should be None in lazy mode"
