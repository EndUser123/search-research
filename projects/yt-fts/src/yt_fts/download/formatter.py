"""
Error formatting utilities for batch download operations.

Provides error classification and formatting for user-friendly display.
"""
from __future__ import annotations

from yt_fts.utils.error_classifier import ErrorCategory, ErrorClassifier


def format_error(raw_error: str) -> tuple[str, str]:
    """
    Classify error and return (emoji, display_message).

    Args:
        raw_error: Raw error string to classify

    Returns:
        Tuple of (emoji, formatted_message)
    """
    category, user_msg = ErrorClassifier.classify(raw_error)
    display_msg = user_msg if user_msg else raw_error

    # Truncate very long messages
    if len(display_msg) > 50:
        display_msg = display_msg[:47] + "..."

    # Use shared emoji mapping from ErrorClassifier
    emoji = ErrorClassifier.EMOJI_MAP.get(category, "❌")

    return emoji, display_msg
