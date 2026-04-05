"""
Channel caching utilities for batch download operations.

Provides database-backed caching of resolved channels to avoid
redundant resolution on every run.
"""
from __future__ import annotations

import re
import sqlite3
import threading
from collections import Counter
from urllib.parse import quote

# Shared counters for aggregated cache status across parallel workers
# Counter provides thread-safe increments via its update() method
# Use RLock for reentrancy (tests may acquire lock, then call __setitem__)
_cache_stats_lock = threading.RLock()
_cache_stats_counter = Counter()  # Thread-safe counter for stats
_reported_lock = threading.RLock()  # Separate lock for "reported" flag


def _normalize_channel_url(url: str) -> str:
    """
    Normalize a channel URL by URL-encoding the handle portion.

    This fixes issues with pipe characters and other special characters
    in YouTube handles that were stored unencoded in the cache.

    Args:
        url: The channel URL to normalize

    Returns:
        Normalized URL with encoded handle portion
    """
    if "/@" in url:
        # Extract handle, encode it, and reconstruct URL
        parts = url.split("/@")
        base = parts[0] + "/@"
        rest = parts[1] if len(parts) > 1 else ""
        handle_part = rest.split("/")[0] if "/" in rest else rest
        path_after = rest.split("/")[1] if "/" in rest and len(rest.split("/")) > 1 else ""
        # Reconstruct with encoded handle
        if path_after:
            return f"{base}{quote(handle_part, safe='')}/{path_after}"
        return f"{base}{quote(handle_part, safe='')}"
    return url


