"""
Fast channel resolver for YouTube channel URL resolution.

This module provides optimized channel resolution without hitting YouTube APIs
when possible, using pattern matching and caching strategies.
"""
import re
from urllib.parse import quote

from rich.console import Console


class FastChannelResolver:
    """Optimized resolver for YouTube channel URLs and handles."""

    def __init__(self, cookies_from_browser: str | None = None, console: Console | None = None):
        """
        Initialize the fast channel resolver.

        Args:
            cookies_from_browser: Browser name for cookie extraction
            console: Rich console instance for output
        """
        self.cookies_from_browser = cookies_from_browser
        self.console = console or Console()

        # Cache for resolved channels
        self.resolution_cache: dict[str, str] = {}

        # Pattern matches for different YouTube URL formats
        self.patterns = {
            "handle": re.compile(r"@([a-zA-Z0-9._-]+)"),
            "custom_url": re.compile(r"youtube\.com/([a-zA-Z0-9._-]+)(?:\?|$)"),
            "channel_id": re.compile(r"youtube\.com/channel/([a-zA-Z0-9_-]{24})"),
        }

    def resolve_channel_fast(self, channel_input: str) -> str | None:
        """
        Resolve a channel input (handle, URL, or channel ID) to a channel ID.

        Args:
            channel_input: Channel handle (@handle), URL, or channel ID

        Returns:
            Resolved channel URL or None if resolution failed
        """
        # Check cache first
        if channel_input in self.resolution_cache:
            return self.resolution_cache[channel_input]

        # Skip if already a channel URL
        if "youtube.com/" in channel_input:
            # Ensure all channel URLs have consistent /videos suffix for caching
            # This prevents the same channel from appearing as "new" on every run
            resolved = channel_input if "/videos" in channel_input else f"{channel_input}/videos"
            # URL-encode the handle portion to fix pipe character and other special chars
            # E.g., @Marvomatic|AIAutomations -> @Marvomatic%7CAIAutomations
            if "/@" in resolved:
                # Extract handle, encode it, and reconstruct URL
                parts = resolved.split("/@")
                base = parts[0] + "/@"
                rest = parts[1] if len(parts) > 1 else ""
                handle_part = rest.split("/")[0] if "/" in rest else rest
                path_after = rest.split("/")[1] if "/" in rest and len(rest.split("/")) > 1 else ""
                # Reconstruct with encoded handle
                if path_after:
                    resolved = f"{base}{quote(handle_part, safe='')}/{path_after}"
                else:
                    resolved = f"{base}{quote(handle_part, safe='')}"
        elif "@" in channel_input:
            # Handle format: @username
            handle = channel_input.lstrip("@")
            resolved = f"https://www.youtube.com/@{quote(handle, safe="")}/videos"
        else:
            # Assume it's a channel ID
            resolved = f"https://www.youtube.com/channel/{channel_input}/videos"

        # Cache the result
        self.resolution_cache[channel_input] = resolved

        # No delay needed for pattern-based resolution (no network calls)
        return resolved

    def batch_resolve(self, channels: list[str], max_workers: int = 3) -> dict[str, str]:
        """
        Resolve multiple channels in parallel using conservative workers.

        Args:
            channels: List of channel inputs to resolve
            max_workers: Maximum number of parallel workers (unused, kept for API compat)

        Returns:
            Dictionary mapping original inputs to resolved URLs
        """
        resolved_channels = {}
        total = len(channels)

        # Show progress every 50 channels or 10%, whichever is more frequent
        progress_interval = max(1, min(50, total // 10))

        # Simple sequential resolution to avoid rate limiting
        for i, channel in enumerate(channels, 1):
            try:
                resolved = self.resolve_channel_fast(channel)
                if resolved:
                    resolved_channels[channel] = resolved
                else:
                    pass  # Resolution failed, silently continue
            except Exception:
                pass  # Suppress error messages during Rich mode

            # Show progress periodically
            if i % progress_interval == 0 or i == total:
                self.console.print(
                    f"[dim]Resolving {i}/{total} channels...[/dim]", end="\r"
                )

        # Clear the progress line
        self.console.print(" " * 50, end="\r")
        # Flush output to ensure progress is visible
        self.console.file.flush()

        return resolved_channels


def create_fast_resolver(cookies_from_browser: str | None = None,
                        console: Console | None = None) -> FastChannelResolver:
    """
    Factory function to create a FastChannelResolver instance.

    Args:
        cookies_from_browser: Browser name for cookie extraction
        console: Rich console instance for output

    Returns:
        FastChannelResolver instance
    """
    return FastChannelResolver(cookies_from_browser=cookies_from_browser, console=console)
