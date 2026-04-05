# __dev\iCHS\ichs\synthesis.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from .database import Database

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    total: int
    success: int
    fail: int
    avg_duration_sec: float


@dataclass
class RunRow:
    id: int
    command: str
    exit_code: int
    success: int
    duration_sec: float
    created_at: str


@dataclass
class IssueCount:
    key: str
    count: int


class Synthesis:
    """
    Aggregation/summary service over the Database.

    Non-breaking: provides read-only helpers; does not alter schema or data.
    """

    def __init__(self, config: Any, db: Database) -> None:
        self._config = config
        self._db = db

    # ---------- Public API ----------

    def summary_for_period(self, *, days: int = 7) -> RunSummary:
        """
        Aggregate summary for the last N day(s).
        """
        cutoff = self._cutoff_iso(days)
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success,
                    AVG(duration_sec) AS avg_duration
                FROM runs
                WHERE created_at >= ?
                """,
                (cutoff,),
            )
            row = cur.fetchone()
            total = int(row["total"] or 0)
            success = int(row["success"] or 0)
            avg = float(row["avg_duration"] or 0.0)
            return RunSummary(
                total=total, success=success, fail=total - success, avg_duration_sec=avg
            )
        finally:
            cur.close()

    def slowest_runs(self, *, days: int = 7, limit: int = 10) -> list[RunRow]:
        """
        Return the slowest runs in the last N day(s).
        """
        cutoff = self._cutoff_iso(days)
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, command, exit_code, success, duration_sec, created_at
                FROM runs
                WHERE created_at >= ?
                ORDER BY duration_sec DESC, id DESC
                LIMIT ?
                """,
                (cutoff, int(limit)),
            )
            rows = cur.fetchall()
            return [
                RunRow(
                    id=int(r["id"]),
                    command=str(r["command"]),
                    exit_code=int(r["exit_code"]),
                    success=int(r["success"]),
                    duration_sec=float(r["duration_sec"]),
                    created_at=str(r["created_at"]),
                )
                for r in rows
            ]
        finally:
            cur.close()

    def recent_failures(self, *, limit: int = 20) -> list[RunRow]:
        """
        Return the most recent failed runs (success=0), newest first.
        """
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, command, exit_code, success, duration_sec, created_at
                FROM runs
                WHERE success = 0
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
            return [
                RunRow(
                    id=int(r["id"]),
                    command=str(r["command"]),
                    exit_code=int(r["exit_code"]),
                    success=int(r["success"]),
                    duration_sec=float(r["duration_sec"]),
                    created_at=str(r["created_at"]),
                )
                for r in rows
            ]
        finally:
            cur.close()

    def issue_counts_by_rule(
        self, *, days: int = 7, limit: int = 20
    ) -> list[IssueCount]:
        """
        Top issue counts grouped by rule_id for runs within the last N day(s).
        """
        cutoff = self._cutoff_iso(days)
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COALESCE(rule_id, '') AS rule, COUNT(*) AS cnt
                FROM issues
                WHERE run_id IN (SELECT id FROM runs WHERE created_at >= ?)
                GROUP BY COALESCE(rule_id, '')
                ORDER BY cnt DESC, rule ASC
                LIMIT ?
                """,
                (cutoff, int(limit)),
            )
            rows = cur.fetchall()
            return [IssueCount(key=str(r["rule"]), count=int(r["cnt"])) for r in rows]
        finally:
            cur.close()

    def issue_counts_by_file(
        self, *, days: int = 7, limit: int = 20
    ) -> list[IssueCount]:
        """
        Top issue counts grouped by file_path for runs within the last N day(s).
        """
        cutoff = self._cutoff_iso(days)
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COALESCE(file_path, '') AS file, COUNT(*) AS cnt
                FROM issues
                WHERE run_id IN (SELECT id FROM runs WHERE created_at >= ?)
                GROUP BY COALESCE(file_path, '')
                ORDER BY cnt DESC, file ASC
                LIMIT ?
                """,
                (cutoff, int(limit)),
            )
            rows = cur.fetchall()
            return [IssueCount(key=str(r["file"]), count=int(r["cnt"])) for r in rows]
        finally:
            cur.close()

    def latest_runs(self, *, limit: int = 20) -> list[RunRow]:
        """
        Latest runs, newest first.
        """
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, command, exit_code, success, duration_sec, created_at
                FROM runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
            return [
                RunRow(
                    id=int(r["id"]),
                    command=str(r["command"]),
                    exit_code=int(r["exit_code"]),
                    success=int(r["success"]),
                    duration_sec=float(r["duration_sec"]),
                    created_at=str(r["created_at"]),
                )
                for r in rows
            ]
        finally:
            cur.close()

    # ---------- Internals ----------

    def _cutoff_iso(self, days: int) -> str:
        dt = datetime.now(UTC) - timedelta(days=max(0, days))
        return dt.replace(microsecond=0).isoformat()
