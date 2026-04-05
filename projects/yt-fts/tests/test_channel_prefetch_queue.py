"""
Tests for ChannelPrefetchQueue - async channel metadata prefetching.

Tests cover:
- Thread-safe initialization and lifecycle
- Database-backed result storage
- Progress tracking and completion detection
- Error handling and recovery
- Stop/join functionality
"""

import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from yt_fts.download.channel_prefetch_queue import ChannelPrefetchQueue


class TestChannelPrefetchQueueInitialization:
    """Tests for ChannelPrefetchQueue initialization and basic setup."""

    def test_initialization_with_required_params(self):
        """Test that queue initializes with required parameters."""
        fetcher = Mock(return_value=("Test Channel", "https://youtube.com/channel/UC123"))
        channel_ids = ["UC123", "UC456"]

        queue = ChannelPrefetchQueue(channel_ids, fetcher=fetcher)

        assert queue.channel_ids == channel_ids
        assert queue._fetcher == fetcher
        assert queue._total == 2
        assert not queue._started
        assert not queue._stopped
        assert len(queue._completed) == 0

    def test_initialization_with_optional_params(self):
        """Test that queue accepts optional parameters."""
        fetcher = Mock()
        console = Mock()
        channel_ids = ["UC123"]

        queue = ChannelPrefetchQueue(
            channel_ids,
            fetcher=fetcher,
            console=console,
            suppress_verbose=True,
            max_workers=4,
        )

        assert queue.console == console
        assert queue.suppress_verbose is True
        assert queue.max_workers == 4

    def test_initialization_with_empty_channel_list(self):
        """Test that empty channel list is handled correctly."""
        queue = ChannelPrefetchQueue([], fetcher=Mock())
        assert queue._total == 0
        assert queue.channel_ids == []


class TestChannelPrefetchQueueLifecycle:
    """Tests for queue lifecycle: start, stop, join."""

    def test_start_begins_background_thread(self):
        """Test that start() creates and starts background thread."""
        import time
        
        fetcher = Mock(return_value=("Name", "https://url"))
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            # Mock DB to return no existing names (so channel needs fetching)
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute().fetchall.return_value = []
            queue._get_db_connection = Mock(return_value=mock_conn)
            queue._add_channel_info = Mock()
            
            queue.start()
            # Give thread a moment to start
            time.sleep(0.01)

        assert queue._started is True
        assert queue._thread is not None
        # Thread should either be alive or have completed successfully
        assert queue._thread.is_alive() or queue.is_complete()

        # Cleanup
        queue.stop()
        queue.join(timeout=5.0)

    def test_start_is_idempotent(self):
        """Test that calling start() multiple times is safe."""
        fetcher = Mock(return_value=("Name", "https://url"))
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            queue.start()
            first_thread = queue._thread
            queue.start()
            second_thread = queue._thread

        assert first_thread is second_thread  # Same thread, not recreated

        # Cleanup
        queue.stop()
        queue.join(timeout=5.0)

    def test_stop_signals_thread_to_stop(self):
        """Test that stop() sets stopped flag."""
        queue = ChannelPrefetchQueue(["UC123"], fetcher=Mock())
        queue.stop()

        assert queue._stopped is True

    def test_join_waits_for_thread_completion(self):
        """Test that join() waits for background thread."""
        fetcher = Mock(return_value=("Name", "https://url"))
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            queue.start()
            result = queue.join(timeout=5.0)

        assert result is True  # Thread completed
        assert not queue._thread.is_alive()

    def test_join_with_timeout_returns_false_if_not_complete(self):
        """Test that join() returns False if thread doesn't complete in time."""
        # Create a fetcher that takes a long time
        def slow_fetcher(channel_id):
            time.sleep(10)  # Longer than timeout
            return ("Name", "https://url")

        queue = ChannelPrefetchQueue(["UC123"], fetcher=slow_fetcher)

        with patch.object(queue, "_init_db_functions"):
            # Mock DB to return no existing names (so channel needs fetching)
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute().fetchall.return_value = []
            queue._get_db_connection = Mock(return_value=mock_conn)
            queue._add_channel_info = Mock()
            
            queue.start()
            result = queue.join(timeout=0.1)  # Short timeout

        assert result is False  # Thread didn't complete
        queue.stop()


