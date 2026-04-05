"""
Channel Resolution Service.

Handles URL → channel ID conversion and resolution logic.
Extracted from batch_downloader.py to reduce complexity and improve
maintainability.
"""
from __future__ import annotations

from yt_fts.download.output_utils import StderrCapture
from yt_fts.utils.dual_sink_logger import get_logger

logger = get_logger(__name__)


class ChannelResolutionService:
    """
    Service for resolving YouTube channel URLs to channel IDs.

    Handles various URL formats: @handles, /channel/UCxxx, /c/custom, etc.
    Provides caching and fallback mechanisms.
    """

    def __init__(self, cookies_from_browser: str | None = None):
        self.cookies_from_browser = cookies_from_browser

    def resolve_channel_url(self, url: str) -> tuple[str | None, str]:
        """
        Resolve a YouTube channel URL to its canonical form and extract channel ID.

        Args:
            url: YouTube channel URL or handle

        Returns:
            tuple: (channel_id, resolved_url)
        """
        from yt_fts.db.channels import (
            get_channel_id_by_handle_substring,
            get_channel_id_by_url_exact,
        )

        # Try exact URL match first
        channel_id = get_channel_id_by_url_exact(url)
        if channel_id:
            return channel_id, url

        # Try URL without /videos suffix
        url_clean = url.rstrip("/").removesuffix("/videos")
        if url_clean != url:
            channel_id = get_channel_id_by_url_exact(url_clean)
            if channel_id:
                return channel_id, url_clean

        # Handle @handle URLs
        if "@" in url:
            handle = url.split("@")[-1].split("/")[0]
            channel_id = get_channel_id_by_handle_substring(handle)
            if channel_id:
                return channel_id, url

        # Fallback: yt-dlp resolution
        channel_id = self._resolve_via_ytdlp(url)
        return channel_id, url

    def _resolve_via_ytdlp(self, url: str) -> str | None:
        """
        Use yt-dlp to resolve channel URL to channel ID.

        Args:
            url: YouTube channel URL

        Returns:
            Channel ID if found, None otherwise
        """
        try:
            import yt_dlp

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "extract_flat": True,
                "extractor_args": {"youtubetab": ["skip=authcheck", "skip=webpage"]},
            }
            with StderrCapture() as _capture:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                resolved_channel_id = info.get("channel_id") or info.get("uploader_id")

                if resolved_channel_id and resolved_channel_id.startswith("UC"):
                    # Check if this ID exists in DB
                    from yt_fts.db.channels import get_channel_id_from_input

                    return get_channel_id_from_input(resolved_channel_id)
        except Exception as e:
            logger.debug(f"yt-dlp resolution failed for {url}: {e}")

        return None

    def get_channel_display_name(
        self, channel_id: str | None, fallback_name: str
    ) -> str:
        """
        Get human-readable channel name from database with progressive fallback.

        Args:
            channel_id: YouTube channel ID
            fallback_name: Fallback display name

        Returns:
            Human-readable channel name with warning indicators if needed
        """
        if not channel_id:
            return fallback_name

        try:
            from yt_fts.db.channels import get_channel_name_from_db

            name = get_channel_name_from_db(channel_id)
            if name and not self._is_raw_channel_id(name):
                return name  # Real cached name, no warning needed
        except Exception as e:
            logger.debug(f"Failed to get channel name from DB: {e}")

        # Progressive fallback with warnings
        return self._get_progressive_display_name(channel_id, fallback_name)

    def _is_raw_channel_id(self, name: str) -> bool:
        """Check if a name is a raw channel ID rather than a human-readable name."""
        return (
            name.startswith("Channel UC")
            or (name.startswith("UC") and len(name) >= 20)
            or name == "__INVALID_CHANNEL__"
        )

    def _get_progressive_display_name(self, channel_id: str, fallback_name: str) -> str:
        """
        Get channel display name with progressive fallback and warning indicators.

        Follows the pattern:
        1. @handle if available
        2. Truncated channel_id with warning
        3. Original fallback
        """
        warning = "⚠️ "

        # 1. If fallback is already @handle format
        if fallback_name.startswith("@"):
            return f"{warning}{fallback_name}"

        # 2. Extract @handle from URL
        if "youtube.com/@" in fallback_name:
            handle_part = fallback_name.split("youtube.com/@")[-1].split("/")[0]
            return f"{warning}@{handle_part}"

        # 3. If fallback is 'channel/UC...', truncate the channel_id
        if fallback_name.startswith("channel/"):
            id_part = fallback_name.split("/")[-1] if len(fallback_name.split("/")[-1]) > len(str(channel_id or "")) else (channel_id or "")
            truncated = id_part[:12] if len(id_part) > 12 else id_part
            return f"{warning}{truncated}..."

        # 4. If fallback is a raw channel_id, truncate it
        if fallback_name.startswith("UC") and len(fallback_name) > 12:
            return f"{warning}{fallback_name[:12]}..."

        # 5. Default: return fallback with warning
        return f"{warning}{fallback_name}"

    def ensure_channel_name_in_db(self, channel_id: str | None) -> str | None:
        """
        Quick check for cached channel name - NO API calls, NO blocking.

        Lazy loading: This only checks if name is already cached.
        If no cached name exists, returns immediately without blocking.

        Args:
            channel_id: YouTube channel ID (may be None)

        Returns:
            The channel_id unchanged (no API discovery here)
        """
        if not channel_id:
            return channel_id

        # Quick check if name already exists in database - NO API call
        from yt_fts.db.channels import get_channel_name_from_db

        existing_name = get_channel_name_from_db(channel_id)
        if existing_name and not self._is_raw_channel_id(existing_name):
            logger.debug(
                f"ensure_channel_name_in_db: cached name '{existing_name}' for {channel_id}"
            )
        else:
            logger.debug(
                f"ensure_channel_name_in_db: no cached name for {channel_id}, will lazy load"
            )

        # Return channel_id unchanged - no blocking API call
        return channel_id
