"""
Database migration tools for implementing sharding on existing large databases.

This module provides tools to:
1. Migrate existing large databases to sharded format
2. Archive old messages to separate databases
3. Perform database maintenance and optimization
"""

import os
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from .schema import get_database_path, get_database_size_gb
from .sharding import get_shard_manager


@dataclass
class MigrationResult:
    """Result of a database migration operation."""

    success: bool
    original_size_gb: float
    new_total_size_gb: float
    shards_created: int
    messages_migrated: int
    errors: list[str]
    backup_path: str | None = None


class DatabaseMigrator:
    """Handles migration of large databases to sharded format."""

    def __init__(self, channel_name: str, create_backup: bool = True):
        self.channel_name = channel_name
        self.create_backup = create_backup
        self.shard_manager = get_shard_manager(channel_name)
        self.original_db_path = get_database_path(channel_name)

    def should_migrate(self) -> bool:
        """
        Check if this database should be migrated.

        Returns:
            True if database is large enough to benefit from sharding
        """
        return self.shard_manager.should_shard_database()

    def create_backup(self) -> str | None:
        """
        Create a backup of the original database.

        Returns:
            Path to backup file or None if backup failed
        """
        if not os.path.exists(self.original_db_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.original_db_path}.backup_{timestamp}"

        try:
            shutil.copy2(self.original_db_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def migrate_to_sharded(self, shard_by_quarters: bool = True) -> MigrationResult:
        """
        Migrate existing database to sharded format.

        Args:
            shard_by_quarters: If True, create shards by quarters; otherwise by size

        Returns:
            MigrationResult with details of the migration
        """
        if not os.path.exists(self.original_db_path):
            return MigrationResult(
                success=False,
                original_size_gb=0.0,
                new_total_size_gb=0.0,
                shards_created=0,
                messages_migrated=0,
                errors=["Original database not found"],
            )

        original_size_gb = get_database_size_gb(self.channel_name)
        backup_path = None
        errors = []

        # Create backup if requested
        if self.create_backup:
            backup_path = self.create_backup()
            if not backup_path:
                errors.append("Failed to create backup")

        try:
            if shard_by_quarters:
                result = self._migrate_by_date_quarters()
            else:
                result = self._migrate_by_size()

            result.original_size_gb = original_size_gb
            result.backup_path = backup_path
            result.errors.extend(errors)

            return result

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return MigrationResult(
                success=False,
                original_size_gb=original_size_gb,
                new_total_size_gb=0.0,
                shards_created=0,
                messages_migrated=0,
                errors=errors + [str(e)],
                backup_path=backup_path,
            )

    def _migrate_by_date_quarters(self) -> MigrationResult:
        """Migrate database by splitting into quarterly shards."""
        shards_created = 0
        messages_migrated = 0
        errors = []

        # Get date range of messages
        with sqlite3.connect(self.original_db_path) as conn:
            cursor = conn.execute(
                "SELECT MIN(date), MAX(date), COUNT(*) FROM messages WHERE date IS NOT NULL"
            )
            min_date_str, max_date_str, total_messages = cursor.fetchone()

            if not min_date_str:
                return MigrationResult(
                    success=False,
                    original_size_gb=0.0,
                    new_total_size_gb=0.0,
                    shards_created=0,
                    messages_migrated=0,
                    errors=["No messages with dates found"],
                )

        # Parse dates
        try:
            min_date = datetime.fromisoformat(min_date_str.replace("Z", "+00:00"))
            max_date = datetime.fromisoformat(max_date_str.replace("Z", "+00:00"))
        except ValueError as e:
            return MigrationResult(
                success=False,
                original_size_gb=0.0,
                new_total_size_gb=0.0,
                shards_created=0,
                messages_migrated=0,
                errors=[f"Date parsing error: {e}"],
            )

        logger.info(
            f"Migrating {total_messages:,} messages from {min_date.date()} to {max_date.date()}"
        )

        # Generate quarterly periods
        quarters = self._generate_quarters(min_date, max_date)

        # Create shards for each quarter
        for i, (start_date, end_date) in enumerate(quarters):
            quarter_name = f"db_{start_date.year}_Q{((start_date.month - 1) // 3) + 1}"

            try:
                # Create the shard
                shard_path = self.shard_manager.create_new_shard(quarter_name)

                # Copy channel data
                self._copy_channel_data(shard_path)

                # Copy messages for this period
                messages_in_quarter = self._copy_messages_by_date(
                    shard_path, start_date, end_date
                )

                messages_migrated += messages_in_quarter
                shards_created += 1

                logger.info(
                    f"Created shard {quarter_name} with {messages_in_quarter:,} messages"
                )

            except Exception as e:
                error_msg = f"Failed to create shard {quarter_name}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Create current shard for recent messages (last 30 days)
        current_cutoff = max_date - timedelta(days=30)
        try:
            current_shard_path = self.shard_manager.create_new_shard("db_current")
            self._copy_channel_data(current_shard_path)
            recent_messages = self._copy_messages_by_date(
                current_shard_path, current_cutoff, max_date
            )
            messages_migrated += recent_messages
            shards_created += 1
            logger.info(
                f"Created current shard with {recent_messages:,} recent messages"
            )
        except Exception as e:
            errors.append(f"Failed to create current shard: {e}")

        # Calculate new total size
        shards = self.shard_manager.get_shard_list()
        new_total_size_gb = sum(shard.size_gb for shard in shards)

        return MigrationResult(
            success=len(errors) == 0,
            original_size_gb=0.0,  # Will be set by caller
            new_total_size_gb=new_total_size_gb,
            shards_created=shards_created,
            messages_migrated=messages_migrated,
            errors=errors,
        )

    def _migrate_by_size(self) -> MigrationResult:
        """Migrate database by splitting when shards reach size limit."""
        # This is a simpler approach - create sequential shards based on size
        # Implementation would be similar but based on row counts instead of dates
        return MigrationResult(
            success=False,
            original_size_gb=0.0,
            new_total_size_gb=0.0,
            shards_created=0,
            messages_migrated=0,
            errors=["Size-based migration not yet implemented"],
        )

    def _generate_quarters(
        self, start_date: datetime, end_date: datetime
    ) -> list[tuple[datetime, datetime]]:
        """Generate quarterly date ranges."""
        quarters = []
        current = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        while current <= end_date:
            # Calculate quarter boundaries
            quarter = ((current.month - 1) // 3) + 1
            quarter_start_month = (quarter - 1) * 3 + 1
            quarter_end_month = quarter * 3

            quarter_start = current.replace(month=quarter_start_month, day=1)

            if quarter_end_month == 12:
                quarter_end = current.replace(
                    year=current.year + 1, month=1, day=1
                ) - timedelta(seconds=1)
            else:
                quarter_end = current.replace(
                    month=quarter_end_month + 1, day=1
                ) - timedelta(seconds=1)

            quarters.append((quarter_start, quarter_end))

            # Move to next quarter
            if quarter_end_month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=quarter_end_month + 1)

        return quarters

    def _copy_channel_data(self, shard_path: str):
        """Copy channel metadata to a shard."""
        with sqlite3.connect(self.original_db_path) as source_conn:
            with sqlite3.connect(shard_path) as dest_conn:
                # Copy channels table
                cursor = source_conn.execute("SELECT * FROM channels")
                channels = cursor.fetchall()

                for channel in channels:
                    dest_conn.execute(
                        "INSERT OR REPLACE INTO channels (id, name, telegram_id, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        channel,
                    )

                dest_conn.commit()

    def _copy_messages_by_date(
        self, shard_path: str, start_date: datetime, end_date: datetime
    ) -> int:
        """Copy messages within date range to a shard."""
        with sqlite3.connect(self.original_db_path) as source_conn:
            with sqlite3.connect(shard_path) as dest_conn:
                # Copy messages
                cursor = source_conn.execute(
                    """
                    SELECT * FROM messages
                    WHERE date >= ? AND date <= ?
                    ORDER BY date
                """,
                    (start_date.isoformat(), end_date.isoformat()),
                )

                messages = cursor.fetchall()

                for message in messages:
                    dest_conn.execute(
                        """
                        INSERT OR REPLACE INTO messages
                        (id, telegram_id, channel_id, reply_to_message_id, date, text, media_type,
                         file_id, file_size, filename, download_status, download_path, error_message,
                         download_attempts, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        message,
                    )

                dest_conn.commit()
                return len(messages)


def migrate_channel(
    channel_name: str, create_backup: bool = True, dry_run: bool = False
) -> MigrationResult:
    """
    Migrate a channel's database to sharded format.

    Args:
        channel_name: Name of the channel to migrate
        create_backup: Whether to create a backup before migration
        dry_run: If True, only analyze what would be migrated

    Returns:
        MigrationResult with migration details
    """
    migrator = DatabaseMigrator(channel_name, create_backup)

    if not migrator.should_migrate():
        return MigrationResult(
            success=False,
            original_size_gb=get_database_size_gb(channel_name),
            new_total_size_gb=0.0,
            shards_created=0,
            messages_migrated=0,
            errors=["Database does not need migration (under 5GB)"],
        )

    if dry_run:
        # Return analysis without actually migrating
        size_gb = get_database_size_gb(channel_name)
        return MigrationResult(
            success=True,
            original_size_gb=size_gb,
            new_total_size_gb=size_gb,
            shards_created=0,
            messages_migrated=0,
            errors=[f"DRY RUN: Would migrate {size_gb:.1f}GB database"],
        )

    return migrator.migrate_to_sharded()


def get_migration_candidates() -> list[dict[str, Any]]:
    """
    Get list of channels that are candidates for migration.

    Returns:
        List of channel information dictionaries
    """
    candidates = []
    channels_dir = Path("channels")

    if not channels_dir.exists():
        return candidates

    for channel_dir in channels_dir.iterdir():
        if channel_dir.is_dir():
            channel_name = channel_dir.name
            size_gb = get_database_size_gb(channel_name)

            if size_gb > 5.0:  # Candidate for migration
                manager = get_shard_manager(channel_name)
                summary = manager.get_shard_summary()

                candidates.append(
                    {
                        "channel_name": channel_name,
                        "size_gb": size_gb,
                        "is_sharded": summary["is_sharded"],
                        "needs_migration": not summary["is_sharded"],
                        "message_count": summary["total_messages"],
                    }
                )

    return candidates
