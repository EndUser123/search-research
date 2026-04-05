"""
Database Inconsistency Logger and Auto-Repair System.

This module provides comprehensive logging and automated repair capabilities
for database inconsistencies detected during batch downloads.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class InconsistencyLogger:
    """Logs database inconsistencies for analysis and repair."""

    def __init__(self, db_path: str | None = None):
        """Initialize the inconsistency logger."""
        if db_path is None:
            from yt_fts.utils.config import get_db_path

            db_path = get_db_path()

        self.db_path = db_path
        self._init_tables()

    def _init_tables(self) -> None:
        """Initialize database tables for inconsistency tracking."""
        try:
            # Use longer timeout for Windows compatibility
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Enable WAL mode for concurrent read/write access (Windows compatibility)
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")

            # Create inconsistency log table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS db_inconsistencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    channel_name TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    inconsistency_type TEXT NOT NULL,
                    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
                    details TEXT,
                    stats_before TEXT,
                    stats_after TEXT,
                    auto_repaired BOOLEAN DEFAULT FALSE,
                    repair_action TEXT,
                    resolved_at TIMESTAMP,
                    notes TEXT
                )
            """
            )

            # Create inconsistency summary table for metrics
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS inconsistency_summary (
                    date TEXT PRIMARY KEY,
                    total_detected INTEGER DEFAULT 0,
                    auto_repaired INTEGER DEFAULT 0,
                    manual_repairs_needed INTEGER DEFAULT 0,
                    unresolved INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.exception(f"Failed to initialize inconsistency tables: {e}")

    def log_inconsistency(
        self,
        channel_id: str,
        channel_name: str | None,
        inconsistency_type: str,
        severity: str,
        details: str,
        stats: dict[str, Any],
    ) -> int:
        """Log a detected database inconsistency."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Insert inconsistency record
            cursor.execute(
                """
                INSERT INTO db_inconsistencies
                (channel_id, channel_name, inconsistency_type, severity, details, stats_before)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    channel_id,
                    channel_name,
                    inconsistency_type,
                    severity,
                    details,
                    json.dumps(stats),
                ),
            )

            inconsistency_id = cursor.lastrowid

            # Update summary for today
            today = datetime.now().strftime("%Y-%m-%d")
            # Use INSERT ... ON CONFLICT for proper upsert
            cursor.execute(
                """
                INSERT INTO inconsistency_summary (date, total_detected, updated_at)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(date) DO UPDATE SET
                    total_detected = total_detected + 1,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (today,),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Logged inconsistency ID {inconsistency_id}: {inconsistency_type} for {channel_name or channel_id}"
            )
            return inconsistency_id

        except Exception as e:
            logger.exception(f"Failed to log inconsistency: {e}")
            return -1

    def log_repair_attempt(
        self,
        inconsistency_id: int,
        repair_action: str,
        success: bool,
        notes: str | None = None,
    ) -> None:
        """Log the result of an auto-repair attempt."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            if success:
                cursor.execute(
                    """
                    UPDATE db_inconsistencies
                    SET auto_repaired = TRUE, repair_action = ?, resolved_at = CURRENT_TIMESTAMP, notes = ?
                    WHERE id = ?
                """,
                    (repair_action, notes, inconsistency_id),
                )

                # Update summary
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute(
                    """
                    UPDATE inconsistency_summary
                    SET auto_repaired = auto_repaired + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?
                """,
                    (today,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE db_inconsistencies
                    SET repair_action = ?, notes = ?
                    WHERE id = ?
                """,
                    (f"FAILED: {repair_action}", notes, inconsistency_id),
                )

            conn.commit()
            conn.close()

            logger.info(
                f"Logged repair {'success' if success else 'failure'} for inconsistency {inconsistency_id}"
            )

        except Exception as e:
            logger.exception(f"Failed to log repair attempt: {e}")

    def get_inconsistency_stats(self, days: int = 30) -> dict[str, Any]:
        """Get inconsistency statistics for analysis."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Get recent inconsistencies
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN auto_repaired THEN 1 ELSE 0 END) as auto_repaired,
                    SUM(CASE WHEN resolved_at IS NOT NULL THEN 1 ELSE 0 END) as resolved,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high
                FROM db_inconsistencies
                WHERE detected_at >= datetime('now', '-{days} days')
            """
            )

            stats = cursor.fetchone()
            conn.close()

            return {
                "total_inconsistencies": stats[0] or 0,
                "auto_repaired": stats[1] or 0,
                "manually_resolved": stats[2] or 0,
                "critical_issues": stats[3] or 0,
                "high_priority": stats[4] or 0,
                "period_days": days,
            }

        except Exception as e:
            logger.exception(f"Failed to get inconsistency stats: {e}")
            return {}

    def get_unresolved_inconsistencies(self) -> list[dict[str, Any]]:
        """Get list of unresolved inconsistencies for manual review."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, channel_id, channel_name, detected_at, inconsistency_type,
                       severity, details, stats_before
                FROM db_inconsistencies
                WHERE resolved_at IS NULL
                ORDER BY detected_at DESC
            """
            )

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "id": row[0],
                    "channel_id": row[1],
                    "channel_name": row[2],
                    "detected_at": row[3],
                    "type": row[4],
                    "severity": row[5],
                    "details": row[6],
                    "stats": json.loads(row[7]) if row[7] else {},
                }
                for row in rows
            ]

        except Exception as e:
            logger.exception(f"Failed to get unresolved inconsistencies: {e}")
            return []


class AutoRepairManager:
    """Automatically repairs common database inconsistencies."""

    def __init__(self, logger: InconsistencyLogger):
        """Initialize the auto-repair manager."""
        self.logger = logger

    def attempt_repair(
        self, inconsistency_id: int, inconsistency_data: dict[str, Any]
    ) -> bool:
        """Attempt to automatically repair a database inconsistency."""
        inconsistency_type = inconsistency_data.get("type", "")

        if "gap" in inconsistency_type.lower():
            return self._repair_video_gap(inconsistency_id, inconsistency_data)
        if "count" in inconsistency_type.lower():
            return self._repair_count_mismatch(inconsistency_id, inconsistency_data)
        # Unknown inconsistency type - cannot auto-repair
        self.logger.log_repair_attempt(
            inconsistency_id,
            "Unknown inconsistency type - manual review required",
            False,
            "Auto-repair not implemented for this inconsistency type",
        )
        return False

    def _repair_video_gap(self, inconsistency_id: int, data: dict[str, Any]) -> bool:
        """Repair gaps in video sequences by fetching missing videos."""
        try:
            channel_id = data.get("channel_id")
            if not channel_id:
                return False

            # Use YouTube API to fetch complete video list
            from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

            backfill = YouTubeAPIBackfill()
            videos_data = backfill.fetch_all_videos_from_channel(channel_id)

            if videos_data:
                from yt_fts.core.database import add_videos_bulk

                added_count = add_videos_bulk(channel_id, videos_data)

                self.logger.log_repair_attempt(
                    inconsistency_id,
                    f"Fetched {len(videos_data)} videos, added {added_count} missing videos",
                    True,
                    f"Gap repair successful: {added_count} videos added",
                )
                return True
            self.logger.log_repair_attempt(
                inconsistency_id,
                "Failed to fetch videos from YouTube API",
                False,
                "YouTube API returned no videos",
            )
            return False

        except Exception as e:
            self.logger.log_repair_attempt(
                inconsistency_id, f"Exception during gap repair: {e}", False, str(e)
            )
            return False

    def _repair_count_mismatch(
        self, inconsistency_id: int, data: dict[str, Any]
    ) -> bool:
        """Repair count mismatches by recalculating statistics."""
        try:
            channel_id = data.get("channel_id")
            if not channel_id:
                return False

            # Recalculate and update channel statistics
            from yt_fts.core.database import get_channel_stats, update_channel_stats

            # Force recalculation of stats
            update_channel_stats(channel_id)

            # Verify the repair
            new_stats = get_channel_stats(channel_id)
            old_stats = data.get("stats", {})

            # Check if the inconsistency is resolved
            if self._verify_count_consistency(new_stats):
                self.logger.log_repair_attempt(
                    inconsistency_id,
                    "Recalculated channel statistics",
                    True,
                    f"Stats updated: {old_stats} -> {new_stats}",
                )
                return True
            self.logger.log_repair_attempt(
                inconsistency_id,
                "Statistics recalculation did not resolve inconsistency",
                False,
                f"Stats after repair: {new_stats}",
            )
            return False

        except Exception as e:
            self.logger.log_repair_attempt(
                inconsistency_id, f"Exception during count repair: {e}", False, str(e)
            )
            return False

    def _verify_count_consistency(self, stats: dict[str, Any]) -> bool:
        """Verify that channel statistics are internally consistent."""
        total = stats.get("total", 0)
        with_subs = stats.get("with_transcripts", 0)
        scheduled = stats.get("scheduled", 0)
        members = stats.get("members_only", 0)
        unavailable = stats.get("unavailable", 0)
        shorts = stats.get("shorts", 0)

        # Basic consistency checks
        if (
            with_subs > total
            or scheduled > total
            or unavailable > total
            or shorts > total
            or members > total
        ):
            return False

        # Check if special categories account for all videos
        special_total = scheduled + unavailable + members + stats.get("no_subs", 0)
        unexplained_gap = total - with_subs

        # Allow some tolerance for rounding/processing errors
        return unexplained_gap >= special_total - 2  # Small tolerance for edge cases
