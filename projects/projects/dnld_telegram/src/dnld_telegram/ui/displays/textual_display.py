"""
Textual TUI Display
Professional terminal user interface with proper asyncio integration
"""

import asyncio
import time
from typing import Any

from ..base import BaseUIDisplay, ConcurrentDownloadMixin

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Footer, Header, ProgressBar, Static

    TEXTUAL_AVAILABLE = True

    class TextualDownloaderApp(App):
        """Textual TUI for Telegram downloads"""

        CSS = """
        Screen {
            background: $surface;
        }

        #main_container {
            margin: 1;
            padding: 1;
            border: solid $primary;
        }

        #status {
            height: 3;
            margin: 1 0;
            padding: 1;
            border: solid $secondary;
        }

        #progress_container {
            height: 5;
            margin: 1 0;
            padding: 1;
            border: solid $accent;
        }

        #stats {
            height: 8;
            margin: 1 0;
            padding: 1;
            border: solid $warning;
        }
        """

        def __init__(self, display_instance):
            super().__init__()
            self.display = display_instance
            self.title = "Telegram Downloader"

        def compose(self) -> ComposeResult:
            """Create the UI layout"""
            yield Header()

            with Vertical(id="main_container"):
                yield Static("🚀 Telegram Downloader Ready", id="status")

                with Vertical(id="progress_container"):
                    yield Static("Progress:", classes="label")
                    yield ProgressBar(total=100, show_eta=True, id="progress_bar")

                with Vertical(id="stats"):
                    yield Static("📊 Statistics:", classes="label")
                    yield Static("Total files: 0", id="total_files")
                    yield Static("Downloaded: 0", id="downloaded_count")
                    yield Static("Failed: 0", id="failed_count")
                    yield Static("Current: Ready", id="current_file")
                    yield Static("Speed: 0 files/s", id="speed")

            yield Footer()

        def update_stats_display(self):
            """Update the statistics display"""
            stats = self.display.stats

            start_time = stats.get("start_time")
            elapsed = (
                time.time() - float(start_time)
                if isinstance(start_time, (int, float))
                else 0
            )

            downloaded = stats.get("downloaded")
            downloaded_float = (
                float(downloaded) if isinstance(downloaded, (int, float)) else 0
            )

            speed = downloaded_float / elapsed if elapsed > 0 else 0

            self.query_one("#total_files", Static).update(
                f"Total files: {stats.get('total_files', 0)}"
            )
            self.query_one("#downloaded_count", Static).update(
                f"Downloaded: {downloaded_float}"
            )
            self.query_one("#failed_count", Static).update(
                f"Failed: {stats.get('failed', 0)}"
            )
            self.query_one("#current_file", Static).update(
                f"Current: {str(stats.get('current_file', ''))[:40]}"
            )
            self.query_one("#speed", Static).update(f"Speed: {speed:.1f} files/s")

        def update_progress_display(self, current: int, filename: str, status: str):
            """Update progress display from external calls"""
            # Update progress bar
            progress_bar = self.query_one("#progress_bar", ProgressBar)
            progress_bar.progress = current

            # Update status
            self.query_one("#status", Static).update(
                f"📥 {status.title()}: {filename[:50]}..."
            )

            # Update current file
            self.display.stats["current_file"] = filename

            # Update stats display
            self.update_stats_display()
except ImportError:
    TEXTUAL_AVAILABLE = False
    TextualDownloaderApp = None


class TextualDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Textual TUI-based display"""

    def __init__(
        self,
        console: Any | None = None,
        show_file_progress: bool = True,
    ):
        super().__init__(console=console)
        self.app: TextualDownloaderApp | None = None
        self.app_task: asyncio.Task | None = None

        if not TEXTUAL_AVAILABLE:
            raise ImportError(
                "textual not available. Install with: pip install textual"
            )

    async def __aenter__(self) -> "TextualDisplay":
        """Enter the async context manager."""
        print("🚀 Textual TUI Display initialized")
        print("🎯 Starting Textual TUI...")

        # Create and start the Textual app
        self.app = TextualDownloaderApp(self)
        self.app_task = asyncio.create_task(self.app.run_async())

        # Wait a moment for the app to initialize
        await asyncio.sleep(1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager."""
        if self.app:
            self.app.exit()
        if self.app_task:
            try:
                await asyncio.wait_for(self.app_task, timeout=5)
            except TimeoutError:
                self.app_task.cancel()

    async def start_progress(self, total_files: int) -> None:
        """Start Textual progress display"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()

        if self.app:
            # Initialize progress bar
            progress_bar = self.app.query_one("#progress_bar", ProgressBar)
            progress_bar.total = total_files
            progress_bar.progress = 0

            self.app.query_one("#status", Static).update(
                f"🚀 Starting download of {total_files} files..."
            )
            self.app.update_stats_display()

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update Textual progress display"""
        if self.app:
            self.app.update_progress_display(current, filename, status)

    async def finish_progress(self) -> None:
        """Finish Textual progress and show summary"""
        if self.app:
            elapsed = time.time() - float(self.display.stats.get("start_time", 0.0))
            success_rate = (
                (
                    float(self.display.stats.get("downloaded", 0.0))
                    / float(self.display.stats.get("total_files", 1.0))
                    * 100
                )
                if float(self.display.stats.get("total_files", 1.0)) > 0
                else 0
            )

            self.app.query_one("#status", Static).update(
                f"✅ Download completed! {self.display.stats['downloaded']}/{self.display.stats['total_files']} files "
                f"({success_rate:.1f}% success) in {elapsed:.1f}s"
            )
            self.display.stats["current_file"] = "Completed"
            self.app.update_stats_display()

            # Keep the UI open for a moment to show results
            await asyncio.sleep(3)

    async def download_files(
        self, files: list[dict[str, Any]], download_func
    ) -> list[bool]:
        """
        Download files with Textual TUI display

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
        if total:
            self.stats["total_files"] = total
        # Textual handles this in its own UI logic

    def start_main_task(self, task_id: str) -> None:
        """Start a main task"""
        pass  # Textual manages its own task lifecycle

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        """Update main task progress"""
        if advance > 0:
            self.stats["downloaded"] = (
                float(self.stats.get("downloaded", 0.0)) + advance
            )
        # Textual updates happen via reactive updates

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        """Complete a main task"""
        pass  # Textual handles completion in its UI

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False  # Textual has built-in Ctrl+C handling

    def log(self, message: str, level: str = "info") -> None:
        """Log a message"""
        print(f"[{level.upper()}] {message}")  # Log outside of TUI

    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task"""
        # Textual manages individual file progress in its own UI
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        pass  # Textual handles this in download worker

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task"""
        pass  # Textual handles this reactively

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task"""
        pass  # Textual handles completion in UI

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task"""
        self.log(f"Error: {filename} - {error_msg}", "error")
