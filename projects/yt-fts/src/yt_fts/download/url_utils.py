"""
URL utilities for YouTube channel validation and normalization.

Provides functions for validating and normalizing YouTube channel URLs
in various formats (@handle, /channel/ID, etc.).
"""

from __future__ import annotations
from collections.abc import Callable
from urllib.parse import quote, unquote, urlparse
from .url_utils_constants import MIN_PATH_COMPONENTS, URL_SLASH_SUFFIX


# User agent strings for HTTP requests (rotated to avoid detection)
USER_AGENTS = [
    # Latest Chrome versions
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Latest Firefox versions
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
    # Latest Safari versions
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    # Latest Edge versions
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]


def validate_channel_url(
    channel_url: str,
    print_callback: Callable[[str], None] | None = None,
) -> str | None:
    """
    Validate and normalize a YouTube channel URL.

    Args:
        channel_url: Channel URL to validate
        print_callback: Optional callback for error messages

    Returns:
        Normalized channel URL or None if invalid
    """
    def print_msg(msg: str) -> None:
        """
        Print message using callback if available.

        Args:
            msg: Message to print
        """
        if print_callback:
            print_callback(msg)

    channel_url = channel_url.strip(URL_SLASH_SUFFIX)
    parsed = urlparse(channel_url)
    domain = parsed.netloc
    path = parsed.path.split("/")

    if not domain.endswith("youtube.com"):
        print_msg("")
        print_msg(
            f"[bold red]Error:[/bold red] Invalid channel domain: [blue]{domain}[/blue]"
        )
        print_msg("[yellow]💡 Suggestions:[/yellow]")
        print_msg("   • Use a YouTube URL (youtube.com)")
        print_msg("   • Try the channel's @handle instead")
        print_msg("")
        return None

    if len(path) < MIN_PATH_COMPONENTS:
        print_msg("")
        print_msg(
            f"[bold red]Error:[/bold red] Invalid channel url: [blue]{channel_url}[/blue]"
        )
        print_msg("[yellow]💡 Suggestions:[/yellow]")
        print_msg("   • Check the URL format")
        print_msg("   • Try the channel's @handle (e.g., @channelname)")
        print_msg("")
        return None

    if path[1].startswith("@"):
        # Extract handle, remove @ prefix
        handle = path[1][1:]
        
        # Check if already URL-encoded to prevent double-encoding
        # If unquoted version differs, it was already encoded
        unquoted = unquote(handle)
        if unquoted == handle:
            # Not encoded yet - encode it now
            encoded_handle = quote(handle, safe="")
        else:
            # Already encoded - use as-is to prevent double-encoding
            # (e.g., %7C should not become %257C)
            encoded_handle = handle
            
        return f"https://www.youtube.com/@{encoded_handle}/videos"

    if path[1] == "channel":
        return f"https://www.youtube.com/channel/{path[2]}/videos"

    print_msg("")
    print_msg(
        f"[bold red]Error:[/bold red] Unknown url format: [blue]{channel_url}[/blue]"
    )
    print_msg("[yellow]💡 Try one of these formats:[/yellow]")
    print_msg("")
    print_msg(
        "    • https://www.youtube.com/[yellow]@channelname[/yellow]"
    )
    print_msg(
        "    • https://www.youtube.com/channel/[yellow]channelId[/yellow]"
    )
    print_msg("")
    return None
