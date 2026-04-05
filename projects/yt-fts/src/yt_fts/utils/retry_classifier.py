"""
Retry Classifier - Determines if errors are retriable and calculates backoff.

YouTube returns 404/403 errors for both:
1. Real failures (channel not found, private video)
2. Transient rate limiting (too many requests)

This module provides intelligent retry logic:
- 404/403 are treated as retriable (may be rate limit)
- Exponential backoff with different rates for rate limit vs standard errors
- After max retries, give up permanently
"""
from __future__ import annotations



# Error patterns that indicate rate limiting
RATE_LIMIT_PATTERNS = [
    "rate-limited",
    "rate limited",
    "http error 429",
    "too many requests",
    "try again later",
]

# Error patterns that indicate retriable transient errors
RETRIABLE_PATTERNS = [
    "http error 403",  # Forbidden - may be rate limit or geo-block
    "http error 404",  # Not Found - may be transient rate limit
    "http error 503",  # Service Unavailable
    "http error 502",  # Bad Gateway
    "connection reset",
    "connection refused",
    "timeout",
    "timed out",
    "network unreachable",
]


def is_retriable_error(error_msg: str) -> bool:
    """
    Determine if an error is retriable.

    404 and 403 errors are considered retriable because YouTube sometimes
    returns these as rate limit responses during high-volume batch processing.

    Args:
        error_msg: The error message to evaluate

    Returns:
        True if error is retriable, False if permanent failure

    Examples:
        >>> is_retriable_error("HTTP Error 404: Not Found")
        True
        >>> is_retriable_error("HTTP Error 403: Forbidden")
        True
        >>> is_retriable_error("HTTP Error 429: Too Many Requests")
        True
        >>> is_retriable_error("Channel not found")
        False  # Only after retries exhausted
    """
    if not error_msg:
        return False

    error_lower = error_msg.lower()

    # Check for rate limit patterns (always retriable)
    for pattern in RATE_LIMIT_PATTERNS:
        if pattern in error_lower:
            return True

    # Check for retriable transient patterns
    return any(pattern in error_lower for pattern in RETRIABLE_PATTERNS)


def is_rate_limit_error(error_msg: str) -> bool:
    """
    Determine if an error is specifically a rate limit response.

    Args:
        error_msg: The error message to evaluate

    Returns:
        True if error is a rate limit, False otherwise
    """
    if not error_msg:
        return False

    error_lower = error_msg.lower()

    for pattern in RATE_LIMIT_PATTERNS:
        if pattern in error_lower:
            return True

    # 403 is often a rate limit
    return bool("http error 403" in error_lower or "403 forbidden" in error_lower)


def get_backoff_time(
    error_msg: str,
    attempt: int,
    is_rate_limit_context: bool = False,
) -> int:
    """
    Calculate backoff time in seconds before next retry.

    Uses different backoff strategies:
    - Rate limit errors: 60 * 2^attempt (capped at 300s)
    - Standard errors: 2^attempt (capped at 60s)

    Args:
        error_msg: The error message to classify
        attempt: Current retry attempt number (0-indexed)
        is_rate_limit_context: If True, use rate limit backoff regardless

    Returns:
        Seconds to wait before next retry

    Examples:
        >>> get_backoff_time("HTTP Error 429", 0)
        60
        >>> get_backoff_time("HTTP Error 404", 1)
        2
        >>> get_backoff_time("HTTP Error 403", 1)
        120
    """
    # Determine if this is a rate limit error
    if is_rate_limit_context or is_rate_limit_error(error_msg):
        # Rate limit backoff: start at 60s, double each time, cap at 300s
        return min(60 * (2 ** attempt), 300)

    # Standard backoff: start at 1s, double each time, cap at 60s
    return min(2 ** attempt, 60)


def should_permanent_fail(
    error_msg: str,
    retry_count: int,
    max_retries: int,
) -> bool:
    """
    Determine if an error should result in permanent failure.

    Args:
        error_msg: The error message to evaluate
        retry_count: Current number of retries attempted
        max_retries: Maximum number of retries allowed

    Returns:
        True if should give up, False if should continue retrying

    Examples:
        >>> should_permanent_fail("HTTP Error 404", 3, 3)
        True
        >>> should_permanent_fail("HTTP Error 404", 2, 3)
        False
    """
    # If we haven't exhausted retries, don't give up
    if retry_count < max_retries:
        return False

    # Retries exhausted - check if error is still retriable
    # Even retriable errors become permanent after max retries
    return True


def should_skip_retry(error_msg: str) -> bool:
    """
    Determine if an error should skip retries entirely (permanent failure on first attempt).

    This is used for genuinely empty channels or permanently deleted channels
    where retrying won't help.

    Args:
        error_msg: The error message to evaluate

    Returns:
        True if should skip retries, False if should retry normally

    Examples:
        >>> should_skip_retry("No videos found for channel")
        True
        >>> should_skip_retry("HTTP Error 404")
        False  # 404 might be transient, so we retry
        >>> should_skip_retry("channel not found")
        True
    """
    if not error_msg:
        return False

    error_lower = error_msg.lower()

    # Patterns that indicate a genuine empty/missing channel (not transient)
    SKIP_RETRY_PATTERNS = [
        "no videos found for channel",
        "channel is empty",
        "this channel does not exist",
        "channel doesn't exist",
        "channel does not have any videos",
    ]

    for pattern in SKIP_RETRY_PATTERNS:
        if pattern in error_lower:
            return True

    # Don't skip retries for HTTP errors (might be transient)
    if "http error" in error_lower:
        return False

    return False


