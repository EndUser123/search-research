"""
Thread-safe progress coordinator for Rich progress bars.

Eliminates race conditions when multiple worker threads update progress concurrently.
"""

from __future__ import annotations

import contextlib
import logging
import queue
import threading
from .thread_safe_manager import ThreadSafeManager
from typing import Any, Literal

from rich.progress import Progress, TaskID

logger = logging.getLogger(__name__)

class ThreadSafeProgressCoordinator:
    """
    Coordinate progress updates from multiple worker threads via a queue.

    This eliminates the race condition where multiple threads calling progress.update()
    simultaneously cause visual duplication in Rich's Live display.

    All progress updates are queued and processed serially by a dedicated thread,
    ensuring only one thread ever touches the Progress object at a time.

    Note: Rich's auto-refresh handles all rendering. Explicit refresh calls are
    omitted to prevent rendering artifacts in Windows Terminal.
    """

    def __init__(self, progress: Progress, daemon: bool=True) -> None:
        """
        Initialize the coordinator.

        Args:
            progress: Rich Progress object to coordinate updates for
            daemon: Whether the update thread should be a daemon thread
        """
        self.progress = progress
        self.update_queue: queue.Queue[Any] = queue.Queue()
        self.running = False
        self.update_thread: threading.Thread | None = None
        self.daemon = daemon
        self.task_ids: dict[str, TaskID] = {}
        self._tsm = ThreadSafeManager()

    def _update_loop(self) -> None:
        """
        Background thread that processes update queue serially.

        This is the only thread that calls progress.update(), eliminating race conditions.

        Uses sentinel value (None) for clean shutdown, avoiding unreliable queue.empty() checks.
        """
        while self.running:
            try:
                update = self.update_queue.get(timeout=0.1)
                # Sentinel value signals shutdown
                if update is None:
                    break
                self._process_update(update)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Progress update error: %s", e, exc_info=True)

    def _process_update(self, update: dict[str, Any]) -> None:
        """
        Process a single update from the queue.

        Args:
            update: Dict with 'action' key and associated data
        """
        if update is None:
            return
        if self.progress is None:
            return
        action = update.get("action")
        if action == "add_task":
            channel_name = update.get("channel_name")

            # CRITICAL: Check for existing task BEFORE creating new Rich progress bar
            # This prevents duplicate progress bars for the same channel
            task_id = None
            if channel_name:
                with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                    existing_task_id: TaskID | None = self.task_ids.get(channel_name)
                    if existing_task_id is not None:
                        task_id = existing_task_id
                        fields = update.get("fields", {})
                        if fields:
                            with contextlib.suppress(Exception):
                                self.progress.update(task_id, **fields)
                        return  # Task exists, updated fields, no need to create new one

            # Only create new task if channel_name not found
            if task_id is None:
                fields = update.get("fields", {})
                task_id = self.progress.add_task(update["description"], total=update.get("total", 100), visible=update.get("visible", True), **fields)
                if channel_name:
                    with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                        self.task_ids[channel_name] = task_id
        elif action == "add_task_sync":
            channel_name = update.get("channel_name")
            event = update.get("event")
            callback = update.get("callback")

            # CRITICAL: Check for existing task BEFORE creating new Rich progress bar
            # This prevents duplicate progress bars for the same channel
            task_id = None
            existing_task_found = False

            if channel_name:
                with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                    existing_task_id: TaskID | None = self.task_ids.get(channel_name)
                    if existing_task_id is not None:
                        task_id = existing_task_id
                        fields = update.get("fields", {})
                        if fields:
                            with contextlib.suppress(Exception):
                                self.progress.update(task_id, **fields)
                        existing_task_found = True
                # Lock released here

            if existing_task_found:
                # Call callback/set event AFTER releasing lock (reduces lock hold time)
                if callback:
                    callback(task_id)
                if event:
                    event.set()
                return  # Early return - task exists, notified caller

            # Only create new task if channel_name not found
            fields = update.get("fields", {})
            task_id = self.progress.add_task(update["description"], total=update.get("total", 100), visible=update.get("visible", True), **fields)
            if channel_name:
                with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                        self.task_ids[channel_name] = task_id

            # Call callback/set event for new task (already outside lock)
            if callback:
                callback(task_id)
            if event:
                event.set()
        elif action == "update":
            task_id = update["task_id"]
            update_kwargs = update.get("kwargs", {}) or {}
            if not isinstance(update_kwargs, dict):
                logger.error("kwargs is not a dict: %s type=%s", update_kwargs, type(update_kwargs))
                update_kwargs = {}
            fields = update_kwargs.pop("fields", {})
            self.progress.update(task_id, **fields, **update_kwargs)
        elif action == "update_by_channel":
            channel_name = update.get("channel_name")
            if not channel_name:
                return

            # Extract and validate kwargs BEFORE lock (minimal work under lock)
            update_kwargs = update.get("kwargs", {}) or {}
            if not isinstance(update_kwargs, dict):
                logger.error("Invalid kwargs type: %s", type(update_kwargs))
                update_kwargs = {}

            fields = update_kwargs.pop("fields", {})

            # CRITICAL FIX: Hold lock during entire lookup + update to prevent TOCTOU
            # Previous code had lock released between lookup and update, allowing
            # task to be removed in between (TOCTOU vulnerability)
            with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                channel_task_id = self.task_ids.get(channel_name)

                if channel_task_id is None:
                    return

                # Update happens while holding lock - prevents race condition
                try:
                    self.progress.update(channel_task_id, **fields, **update_kwargs)
                except (OSError, TimeoutError, ValueError, RuntimeError):
                    # Log error but don't crash - progress updates are non-critical
                    logger.debug("Progress update failed for channel %s", channel_name)
        elif action == "remove_task":
            channel_name = update.get("channel_name")
            with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                task_id = self.task_ids.get(channel_name)
                if task_id is not None:
                    try:
                        self.progress.update(task_id, completed=100)
                    except (OSError, TimeoutError, ValueError, RuntimeError):
                        self.progress.update(task_id, completed=100)
                    del self.task_ids[channel_name]
        elif action == "remove_task_sync":
            channel_name = update.get("channel_name")
            event = update.get("event")
            keep_visible = update.get("keep_visible", True)
            with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                task_id = self.task_ids.get(channel_name)
                if task_id is not None:
                    try:
                        if keep_visible:
                            self.progress.update(task_id, completed=100)
                        else:
                            self.progress.update(task_id, completed=100, visible=False)
                    except (OSError, TimeoutError, ValueError, RuntimeError):
                        if keep_visible:
                            self.progress.update(task_id, completed=100)
                        else:
                            self.progress.update(task_id, visible=False)
                    del self.task_ids[channel_name]
            # Force Rich to refresh immediately so the progress bar updates
            try:
                self.progress.refresh()
            except (OSError, TimeoutError, ValueError, RuntimeError):
                pass
            if event:
                event.set()
            # Clear residual progress bar output (Windows Terminal ghosting workaround)
            # Completed tasks can leave visual artifacts in terminal output
            # Force a newline to move past the completed progress bar display
            self.progress.console.print("")

    def start(self) -> None:
        """Start the background update thread."""
        if self.running:
            return
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=self.daemon, name="ProgressUpdateThread")
        self.update_thread.start()

    def stop(self, wait: bool=True) -> None:
        """
        Stop the background update thread.

        Args:
            wait: Whether to wait for thread to finish (default: True).
                  Set to False for immediate shutdown (e.g., on KeyboardInterrupt).
        """
        if not self.running:
            return
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            with contextlib.suppress(queue.Full):
                self.update_queue.put(None, timeout=0.1)
            import sys
            in_exception_context = sys.exc_info()[0] is not None
            if wait and (not in_exception_context):
                self.update_thread.join(timeout=0.5)

    def add_task(self, description: str, channel_name: str | None=None, total: int=100, visible: bool=True, fields: dict[str, Any] | None=None) -> None:
        """
        Add a new progress task.

        This method is thread-safe and can be called from any thread.

        Args:
            description: Task description
            channel_name: Optional channel name to identify the task
            total: Total units for the task
            visible: Whether the task is visible
            fields: Optional dict of task fields for Rich display
        """
        self.update_queue.put({"action": "add_task", "description": description, "channel_name": channel_name, "total": total, "visible": visible, "fields": fields or {}})

    def add_task_sync(self, description: str, channel_name: str | None=None, total: int=100, visible: bool=True, fields: dict[str, Any] | None=None, timeout: float = 1.0) -> TaskID | None:
        """
        Add a new progress task and wait for it to be created.

        This is a synchronous version of add_task() that waits for the background
        thread to process the action and create the task before returning.

        This is necessary when you need to use the task immediately after creation,
        such as when passing it to a worker that will call update_by_channel().

        Args:
            description: Task description
            channel_name: Optional channel name to identify the task
            total: Total units for the task
            visible: Whether the task is visible
            fields: Optional dict of task fields for Rich display
            timeout: Maximum time to wait for task creation (default 1.0s)

        Returns:
            TaskID if created successfully, None if timeout or error
        """
        import threading
        event = threading.Event()
        result_container = {"task_id": None}

        def on_created(task_id: TaskID) -> None:
            result_container["task_id"] = task_id
            event.set()

        self.update_queue.put({
            "action": "add_task_sync",
            "description": description,
            "channel_name": channel_name,
            "total": total,
            "visible": visible,
            "fields": fields or {},
            "event": event,
            "callback": on_created
        })

        if not event.wait(timeout=timeout):
            logger.warning("add_task_sync timeout for '%s'", description)
            return None

        return result_container["task_id"]

    def update(self, task_id: TaskID, **kwargs: Any) -> None:
        """
        Update a progress task by task ID.

        This method is thread-safe and can be called from any thread.

        Args:
            task_id: Rich TaskID to update
            **kwargs: Arguments to pass to progress.update()
        """
        self.update_queue.put({"action": "update", "task_id": task_id, "kwargs": kwargs})

    def update_by_channel(self, channel_name: str, **kwargs: Any) -> None:
        """
        Update a progress task by channel name.

        This is the preferred method for download handlers as they
        know their channel name but not the task ID.

        This method is thread-safe and can be called from any thread.

        Args:
            channel_name: Channel name identifying the task
            **kwargs: Arguments to pass to progress.update()
        """
        self.update_queue.put({"action": "update_by_channel", "channel_name": channel_name, "kwargs": kwargs})


    def remove_task(self, channel_name: str) -> None:
        """
        Remove a task from tracking (asynchronous).

        This method is thread-safe and can be called from any thread.
        The removal happens in the background thread.

        Args:
            channel_name: Channel name of the task to remove
        """
        self.update_queue.put({"action": "remove_task", "channel_name": channel_name})

    def remove_task_sync(self, channel_name: str, timeout: float = 0.5, keep_visible: bool = True) -> None:
        """
        Remove a task from tracking and wait for completion.

        This method queues the removal and waits for the background thread
        to process it before returning. Use this when you need to ensure
        the task is removed before printing output (prevents line wrapping).

        Args:
            channel_name: Channel name of the task to remove
            timeout: Maximum time to wait for removal (default 0.5s)
            keep_visible: If False, hide the completed progress bar (default: True, keeps bar visible)
        """
        # If background thread is not running, remove directly to avoid race condition
        if not self.running:
            with self._tsm.get_lock("ThreadSafeProgressCoordinator"):
                if channel_name in self.task_ids:
                    task_id = self.task_ids[channel_name]
                    try:
                        self.progress.update(task_id, completed=100)
                    except (OSError, TimeoutError, ValueError, RuntimeError):
                        self.progress.update(task_id, completed=100)
                    del self.task_ids[channel_name]
            return
        # Create a unique event for this removal
        event = threading.Event()
        self.update_queue.put({
            "action": "remove_task_sync",
            "channel_name": channel_name,
            "event": event,
            "keep_visible": keep_visible
        })
        # Wait for the background thread to process it
        if not event.wait(timeout=timeout):
            logger.warning("remove_task_sync timeout for %s", channel_name)

    def __enter__(self) -> ThreadSafeProgressCoordinator:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        """Context manager exit."""
        self.stop()
        return False
ProgressCoordinator = ThreadSafeProgressCoordinator