class TestChannelPrefetchQueueDatabaseIntegration:
    """Tests for database-backed result storage."""

    def test_is_ready_checks_completed_set(self):
        """Test that is_ready() checks completed channels."""
        fetcher = Mock(return_value=("Name", "https://url"))
        queue = ChannelPrefetchQueue(["UC123", "UC456"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            # Mark one as completed
            with queue._lock:
                queue._completed.add("UC123")

            assert queue.is_ready("UC123") is True
            assert queue.is_ready("UC456") is False

    def test_is_ready_queries_database_if_not_completed(self):
        """Test that is_ready() falls back to database query."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        # Mock DB query to return a name
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute().fetchone.return_value = ["Channel Name"]

        with patch.object(queue, "_init_db_functions"):
            queue._get_db_connection = Mock(return_value=mock_conn)

            assert queue.is_ready("UC123") is True

    def test_get_name_retrieves_from_database(self):
        """Test that get_name() retrieves channel name from database."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        # Mock DB query
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute().fetchone.return_value = ["Test Channel"]

        with patch.object(queue, "_init_db_functions"):
            queue._get_db_connection = Mock(return_value=mock_conn)

            name = queue.get_name("UC123")

        assert name == "Test Channel"

    def test_get_name_returns_none_if_not_found(self):
        """Test that get_name() returns None if channel not in database."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        # Mock DB query to return None
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute().fetchone.return_value = None

        with patch.object(queue, "_init_db_functions"):
            queue._get_db_connection = Mock(return_value=mock_conn)

            name = queue.get_name("UC123")

        assert name is None


class TestChannelPrefetchQueueProgress:
    """Tests for progress tracking and reporting."""

    def test_get_progress_returns_completed_and_total(self):
        """Test that get_progress() returns (completed, total) tuple."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123", "UC456", "UC789"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            with queue._lock:
                queue._completed.update(["UC123", "UC456"])

            completed, total = queue.get_progress()

        assert completed == 2
        assert total == 3

    def test_is_complete_returns_true_when_all_done(self):
        """Test that is_complete() returns True when all channels processed."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123", "UC456"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            with queue._lock:
                queue._completed.update(["UC123", "UC456"])

            assert queue.is_complete() is True

    def test_is_complete_returns_false_when_incomplete(self):
        """Test that is_complete() returns False when channels pending."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123", "UC456"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            with queue._lock:
                queue._completed.add("UC123")

            assert queue.is_complete() is False


class TestChannelPrefetchQueueWaitFor:
    """Tests for wait_for() blocking behavior."""

    def test_wait_for_returns_true_when_ready(self):
        """Test that wait_for() returns True when channel becomes ready."""
        fetcher = Mock(return_value=("Name", "https://url"))
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            # Simulate channel becoming ready
            def delayed_ready():
                time.sleep(0.1)
                with queue._lock:
                    queue._completed.add("UC123")

            threading.Thread(target=delayed_ready).start()
            result = queue.wait_for("UC123", timeout=1.0)

        assert result is True

    def test_wait_for_returns_false_on_timeout(self):
        """Test that wait_for() returns False when timeout expires."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            # Don't mark as completed - trigger timeout
            result = queue.wait_for("UC123", timeout=0.1)

        assert result is False

    def test_wait_for_returns_immediately_if_already_ready(self):
        """Test that wait_for() returns immediately if channel already ready."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            with queue._lock:
                queue._completed.add("UC123")

            start = time.time()
            result = queue.wait_for("UC123", timeout=5.0)
            elapsed = time.time() - start

        assert result is True
        assert elapsed < 0.1  # Should return immediately


class TestChannelPrefetchQueueWorker:
    """Tests for background worker behavior."""

    def test_worker_fetches_missing_channels(self):
        """Test that worker fetches channels not in database."""
        # This test verifies the worker calls the fetcher for missing channels
        fetcher = Mock(return_value=("Test Channel", "https://url"))
        add_channel_info = Mock()
        queue = ChannelPrefetchQueue(["UC123", "UC456"], fetcher=fetcher, suppress_verbose=True)

        with patch.object(queue, "_init_db_functions"):
            queue._add_channel_info = add_channel_info
            # Mock DB query to return no existing names
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute().fetchall.return_value = []
            queue._get_db_connection = Mock(return_value=mock_conn)

            queue._prefetch_worker()

        # Should have called fetcher for both channels
        assert fetcher.call_count == 2
        # Should have saved both to database
        assert add_channel_info.call_count == 2

    def test_worker_skips_channels_already_in_database(self):
        """Test that worker skips channels that already have names."""
        fetcher = Mock(return_value=("Name", "https://url"))
        add_channel_info = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher, suppress_verbose=True)

        with patch.object(queue, "_init_db_functions"):
            queue._add_channel_info = add_channel_info
            # Mock DB query to return existing name
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute().fetchall.return_value = [("UC123", "Existing Channel")]
            queue._get_db_connection = Mock(return_value=mock_conn)

            queue._prefetch_worker()

        # Should not have called fetcher (channel already in DB)
        fetcher.assert_not_called()
        add_channel_info.assert_not_called()

    def test_worker_handles_fetcher_errors_gracefully(self):
        """Test that worker continues when fetcher raises exception."""
        def failing_fetcher(channel_id):
            raise ValueError("Network error")

        add_channel_info = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=failing_fetcher, suppress_verbose=True)

        with patch.object(queue, "_init_db_functions"):
            queue._add_channel_info = add_channel_info
            # Mock DB query to return no existing names
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute().fetchall.return_value = []
            queue._get_db_connection = Mock(return_value=mock_conn)

            # Should not raise exception
            queue._prefetch_worker()

        # Channel should still be marked as completed (with failed marker)
        assert "UC123" in queue._completed
        # Should have saved failed marker
        add_channel_info.assert_called_once()
        call_args = add_channel_info.call_args[0]
        assert "[Fetch Error]" in call_args[1]  # name contains marker

    def test_worker_respects_stop_signal(self):
        """Test that worker stops when stop() is called."""
        import threading

        def slow_fetcher(channel_id):
            time.sleep(10)  # Long operation
            return ("Name", "https://url")

        queue = ChannelPrefetchQueue(
            ["UC123", "UC456", "UC789"],
            fetcher=slow_fetcher,
            max_workers=1,  # Single worker for predictable stopping
            suppress_verbose=True,
        )

        with patch.object(queue, "_init_db_functions"):
            queue._add_channel_info = Mock()
            # Mock DB query to return no existing names
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute().fetchall.return_value = []
            queue._get_db_connection = Mock(return_value=mock_conn)

            # Start worker in background thread
            worker_thread = threading.Thread(target=queue._prefetch_worker)
            worker_thread.start()

            # Stop after short delay
            time.sleep(0.1)
            queue.stop()
            worker_thread.join(timeout=1.0)

        # Should have stopped (not all channels processed)
        assert len(queue._completed) < 3