def should_verify_channel(
    error_msg: str,
    channel_url: str,
    attempt: int,
) -> bool:
    """
    Determine if channel existence should be verified.

    For 404 errors on early attempts, we should verify the channel
    actually exists (not just assume it's a rate limit).

    Args:
        error_msg: The error message to evaluate
        channel_url: The channel URL being accessed
        attempt: Current retry attempt number

    Returns:
        True if channel should be verified, False otherwise

    Examples:
        >>> should_verify_channel("HTTP Error 404", "https://...", 0)
        True
        >>> should_verify_channel("HTTP Error 404", "https://...", 3)
        False  # Don't verify on later retries
    """
    # Only verify on first 404 attempt
    if attempt > 0:
        return False

    error_lower = error_msg.lower()
    return "http error 404" in error_lower or "404 not found" in error_lower


def get_retry_strategy(
    error_msg: str,
    max_retries: int = 3,
) -> dict:
    """
    Get complete retry strategy for an error.

    Args:
        error_msg: The error message to analyze
        max_retries: Maximum number of retries (default: 3)

    Returns:
        Dictionary with retry strategy:
        {
            "retriable": bool,
            "is_rate_limit": bool,
            "backoff_fn": callable,
            "max_retries": int,
            "should_verify": bool,
        }

    Examples:
        >>> strategy = get_retry_strategy("HTTP Error 404")
        >>> strategy["retriable"]
        True
        >>> strategy["is_rate_limit"]
        False
    """
    return {
        "retriable": is_retriable_error(error_msg),
        "is_rate_limit": is_rate_limit_error(error_msg),
        "backoff_fn": lambda attempt: get_backoff_time(error_msg, attempt),
        "max_retries": max_retries,
        "should_verify": should_verify_channel(error_msg, "", 0),
    }


# Error message mappings for user-friendly display
_ERROR_MESSAGE_MAP: dict[str, str] = {
    # HTTP 4xx - Client errors
    "http error 403": (
        "Rate limited by YouTube. Please wait a few minutes before trying again. "
        "This error can also occur if content is geo-blocked in your region."
    ),
    "403 forbidden": (
        "Rate limited by YouTube. Please wait a few minutes before trying again. "
        "This error can also occur if content is geo-blocked in your region."
    ),
    "http error 404": (
        "Channel or video not found. Please verify the URL is correct. "
        "If this persists, the content may have been deleted or made private."
    ),
    "404 not found": (
        "Channel or video not found. Please verify the URL is correct. "
        "If this persists, the content may have been deleted or made private."
    ),
    "http error 429": (
        "Too many requests to YouTube. Please wait 10-15 minutes before trying again. "
        "Consider reducing the number of simultaneous downloads."
    ),
    "too many requests": (
        "Too many requests to YouTube. Please wait 10-15 minutes before trying again. "
        "Consider reducing the number of simultaneous downloads."
    ),
    # HTTP 5xx - Server errors
    "http error 502": "YouTube servers are experiencing issues. Please try again in a few minutes.",
    "http error 503": "YouTube service is temporarily unavailable. Please try again later.",
    "http error 500": "YouTube encountered an internal error. Please try again.",
    # Network errors
    "connection reset": "Connection was reset. Please check your internet connection and try again.",
    "connection refused": "Connection refused. Please check your internet connection and try again.",
    "connection timed out": "Connection timed out. Please check your internet connection and try again.",
    "timeout": "Request timed out. Please check your internet connection and try again.",
    "timed out": "Request timed out. Please check your internet connection and try again.",
    "network unreachable": "Network unreachable. Please check your internet connection.",
    # SSL/TLS errors
    "ssl": "Secure connection failed. This may be a temporary network issue.",
    "certificate": "Certificate verification failed. This may be a temporary network issue.",
    # Authentication errors
    "unauthorized": "Authentication failed. Please check your API credentials if configured.",
    "authentication": "Authentication failed. Please check your API credentials if configured.",
    # Generic YouTube errors
    "sign in": "YouTube requires sign-in. This content may be age-restricted or private.",
    "private": "This content is private and cannot be accessed.",
    "age restricted": "This content is age-restricted and cannot be accessed.",
    # Download errors
    "video unavailable": "Video is unavailable. It may have been deleted or made private.",
    "premium": "This content requires YouTube Premium.",
    "members only": "This content is for channel members only.",
}


def get_user_friendly_message(error_msg: str) -> str:
    """
    Convert technical error messages into user-friendly messages with actionable suggestions.

    Args:
        error_msg: The raw error message to translate

    Returns:
        A user-friendly error message with helpful next steps

    Examples:
        >>> get_user_friendly_message("HTTP Error 403: Forbidden")
        "Rate limited by YouTube. Please wait a few minutes..."
        >>> get_user_friendly_message("Connection refused")
        "Connection refused. Please check your internet connection..."
    """
    if not error_msg:
        return "An unknown error occurred. Please try again."

    error_lower = error_msg.lower()

    # Check for matching error patterns
    for pattern, user_message in _ERROR_MESSAGE_MAP.items():
        if pattern in error_lower:
            return user_message

    # No specific match - return generic helpful message
    return (
        f"An error occurred: {error_msg}. "
        "If this persists, please check your internet connection and try again later."
    )
