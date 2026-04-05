"""
Unified Channel Discovery - Single source of truth for channel metadata.

Combines channel resolution and pre-flight discovery into one phase.
Checks database cache first, then falls back to yt-dlp discovery.

This replaces the separate FastChannelResolver + discover_channel pattern
with a single unified approach that eliminates redundant yt-dlp calls.
"""

import random
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TypedDict

import yt_dlp

from yt_fts.core.database import add_channel_info, get_db_connection, get_num_vids
from yt_fts.utils.dual_sink_logger import get_logger

from .url_utils import USER_AGENTS


class DiscoveryResult(TypedDict):
    """Result of unified channel discovery."""

    channel_id: str | None
    channel_name: str | None
    channel_url: str
    total_videos: int
    with_subs: int
    without_subs: int
    scheduled: int
    members_only: int
    unavailable: int
    source: str


logger = get_logger(__name__)


class YtdlpSilentLogger:
    """Silent logger for yt-dlp to suppress stderr spam (MODIFIED: Verbose for debug)."""

    def debug(self, msg):
        print(f"YTDLP DEBUG: {msg}")

    def warning(self, msg):
        print(f"YTDLP WARNING: {msg}")

    def error(self, msg):
        print(f"YTDLP ERROR: {msg}")


class TimeoutError(Exception):
    """Exception raised when timeout occurs."""


def with_timeout(func, timeout_seconds=60, _logger=None):
    """
    Execute a function with a timeout using ThreadPoolExecutor.

    Args:
        func: Function to execute
        timeout_seconds: Maximum time to wait in seconds
        _logger: Logger instance (internal, for late binding)

    Returns:
        The result of the function

    Raises:
        TimeoutError: If function doesn't complete within timeout
    """
    # Detect if we're already inside a ThreadPoolExecutor to avoid deadlock
    # ThreadPoolExecutor threads have names like "ThreadPoolExecutor-0_1"
    current_thread = threading.current_thread()
    in_thread_pool = current_thread.name.startswith("ThreadPoolExecutor")

    if in_thread_pool:
        # Skip nested ThreadPoolExecutor - rely on yt-dlp's socket_timeout
        if _logger:
            _logger.debug("[UNIFIED DISCOVERY] Skipping nested timeout wrapper")
        return func()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        if _logger:
            _logger.debug("[UNIFIED DISCOVERY] Timeout after %ss", timeout_seconds)
        msg = f"Operation timed out after {timeout_seconds} seconds"
        raise TimeoutError(msg)





