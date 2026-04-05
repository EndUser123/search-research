"""
User-friendly error message system.

Converts technical error messages into actionable guidance for users.
"""
from __future__ import annotations

from typing import Any


class UserFriendlyErrorHandler:
    """
    Converts technical errors into user-friendly, actionable messages.

    This system helps users understand what went wrong and how to fix it,
    rather than showing cryptic technical error messages.
    """

    def __init__(self):
        self.error_patterns = {
            # Network and connectivity errors
            "connection": {
                "patterns": [
                    "ConnectionError",
                    "TimeoutError",
                    "requests.exceptions.ConnectionError",
                    "urllib3.exceptions.MaxRetryError",
                    "NewConnectionError",
                    "Failed to establish a new connection",
                    "Network is unreachable",
                    "Temporary failure in name resolution",
                ],
                "message": "Network connection issue",
                "suggestions": [
                    "Check your internet connection",
                    "Try again in a few minutes",
                    "Disable VPN if you're using one",
                    "Check if YouTube is accessible in your browser",
                ],
            },
            # DNS resolution errors
            "dns": {
                "patterns": [
                    "Name resolution failure",
                    "getaddrinfo failed",
                    "nodename nor servname provided",
                    "[Errno 11001] getaddrinfo failed",
                    "[Errno -2] Name or service not known",
                ],
                "message": "DNS resolution failed",
                "suggestions": [
                    "Check your internet connection",
                    "Try a different DNS server (8.8.8.8)",
                    "Restart your router/modem",
                    "Try again in a few minutes",
                ],
            },
            # Rate limiting errors
            "rate_limit": {
                "patterns": [
                    "HTTP 429",
                    "Too Many Requests",
                    "rate limit",
                    "quota exceeded",
                    "quotaExceeded",
                    "Rate exceeded",
                ],
                "message": "Rate limit or quota exceeded",
                "suggestions": [
                    "Wait a few minutes before trying again",
                    "Reduce the number of parallel downloads (use --jobs 1)",
                    "Use --cookies-from-browser to avoid rate limits",
                    "Check your YouTube API quota at https://console.cloud.google.com/",
                ],
            },
            # Authentication errors
            "auth": {
                "patterns": [
                    "HTTP 401",
                    "HTTP 403",
                    "Unauthorized",
                    "Forbidden",
                    "Sign in to confirm",
                    "Login required",
                    "authentication",
                    "not signed in",
                ],
                "message": "Authentication required",
                "suggestions": [
                    "Use --cookies-from-browser firefox (or chrome)",
                    "Make sure you're logged into YouTube in your browser",
                    "Try a different browser if cookies aren't working",
                    "Check if the video/channel requires login",
                ],
            },
            # Geo-blocking errors
            "geo_block": {
                "patterns": [
                    "not available in your country",
                    "geographic restriction",
                    "blocked in your region",
                    "not available",
                    "This video is not available",
                    "who has blocked it on copyright grounds",
                ],
                "message": "Content blocked in your region",
                "suggestions": [
                    "Try using a VPN",
                    "Use --cookies-from-browser (may help with some blocks)",
                    "The video may not be available in your country",
                    "Check if the content is region-restricted",
                ],
            },
            # Channel not found errors
            "channel_not_found": {
                "patterns": [
                    "channel not found",
                    "does not exist",
                    "Invalid channel",
                    "UC.* not found",
                    "@.* not found",
                    "Unable to extract uploader id",
                ],
                "message": "Channel not found",
                "suggestions": [
                    "Double-check the channel URL or handle",
                    "Make sure the channel still exists",
                    "Try using the full URL instead of @handle",
                    "Use https://www.youtube.com/channel/UC... format if you have the ID",
                ],
            },
            # Video not found errors
            "video_not_found": {
                "patterns": [
                    "Video unavailable",
                    "video not found",
                    "Private video",
                    "This video has been removed",
                    "deleted by the user",
                    "is private",
                    "is unavailable",
                ],
                "message": "Video not available",
                "suggestions": [
                    "The video may have been deleted or made private",
                    "Check if the video URL is correct",
                    "Try updating the channel to get current videos",
                    "Some videos may be temporarily unavailable",
                ],
            },
            # yt-dlp specific errors
            "ytdlp_generic": {
                "patterns": [
                    "yt-dlp",
                    "youtube-dl",
                    "ExtractorError",
                    "DownloadError",
                ],
                "message": "Download tool error",
                "suggestions": [
                    "Try updating yt-dlp: pip install --upgrade yt-dlp",
                    "Use --cookies-from-browser to help with restrictions",
                    "Some content may not be downloadable",
                    "Check yt-dlp GitHub issues for similar problems",
                ],
            },
            # Database errors
            "database": {
                "patterns": [
                    "database is locked",
                    "SQLITE_BUSY",
                    "database disk image is malformed",
                    "no such table",
                    "foreign key constraint failed",
                ],
                "message": "Database error",
                "suggestions": [
                    "Close other yt-fts processes",
                    "Run 'yt-fts health' to check database integrity",
                    "Try deleting subtitles.db and re-downloading",
                    "Make sure you have write permissions to the database file",
                ],
            },
            # Permission errors
            "permission": {
                "patterns": [
                    "Permission denied",
                    "Access is denied",
                    "[Errno 13]",
                    "errno 13",
                    "readonly",
                ],
                "message": "File permission error",
                "suggestions": [
                    "Run the command as administrator/sudo",
                    "Check write permissions for the output directory",
                    "Make sure the database file isn't read-only",
                    "Try running in a different directory",
                ],
            },
            # Disk space errors
            "disk_space": {
                "patterns": [
                    "No space left on device",
                    "Disk full",
                    "errno 28",
                    "[Errno 28]",
                ],
                "message": "Not enough disk space",
                "suggestions": [
                    "Free up disk space",
                    "Choose a different output directory",
                    "Delete temporary files",
                    "Check available space with 'df -h' (Linux/Mac) or disk properties (Windows)",
                ],
            },
        }

    def get_user_friendly_message(self, error_msg: str) -> dict[str, Any]:
        """
        Convert a technical error message into user-friendly guidance.

        Args:
            error_msg: The original technical error message

        Returns:
            Dict with keys: message, suggestions, category
        """
        error_lower = str(error_msg).lower()

        # Check each error category for matches
        for category, info in self.error_patterns.items():
            for pattern in info["patterns"]:
                if pattern.lower() in error_lower:
                    return {
                        "message": info["message"],
                        "suggestions": info["suggestions"],
                        "category": category,
                        "original_error": error_msg,
                    }

        # Default fallback for unrecognized errors
        return {
            "message": "An unexpected error occurred",
            "suggestions": [
                "Try the command again",
                "Check the error details above for more information",
                "Use --verbose flag for more detailed error output",
                "Report the issue if it persists",
            ],
            "category": "unknown",
            "original_error": error_msg,
        }

    def format_error_display(self, error_result: dict[str, Any]) -> str:
        """
        Format error information for display to the user.

        Args:
            error_result: Result from get_user_friendly_message()

        Returns:
            Formatted error message string
        """
        lines = []

        # Main error message
        lines.append(f"[bold red]❌ {error_result['message']}[/bold red]")

        # Suggestions
        if error_result["suggestions"]:
            lines.append("")
            lines.append("[yellow]💡 Suggestions:[/yellow]")
            for suggestion in error_result["suggestions"]:
                lines.append(f"  • {suggestion}")

        # Show original error in debug mode or for unknown errors
        if error_result["category"] == "unknown":
            lines.append("")
            lines.append("[dim]Technical details:[/dim]")
            lines.append(f"[dim]{error_result['original_error']}[/dim]")

        return "\n".join(lines)


# Global instance for convenience
_error_handler = UserFriendlyErrorHandler()


def get_user_friendly_message(error_msg: str) -> dict[str, Any]:
    """
    Get user-friendly error message for any error string.

    This is the main entry point for converting technical errors
    into user-friendly messages.

    Args:
        error_msg: Technical error message

    Returns:
        Dict with user-friendly message, suggestions, and category
    """
    return _error_handler.get_user_friendly_message(error_msg)


def format_error_for_display(error_msg: str) -> str:
    """
    Get a formatted, user-friendly error message ready for display.

    Args:
        error_msg: Technical error message

    Returns:
        Formatted string with error message and suggestions
    """
    error_result = _error_handler.get_user_friendly_message(error_msg)
    return _error_handler.format_error_display(error_result)
