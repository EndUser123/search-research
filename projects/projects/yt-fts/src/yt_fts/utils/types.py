"""
Type definitions for yt-fts.

This module contains centralized type definitions used throughout the yt-fts
application to ensure type safety and consistency.

Contract Best Practices:
- Use TypedDict for all cross-module data structures
- Use Protocol for interface definitions
- Run mypy/pyright in CI to catch contract violations
- Update TypedDict when adding new fields (not dict[str, Any])
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, TypedDict, TypeVar, Union

from typing_extensions import NotRequired, Required

# Generic type variable
T = TypeVar("T")

# =============================================================================
# Database Types
# =============================================================================


class ChannelInfo(TypedDict):
    """Type definition for channel information."""

    id: str
    name: str
    url: str
    created_at: str


class VideoInfo(TypedDict):
    """Type definition for video information."""

    id: str
    channel_id: str
    title: str
    url: str
    date: str


class SubtitleEntry(TypedDict):
    """Type definition for subtitle entry."""

    video_id: str
    start_time: str
    text: str


# =============================================================================
# Search Types
# =============================================================================


class SearchOptions(TypedDict):
    """Type definition for search options."""

    query: str
    channel_id: str | None
    video_id: str | None
    limit: int
    export: bool


class SearchResults(TypedDict, total=False):
    """
    Contract for search results passed to display plugins.

    This TypedDict defines the contract between search modules and display plugins.

    Required fields:
        query: Search query string
        scope: Search scope (all, channel, video)
        matches: List of search result matches

    Optional fields:
        total_matches: Total count of matches (derived from matches if omitted)
        total_videos: Total count of videos with matches
        total_channels: Total count of channels with matches
    """

    query: Required[str]
    scope: Required[str]
    matches: Required[list[dict[str, Any]]]
    total_matches: NotRequired[int]
    total_videos: NotRequired[int]
    total_channels: NotRequired[int]


# =============================================================================
# Display & UI Types (Cross-Module Contracts)
# =============================================================================


class RssInfo(TypedDict, total=False):
    """
    Contract for RSS feed check results.

    This TypedDict defines the contract between batch_downloader and display plugins.
    When adding fields, update this TypedDict instead of using dict[str, Any].

    Required fields:
        status: RSS check status ('skip', 'new_videos', 'gap_detected', 'error')
        message: Human-readable status message

    Optional fields:
        missing_count: Number of missing videos (if applicable)
        scan_count: Number to scan (after max_videos limit)
        error_msg: Error message (if status == 'error')
    """

    status: Required[str]
    message: Required[str]
    missing_count: NotRequired[int]
    scan_count: NotRequired[int]
    error_msg: NotRequired[str]


class DownloadResultInfo(TypedDict, total=False):
    """
    Contract for download result information.

    This TypedDict defines the contract between batch_downloader and display plugins.

    Required fields:
        success: Boolean success status

    Optional fields:
        videos_count: Number of videos downloaded
        videos_without_subtitles: Videos that had no subtitles
        total_videos: Total videos found
        error: Error message (if failed)
        message: Success message
        target_reached: Boolean indicating if min_saved target was reached
    """

    success: Required[bool]
    videos_count: NotRequired[int]
    videos_without_subtitles: NotRequired[int]
    total_videos: NotRequired[int]
    error: NotRequired[str]
    message: NotRequired[str]
    target_reached: NotRequired[bool]


class ChannelDisplayInfo(TypedDict, total=False):
    """
    Contract for channel display header information.

    This TypedDict defines the contract for channel header display.

    Required fields:
        index: Channel index in batch (1-based)
        total: Total channels in batch
        name: Channel display name

    Optional fields:
        channel_url: YouTube channel URL for making name clickable
        db_count: Number of videos in database
        db_stats: Detailed db statistics string
        inconsistent: Whether database state is inconsistent
        inconsistency_reason: Reason for inconsistency
        db_stats_details: Detailed database statistics
        successful_downloads: Number of successful downloads for this channel
    """

    index: Required[int]
    total: Required[int]
    name: Required[str]
    channel_url: NotRequired[str]
    db_count: NotRequired[int]
    db_stats: NotRequired[str]
    inconsistent: NotRequired[bool]
    inconsistency_reason: NotRequired[str]
    db_stats_details: NotRequired[str]
    successful_downloads: NotRequired[int]


class ImportProgressInfo(TypedDict, total=False):
    """
    Contract for import progress information.

    This TypedDict defines the contract for import progress display.

    Required fields:
        source: Import source (file, url, etc.)
        progress: Current progress (0-100)
        message: Status message

    Optional fields:
        imported: Number of items imported so far
    """

    source: Required[str]
    progress: Required[int]
    message: Required[str]
    imported: NotRequired[int]


class ImportResultInfo(TypedDict, total=False):
    """
    Contract for import completion results.

    This TypedDict defines the contract for import result display.

    Required fields:
        success: Boolean success status

    Optional fields:
        imported: Number of items imported
        failed: Number of items that failed
        duration: Import duration (seconds)
        errors: List of error messages
    """

    success: Required[bool]
    imported: NotRequired[int]
    failed: NotRequired[int]
    duration: NotRequired[int]
    errors: NotRequired[list[str]]


# =============================================================================
# Configuration Types
# =============================================================================


class DatabaseConfig(TypedDict):
    """Type definition for database configuration."""

    path: str
    timeout: int
    check_same_thread: bool


class APIConfig(TypedDict):
    """Type definition for API configuration."""

    openai_key: str | None
    gemini_key: str | None
    timeout: int


class DownloadConfig(TypedDict):
    """Type definition for download configuration."""

    jobs: int
    language: str
    cookies_browser: str | None


# =============================================================================
# Protocol Types (Interface Contracts)
# =============================================================================

from typing import Protocol


class DatabaseConnection(Protocol):
    """Protocol for database connections."""

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> Any:
        """Execute database query."""
        ...

    def commit(self) -> None:
        """Commit transaction."""
        ...

    def close(self) -> None:
        """Close connection."""
        ...


class ProgressReporter(Protocol):
    """Protocol for progress reporting."""

    def report_progress(self, current: int, total: int) -> None:
        """Report progress."""
        ...

    def report_status(self, message: str) -> None:
        """Report status."""
        ...


# Union Types for common patterns
VideoId = str
ChannelId = str
SearchQuery = str
Timestamp = str

# Common return types
MaybeString = Optional[str]
MaybeInt = Optional[int]
MaybeBool = Optional[bool]

# Complex types for function signatures
VideoList = list[VideoInfo]
ChannelList = list[ChannelInfo]
SubtitleList = list[SubtitleEntry]
ConfigDict = dict[str, Any]
ErrorDict = dict[str, str | int | bool]

# File system types
FilePath = Union[str, Path]
DirPath = Union[str, Path]
