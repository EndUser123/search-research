"""
Database Query Logging for NFR-15 Comprehensive Logging.

Provides slow query logging and performance tracking for SQLite operations.
Logs queries that take longer than 100ms (NFR-15 AC.15.4).

Example:
    from .db_logging import logged_query, log_slow_query

    # Use context manager for automatic logging
    with logged_query("get_channel_videos", "SELECT * FROM Videos WHERE channel_id = ?"):
        results = cursor.execute(query, (channel_id,))

    # Or log manually
    log_slow_query("get_channel_videos", 250.5, row_count=150)
"""
from __future__ import annotations

import logging
import sqlite3
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

from .dual_sink_logger import get_logger, log_operation

logger = get_logger(__name__)

# Slow query threshold in milliseconds (NFR-15 AC.15.4)
SLOW_QUERY_THRESHOLD_MS = 100


@contextmanager
def logged_query(operation: str, sql: str | None = None, **context: Any) -> Generator[None, None, None]:
    """
    Context manager for logging database queries with timing.

    Logs all queries, and highlights slow queries (>100ms) as warnings.

    Args:
        operation: Operation name (e.g., "get_channel_videos", "add_subtitle")
        sql: SQL query (will be truncated if very long)
        **context: Additional context (table, row_count, etc.)

    Yields:
        None

    Example:
        with logged_query("get_channel", "SELECT * FROM Channels WHERE channel_id = ?", channel_id="UC..."):
            result = cursor.execute(query, (channel_id,))
    """
    start_time = time.time()

    # Sanitize SQL for logging (truncate long queries)
    sanitized_sql = None
    if sql:
        sanitized_sql = sql[:500] if len(sql) > 500 else sql

    log_operation(
        f"db.{operation}",
        f"Database query {operation} starting",
        level=logging.DEBUG,

        sql=sanitized_sql,
        **context
    )

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000

        # Determine log level based on duration
        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            log_level = logging.WARNING
            message = f"Slow database query {operation} ({duration_ms:.1f}ms)"
        else:
            log_level = logging.DEBUG
            message = f"Database query {operation} completed"

        log_operation(
            f"db.{operation}",
            message,
            level=log_level,

            duration_ms=round(duration_ms, 2),
            sql=sanitized_sql,
            slow=(duration_ms > SLOW_QUERY_THRESHOLD_MS),
            **context
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        log_operation(
            f"db.{operation}",
            f"Database query {operation} failed",
            level=logging.ERROR,

            duration_ms=round(duration_ms, 2),
            sql=sanitized_sql,
            error_type=type(e).__name__,
            error_message=str(e)[:200],
            **context
        )
        raise


def log_slow_query(
    operation: str,
    duration_ms: float,
    sql: str | None = None,
    row_count: int | None = None,
    **context: Any) -> None:
    """
    Log a slow database query (NFR-15 AC.15.4).

    Args:
        operation: Operation name
        duration_ms: Query execution time in milliseconds
        sql: SQL query (optional, will be truncated)
        row_count: Number of rows returned/affected (optional)
        **context: Additional context
    """
    sanitized_sql = None
    if sql:
        sanitized_sql = sql[:500] if len(sql) > 500 else sql

    log_operation(
        "db.slow_query",
        f"Slow database query detected: {operation} ({duration_ms:.1f}ms)",
        level=logging.WARNING,

        duration_ms=round(duration_ms, 2),
        sql=sanitized_sql,
        row_count=row_count,
        **context
    )


class LoggedConnection(sqlite3.Connection):
    """
    SQLite Connection subclass that automatically logs slow queries.

    Wraps execute() and executemany() to track query performance.

    Example:
        conn = sqlite3.connect(db_path, factory=LoggedConnection)
        conn.set_operation_name("get_channel")  # Optional: set operation name
        cursor = conn.execute("SELECT * FROM Videos WHERE channel_id = ?", (channel_id,))
    """

    _operation_name: str | None = None

    def set_operation_name(self, name: str, **context: Any) -> None:
        """Set the operation name for logging subsequent queries."""
        self._operation_name = name

    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:
        """Execute SQL with automatic slow query logging."""
        start_time = time.time()

        try:
            cursor = super().execute(sql, parameters)
            duration_ms = (time.time() - start_time) * 1000

            # Log if slow
            if duration_ms > SLOW_QUERY_THRESHOLD_MS:
                sanitized_sql = sql[:500] if len(sql) > 500 else sql
                log_operation(
                    "db.slow_query",
                    f"Slow query detected ({duration_ms:.1f}ms)",
                    level=logging.WARNING,
                    db_operation=self._operation_name or "execute",
                    duration_ms=round(duration_ms, 2),
                    sql=sanitized_sql,
                )

            return cursor

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_operation(
                "db.error",
                f"Query failed: {type(e).__name__}",
                level=logging.ERROR,
                db_operation=self._operation_name or "execute",
                duration_ms=round(duration_ms, 2),
                sql=sql[:500] if len(sql) > 500 else sql,
                error_message=str(e)[:200],
            )
            raise

    def executemany(self, sql: str, parameters: Any) -> sqlite3.Cursor:
        """Execute many SQL statements with batch logging."""
        start_time = time.time()
        param_count = len(parameters) if parameters else 0

        try:
            cursor = super().executemany(sql, parameters)
            duration_ms = (time.time() - start_time) * 1000

            # Log batch operations
            log_operation(
                "db.batch",
                f"Batch executed {param_count} statements",
                level=logging.DEBUG,
                db_operation=self._operation_name or "executemany",
                duration_ms=round(duration_ms, 2),
                statement_count=param_count,
                sql=sql[:500] if len(sql) > 500 else sql,
            )

            # Warn if slow batch
            if duration_ms > SLOW_QUERY_THRESHOLD_MS:
                log_operation(
                    "db.slow_batch",
                    f"Slow batch operation ({duration_ms:.1f}ms for {param_count} statements)",
                    level=logging.WARNING,
                    db_operation=self._operation_name or "executemany",
                    duration_ms=round(duration_ms, 2),
                    statement_count=param_count,
                )

            return cursor

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_operation(
                "db.batch_error",
                f"Batch failed: {type(e).__name__}",
                level=logging.ERROR,
                db_operation=self._operation_name or "executemany",
                duration_ms=round(duration_ms, 2),
                statement_count=param_count,
                error_message=str(e)[:200],
            )
            raise


def logged_cursor_execute(operation: str) -> Callable[..., Any]:
    """
    Decorator to add query logging to cursor execute methods.

    Args:
        operation: Operation name for logging

    Returns:
        Decorator function

    Example:
        @logged_cursor_execute("get_channel_videos")
        def get_videos(channel_id: str) -> list:
            cursor = conn.cursor()
            return cursor.execute("SELECT * FROM Videos WHERE channel_id = ?", (channel_id,))
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator function that wraps the target function.

        Args:
            func: Function to wrap with query logging

        Returns:
            Wrapped function with logging capability
        """
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function that logs query execution time.

            Args:
                *args: Positional arguments to the wrapped function
                **kwargs: Keyword arguments to the wrapped function

            Returns:
                Result from the wrapped function

            Raises:
                Exception: Re-raises any exception from wrapped function
            """
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                if duration_ms > SLOW_QUERY_THRESHOLD_MS:
                    log_operation(
                        "db.slow_query",
                        f"Slow operation: {operation} ({duration_ms:.1f}ms)",
                        level=logging.WARNING,

                        duration_ms=round(duration_ms, 2),
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_operation(
                    "db.error",
                    f"Operation failed: {operation}",
                    level=logging.ERROR,

                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],
                )
                raise

        return wrapper
    return decorator


def get_db_performance_stats() -> dict[str, Any]:
    """
    Get database performance statistics.

    Returns:
        Dict with slow_query_count, total_queries, etc.
    """
    # This would be populated by a stats collector in a full implementation
    # For now, return a placeholder
    return {
        "slow_query_threshold_ms": SLOW_QUERY_THRESHOLD_MS,
        "stats_collection": "pending",
    }
