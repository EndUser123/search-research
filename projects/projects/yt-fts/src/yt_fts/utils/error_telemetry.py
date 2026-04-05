"""
Error Telemetry Module for yt-dlp Error Distribution Tracking

Tracks error category distribution during batch operations and provides
summary statistics for debugging and monitoring.
"""

import logging
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any

from .error_classifier import ErrorCategory

# Constants (PLR2004)
_DEFAULT_MAX_RECENT_ERRORS = 100
_MAX_RECENT_ERRORS_LIMIT = 100


class TelemetryEvent(Enum):
    """Types of telemetry events."""
    ERROR_OCCURRED = "error_occurred"
    VIDEO_FAILED = "video_failed"
    CHANNEL_FAILED = "channel_failed"
    DOWNLOAD_COMPLETED = "download_completed"
    BATCH_COMPLETED = "batch_completed"


@dataclass
class ErrorRecord:
    """Record of a single error occurrence."""
    category: ErrorCategory
    message: str
    video_id: str | None = None
    channel_id: str | None = None
    timestamp: float | None = None
    context: dict[str, Any] | None = None


@dataclass
class ErrorStats:
    """
    Statistics for error occurrences during a batch operation.

    Attributes:
        total_errors: Total number of errors recorded
        by_category: Counter of errors by ErrorCategory
        by_channel: Counter of errors by channel_id
        recent_errors: List of most recent errors (max 100)
    """
    total_errors: int = 0
    by_category: Counter[ErrorCategory] = field(default_factory=Counter)
    by_channel: Counter[str] = field(default_factory=Counter)
    recent_errors: list[ErrorRecord] = field(default_factory=list)

    def add_error(self, error: ErrorRecord) -> None:
        """Add an error record to statistics."""
        self.total_errors += 1
        self.by_category[error.category] += 1
        if error.channel_id:
            self.by_channel[error.channel_id] += 1

        # Keep only recent errors
        self.recent_errors.append(error)
        if len(self.recent_errors) > _MAX_RECENT_ERRORS_LIMIT:
            self.recent_errors.pop(0)

    def get_summary(self) -> str:
        """Get a human-readable summary of error statistics."""
        if self.total_errors == 0:
            return "No errors recorded"

        lines = [
            f"Total errors: {self.total_errors}",
            "",
            "Errors by category:",
        ]
        for category, count in self.by_category.most_common():
            percentage = (count / self.total_errors) * 100
            lines.append(f"  - {category.value}: {count} ({percentage:.1f}%)")

        if self.by_channel:
            lines.append("")
            lines.append("Top affected channels:")
            for channel_id, count in self.by_channel.most_common(5):
                lines.append(f"  - {channel_id}: {count} errors")

        return "\n".join(lines)


