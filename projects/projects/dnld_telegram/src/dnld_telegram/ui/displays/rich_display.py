import time
from typing import Any, cast

from ..base import BaseUIDisplay, ConcurrentDownloadMixin

try:
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        FileSizeColumn,
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
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class RichDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Rich-based progress display (improved version)"""

    def __init__(
        self,
        console: Console | None = None,
        show_file_progress: bool = True,
    ):
        super().__init__(console=console)
        self.console = console if console is not None else Console()
        self.show_file_progress = show_file_progress
        self.download_tasks: dict[str, TaskID] = {}
        self.main_tasks: dict[str, TaskID] = {}
        self.progress: Progress | None = None
        self.live: Live | None = None
        self.layout: Layout | None = None
        self.current_file: str = ""
        self.session_start_time: float = 0
        self.total_files_count: int = 0
        self.current_channel: str = ""

        if not RICH_AVAILABLE:
            raise ImportError("rich not available. Install with: pip install rich")

    async def initialize(self) -> None:
        """Initialize the Rich display"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

        if self.console:
            self.console.print("🚀 Rich Progress Display initialized")
            self.console.print()

    async def start_progress(self, total_files: int) -> None:
        """Start enhanced Rich progress display"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()
        self.session_start_time = time.time()
        self.total_files_count = total_files

        # Create enhanced progress with download-specific columns
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn(
                "[blue]{task.completed}[/blue]/[green]{task.total}[/green] files"
            ),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        # Create layout for enhanced display
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=3),
            Layout(name="stats", size=5),
            Layout(name="current", size=2),
        )

        # Start the progress display
        self.progress.start()

        # Add main task with better description
        description = f"📥 Downloading from {self.current_channel or 'channel'}"
        self.task_id: TaskID | None = self.progress.add_task(
            description, total=total_files
        )

        # Start live display
        self._update_live_display()
        if self.live is None:
            self.live = Live(self.layout, console=self.console, refresh_per_second=4)
            self.live.start()

    def _update_live_display(self) -> None:
        """Update the live display layout"""
        if not self.layout:
            return

        # Header panel
        header_table = Table.grid(padding=1)
        header_table.add_column(style="cyan", justify="left")
        header_table.add_column(style="magenta", justify="center")
        header_table.add_column(style="green", justify="right")

        header_table.add_row(
            "🎯 dnld_telegram",
            f"📁 {self.current_channel or 'Loading...'}",
            f"🕒 {time.strftime('%H:%M:%S')}",
        )

        self.layout["header"].update(Panel(header_table, border_style="blue"))

        # Progress panel
        if self.progress:
            self.layout["progress"].update(
                Panel(self.progress, title="Progress", border_style="green")
            )

        # Stats panel
        stats_table = self._create_stats_table()
        self.layout["stats"].update(
            Panel(stats_table, title="Statistics", border_style="yellow")
        )

        # Current file panel
        current_text = self._get_current_file_display()
        self.layout["current"].update(
            Panel(current_text, title="Current File", border_style="cyan")
        )

    def _create_stats_table(self) -> Table:
        """Create statistics table"""
        table = Table.grid(padding=1)
        table.add_column(style="bold cyan", justify="left", min_width=15)
        table.add_column(style="white", justify="right")

        # Calculate stats
        elapsed = (
            time.time() - self.session_start_time if self.session_start_time else 0
        )
        completed = self.stats.get("downloaded", 0)
        failed = self.stats.get("failed", 0)
        total = self.total_files_count

        # Calculate rates
        completion_rate = (completed / total * 100) if total > 0 else 0
        files_per_second = (completed / elapsed) if elapsed > 0 else 0

        # Add rows
        table.add_row("✅ Completed:", f"{completed:,}")
        table.add_row("❌ Failed:", f"{failed:,}")
        table.add_row("📊 Success Rate:", f"{completion_rate:.1f}%")
        table.add_row("⚡ Speed:", f"{files_per_second:.1f} files/s")
        if elapsed > 0:
            table.add_row("⏱️ Elapsed:", f"{elapsed:.1f}s")

        return table

    def _get_current_file_display(self) -> Text:
        """Get current file display text"""
        if not self.current_file:
            return Text("Waiting for next file...", style="dim")

        # Truncate long filenames
        display_name = self.current_file
        if len(display_name) > 50:
            display_name = display_name[:25] + "..." + display_name[-22:]

        return Text(f"📄 {display_name}", style="bold white")

    def set_channel(self, channel_name: str) -> None:
        """Set the current channel name"""
        self.current_channel = channel_name
        self._update_live_display()

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update enhanced Rich progress display"""
        if self.progress is None or self.task_id is None:
            return

        progress_instance = self.progress
        task_id_instance = self.task_id

        # Update current file
        self.current_file = filename

        # Update task description based on status
        if status == "downloading":
            description = f"📥 Downloading from {self.current_channel or 'channel'}"
            # Update stats
            self.stats["current_file"] = filename
        elif status == "completed":
            description = f"📥 Downloading from {self.current_channel or 'channel'}"
            # Advance progress
            progress_instance.advance(cast(TaskID, task_id_instance), 1)
            self.stats["downloaded"] = self.stats.get("downloaded", 0) + 1
        elif status == "failed":
            description = f"📥 Downloading from {self.current_channel or 'channel'}"
            # Advance progress
            progress_instance.advance(cast(TaskID, task_id_instance), 1)
            self.stats["failed"] = self.stats.get("failed", 0) + 1
        elif status == "error":
            description = f"📥 Downloading from {self.current_channel or 'channel'}"
            # Advance progress
            progress_instance.advance(cast(TaskID, task_id_instance), 1)
            self.stats["failed"] = self.stats.get("failed", 0) + 1
        else:
            description = f"📥 {status} from {self.current_channel or 'channel'}"

        # Update the task description
        progress_instance.update(
            cast(TaskID, task_id_instance), description=description
        )

        # Update live display
        self._update_live_display()

    async def finish_progress(self) -> None:
        """Finish Rich progress and show summary"""
        # Stop live display first
        if self.live:
            self.live.stop()
            self.live = None

        if self.progress:
            # Complete the progress
            self.progress.update(
                cast(TaskID, self.task_id), description="✅ Download completed!"
            )
            self.progress.stop()

        # Final summary
        elapsed = 0.0
        if self.stats["start_time"] is not None:
            elapsed = time.time() - float(self.stats["start_time"])

        total_files_raw = self.stats.get("total_files", 0)
        total_files = (
            float(total_files_raw) if isinstance(total_files_raw, (int, float)) else 0.0
        )
        downloaded_files_raw = self.stats.get("downloaded", 0)
        downloaded_files = (
            float(downloaded_files_raw)
            if isinstance(downloaded_files_raw, (int, float))
            else 0.0
        )

        success_rate = (downloaded_files / total_files * 100) if total_files > 0 else 0

        # Enhanced summary with Rich formatting and panels
        if self.console:
            self.console.print()

            # Create summary table
            summary_table = Table.grid(padding=1)
            summary_table.add_column(style="bold cyan", justify="left", min_width=20)
            summary_table.add_column(style="white", justify="right")

            summary_table.add_row("📊 Total Files:", f"{int(total_files):,}")
            summary_table.add_row(
                "✅ Downloaded:", f"[green]{int(downloaded_files):,}[/green]"
            )
            summary_table.add_row(
                "❌ Failed:", f"[red]{self.stats.get('failed', 0):,}[/red]"
            )
            summary_table.add_row(
                "📈 Success Rate:", f"[yellow]{success_rate:.1f}%[/yellow]"
            )
            summary_table.add_row("⏱️ Total Time:", f"[blue]{elapsed:.1f}s[/blue]")

            if elapsed > 0:
                summary_table.add_row(
                    "🚀 Average Speed:",
                    f"[cyan]{downloaded_files / elapsed:.1f}[/cyan] files/s",
                )
            else:
                summary_table.add_row("🚀 Average Speed:", "[cyan]N/A[/cyan]")

            # Create final summary panel
            summary_panel = Panel(
                summary_table,
                title="[bold green]✅ Download Summary[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

            self.console.print(summary_panel)

            # Additional completion message
            if success_rate >= 95:
                self.console.print(
                    "[bold green]🎉 Excellent! Nearly all files downloaded successfully.[/bold green]"
                )
            elif success_rate >= 80:
                self.console.print(
                    "[bold yellow]👍 Good! Most files downloaded successfully.[/bold yellow]"
                )
            else:
                self.console.print(
                    "[bold red]⚠️ Warning: Many files failed to download.[/bold red]"
                )

    async def cleanup(self) -> None:
        """Cleanup Rich resources"""
        # Stop live display if running
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass  # Ignore errors during cleanup
            self.live = None

        # Stop progress display
        if self.progress:
            try:
                self.progress.stop()
            except Exception:
                pass  # Ignore errors during cleanup
            self.progress = None

        # Clear layout
        self.layout = None

        # Clear task tracking
        self.download_tasks.clear()
        self.main_tasks.clear()

    async def download_files(
        self, files: list[dict[str, Any]], download_func: Any
    ) -> list[bool]:
        """
        Download files with Rich progress display

        Args:
            files: List of file info dictionaries
            download_func: Async function to download a single file

        Returns:
            List of success/failure results
        """
        return await self.download_files_concurrent(files, download_func, 2)

    # Missing interface methods for compatibility
    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        """Add a main task"""
        if total and self.progress:
            rich_task_id = self.progress.add_task(description, total=total)
            self.main_tasks = getattr(self, "main_tasks", {})
            self.main_tasks[str(task_id)] = rich_task_id

    def start_main_task(self, task_id: str) -> None:
        """Start a main task"""
        main_tasks = getattr(self, "main_tasks", {})
        if task_id in main_tasks and self.progress:
            self.progress.start_task(main_tasks[task_id])

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        """Update main task progress"""
        main_tasks = getattr(self, "main_tasks", {})
        if task_id in main_tasks and self.progress:
            if advance > 0:
                self.progress.update(main_tasks[task_id], advance=advance)
            if status:
                self.progress.update(main_tasks[task_id], description=status)

    def complete_main_task(self, task_id: str, final_status: str | None = None) -> None:
        """Complete a main task"""
        main_tasks = getattr(self, "main_tasks", {})
        if task_id in main_tasks and self.progress:
            if final_status:
                self.progress.update(main_tasks[task_id], description=final_status)

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False  # Rich doesn't have built-in termination detection

    def log(self, message: str, level: str = "info") -> None:
        """Log a message"""
        if self.console:
            self.console.print(f"[{level.upper()}] {message}")
        else:
            print(f"[{level.upper()}] {message}")

    def update_stats(self, **kwargs):
        """Update statistics"""
        self.stats.update(kwargs)

    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task"""
        if self.progress:
            task_id = self.progress.add_task(f"📁 {filename}", total=total_bytes)
            download_tasks = getattr(self, "download_tasks", {})
            download_tasks[filename] = task_id
            self.download_tasks = download_tasks
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        download_tasks = getattr(self, "download_tasks", {})
        if filename in download_tasks and self.progress:
            self.progress.start_task(download_tasks[filename])

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task"""
        download_tasks = getattr(self, "download_tasks", {})
        if filename in download_tasks and self.progress:
            self.progress.update(download_tasks[filename], advance=advance)

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task"""
        download_tasks = getattr(self, "download_tasks", {})
        if filename in download_tasks and self.progress:
            task_id = download_tasks[filename]
            self.progress.update(task_id, description=f"✅ {filename}")
            # Rich tasks can be marked as complete
            del download_tasks[filename]

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task"""
        download_tasks = getattr(self, "download_tasks", {})
        if filename in download_tasks and self.progress:
            task_id = download_tasks[filename]
            self.progress.update(task_id, description=f"❌ {filename}")
            del download_tasks[filename]
        self.log(f"Error: {filename} - {error_msg}", "error")
