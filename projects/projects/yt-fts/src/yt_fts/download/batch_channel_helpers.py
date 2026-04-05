"""
Helper functions for batch download channel processing.

Extracted from batch_downloader.py to reduce cyclomatic complexity.
These functions handle specific aspects of channel processing workflow.
"""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from typing import Any


def initialize_channel_state(
    db_count: int = 0,
    db_with_subs: int = 0,
    db_no_subs: int = 0,
    db_scheduled: int = 0,
    db_members: int = 0,
    db_unavailable: int = 0,
    db_unavail_deleted: int = 0,
    db_unavail_private: int = 0,
    db_unavail_geo: int = 0,
    db_unavail_age: int = 0,
    db_unavail_generic: int = 0,
    db_shorts: int = 0,
) -> dict[str, int]:
    """Initialize empty database statistics state.

    Returns:
        Dict with all DB stat keys set to 0
    """
    return {
        "db_count": db_count,
        "db_video_ids": set(),
        "db_with_subs": db_with_subs,
        "db_scheduled": db_scheduled,
        "db_members": db_members,
        "db_unavailable": db_unavailable,
        "db_unavail_deleted": db_unavail_deleted,
        "db_unavail_private": db_unavail_private,
        "db_unavail_geo": db_unavail_geo,
        "db_unavail_age": db_unavail_age,
        "db_unavail_generic": db_unavail_generic,
        "db_shorts": db_shorts,
        "db_no_subs": db_no_subs,
    }


def load_channel_db_stats(
    channel_id: str,
    get_vid_ids_by_channel_id: Callable,
    get_channel_stats: Callable,
    logger: Logger,
) -> dict[str, Any]:
    """Load channel statistics from database.

    Args:
        channel_id: YouTube channel ID
        get_vid_ids_by_channel_id: Function to get video IDs for channel
        get_channel_stats: Function to get channel stats
        logger: Logger instance

    Returns:
        Dict with database stats (db_count, db_video_ids, etc.)
    """
    state = initialize_channel_state()
    try:
        local_vid_ids = [v[0] for v in get_vid_ids_by_channel_id(channel_id)]
        state["db_video_ids"] = set(local_vid_ids)
        stats = get_channel_stats(channel_id)
        state["db_count"] = stats["total"]
        state["db_with_subs"] = stats["with_transcripts"]
        state["db_scheduled"] = stats["scheduled"]
        state["db_members"] = stats["members_only"]
        state["db_unavailable"] = stats["unavailable"]
        state["db_unavail_deleted"] = stats.get("unavailable_deleted", 0)
        state["db_unavail_private"] = stats.get("unavailable_private", 0)
        state["db_unavail_geo"] = stats.get("unavailable_geo", 0)
        state["db_unavail_age"] = stats.get("unavailable_age", 0)
        state["db_unavail_generic"] = stats.get("unavailable_generic", 0)
        state["db_shorts"] = stats["shorts"]
        state["db_no_subs"] = stats["without_transcripts"]
        logger.debug(
            "Querying with channel_id=%s, found %s videos",
            channel_id,
            state["db_count"],
        )
    except Exception as e:
        logger.debug(
            "Query failed with channel_id=%s: %s", channel_id, e
        )
        # Return empty state on error
        state = initialize_channel_state()
    return state


def determine_status_name(
    channel_id: str | None,
    resolved_url: str,
) -> str:
    """Determine display name for channel status.

    Args:
        channel_id: YouTube channel ID (or None)
        resolved_url: Resolved channel URL

    Returns:
        Display string for status
    """
    if channel_id:
        if len(channel_id) > 15:
            return channel_id[:20] + "..."
        return f"channel/{channel_id}"
    if "@" in resolved_url:
        handle = resolved_url.split("@")[-1].split("/")[0]
        return f"@{handle}"
    return resolved_url[:40] + "..."


def extract_handle(resolved_url: str) -> str | None:
    """Extract YouTube handle from resolved URL.

    Args:
        resolved_url: Channel URL that may contain @handle

    Returns:
        Handle string (without @) or None
    """
    if "@" in resolved_url:
        return resolved_url.split("@")[-1].split("/")[0]
    return None


def should_skip_fresh_channel(
    channel_id: str,
    db_count: int,
    freshness_hours: int,
    is_channel_fresh: Callable,
) -> tuple[bool, str | None]:
    """Check if channel was recently checked and should be skipped.

    Args:
        channel_id: YouTube channel ID
        db_count: Number of videos in database
        freshness_hours: Hours to consider channel "fresh"
        is_channel_fresh: Function to check freshness

    Returns:
        Tuple of (should_skip, skip_reason or hours_ago)
    """
    if db_count == 0 or freshness_hours <= 0:
        return False, None

    is_fresh, last_checked = is_channel_fresh(channel_id, freshness_hours)
    if is_fresh:
        from datetime import datetime

        hours_ago = int(
            (datetime.now() - datetime.fromisoformat(last_checked)).total_seconds() / 3600
        )
        return True, f"Recently checked ({hours_ago}h ago)"
    return False, None


