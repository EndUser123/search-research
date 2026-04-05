"""
Channel Identifier Resolver

Resolves various YouTube channel identifier formats to canonical channel IDs.
Supports @handles, channel IDs, custom URLs, and video URLs.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from rich.console import Console

try:
    import yt_dlp

    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

    from yt_fts.db.channels import get_channel_id_from_name, get_channel_id_from_rowid

from .channel_file_updater import ChannelFileUpdater


@dataclass
class ResolutionResult:
    """Result of channel identifier resolution."""

    success: bool
    channel_id: str | None = None
    channel_url: str | None = None
    channel_name: str | None = None
    resolution_method: str = ""
    error_message: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """
        Initialize metadata dict if None (dataclass post-processor).
        """
        if self.metadata is None:
            self.metadata = {}


class ResolutionStrategy(ABC):
    """Abstract base class for channel resolution strategies."""

    @abstractmethod
    def can_resolve(self, input_value: str) -> bool:
        """Check if this strategy can resolve the given input."""

    @abstractmethod
    def resolve(self, input_value: str) -> ResolutionResult:
        """Resolve the input to a channel ID."""


class DatabaseStrategy(ResolutionStrategy):
    """Resolve channel identifiers using existing database records."""

    def can_resolve(self, input_value: str) -> bool:
        """Database can resolve any input format."""
        return True

    def resolve(self, input_value: str) -> ResolutionResult:
        """Try to resolve using existing database records."""
        try:
            # Check if input looks like a rowid (numeric)
            try:
                rowid = int(input_value)
                channel_id = get_channel_id_from_rowid(rowid)
                if channel_id:
                    return ResolutionResult(
                        success=True,
                        channel_id=channel_id,
                        resolution_method="database",
                        metadata={"cached": True},
                    )
            except ValueError:
                # Not a numeric rowid, continue to name lookup
                pass

            # Try to resolve by channel name
            channel_id = get_channel_id_from_name(input_value)
            if channel_id:
                return ResolutionResult(
                    success=True,
                    channel_id=channel_id,
                    resolution_method="database",
                    metadata={"cached": True},
                )

            # Channel not found in database
            return ResolutionResult(
                success=False,
                resolution_method="database",
                error_message="Channel not found in database",
            )

        except Exception as e:
            # Any other error, return failure
            return ResolutionResult(
                success=False,
                resolution_method="database",
                error_message=f"Database lookup error: {e!s}",
            )

        return ResolutionResult(
            success=False,
            resolution_method="database",
            error_message="Channel not found in database",
        )


class YtdlpStrategy(ResolutionStrategy):
    """Resolve channel identifiers using yt-dlp."""

    def __init__(self, console: Console):
        """
        Initialize yt-dlp resolution strategy.

        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.ydl_opts = {
            "verbose": False,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "socket_timeout": 15,
            "skip_download": True,
            "ignoreerrors": False,
        }

    def can_resolve(self, input_value: str) -> bool:
        """yt-dlp can handle most YouTube formats."""
        return YTDLP_AVAILABLE and self._is_youtube_format(input_value)

    def resolve(self, input_value: str) -> ResolutionResult:
        """Resolve using yt-dlp extraction."""
        print(f"DEBUG: YtdlpStrategy.resolve entry: {input_value}")
        if not YTDLP_AVAILABLE:
            return ResolutionResult(
                success=False,
                resolution_method="ytdlp",
                error_message="yt-dlp not available",
            )

        try:
            # Convert @handle to full URL if needed
            extract_url = input_value
            if input_value.startswith("@"):
                extract_url = f"https://www.youtube.com/{input_value}"
                self.console.print(
                    f"🔧 Converting @handle to URL: {input_value} → {extract_url}"
                )

            # Use extract_flat=False for better reliability for non-playlist URLs
            self.ydl_opts["extract_flat"] = False
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(extract_url, download=False)

                if info:
                    print(f"DEBUG: info keys: {list(info.keys())}")
                    if "channel_id" in info:
                        print(f"DEBUG: Found channel_id: {info['channel_id']}")
                        return ResolutionResult(
                            success=True,
                            channel_id=info["channel_id"],
                            channel_url=info.get("channel_url"),
                            channel_name=info.get("channel") or info.get("uploader"),
                            resolution_method="ytdlp",
                            metadata={
                                "extractor": info.get("extractor"),
                                "uploader": info.get("uploader"),
                                "channel_url": info.get("channel_url"),
                                "original_input": input_value,
                                "extract_url": extract_url,
                            },
                        )

        except Exception as e:
            print(f"DEBUG: YTDLP EXTRACTION ERROR: {e}")
            return ResolutionResult(
                success=False,
                resolution_method="ytdlp",
                error_message=f"yt-dlp extraction failed: {e!s}",
            )

        return ResolutionResult(
            success=False,
            resolution_method="ytdlp",
            error_message="Could not extract channel information",
        )

    def _is_youtube_format(self, input_value: str) -> bool:
        """Check if input looks like a YouTube URL/identifier."""
        youtube_patterns = [
            r"^@",  # @handle format
            r"youtube\.com/@",
            r"youtube\.com/channel/",
            r"youtube\.com/c/",
            r"youtu\.be/",
            r"youtube\.com/watch\?v=",
        ]
        return any(
            re.search(pattern, input_value, re.IGNORECASE)
            for pattern in youtube_patterns
        )


