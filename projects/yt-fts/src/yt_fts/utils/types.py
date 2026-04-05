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

# =============================================================================
# Discovery Types (State-Based Video Discovery System)
# =============================================================================

# Note: ChannelState and DiscoveryMethod enums are defined in state_detection.py
# to avoid circular imports. This module provides TypedDict contracts only.


class VideoTypeEnum(str):
    """Video classification type as a string enum for type checking."""
    NORMAL = "normal"
    SHORT = "short"
    SCHEDULED = "scheduled"
    MEMBERS_ONLY = "members_only"
    UNAVAILABLE = "unavailable"
    NO_SUBTITLES = "no_subtitles"


class ChannelDiscoveryState(TypedDict, total=False):
    """
    Contract for channel discovery state information.

    This TypedDict defines the contract for state detection results.
    Used by: state_detection.py, batch_downloader.py

    Required fields:
        state: Current discovery state (TRANSITION, STEADY_STATE, RECOVERY)
        channel_id: YouTube channel ID

    Optional fields:
        db_count: Number of videos in database
        api_total: Total videos per API
        last_checked: Timestamp of last verification
        days_since_check: Days since last verification
        gap_size: Number of missing videos (if in RECOVERY)
    """

    state: Required[str]  # ChannelState enum value (from state_detection.py)
    channel_id: Required[str]
    db_count: NotRequired[int]
    api_total: NotRequired[int | None]
    last_checked: NotRequired[str | None]
    days_since_check: NotRequired[int]
    gap_size: NotRequired[int]


class DiscoveryStrategyResult(TypedDict, total=False):
    """
    Contract for discovery strategy selection result.

    This TypedDict defines the contract for strategy method selection.
    Used by: state_detection.py

    Required fields:
        method: Discovery method to use (RSS, API, YTDLP)
        reason: Human-readable reason for method selection

    Optional fields:
        quota_pct: Available quota percentage
        estimated_time: Estimated time for discovery (seconds)
    """

    method: Required[str]  # DiscoveryMethod enum value (from state_detection.py)
    reason: Required[str]
    quota_pct: NotRequired[int]
    estimated_time: NotRequired[float]


class VideoClassificationResult(TypedDict, total=False):
    """
    Contract for video classification result.

    This TypedDict defines the contract for video type classification.
    Used by: video_classifier.py

    Required fields:
        video_id: YouTube video ID
        video_type: Classification result (VideoTypeEnum)

    Optional fields:
        url: Video URL
        title: Video title
        downloadable: Whether video can be downloaded
        retryable: Whether classification should be retried later
        reason: Reason for classification (e.g., "no subtitles available")
    """

    video_id: Required[str]
    video_type: Required[str]  # VideoTypeEnum value
    url: NotRequired[str]
    title: NotRequired[str]
    downloadable: NotRequired[bool]
    retryable: NotRequired[bool]
    reason: NotRequired[str]


class DownloadQueueInfo(TypedDict, total=False):
    """
    Contract for download queue information.

    This TypedDict defines the contract for download queue results.
    Used by: state_detection.py, batch_downloader.py

    Required fields:
        priority: Queue priority ("high", "medium", "low")
        video_ids: List of video IDs to download
        reason: Reason for queue (e.g., "missing_transcripts")

    Optional fields:
        count: Number of videos in queue (derived from video_ids if omitted)
        estimated_time: Estimated download time (seconds)
    """

    priority: Required[str]
    video_ids: Required[list[str]]
    reason: Required[str]
    count: NotRequired[int]
    estimated_time: NotRequired[float]

