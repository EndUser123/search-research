"""
Message archive strategy implementation.

This module implements Option 2 from LARGE_DATABASE_STRATEGY.md:
- Move old messages to read-only archive databases
- Keep recent 6 months in active database
- Archive older messages by year
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from .schema import get_database_path


class ArchiveManager:
    """Manages message archiving for a channel."""

    def __init__(self, channel_name: str, active_months: int = 6):
        self.channel_name = channel_name
        self.active_months = active_months  # Keep recent N months in active database
        self.channel_dir = Path("channels") / channel_name
        self.channel_dir.mkdir(parents=True, exist_ok=True)

    def should_archive(self) -> bool:
        """
        Check if channel should be archived.

        Returns:
            True if channel has messages older than active_months
        """
        db_path = get_database_path(self.channel_name)
        if not os.path.exists(db_path):
            return False

        cutoff_date = datetime.now() - timedelta(days=self.active_months * 30)

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE date < ?",
                    (cutoff_date.isoformat(),),
                )
                old_message_count = cursor.fetchone()[0]
                return old_message_count > 0
        except sqlite3.Error:
            return False

    def create_archive(self, year: int) -> str:
        """
        Create an archive database for a specific year.

        Args:
            year: Year to create archive for

        Returns:
            Path to created archive database
        """
        archive_path = self.channel_dir / f"archive_{year}.db"

        # Initialize archive database with same schema
        try:
            with sqlite3.connect(str(archive_path)) as conn:
                # Copy schema from main database
                main_db_path = get_database_path(self.channel_name)
                conn.execute(f"ATTACH DATABASE '{main_db_path}' AS main")

                # Copy schema
                schema_query = conn.execute(
                    "SELECT sql FROM main.sqlite_master WHERE type='table'"
                ).fetchall()

                for (sql,) in schema_query:
                    if sql:
                        conn.execute(sql)

                # Copy indexes and triggers
                for obj_type in ["index", "trigger"]:
                    objects = conn.execute(
                        f"SELECT sql FROM main.sqlite_master WHERE type='{obj_type}'"
                    ).fetchall()

                    for (sql,) in objects:
                        if sql and "sqlite_" not in sql:  # Skip system objects
                            try:
                                conn.execute(sql)
                            except sqlite3.Error:
                                pass  # Some objects might not be copyable

                conn.execute("DETACH DATABASE main")
                conn.commit()

                logger.info(f"Created archive database for {year}: {archive_path}")
                return str(archive_path)

        except sqlite3.Error as e:
            logger.error(f"Failed to create archive for {year}: {e}")
            raise

    def archive_messages_by_year(self, target_year: int) -> int:
        """
        Archive messages from a specific year.

        Args:
            target_year: Year to archive messages for

        Returns:
            Number of messages archived
        """
        main_db_path = get_database_path(self.channel_name)
        archive_path = self.create_archive(target_year)

        year_start = f"{target_year}-01-01"
        year_end = f"{target_year}-12-31 23:59:59"

        try:
            with sqlite3.connect(main_db_path) as main_conn:
                with sqlite3.connect(archive_path) as archive_conn:
                    # Copy channel metadata
                    channels = main_conn.execute("SELECT * FROM channels").fetchall()
                    for channel in channels:
                        archive_conn.execute(
                            "INSERT OR REPLACE INTO channels VALUES (?, ?, ?, ?, ?, ?)",
                            channel,
                        )

                    # Copy messages for the year
                    messages = main_conn.execute(
                        "SELECT * FROM messages WHERE date >= ? AND date <= ?",
                        (year_start, year_end),
                    ).fetchall()

                    for message in messages:
                        archive_conn.execute(
                            """INSERT OR REPLACE INTO messages
                               (id, telegram_id, channel_id, reply_to_message_id, date, text,
                                media_type, file_id, file_size, filename, download_status,
                                download_path, error_message, download_attempts, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            message,
                        )

                    # Copy download history
                    history_records = main_conn.execute(
                        """SELECT dh.* FROM download_history dh
                           JOIN messages m ON dh.message_id = m.id
                           WHERE m.date >= ? AND m.date <= ?""",
                        (year_start, year_end),
                    ).fetchall()

                    for record in history_records:
                        archive_conn.execute(
                            """INSERT OR REPLACE INTO download_history
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            record,
                        )

                    archive_conn.commit()

                    # Remove archived messages from main database
                    main_conn.execute(
                        "DELETE FROM messages WHERE date >= ? AND date <= ?",
                        (year_start, year_end),
                    )
                    main_conn.commit()

                    # Vacuum main database to reclaim space
                    main_conn.execute("VACUUM")

                    logger.info(
                        f"Archived {len(messages)} messages for year {target_year}"
                    )
                    return len(messages)

        except sqlite3.Error as e:
            logger.error(f"Failed to archive messages for {target_year}: {e}")
            raise

    def archive_old_messages(self) -> dict[str, Any]:
        """
        Archive messages older than active_months.

        Returns:
            Dictionary with archiving results
        """
        if not self.should_archive():
            return {
                "archived_years": [],
                "messages_archived": 0,
                "space_reclaimed_gb": 0.0,
                "success": True,
            }

        cutoff_date = datetime.now() - timedelta(days=self.active_months * 30)
        original_size_gb = os.path.getsize(get_database_path(self.channel_name)) / (
            1024**3
        )

        # Get years that need archiving
        db_path = get_database_path(self.channel_name)

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(
                    """SELECT DISTINCT strftime('%Y', date) as year
                       FROM messages
                       WHERE date < ? AND date IS NOT NULL
                       ORDER BY year""",
                    (cutoff_date.isoformat(),),
                )
                years_to_archive = [int(row[0]) for row in cursor.fetchall()]

            results = {
                "archived_years": [],
                "messages_archived": 0,
                "space_reclaimed_gb": 0.0,
                "success": True,
                "errors": [],
            }

            # Archive each year
            for year in years_to_archive:
                try:
                    messages_count = self.archive_messages_by_year(year)
                    results["archived_years"].append(year)
                    results["messages_archived"] += messages_count
                    logger.info(
                        f"Successfully archived {messages_count} messages for {year}"
                    )
                except Exception as e:
                    error_msg = f"Failed to archive year {year}: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Calculate space reclaimed
            new_size_gb = os.path.getsize(get_database_path(self.channel_name)) / (
                1024**3
            )
            results["space_reclaimed_gb"] = original_size_gb - new_size_gb

            logger.info(
                f"Archiving completed: {results['messages_archived']} messages archived, "
                f"{results['space_reclaimed_gb']:.1f}GB space reclaimed"
            )

            return results

        except Exception as e:
            logger.error(f"Archiving failed: {e}")
            return {
                "archived_years": [],
                "messages_archived": 0,
                "space_reclaimed_gb": 0.0,
                "success": False,
                "errors": [str(e)],
            }

    def list_archives(self) -> list[dict[str, Any]]:
        """
        List all archive databases for this channel.

        Returns:
            List of archive information dictionaries
        """
        archives = []

        for archive_file in self.channel_dir.glob("archive_*.db"):
            try:
                year = int(archive_file.stem.split("_")[1])
                size_gb = os.path.getsize(archive_file) / (1024**3)

                # Get message count
                with sqlite3.connect(str(archive_file)) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM messages")
                    message_count = cursor.fetchone()[0]

                archives.append(
                    {
                        "year": year,
                        "file_path": str(archive_file),
                        "size_gb": round(size_gb, 2),
                        "message_count": message_count,
                    }
                )

            except (ValueError, sqlite3.Error, OSError) as e:
                # Skip invalid archive files but log the issue
                logger.debug(f"Skipping invalid archive file {archive_file}: {e}")
                continue

        return sorted(archives, key=lambda x: x["year"])

    def get_archive_summary(self) -> dict[str, Any]:
        """
        Get summary of archiving status for this channel.

        Returns:
            Dictionary with archive summary
        """
        archives = self.list_archives()

        return {
            "channel_name": self.channel_name,
            "active_months": self.active_months,
            "should_archive": self.should_archive(),
            "archive_count": len(archives),
            "archives": archives,
            "total_archived_size_gb": sum(a["size_gb"] for a in archives),
            "total_archived_messages": sum(a["message_count"] for a in archives),
        }


def get_archive_manager(channel_name: str, active_months: int = 6) -> ArchiveManager:
    """
    Get an ArchiveManager instance for a channel.

    Args:
        channel_name: Name of the channel
        active_months: Number of months to keep in active database

    Returns:
        ArchiveManager instance
    """
    return ArchiveManager(channel_name, active_months)