def get_cached_channels(
    channels: list[str],
    conn: sqlite3.Connection,
) -> tuple[dict, list]:
    """
    Check database for already-resolved channels to avoid redundant resolution.

    OPTIMIZED: Uses targeted WHERE IN queries instead of full table scan.
    Only fetches channels that match the input list, not all channels in DB.

    Args:
        channels: List of channel inputs (URLs, handles, or IDs)
        conn: Database connection

    Returns:
        Tuple of (cached_channels dict, channels_to_resolve list)
        cached_channels: {input: (channel_id, resolved_url)} tuple mapping
        channels_to_resolve: List of inputs that need resolution
    """
    import logging
    logger = logging.getLogger(__name__)

    cached_channels = {}
    channels_to_resolve = []
    skipped_empty = 0
    skipped_invalid = 0

    # Phase 0: Skip channels marked as invalid (is_valid=0)
    # This prevents wasting time on channels that previously 404'd/400'd
    try:
        column_exists = conn.execute("""
            SELECT COUNT(*) FROM pragma_table_info('Channels') WHERE name='is_valid'
        """).fetchone()

        if column_exists and column_exists[0] > 0:
            # Extract potential IDs and handles from input for filtering
            potential_ids = set()
            potential_handles = set()

            for channel_input in channels:
                normalized = channel_input.strip().rstrip("/")
                if not normalized:
                    continue
                if normalized.startswith("http"):
                    if "/channel/" in normalized:
                        cid = normalized.split("/channel/")[1].split("/")[0]
                        potential_ids.add(cid)
                    elif "/@" in normalized:
                        handle = normalized.split("@")[1].split("/")[0]
                        potential_handles.add(handle.lower())
                elif normalized.startswith("@"):
                    handle = normalized[1:]
                    potential_handles.add(handle.lower())
                elif re.match(r"^UC[a-zA-Z0-9_-]{22}$", normalized):
                    potential_ids.add(normalized)

            # Query for invalid channels
            invalid_ids = set()
            if potential_ids:
                placeholders = ",".join(["?"] * len(potential_ids))
                invalid_query = f"SELECT channel_id FROM Channels WHERE channel_id IN ({placeholders}) AND is_valid = 0"
                invalid_ids.update(row[0] for row in conn.execute(invalid_query, list(potential_ids)).fetchall())

            # Filter out invalid channels
            valid_channels = []
            for ch in channels:
                normalized = ch.strip().rstrip("/")
                is_invalid = False

                # Check if this channel is marked invalid
                if normalized in potential_ids:
                    # ID match
                    if normalized in invalid_ids:
                        is_invalid = True
                elif "@" in normalized:
                    # For handle inputs, we need to check if the resolved channel is invalid
                    # Query Channels table to find channels with this handle that are marked invalid
                    handle = normalized[1:] if normalized.startswith("@") else normalized.split("@")[-1].split("/")[0]
                    handle_check = conn.execute(
                        "SELECT channel_id FROM Channels WHERE channel_url LIKE ? AND is_valid = 0",
                        (f"%@{handle}%",)
                    ).fetchone()
                    if handle_check:
                        is_invalid = True

                if is_invalid:
                    skipped_invalid += 1
                    logger.debug(f"Skipping invalid channel: {ch}")
                else:
                    valid_channels.append(ch)

            if skipped_invalid > 0:
                logger.info(f"Skipped {skipped_invalid} channels marked as invalid")

            channels = valid_channels
    except Exception as e:
        logger.debug(f"Could not filter invalid channels: {e}")

    # Phase 1: Extract potential IDs and handles from input channels
    # This allows us to query ONLY matching channels, not the entire DB
    potential_ids = set()
    potential_handles = set()
    input_urls_to_check = set()

    for channel_input in channels:
        normalized = channel_input.strip().rstrip("/")
        if not normalized:
            skipped_empty += 1
            continue

        if normalized.startswith("http"):
            input_urls_to_check.add(normalized)
            # Extract components from URL
            if "/channel/" in normalized:
                cid = normalized.split("/channel/")[1].split("/")[0]
                potential_ids.add(cid)
            elif "/@" in normalized:
                handle = normalized.split("@")[1].split("/")[0]
                potential_handles.add(handle.lower())
        elif normalized.startswith("@"):
            handle = normalized[1:]  # Remove @
            potential_handles.add(handle.lower())
        elif re.match(r"^UC[a-zA-Z0-9_-]{22}$", normalized):
            potential_ids.add(normalized)

    # Phase 2: Query ONLY matching channels using WHERE IN
    # This is the key optimization - O(input_size) instead of O(db_size)
    existing_channels = []

    if potential_ids:
        placeholders = ",".join(["?"] * len(potential_ids))
        query = f"SELECT channel_id, channel_url, channel_name FROM Channels WHERE channel_id IN ({placeholders})"
        existing_channels.extend(conn.execute(query, list(potential_ids)).fetchall())

    if potential_handles:
        # For handles, we need to match against channel_url containing the handle
        for handle in potential_handles:
            existing_channels.extend(conn.execute(
                "SELECT channel_id, channel_url, channel_name FROM Channels WHERE channel_url LIKE ?",
                (f"%@{handle}%",)
            ).fetchall())

    # Also check exact URLs from input
    for url in input_urls_to_check:
        # Remove /videos suffix for matching
        url_to_check = url.removesuffix("/videos").rstrip("/")
        existing_channels.extend(conn.execute(
            "SELECT channel_id, channel_url, channel_name FROM Channels WHERE channel_url = ? OR channel_url = ?",
            (url, url_to_check)
        ).fetchall())

    # Phase 3: Build lookup structures from the smaller result set
    existing_urls = set()
    handle_to_url = {}
    id_to_url = {}
    url_to_channel_id = {}  # NEW: Map URL to channel_id for canonical lookups

    for channel_id, channel_url, _channel_name in existing_channels:
        # Store URL variations for exact matching
        existing_urls.add(channel_url)
        url_without_videos = channel_url.removesuffix("/videos")
        existing_urls.add(url_without_videos)
        existing_urls.add(channel_url.rstrip("/"))

        # Map by database channel_id
        if channel_id:
            id_to_url[channel_id] = channel_url

        # NEW: Map URLs to their channel_id
        url_to_channel_id[channel_url] = channel_id
        url_to_channel_id[url_without_videos] = channel_id
        url_to_channel_id[channel_url.rstrip("/")] = channel_id

        # Extract and map handle if present
        if "@" in channel_url:
            handle = channel_url.split("@")[-1].split("/")[0]
            handle_lower = handle.lower()
            handle_to_url[f"@{handle_lower}"] = channel_url
            handle_to_url[handle_lower] = channel_url

        # Extract channel ID from URL
        if "/channel/" in channel_url:
            url_channel_id = channel_url.split("/channel/")[1].split("/")[0]
            if url_channel_id not in id_to_url:
                id_to_url[url_channel_id] = channel_url

    # Phase 4: Check each input channel against cached data
    for channel_input in channels:
        normalized = channel_input.strip().rstrip("/")

        if not normalized:
            continue

        input_url = normalized if normalized.startswith("http") else None
        input_handle = None
        input_id = None

        # Extract components from input
        if input_url:
            if "@" in input_url:
                input_handle = "@" + input_url.split("@")[-1].split("/")[0]
            elif "/channel/" in input_url:
                input_id = input_url.split("/channel/")[1].split("/")[0]
        elif normalized.startswith("@"):
            input_handle = normalized
        elif re.match(r"^UC[a-zA-Z0-9_-]{22}$", normalized):
            input_id = normalized

        # Check against cache with direct lookups
        is_cached = False

        # 1. Exact URL match
        if input_url and input_url in existing_urls:
            base_url = input_url.removesuffix("/videos")
            normalized_url = base_url if base_url in existing_urls else input_url
            # Look up channel_id for this URL
            matched_channel_id = url_to_channel_id.get(normalized_url) or url_to_channel_id.get(_normalize_channel_url(normalized_url))
            cached_channels[channel_input] = (matched_channel_id, _normalize_channel_url(normalized_url))
            is_cached = True

        # 2. Handle match (direct lookup)
        elif input_handle:
            handle_key = input_handle.lower()
            if handle_key in handle_to_url:
                matched_url = handle_to_url[handle_key]
                matched_channel_id = url_to_channel_id.get(matched_url)
                cached_channels[channel_input] = (matched_channel_id, _normalize_channel_url(matched_url))
                is_cached = True

        # 3. Channel ID match (direct lookup)
        elif input_id and input_id in id_to_url:
            cached_channels[channel_input] = (input_id, _normalize_channel_url(id_to_url[input_id]))
            is_cached = True

        if not is_cached:
            channels_to_resolve.append(channel_input)

    return cached_channels, channels_to_resolve


