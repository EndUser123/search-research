"""
Unified logging utilities for yt-fts.

Provides simple logging functions for batch operations and other utilities.
Extracted from multiple duplicate implementations across batch modules.
"""
import sys
from datetime import datetime as dt


def log_msg(tag: str, message: str) -> None:
    """Log a message with timestamp to stderr.

    This is a simple logging utility for batch operations and other utilities.
    For more advanced logging with structured output and dual sinks (file + console),
    see dual_sink_logger.py in the same utils directory.

    Args:
        tag: Log tag/category (e.g., 'QUOTA', 'LOAD', 'DOWNLOAD')
        message: Message to log
    """
    timestamp = dt.now().strftime("%H:%M:%S")
    sys.stderr.write(f"[{timestamp}] [{tag}] {message}\n")
    sys.stderr.flush()
