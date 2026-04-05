"""
Database connection factory for yt-fts.

This module provides a centralized, production-ready interface for creating
SQLite database connections with standardized configuration. It handles:
- WAL mode for better concurrent access
- Proper connection timeouts and busy handling
- Thread-safe connections
- Parent directory creation
- Comprehensive error handling and logging

Example:
    >>> from yt_fts.db.factory import get_connection, open_connection
    >>>
    >>> # Using context manager (recommended for auto-cleanup)
    >>> with get_connection() as conn:
    >>>     cursor = conn.cursor()
    >>>     cursor.execute("SELECT COUNT(*) FROM Videos")
    >>>     print(cursor.fetchone()[0])
    >>>
    >>> # Direct connection (manual close required)
    >>> conn = open_connection()
    >>> try:
    >>>     cursor = conn.cursor()
    >>>     cursor.execute("SELECT COUNT(*) FROM Videos")
    >>>     print(cursor.fetchone()[0])
    >>> finally:
    >>>     conn.close()
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from yt_fts.utils.config import get_db_path

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

# Standard PRAGMA settings applied to all connections
_DEFAULT_PRAGMAS = {
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "busy_timeout": "5000",
    "foreign_keys": "ON",
    "cache_size": "-64000",  # 64MB cache
    "temp_store": "MEMORY",
    "mmap_size": "268435456",  # 256MB mmap
}


@contextmanager
def get_connection(
    db_path: str | None = None,
    timeout: float = 5.0,
    isolation_level: str | None = None,
) -> Iterator[sqlite3.Connection]:
    """Context manager for database connections with automatic cleanup.

    Opens a connection to the database with optimized settings and ensures
    proper cleanup on exit. The connection is automatically closed when
    the context manager exits, even if an exception occurs.

    Args:
        db_path: Path to the SQLite database file. If None, uses the default
            path from get_db_path().
        timeout: Connection timeout in seconds. Default is 5.0.
        isolation_level: The isolation level for the connection.
            - None: Autocommit mode (default)
            - "DEFERRED": Deferred transactions
            - "IMMEDIATE": Immediate transactions
            - "EXCLUSIVE": Exclusive transactions

    Yields:
        A configured sqlite3.Connection object.

    Raises:
        sqlite3.OperationalError: If the database is corrupted or
            cannot be accessed.
        OSError: If the database directory cannot be created.

    Example:
        >>> with get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM Videos LIMIT 1")
        ...     result = cursor.fetchone()
    """
    conn = None
    try:
        conn = open_connection(db_path=db_path, timeout=timeout, isolation_level=isolation_level)
        yield conn
    except sqlite3.DatabaseError as e:
        logger.exception("Database error during connection: %s", e)
        raise
    except sqlite3.OperationalError as e:
        if "database is malformed" in str(e).lower() or "database disk image is malformed" in str(e).lower():
            logger.exception("Corrupted database detected at %s: %s", db_path or get_db_path(), e)
        raise
    finally:
        if conn is not None:
            conn.close()


def open_connection(
    db_path: str | None = None,
    timeout: float = 5.0,
    isolation_level: str | None = None,
) -> sqlite3.Connection:
    """Open a database connection with standardized settings.

    Creates a new SQLite connection with optimized PRAGMA settings for
    concurrent access and performance. The caller is responsible for
    closing the connection when done.

    Connection settings applied:
        - journal_mode=WAL: Write-Ahead Logging for better concurrency
        - synchronous=NORMAL: Balance between safety and performance
        - busy_timeout=5000: Wait up to 5 seconds for locks
        - check_same_thread=False: Allow connection sharing across threads
        - cache_size=64MB: In-memory cache for better performance

    Args:
        db_path: Path to the SQLite database file. If None, uses the default
            path from get_db_path().
        timeout: Connection timeout in seconds. Default is 5.0.
        isolation_level: The isolation level for the connection.
            - None: Autocommit mode (default)
            - "DEFERRED": Deferred transactions
            - "IMMEDIATE": Immediate transactions
            - "EXCLUSIVE": Exclusive transactions

    Returns:
        A configured sqlite3.Connection object.

    Raises:
        sqlite3.OperationalError: If the database is corrupted or
            cannot be accessed.
        OSError: If the database directory cannot be created.

    Example:
        >>> conn = open_connection()
        >>> try:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM Videos LIMIT 1")
        ...     result = cursor.fetchone()
        ... finally:
        ...     conn.close()
    """
    # Get the actual database path
    actual_db_path = db_path if db_path is not None else get_db_path()

    # Ensure parent directory exists
    _ensure_db_directory(actual_db_path)

    # Convert timeout to seconds (sqlite3 expects int/float)
    timeout_seconds = int(timeout)

    try:
        conn = sqlite3.connect(
            actual_db_path,
            timeout=timeout_seconds,
            check_same_thread=False,
            isolation_level=isolation_level,
        )

        # Apply standardized PRAGMA settings
        _apply_pragmas(conn)

        logger.debug("Opened connection to database: %s", actual_db_path)
        return conn

    except sqlite3.DatabaseError as e:
        if "database is malformed" in str(e).lower() or "database disk image is malformed" in str(e).lower():
            logger.exception("Corrupted database detected at %s: %s", actual_db_path, e)
        else:
            logger.exception("Database error opening %s: %s", actual_db_path, e)
        raise
    except sqlite3.OperationalError as e:
        logger.exception("Operational error opening database %s: %s", actual_db_path, e)
        raise
    except OSError as e:
        logger.exception("OS error accessing database %s: %s", actual_db_path, e)
        raise


def _ensure_db_directory(db_path: str) -> None:
    """Ensure the database parent directory exists.

    Args:
        db_path: Path to the database file.

    Raises:
        OSError: If the directory cannot be created.
    """
    db_file = Path(db_path)
    parent_dir = db_file.parent

    if parent_dir != Path() and not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Created database directory: %s", parent_dir)
        except OSError as e:
            logger.exception("Failed to create database directory %s: %s", parent_dir, e)
            raise


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply standardized PRAGMA settings to a connection.

    Args:
        conn: The SQLite connection to configure.

    Raises:
        sqlite3.OperationalError: If a PRAGMA cannot be set.
    """
    cursor = conn.cursor()

    for pragma_name, pragma_value in _DEFAULT_PRAGMAS.items():
        try:
            cursor.execute(f"PRAGMA {pragma_name}={pragma_value}")
        except sqlite3.OperationalError as e:
            # Log but don't fail for non-critical PRAGMAs
            logger.warning("Failed to set PRAGMA %s=%s: %s", pragma_name, pragma_value, e)

    # Row factory for dict-like access (optional, but commonly useful)
    # conn.row_factory = sqlite3.Row  # Uncomment if dict access is desired

    cursor.close()


