"""
Log storage and management for the TUI.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


class EnhancedLogStore:
    """Enhanced log storage with filtering."""

    def __init__(self, max_logs: int = 5000):
        self.all_logs: list[dict[str, Any]] = []
        self.channel_logs: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.error_logs: list[dict[str, Any]] = []
        self.max_logs = max_logs

    def add_log(self, message: str, level: str = "INFO", channel: str | None = None):
        """Add a log entry with metadata."""
        timestamp = datetime.now()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "channel": channel,
            "formatted": f"{timestamp.strftime('%H:%M:%S')} [{level:^8}] {message}",
        }

        self.all_logs.append(log_entry)
        if len(self.all_logs) > self.max_logs:
            self.all_logs = self.all_logs[-self.max_logs :]

        if channel:
            self.channel_logs[channel].append(log_entry)

        if level in ["ERROR", "CRITICAL"]:
            self.error_logs.append(log_entry)

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of recent errors."""
        recent_errors = [
            log
            for log in self.error_logs
            if datetime.now() - log["timestamp"] < timedelta(hours=1)
        ]

        return {
            "total_recent": len(recent_errors),
            "last_error": recent_errors[-1] if recent_errors else None,
        }
