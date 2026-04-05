import time
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from ...ui.base import BaseUIDisplay


class PaneledProgressDisplay(BaseUIDisplay):
    """
    A two-panel progress display that inherits from the non-blocking base class.
    """

    def __init__(
        self, console: Console | None = None, show_file_progress: bool = True
    ):
        super().__init__()
        self.console = console or Console()
        self.show_file_progress = show_file_progress
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        self.download_tasks: dict[str, Any] = {}
        self.main_tasks: dict[str, Any] = {}

    def _render_stats_table(self) -> Table:
        """Renders a statistics table."""
        table = Table.grid(padding=1)
        table.add_column(justify="right", style="cyan", no_wrap=True)
        table.add_column()

        for k, v in self.stats.items():
            if k not in ["start_time", "last_update", "update_interval"]:
                table.add_row(str(k), str(v))

        if "start_time" in self.stats and self.stats["start_time"]:
            elapsed = time.time() - float(self.stats["start_time"])
            files_per_sec = (
                float(self.stats.get("files_processed", 0.0)) / elapsed
                if elapsed > 0
                else 0
            )
            table.add_row("Speed", f"{files_per_sec:.1f} files/s")

        return table

    def render(self) -> Panel:
        """Creates the two-panel Rich Layout."""
        layout = Layout()
        layout.split_row(
            Layout(
                Panel(
                    self._render_stats_table(),
                    title="[bold]Info & Stats[/bold]",
                    border_style="green",
                ),
                name="left",
                ratio=1,
                minimum_size=40,
            ),
            Layout(
                Panel(
                    self.progress, title="[bold]Progress[/bold]", border_style="blue"
                ),
                name="right",
                ratio=2,
                minimum_size=60,
            ),
        )
        return Panel(layout)

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        self.main_tasks[task_id] = self.progress.add_task(description, total=total)

    def start_main_task(self, task_id: str) -> None:
        if task_id in self.main_tasks:
            self.progress.start_task(self.main_tasks[task_id])

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            update_kwargs: dict[str, Any] = {"advance": advance} if advance > 0 else {}
            if status is not None:
                update_kwargs["description"] = status
            self.progress.update(self.main_tasks[task_id], **update_kwargs)

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            task = self.progress.tasks[self.main_tasks[task_id]]
            if final_status:
                self.progress.update(self.main_tasks[task_id], description=final_status)
            self.progress.update(self.main_tasks[task_id], completed=task.total or 100)

    def add_download_task(self, filename: str, total_bytes: int) -> int | None:
        if not self.show_file_progress:
            return None
        max_width = 25
        display_filename = filename
        if len(display_filename) > max_width:
            display_filename = display_filename[: max_width - 3] + "..."
        task_id = self.progress.add_task(
            f"Download {display_filename}", total=total_bytes
        )
        self.download_tasks[filename] = task_id
        return task_id

    def start_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            self.progress.start_task(self.download_tasks[filename])

    def update_download_task(self, filename: str, advance: int) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            if task_id in self.progress.tasks:
                self.progress.update(task_id, advance=advance)

    def complete_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            if task_id in self.progress.tasks:
                task = self.progress.tasks[task_id]
                self.progress.update(task_id, completed=task.total or 100)
                self.progress.remove_task(task_id)
            del self.download_tasks[filename]

    def error_download_task(self, filename: str, error: str) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            if task_id in self.progress.tasks:
                self.progress.update(
                    task_id, description=f"[red]Error: {filename} ({error})[/]"
                )
                self.progress.remove_task(task_id)
            del self.download_tasks[filename]
