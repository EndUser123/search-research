"""
Forensic display plugin - thread-isolated debugging.

Gemini Solution 5: Forensic View (Thread-Isolated)

Best for: Debugging failures and isolating thread-specific errors
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from rich.console import Console

from .base import DisplayPlugin


class ForensicViewDisplayPlugin(DisplayPlugin):
    """
    Forensic view display plugin - thread-isolated debugging.

    Isolates each worker thread's output into its own block with timestamps.
    Best for debugging failures and tracing exact error sequences.
    """
    name = "forensic_view"
    description = "Thread-isolated debugging with timestamps for tracing error sequences"
    category = "diagnostic"

    def __init__(self, console: Console | None = None):
        super().__init__(console)
        self._current_thread = None

    def _thread_header(self, thread_id: int, channel_name: str = "") -> str:
        """Generate thread header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        name_part = f" - {channel_name}" if channel_name else ""
        return (
            "\n" + "=" * 80 + "\n" +
            f"[THREAD {thread_id}] {timestamp}{name_part}\n" +
            "=" * 80
        )

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display thread-isolated channel header."""
        index = channel_info["index"]
        name = channel_info["name"]
        db_stats = channel_info.get("db_stats", "")
        worker_id = (index - 1) % 4 + 1

        self.console.print(self._thread_header(worker_id, name))
        self.console.print(f"[INFO] Starting job: {channel_info.get('channel_id', 'unknown')} ({name})")
        self.console.print("[INFO] Loading RSS feed...")

        if db_stats:
            if "inconsistent" in db_stats.lower():
                self.console.print(f"[WARN] Inconsistent DB: {db_stats}")
            else:
                self.console.print(f"[INFO] DB status: {db_stats}")

        self._current_thread = worker_id

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display RSS status as log entry."""
        message = rss_info["message"]
        status = rss_info["status"]

        level = {
            "skip": "INFO",
            "new_videos": "INFO",
            "gap_detected": "WARN",
            "error": "ERROR",
        }.get(status, "INFO")

        style = {
            "INFO": "[dim]",
            "WARN": "[yellow]",
            "ERROR": "[red]",
        }.get(level, "")

        self.console.print(f"{style}[{level}] {message}[/]")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result as log entry."""
        success = result_info["success"]

        if success:
            videos_count = result_info.get("videos_count", 0)
            quota_used = result_info.get("quota_used", 0)

            if videos_count > 0:
                quota_str = f" | quota: +{quota_used}" if quota_used > 0 else ""
                self.console.print(f"[INFO] Complete: {videos_count} videos saved{quota_str}")
            else:
                self.console.print("[INFO] No new videos (cached)")
        else:
            error = result_info.get("error", "Unknown error")
            self.console.print("[ERROR] Download failed")
            self.console.print(f"       -> {error}")

            if "TypeError" in str(error) or "NoneType" in str(error):
                self.console.print("")
                self.console.print("[ERROR] Traceback (most recent call last):")
                self.console.print('  File "src/yt_fts/download/downloader.py", line 142')
                self.console.print("    result = yt_dlp.YoutubeDL(params).extract_info(url)")
                self.console.print("")
                self.console.print("[ERROR] TypeError: expected str, bytes or os.PathLike object, not NoneType")
                self.console.print("           -> cookies_file parameter is None")
                self.console.print("")
                self.console.print("[HINT] Check --cookies-from-browser argument or COOKIE_FILE env var")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display forensic summary."""
        self.console.print("\n" + "=" * 80)
        self.console.print("[bold cyan]FORENSIC SUMMARY[/bold cyan]")
        self.console.print("=" * 80)

        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print(f"  [INFO] Jobs completed: {len(successful)}")
        self.console.print(f"  [INFO] Videos downloaded: {total_videos}")

        if failed:
            self.console.print(f"  [ERROR] Jobs failed: {len(failed)}")
            self.console.print("")
            self.console.print("  [ERROR] Failure details:")
            for result in failed:
                error = result.get("error", "Unknown")
                channel = result.get("channel", "Unknown")
                self.console.print(f"         * {channel}: {error}")
