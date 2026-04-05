"""
Channel caching utilities for batch download operations.

Provides database-backed caching of resolved channels to avoid
redundant resolution on every run.
"""

import re
import sqlite3
import threading
from urllib.parse import quote

# Shared counters for aggregated cache status across parallel workers
_cache_stats_lock = threading.Lock()
_cache_stats = {
    "cached": 0,
    "new": 0,
    "skipped_empty": 0,
    "reported": False,
}


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

    Args:
        channels: List of channel inputs (URLs, handles, or IDs)
        conn: Database connection

    Returns:
        Tuple of (cached_channels dict, channels_to_resolve list)
        cached_channels: {input: resolved_url} mapping
        channels_to_resolve: List of inputs that need resolution
    """
    cached_channels = {}
    channels_to_resolve = []
    skipped_empty = 0

    # Get all existing channels from database, including channel_id for matching
    existing_channels = conn.execute(
        "SELECT channel_id, channel_url, channel_name FROM Channels"
    ).fetchall()

    # Create lookup structures for fast, accurate matching
    existing_urls = set()
    handle_to_url = {}
    id_to_url = {}

    for channel_id, channel_url, _channel_name in existing_channels:
        # Store URL variations for exact matching
        existing_urls.add(channel_url)
        # Use removesuffix instead of rstrip to remove /videos as a suffix, not characters
        url_without_videos = channel_url.removesuffix("/videos")
        existing_urls.add(url_without_videos)
        existing_urls.add(channel_url.rstrip("/"))

        # Map by database channel_id (most reliable - handles URL → handle mappings)
        if channel_id:
            id_to_url[channel_id] = channel_url

        # Extract and map handle if present
        if "@" in channel_url:
            handle = channel_url.split("@")[-1].split("/")[0]
            handle_lower = handle.lower()
            handle_to_url[f"@{handle_lower}"] = channel_url
            handle_to_url[handle_lower] = channel_url

        # Also extract channel ID from URL (for entries where channel_id might be missing)
        if "/channel/" in channel_url:
            url_channel_id = channel_url.split("/channel/")[1].split("/")[0]
            if url_channel_id not in id_to_url:  # Don't override if already set from DB
                id_to_url[url_channel_id] = channel_url

    # Check each input channel against cached data
    for channel_input in channels:
        # Normalize input for comparison
        normalized = channel_input.strip().rstrip("/")

        # Skip empty entries
        if not normalized:
            skipped_empty += 1
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
            if base_url in existing_urls:
                cached_channels[channel_input] = _normalize_channel_url(base_url)
            else:
                cached_channels[channel_input] = _normalize_channel_url(input_url)
            is_cached = True

        # 2. Handle match (direct lookup)
        elif input_handle:
            handle_key = input_handle.lower()
            if handle_key in handle_to_url:
                cached_channels[channel_input] = _normalize_channel_url(handle_to_url[handle_key])
                is_cached = True

        # 3. Channel ID match (direct lookup)
        elif input_id and input_id in id_to_url:
            cached_channels[channel_input] = _normalize_channel_url(id_to_url[input_id])
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
        Number of channels successfully cached
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

    Args:
        console: Rich console instance
        cached_count: Number of channels found in cache
        resolve_count: Number of channels needing resolution
        skipped_empty: Number of empty entries skipped
    """
    global _cache_stats, _cache_stats_lock

    with _cache_stats_lock:
        _cache_stats["cached"] += cached_count
        _cache_stats["new"] += resolve_count
        _cache_stats["skipped_empty"] += skipped_empty


def print_aggregated_cache_status(console) -> None:
    """
    Print the aggregated cache status summary (call once at end).

    Args:
        console: Rich console instance
    """
    global _cache_stats, _cache_stats_lock, _cache_stats

    with _cache_stats_lock:
        if _cache_stats["reported"]:
            return
        _cache_stats["reported"] = True

        cached = _cache_stats["cached"]
        new = _cache_stats["new"]
        skipped = _cache_stats["skipped_empty"]
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