class UnifiedChannelDiscovery:
    """
    Single source of truth for channel metadata.

    Replaces the pattern-based resolution + separate discovery approach
    with a unified method that:
    1. Checks database cache first (fastest path)
    2. Falls back to yt-dlp discovery (single call)
    3. Caches results for reuse

    This eliminates the 2-3 redundant yt-dlp calls per new channel
    that existed in the old architecture.
    """

    def __init__(self, cookies_from_browser: str | None = None):
        """
        Initialize the unified discovery system.

        Args:
            cookies_from_browser: Browser to extract cookies from
        """
        print(
            f"DEBUG: UnifiedChannelDiscovery.__init__ entry (cookies: {cookies_from_browser})"
        )
        self.cookies_from_browser = cookies_from_browser
        self._user_agents = USER_AGENTS
        self._cache: dict[str, DiscoveryResult] = {}

    def discover(self, input_str: str, force_refresh: bool = False) -> DiscoveryResult:
        """
        Discover channel metadata from any input format.

        This is the primary entry point. It handles:
        - @username handles
        - /c/custom URLs
        - /channel/UCxxx IDs
        - Full YouTube URLs

        Args:
            input_str: User input in any format
            force_refresh: Skip database cache, force yt-dlp call

        Returns:
            DiscoveryResult with channel metadata
        """
        print(f"\n\n[DEBUG] discover entry: {input_str}")
        if not force_refresh and input_str in self._cache:
            logger.debug("[UNIFIED DISCOVERY] Memory cache hit for: %s", input_str)
            return self._cache[input_str]
        if not force_refresh:
            db_result = self._get_from_database(input_str)
            if db_result:
                print(f"[DEBUG] Database hit: {db_result['channel_id']}")
                logger.debug(
                    "[UNIFIED DISCOVERY] Database cache hit for: %s", input_str
                )
                self._cache[input_str] = db_result
                return db_result
        print("[DEBUG] Cache miss, calling _discover_via_ytdlp")
        logger.debug("[UNIFIED DISCOVERY] Cache miss, discovering: %s", input_str)
        return self._discover_via_ytdlp(input_str, timeout_seconds=120)

    def _get_from_database(self, input_str: str) -> DiscoveryResult | None:
        """
        Check database for existing channel metadata.

        Args:
            input_str: User input in any format

        Returns:
            DiscoveryResult if found in database, None otherwise
        """
        print(f"DEBUG: UnifiedChannelDiscovery._get_from_database entry: {input_str}")
        try:
            patterns_to_try = [
                input_str,
                input_str.removesuffix("/videos"),
                input_str.rstrip("/"),
            ]
            if "@" in input_str:
                handle = input_str.split("@")[-1].split("/")[0]
                patterns_to_try.append(f"%@{handle}%")
            for pattern in patterns_to_try:
                try:
                    conn = get_db_connection(timeout=30.0)
                    cursor = conn.cursor()
                    row = cursor.execute(
                        "SELECT channel_id, channel_name FROM Channels WHERE channel_url = ? LIMIT 1",
                        (pattern,),
                    ).fetchone()
                    conn.close()
                    if row:
                        channel_id, channel_name = row
                        db_count = get_num_vids(channel_id)
                        if db_count > 0:
                            logger.debug(
                                "[UNIFIED DISCOVERY] Found %s videos in DB for %s",
                                db_count,
                                channel_id,
                            )
                            return DiscoveryResult(
                                channel_id=channel_id,
                                channel_name=channel_name,
                                channel_url=input_str,
                                total_videos=db_count,
                                with_subs=db_count,
                                without_subs=0,
                                scheduled=0,
                                members_only=0,
                                unavailable=0,
                                source="database",
                            )
                except Exception:
                    continue
        except Exception as e:
            logger.debug("[UNIFIED DISCOVERY] DB lookup error: %s", e)
        return None

    def _discover_via_ytdlp(
        self, input_str: str, timeout_seconds: int = 30
    ) -> DiscoveryResult:
        """
        Discover channel metadata using yt-dlp.

        This is the fallback when database cache misses.

        Args:
            input_str: User input in any format
            timeout_seconds: Maximum time to wait for yt-dlp (default 30s)

        Returns:
            DiscoveryResult with full metadata from yt-dlp
        """
        print(f"DEBUG: UnifiedChannelDiscovery._discover_via_ytdlp entry: {input_str}")
        discovery: DiscoveryResult = {
            "channel_id": None,
            "channel_name": None,
            "channel_url": input_str,
            "total_videos": 0,
            "with_subs": 0,
            "without_subs": 0,
            "scheduled": 0,
            "members_only": 0,
            "unavailable": 0,
            "source": "ytdlp",
        }
        ydl_opts = {
            "http_headers": {"User-Agent": random.choice(self._user_agents)},
            "quiet": True,
            "noprogress": True,
            "extract_flat": True,
            "listsubtitles": False,
            "socket_timeout": 30,
            "retries": 2,
            "no_warnings": True,
            "logger": YtdlpSilentLogger(),
        }
        if self.cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)

        def _extract_info():
            """Inner function to run with timeout."""
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(input_str, download=False)

        try:
            info = with_timeout(
                _extract_info, timeout_seconds=timeout_seconds, _logger=logger
            )
            if info:
                if "channel_id" in info:
                    discovery["channel_id"] = info["channel_id"]
                if "channel" in info and isinstance(info["channel"], str):
                    discovery["channel_name"] = info["channel"]
                elif "uploader" in info:
                    discovery["channel_name"] = info["uploader"]
                if "webpage_url" in info:
                    discovery["channel_url"] = info["webpage_url"]
                if "entry_count" in info:
                    discovery["total_videos"] = info["entry_count"]
                elif info.get("entries"):
                    discovery["total_videos"] = len([e for e in info["entries"] if e])
            self._cache[input_str] = discovery
            logger.debug(
                "[UNIFIED DISCOVERY] Complete: %s total, %s with subs, channel_id=%s",
                discovery["total_videos"],
                discovery["with_subs"],
                discovery.get("channel_id"),
            )
            self._ensure_channel_in_db(discovery, input_str)
        except TimeoutError:
            logger.warning(
                "[UNIFIED DISCOVERY] Timeout for %s (>%ss)", input_str, timeout_seconds
            )
            discovery["source"] = "none"
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"DEBUG RESOLVE ERROR: {e}")
            logger.debug("[UNIFIED DISCOVERY] Error for %s: %s", input_str, e)
            discovery["source"] = "none"
        return discovery

    def _is_valid_channel(self, discovery: DiscoveryResult) -> bool:
        """
        Validate that discovery contains a real, usable channel.

        Args:
            discovery: DiscoveryResult to validate

        Returns:
            True if channel_id is valid and channel exists
        """
        channel_id = discovery.get("channel_id")
        if not channel_id:
            return False
        if not isinstance(channel_id, str):
            return False
        if len(channel_id) < 10 or len(channel_id) > 100:
            return False
        return discovery.get("source") != "none"

    def _ensure_channel_in_db(self, discovery: DiscoveryResult, input_str: str) -> None:
        """
        Ensure discovered channel is in database.

        Adds valid channels to database during discovery phase,
        even if no videos are downloaded. This captures all
        channels from input files for later reference.

        Args:
            discovery: DiscoveryResult from yt-dlp
            input_str: Original input string for URL fallback
        """
        if not self._is_valid_channel(discovery):
            return
        channel_id = discovery["channel_id"]
        channel_name = discovery.get("channel_name") or channel_id
        channel_url = discovery.get("channel_url") or input_str
        try:
            add_channel_info(channel_id, channel_name, channel_url)
            logger.debug("[UNIFIED DISCOVERY] Added channel to DB: %s", channel_id)
        except Exception as e:
            logger.debug("[UNIFIED DISCOVERY] DB insert note: %s", e)

    def clear_cache(self) -> None:
        """Clear the in-memory discovery cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Return the number of cached discovery results."""
        return len(self._cache)
