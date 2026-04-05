import time
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from ...ui.base import BaseUIDisplay


class ProductionProgressDisplay(BaseUIDisplay):
    """
    A production-quality, multi-panel progress display that inherits from the non-blocking base class.
    """

    def __init__(
        self, console: Console | None = None, show_file_progress: bool = True
    ):
        super().__init__()
        self.console = console or Console()
        self.show_file_progress = show_file_progress

        self.main_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TextColumn("[green]{task.fields[status]!s}"),
            console=console,
            expand=False,
        )

        self.download_progress = Progress(
            TextColumn("[bold green]{task.description}", justify="left"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=False,
        )

        self.main_tasks: dict[str, TaskID] = {}
        self.download_tasks: dict[str, TaskID] = {}

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
        """Creates the three-panel Rich Layout."""
        layout = Layout()
        layout.split_column(
            Layout(
                Panel(
                    self.main_progress,
                    title="[bold]Operations[/bold]",
                    border_style="blue",
                ),
                name="main",
                size=5,
            ),
            Layout(
                Panel(
                    self.download_progress,
                    title="[bold]Active Downloads[/bold]",
                    border_style="green",
                ),
                name="downloads",
            ),
            Layout(
                Panel(
                    self._render_stats_table(),
                    title="[bold]Statistics[/bold]",
                    border_style="yellow",
                ),
                name="stats",
                size=4,
            ),
        )
        return Panel(layout)

    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        self.main_tasks[task_id] = self.main_progress.add_task(
            description, total=total, status=""
        )

    def start_main_task(self, task_id: str) -> None:
        if task_id in self.main_tasks:
            self.main_progress.start_task(self.main_tasks[task_id])

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            update_kwargs: dict[str, Any] = {"advance": advance} if advance > 0 else {}
            if status is not None:
                update_kwargs["status"] = status
            self.main_progress.update(self.main_tasks[task_id], **update_kwargs)

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        if task_id in self.main_tasks:
            task = self.main_progress.tasks[self.main_tasks[task_id]]
            self.main_progress.update(
                self.main_tasks[task_id],
                completed=task.total or 100,
                status=f"[bold green]Done: {final_status or ''}[/]",
            )

    def add_download_task(self, filename: str, total_bytes: int) -> int | None:
        if not self.show_file_progress:
            return None
        max_width = 25
        display_filename = filename
        if len(display_filename) > max_width:
            display_filename = display_filename[: max_width - 3] + "..."
        task_id = self.download_progress.add_task(display_filename, total=total_bytes)
        self.download_tasks[filename] = task_id
        return task_id

    def start_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            self.download_progress.start_task(self.download_tasks[filename])

    def update_download_task(self, filename: str, advance: int) -> None:
        if filename in self.download_tasks:
            self.download_progress.update(
                self.download_tasks[filename], advance=advance
            )
            total_data = float(self.stats.get("total_data", 0.0)) + advance
            self.update_main_task("Downloading...", status=f"Total data: {total_data}")

    def complete_download_task(self, filename: str) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            task = self.download_progress.tasks[task_id]
            self.download_progress.update(task_id, completed=task.total or 100)
            time.sleep(0.1)
            self.download_progress.remove_task(task_id)
            del self.download_tasks[filename]
            files_downloaded = float(self.stats.get("files_processed", 0.0)) + 1
            self.update_main_task(
                "Downloading...", status=f"Files downloaded: {files_downloaded}"
            )

    def error_download_task(self, filename: str, error: str) -> None:
        if filename in self.download_tasks:
            task_id = self.download_tasks[filename]
            self.download_progress.update(
                task_id, description=f"[bold red]Error: {filename} ({error})[/]"
            )
            time.sleep(2)
            self.download_progress.remove_task(task_id)
            del self.download_tasks[filename]
            errors = float(self.stats.get("errors", 0.0)) + 1
            self.update_main_task("Error", status=f"Errors: {errors}")
