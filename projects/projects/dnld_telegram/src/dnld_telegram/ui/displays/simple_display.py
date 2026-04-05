import sys
import time
from typing import Any

from rich.console import Console

from ..base import BaseUIDisplay, ConcurrentDownloadMixin


class SimpleDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """Simple print-based progress display"""

    def __init__(
        self,
        console: Console | None = None,
        show_file_progress: bool = True,
    ):
        super().__init__(console=console)
        self.console = console or Console()

    async def initialize(self) -> None:
        """Initialize the Simple display"""
        print("🚀 Simple Progress Display initialized")
        print()

    async def start_progress(self, total_files: int) -> None:
        """Start simple progress display"""
        self.stats["total_files"] = total_files
        self.stats["start_time"] = time.time()

        print(f"\n🚀 Starting download of {total_files} files...")
        print()

        # Header
        print("Progress | File                                     | Status | Speed")
        print("-" * 80)

    def update_progress_line(
        self, current: int, total: int, filename: str, status: str = "OK"
    ) -> None:
        """Update progress with simple print statements"""
        percent = (current / total) * 100
        start_time = self.stats["start_time"]
        if isinstance(start_time, (int, float)):
            elapsed = time.time() - float(start_time)
        else:
            elapsed = 0
        rate = current / elapsed if elapsed > 0 else 0

        # Clear line and print progress
        sys.stdout.write("\r" + " " * 100)  # Clear line
        sys.stdout.write(
            f"\r[{current:3d}/{total:3d}] {percent:5.1f}% | {filename[:40]:<40} | {status:>4} | {rate:.1f} files/s"
        )
        sys.stdout.flush()

    async def update_progress(
        self, current: int, filename: str, status: str = "downloading"
    ) -> None:
        """Update simple progress display"""
        status_map = {
            "downloading": "...",
            "completed": "OK",
            "failed": "FAIL",
            "error": "ERR",
        }

        display_status = status_map.get(status, status.upper()[:4])
        total_files_raw = self.stats["total_files"]
        total_files = (
            int(total_files_raw) if isinstance(total_files_raw, (int, float)) else 0
        )
        self.update_progress_line(current, total_files, filename, display_status)

    async def finish_progress(self) -> None:
        """Finish simple progress and show summary"""
        # Final summary
        elapsed = 0.0
        if self.stats["start_time"] is not None:
            start_time = self.stats["start_time"]
        if isinstance(start_time, (int, float)):
            elapsed = time.time() - float(start_time)
        else:
            elapsed = 0

        total_files_raw = self.stats.get("total_files", 0)
        total_files = (
            int(total_files_raw) if isinstance(total_files_raw, (int, float)) else 0
        )
        downloaded_files_raw = self.stats.get("downloaded", 0)
        downloaded_files = (
            int(downloaded_files_raw)
            if isinstance(downloaded_files_raw, (int, float))
            else 0
        )

        success_rate = (downloaded_files / total_files * 100) if total_files > 0 else 0

        print("\n")
        print("=" * 50)
        print("✅ Download completed!")
        print(f"📊 Downloaded: {downloaded_files}/{total_files}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"   📈 Success rate: {success_rate:.1f}%")
        print(f"⏱️  Total time: {elapsed:.1f} seconds")

        if elapsed > 0:
            print(f"🚀 Average speed: {downloaded_files / elapsed:.1f} files/second")
        else:
            print("🚀 Average speed: N/A (elapsed time is zero)")

        failed_count = self.stats["failed"]
        if isinstance(failed_count, (int, float)) and failed_count > 0:
            downloaded_raw = self.stats["downloaded"]
            total_files_raw = self.stats["total_files"]
            if (
                isinstance(downloaded_raw, (int, float))
                and isinstance(total_files_raw, (int, float))
                and total_files_raw > 0
            ):
                success_rate = float(downloaded_raw) / float(total_files_raw) * 100
                print(f"⚠️  Success rate: {success_rate:.1f}%")

    async def cleanup(self) -> None:
        """Cleanup simple display resources"""
        pass  # No cleanup needed for simple print

    async def download_files(
        self, files: list[dict[str, Any]], download_func: Any
    ) -> list[bool]:
        """
        Download files with simple progress display

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
        """Add a main task (simple display shows overall progress)"""
        if total:
            self.stats["total_files"] = total
            print(f"📋 Task: {description} ({total} items)")

    def start_main_task(self, task_id: str) -> None:
        """Start a main task"""
        pass  # Simple display starts automatically

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

    def complete_main_task(
        self, task_id: str, final_status: str | None = None
    ) -> None:
        """Complete a main task"""
        if final_status:
            print(f"\n✅ {final_status}")

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False  # Simple display doesn't handle Ctrl+C detection

    def log(self, message: str, level: str = "info") -> None:
        """Log a message"""
        print(f"[{level.upper()}] {message}")

    def update_stats(self, **kwargs):
        """Update statistics"""
        self.stats.update(kwargs)

    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task"""
        print(f"📁 Starting: {filename}")
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        pass  # Simple display doesn't track individual files

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task"""
        pass  # Simple display doesn't track individual file progress

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task"""
        print(f"✅ Completed: {filename}")

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task"""
        print(f"❌ Error: {filename} - {error_msg}")
