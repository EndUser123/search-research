"""
TaskMaster Database Migration Base Class

Provides common migration functionality:
- Automatic backup before migration
- Migration tracking table
- Rollback support
- Validation hooks

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


class TaskMasterMigration:
    """Base class for TaskMaster database migrations."""

    def __init__(self, db_path: str):
        """Initialize migration.

        Args:
            db_path: Path to the TaskMaster database
        """
        self.db_path = Path(db_path)
        self.migration_version = "000"
        self.migration_name = "base"
        self.conn: sqlite3.Connection | None = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def backup_database(self) -> Path:
        """Create a backup of the database.

        Returns:
            Path to the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.db_path.parent.parent / "__csf" / "backups" / "taskmaster_migrations"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = backup_dir / f"{self.db_path.stem}_backup_{timestamp}{self.db_path.suffix}"
        shutil.copy2(self.db_path, backup_path)

        self.logger.info(f"Database backed up to: {backup_path}")
        return backup_path

    def create_migration_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        if not self.conn:
            raise RuntimeError("Not connected to database")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS taskmaster_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                backup_path TEXT
            )
        """)
        self.conn.commit()

    def check_migration_applied(self) -> bool:
        """Check if this migration has already been applied.

        Returns:
            True if migration already applied, False otherwise
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM taskmaster_migrations WHERE version = ? LIMIT 1",
            (self.migration_version,)
        )
        return cursor.fetchone() is not None

    def record_migration(self, backup_path: Path):
        """Record that this migration has been applied.

        Args:
            backup_path: Path to the database backup
        """
        if not self.conn:
            raise RuntimeError("Not connected to database")

        self.conn.execute(
            "INSERT INTO taskmaster_migrations (version, name, backup_path) VALUES (?, ?, ?)",
            (self.migration_version, self.migration_name, str(backup_path))
        )
        self.conn.commit()

    def rollback_migration(self) -> tuple[bool, str]:
        """Rollback this migration by restoring from backup.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get the backup path for this migration
            if not self.conn:
                self.connect()

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT backup_path FROM taskmaster_migrations WHERE version = ?",
                (self.migration_version,)
            )
            row = cursor.fetchone()

            if not row or not row["backup_path"]:
                return False, "No backup found for this migration"

            backup_path = Path(row["backup_path"])
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_path}"

            # Close connection before restoring
            self.close()

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)

            # Remove migration record
            self.connect()
            self.conn.execute(
                "DELETE FROM taskmaster_migrations WHERE version = ?",
                (self.migration_version,)
            )
            self.conn.commit()

            self.logger.info(f"Migration {self.migration_version} rolled back from {backup_path}")
            return True, f"Rollback complete. Restored from {backup_path}"

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False, f"Rollback failed: {str(e)}"
        finally:
            self.close()

    def execute_migration(self) -> tuple[bool, str]:
        """Execute the migration.

        Subclasses should override this method.

        Returns:
            Tuple of (success, message)
        """
        raise NotImplementedError("Subclasses must implement execute_migration()")
