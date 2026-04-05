# --- INTEGRITY ---
# Previous Character Count: 8974
# Current Character Count: 9115
# Syntax Check: [PASS]
# Logic Validation: [Refactored UI creation to build static elements once, fixing the redraw bug.]
# Reason for Change: [To fix a UI rendering artifact causing repeated header printing.]
# ------------------
# --- METADATA ---
# Filename: src/ui_dashboard.py
# Version: 2.6
#
# --- CHANGELOG ---
# v2.6: BUGFIX: Fixed UI redraw issue by creating static layout elements (header,
#       footer) only once during initialization, instead of in the update loop.
# v2.5: Disabled text wrapping entirely in the log panel by setting no_wrap=True
#       on the consolidated log Text object.
# ------------------

from collections import deque
from typing import Any

import structlog
from rich.box import SIMPLE
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
)
from rich.table import Table
from rich.text import Text


class Dashboard:
    def __init__(self, num_cpu_workers: int):
        self.log_deque: deque[str] = deque(maxlen=20)
        self.summary_data: dict[str, Any] = {
            "status": "Initializing...",
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "failed": 0,
            "queued": 0,
            "failures": [],
        }
        self.num_cpu_workers = num_cpu_workers

        self.overall_progress = Progress(
            TextColumn("[bold]Overall Progress[/]"), BarColumn(), MofNCompleteColumn()
        )
        self.overall_task = self.overall_progress.add_task("Starting...", total=0)

        self.current_task_text = Text("", justify="left")
        self.subtitle_subtask_group = Group()
        self.active_subtask_progress: list[Progress] = []

        self.cpu_progress = Progress(
            TextColumn(
                "    [cyan]Worker {task.fields[worker_id]}[/] - {task.description}"
            ),
            BarColumn(),
            TextColumn("[yellow]{task.percentage:>3.0f}%[/]"),
        )
        self.cpu_worker_tasks = [
            self.cpu_progress.add_task(
                description="Idle",
                worker_id=i + 1,
                total=100,
                completed=0,
                visible=False,
            )
            for i in range(num_cpu_workers)
        ]

        self.layout = self._create_layout()

    def _create_layout(self) -> Layout:
        """Builds the initial layout structure and populates static elements."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=1),
        )
        layout["main"].split_row(
            Layout(name="left", size=50, minimum_size=40),
            Layout(name="right", size=80, minimum_size=60),
        )
        layout["left"].split(Layout(name="settings"), Layout(name="summary"))
        layout["right"].split(
            Layout(name="progress", ratio=1),
            Layout(name="logs", ratio=6),
        )

        # Populate static parts once
        layout["header"].update(self._create_header())
        layout["footer"].update(self._create_footer())

        # Populate dynamic parts with initial state
        layout["summary"].update(self._create_summary_panel())
        layout["progress"].update(self._create_progress_panel())
        layout["logs"].update(self._create_log_panel())

        return layout

    def update(self, settings_panel: Panel) -> None:
        """Updates only the dynamic parts of the layout."""
        # Static elements (header, footer) are no longer updated here.
        self.layout["settings"].update(settings_panel)
        self.layout["summary"].update(self._create_summary_panel())
        self.layout["progress"].update(self._create_progress_panel())
        self.layout["logs"].update(self._create_log_panel())
        log = structlog.get_logger("vidrec.ui")
        log.info("Dashboard updated", category="ui")

    def _create_header(self) -> Panel:
        return Panel(
            Text(
                "Vid_ReC: Video Processing Dashboard",
                justify="center",
                style="bold yellow",
            ),
            border_style="green",
            box=SIMPLE,
        )

    def _create_footer(self) -> Text:
        return Text("Press 'q' to quit", justify="left", style="dim")

    def _create_summary_panel(self) -> Panel:
        data = self.summary_data
        status_style = "yellow"
        if data["status"] == "Complete":
            status_style = "green"
        elif (
            data["status"] == "Failed"
            or data["failed"] > 0
            or "Stopped" in data["status"]
        ):
            status_style = "red"

        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column()
        grid.add_column(style="bold")
        grid.add_row("Status:", f"[{status_style}]{data['status']}[/]")
        grid.add_row()
        grid.add_row("Total Files:", str(data["total"]))
        grid.add_row("[green]✔ Completed:[/]", str(data["completed"]))
        grid.add_row("[yellow]⚠ In Progress:[/]", str(data["in_progress"]))
        grid.add_row("[red]✗ Failed:[/]", str(data["failed"]))
        grid.add_row("[dim]⏳ Queued:[/]", str(data["queued"]))
        if data["failures"]:
            grid.add_row()
            grid.add_row("[bold red]Latest Failure:[/]")
            latest_failure = data["failures"][-1]
            grid.add_row(
                f"  [cyan]{latest_failure['file']}[/]",
                f"[red]{latest_failure['error']}[/]",
            )
        return Panel(
            grid, title="[bold]Run Summary[/]", border_style="green", box=SIMPLE
        )

    def _create_progress_panel(self) -> Panel:
        return Panel(
            Group(
                self.overall_progress,
                self.current_task_text,
                self.subtitle_subtask_group,
                self.cpu_progress,
            ),
            title="[bold]Progress Trackers[/]",
            border_style="green",
            box=SIMPLE,
        )

    def _create_log_panel(self) -> Panel:
        # Log entries are now pre-formatted with Rich markup by RichTextFormatter in logger.py
        log_content = "\n".join(self.log_deque)
        log_text = Text.from_markup(log_content)
        return Panel(
            log_text,
            title="[bold]Live Event Log[/]",
            border_style="green",
            box=SIMPLE,
            subtitle=f"[dim]Showing last {len(self.log_deque)} events[/]",
        )

    def get_final_summary_panel(self) -> Panel:
        data = self.summary_data
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column()
        grid.add_column(style="bold")
        status_text = (
            f"[bold green]✔ {data['status']}[/bold green]"
            if data["status"] == "Complete"
            else f"[bold red]✗ {data['status']}[/bold red]"
        )
        grid.add_row(status_text)
        grid.add_row()
        grid.add_row("Total Files Evaluated:", str(data["total"]))
        grid.add_row("Completed Successfully:", f"[green]{data['completed']}[/green]")
        grid.add_row("Failed:", f"[red]{data['failed']}[/red]")
        if data["failures"]:
            grid.add_row()
            grid.add_row("[bold red]Failed Jobs:[/bold red]")
            for i, failure in enumerate(data["failures"]):
                grid.add_row(f"  [cyan]{i + 1}. {failure['file']}[/cyan]")
                grid.add_row("     [red]Error:[/red]", failure["error"])
        grid.add_row()
        return Panel(
            grid, title="[bold]Final Run Summary[/]", border_style="green", box=SIMPLE
        )

    def show_final_summary(self) -> None:
        self.layout["summary"].update(self.get_final_summary_panel())
        log = structlog.get_logger("vidrec.ui")
        log.info("Final summary displayed", category="ui")

    def add_subtitle_subtask(self, description: str) -> Progress:
        if self.active_subtask_progress:
            last_task = self.active_subtask_progress[-1]
            last_task.update(last_task.tasks[0].id, completed=100)
        progress = Progress(
            TextColumn(f"  - {description}"),
            BarColumn(),
            TextColumn("[yellow]{task.percentage:>3.0f}%[/]"),
        )
        progress.add_task(description, total=100)
        self.subtitle_subtask_group = Group(
            *list(self.subtitle_subtask_group.renderables), progress
        )
        self.active_subtask_progress.append(progress)
        log = structlog.get_logger("vidrec.ui")
        log.info("Subtitle subtask added", description=description, category="ui")
        return progress

    def clear_subtitle_subtasks(self):
        self.subtitle_subtask_group = Group()
        self.active_subtask_progress = []
        self.current_task_text.plain = ""
