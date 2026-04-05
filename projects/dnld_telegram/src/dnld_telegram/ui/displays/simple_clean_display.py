"""
Simple clean display for UI A mode - no tqdm, just clean text output
"""

import time
from typing import Any

from ..base import BaseUIDisplay, ConcurrentDownloadMixin


class SimpleCleanDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Simple clean text display without progress bars (UI A mode)"""

    def __init__(
        self,
        console: Any | None = None,
        show_file_progress: bool = True,
        config: Any | None = None,
    ):
        super().__init__(console=console)
        self.show_file_progress = show_file_progress
        self.config = config
        self.channel_name: str | None = None
        self.current_file: str = ""
        self.start_time: float | None = None
        self.last_update_time: float = 0.0

    async def initialize(self) -> None:
        """Initialize the simple display"""
        print("🚀 Simple Progress Display initialized")
        print()

    async def start_progress(self, total_files: int) -> None:
        """Start progress tracking"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()
        self.start_time = time.time()

        channel_display = self.channel_name or "channel"
        print(f"📥 Starting download from {channel_display}")
        print(f"📊 Total files: {total_files}")
        print("-" * 60)

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update progress with simple text output"""
        self.current_file = filename
        current_time = time.time()

        # Throttle updates to avoid spam
        if current_time - self.last_update_time < 0.5:
            return
        self.last_update_time = current_time

        if status == "downloading":
            print(f"📥 Downloading: {filename}")
            self.stats["current_file"] = filename
        elif status == "completed":
            self.stats["downloaded"] = self.stats.get("downloaded", 0) + 1
            completed = self.stats["downloaded"]
            total = self.stats.get("total_files", 0)
            print(f"✅ Completed: {filename} ({completed}/{total})")
        elif status in ["failed", "error"]:
            self.stats["failed"] = self.stats.get("failed", 0) + 1
            failed = self.stats["failed"]
            print(f"❌ Failed: {filename} (total failures: {failed})")

    async def finish_progress(self) -> None:
        """Finish progress and show summary"""
        # Calculate final statistics
        elapsed = 0.0
        if self.start_time:
            elapsed = time.time() - self.start_time

        total_files = self.stats.get("total_files", 0)
        downloaded = self.stats.get("downloaded", 0)
        failed = self.stats.get("failed", 0)
        success_rate = (downloaded / total_files * 100) if total_files > 0 else 0

        # Show summary
        print("\n" + "=" * 60)
        print("🎉 Download completed!")
        print("📊 Final Summary:")
        print(f"   Total files: {total_files}")
        print(f"   ✅ Downloaded: {downloaded}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success rate: {success_rate:.1f}%")
        print(f"   ⏱️  Total time: {elapsed:.1f} seconds")

        if elapsed > 0:
            print(f"   🚀 Average speed: {downloaded / elapsed:.1f} files/second")

        if success_rate >= 95:
            print("🎉 Excellent! Nearly all files downloaded successfully.")
        elif success_rate >= 80:
            print("👍 Good! Most files downloaded successfully.")
        elif failed > 0:
            print("⚠️ Warning: Some files failed to download.")

        print("=" * 60)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass

    def set_channel_name(self, channel_name: str) -> None:
        """Set the channel name for display"""
        self.channel_name = channel_name

    # Interface methods for compatibility
    def add_main_task(
        self, task_id: str, description: str, total: int | None = None
    ) -> None:
        """Add a main task"""
        if total:
            print(f"🎯 Starting: {description} ({total} items)")

    def start_main_task(self, task_id: str) -> None:
        """Start a main task"""
        pass

    def update_main_task(
        self, task_id: str, advance: int = 0, status: str | None = None
    ) -> None:
        """Update main task progress"""
        if status:
            print(f"📊 Status: {status}")

    def complete_main_task(self, task_id: str, final_status: str | None = None) -> None:
        """Complete a main task"""
        if final_status:
            print(f"✅ Completed: {final_status}")

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False

    def log(self, message: str, level: str = "info") -> None:
        """Log a message"""
        print(f"[{level.upper()}] {message}")

    def update_stats(self, **kwargs):
        """Update statistics"""
        self.stats.update(kwargs)

    # Download task methods for compatibility
    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task"""
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        pass

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task"""
        pass

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task"""
        if self.show_file_progress:
            print(f"✅ {filename}")

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task"""
        print(f"❌ {filename}: {error_msg}")

    async def download_files(
        self, files: list[dict[str, Any]], download_func: Any
    ) -> list[bool]:
        """Download files with simple progress display"""
        max_concurrent = 2
        if self.config and hasattr(self.config, "max_concurrent"):
            max_concurrent = getattr(self.config, "max_concurrent", 2)

        return await self.download_files_concurrent(
            files, download_func, max_concurrent
        )
