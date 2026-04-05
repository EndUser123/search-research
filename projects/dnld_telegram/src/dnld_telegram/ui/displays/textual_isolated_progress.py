"""
Textual Progress Bar in Isolation - Implementation #2
Based on docs/examples/widgets/progress_bar_isolated.py pattern
Minimal implementation with just the progress bar component
"""

import asyncio
import time
from typing import Any

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import ProgressBar, Static

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from ...ui.base import BaseUIDisplay, ConcurrentDownloadMixin, UIConfig


class MinimalProgressApp(App):
    """Minimal app with just isolated progress bar - based on official isolated example"""

    CSS = """
    Screen {
        background: $surface;
        padding: 2;
    }

    #progress_container {
        height: 8;
        border: solid $primary;
        padding: 1;
    }

    ProgressBar {
        margin: 1 0;
    }
    """

    def __init__(self, display_instance):
        super().__init__()
        self.display = display_instance
        self.title = "Download Progress"
        self.progress_bar = None

    def compose(self) -> ComposeResult:
        """Create minimal UI with just progress bar"""
        with Vertical(id="progress_container"):
            yield Static("📥 Telegram Download Progress", id="title")
            # Start indeterminate (unknown total)
            yield ProgressBar(total=None, show_eta=False, id="progress_bar")
            yield Static("Initializing...", id="status")

    def on_mount(self) -> None:
        """Initialize when app mounts"""
        self.progress_bar = self.query_one("#progress_bar", ProgressBar)

    def update_progress_display(
        self, current: int, total: int, filename: str, status: str
    ):
        """Update the isolated progress bar"""
        if self.progress_bar:
            # Switch to determinate if we now know the total
            if self.progress_bar.total is None and total > 0:
                self.progress_bar.total = total
                self.progress_bar.show_eta = True

            # Update progress
            self.progress_bar.progress = current

            # Update status
            status_text = f"{status.title()}: {filename[:50]}"
            if total > 0:
                percent = (current / total) * 100
                status_text = f"[{current}/{total}] {percent:.1f}% - {filename[:40]}"

            self.query_one("#status", Static).update(status_text)

    def set_indeterminate(self):
        """Switch to indeterminate mode"""
        if self.progress_bar:
            self.progress_bar.total = None
            self.progress_bar.show_eta = False

    def set_determinate(self, total: int):
        """Switch to determinate mode"""
        if self.progress_bar:
            self.progress_bar.total = total
            self.progress_bar.progress = 0
            self.progress_bar.show_eta = True

    def complete_progress(self, success_count: int, total_count: int, elapsed: float):
        """Show completion status"""
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        completion_text = f"✅ Complete: {success_count}/{total_count} files ({success_rate:.1f}%) in {elapsed:.1f}s"
        self.query_one("#status", Static).update(completion_text)


class TextualIsolatedProgressDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Isolated Progress Bar implementation - minimal and focused"""

    def __init__(
        self, download_dir: str = "downloads", config: UIConfig | None = None
    ):
        super().__init__()
        self.config = config or UIConfig()
        self.app: MinimalProgressApp | None = None
        self.app_task: asyncio.Task | None = None

        if not TEXTUAL_AVAILABLE:
            raise ImportError(
                "textual not available. Install with: pip install textual"
            )

    async def initialize(self) -> None:
        """Initialize the isolated progress display"""
        print("🚀 Textual Isolated Progress Display initialized")
        print(f"📁 Download directory: {self.download_dir}")
        print("🎯 Starting minimal progress bar...")

        # Create the minimal app
        self.app = MinimalProgressApp(self)
        self.app_task = asyncio.create_task(self.app.run_async())

        # Wait for app to initialize
        await asyncio.sleep(1)

    async def start_progress(self, total_files: int) -> None:
        """Start progress display"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()

        if self.app:
            if total_files > 0:
                # We know the total, start determinate
                self.app.set_determinate(total_files)
                self.app.query_one("#status", Static).update(
                    f"Starting download of {total_files} files..."
                )
            else:
                # Unknown total, start indeterminate
                self.app.set_indeterminate()
                self.app.query_one("#status", Static).update("Discovering files...")

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update isolated progress display"""
        if self.app:
            self.app.update_progress_display(
                current, self.stats["total_files"], filename, status
            )

            # Update internal stats
            if status in ["completed", "failed", "error"]:
                if status == "completed":
                    self.stats["downloaded"] += 1
                else:
                    self.stats["failed"] += 1

    async def finish_progress(self) -> None:
        """Finish isolated progress display"""
        if self.app:
            elapsed = time.time() - self.stats["start_time"]
            self.app.complete_progress(
                self.stats["downloaded"], self.stats["total_files"], elapsed
            )

            # Keep display open briefly to show results
            await asyncio.sleep(2)

    async def cleanup(self) -> None:
        """Cleanup isolated progress resources"""
        if self.app:
            self.app.exit()
        if self.app_task:
            try:
                await asyncio.wait_for(self.app_task, timeout=3)
            except TimeoutError:
                self.app_task.cancel()

    async def download_files(
        self, files: list[dict[str, Any]], download_func
    ) -> list[bool]:
        """Download files with isolated progress display"""
        return await self.download_files_concurrent(
            files, download_func, self.config.max_concurrent
        )


# Factory registration
if TEXTUAL_AVAILABLE:
    __all__ = ["TextualIsolatedProgressDisplay"]
else:
    __all__ = []
