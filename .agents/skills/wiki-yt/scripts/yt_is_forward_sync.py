#!/usr/bin/env python3
"""Forward-sync provider: check yt-is cache before calling NotebookLM.

Before wiki-yt calls `nlm source content` for a YouTube source, this
provider checks yt-is `transcript_cache` for a matching video_id via the
title bridge. If found, reads from cache (skips NLM fetch). If not found,
returns empty — the caller falls through to NotebookLM as before.

Design contract:
  - NEVER raises (fail-through to NLM on any error)
  - Returns (transcript_body, video_id) on cache hit
  - Returns ("", "") on cache miss or any error
  - Builds the title bridge once per notebook (caller manages lifecycle)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add yt-is package root to sys.path for csf.cache import
_YT_IS_ROOT = Path("P:/packages/yt-is")
if str(_YT_IS_ROOT) not in sys.path:
    sys.path.insert(0, str(_YT_IS_ROOT))

# Add yt-is scripts dir for title_bridge import
_YT_IS_SCRIPTS = _YT_IS_ROOT / "scripts"
if str(_YT_IS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_YT_IS_SCRIPTS))


def fetch_from_yt_is_cache(
    source: dict,
    bridge: dict[str, list[str]],
) -> tuple[str, str]:
    """Check yt-is cache for a transcript matching this source.

    Args:
        source: NotebookLM source dict with 'title' field
        bridge: title->video_id bridge (from title_bridge.build_title_bridge())

    Returns:
        (transcript_body, video_id) on cache hit
        ("", "") on cache miss or any error (fail-through to NLM)
    """
    try:
        from title_bridge import normalize_title, match_title
        from csf.cache import get_cached_transcript_by_video_id

        title = source.get("title", "")
        if not title:
            return "", ""

        vid, match_type = match_title(title, bridge)
        if vid is None:
            return "", ""

        cached = get_cached_transcript_by_video_id(vid)
        if cached is None:
            return "", ""

        return cached.transcript, vid

    except Exception:
        # NEVER raise — fail-through to NLM on any error
        return "", ""


def build_bridge_once() -> dict[str, list[str]]:
    """Build the title bridge once (caller caches the result).

    Returns the merged clusters.json + analysis_status bridge.
    """
    try:
        from title_bridge import build_title_bridge
        return build_title_bridge()
    except Exception:
        return {}


def _resolve_video_id(source: dict, bridge: dict[str, list[str]]) -> str:
    """Resolve a YouTube video_id from a source dict using the title bridge.

    Used by feed-forward (export_transcripts.py) to determine which video_id
    to cache the transcript under. Returns empty string on failure.

    Args:
        source: NotebookLM source dict with 'title' field
        bridge: title->video_id bridge

    Returns:
        video_id string (11 chars) or "" if unresolvable
    """
    try:
        from title_bridge import match_title
        title = source.get("title", "")
        if not title:
            return ""
        vid, _ = match_title(title, bridge)
        return vid or ""
    except Exception:
        return ""
