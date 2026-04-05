"""
Sharding-aware database storage system.

This module provides a unified interface for database operations that
transparently handles both single-database and sharded configurations.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from loguru import logger

from .schema import (
    calculate_optimal_sqlite_settings,
    get_database_size_gb,
)
from .sharding import get_shard_manager


class ShardedStorage:
    """
    Sharding-aware database storage interface.

    Provides transparent access to both single-database and sharded channels,
    automatically routing queries to appropriate shards.
    """

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.shard_manager = get_shard_manager(channel_name)

    @contextmanager
    def get_connection(self, for_date: datetime | None = None):
        """
        Get database connection, automatically selecting appropriate shard.

        Args:
            for_date: Optional date to select shard for (uses current shard if None)

        Yields:
            SQLite connection to appropriate shard
        """
        if for_date:
            shard_path = self.shard_manager.get_shard_for_date(for_date)
        else:
            shard_path = self.shard_manager.get_current_shard_path()

        # Apply optimal settings based on shard size
        conn = sqlite3.connect(shard_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")

        # Apply size-based optimizations
        size_gb = get_database_size_gb(
            self.channel_name
        )  # TODO: Get specific shard size
        optimal_settings = calculate_optimal_sqlite_settings(size_gb)

        conn.execute(f"PRAGMA busy_timeout = {optimal_settings['busy_timeout']};")
        conn.execute(f"PRAGMA cache_size = {optimal_settings['cache_size']};")

        if optimal_settings["mmap_size"] > 0:
            conn.execute(f"PRAGMA mmap_size = {optimal_settings['mmap_size']};")

        try:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        except sqlite3.Error:
            pass  # Not critical if checkpoint fails

        try:
            yield conn
        finally:
            conn.close()

    def insert_message(self, message_data: dict[str, Any]) -> int:
        """
        Insert a message into the appropriate shard.

        Args:
            message_data: Message data dictionary

        Returns:
            ID of inserted message
        """
        message_date = None
        if "date" in message_data and message_data["date"]:
            if isinstance(message_data["date"], str):
                try:
                    message_date = datetime.fromisoformat(
                        message_data["date"].replace("Z", "+00:00")
                    )
                except ValueError as e:
                    # Failed to parse date, use None (current shard)
                    logger.debug(f"Failed to parse message date: {e}")
                    pass
            elif isinstance(message_data["date"], datetime):
                message_date = message_data["date"]

        with self.get_connection(for_date=message_date) as conn:
            # Prepare INSERT statement
            columns = ", ".join(message_data.keys())
            placeholders = ", ".join(["?" for _ in message_data])

            query = (
                f"INSERT OR REPLACE INTO messages ({columns}) VALUES ({placeholders})"
            )
            cursor = conn.execute(query, list(message_data.values()))
            conn.commit()

            return cursor.lastrowid

    def get_messages(
        self,
        limit: int | None = None,
        offset: int = 0,
        where_clause: str = "",
        params: list | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get messages from all shards, ordered by date.

        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            where_clause: WHERE clause (without WHERE keyword)
            params: Parameters for WHERE clause

        Returns:
            List of message dictionaries
        """
        all_messages = []
        shards = self.shard_manager.get_shard_list()

        # Query all shards
        for shard in shards:
            try:
                with sqlite3.connect(shard.file_path) as conn:
                    conn.row_factory = sqlite3.Row

                    query = "SELECT * FROM messages"
                    if where_clause:
                        query += f" WHERE {where_clause}"
                    query += " ORDER BY date DESC"

                    cursor = conn.execute(query, params or [])
                    shard_messages = [dict(row) for row in cursor.fetchall()]
                    all_messages.extend(shard_messages)

            except sqlite3.Error as e:
                logger.error(f"Error querying shard {shard.shard_name}: {e}")
                continue

        # Sort all messages by date (most recent first)
        all_messages.sort(key=lambda m: m.get("date", ""), reverse=True)

        # Apply offset and limit
        start_idx = offset
        end_idx = start_idx + limit if limit else len(all_messages)

        return all_messages[start_idx:end_idx]

    def get_pending_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get pending messages from all shards.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of pending message dictionaries
        """
        return self.get_messages(
            limit=limit, where_clause="download_status = 'pending'", params=[]
        )

    def update_message_status(
        self, message_id: int, status: str, error_message: str = None
    ) -> bool:
        """
        Update message download status across all shards.

        Args:
            message_id: Telegram message ID
            status: New download status
            error_message: Optional error message

        Returns:
            True if message was found and updated
        """
        shards = self.shard_manager.get_shard_list()

        for shard in shards:
            try:
                with sqlite3.connect(shard.file_path) as conn:
                    query = "UPDATE messages SET download_status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?"
                    cursor = conn.execute(query, [status, error_message, message_id])
                    conn.commit()

                    if cursor.rowcount > 0:
                        return True

            except sqlite3.Error as e:
                logger.error(
                    f"Error updating message {message_id} in shard {shard.shard_name}: {e}"
                )
                continue

        return False

    def get_channel_stats(self) -> dict[str, Any]:
        """
        Get comprehensive channel statistics across all shards.

        Returns:
            Dictionary with channel statistics
        """
        stats = {
            "total_messages": 0,
            "completed_downloads": 0,
            "pending_downloads": 0,
            "failed_downloads": 0,
            "total_size_gb": 0.0,
            "shards": [],
        }

        shards = self.shard_manager.get_shard_list()

        for shard in shards:
            try:
                with sqlite3.connect(shard.file_path) as conn:
                    conn.row_factory = sqlite3.Row

                    # Get message counts by status
                    cursor = conn.execute(
                        """
                        SELECT download_status, COUNT(*) as count
                        FROM messages
                        GROUP BY download_status
                    """
                    )

                    shard_stats = {"name": shard.shard_name, "size_gb": shard.size_gb}

                    for row in cursor.fetchall():
                        status, count = row["download_status"], row["count"]
                        stats["total_messages"] += count

                        if status == "completed":
                            stats["completed_downloads"] += count
                        elif status == "pending":
                            stats["pending_downloads"] += count
                        elif status in ["failed", "error"]:
                            stats["failed_downloads"] += count

                    stats["total_size_gb"] += shard.size_gb
                    stats["shards"].append(shard_stats)

            except sqlite3.Error as e:
                logger.error(f"Error getting stats for shard {shard.shard_name}: {e}")
                continue

        return stats

    def check_sharding_needed(self) -> bool:
        """
        Check if database needs to be sharded or needs a new shard.

        Returns:
            True if sharding action is needed
        """
        return (
            self.shard_manager.should_shard_database()
            or self.shard_manager.needs_new_shard()
        )


def get_sharded_storage(channel_name: str) -> ShardedStorage:
    """
    Get a ShardedStorage instance for a channel.

    Args:
        channel_name: Name of the channel

    Returns:
        ShardedStorage instance
    """
    return ShardedStorage(channel_name)


# Backward compatibility functions
def get_sharded_connection(channel_name: str, for_date: datetime | None = None):
    """
    Get database connection with sharding support (backward compatibility).

    Args:
        channel_name: Name of the channel
        for_date: Optional date to select shard for

    Returns:
        Context manager for database connection
    """
    storage = get_sharded_storage(channel_name)
    return storage.get_connection(for_date=for_date)
