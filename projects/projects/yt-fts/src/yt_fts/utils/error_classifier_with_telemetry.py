"""
Enhanced Error Classifier with Telemetry Integration

This module extends the base ErrorClassifier with automatic telemetry
recording for all classified errors.
"""


__all__ = [
    "ErrorClassifierWithTelemetry",
    "get_error_statistics",
    "get_telemetry_summary",
    "print_error_summary",
]


from .error_classifier import ErrorCategory, ErrorClassifier
from .error_telemetry import ErrorTelemetry, get_global_telemetry


class ErrorClassifierWithTelemetry:
    """
    Error classifier with automatic telemetry tracking.

    Automatically records all classified errors to the global telemetry
    collector for later analysis and reporting.

    Usage:
        # Initialize telemetry at start of batch
        telemetry = get_global_telemetry()

        # Classify errors (automatically recorded)
        category, message = ErrorClassifierWithTelemetry.classify(stderr_output)

        # Get summary at end
        print(telemetry.display_summary())
    """

    @classmethod
    def classify(
        cls,
        stderr_output: str,
        *,
        record_telemetry: bool = True,
        video_id: str | None = None,
        channel_id: str | None = None,
        telemetry_instance: ErrorTelemetry | None = None,
    ) -> tuple[ErrorCategory, str]:
        """
        Classify error and optionally record to telemetry.

        Args:
            stderr_output: Raw stderr output from yt-dlp
            record_telemetry: Whether to record this error to telemetry (default: True)
            video_id: Optional video ID for telemetry
            channel_id: Optional channel ID for telemetry
            telemetry_instance: Specific telemetry instance to use (default: global)

        Returns:
            Tuple of (ErrorCategory, user_friendly_message)
        """
        # Use base classifier for actual classification
        category, message = ErrorClassifier.classify(stderr_output)

        # Record to telemetry if enabled
        if record_telemetry:
            telemetry = telemetry_instance or get_global_telemetry()
            telemetry.record_error(
                category=category,
                message=message,
                video_id=video_id,
                channel_id=channel_id,
                context={"raw_stderr": stderr_output[:200]},  # First 200 chars
            )

        return category, message

    @classmethod
    def classify_and_format(
        cls,
        stderr_output: str,
        *,
        record_telemetry: bool = True,
        video_id: str | None = None,
        channel_id: str | None = None,
        emoji: bool = True,
    ) -> str:
        """
        Classify error and return a formatted string for display.

        Args:
            stderr_output: Raw stderr output from yt-dlp
            record_telemetry: Whether to record to telemetry
            video_id: Optional video ID for telemetry
            channel_id: Optional channel ID for telemetry
            emoji: Whether to include emoji in output

        Returns:
            Formatted error string (e.g., "⚠ Rate limited - use cookies or wait")
        """
        category, message = cls.classify(
            stderr_output,
            record_telemetry=record_telemetry,
            video_id=video_id,
            channel_id=channel_id,
        )

        # Add emoji based on category
        emoji_map = {
            ErrorCategory.RATE_LIMITED: "⚠",
            ErrorCategory.CHANNEL_NOT_FOUND: "✖",
            ErrorCategory.TIMEOUT: "⏱",
            ErrorCategory.NETWORK_ERROR: "🌐",
            ErrorCategory.PRIVATE_CHANNEL: "🔒",
            ErrorCategory.GEO_BLOCKED: "🌍",
            ErrorCategory.AGE_RESTRICTED: "🔞",
            ErrorCategory.UNKNOWN: "✗",
        }

        prefix = f"{emoji_map.get(category, '✗')} " if emoji else ""
        return f"{prefix}{message}"


def get_telemetry_summary() -> str:
    """
    Get a formatted summary of all recorded errors.

    Convenience function that returns the global telemetry summary.

    Returns:
        Formatted summary string
    """
    telemetry = get_global_telemetry()
    return telemetry.display_summary()


def get_error_statistics() -> dict[str, int]:
    """
    Get error statistics as a dictionary.

    Returns:
        Dict with error category counts
    """
    telemetry = get_global_telemetry()
    stats = telemetry.get_stats()

    return {
        category.value: count
        for category, count in stats.by_category.items()
    }


def print_error_summary() -> None:
    """Print the error telemetry summary to console."""
    print(get_telemetry_summary())
