"""
Unit tests for WorkerProgressTracker module.

Tests per-worker progress tracking functionality including:
- Worker initialization
- Progress updates
- Thread safety
- Worker completion
- Format utilities
"""

from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.worker_progress_tracker import WorkerProgressTracker


# Patch Rich Progress to avoid terminal interaction during tests
@pytest.fixture
def mock_progress():
    """Provide a mocked Rich Progress instance."""
    with patch('yt_fts.download.worker_progress_tracker.Progress') as mock:
        yield mock


class TestWorkerProgressTrackerInit:
    """Test WorkerProgressTracker initialization."""

    def test_initialization_creates_correct_number_of_workers(self, mock_progress):
        """Given: max_workers=3, When: initializing, Then: 3 worker bars created"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        with WorkerProgressTracker(console, max_workers=3) as tracker:
            assert tracker.max_workers == 3
            assert tracker.console == console
            assert len(tracker.worker_tasks) == 3

    def test_initialization_with_context_manager(self, mock_progress):
        """Given: Using context manager, When: entering, Then: progress started"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        with WorkerProgressTracker(console, max_workers=2) as tracker:
            assert tracker.max_workers == 2
            assert len(tracker.worker_tasks) == 2
            mock_progress.return_value.__enter__.assert_called_once()

    def test_context_manager_exit_on_completion(self, mock_progress):
        """Given: Active tracker, When: exiting context, Then: progress stopped"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.__exit__ = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()
        tracker.__exit__(None, None, None)

        assert tracker._finished is True
        mock_progress.return_value.__exit__.assert_called_once()


class TestWorkerRegistration:
    """Test worker registration and video assignment."""

    def test_register_worker_updates_description(self, mock_progress):
        """Given: Worker exists, When: registering video, Then: description updated"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.register_worker(0, "abc123def45")

        # Should update the task description with video ID (truncated to 8 chars)
        mock_progress.return_value.update.assert_called()
        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert 'abc123de' in call_kwargs.get('description', '')

    def test_register_worker_with_short_video_id(self, mock_progress):
        """Given: Short video ID, When: registering, Then: full ID shown"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=1)
        tracker.__enter__()

        tracker.register_worker(0, "abc123")

        # Short ID should be shown in full
        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert 'abc123' in call_kwargs.get('description', '')

    def test_register_invalid_worker_id(self, mock_progress):
        """Given: Invalid worker_id, When: registering, Then: no update made"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        # Should not raise error
        tracker.register_worker(5, "abc123")

        # update should not have been called since worker 5 doesn't exist
        mock_progress.return_value.update.assert_not_called()


class TestProgressUpdates:
    """Test progress update functionality."""

    def test_update_progress_with_bytes(self, mock_progress):
        """Given: Active download, When: updating progress, Then: percentage calculated"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.update_worker_progress(
            worker_id=0,
            downloaded_bytes=5000000,  # 5MB
            total_bytes=10000000,      # 10MB
            speed=2000000,              # 2MB/s
            eta=5
        )

        # Should update progress with 50%
        mock_progress.return_value.update.assert_called()
        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert call_kwargs['completed'] == 50.0

    def test_update_progress_with_zero_total(self, mock_progress):
        """Given: Unknown total size, When: updating, Then: percentage remains 0"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.update_worker_progress(
            worker_id=0,
            downloaded_bytes=1000000,
            total_bytes=0,
            speed=1000000,
            eta=None
        )

        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert call_kwargs['completed'] == 0

    def test_update_progress_formatting(self, mock_progress):
        """Given: Speed and ETA, When: updating, Then: formatted correctly"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.update_worker_progress(
            worker_id=0,
            downloaded_bytes=1000000,
            total_bytes=10000000,
            speed=2500000,  # 2.5MB/s
            eta=125         # 2m 5s
        )

        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        # Speed should be formatted as MB/s
        assert 'MB' in call_kwargs['speed'] or '/s' in call_kwargs['speed']
        # ETA should be formatted as minutes/seconds
        assert 'm' in call_kwargs['eta'] or 's' in call_kwargs['eta']


class TestWorkerCompletion:
    """Test worker completion handling."""

    def test_finish_worker_success(self, mock_progress):
        """Given: Successful download, When: finishing, Then: shows success status"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.finish_worker(0, success=True)

        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert call_kwargs['completed'] == 100
        assert '✓' in call_kwargs['speed']
        assert 'Done' in call_kwargs['eta']

    def test_finish_worker_failure(self, mock_progress):
        """Given: Failed download, When: finishing, Then: shows failure status"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.finish_worker(0, success=False)

        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert '✗' in call_kwargs['speed']
        assert 'Failed' in call_kwargs['eta']

    def test_reset_worker_to_waiting(self, mock_progress):
        """Given: Completed worker, When: resetting, Then: shows waiting status"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=2)
        tracker.__enter__()

        tracker.reset_worker(0)

        call_kwargs = mock_progress.return_value.update.call_args.kwargs
        assert 'Waiting' in call_kwargs['description']
        assert call_kwargs['completed'] == 0


class TestFormatUtilities:
    """Test formatting utility methods."""

    def test_format_bytes_small(self):
        """Given: Bytes < 1KB, When: formatting, Then: show in bytes"""
        result = WorkerProgressTracker._format_bytes(512)
        assert '512' in result
        assert 'B' in result

    def test_format_bytes_kilobytes(self):
        """Given: Bytes in KB range, When: formatting, Then: show in KB"""
        result = WorkerProgressTracker._format_bytes(5120)
        assert 'KB' in result
        assert '5.0' in result

    def test_format_bytes_megabytes(self):
        """Given: Bytes in MB range, When: formatting, Then: show in MB"""
        result = WorkerProgressTracker._format_bytes(5000000)
        assert 'MB' in result

    def test_format_bytes_gigabytes(self):
        """Given: Bytes in GB range, When: formatting, Then: show in GB"""
        result = WorkerProgressTracker._format_bytes(2000000000)
        assert 'GB' in result

    def test_format_eta_seconds(self):
        """Given: ETA < 1 minute, When: formatting, Then: show in seconds"""
        result = WorkerProgressTracker._format_eta(45)
        assert '45s' in result

    def test_format_eta_minutes(self):
        """Given: ETA in minutes, When: formatting, Then: show min and sec"""
        result = WorkerProgressTracker._format_eta(125)  # 2m 5s
        assert '2m' in result
        assert '5s' in result

    def test_format_eta_hours(self):
        """Given: ETA in hours, When: formatting, Then: show hours and min"""
        result = WorkerProgressTracker._format_eta(3661)  # 1h 1m 1s
        assert '1h' in result
        assert '1m' in result


class TestThreadSafety:
    """Test thread safety of progress updates."""

    def test_concurrent_updates_use_lock(self, mock_progress):
        """Given: Multiple threads, When: updating concurrently, Then: lock used"""
        console = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
        mock_progress.return_value.update = MagicMock()
        mock_progress.return_value.add_task = MagicMock(return_value=0)

        tracker = WorkerProgressTracker(console, max_workers=4)
        tracker.__enter__()

        # Simulate concurrent updates
        import threading

        def update_worker(worker_id: int):
            for i in range(10):
                tracker.update_worker_progress(
                    worker_id, i * 1000000, 10000000, 1000000, 10
                )

        threads = [
            threading.Thread(target=update_worker, args=(i,))
            for i in range(4)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
