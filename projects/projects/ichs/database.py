import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EnhancedConfig as Config

logger = logging.getLogger(__name__)


class Database:
    """Manages logging and historical data storage for iCHS."""

    def __init__(self, config: Config) -> None:
        """Initialize the database with configuration.

        Args:
            config: Configuration object containing database settings
        """
        self.config = config
        self.db_path = Path(str(config.get("database", "path", "ichs.db")))
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create runs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    command TEXT NOT NULL,
                    exit_code INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    cwd TEXT,
                    success BOOLEAN NOT NULL
                )
                """
            )

            # Create issues table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    parser TEXT NOT NULL,
                    file_path TEXT,
                    line_number INTEGER,
                    rule_id TEXT,
                    severity TEXT,
                    message TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs (id)
                )
                """
            )

            # Create performance metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs (id)
                )
                """
            )

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def log_run(
        self,
        command: str,
        exit_code: int,
        duration: float,
        cwd: str | None = None,
        success: bool = True,
    ) -> int:
        """Log a command run to the database.

        Args:
            command: Command that was executed
            exit_code: Exit code from the command
            duration: Duration in seconds
            cwd: Working directory
            success: Whether the command succeeded

        Returns:
            The ID of the inserted run record
        """
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO runs (timestamp, command, exit_code, duration, cwd, success)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, command, exit_code, duration, cwd, success),
            )
            run_id = cursor.lastrowid
            conn.commit()

        logger.info(
            f"Logged run {run_id}: {command} (exit: {exit_code}, duration: {duration:.2f}s)"
        )
        return int(run_id) if run_id is not None else -1

    def log_issue(
        self,
        run_id: int,
        parser: str,
        file_path: str | None = None,
        line_number: int | None = None,
        rule_id: str | None = None,
        severity: str | None = None,
        message: str | None = None,
    ) -> None:
        """Log an issue found during analysis.

        Args:
            run_id: ID of the run this issue belongs to
            parser: Name of the parser that found the issue
            file_path: File path where the issue was found
            line_number: Line number of the issue
            rule_id: Rule identifier
            severity: Severity level
            message: Issue description
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO issues (run_id, parser, file_path, line_number, rule_id, severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, parser, file_path, line_number, rule_id, severity, message),
            )
            conn.commit()

        logger.debug(f"Logged issue for run {run_id}: {parser} - {message}")

    def log_performance_metric(
        self, run_id: int, metric_name: str, metric_value: float
    ) -> None:
        """Log a performance metric for a run.

        Args:
            run_id: ID of the run this metric belongs to
            metric_name: Name of the metric
            metric_value: Value of the metric
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO performance_metrics (run_id, metric_name, metric_value)
                VALUES (?, ?, ?)
                """,
                (run_id, metric_name, metric_value),
            )
            conn.commit()

        logger.debug(
            f"Logged performance metric for run {run_id}: {metric_name} = {metric_value}"
        )

    def get_recent_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most recent runs from the database.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run records as dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?
                """,
                (limit,),
            )
            runs = [dict(row) for row in cursor.fetchall()]

        return runs

    def get_issues_by_run(self, run_id: int) -> list[dict[str, Any]]:
        """Get all issues for a specific run.

        Args:
            run_id: ID of the run

        Returns:
            List of issue records as dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM issues WHERE run_id = ? ORDER BY severity, file_path, line_number
                """,
                (run_id,),
            )
            issues = [dict(row) for row in cursor.fetchall()]

        return issues

    def get_performance_summary(self, days: int = 7) -> dict[str, Any]:
        """Get performance summary for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary containing performance metrics
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get total runs and success rate
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as total_runs,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(duration) as avg_duration,
                    MIN(duration) as min_duration,
                    MAX(duration) as max_duration
                FROM runs
                WHERE timestamp >= datetime('now', '-{days} days')
                """
            )

            row = cursor.fetchone()
            summary: dict[str, Any] = dict(row) if row is not None else {}

            # Get issue counts by severity
            cursor.execute(
                f"""
                SELECT severity, COUNT(*) as count
                FROM issues i
                JOIN runs r ON i.run_id = r.id
                WHERE r.timestamp >= datetime('now', '-{days} days')
                GROUP BY severity
                """
            )

            issue_counts = {
                row_["severity"]: row_["count"] for row_ in cursor.fetchall()
            }
            summary["issue_counts"] = issue_counts

        return summary

    def get_run_by_id(self, run_id: int) -> dict[str, Any] | None:
        """Fetch a single run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_runs_by_date_range(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """Fetch runs between start and end datetimes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM runs WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
                (start.isoformat(), end.isoformat()),
            )
            return [dict(r) for r in cursor.fetchall()]
