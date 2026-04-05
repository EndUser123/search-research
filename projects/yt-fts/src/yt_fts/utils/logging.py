"""
Unified logging utilities for yt-fts.

Provides simple logging functions for batch operations and other utilities.
Extracted from multiple duplicate implementations across batch modules.
"""

from __future__ import annotations
import sys
import threading
from datetime import datetime as dt


# Lock for thread-safe stderr writes
_stderr_write_lock = threading.Lock()


def log_msg(tag: str, message: str) -> None:
    """Log a message with timestamp to stderr.

    This is a simple logging utility for batch operations and other utilities.
    For more advanced logging with structured output and dual sinks (file + console),
    see dual_sink_logger.py in the same utils directory.

    Thread-safe: acquires lock before writing to stderr.

    Args:
        tag: Log tag/category (e.g., 'QUOTA', 'LOAD', 'DOWNLOAD')
        message: Message to log
    """
    timestamp = dt.now().strftime("%H:%M:%S")
    with _stderr_write_lock:
        sys.stderr.write(f"[{timestamp}] [{tag}] {message}\n")
        sys.stderr.flush()