class ErrorTelemetry:
    """
    Thread-safe error telemetry collector for batch operations.

    Tracks error distribution and provides summary statistics
    at the end of batch operations.

    Usage:
        telemetry = ErrorTelemetry()

        # Record errors as they occur
        telemetry.record_error(
            category=ErrorCategory.RATE_LIMITED,
            message="Rate limit exceeded",
            channel_id="UCxxxx",
        )

        # Get summary at end of batch
        print(telemetry.get_summary())
    """

    def __init__(self, max_recent_errors: int = _DEFAULT_MAX_RECENT_ERRORS) -> None:
        """
        Initialize error telemetry collector.

        Args:
            max_recent_errors: Maximum number of recent errors to keep in memory
        """
        self._stats = ErrorStats()
        self._lock = Lock()
        self._max_recent_errors = max_recent_errors
        self._logger = logging.getLogger(__name__)

    def record_error(
        self,
        category: ErrorCategory,
        message: str,
        video_id: str | None = None,
        channel_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Record an error occurrence.

        Thread-safe method to add error to telemetry.

        Args:
            category: ErrorCategory enum value
            message: Human-readable error message
            video_id: Optional video ID that failed
            channel_id: Optional channel ID that failed
            context: Optional additional context dictionary
        """
        error = ErrorRecord(
            category=category,
            message=message,
            video_id=video_id,
            channel_id=channel_id,
            timestamp=time.time(),
            context=context,
        )

        with self._lock:
            self._stats.add_error(error)
            self._logger.debug(
                "Error recorded: category=%s, channel=%s, video=%s",
                category.value,
                channel_id,
                video_id,
            )

    def get_stats(self) -> ErrorStats:
        """
        Get a snapshot of current error statistics.

        Returns:
            ErrorStats copy (thread-safe)
        """
        with self._lock:
            # Return a copy to avoid external modification
            return ErrorStats(
                total_errors=self._stats.total_errors,
                by_category=self._stats.by_category.copy(),
                by_channel=self._stats.by_channel.copy(),
                recent_errors=self._stats.recent_errors.copy(),
            )

    def get_summary(self) -> str:
        """
        Get a human-readable summary of error statistics.

        Returns:
            Formatted summary string
        """
        stats = self.get_stats()
        return stats.get_summary()

    def display_summary(self, title: str = "Error Distribution Summary") -> str:
        """
        Get a formatted summary suitable for console display.

        Args:
            title: Title for the summary

        Returns:
            Formatted summary with title and borders
        """
        summary = self.get_summary()
        if "No errors recorded" in summary:
            return f"[green]✓ {title}[/green]\n[green]✓ No errors occurred during batch operation[/green]"

        lines = [
            f"\n[bold cyan]─ {title} ─[/bold cyan]",
            summary,
            "[bold cyan]─[/bold cyan]",
        ]
        return "\n".join(lines)

    def get_error_count(self, category: ErrorCategory | None = None) -> int:
        """
        Get the count of errors, optionally filtered by category.

        Args:
            category: Optional ErrorCategory to filter by

        Returns:
            Number of errors (total or filtered)
        """
        with self._lock:
            if category is None:
                return self._stats.total_errors
            return self._stats.by_category.get(category, 0)

    def get_top_error_categories(self, n: int = 5) -> list[tuple[ErrorCategory, int]]:
        """
        Get the top N error categories by occurrence.

        Args:
            n: Number of top categories to return

        Returns:
            List of (ErrorCategory, count) tuples
        """
        with self._lock:
            return self._stats.by_category.most_common(n)

    def get_top_affected_channels(self, n: int = 5) -> list[tuple[str, int]]:
        """
        Get the top N channels by error count.

        Args:
            n: Number of top channels to return

        Returns:
            List of (channel_id, error_count) tuples
        """
        with self._lock:
            return self._stats.by_channel.most_common(n)

    def clear(self) -> None:
        """Clear all recorded error statistics."""
        with self._lock:
            self._stats = ErrorStats()
            self._logger.debug("Error telemetry cleared")

    def has_errors(self) -> bool:
        """Check if any errors have been recorded."""
        with self._lock:
            return self._stats.total_errors > 0

    def get_rate_limit_percentage(self) -> float:
        """
        Get the percentage of errors that were rate limit related.

        Returns:
            Percentage (0-100) of rate limit errors
        """
        with self._lock:
            if self._stats.total_errors == 0:
                return 0.0
            rate_limit_count = self._stats.by_category.get(ErrorCategory.RATE_LIMITED, 0)
            return (rate_limit_count / self._stats.total_errors) * 100


# Global singleton instance for convenient access
_global_telemetry: ErrorTelemetry | None = None
_global_lock = Lock()


def get_global_telemetry() -> ErrorTelemetry:
    """Get the global error telemetry instance (lazy initialization)."""
    global _global_telemetry

    if _global_telemetry is None:
        with _global_lock:
            if _global_telemetry is None:
                _global_telemetry = ErrorTelemetry()

    return _global_telemetry


def reset_global_telemetry() -> None:
    """Reset the global error telemetry instance."""
    global _global_telemetry

    with _global_lock:
        _global_telemetry = None
