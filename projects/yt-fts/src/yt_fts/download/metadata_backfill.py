from __future__ import annotations

"""
Metadata backfill module for batch downloader.

Extracted from batch_downloader.py to separate concerns.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class MetadataBackfill:
    """
    Handles metadata backfill operations for YouTube channels.

    Fetches missing or stale channel metadata using YouTube API and yt-dlp.
    """

    def __init__(
        self,
        console,
        display_plugin,
        suppress_verbose: bool = False,
        quota_strategy: Any = None,
    ) -> None:
        """
        Initialize MetadataBackfill.

        Args:
            console: Rich Console instance for output
            display_plugin: Display plugin for user messages
            suppress_verbose: Whether to suppress verbose output
            quota_strategy: Optional quota strategy for API usage decisions
        """
        self.console = console
        self.display_plugin = display_plugin
        self.suppress_verbose = suppress_verbose
        self.quota_strategy = quota_strategy

    def backfill_channel_metadata_if_needed(self, channel_id: str) -> str | None:
        """
        Backfill channel metadata using yt-api if subscriber_count is NULL or stale.

        This is called during batch-download when we detect a channel lacks metadata.
        Uses the API quota for faster metadata fetching (1 quota per channel).

        Checks for:
        - NULL subscriber_count_last_updated (never fetched)
        - OR subscriber_count_last_updated > 30 days ago (stale data)

        Args:
            channel_id: YouTube channel ID

        Returns:
            Subscriber count string (e.g., "1.5M", "50K") or None
        """
        from yt_fts.core.database import get_db_connection
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        # Ensure .env is loaded (may not be in all subprocess contexts)
        from yt_fts.utils.config import find_and_load_env

        find_and_load_env()

        # Check if API key is configured
        import os

        if not os.getenv("YOUTUBE_API_KEY"):
            return None

        # Check if backfill is needed (NULL or stale > 30 days)
        needs_backfill = False
        try:
            conn = get_db_connection(timeout=5.0)
            try:
                row = conn.execute(
                    "SELECT subscriber_count_last_updated FROM Channels WHERE channel_id = ?",
                    (channel_id,),
                ).fetchone()
            finally:
                conn.close()

            if row is None or row[0] is None:
                # Never fetched
                needs_backfill = True
            else:
                # Check if stale (> 30 days old)
                try:
                    last_updated = datetime.fromisoformat(row[0])
                    if datetime.now() - last_updated > timedelta(days=30):
                        needs_backfill = True
                except (ValueError, TypeError):
                    # Invalid timestamp, treat as needs backfill
                    needs_backfill = True
        except Exception as e:
            logger.debug(
                "Failed to check subscriber_count_last_updated for %s: %s",
                channel_id[:20],
                e,
            )
            # On error, assume backfill needed
            needs_backfill = True

        if not needs_backfill:
            return None

        # Check quota before proceeding
        api_backfill = YouTubeAPIBackfill(show_progress=False)
        quota_info = api_backfill.get_global_quota_info()
        if quota_info["remaining"] <= 10:
            return None

        try:
            result = api_backfill.backfill_channel_metadata(channel_id)
            if result.get("updated"):
                sub_count = result.get("subscriber_count", 0)
                if sub_count:
                    if sub_count >= 1000000:
                        sub_str = f"{sub_count / 1000000:.1f}M"
                    elif sub_count >= 1000:
                        sub_str = f"{sub_count / 1000:.0f}K"
                    else:
                        sub_str = f"{sub_count}"
                    # Return subscriber count for display after header
                    # Don't print here to avoid message appearing before channel header
                    return sub_str
        except Exception as e:
            logger.debug(
                "Failed to backfill channel metadata for %s: %s", channel_id[:20], e
            )

        return None

    def backfill_playlist_count_if_needed(self, channel_id: str) -> None:
        """
        Backfill playlist_count using yt-dlp if NULL.

        YouTube API does NOT provide playlist_count, so we use yt-dlp
        to scrape the channel playlists page. This is slower but necessary
        for complete metadata collection.

        Args:
            channel_id: YouTube channel ID
        """
        from yt_fts.core.database import get_db_connection
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        # Check if playlist_count is NULL
        try:
            conn = get_db_connection(timeout=5.0)
            row = conn.execute(
                "SELECT playlist_count FROM Channels WHERE channel_id = ?",
                (channel_id,),
            ).fetchone()
            conn.close()

            if row and row[0] is not None:
                return  # Already has playlist_count
        except (sqlite3.OperationalError, sqlite3.DatabaseError, TimeoutError) as e:
            logger.debug(
                "Failed to check playlist_count for %s: %s", channel_id[:20], e
            )
            return

        # Backfill playlist_count using yt-dlp
        try:
            from rich.status import Status

            api_backfill = YouTubeAPIBackfill(show_progress=False)
            result = {}

            with Status(
                "   ⎿ yt-dlp: Fetching playlist metadata...",
                console=self.console,
                spinner="dots"
            ) as status:
                result = api_backfill.backfill_playlist_count_ytdlp(channel_id)
                if result.get("updated"):
                    playlist_count = result.get("playlist_count", 0)
                    status.update(f"   ⎿ yt-dlp: Found {playlist_count} playlists")

            if result.get("updated") and not self.suppress_verbose:
                self.console.print(
                    f"   ⎿ [dim]metadata: {result.get('playlist_count', 0)} playlists (via yt-dlp)[/dim]"
                )
        except Exception as e:
            logger.debug(
                "Failed to backfill playlist_count for %s: %s", channel_id[:20], e
            )

    def should_use_api_for_metadata(self, db_count: int) -> bool:
        """
        Determine if API should be used for metadata fetching.

        Args:
            db_count: Current database video count

        Returns:
            bool: True if API should be used, False otherwise
        """
        use_api = True
        if self.quota_strategy:
            # quota_strategy.should_use_api_for_metadata returns tuple[bool, str]
            use_api, reason = self.quota_strategy.should_use_api_for_metadata(
                db_count=db_count,
                context="new_channel" if db_count == 0 else "gap_fill"
            )
            if not use_api and not self.suppress_verbose:
                self.display_plugin.info(
                    f"💰 Quota conservation: {reason}"
                )
        return use_api
