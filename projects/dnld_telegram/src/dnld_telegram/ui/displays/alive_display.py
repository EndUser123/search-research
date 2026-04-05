import time
from typing import Any

from ..base import BaseUIDisplay, ConcurrentDownloadMixin

try:
    from alive_progress import alive_bar

    ALIVE_PROGRESS_AVAILABLE = True
except ImportError:
    ALIVE_PROGRESS_AVAILABLE = False


class AliveDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Alive-Progress based display"""

    def __init__(
        self,
        console: Any | None = None,
        show_file_progress: bool = True,
    ):
        super().__init__(console=console)
        self.bar = None

        if not ALIVE_PROGRESS_AVAILABLE:
            raise ImportError(
                "alive-progress not available. Install with: pip install alive-progress"
            )

    async def initialize(self) -> None:
        """Initialize the Alive-Progress display"""
        print("🚀 Alive-Progress Display initialized")
        print()

    async def start_progress(self, total_files: int) -> None:
        """Start Alive-Progress bar"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()

        # Create alive-progress bar
        self.bar = alive_bar(
            total_files,
            title="Telegram Download",
            bar="smooth",
            spinner="dots_waves",
            stats="{count}/{total} files",
            elapsed=True,
            eta=True,
            monitor=True,
            stats_end=True,
        ).__enter__()

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update Alive-Progress display"""
        if self.bar:
            # Update progress bar text based on status
            if status == "downloading":
                self.bar.text = f"📥 {filename[:40]}"
            elif status == "completed":
                self.bar.text = f"✅ {filename[:40]}"
                self.bar()  # Increment progress
            elif status == "failed":
                self.bar.text = f"❌ {filename[:40]} (Failed)"
                self.bar()  # Increment progress
            elif status == "error":
                self.bar.text = f"💥 {filename[:40]} (Error)"
                self.bar()  # Increment progress

    async def finish_progress(self) -> None:
        """Finish Alive-Progress and show summary"""
        if self.bar:
            self.bar.__exit__(None, None, None)
            self.bar = None

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

        print("\n🎉 Download completed!")
        print("📊 Results:")
        print(f"   ✅ Downloaded: {downloaded_files}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print(f"   📈 Success rate: {success_rate:.1f}%")
        print(f"   ⏱️  Total time: {elapsed:.1f} seconds")

        if elapsed > 0:
            print(f"   🚀 Average speed: {downloaded_files / elapsed:.1f} files/second")
        else:
            print("   🚀 Average speed: N/A (elapsed time is zero)")

    async def cleanup(self) -> None:
        """Cleanup Alive-Progress resources"""
        if self.bar:
            self.bar.__exit__(None, None, None)
            self.bar = None

    async def download_files(
        self, files: list[dict[str, Any]], download_func: Any
    ) -> list[bool]:
        """
        Download files with Alive-Progress display

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
            print(f"📋 Task: {description} ({total} items)")

    def start_main_task(self, task_id: str) -> None:
        """Start a main task"""
        pass  # Alive-progress starts automatically

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        """Update main task progress"""
        if advance > 0:
            current_downloaded = self.stats.get("downloaded", 0)
            if isinstance(current_downloaded, (int, float)):
                self.stats["downloaded"] = float(current_downloaded) + advance
            else:
                self.stats["downloaded"] = advance
            if self.bar:
                self.bar()  # Advance alive-progress bar

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        """Complete a main task"""
        if final_status:
            print(f"✅ {final_status}")

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False  # Alive-progress doesn't have built-in termination detection

    def log(self, message: str, level: str = "info") -> None:
        """Log a message"""
        print(f"[{level.upper()}] {message}")

    def update_stats(self, **kwargs):
        """Update statistics"""
        self.stats.update(kwargs)

    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task"""
        if self.bar:
            self.bar.text = f"Starting: {filename}"
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        if self.bar:
            self.bar.text = f"Downloading: {filename}"

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task"""
        if self.bar:
            self.bar.text = f"Downloading: {filename} ({advance:,} bytes)"

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task"""
        if self.bar:
            self.bar.text = f"Completed: {filename}"

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task"""
        if self.bar:
            self.bar.text = f"Error: {filename}"
        print(f"❌ Error: {filename} - {error_msg}")
