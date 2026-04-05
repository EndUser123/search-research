"""
Test that WorkerProgressTracker is enabled in Rich mode.

This test verifies the fix for duplicate progress bars when running in Rich TUI mode.
The issue: WorkerProgressTracker was disabled when rich_mode=True, causing
multiple aggregate progress bars instead of per-worker progress bars.
"""

from unittest.mock import MagicMock, patch

from yt_fts.download.download_handler import DownloadHandler


class TestWorkerProgressInRichMode:
    """Test WorkerProgressTracker initialization in Rich mode."""

    def test_worker_progress_tracker_enabled_when_rich_mode_true(self):
        """
        GIVEN: DownloadHandler with rich_mode=True (TUI mode)
        WHEN: _submit_download_tasks is called
        THEN: WorkerProgressTracker should be initialized (not skipped)
        """
        console = MagicMock()
        handler = DownloadHandler(
            number_of_jobs=2,
            console=console,
            rich_mode=True,  # TUI mode
            suppress_status_messages=False,
        )
        handler.video_ids = ["abc123", "def456"]
        handler.channel_id = "UC123"
        handler.channel_name = "Test Channel"

        with patch('yt_fts.download.worker_progress_tracker.Progress') as mock_progress:
            mock_progress.return_value.add_task = MagicMock(return_value=0)
            mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress.return_value)
            mock_progress.return_value.__exit__ = MagicMock()

            # Submit download tasks
            executor, futures = handler._submit_download_tasks()

            # Verify WorkerProgressTracker was initialized
            mock_progress.assert_called_once()
            assert handler._worker_progress is not None

            # Cleanup
            handler._worker_progress = None
            handler._worker_assignments.clear()

    def test_worker_progress_tracker_skipped_when_suppress_status_true(self):
        """
        GIVEN: DownloadHandler with suppress_status_messages=True
        WHEN: _submit_download_tasks is called
        THEN: WorkerProgressTracker should NOT be initialized (batch mode)
        """
        console = MagicMock()
        handler = DownloadHandler(
            number_of_jobs=2,
            console=console,
            rich_mode=False,
            suppress_status_messages=True,  # Batch mode
        )
        handler.video_ids = ["abc123", "def456"]
        handler.channel_id = "UC123"
        handler.channel_name = "Test Channel"

        executor, futures = handler._submit_download_tasks()

        # Verify WorkerProgressTracker was NOT initialized
        assert handler._worker_progress is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
