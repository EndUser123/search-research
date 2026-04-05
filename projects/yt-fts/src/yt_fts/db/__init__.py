"""
Database connection factory module for yt-fts.

This module provides a centralized interface for creating SQLite database
connections with standardized configuration for concurrent access and performance.

The main exports are:
    - get_connection: Context manager for automatic connection cleanup
    - open_connection: Direct connection function (manual cleanup required)
    - is_wal_mode: Check if database is in WAL mode
    - run_wal_checkpoint: Execute WAL checkpoint operations

Example:
    >>> from yt_fts.db import get_connection
    >>>
    >>> with get_connection() as conn:
    ...     cursor = conn.cursor()
    ...     cursor.execute("SELECT COUNT(*) FROM Videos")
    ...     count = cursor.fetchone()[0]
"""
from __future__ import annotations

from yt_fts.db.factory import (
    get_connection,
    get_pragma,
    is_wal_mode,
    open_connection,
    run_wal_checkpoint,
)

__all__ = [
    "get_connection",
    "get_pragma",
    "is_wal_mode",
    "open_connection",
    "run_wal_checkpoint",
]
