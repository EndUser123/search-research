"""
Embedding recovery manager for yt-fts.

Manages recovery and repair of embedding data for vector search functionality.
"""

import sqlite3
from typing import Any

from rich.console import Console

from yt_fts.utils.config import get_db_path


class EmbeddingRecoveryManager:
    """Manager for recovering and repairing embedding data."""

    def __init__(self, console: Console | None = None):
        """
        Initialize the embedding recovery manager.

        Args:
            console: Rich console instance for output
        """
        self.console = console or Console()
        self.db_path = get_db_path()

    def check_embedding_consistency(self) -> dict[str, Any]:
        """
        Check consistency of embedding data in the database.

        Returns:
            Dictionary with consistency statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if embeddings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='embeddings'
            """)
            embeddings_table_exists = cursor.fetchone() is not None

            if not embeddings_table_exists:
                return {
                    "embeddings_table_exists": False,
                    "total_subtitles": 0,
                    "total_embeddings": 0,
                    "missing_embeddings": 0,
                    "orphaned_embeddings": 0
                }

            # Get total subtitles
            cursor.execute("SELECT COUNT(*) FROM subtitles")
            total_subtitles = cursor.fetchone()[0]

            # Get total embeddings
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            total_embeddings = cursor.fetchone()[0]

            # Check for subtitles without embeddings
            cursor.execute("""
                SELECT COUNT(*) FROM subtitles s
                LEFT JOIN embeddings e ON s.rowid = e.subtitle_id
                WHERE e.subtitle_id IS NULL
            """)
            missing_embeddings = cursor.fetchone()[0]

            # Check for embeddings without subtitles
            cursor.execute("""
                SELECT COUNT(*) FROM embeddings e
                LEFT JOIN subtitles s ON e.rowid = s.subtitle_id
                WHERE s.rowid IS NULL
            """)
            orphaned_embeddings = cursor.fetchone()[0]

            conn.close()

            return {
                "embeddings_table_exists": True,
                "total_subtitles": total_subtitles,
                "total_embeddings": total_embeddings,
                "missing_embeddings": missing_embeddings,
                "orphaned_embeddings": orphaned_embeddings
            }

        except Exception as e:
            self.console.print(f"[red]Error checking embedding consistency: {e}[/red]")
            return {
                "error": str(e),
                "embeddings_table_exists": False,
                "total_subtitles": 0,
                "total_embeddings": 0,
                "missing_embeddings": 0,
                "orphaned_embeddings": 0
            }

    def repair_embeddings(self) -> dict[str, Any]:
        """
        Attempt to repair embedding data issues.

        Returns:
            Dictionary with repair results
        """
        try:
            consistency = self.check_embedding_consistency()
            repair_results = {
                "removed_orphaned_embeddings": 0,
                "recreated_missing_embeddings": 0,
                "errors": []
            }

            # Remove orphaned embeddings
            if consistency.get("orphaned_embeddings", 0) > 0:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM embeddings
                    WHERE rowid NOT IN (
                        SELECT subtitle_id FROM subtitles
                        WHERE subtitle_id IS NOT NULL
                    )
                """)

                removed = cursor.rowcount
                repair_results["removed_orphaned_embeddings"] = removed
                conn.commit()
                conn.close()

                self.console.print(f"[green]Removed {removed} orphaned embeddings[/green]")

            return repair_results

        except Exception as e:
            error_msg = f"Error during embedding repair: {e}"
            self.console.print(f"[red]{error_msg}[/red]")
            return {"errors": [error_msg]}

    def get_embedding_status(self) -> str:
        """
        Get a summary status of embeddings.

        Returns:
            Status string describing embedding state
        """
        consistency = self.check_embedding_consistency()

        if not consistency.get("embeddings_table_exists"):
            return "No embeddings table found"

        total_subtitles = consistency.get("total_subtitles", 0)
        total_embeddings = consistency.get("total_embeddings", 0)
        missing = consistency.get("missing_embeddings", 0)

        if total_embeddings == 0:
            return "No embeddings generated yet"
        if missing == 0:
            return f"Complete: {total_embeddings} embeddings for {total_subtitles} subtitles"
        return f"Partial: {total_embeddings}/{total_subtitles} embeddings ({missing} missing)"
