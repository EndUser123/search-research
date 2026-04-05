"""
Database sharding system for large Telegram channels.

This module implements the sharding strategy from LARGE_DATABASE_STRATEGY.md:
- Split large channels into multiple database files by date/size
- Each shard < 2GB for optimal SQLite performance
- Backward compatibility with existing single-database channels
"""

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger

from .schema import (
    CREATE_CHANNELS_TABLE,
    CREATE_DOWNLOAD_HISTORY_TABLE,
    CREATE_INDEXES,
    CREATE_MESSAGES_TABLE,
    CREATE_SCHEMA_VERSION_TABLE,
    CREATE_TRIGGERS,
    SCHEMA_VERSION,
    get_database_path,
    get_database_size_gb,
)

# Sharding Configuration
MAX_SHARD_SIZE_GB = 2.0  # Maximum size per shard (2GB)
SHARDING_THRESHOLD_GB = 5.0  # Start sharding when database exceeds 5GB
SHARD_TIME_PERIOD_MONTHS = 3  # Split by quarters (3 months each)


@dataclass
class ShardInfo:
    """Information about a database shard."""

    shard_name: str  # e.g., "db_2024_Q1", "db_current"
    file_path: str
    size_gb: float
    date_range: tuple[str, str] | None  # (start_date, end_date) or None for current
    is_current: bool  # True if this is the active shard for new messages
    message_count: int


