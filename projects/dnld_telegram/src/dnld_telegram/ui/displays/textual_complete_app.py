"""
Textual Complete App - Production Implementation
Full TUI for Telegram downloads with real download integration
Based on research findings for proper Textual Workers architecture
"""

import asyncio
import time
from typing import Any

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Footer, Header, ProgressBar, Static

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from ...ui.base import BaseUIDisplay, ConcurrentDownloadMixin, UIConfig


class TelegramDownloaderCompleteApp(App):
    """Production Textual TUI for Telegram downloads"""

    CSS = """
    Screen {
        background: $surface;
    }

    #main_container {
        margin: 1;
        padding: 1;
        border: solid $primary;
        height: auto;
    }

    #progress_container {
        height: 8;
        margin: 1 0;
        padding: 1;
        border: solid $accent;
    }

    #files_container {
        height: 15;
        margin: 1 0;
        padding: 1;
        border: solid $secondary;
    }

    #stats_container {
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
        self.sub_title = f"Download Directory: {display_instance.download_dir}"

        # Real download state
        self.main_progress = None
        self.file_progress_bars = {}  # filename -> ProgressBar widget
        self.current_downloads = {}  # filename -> file info

    def compose(self) -> ComposeResult:
        """Create the production UI layout"""
        yield Header()

        with Vertical(id="main_container"):
            # Main progress section
            with Vertical(id="progress_container"):
                yield Static("📥 Overall Progress:", classes="label")
                yield ProgressBar(total=None, show_eta=True, id="main_progress")
                yield Static("Ready to download...", id="main_status")

            # Individual files section - dynamically populated
            with Vertical(id="files_container"):
                yield Static("📁 Current Downloads:", classes="label")
                yield Static("No active downloads", id="files_status")

            # Statistics section
            with Vertical(id="stats_container"):
                yield Static("📊 Statistics:", classes="label")
                yield Static("Total: 0", id="total_files")
                yield Static("Downloaded: 0", id="downloaded_count")
                yield Static("Failed: 0", id="failed_count")
                yield Static("Speed: 0 files/s", id="download_speed")
                yield Static("Elapsed: 0s", id="elapsed_time")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize when app mounts"""
        self.main_progress = self.query_one("#main_progress", ProgressBar)

    def setup_main_task(self, description: str, total: int):
        """Setup main progress bar"""
        if self.main_progress:
            self.main_progress.total = total
            self.main_progress.progress = 0
            self.query_one("#main_status", Static).update(description)
            self.query_one("#total_files", Static).update(f"Total: {total}")

    def update_main_progress(self, advance: int = 0, status: str | None = None):
        """Update main progress bar"""
        if self.main_progress:
            if advance > 0:
                self.main_progress.advance(advance)
            if status:
                self.query_one("#main_status", Static).update(status)

    def add_file_download(self, filename: str, total_bytes: int):
        """Add individual file progress bar"""
        # Create new progress bar for this file
        files_container = self.query_one("#files_container", Vertical)

        # Limit to showing max 5 concurrent downloads to avoid clutter
        if len(self.file_progress_bars) >= 5:
            return

        # Create progress bar
        display_name = filename[-40:] if len(filename) > 40 else filename
        progress_bar = ProgressBar(
            total=total_bytes, show_eta=True, id=f"file_{len(self.file_progress_bars)}"
        )

        # Add to container
        files_container.mount(Static(f"📁 {display_name}"))
        files_container.mount(progress_bar)

        # Track it
        self.file_progress_bars[filename] = progress_bar
        self.current_downloads[filename] = {"bytes": total_bytes, "progress": 0}

        # Update status
        if len(self.file_progress_bars) == 1:
            self.query_one("#files_status", Static).update(
                f"{len(self.file_progress_bars)} active download"
            )
        else:
            self.query_one("#files_status", Static).update(
                f"{len(self.file_progress_bars)} active downloads"
            )

    def update_file_download(self, filename: str, advance: int):
        """Update individual file progress"""
        if filename in self.file_progress_bars:
            progress_bar = self.file_progress_bars[filename]
            progress_bar.advance(advance)
            self.current_downloads[filename]["progress"] += advance

    def complete_file_download(self, filename: str, success: bool = True):
        """Complete individual file download"""
        if filename in self.file_progress_bars:
            progress_bar = self.file_progress_bars[filename]

            # Complete the progress bar
            if success:
                progress_bar.progress = progress_bar.total or progress_bar.progress

            # Remove from tracking after a brief delay
            self.set_timer(2.0, lambda: self.remove_file_download(filename))

    def remove_file_download(self, filename: str):
        """Remove completed file download from display"""
        if filename in self.file_progress_bars:
            # Remove from tracking
            del self.file_progress_bars[filename]
            del self.current_downloads[filename]

            # Update status
            if len(self.file_progress_bars) == 0:
                self.query_one("#files_status", Static).update("No active downloads")
            elif len(self.file_progress_bars) == 1:
                self.query_one("#files_status", Static).update("1 active download")
            else:
                self.query_one("#files_status", Static).update(
                    f"{len(self.file_progress_bars)} active downloads"
                )

    def update_stats_display(self):
        """Update the statistics display"""
        stats = self.display.stats
        elapsed = time.time() - stats["start_time"] if stats["start_time"] else 0
        speed = stats["downloaded"] / elapsed if elapsed > 0 else 0

        # Calculate ETA
        if speed > 0 and stats["total_files"] > 0:
            remaining = stats["total_files"] - (stats["downloaded"] + stats["failed"])
            eta = remaining / speed if remaining > 0 else 0
            eta_text = f"{eta:.0f}s" if eta > 0 else "Complete"
        else:
            eta_text = "Calculating..."

        # Update all stats
        self.query_one("#total_files", Static).update(
            f"Total files: {stats['total_files']}"
        )
        self.query_one("#downloaded_count", Static).update(
            f"Downloaded: {stats['downloaded']}"
        )
        self.query_one("#failed_count", Static).update(f"Failed: {stats['failed']}")
        self.query_one("#current_file", Static).update(
            f"Current: {stats['current_file'][:35]}"
        )
        self.query_one("#elapsed_time", Static).update(f"Elapsed: {elapsed:.0f}s")
        self.query_one("#eta_display", Static).update(f"ETA: {eta_text}")
        self.query_one("#progress_stats", Static).update(
            f"Files: {stats['downloaded'] + stats['failed']}/{stats['total_files']} | Speed: {speed:.1f} files/s"
        )


class TextualCompleteAppDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Production Textual TUI implementation for Telegram downloads"""

    def __init__(
        self, download_dir: str = "downloads", config: UIConfig | None = None
    ):
        super().__init__()
        self.config = config or UIConfig()
        self.app: TelegramDownloaderCompleteApp | None = None
        self.app_task: asyncio.Task | None = None

        if not TEXTUAL_AVAILABLE:
            raise ImportError(
                "textual not available. Install with: pip install textual"
            )

    async def initialize(self) -> None:
        """Initialize the Textual TUI"""
        print("🚀 Textual Complete TUI Display initialized")
        print(f"📁 Download directory: {self.download_dir}")

        # Create and start the app in background
        self.app = TelegramDownloaderCompleteApp(self)
        if self.app:
            self.app.run_async()

        # Wait for app to fully initialize
        await asyncio.sleep(1)

    async def start_progress(self, total_files: int) -> None:
        """Start progress display"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()

        if self.app:
            self.app.setup_main_task(f"Downloading {total_files} files", total_files)

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update progress display"""
        if self.app:
            # Update internal stats
            if status in ["completed", "failed", "error"]:
                if status == "completed":
                    self.stats["downloaded"] += 1
                    self.app.update_main_progress(advance=1)
                else:
                    self.stats["failed"] += 1
                    self.app.update_main_progress(advance=1)

                # Update statistics display
                self.app.update_stats_display()

    async def finish_progress(self) -> None:
        """Finish progress display"""
        if self.app:
            elapsed = time.time() - self.stats["start_time"]
            success_rate = (
                (self.stats["downloaded"] / self.stats["total_files"] * 100)
                if self.stats["total_files"] > 0
                else 0
            )

            status = f"✅ Complete: {self.stats['downloaded']}/{self.stats['total_files']} files ({success_rate:.1f}%) in {elapsed:.1f}s"
            self.app.update_main_progress(status=status)

            # Keep TUI open briefly to show results
            await asyncio.sleep(3)

    async def cleanup(self) -> None:
        """Cleanup Textual resources"""
        if self.app:
            self.app.exit()
        if self.app_task:
            try:
                await asyncio.wait_for(self.app_task, timeout=5)
            except TimeoutError:
                self.app_task.cancel()

    async def download_files(
        self, files: list[dict[str, Any]], download_func: Any
    ) -> list[bool]:
        """Download files with Textual TUI display"""
        return await self.download_files_concurrent(
            files, download_func, self.config.max_concurrent
        )

    # Production interface methods - connect to real TUI
    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        """Add a main task"""
        if total and self.app:
            self.stats["total_files"] = total
            self.app.setup_main_task(description, total)

    def start_main_task(self, task_id: str) -> None:
        """Start a main task"""
        pass  # Already started in add_main_task

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        """Update main task progress"""
        if self.app:
            if advance > 0:
                self.stats["downloaded"] = self.stats.get("downloaded", 0) + advance
                self.app.update_main_progress(advance=advance)
            if status:
                self.app.update_main_progress(status=status)
            self.app.update_stats_display()

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        """Complete a main task"""
        if self.app and final_status:
            self.app.update_main_progress(status=final_status)

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False  # Textual has built-in Ctrl+C handling

    def log(self, message: str, level: str = "info") -> None:
        """Log a message"""
        # Log outside of TUI to avoid interfering with display
        print(f"[{level.upper()}] {message}")

    def update_stats(self, **kwargs):
        """Update statistics"""
        self.stats.update(kwargs)
        if self.app:
            self.app.update_stats_display()

    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task"""
        if self.app:
            self.app.add_file_download(filename, total_bytes)
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        # File download already started when added
        pass

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task"""
        if self.app:
            self.app.update_file_download(filename, advance)

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task"""
        if self.app:
            self.app.complete_file_download(filename, success=True)

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task"""
        if self.app:
            self.app.complete_file_download(filename, success=False)
        self.log(f"Error: {filename} - {error_msg}", "error")

    # Add async context manager support
    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# Factory registration would happen in __init__.py
if TEXTUAL_AVAILABLE:
    __all__ = ["TextualCompleteAppDisplay"]
else:
    __all__ = []