class DirectIdStrategy(ResolutionStrategy):
    """Handle direct channel ID inputs."""

    def can_resolve(self, input_value: str) -> bool:
        """Check if input is a direct channel ID."""
        return self._is_channel_id_format(input_value)

    def resolve(self, input_value: str) -> ResolutionResult:
        """Return the channel ID directly."""
        if self._is_channel_id_format(input_value):
            return ResolutionResult(
                success=True,
                channel_id=input_value,
                channel_url=f"https://www.youtube.com/channel/{input_value}",
                resolution_method="direct_id",
                metadata={"format": "channel_id"},
            )

        return ResolutionResult(
            success=False,
            resolution_method="direct_id",
            error_message="Invalid channel ID format",
        )

    def _is_channel_id_format(self, input_value: str) -> bool:
        """Check if input matches YouTube channel ID format (24 characters)."""
        return bool(re.match(r"^UC[a-zA-Z0-9_-]{22}$", input_value))


class ChannelIdentifierResolver:
    """
    Main resolver that coordinates multiple resolution strategies.

    Resolution strategy priority:
    1. Database (fastest for existing channels)
    2. Direct ID (for explicit channel IDs)
    3. yt-dlp (comprehensive extraction)
    """

    def __init__(
        self, console: Console | None = None, enable_file_updates: bool = True
    ):
        """
        Initialize the channel identifier resolver.

        Args:
            console: Rich console instance for output
            enable_file_updates: Whether to enable discovery cache file updates
        """
        self.console = console or Console()
        self.file_updater = (
            ChannelFileUpdater(self.console) if enable_file_updates else None
        )

        # Add cached strategy as first priority
        strategies = [
            DatabaseStrategy(),
            DirectIdStrategy(),
            YtdlpStrategy(self.console),
        ]

        if self.file_updater:
            # Insert discovery cache strategy after database but before expensive calls
            strategies.insert(1, DiscoveryCacheStrategy(self.file_updater))

        self.strategies = strategies

    def resolve(self, input_value: str) -> ResolutionResult:
        """
        Resolve a channel identifier to a canonical channel ID.

        Args:
            input_value: Channel identifier (@handle, channel ID, URL, etc.)

        Returns:
            ResolutionResult with channel ID and metadata
        """
        input_value = input_value.strip()

        if not input_value:
            return ResolutionResult(success=False, error_message="Empty input value")

        # Try each strategy in order
        for strategy in self.strategies:
            if strategy.can_resolve(input_value):
                result = strategy.resolve(input_value)
                if result.success:
                    # Debug: print resolution (disabled for cleaner output)
                    # self.console.print(
                    #     f"✅ [green]Resolved '{input_value}' → {result.channel_id} "
                    #     f"({result.resolution_method})[/green]"
                    # )

                    # Capture and store discovery if we have a file updater
                    if (
                        self.file_updater
                        and result.channel_name
                        and result.channel_name.startswith("@")
                    ):
                        # Record the discovery: original input → discovered @handle
                        self.file_updater.record_discovery(
                            input_value, result.channel_id, result.channel_name
                        )

                    return result
                # If strategy can resolve but failed, continue to next strategy

        # All strategies failed
        return ResolutionResult(
            success=False,
            error_message=f"Could not resolve channel identifier: '{input_value}'",
        )


class DiscoveryCacheStrategy(ResolutionStrategy):
    """Strategy that uses cached @handle discoveries for faster resolution."""

    def __init__(self, file_updater: ChannelFileUpdater):
        """
        Initialize discovery cache strategy.

        Args:
            file_updater: ChannelFileUpdater instance for cache access
        """
        self.file_updater = file_updater

    def can_resolve(self, input_value: str) -> bool:
        """Can resolve any input - checks cache first."""
        return True

    def resolve(self, input_value: str) -> ResolutionResult:
        """Try to resolve using cached discoveries."""
        # For @handles, check if we have corresponding channel ID
        if input_value.startswith("@"):
            # This would require reverse lookup - more complex
            # For now, let other strategies handle @handles
            return ResolutionResult(
                success=False,
                resolution_method="discovery_cache",
                error_message="Direct @handle resolution not cached",
            )

        # For URLs, check if we have cached @handle
        if input_value.startswith("https://"):
            # Try to extract channel ID from URL first
            channel_id = self._extract_channel_id_from_url(input_value)
            if channel_id:
                cached_handle = self.file_updater.get_discovered_handle(
                    input_value, channel_id
                )
                if cached_handle:
                    return ResolutionResult(
                        success=True,
                        channel_id=channel_id,
                        channel_name=cached_handle,
                        channel_url=input_value,
                        resolution_method="discovery_cache",
                        metadata={"cached": True, "from_previous_discovery": True},
                    )

        return ResolutionResult(
            success=False,
            resolution_method="discovery_cache",
            error_message="No cached discovery found",
        )

    def _extract_channel_id_from_url(self, url: str) -> str | None:
        """Extract channel ID from URL."""
        if "/channel/" in url:
            # Extract channel ID from /channel/UC... format
            match = re.search(r"/channel/(UC[a-zA-Z0-9_-]{22})", url)
            if match:
                return match.group(1)
        return None

    def resolve_batch(self, input_values: list[str]) -> dict[str, ResolutionResult]:
        """
        Resolve multiple channel identifiers.

        Args:
            input_values: List of channel identifiers

        Returns:
            Dictionary mapping input values to resolution results
        """
        results = {}

        for input_value in input_values:
            results[input_value] = self.resolve(input_value)

        return results

    def get_supported_formats(self) -> dict[str, str]:
        """
        Get information about supported input formats.

        Returns:
            Dictionary of format descriptions
        """
        return {
            "@handle": "YouTube handle (e.g., @channelname)",
            "Channel ID": "YouTube channel ID (e.g., UC...) - 24 characters",
            "Custom URL": "Custom channel URL (e.g., youtube.com/c/channelname)",
            "Channel URL": "Channel URL (e.g., youtube.com/channel/UC...)",
            "Video URL": "Video URL (extracts channel from video)",
            "Channel Name": "Plain channel name (requires yt-dlp)",
        }
