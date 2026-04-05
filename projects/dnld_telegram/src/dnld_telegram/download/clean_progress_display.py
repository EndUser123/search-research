from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    FileSizeColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TotalFileSizeColumn,
    TransferSpeedColumn,
)

from ...ui.base import BaseUIDisplay


class CleanProgressDisplay(BaseUIDisplay):
    """Clean progress display with minimal visual clutter."""

    def __init__(
        self, console: Console | None = None, show_file_progress: bool = True
    ):
        super().__init__(console)
        self.show_file_progress = show_file_progress

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            FileSizeColumn(),
            "/",
            TotalFileSizeColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=False,
            transient=False,
        )

        self.download_tasks: dict[str, Any] = {}
        self.main_tasks: dict[str, Any] = {}

    def render(self):
        return self.progress

    def add_download_task(self, filename: str, total_bytes: int) -> str | None:
        if not self.show_file_progress:
            return None

        if len(filename) > 50:
            display_name = filename[:47] + "..."
        else:
            display_name = filename

        task_id = self.progress.add_task(f"Download {display_name}", total=total_bytes)
        self.download_tasks[filename] = task_id
        return str(task_id)

    def start_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            self.progress.start_task(self.download_tasks[filename])

    def update_download_task(self, filename: str, advance: int) -> None:
        if filename in self.download_tasks:
            self.progress.update(self.download_tasks[filename], advance=advance)

    def complete_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            self.progress.update(
                task_id, completed=self.progress.tasks[task_id].total or 100
            )
            self.progress.remove_task(task_id)
            del self.download_tasks[filename]

    def error_download_task(self, filename: str, error: str) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            self.progress.update(task_id, description=f"[red]Error: {filename}")
            self.progress.remove_task(task_id)
            del self.download_tasks[filename]

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        prog_task_id = self.progress.add_task(description, total=total)
        self.main_tasks[task_id] = prog_task_id

    def start_main_task(self, task_id: str) -> None:
        if task_id in self.main_tasks:
            self.progress.start_task(self.main_tasks[task_id])

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            kwargs: dict[str, Any] = {}
            if advance > 0:
                kwargs["advance"] = advance
            if status:
                kwargs["description"] = status
            if kwargs:
                self.progress.update(self.main_tasks[task_id], **kwargs)

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            task = self.progress.tasks[self.main_tasks[task_id]]
            if final_status:
                self.progress.update(self.main_tasks[task_id], description=final_status)
            self.progress.update(self.main_tasks[task_id], completed=task.total or 100)
            self.progress.remove_task(self.main_tasks[task_id])
            del self.main_tasks[task_id]