class TestChannelPrefetchQueueThreadSafety:
    """Tests for thread-safe behavior."""

    def test_concurrent_is_ready_calls(self):
        """Test that multiple threads can safely call is_ready()."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            results = []
            threads = []

            def check_ready():
                for _ in range(100):
                    results.append(queue.is_ready("UC123"))

            # Spawn 10 threads checking concurrently
            for _ in range(10):
                t = threading.Thread(target=check_ready)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

        # All calls should complete without error
        assert len(results) == 1000

    def test_concurrent_get_progress_calls(self):
        """Test that multiple threads can safely call get_progress()."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        with patch.object(queue, "_init_db_functions"):
            results = []
            threads = []

            def check_progress():
                for _ in range(100):
                    results.append(queue.get_progress())

            # Spawn 10 threads checking concurrently
            for _ in range(10):
                t = threading.Thread(target=check_progress)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

        # All calls should complete without error
        assert len(results) == 1000


class TestChannelPrefetchQueueRawChannelDetection:
    """Tests for raw channel ID detection."""

    def test_is_raw_channel_id_detects_valid_ids(self):
        """Test that _is_raw_channel_id() correctly identifies raw IDs."""
        fetcher = Mock()
        queue = ChannelPrefetchQueue(["UC123"], fetcher=fetcher)

        # Valid raw channel IDs
        assert queue._is_raw_channel_id("UCabcdefghijklmnopqrstuv") is True
        assert queue._is_raw_channel_id("UCabcdefghijklmnopqrstuv") is True

        # Invalid (wrong format)
        assert queue._is_raw_channel_id("UC123") is False  # Too short
        assert queue._is_raw_channel_id("@channel") is False  # Handle format
        assert queue._is_raw_channel_id("Channel Name") is False  # Name
        assert queue._is_raw_channel_id("") is False  # Empty
        assert queue._is_raw_channel_id("UC1234567890ABCDEFGHIJKLMNO") is False  # Wrong char
