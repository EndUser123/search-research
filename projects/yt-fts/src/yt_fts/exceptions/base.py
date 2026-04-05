"""
Base exceptions for yt-fts.

Core exception classes that serve as the foundation for all yt-fts error handling.
"""
from __future__ import annotations

from typing import Any


class YtftsError(Exception):
    """Base exception for all yt-fts errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Initialize yt-fts error.

        Args:
            message: Error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """
        Return string representation of the error with details.

        Returns:
            Error message with optional details in parentheses
        """
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DownloadError(YtftsError):
    """Base exception for download-related errors."""


class VideoNotFoundError(DownloadError):
    """Video not found on YouTube or has been removed."""


class SubtitleNotFoundError(DownloadError):
    """Subtitles not available for the requested video."""


class PlaylistProcessingError(YtftsError):
    """Error processing a YouTube playlist."""


class DatabaseError(YtftsError):
    """Database operation error."""


class ValidationError(YtftsError):
    """Input validation error."""


class TimeoutError(YtftsError):
    """Operation timed out."""
