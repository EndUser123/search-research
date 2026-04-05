"""
Batch filtering operations for efficient channel processing.
"""
from __future__ import annotations

import sys
from datetime import datetime

from yt_fts.db.channels import get_batch_channel_ids_from_urls, get_fresh_channels


def _log(tag: str, msg: str) -> None:
    """Write timestamped log message to stderr."""
    ts = datetime.now().strftime("%H:%M:%S")
    sys.stderr.write(f"[{ts}] [{tag}] {msg}" + chr(10))
    sys.stderr.flush()


def pre_filter_fresh_channels(
    channels: list[str],
    freshness_hours: int,
    min_saved: int | None,
    resolve_func=None,
) -> tuple[list[str], int]:
    """
    Pre-filter channels that were recently checked.

    This is a BATCH operation that avoids individual database queries
    per channel. Instead, it resolves all channels to channel_ids and
    does a single database query to find fresh ones.

    Args:
        channels: List of channel URLs/handles
        freshness_hours: Freshness threshold in hours
        min_saved: If 0 (metadata mode), enable freshness skipping
        resolve_func: Optional legacy resolver (kept for compatibility)

    Returns:
        Tuple of (channels_to_process, skipped_count)
    """
    if freshness_hours <= 0 or min_saved != 0:
        return channels, 0

    _log("FILTER", "Resolving channel IDs for batch freshness check...")
    sys.stderr.flush()

    # STEP 1: Batch lookup in Channels table (fastest - covers all URL formats)
    url_to_id = get_batch_channel_ids_from_urls(channels)

    # Mark completion
    _log("FILTER", "done")
    sys.stderr.flush()

    # STEP 2: Build resolution map and track unresolved channels
    channel_id_map = {}
    unresolved = []

    for channel in channels:
        # Check if already resolved from DB lookup
        if url_to_id.get(channel):
            channel_id_map[channel] = url_to_id[channel]
            continue

        # Try simple parsing for /channel/ URLs (no API call needed)
        if "/channel/" in channel:
            try:
                cid = channel.split("/channel/")[-1].split("/")[0]
                if cid.startswith("UC"):
                    channel_id_map[channel] = cid
                    continue
            except (ValueError, IndexError, AttributeError):
                pass

        # Channel not resolved - mark for processing
        unresolved.append(channel)

    # Get all resolved channel IDs
    resolved_ids = list(channel_id_map.values())

    if not resolved_ids and unresolved:
        # Nothing to filter - return all channels
        return channels, 0

    # BATCH QUERY: Get all fresh channels at once
    fresh_ids = (
        get_fresh_channels(resolved_ids, freshness_hours) if resolved_ids else set()
    )

    # Build result: fresh channels skipped, others processed
    channels_to_process = []
    skipped_count = 0

    # Process resolved channels
    for channel, cid in channel_id_map.items():
        if cid in fresh_ids:
            skipped_count += 1
        else:
            channels_to_process.append(channel)

    # Add unresolved channels (no freshness check possible)
    channels_to_process.extend(unresolved)

    # Always show summary
    n_to_process = len(channels_to_process)
    if skipped_count > 0:
        _log(
            "FILTER",
            f"Skipped {skipped_count} recently-checked channels (processing {n_to_process})",
        )
    else:
        _log(
            "FILTER", f"Processing all {n_to_process} channels (none recently checked)"
        )

    return channels_to_process, skipped_count
