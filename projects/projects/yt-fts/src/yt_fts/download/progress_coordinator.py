"""
Thread-safe progress coordinator for Rich progress bars.

Eliminates race conditions when multiple worker threads update progress concurrently.
"""
import contextlib
import logging
import queue
import threading
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
        self.task_lock = threading.Lock()

    def _update_loop(self) -> None:
        """
        Background thread that processes update queue serially.

        This is the only thread that calls progress.update(), eliminating race conditions.
        """
        while self.running or not self.update_queue.empty():
            try:
                update = self.update_queue.get(timeout=0.1)
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
            if channel_name:
                with self.task_lock:
                    existing_task_id: TaskID | None = self.task_ids.get(channel_name)
                    if existing_task_id is not None:
                        fields = update.get("fields", {})
                        if fields:
                            with contextlib.suppress(Exception):
                                self.progress.update(existing_task_id, **fields)
                        return
            fields = update.get("fields", {})
            task_id = self.progress.add_task(update["description"], total=update.get("total", 100), visible=update.get("visible", True), **fields)
            if channel_name:
                with self.task_lock:
                    self.task_ids[channel_name] = task_id
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
            if channel_name:
                with self.task_lock:
                    channel_task_id: TaskID | None = self.task_ids.get(channel_name)
                if channel_task_id is not None:
                    update_kwargs = update.get("kwargs", {}) or {}
                    if not isinstance(update_kwargs, dict):
                        logger.error("kwargs is not a dict: %s type=%s", update_kwargs, type(update_kwargs))
                        update_kwargs = {}
                    fields = update_kwargs.pop("fields", {})
                    self.progress.update(channel_task_id, **fields, **update_kwargs)
        elif action == "remove_task":
            channel_name = update.get("channel_name")
            with self.task_lock:
                if channel_name in self.task_ids:
                    task_id = self.task_ids[channel_name]
                    try:
                        self.progress.update(task_id, completed=100, visible=False)
                    except Exception:
                        self.progress.update(task_id, visible=False)
                    del self.task_ids[channel_name]

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
        Remove a task from tracking.

        This method is thread-safe and can be called from any thread.

        Args:
            channel_name: Channel name of the task to remove
        """
        self.update_queue.put({"action": "remove_task", "channel_name": channel_name})

    def __enter__(self) -> "ThreadSafeProgressCoordinator":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        """Context manager exit."""
        self.stop()
        return False
ProgressCoordinator = ThreadSafeProgressCoordinator