def save_resolved_channels(
    newly_resolved: dict,
    console=None,
) -> int:
    """
    Save newly resolved channels to database for future caching.

    Args:
        newly_resolved: {original_input: resolved_url} mapping
        console: Optional Rich console for progress messages

    Returns:
        Number of channels actually inserted as NEW (duplicates filtered out).
        This is the accurate count of truly new channels, not just resolution attempts.
    """
    from yt_fts.core.database import add_channel_info_batch

    if not newly_resolved:
        return 0

    # Prepare batch data: (channel_id, channel_name, channel_url)
    channels_to_insert = []
    for _original_input, resolved_url in newly_resolved.items():
        # Extract channel ID or handle for caching
        channel_id = None

        if "/channel/" in resolved_url:
            # Extract channel ID from /channel/ URLs
            channel_id = resolved_url.split("/channel/")[1].split("/")[0]
        elif "/@" in resolved_url:
            # Extract handle from /@/ URLs for caching
            handle = resolved_url.split("/@")[1].split("/")[0]
            channel_id = f"@{handle}"  # Use handle as channel_id for caching
        else:
            # For custom URLs or other formats, use the URL itself as the identifier
            # This ensures we cache the channel even if we can't extract a clean ID
            # Remove protocol and trailing slashes for a cleaner key
            clean_url = resolved_url.replace("https://", "").replace("http://", "").rstrip("/")
            channel_id = f"url:{clean_url}"  # Prefix with "url:" to avoid collisions

        # Skip if we couldn't extract a usable identifier
        if not channel_id:
            continue

        channels_to_insert.append((
            channel_id,
            channel_id,  # placeholder: will be updated with real name during discovery
            resolved_url
        ))

    # Batch insert in chunks with progress
    if channels_to_insert:
        try:
            total = len(channels_to_insert)
            chunk_size = 100
            total_inserted = 0

            # Process in chunks
            for i in range(0, total, chunk_size):
                chunk = channels_to_insert[i:i + chunk_size]
                inserted = add_channel_info_batch(chunk)
                total_inserted += inserted

                # Show progress
                if console:
                    if i + chunk_size >= total:
                        console.print(f"[dim]✓ Cached {total_inserted}/{total} new channels[/dim]")
                    else:
                        console.print(
                            f"[dim]Caching {min(i + chunk_size, total)}/{total} channels...[/dim]",
                            end="\r"
                        )

            return total_inserted

        except Exception as e:
            # Batch insert failed, just skip caching this time
            if console:
                console.print(f"[dim]Cache skip: {str(e)[:50]}[/dim]")
            return 0

    return 0


