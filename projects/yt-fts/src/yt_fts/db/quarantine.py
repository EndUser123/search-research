"""Quarantine system for safer channel cleanup workflow.

Moves suspicious entries to quarantine instead of deleting immediately.
Requires explicit confirmation before permanent deletion.
"""

import sqlite3
from datetime import datetime


class QuarantineSystem:
    """Manages quarantined channel entries with audit trail."""

    def __init__(self, db_path: str):
        """Initialize the quarantine system.

        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize quarantine and log tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create channels_quarantine table (same schema as channels)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels_quarantine (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                channel_url TEXT,
                api_total_video_count INTEGER,
                api_total_last_checked TEXT,
                quarantine_date TEXT,
                reason TEXT,
                quarantined_by TEXT
            )
        """)

        # Create deletion_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deletion_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT,
                channel_name TEXT,
                reason TEXT,
                deleted_date TEXT,
                deleted_by TEXT,
                restored_date TEXT,
                restored_by TEXT
            )
        """)

        conn.commit()
        conn.close()

    def quarantine_channel(
        self,
        channel_id: str,
        reason: str,
        quarantined_by: str = "system"
    ) -> bool:
        """Move a channel to quarantine.

        Args:
            channel_id: The channel_id to quarantine
            reason: Why this entry is being quarantined
            quarantined_by: Who/what is quarantining this entry

        Returns:
            True if successful, False if channel not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get the entry from main table
        cursor.execute(
            "SELECT * FROM channels WHERE channel_id = ?",
            (channel_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        # Move to quarantine table
        quarantine_date = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO channels_quarantine
               (channel_id, channel_name, channel_url, api_total_video_count,
                api_total_last_checked, quarantine_date, reason, quarantined_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (*row, quarantine_date, reason, quarantined_by)
        )

        # Delete from main table
        cursor.execute(
            "DELETE FROM channels WHERE channel_id = ?",
            (channel_id,)
        )

        # Log the action
        cursor.execute(
            """INSERT INTO deletion_log
               (channel_id, channel_name, reason, deleted_date, deleted_by)
               VALUES (?, ?, ?, ?, ?)""",
            (row[0], row[1], reason, quarantine_date, quarantined_by)
        )

        conn.commit()
        conn.close()
        return True

    def list_quarantined(self) -> list[dict]:
        """List all quarantined entries.

        Returns:
            List of dicts with quarantined channel info
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT channel_id, channel_name, channel_url,
                   quarantine_date, reason, quarantined_by
            FROM channels_quarantine
            ORDER BY quarantine_date DESC
        """)

        entries = []
        for row in cursor.fetchall():
            entries.append({
                "channel_id": row[0],
                "channel_name": row[1],
                "channel_url": row[2],
                "quarantine_date": row[3],
                "reason": row[4],
                "quarantined_by": row[5]
            })

        conn.close()
        return entries

    def restore_channel(self, channel_id: str, restored_by: str = "user") -> bool:
        """Restore a quarantined channel back to main table.

        Args:
            channel_id: The channel_id to restore
            restored_by: Who is restoring this entry

        Returns:
            True if successful, False if not found in quarantine
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get from quarantine
        cursor.execute(
            "SELECT * FROM channels_quarantine WHERE channel_id = ?",
            (channel_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        # Insert back into main table (exclude quarantine-specific fields)
        cursor.execute(
            """INSERT INTO channels
               (channel_id, channel_name, channel_url, api_total_video_count, api_total_last_checked)
               VALUES (?, ?, ?, ?, ?)""",
            (row[0], row[1], row[2], row[3], row[4])
        )

        # Remove from quarantine
        cursor.execute(
            "DELETE FROM channels_quarantine WHERE channel_id = ?",
            (channel_id,)
        )

        # Update deletion log
        restored_date = datetime.now().isoformat()
        cursor.execute(
            """UPDATE deletion_log
               SET restored_date = ?, restored_by = ?
               WHERE channel_id = ? AND restored_date IS NULL""",
            (restored_date, restored_by, channel_id)
        )

        conn.commit()
        conn.close()
        return True

    def permanent_delete(self, channel_id: str, confirmed: bool = False) -> bool:
        """Permanently delete a quarantined entry.

        Args:
            channel_id: The channel_id to permanently delete
            confirmed: Must be True to actually delete (safety check)

        Returns:
            True if deleted, False if not confirmed or not found
        """
        if not confirmed:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if in quarantine
        cursor.execute(
            "SELECT channel_id FROM channels_quarantine WHERE channel_id = ?",
            (channel_id,)
        )
        if not cursor.fetchone():
            conn.close()
            return False

        # Delete from quarantine
        cursor.execute(
            "DELETE FROM channels_quarantine WHERE channel_id = ?",
            (channel_id,)
        )

        conn.commit()
        conn.close()
        return True

    def get_stats(self) -> dict:
        """Get statistics about quarantined entries.

        Returns:
            Dict with quarantine statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count quarantined
        cursor.execute("SELECT COUNT(*) FROM channels_quarantine")
        quarantined_count = cursor.fetchone()[0]

        # Count in main table
        cursor.execute("SELECT COUNT(*) FROM channels")
        main_table_count = cursor.fetchone()[0]

        # Count permanently deleted (log entries with no restore date)
        cursor.execute("""
            SELECT COUNT(*) FROM deletion_log
            WHERE restored_date IS NULL
        """)
        deleted_count = cursor.fetchone()[0]

        # Count restored
        cursor.execute("""
            SELECT COUNT(*) FROM deletion_log
            WHERE restored_date IS NOT NULL
        """)
        restored_count = cursor.fetchone()[0]

        conn.close()

        return {
            "quarantined_count": quarantined_count,
            "main_table_count": main_table_count,
            "permanently_deleted_count": deleted_count,
            "restored_count": restored_count
        }