def get_pragma(conn: sqlite3.Connection, pragma_name: str) -> str | int | None:
    """Get the current value of a PRAGMA setting.

    Args:
        conn: The SQLite connection to query.
        pragma_name: Name of the PRAGMA setting (e.g., "journal_mode").

    Returns:
        The current value of the PRAGMA, or None if it cannot be retrieved.

    Example:
        >>> with get_connection() as conn:
        ...     mode = get_pragma(conn, "journal_mode")
        ...     print(mode)  # 'wal'
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA {pragma_name}")
        result = cursor.fetchone()
        cursor.close()

        if result:
            return result[0]
        return None
    except sqlite3.OperationalError as e:
        logger.warning("Failed to get PRAGMA %s: %s", pragma_name, e)
        return None


def is_wal_mode(db_path: str | None = None) -> bool:
    """Check if the database is in WAL mode.

    Args:
        db_path: Path to the database file. If None, uses the default path.

    Returns:
        True if the database is in WAL mode, False otherwise.
    """
    try:
        with get_connection(db_path=db_path) as conn:
            mode = get_pragma(conn, "journal_mode")
            return isinstance(mode, str) and mode.lower() == "wal"
    except Exception:
        return False


def run_wal_checkpoint(db_path: str | None = None, mode: str = "TRUNCATE") -> bool:
    """Run a WAL checkpoint to merge the WAL file into the main database.

    This can be useful for:
        - Reducing WAL file size
        - Cleaning up after a crash
        - Preparing for backup

    Args:
        db_path: Path to the database file. If None, uses the default path.
        mode: Checkpoint mode (PASSIVE, TRUNCATE, RESET, FULL).

    Returns:
        True if the checkpoint succeeded, False otherwise.

    Example:
        >>> success = run_wal_checkpoint()
        >>> if success:
        ...     print("WAL checkpoint completed")
    """
    valid_modes = {"PASSIVE", "TRUNCATE", "RESET", "FULL"}
    if mode.upper() not in valid_modes:
        logger.warning("Invalid WAL checkpoint mode: %s", mode)
        return False

    try:
        with get_connection(db_path=db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA wal_checkpoint({mode})")
            result = cursor.fetchone()
            cursor.close()

            if result:
                # Returns (busy, log, checkpointed)
                busy, log, checkpointed = result
                logger.debug(
                    "WAL checkpoint: busy=%d, log=%d, checkpointed=%d",
                    busy, log, checkpointed
                )
            return True

    except Exception as e:
        logger.exception("WAL checkpoint failed: %s", e)
        return False