def report_cache_status(
    console,
    cached_count: int,
    resolve_count: int,
    skipped_empty: int = 0,
) -> None:
    """
    Aggregate cache stats across parallel workers (thread-safe).
    Prints aggregated summary only once at the end.

    Uses Counter for thread-safe increments.

    Args:
        console: Rich console instance
        cached_count: Number of channels found in cache
        resolve_count: Number of channels needing resolution (NOT added to "new" counter)
        skipped_empty: Number of empty entries skipped

    Note:
        The "new" counter is only updated when channels are actually inserted
        into the database (in save_resolved_channels), not when they just
        need resolution. This prevents counting duplicate channels or existing
        channels with URL variations as "new".
    """
    global _cache_stats_counter, _cache_stats_lock

    # Counter.update() is thread-safe for increments
    # NOTE: We do NOT add resolve_count to "new" here because:
    # - resolve_count = channels needing resolution (may include existing channels with URL variations)
    # - "new" should only count actual database insertions (tracked later in save_resolved_channels)
    with _cache_stats_lock:
        _cache_stats_counter.update({
            "cached": cached_count,
            "skipped_empty": skipped_empty,
        })


def print_aggregated_cache_status(console) -> None:
    """
    Print the aggregated cache status summary (call once at end).

    Thread-safe: All stats reads and "reported" flag check/set happen
    atomically within the same lock.

    Args:
        console: Rich console instance
    """
    global _cache_stats_counter, _reported_lock

    # Check and set "reported" flag atomically, then read stats
    # This prevents race between reporting threads and printing thread
    with _reported_lock:
        # Use a function attribute to prevent duplicate prints
        if not hasattr(print_aggregated_cache_status, "_reported"):
            print_aggregated_cache_status._reported = False

        if print_aggregated_cache_status._reported:
            return
        print_aggregated_cache_status._reported = True

    # Read stats after flag is set (outside reported lock to allow concurrent reports)
    with _cache_stats_lock:
        cached = _cache_stats_counter.get("cached", 0)
        new = _cache_stats_counter.get("new", 0)
        skipped = _cache_stats_counter.get("skipped_empty", 0)
        total = cached + new

    if skipped > 0:
        console.print(f"[dim]Skipped {skipped} empty line(s)[/dim]")

    if cached > 0 or new > 0:
        if cached > 0:
            console.print(
                f"[cyan]✓ {cached} cached, + {new} new → {total} channels[/cyan]"
            )
        else:
            console.print(
                f"[cyan]🔍 Resolving {total} channel(s)...[/cyan]"
            )


# Backwards compatibility: provide mutable dict wrapper for tests
# Tests import _cache_stats and modify it directly in setup_method
class _CacheStatsDict(dict):
    """Mutable dict wrapper that syncs with thread-safe Counter."""

    def __getitem__(self, key):
        if key == "reported":
            return getattr(print_aggregated_cache_status, "_reported", False)
        with _cache_stats_lock:
            return _cache_stats_counter.get(key, 0)

    def __setitem__(self, key, value):
        if key == "reported":
            with _reported_lock:
                setattr(print_aggregated_cache_status, "_reported", value)
        else:
            with _cache_stats_lock:
                _cache_stats_counter[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


# Module-level mutable dict for backwards compatibility with tests
_cache_stats = _CacheStatsDict()