def create_thread_db_connection(
    get_db_connection: Callable,
    timeout: float,
    thread_local: Any,
    all_conns: list,
    conns_lock: Any,
) -> Any:
    """Get or create database connection for current thread.

    Args:
        get_db_connection: Function to create new DB connection
        timeout: Connection timeout in seconds
        thread_local: threading.local() storage
        all_conns: List to track all connections for cleanup
        conns_lock: Lock for thread-safe list access

    Returns:
        Database connection for current thread
    """
    if not hasattr(thread_local, "conn"):
        conn = get_db_connection(timeout=timeout)
        thread_local.conn = conn
        with conns_lock:
            all_conns.append(conn)
    return thread_local.conn


def format_skip_message(
    rss_skip: bool,
    should_skip_download: bool,
    rss_result: Any,
) -> str:
    """Format skip message for display.

    Args:
        rss_skip: Whether RSS check indicated skip
        should_skip_download: Whether download should be skipped
        rss_result: RSS check result object

    Returns:
        Formatted skip message string
    """
    if rss_skip:
        msg = "all videos already in database"
        if (
            rss_result
            and hasattr(rss_result, "unavailable_video_ids")
            and isinstance(rss_result.unavailable_video_ids, list)
            and rss_result.unavailable_video_ids
        ):
            msg += f" (tracking {len(rss_result.unavailable_video_ids)} unavailable)"
        return msg
    return "Channel complete (verified via API)"


def recheck_unavailable_videos(
    channel_id: str,
    rss_checker: Any,
    get_videos_needing_recheck: Callable,
    update_video_last_checked: Callable,
) -> list[str]:
    """Recheck previously unavailable videos for availability.

    Args:
        channel_id: YouTube channel ID
        rss_checker: RSS checker instance
        get_videos_needing_recheck: Function to get videos needing recheck
        update_video_last_checked: Function to update video last_checked

    Returns:
        List of video IDs that became available
    """
    from datetime import datetime

    recheck_available = []
    old_unavailable = get_videos_needing_recheck(days=7)
    channel_old_unavailable = [
        (v[0], v[2]) for v in old_unavailable if v[1] == channel_id
    ]
    if channel_old_unavailable and rss_checker:
        availability = rss_checker._check_video_availability(
            [v[0] for v in channel_old_unavailable]
        )
        for vid, _title in channel_old_unavailable:
            status = availability.get(vid, "unknown")
            if status == "available":
                recheck_available.append(vid)
            update_video_last_checked(vid, datetime.now().isoformat())
    return recheck_available


def perform_rss_check(
    channel_id: str | None,
    handle: str | None,
    resolved_url: str,
    db_video_ids: set,
    db_count: int,
    rss_checker: Any,
    log_operation: Callable,
    original_channel: str,
) -> tuple[Any, bool]:
    """Perform RSS check for channel.

    Args:
        channel_id: YouTube channel ID
        handle: Channel handle
        resolved_url: Resolved channel URL
        db_video_ids: Set of existing video IDs
        db_count: Number of videos in database
        rss_checker: RSS checker instance
        log_operation: Logging function
        original_channel: Original channel input

    Returns:
        Tuple of (rss_result, new_channel_skipped_rss)
    """
    new_channel_skipped_rss = False
    rss_result = None

    if db_count == 0:
        # New channel - skip RSS, use yt-api
        new_channel_skipped_rss = True
    elif channel_id:
        log_operation(
            "rss_check_start",
            f"Starting RSS check for: {original_channel}",
            channel=original_channel,
            channel_id=channel_id,
            db_video_count=len(db_video_ids) if db_video_ids else 0,
            level=10,
        )
        rss_result = rss_checker.check(
            channel_id=channel_id,
            handle=handle,
            resolved_url=resolved_url,
            db_video_ids=db_video_ids,
        )

    if rss_result:
        log_operation(
            "rss_check_complete",
            f"RSS check complete for: {original_channel}",
            channel=original_channel,
            channel_id=channel_id,
            status=rss_result.status,
            video_count=len(rss_result.video_ids) if rss_result.video_ids else 0,
            level=10,
        )

    return rss_result, new_channel_skipped_rss


def get_unavailable_video_title(status: str) -> str:
    """Get display title for unavailable video based on status.

    Args:
        status: Video status string

    Returns:
        Display title for the unavailable video
    """
    status_to_title = {
        "scheduled": "[Scheduled]",
        "members_only": "[Members only]",
        "unavailable/deleted": "[Unavailable/Deleted]",
        "unavailable/private": "[Unavailable/Private]",
        "unavailable/geo": "[Unavailable/Geo-blocked]",
    }
    return status_to_title.get(status, "[Unavailable]")