class ShardManager:
    """Manages database sharding for a channel."""

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.channel_dir = Path("channels") / channel_name
        self.channel_dir.mkdir(parents=True, exist_ok=True)

    def should_shard_database(self) -> bool:
        """
        Check if the main database should be sharded.

        Returns:
            True if database exceeds sharding threshold
        """
        size_gb = get_database_size_gb(self.channel_name)
        return size_gb > SHARDING_THRESHOLD_GB

    def get_shard_list(self) -> list[ShardInfo]:
        """
        Get list of all shards for this channel.

        Returns:
            List of ShardInfo objects sorted by date
        """
        shards = []

        # Check for main database (legacy single file)
        main_db_path = get_database_path(self.channel_name)
        if os.path.exists(main_db_path):
            size_gb = get_database_size_gb(self.channel_name)
            shards.append(
                ShardInfo(
                    shard_name="telegram_data",
                    file_path=main_db_path,
                    size_gb=size_gb,
                    date_range=self._get_database_date_range(main_db_path),
                    is_current=True,  # Main DB is current until sharded
                    message_count=self._get_message_count(main_db_path),
                )
            )

        # Check for shard databases
        for shard_file in self.channel_dir.glob("db_*.db"):
            size_gb = os.path.getsize(shard_file) / (1024**3)
            shard_name = shard_file.stem
            is_current = shard_name == "db_current"

            shards.append(
                ShardInfo(
                    shard_name=shard_name,
                    file_path=str(shard_file),
                    size_gb=size_gb,
                    date_range=self._get_database_date_range(str(shard_file))
                    if not is_current
                    else None,
                    is_current=is_current,
                    message_count=self._get_message_count(str(shard_file)),
                )
            )

        # Sort by date (current shard goes last)
        shards.sort(key=lambda s: (s.is_current, s.shard_name))
        return shards

    def get_current_shard_path(self) -> str:
        """
        Get the path to the current active shard for new messages.

        Returns:
            Path to current shard database
        """
        shards = self.get_shard_list()

        # Find current shard
        for shard in shards:
            if shard.is_current:
                return shard.file_path

        # No current shard exists, create one
        return self._create_current_shard()

    def get_shard_for_date(self, message_date: datetime) -> str:
        """
        Get the appropriate shard for a message with given date.

        Args:
            message_date: Date of the message

        Returns:
            Path to the appropriate shard database
        """
        shards = self.get_shard_list()

        # Check existing shards for date range
        for shard in shards:
            if shard.date_range:
                start_date, end_date = shard.date_range
                if start_date <= message_date.isoformat() <= end_date:
                    return shard.file_path

        # No matching shard, use current shard
        return self.get_current_shard_path()

    def create_new_shard(self, shard_name: str) -> str:
        """
        Create a new database shard.

        Args:
            shard_name: Name of the new shard (e.g., "db_2024_Q1")

        Returns:
            Path to the created shard
        """
        shard_path = self.channel_dir / f"{shard_name}.db"

        try:
            with sqlite3.connect(str(shard_path)) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON;")

                # Create tables
                conn.execute(CREATE_CHANNELS_TABLE)
                conn.execute(CREATE_MESSAGES_TABLE)
                conn.execute(CREATE_DOWNLOAD_HISTORY_TABLE)
                conn.execute(CREATE_SCHEMA_VERSION_TABLE)

                # Create indexes
                for index_sql in CREATE_INDEXES:
                    conn.execute(index_sql)

                # Create triggers
                for trigger_sql in CREATE_TRIGGERS:
                    conn.execute(trigger_sql)

                # Record schema version
                conn.execute(
                    "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,),
                )

                conn.commit()
                logger.info(
                    f"Created new shard '{shard_name}' for channel '{self.channel_name}' at {shard_path}"
                )

        except sqlite3.Error as e:
            logger.error(
                f"Failed to create shard '{shard_name}' for channel '{self.channel_name}': {e}"
            )
            raise

        return str(shard_path)

    def needs_new_shard(self) -> bool:
        """
        Check if current shard needs to be archived and a new one created.

        Returns:
            True if current shard is too large
        """
        current_shard_path = self.get_current_shard_path()
        try:
            size_gb = os.path.getsize(current_shard_path) / (1024**3)
            return size_gb > MAX_SHARD_SIZE_GB
        except OSError:
            return False

    def _create_current_shard(self) -> str:
        """Create the current active shard."""
        return self.create_new_shard("db_current")

    def _get_database_date_range(self, db_path: str) -> tuple[str, str] | None:
        """Get the date range of messages in a database."""
        try:
            with sqlite3.connect(db_path, timeout=5.0) as conn:
                cursor = conn.execute(
                    "SELECT MIN(date), MAX(date) FROM messages WHERE date IS NOT NULL"
                )
                result = cursor.fetchone()
                return result if result and result[0] else None
        except sqlite3.Error:
            return None

    def _get_message_count(self, db_path: str) -> int:
        """Get the count of messages in a database."""
        try:
            with sqlite3.connect(db_path, timeout=5.0) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM messages")
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0

    def get_shard_summary(self) -> dict:
        """
        Get a summary of all shards for this channel.

        Returns:
            Dictionary with shard statistics
        """
        shards = self.get_shard_list()

        total_size_gb = sum(shard.size_gb for shard in shards)
        total_messages = sum(shard.message_count for shard in shards)

        return {
            "channel_name": self.channel_name,
            "total_shards": len(shards),
            "total_size_gb": round(total_size_gb, 2),
            "total_messages": total_messages,
            "is_sharded": len(shards) > 1
            or any(shard.shard_name != "telegram_data" for shard in shards),
            "needs_sharding": self.should_shard_database(),
            "shards": [
                {
                    "name": shard.shard_name,
                    "size_gb": round(shard.size_gb, 2),
                    "message_count": shard.message_count,
                    "date_range": shard.date_range,
                    "is_current": shard.is_current,
                }
                for shard in shards
            ],
        }


def get_shard_manager(channel_name: str) -> ShardManager:
    """
    Get a ShardManager instance for a channel.

    Args:
        channel_name: Name of the channel

    Returns:
        ShardManager instance
    """
    return ShardManager(channel_name)


def check_all_channels_sharding_status() -> list[dict]:
    """
    Check sharding status for all channels.

    Returns:
        List of channel sharding summaries
    """
    channels_dir = Path("channels")
    if not channels_dir.exists():
        return []

    summaries = []
    for channel_dir in channels_dir.iterdir():
        if channel_dir.is_dir():
            manager = ShardManager(channel_dir.name)
            summaries.append(manager.get_shard_summary())

    return summaries
