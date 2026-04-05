"""
Error Classifier for yt-dlp errors

Parses yt-dlp stderr output and classifies errors into user-friendly categories.
"""

import re
from enum import Enum


class ErrorCategory(Enum):
    """Categories of yt-dlp errors."""
    CHANNEL_NOT_FOUND = "channel_not_found"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    PRIVATE_CHANNEL = "private_channel"
    GEO_BLOCKED = "geo_blocked"
    AGE_RESTRICTED = "age_restricted"
    UNKNOWN = "unknown"


class ErrorClassifier:
    """Classify yt-dlp errors into user-friendly categories."""

    # Patterns for error classification
    PATTERNS = {
        ErrorCategory.CHANNEL_NOT_FOUND: [
            r"HTTP Error 404: Not Found",
            r"Requested entity was not found",
            r"channel .+(does not exist|is not available)",
            r"Video .+(unavailable|not found)",
            r"No videos found",
        ],
        ErrorCategory.RATE_LIMITED: [
            r"HTTP Error 429:.*Too Many Requests",
            r"RATE_LIMIT_EXCEEDED",
            r"Too many requests",
            r"quota.*exceeded",
            r"rate-limited",
            r"has been rate-limited",
            r"try again later",
        ],
        ErrorCategory.NETWORK_ERROR: [
            r"Connection.*reset",
            r"Network.*unreachable",
            r"Connection.*refused",
            r"Unable to download API page",
        ],
        ErrorCategory.TIMEOUT: [
            r"socket\.timeout",
            r"TimeoutError",
            r"timed out",
            r"ReadTimeout",
        ],
        ErrorCategory.PRIVATE_CHANNEL: [
            r"Private.*video",
            r"sign in to confirm.*age",
            r"This video is private",
        ],
        ErrorCategory.GEO_BLOCKED: [
            r"Not available in your country",
            r"geo.*blocked",
            r"not available.*region",
        ],
        ErrorCategory.AGE_RESTRICTED: [
            r"sign in.*age",
            r"age.*verification",
        ],
    }

    USER_MESSAGES = {
        ErrorCategory.CHANNEL_NOT_FOUND: "Channel not found or deleted",
        ErrorCategory.RATE_LIMITED: "Rate limited by YouTube - waiting before retry",
        ErrorCategory.NETWORK_ERROR: "Network error - check connection",
        ErrorCategory.TIMEOUT: "Request timed out",
        ErrorCategory.PRIVATE_CHANNEL: "Private channel - no access",
        ErrorCategory.GEO_BLOCKED: "Geo-blocked - not available in region",
        ErrorCategory.AGE_RESTRICTED: "Age-restricted - requires login",
        ErrorCategory.UNKNOWN: "Unknown error",
    }

    @classmethod
    def classify(cls, stderr_output: str) -> tuple[ErrorCategory, str]:
        """
        Classify error from stderr output.

        Args:
            stderr_output: Raw stderr output from yt-dlp

        Returns:
            Tuple of (ErrorCategory, user_friendly_message)
        """
        if not stderr_output:
            return ErrorCategory.UNKNOWN, cls.USER_MESSAGES[ErrorCategory.UNKNOWN]

        stderr_output.lower()

        # Check each category's patterns
        for category, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, stderr_output, re.IGNORECASE):
                    return category, cls.USER_MESSAGES[category]

        # Try to extract useful info from unknown errors
        if "404" in stderr_output:
            return ErrorCategory.CHANNEL_NOT_FOUND, cls.USER_MESSAGES[ErrorCategory.CHANNEL_NOT_FOUND]
        if "429" in stderr_output:
            return ErrorCategory.RATE_LIMITED, cls.USER_MESSAGES[ErrorCategory.RATE_LIMITED]

        # Extract first line of error for context
        first_line = stderr_output.split("\n")[0].strip()
        if first_line:
            return ErrorCategory.UNKNOWN, f"Error: {first_line[:80]}"

        return ErrorCategory.UNKNOWN, cls.USER_MESSAGES[ErrorCategory.UNKNOWN]

    @classmethod
    def should_suppress(cls, stderr_output: str) -> bool:
        """
        Determine if stderr output should be fully suppressed (safe to hide).

        Returns:
            True if output is safe to suppress, False if it contains important info
        """
        if not stderr_output:
            return True

        # Don't suppress if it contains useful debugging info
        important_keywords = [
            "traceback",
            "exception",
            "fatal",
            "corruption",
        ]

        stderr_lower = stderr_output.lower()
        for keyword in important_keywords:
            if keyword in stderr_lower:
                return False

        # Safe to suppress known yt-dlp error spam
        safe_patterns = [
            r"error: \[youtube:tab\]",
            r"error: \[youtube\]",
            r"http error \d+",
        ]

        return any(re.search(pattern, stderr_lower) for pattern in safe_patterns)
