"""
Metrics collection utilities for dnld_telegram
"""

import time
from typing import Any


class MetricsCollector:
    """Metrics collector for monitoring application performance and statistics."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.active_downloads = 0
        self.completed_downloads = 0
        self.total_bytes_downloaded = 0
        self.download_start_times = {}
        self.download_speeds = []  # Track individual download speeds for averaging

    async def record_download_start(self, file_name: str):
        """Record the start of a download operation.

        Args:
            file_name: Name of the file being downloaded
        """
        self.active_downloads += 1
        self.download_start_times[file_name] = time.time()

    async def record_download_complete(self, file_name: str, bytes_downloaded: int):
        """Record the completion of a download operation.

        Args:
            file_name: Name of the file that was downloaded
            bytes_downloaded: Number of bytes downloaded
        """
        self.active_downloads -= 1
        self.completed_downloads += 1
        self.total_bytes_downloaded += bytes_downloaded

        # Calculate download speed for this file
        if file_name in self.download_start_times:
            start_time = self.download_start_times[file_name]
            duration = time.time() - start_time
            if duration > 0:  # Avoid division by zero
                speed = bytes_downloaded / duration  # bytes per second
                self.download_speeds.append(speed)

            # Clean up start time tracking
            del self.download_start_times[file_name]

    async def get_current_metrics(self) -> dict[str, Any]:
        """Get current metrics.

        Returns:
            Dict containing current metrics
        """
        # Calculate average download speed
        if self.download_speeds:
            # Use a moving average of recent download speeds (last 100 downloads)
            recent_speeds = self.download_speeds[-100:]
            average_speed = sum(recent_speeds) / len(recent_speeds)
        else:
            average_speed = 0

        return {
            "active_downloads": self.active_downloads,
            "completed_downloads": self.completed_downloads,
            "total_bytes_downloaded": self.total_bytes_downloaded,
            "average_download_speed": average_speed,
            "bytes_downloaded_human": self._format_bytes(self.total_bytes_downloaded),
        }

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value in a human-readable format.

        Args:
            bytes_value: Number of bytes

        Returns:
            Formatted string with appropriate unit (B, KB, MB, GB)
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
