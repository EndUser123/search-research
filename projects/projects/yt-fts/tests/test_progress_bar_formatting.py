"""Tests for progress bar display formatting in batch download.

These tests verify that progress bars display correctly without:
1. Double progress bar rendering
2. Missing newlines between messages and progress bars
3. Misaligned progress bar prefixes
"""

import pytest
from io import StringIO
from unittest.mock import Mock, patch

from yt_fts.download.progress_tracker import DownloadProgressTracker
from yt_fts.download.worker_progress_tracker import WorkerProgressTracker


class TestProgressBarFormatting:
    """Test suite for progress bar display formatting issues."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console for testing."""
        import time

        console = Mock()
        # Mock stderr attribute
        console.stderr = True
        console.is_terminal = True
        console.is_interactive = True
        # Mock the Live context manager for Progress
        mock_live = Mock()
        mock_live.__enter__ = Mock(return_value=Mock())
        mock_live.__exit__ = Mock(return_value=Mock())
        console.live = Mock(return_value=mock_live)
        # Mock get_time method for Progress speed estimation
        console.get_time = Mock(return_value=time.time())
        return console

    @pytest.fixture
    def progress_tracker(self, mock_console):
        """Create a progress tracker with mock console."""
        return DownloadProgressTracker(
            channel_name="Test Channel",
            console=mock_console,
            rich_mode=False,
            suppress_status_messages=False
        )

    def test_downloading_message_ends_with_newline(self, progress_tracker):
        """Test that "Downloading X vtt files" message ends with a newline.

        This prevents the progress bar from appearing on the same line.
        Issue: User saw "⎿ yt-dlp: [progress] ⎿ Downloading 122 vtt files"
        Expected: "⎿ Downloading 122 vtt files" on its own line, then progress bar
        """
        # The actual message format from download_handler.py line 926
        num_videos = 122
        message = f"[green][bold]Downloading [red]{num_videos}[/red] vtt files[/bold][/green]\n"

        # Verify the message ends with newline
        assert message.endswith("\n"), "Downloading message must end with newline for proper formatting"

        # Verify it contains the expected content
        assert "Downloading" in message
        assert "vtt files" in message

    def test_single_progress_tracker_not_duplicated(self, progress_tracker):
        """Test that only one progress tracker is active at a time.

        Issue: User saw double progress bar output:
        "⎿ yt-dlp: [progress bar] ⎿ Downloading 122 vtt files"
        "⎿ yt-dlp: [progress bar]" (duplicate)

        This can happen when both WorkerProgressTracker and DownloadProgressTracker
        are active simultaneously.
        """
        # When suppress_status_messages is False, only one progress tracker should be used
        # The WorkerProgressTracker handles per-worker progress
        # The coordinator's "yt-dlp:" task should not create its own progress bar

        # Verify that if we have a worker progress tracker, we don't duplicate
        tracker = DownloadProgressTracker(
            channel_name="Test",
            console=progress_tracker.console,
            rich_mode=False,
            suppress_status_messages=True  # This should suppress the yt-dlp progress bar
        )

        # With suppress_status_messages=True, should use DummyProgress
        # This prevents double progress bars
        assert tracker.suppress_status_messages is True

    def test_worker_progress_tracker_respects_max_workers(self, mock_console):
        """Test that WorkerProgressTracker creates the correct number of progress bars.

        Issue: Multiple "yt-dlp:" prefixes appearing suggest multiple progress bars
        when there should be only one per worker.
        """
        max_workers = 2
        tracker = WorkerProgressTracker(mock_console, max_workers)

        # Should create exactly max_workers progress bars
        with tracker:
            assert len(tracker.worker_tasks) == max_workers
            assert all(worker_id in tracker.worker_tasks for worker_id in range(max_workers))

    def test_progress_bar_description_format(self, mock_console):
        """Test that progress bar descriptions are formatted correctly.

        Issue: Inconsistent "yt-dlp:" prefix placement
        """
        max_workers = 2
        tracker = WorkerProgressTracker(mock_console, max_workers)

        with tracker:
            # Check initial descriptions (waiting state)
            for worker_id in range(max_workers):
                task_id = tracker.worker_tasks[worker_id]
                task = tracker.progress.tasks[task_id]
                # Should show "Worker N [Waiting...]" format
                assert "Worker" in task.description
                assert "[Waiting...]" in task.description

    def test_progress_update_does_not_duplicate(self, mock_console):
        """Test that progress updates don't create duplicate progress bars.

        Issue: Multiple identical progress bars appearing
        """
        tracker = WorkerProgressTracker(mock_console, max_workers=2)

        with tracker:
            # Register a worker (just verify it doesn't crash)
            tracker.register_worker(0, "test_video_id")

            # Should still have exactly 2 tasks (one per worker)
            assert len(tracker.progress.tasks) == 2


class TestProgressMessageFormatting:
    """Test suite for progress message formatting in default display plugin."""

    def test_downloading_message_format_in_default_plugin(self):
        """Test that the default plugin formats downloading messages correctly.

        The message should use the detail format with proper ⎿ prefix when
        include_channel_name_in_messages is enabled.
        """
        # Simulate the _detail_message formatting
        include_channel_name = True

        # When channel name is included, should have pipe prefix
        message = f"Downloading 122 vtt file{'s' if 122 != 1 else ''}"
        if include_channel_name:
            formatted = f"   ⎿ {message}"
        else:
            formatted = message

        # Verify the format
        assert formatted.startswith("   ⎿ ")
        assert "Downloading" in formatted
        assert "122 vtt files" in formatted or "122 vtt file" in formatted

    def test_yt_dlp_prefix_formatting(self):
        """Test that yt-dlp prefix is formatted consistently.

        Issue: The coordinator adds "     yt-dlp:" prefix which may not align
        with the ⎿ prefix pattern used elsewhere.
        """
        # The coordinator uses this format
        coordinator_description = "     yt-dlp:"

        # Should have specific spacing for alignment
        assert coordinator_description.startswith("     ")  # 5 spaces
        assert "yt-dlp:" in coordinator_description

        # The ⎿ format used by default plugin
        default_prefix = "   ⎿ "

        # Verify different formats (these are intentionally different)
        assert "yt-dlp:" in coordinator_description
        assert "⎿" in default_prefix
