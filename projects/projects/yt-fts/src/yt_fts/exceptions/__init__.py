"""
YT-FTS Exceptions

Custom exception classes for yt-fts applications.
Provides structured error handling and better error messages.

Author: CSF NIP Implementation Team
Version: 1.0.0
"""

from .base import (
    DatabaseError,
    DownloadError,
    PlaylistProcessingError,
    SubtitleNotFoundError,
    TimeoutError,
    ValidationError,
    VideoNotFoundError,
    YtftsError,
)
from .channel_processing import (
    AuthenticationError,
    ChannelProcessingError,
    ChannelResolutionError,
    ChannelValidationError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
)

__all__ = [
    "AuthenticationError",
    # Channel processing exceptions
    "ChannelProcessingError",
    "ChannelResolutionError",
    "ChannelValidationError",
    "ConfigurationError",
    "DatabaseError",
    # Download exceptions
    "DownloadError",
    # Network and auth exceptions
    "NetworkError",
    # Other processing exceptions
    "PlaylistProcessingError",
    "RateLimitError",
    "SubtitleNotFoundError",
    "TimeoutError",
    "ValidationError",
    "VideoNotFoundError",
    # Base exceptions
    "YtftsError",
]
