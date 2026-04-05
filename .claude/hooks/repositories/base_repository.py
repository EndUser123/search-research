"""Base repository for project context management.

Ported from MCP Memory Keeper BaseRepository pattern.
Provides common database operations and utilities for all repositories.

Constitutional Requirements:
- Solo developer optimization (simple, direct implementation)
- Evidence-based operations (transaction support, proper error handling)
- Force multiplier (extensible base class for repositories)
- No enterprise bloat (no ORM, direct SQLite)
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar('T')

logger = logging.getLogger(__name__)


# Retry configuration for transient database errors
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 0.1  # 100ms initial delay


def _retry_sqlite_transient(max_retries: int = DEFAULT_MAX_RETRIES,
                             initial_delay: float = DEFAULT_RETRY_DELAY):
    """Decorator to retry SQLite operations on transient errors.

    Transient errors that trigger retry:
    - sqlite3.OperationalError: "database is locked", "disk I/O error"
    - sqlite3.DatabaseError: Temporary database issues

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds, doubled each retry (default: 0.1)

    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_error = e
                    # Retry on specific transient errors
                    error_msg = str(e).lower()
                    if any(msg in error_msg for msg in ("locked", "disk i/o error", "busy")):
                        if attempt < max_retries:
                            logger.debug(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                            time.sleep(delay)
                            delay *= 2  # Exponential backoff
                            continue
                    raise  # Re-raise if not transient or max retries exceeded
                except sqlite3.DatabaseError as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.debug(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                        time.sleep(delay)
                        delay *= 2
                        continue
                    raise

            # Should never reach here, but handle gracefully
            raise last_error  # type: ignore

        return wrapper
    return decorator


@dataclass
class RepositoryResult:
    """Standard result from repository operations."""
    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseRepository(ABC):
    """Abstract base class for project context repositories.

    Provides common database operations and utilities following the
    MCP Memory Keeper repository pattern.

    Time Complexity:
    - CRUD operations: O(1) for indexed queries
    - Batch operations: O(n) where n is batch size
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize repository with database path.

        Args:
            db_path: Path to CKS SQLite database
        """
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @_retry_sqlite_transient()
    def conn(self) -> sqlite3.Connection:
        """Get or create database connection with retry on transient errors."""
        if self._conn is None:
            # Ensure parent directory exists before opening database
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # Enable foreign keys
            self._conn.execute("PRAGMA foreign_keys = ON")
            self.logger.debug(f"Database connection opened: {self.db_path}")

            # Initialize schema if this is a new database
            if not db_file.exists() or db_file.stat().st_size == 0:
                self.initialize_schema()
        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self.logger.debug("Database connection closed")

    @contextlib.contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions.

        Usage:
            with self.transaction() as conn:
                # Multiple operations
                conn.execute(...)
                conn.execute(...)
                # Automatically commits or rolls back
        """
        try:
            yield self.conn
            self.conn.commit()
            self.logger.debug("Transaction committed")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Transaction rolled back: {e}")
            raise

    def _generate_id(self) -> str:
        """Generate unique ID using UUID4."""
        return str(uuid.uuid4())

    def _current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    def _calculate_size(self, value: str) -> int:
        """
        Calculate UTF-8 byte length of string value.

        Args:
            value: String to measure

        Returns:
            Byte length of UTF-8 encoded string
        """
        return len(value.encode('utf-8'))

    @_retry_sqlite_transient()
    def _execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False
    ) -> sqlite3.Row | list[sqlite3.Row] | None:
        """
        Execute a database query with error handling and retry on transient errors.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: If True, fetch one row; otherwise fetch all

        Returns:
            Row or list of rows, or None if error
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()

        except sqlite3.Error as e:
            self.logger.error(f"Query failed: {query} - Error: {e}")
            return None

    @abstractmethod
    def initialize_schema(self) -> bool:
        """
        Initialize repository schema tables.

        Returns:
            True if schema initialization successful, False otherwise
        """
        pass
