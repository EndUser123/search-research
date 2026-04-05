"""Database health diagnostics."""

import sqlite3
from pathlib import Path

from yt_fts.utils.config import get_db_path

from .checker import DiagnosticChecker, Status


class DatabaseChecker(DiagnosticChecker):
    """Check database health for yt-fts."""

    def run(self) -> list:
        """Run all database diagnostics."""
        self.results.clear()
        self._check_database_file()
        self._check_database_connection()
        self._check_database_integrity()
        return self.results

    def _check_database_file(self):
        """Check if database file exists."""
        db_path = Path(get_db_path())
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            self.add_result(
                category="Database File",
                status=Status.PASS,
                message="Found",
                details=[
                    f"Path: {db_path}",
                    f"Size: {size_mb:.2f} MB",
                ],
            )
        else:
            self.add_result(
                category="Database File",
                status=Status.INFO,
                message="Not found (new installation)",
                details=[f"Expected: {db_path}"],
                remediation="Run: yt-fts download <channel_url> to create the database",
            )

    def _check_database_connection(self):
        """Check database connection."""
        db_path = get_db_path()
        if not Path(get_db_path()).exists():
            return

        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            conn.close()

            self.add_result(
                category="Database Connection",
                status=Status.PASS,
                message="Working",
                details=[f"SQLite version: {version}"],
            )
        except Exception as e:
            self.add_result(
                category="Database Connection",
                status=Status.FAIL,
                message="Failed",
                details=[f"Error: {e}"],
                remediation="Database may be corrupted. Try: yt-fts --rebuild-db",
            )

    def _check_database_integrity(self):
        """Check database integrity and get stats."""
        db_path = get_db_path()
        if not Path(get_db_path()).exists():
            return

        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            cursor = conn.cursor()

            # Check integrity (use quick_check for large databases)
            cursor.execute("PRAGMA quick_check")
            integrity = cursor.fetchone()[0]

            # Get stats from the correct schema
            cursor.execute("SELECT COUNT(*) FROM Videos")
            total_videos = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Channels")
            total_channels = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Subtitles")
            total_subtitles = cursor.fetchone()[0]

            # Count videos without subtitles (via LEFT JOIN)
            cursor.execute("""
                SELECT COUNT(DISTINCT v.video_id)
                FROM Videos v
                LEFT JOIN Subtitles s ON v.video_id = s.video_id
                WHERE s.subtitle_id IS NULL
            """)
            no_subtitle = cursor.fetchone()[0]

            conn.close()

            if integrity == "ok":
                self.add_result(
                    category="Database Integrity",
                    status=Status.PASS,
                    message="Valid",
                    details=[
                        f"Videos: {total_videos:,} total",
                        f"Channels: {total_channels}",
                        f"Subtitles: {total_subtitles:,}",
                        f"Videos without subtitles: {no_subtitle:,}",
                    ],
                )
            else:
                self.add_result(
                    category="Database Integrity",
                    status=Status.FAIL,
                    message="Corrupted",
                    details=[f"Integrity check: {integrity}"],
                    remediation="Database is corrupted. Consider rebuilding from scratch.",
                )
        except Exception as e:
            self.add_result(
                category="Database Integrity",
                status=Status.FAIL,
                message="Check failed",
                details=[f"Error: {e}"],
                remediation="Try: yt-fts --rebuild-db",
            )
