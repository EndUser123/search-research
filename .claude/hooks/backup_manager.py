"""
BackupManager - Generic backup rotation and restoration system.

Provides file backup rotation with configurable generations, supporting
backup discovery and restoration for any file type.
"""

import shutil
from pathlib import Path


class BackupManager:
    """
    Manages backup file rotation and restoration.

    Maintains a configurable number of backup generations (.1, .2, .3, etc.)
    with automatic rotation and removal of oldest backups.

    Attributes:
        primary_path: Path to the primary file being backed up
        count: Number of backup generations to maintain
    """

    def __init__(self, primary_path: Path, count: int) -> None:
        """
        Initialize BackupManager.

        Args:
            primary_path: Path to the primary file (e.g., "evidence.db")
            count: Number of backup generations to keep
        """
        self.primary_path = primary_path
        self.count = count

    def _backup_path(self, generation: int) -> Path:
        """Return the backup path for a specific generation number."""
        return self.primary_path.with_suffix(f"{self.primary_path.suffix}.{generation}")

    def rotate_backups(self) -> None:
        """
        Rotate backup files (primary -> .1, .1 -> .2, .2 -> .3, etc.).

        Rotation sequence (for count=3):
        1. Remove oldest (.3) if it exists
        2. .2 -> .3
        3. .1 -> .2
        4. primary -> .1

        Uses shutil.copy for file copying to preserve metadata.
        """
        # Rotate from oldest to newest (count down to 1)
        for generation in range(self.count, 1, -1):
            old_backup = self._backup_path(generation - 1)
            new_backup = self._backup_path(generation)

            if old_backup.exists():
                shutil.copy(old_backup, new_backup)

        # Copy primary to first backup generation
        if self.primary_path.exists():
            first_backup = self._backup_path(1)
            shutil.copy(self.primary_path, first_backup)

    def find_latest_backup(self) -> Path | None:
        """
        Find most recent backup file.

        Searches from highest generation number down to .1,
        returning the first (most recent) backup found.

        Returns:
            Path to most recent backup (e.g., "evidence.db.3") or None if no backups
        """
        for generation in range(self.count, 0, -1):
            backup = self._backup_path(generation)
            if backup.exists():
                return backup
        return None

    def restore_from_backup(self, backup_path: Path) -> None:
        """
        Restore primary file from backup.

        Copies the backup file to the primary location using shutil.copy,
        preserving the backup file.

        Args:
            backup_path: Path to backup file (e.g., "evidence.db.3")
        """
        if backup_path.exists():
            shutil.copy(backup_path, self.primary_path)
