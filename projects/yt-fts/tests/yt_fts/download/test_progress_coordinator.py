"""
Integration tests for ThreadSafeProgressCoordinator.

Tests the thread-safe progress bar coordinator that eliminates race conditions
when multiple worker threads update Rich progress concurrently.
"""

import queue
import threading
import time
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from rich.progress import Progress, TaskID


@pytest.fixture
def mock_progress() -> MagicMock:
    """Create a mock Rich Progress object."""
    mock = MagicMock(spec=Progress)
    mock.add_task = MagicMock(return_value=TaskID(1))
    mock.update = MagicMock()
    return mock


@pytest.fixture
def coordinator(mock_progress: MagicMock) -> Any:
    """Import and create a ThreadSafeProgressCoordinator instance."""
    from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator

    coord = ThreadSafeProgressCoordinator(mock_progress, daemon=True)
    yield coord
    # Cleanup
    if coord.running:
        coord.stop(wait=False)


class TestThreadSafeProgressCoordinator:
    """Test suite for ThreadSafeProgressCoordinator."""

    def test_new_task_with_fields(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test adding a new task with fields dict (fixes recent KeyError issue)."""
        coordinator.start()

        # Add task with fields dict - this was causing KeyError before fix
        coordinator.add_task(
            description="Test Channel",
            channel_name="test_channel",
            total=100,
            visible=True,
            fields={"stats": ""},  # This should not raise KeyError
        )

        # Wait for queue to process
        time.sleep(0.2)
        coordinator.stop(wait=True)

        # Verify add_task was called with fields unpacked as kwargs
        mock_progress.add_task.assert_called_once()
        call_args = mock_progress.add_task.call_args
        assert call_args[1]["total"] == 100
        assert call_args[1]["visible"] is True
        # Fields dict should be unpacked: fields={"stats": ""} becomes stats=""
        assert "stats" in call_args[1] or call_args.kwargs.get("stats") == ""

    def test_existing_task_update_with_fields(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test updating an existing task with new fields."""
        coordinator.start()

        channel_name = "existing_channel"

        # First, create the task
        mock_progress.add_task.return_value = TaskID(42)
        coordinator.add_task(
            description="Existing Channel",
            channel_name=channel_name,
            total=100,
            fields={"stats": ""},
        )
        time.sleep(0.2)

        # Reset mock to track update calls
        mock_progress.reset_mock()

        # Update the existing task with new fields
        coordinator.update_by_channel(
            channel_name=channel_name,
            completed=50,
            fields={"stats": "50/100 (50%)"},
        )
        time.sleep(0.2)

        coordinator.stop(wait=True)

        # Verify update was called with unpacked fields
        mock_progress.update.assert_called_once_with(
            TaskID(42),
            completed=50,
            stats="50/100 (50%)",
        )

    def test_rapid_concurrent_updates(self, mock_progress: MagicMock) -> None:
        """Test that rapid concurrent updates don't cause race conditions."""
        from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator

        coordinator = ThreadSafeProgressCoordinator(mock_progress, daemon=True)
        coordinator.start()

        # Create a task
        mock_progress.add_task.return_value = TaskID(1)
        coordinator.add_task(
            description="Concurrent Test",
            channel_name="concurrent_channel",
            total=100,
            fields={"stats": ""},
        )
        time.sleep(0.1)

        # Track successful updates
        update_count = {"success": 0}
        update_lock = threading.Lock()

        def update_task(iteration: int) -> None:
            """Update the task from a worker thread."""
            try:
                for i in range(10):
                    coordinator.update_by_channel(
                        channel_name="concurrent_channel",
                        completed=iteration * 10 + i,
                        fields={"stats": f"{iteration * 10 + i}/100"},
                    )
                    time.sleep(0.001)  # Small delay to interleave updates
                with update_lock:
                    update_count["success"] += 1
            except Exception as e:
                # This should not happen with thread-safe coordinator
                pytest.fail(f"Concurrent update failed: {e}")

        # Launch multiple threads updating the same task
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_task, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)

        coordinator.stop(wait=True)

        # All threads should complete successfully
        assert update_count["success"] == 5

        # Verify updates were called (exact count may vary due to queue processing)
        assert mock_progress.update.call_count > 0

    def test_add_task_with_missing_fields_initialization(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test that tasks without fields param still work correctly."""
        coordinator.start()

        # Add task without fields dict (backward compatibility)
        coordinator.add_task(
            description="No Fields Task",
            channel_name="no_fields_channel",
            total=50,
            visible=True,
            # No fields param - should not cause error
        )
        time.sleep(0.2)
        coordinator.stop(wait=True)

        # Should still work correctly
        mock_progress.add_task.assert_called_once()

    def test_update_by_nonexistent_channel(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test updating a task by channel name that doesn't exist."""
        coordinator.start()

        # Try to update a non-existent channel - should not crash
        coordinator.update_by_channel(
            channel_name="nonexistent_channel",
            completed=25,
            fields={"stats": "25/100"},
        )
        time.sleep(0.2)
        coordinator.stop(wait=True)

        # Update should not be called (task doesn't exist)
        mock_progress.update.assert_not_called()

    def test_remove_task(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test removing a task from tracking."""
        coordinator.start()

        # Create a task
        mock_progress.add_task.return_value = TaskID(99)
        coordinator.add_task(
            description="To Remove",
            channel_name="remove_channel",
            total=100,
        )
        time.sleep(0.1)

        # Remove the task
        coordinator.remove_task(channel_name="remove_channel")
        time.sleep(0.2)

        # Verify task was marked complete (remove_task always keeps visible)
        # Note: Use remove_task_sync(keep_visible=False) to hide the task
        mock_progress.update.assert_called_once_with(
            TaskID(99),
            completed=100,
        )

        coordinator.stop(wait=True)

    def test_context_manager(self, mock_progress: MagicMock) -> None:
        """Test that coordinator works as context manager."""
        from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator

        with ThreadSafeProgressCoordinator(mock_progress) as coord:
            assert coord.running is True

            # Add a task
            coord.add_task(
                description="Context Manager Test",
                channel_name="ctx_channel",
                total=100,
                fields={"stats": ""},
            )
            time.sleep(0.1)

        # After exiting context, coordinator should be stopped
        assert coord.running is False

    def test_fields_dict_unpacking(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test that fields dict is properly unpacked as kwargs."""
        coordinator.start()

        # Add task with multiple fields
        coordinator.add_task(
            description="Multi Fields",
            channel_name="multi_field_channel",
            total=100,
            fields={"stats": "0/100", "extra": "value"},
        )
        time.sleep(0.2)
        coordinator.stop(wait=True)

        # Verify fields were unpacked as kwargs
        call_args = mock_progress.add_task.call_args
        # The fields dict values should be in the kwargs
        assert call_args.kwargs.get("stats") == "0/100"
        assert call_args.kwargs.get("extra") == "value"

    def test_concurrent_task_creation_and_updates(self, mock_progress: MagicMock) -> None:
        """Test creating multiple tasks and updating them concurrently."""
        from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator

        coordinator = ThreadSafeProgressCoordinator(mock_progress, daemon=True)
        coordinator.start()

        def create_and_update(channel_num: int) -> None:
            """Create and update a task from a thread."""
            channel_name = f"channel_{channel_num}"
            task_id = TaskID(channel_num)
            mock_progress.add_task.return_value = task_id

            # Create task
            coordinator.add_task(
                description=f"Channel {channel_num}",
                channel_name=channel_name,
                total=100,
                fields={"stats": ""},
            )
            time.sleep(0.01)

            # Update task multiple times
            for i in range(5):
                coordinator.update_by_channel(
                    channel_name=channel_name,
                    completed=i * 20,
                    fields={"stats": f"{i * 20}/100"},
                )
                time.sleep(0.005)

        # Launch multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_and_update, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=5)

        coordinator.stop(wait=True)

        # Verify all tasks were created
        assert mock_progress.add_task.call_count == 3

        # Verify updates were processed
        assert mock_progress.update.call_count >= 10  # 3 tasks * 3+ updates each


class TestProgressCoordinatorErrorHandling:
    """Test error handling in ThreadSafeProgressCoordinator."""

    def test_update_with_invalid_task_id(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test that updating with invalid task ID doesn't crash coordinator."""
        coordinator.start()

        # This should not crash even if task_id doesn't exist
        coordinator.update(TaskID(999), completed=50, fields={"stats": "50%"})
        time.sleep(0.2)
        coordinator.stop(wait=True)

        # The mock may raise, but coordinator should queue the request
        mock_progress.update.assert_called_once()

    def test_queue_processing_continues_after_error(self, mock_progress: MagicMock) -> None:
        """Test that queue processing continues even after an update error."""
        from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator

        # Make update raise an exception
        mock_progress.update.side_effect = RuntimeError("Test error")

        coordinator = ThreadSafeProgressCoordinator(mock_progress, daemon=True)
        coordinator.start()

        # Add a valid task
        mock_progress.add_task.return_value = TaskID(1)
        coordinator.add_task(
            description="Error Test",
            channel_name="error_channel",
            total=100,
        )
        time.sleep(0.1)

        # Try to update (will fail, but shouldn't crash coordinator)
        coordinator.update_by_channel(
            channel_name="error_channel",
            completed=50,
        )
        time.sleep(0.2)

        # Coordinator should still be running
        assert coordinator.running is True

        coordinator.stop(wait=True)

    def test_stop_with_wait_false(self, mock_progress: MagicMock) -> None:
        """Test immediate shutdown without waiting for queue to drain."""
        from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator

        coordinator = ThreadSafeProgressCoordinator(mock_progress, daemon=True)
        coordinator.start()

        # Add many updates to queue
        for i in range(100):
            coordinator.add_task(
                description=f"Task {i}",
                channel_name=f"channel_{i}",
                total=100,
            )

        # Stop immediately without waiting
        coordinator.stop(wait=False)

        # Coordinator should be stopped
        assert coordinator.running is False

    def test_update_with_none_kwargs_does_not_crash(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test that update with kwargs=None doesn't cause 'pop from empty list' error.

        Regression test for bug where update.get('kwargs', {}) returns None when
        kwargs is explicitly set to None (not absent), causing .pop() to fail.
        """
        coordinator.start()

        # Create a task first
        mock_progress.add_task.return_value = TaskID(1)
        coordinator.add_task(
            description="Test Channel",
            channel_name="test_channel",
            total=100,
        )
        time.sleep(0.1)

        # Reset mock to track the update call
        mock_progress.reset_mock()

        # Directly queue an update with kwargs=None (simulating the bug condition)
        # This is what happens when code passes None as kwargs
        coordinator.update_queue.put({
            "action": "update",
            "task_id": TaskID(1),
            "kwargs": None  # Explicitly None, not absent
        })
        time.sleep(0.2)

        # The update should have been processed successfully
        # If the bug exists, progress.update won't be called due to the exception
        mock_progress.update.assert_called_once_with(TaskID(1))

        coordinator.stop(wait=True)

    def test_update_by_channel_with_none_kwargs_does_not_crash(self, coordinator: Any, mock_progress: MagicMock) -> None:
        """Test that update_by_channel with kwargs=None doesn't cause crash.

        Regression test for the update_by_channel path with None kwargs.
        """
        coordinator.start()

        # Create a task first
        mock_progress.add_task.return_value = TaskID(42)
        coordinator.add_task(
            description="Test Channel",
            channel_name="test_channel",
            total=100,
        )
        time.sleep(0.1)

        # Reset mock to track the update call
        mock_progress.reset_mock()

        # Directly queue an update_by_channel with kwargs=None
        coordinator.update_queue.put({
            "action": "update_by_channel",
            "channel_name": "test_channel",
            "kwargs": None  # Explicitly None
        })
        time.sleep(0.2)

        # The update should have been processed successfully
        mock_progress.update.assert_called_once_with(TaskID(42))

        coordinator.stop(wait=True)