def process_unavailable_videos(
    channel_id: str,
    unavailable_video_ids: list,
    unavailable_video_status: dict,
    add_video: Callable,
) -> None:
    """Add unavailable videos to database with appropriate titles.

    Args:
        channel_id: YouTube channel ID
        unavailable_video_ids: List of unavailable video IDs
        unavailable_video_status: Dict mapping video IDs to statuses
        add_video: Function to add video to database
    """
    from datetime import datetime

    last_checked = datetime.now().isoformat()
    status_dict = unavailable_video_status or {}

    for vid in unavailable_video_ids:
        try:
            status = status_dict.get(vid, "unavailable")
            title = get_unavailable_video_title(status)
            add_video(
                channel_id=channel_id,
                video_id=vid,
                video_title=title,
                video_url=f"https://youtu.be/{vid}",
                video_date="",
                last_checked=last_checked,
            )
        except Exception:
            pass


def determine_rss_status(
    rss_result: Any | None,
    rss_skip: bool,
    rss_missing_count: int | None,
    new_channel_skipped_rss: bool,
) -> str:
    """Determine RSS status from result and flags.

    Args:
        rss_result: RSS check result
        rss_skip: Whether to skip
        rss_missing_count: Number of missing videos
        new_channel_skipped_rss: Whether new channel skipped RSS

    Returns:
        RSS status string: "skip", "new_videos", "gap_detected", "error"
    """
    if rss_missing_count == 0:
        return "skip"
    if not new_channel_skipped_rss:
        status = rss_result.status if rss_result else "error"
        if rss_skip:
            status = "skip"
        return status
    return "new_videos" if rss_missing_count else "skip"


def format_rss_status_message(
    rss_status: str,
    rss_result: Any | None,
    rss_missing_count: int | None,
    rss_error_msg: str | None,
    new_channel_skipped_rss: bool,
) -> tuple[str, str]:
    """Format RSS status message for display.

    Args:
        rss_status: RSS status string
        rss_result: RSS check result object
        rss_missing_count: Number of missing videos
        rss_error_msg: Error message from RSS check
        new_channel_skipped_rss: Whether new channel skipped RSS

    Returns:
        Tuple of (status, message) for display
    """
    if rss_status == "skip":
        msg = "all videos already in database"
        if (
            rss_result
            and hasattr(rss_result, "unavailable_video_ids")
            and isinstance(rss_result.unavailable_video_ids, list)
            and rss_result.unavailable_video_ids
        ):
            msg += f" (tracking {len(rss_result.unavailable_video_ids)} unavailable)"
        return "skip", msg

    if rss_status == "new_videos":
        if new_channel_skipped_rss:
            return "new_videos", "new channel, switching to yt-api for full scan"
        available_count = rss_missing_count or 0
        unavailable_count = (
            len(rss_result.unavailable_video_ids)
            if (
                rss_result
                and hasattr(rss_result, "unavailable_video_ids")
                and isinstance(rss_result.unavailable_video_ids, list)
            )
            else 0
        )
        total_new = available_count + unavailable_count
        video_word = "video" if total_new == 1 else "videos"
        if unavailable_count > 0:
            msg = f"discovered {total_new} new {video_word} not in db ({available_count} available, {unavailable_count} unavailable)"
        else:
            msg = f"discovered {total_new} new {video_word} not in db"
        return "new_videos", msg

    if rss_status == "gap_detected":
        return "gap_detected", "gaps detected, scanning full channel"

    if rss_result and hasattr(rss_result, "message") and isinstance(rss_result.message, str) and rss_result.message:
        return "skip", f"{rss_result.message}, using direct scan"

    if rss_error_msg:
        return "skip", f"{rss_error_msg}, using direct scan"

    return "skip", "feed unavailable, using direct scan"


class ChannelDownloadContext:
    """Context manager for channel download operations.

    Manages thread-local database connections and executor cleanup.
    """

    def __init__(
        self,
        get_db_connection: Callable,
        max_workers: int = 1,
        db_timeout: float = 30.0,
    ):
        """Initialize channel download context.

        Args:
            get_db_connection: Function to create DB connections
            max_workers: Maximum number of worker threads
            db_timeout: Database connection timeout
        """
        import threading

        self._get_db_connection = get_db_connection
        self._max_workers = max_workers
        self._db_timeout = db_timeout
        self._thread_local = threading.local()
        self._all_conns: list[Any] = []
        self._conns_lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None

    def get_thread_conn(self) -> Any:
        """Get database connection for current thread."""
        return create_thread_db_connection(
            self._get_db_connection,
            self._db_timeout,
            self._thread_local,
            self._all_conns,
            self._conns_lock,
        )

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Get thread pool executor (create if needed)."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        return self._executor

    def cleanup(self) -> None:
        """Clean up resources (DB connections and executor)."""
        import contextlib

        for conn in self._all_conns:
            with contextlib.suppress(Exception):
                conn.close()
        self._all_conns.clear()

        if self._executor and not self._executor._shutdown:
            self._executor.shutdown(wait=True)
        self._executor = None
