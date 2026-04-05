"""
Time formatting utilities for download subsystem.
"""
from __future__ import annotations


def format_eta(seconds: float) -> str:
    """Format seconds into human-readable time remaining.

    Examples:
        >>> format_eta(45)
        '45s'
        >>> format_eta(90)
        '1m 30s'
        >>> format_eta(3700)
        '1h 1m'
        >>> format_eta(-1)
        'unknown'

    Args:
        seconds: Time in seconds (can be negative for unknown)

    Returns:
        Human-readable time string (e.g., "1h 23m 45s")
    """
    if seconds < 0:
        return "unknown"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s" if secs else f"{mins}m"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h {mins}m" if mins else f"{hours}h"
