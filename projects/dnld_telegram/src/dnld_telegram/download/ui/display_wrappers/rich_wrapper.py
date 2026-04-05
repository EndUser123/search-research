from typing import Any

from loguru import logger

from .....ui.base import BaseUIDisplay


class GorgeousProgressWrapper(BaseUIDisplay):
    """Wrapper that makes your existing progress work with gorgeous display"""

    def __init__(self, gorgeous_display: Any):
        self.gorgeous_display = gorgeous_display
        self.console = gorgeous_display.console
        self._download_tasks = {}  # To keep track of individual download tasks

    def add_download_task(self, description: str, total: float | None = None) -> Any:
        task_id = f"download_{description}"
        self._download_tasks[task_id] = {
            "description": description,
            "total": total,
            "completed": 0,
        }
        self.gorgeous_display.update_operation(f"Downloading: {description}")
        return task_id

    def start_download_task(self, task_id: Any) -> None:
        pass

    def update_download_task(
        self, task_id: Any, current: float, total: float | None = None
    ) -> None:
        if task_id in self._download_tasks:
            self._download_tasks[task_id]["completed"] = current
            self._download_tasks[task_id]["total"] = (
                total if total is not None else self._download_tasks[task_id]["total"]
            )

            completed = self._download_tasks[task_id]["completed"]
            total_bytes = self._download_tasks[task_id]["total"]
            description = self._download_tasks[task_id]["description"]

            if total_bytes:
                self.gorgeous_display.update_operation(
                    f"Downloading: {description} ({completed}/{total_bytes} bytes)"
                )
            else:
                self.gorgeous_display.update_operation(
                    f"Downloading: {description} ({completed} bytes)"
                )
        self.gorgeous_display.update_display()

    def complete_download_task(self, task_id: Any, status: str = "Complete") -> None:
        if task_id in self._download_tasks:
            description = self._download_tasks[task_id]["description"]
            self.gorgeous_display.update_operation(
                f"Finished: {description} - {status}"
            )
            del self._download_tasks[task_id]
        self.gorgeous_display.update_display()

    def error_download_task(self, task_id: Any, error_message: str = "Error") -> None:
        if task_id in self._download_tasks:
            description = self._download_tasks[task_id]["description"]
            self.gorgeous_display.update_operation(
                f"Error downloading: {description} - {error_message}"
            )
            del self._download_tasks[task_id]
        self.gorgeous_display.update_display()

    def add_main_task(
        self, task_id: str, description: str, total: float | None = None
    ) -> Any:
        self.gorgeous_display.update_operation(description)
        return task_id

    def start_main_task(self, task_id: Any):
        pass

    def update_main_task(
        self, task_id: Any, advance: float = 1, status: str | None = None
    ):
        if status:
            self.gorgeous_display.update_operation(status)
        self.gorgeous_display.stats["files_processed"] += advance
        self.gorgeous_display.update_display()

    def complete_main_task(self, task_id: Any, status: str):
        self.gorgeous_display.update_operation(status)

    def log(self, message: str, style: str | None = None):
        logger.info(message)

    def is_termination_requested(self) -> bool:
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        pass
