"""
TaskMaster Integration (DEPRECATED)

This module is DEPRECATED. TaskMaster has been removed from the system.

Pattern storage is now handled by CKS (Constitutional Knowledge System).
See cks_pattern_integration.py for the current implementation.

This file is kept for reference only and will be removed in a future release.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any


class TaskMasterIntegration:
    """
    Integration with TaskMaster for RCA evidence storage and pattern analysis
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or "P:/.speckit/taskmaster/tasks.db"
        self.db_connection: sqlite3.Connection | None = None
        self.lock = threading.RLock()
        self._ensure_connection()
        self._ensure_schema()

    @contextmanager
    def _get_cursor(self) -> Any:
        """Thread-safe database cursor context manager"""
        with self.lock:
            if self.db_connection is None:
                self._ensure_connection()
            assert self.db_connection is not None
            cursor = self.db_connection.cursor()
            try:
                yield cursor
                self.db_connection.commit()
            except Exception:
                self.db_connection.rollback()
                raise
            finally:
                cursor.close()

    def _ensure_connection(self):
        """Ensure database connection is established"""
        try:
            self.db_connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self.db_connection.row_factory = sqlite3.Row
        except Exception as e:
            raise ConnectionError(f"Failed to connect to TaskMaster database: {e}")

    def _ensure_schema(self):
        """Ensure required database schema exists"""
        with self._get_cursor() as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('rca_sessions', 'rca_evidence', 'rca_performance', 'rca_patterns')
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]

            # Create tables if they don't exist
            if "rca_sessions" not in existing_tables:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rca_sessions (
                        id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        problem_description TEXT NOT NULL,
                        context_analysis TEXT,
                        tool_selection TEXT,
                        findings TEXT,
                        recommendations TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)
            else:
                # Migration: Add missing columns to rca_sessions
                cursor.execute("PRAGMA table_info(rca_sessions)")
                columns = [row[1] for row in cursor.fetchall()]
                if "task_id" not in columns:
                    cursor.execute("ALTER TABLE rca_sessions ADD COLUMN task_id TEXT DEFAULT ''")
                if "status" not in columns:
                    cursor.execute("ALTER TABLE rca_sessions ADD COLUMN status TEXT DEFAULT 'active'")
                if "created_at" not in columns:
                    # SQLite requires constant default for ALTER TABLE
                    cursor.execute("ALTER TABLE rca_sessions ADD COLUMN created_at TIMESTAMP DEFAULT ''")
                    # Update existing rows with current timestamp
                    cursor.execute("UPDATE rca_sessions SET created_at = datetime('now') WHERE created_at = ''")

            if "rca_evidence" not in existing_tables:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rca_evidence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        evidence_type TEXT NOT NULL,
                        evidence_data TEXT NOT NULL,
                        metadata TEXT,
                        tool_used TEXT,
                        confidence_score REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES rca_sessions(id) ON DELETE CASCADE
                    )
                """)

            if "rca_performance" not in existing_tables:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rca_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        optimization_type TEXT NOT NULL,
                        time_reduction_ms REAL,
                        cache_hits INTEGER,
                        parallel_tasks INTEGER,
                        performance_metrics TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES rca_sessions(id) ON DELETE CASCADE
                    )
                """)

            if "rca_patterns" not in existing_tables:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rca_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        problem_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confidence_score REAL DEFAULT 1.0,
                        success_rate REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_rca_sessions_task_id ON rca_sessions(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_rca_sessions_status ON rca_sessions(status)",
                "CREATE INDEX IF NOT EXISTS idx_rca_sessions_created_at ON rca_sessions(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_rca_evidence_session_id ON rca_evidence(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_rca_evidence_type ON rca_evidence(evidence_type)",
                "CREATE INDEX IF NOT EXISTS idx_rca_performance_session_id ON rca_performance(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_rca_patterns_problem_type ON rca_patterns(problem_type)",
                "CREATE INDEX IF NOT EXISTS idx_rca_patterns_last_seen ON rca_patterns(last_seen)"
            ]

            for index_sql in indexes:
                cursor.execute(index_sql)

    def create_rca_session(self, problem_description: str, context: dict, tool_selection: dict) -> str:
        """
        Create new RCA session in TaskMaster

        Args:
            problem_description: Description of the problem being analyzed
            context: Context analysis results
            tool_selection: Tool selection results

        Returns:
            Session ID for the created session

        """
        session_id = self._generate_session_id()
        task_id = f"RCA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        session_data = {
            "id": session_id,
            "task_id": task_id,
            "problem_description": problem_description,
            "context_analysis": json.dumps(context),
            "tool_selection": json.dumps(tool_selection),
            "status": "active"
        }

        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO rca_sessions
                (id, task_id, problem_description, context_analysis, tool_selection, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_data["id"],
                session_data["task_id"],
                session_data["problem_description"],
                session_data["context_analysis"],
                session_data["tool_selection"],
                session_data["status"]
            ))

        return session_id

    def store_evidence(self, session_id: str, evidence_type: str, evidence_data: dict,
                      metadata: dict | None = None, tool_used: str | None = None, confidence_score: float | None = None):
        """
        Store evidence in TaskMaster

        Args:
            session_id: RCA session ID
            evidence_type: Type of evidence (context_analysis, tool_selection, finding, etc.)
            evidence_data: Evidence data
            metadata: Additional metadata
            tool_used: Tool that generated this evidence
            confidence_score: Confidence score for the evidence

        """
        evidence_record = {
            "session_id": session_id,
            "evidence_type": evidence_type,
            "evidence_data": json.dumps(evidence_data),
            "metadata": json.dumps(metadata) if metadata else None,
            "tool_used": tool_used,
            "confidence_score": confidence_score
        }

        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO rca_evidence
                (session_id, evidence_type, evidence_data, metadata, tool_used, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                evidence_record["session_id"],
                evidence_record["evidence_type"],
                evidence_record["evidence_data"],
                evidence_record["metadata"],
                evidence_record["tool_used"],
                evidence_record["confidence_score"]
            ))

        # Update patterns if this is successful evidence
        if confidence_score and confidence_score > 0.7:
            self._update_patterns(evidence_type, evidence_data, confidence_score)

    def store_performance_metrics(self, session_id: str, optimization_type: str,
                                performance_data: dict):
        """
        Store performance metrics for RCA session

        Args:
            session_id: RCA session ID
            optimization_type: Type of optimization applied
            performance_data: Performance metrics data

        """
        time_reduction = performance_data.get("time_reduction_ms", 0)
        cache_hits = performance_data.get("cache_hits", 0)
        parallel_tasks = performance_data.get("parallel_tasks", 0)
        performance_metrics_json = json.dumps(performance_data)

        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO rca_performance
                (session_id, optimization_type, time_reduction_ms, cache_hits, parallel_tasks, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                optimization_type,
                time_reduction,
                cache_hits,
                parallel_tasks,
                performance_metrics_json
            ))

    def complete_session(self, session_id: str, findings: dict, recommendations: list[str]):
        """
        Complete RCA session with findings and recommendations

        Args:
            session_id: RCA session ID
            findings: Analysis findings
            recommendations: Recommendations generated

        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                UPDATE rca_sessions
                SET findings = ?, recommendations = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                json.dumps(findings),
                json.dumps(recommendations),
                session_id
            ))

    def get_session(self, session_id: str) -> dict | None:
        """
        Get RCA session details

        Args:
            session_id: RCA session ID

        Returns:
            Session data or None if not found

        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM rca_sessions WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()

            if row:
                return {
                    "id": row["id"],
                    "task_id": row["task_id"],
                    "problem_description": row["problem_description"],
                    "context_analysis": json.loads(row["context_analysis"]) if row["context_analysis"] else None,
                    "tool_selection": json.loads(row["tool_selection"]) if row["tool_selection"] else None,
                    "findings": json.loads(row["findings"]) if row["findings"] else None,
                    "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else None,
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "completed_at": row["completed_at"]
                }
            return None

    def get_session_evidence(self, session_id: str, evidence_type: str | None = None) -> list[dict]:
        """
        Get evidence for RCA session

        Args:
            session_id: RCA session ID
            evidence_type: Optional evidence type filter

        Returns:
            List of evidence records

        """
        with self._get_cursor() as cursor:
            if evidence_type:
                cursor.execute("""
                    SELECT * FROM rca_evidence
                    WHERE session_id = ? AND evidence_type = ?
                    ORDER BY timestamp
                """, (session_id, evidence_type))
            else:
                cursor.execute("""
                    SELECT * FROM rca_evidence
                    WHERE session_id = ?
                    ORDER BY timestamp
                """, (session_id,))

            evidence = []
            for row in cursor.fetchall():
                evidence.append({
                    "id": row["id"],
                    "evidence_type": row["evidence_type"],
                    "evidence_data": json.loads(row["evidence_data"]),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "tool_used": row["tool_used"],
                    "confidence_score": row["confidence_score"],
                    "timestamp": row["timestamp"]
                })

            return evidence

    def get_historical_patterns(self, problem_type: str, limit: int = 10,
                              days_back: int = 180) -> list[dict]:
        """
        Get historically successful patterns for similar problems

        Args:
            problem_type: Type of problem to search for
            limit: Maximum number of patterns to return
            days_back: How many days back to search

        Returns:
            List of historically successful patterns

        """
        cutoff_date = datetime.now() - timedelta(days=days_back)

        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT s.findings, s.recommendations, s.tool_selection, s.context_analysis,
                       (SELECT COUNT(*) FROM rca_evidence e WHERE e.session_id = s.id) as evidence_count,
                       AVG(p.time_reduction_ms) as avg_time_reduction
                FROM rca_sessions s
                LEFT JOIN rca_performance p ON s.id = p.session_id
                WHERE JSON_EXTRACT(s.context_analysis, '$.problem_type') = ?
                AND s.status = 'completed'
                AND s.created_at > ?
                GROUP BY s.id
                ORDER BY evidence_count DESC, avg_time_reduction DESC, s.created_at DESC
                LIMIT ?
            """, (problem_type, cutoff_date, limit))

            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    "findings": json.loads(row["findings"]) if row["findings"] else {},
                    "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else [],
                    "tool_selection": json.loads(row["tool_selection"]) if row["tool_selection"] else {},
                    "context_analysis": json.loads(row["context_analysis"]) if row["context_analysis"] else {},
                    "evidence_count": row["evidence_count"],
                    "avg_time_reduction": row["avg_time_reduction"] or 0
                })

            return patterns

    def get_performance_analytics(self, days_back: int = 30) -> dict:
        """
        Get performance analytics for RCA sessions

        Args:
            days_back: Number of days to analyze

        Returns:
            Performance analytics data

        """
        cutoff_date = datetime.now() - timedelta(days=days_back)

        with self._get_cursor() as cursor:
            # Session statistics
            cursor.execute("""
                SELECT COUNT(*) as total_sessions,
                       AVG(CASE WHEN completed_at IS NOT NULL THEN
                           (julianday(completed_at) - julianday(created_at)) * 24 * 60
                           ELSE NULL END) as avg_duration_minutes,
                       COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions
                FROM rca_sessions
                WHERE created_at > ?
            """, (cutoff_date,))
            session_stats = cursor.fetchone()

            # Performance optimization statistics
            cursor.execute("""
                SELECT optimization_type,
                       COUNT(*) as usage_count,
                       AVG(time_reduction_ms) as avg_time_reduction,
                       AVG(cache_hits) as avg_cache_hits,
                       AVG(parallel_tasks) as avg_parallel_tasks
                FROM rca_performance p
                JOIN rca_sessions s ON p.session_id = s.id
                WHERE s.created_at > ?
                GROUP BY optimization_type
            """, (cutoff_date,))
            perf_stats = cursor.fetchall()

            # Problem type distribution
            cursor.execute("""
                SELECT JSON_EXTRACT(context_analysis, '$.problem_type') as problem_type,
                       COUNT(*) as session_count
                FROM rca_sessions
                WHERE created_at > ? AND context_analysis IS NOT NULL
                GROUP BY JSON_EXTRACT(context_analysis, '$.problem_type')
                ORDER BY session_count DESC
            """, (cutoff_date,))
            problem_distribution = cursor.fetchall()

            return {
                "session_statistics": {
                    "total_sessions": session_stats["total_sessions"] or 0,
                    "completed_sessions": session_stats["completed_sessions"] or 0,
                    "completion_rate": (
                        (session_stats["completed_sessions"] or 0) / max(session_stats["total_sessions"] or 1, 1)
                    ) * 100,
                    "avg_duration_minutes": session_stats["avg_duration_minutes"] or 0
                },
                "performance_optimizations": [
                    {
                        "optimization_type": row["optimization_type"],
                        "usage_count": row["usage_count"],
                        "avg_time_reduction_ms": row["avg_time_reduction"] or 0,
                        "avg_cache_hits": row["avg_cache_hits"] or 0,
                        "avg_parallel_tasks": row["avg_parallel_tasks"] or 0
                    }
                    for row in perf_stats
                ],
                "problem_type_distribution": [
                    {
                        "problem_type": row["problem_type"] or "unknown",
                        "session_count": row["session_count"]
                    }
                    for row in problem_distribution
                ]
            }

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"rca_{uuid.uuid4().hex[:12]}"

    def _update_patterns(self, evidence_type: str, evidence_data: dict, confidence_score: float):
        """Update pattern analysis based on successful evidence"""
        # Extract problem type from evidence data if available
        problem_type = evidence_data.get("problem_type", "unknown")

        with self._get_cursor() as cursor:
            # Check if pattern already exists
            cursor.execute("""
                SELECT id, frequency, success_rate FROM rca_patterns
                WHERE problem_type = ? AND pattern_data = ?
            """, (problem_type, json.dumps(evidence_data)))

            existing_pattern = cursor.fetchone()

            if existing_pattern:
                # Update existing pattern
                new_frequency = existing_pattern["frequency"] + 1
                # Update success rate as weighted average
                current_rate = existing_pattern["success_rate"] or 0.0
                new_success_rate = (current_rate * existing_pattern["frequency"] + confidence_score) / new_frequency

                cursor.execute("""
                    UPDATE rca_patterns
                    SET frequency = ?, last_seen = CURRENT_TIMESTAMP, confidence_score = ?, success_rate = ?
                    WHERE id = ?
                """, (new_frequency, confidence_score, new_success_rate, existing_pattern["id"]))
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO rca_patterns
                    (problem_type, pattern_data, frequency, confidence_score, success_rate)
                    VALUES (?, ?, ?, ?, ?)
                """, (problem_type, json.dumps(evidence_data), 1, confidence_score, confidence_score))

    def get_pattern_recommendations(self, context: dict, limit: int = 5) -> list[dict]:
        """
        Get pattern-based recommendations for current context

        Args:
            context: Current context analysis
            limit: Maximum number of recommendations

        Returns:
            List of pattern-based recommendations

        """
        problem_type = context.get("problem_type", "unknown")

        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT pattern_data, frequency, confidence_score, success_rate
                FROM rca_patterns
                WHERE problem_type = ? AND success_rate > 0.7
                ORDER BY (frequency * success_rate * confidence_score) DESC
                LIMIT ?
            """, (problem_type, limit))

            recommendations = []
            for row in cursor.fetchall():
                pattern_data = json.loads(row["pattern_data"])
                recommendations.append({
                    "pattern_data": pattern_data,
                    "frequency": row["frequency"],
                    "confidence_score": row["confidence_score"],
                    "success_rate": row["success_rate"],
                    "recommendation_strength": row["frequency"] * row["success_rate"] * row["confidence_score"]
                })

            return recommendations

    def cleanup_old_sessions(self, days_to_keep: int = 365):
        """
        Clean up old RCA sessions and evidence

        Args:
            days_to_keep: Number of days to keep sessions

        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with self._get_cursor() as cursor:
            # Delete old evidence first (due to foreign key constraint)
            cursor.execute("""
                DELETE FROM rca_evidence
                WHERE session_id IN (
                    SELECT id FROM rca_sessions WHERE created_at < ?
                )
            """, (cutoff_date,))

            # Delete old performance data
            cursor.execute("""
                DELETE FROM rca_performance
                WHERE session_id IN (
                    SELECT id FROM rca_sessions WHERE created_at < ?
                )
            """, (cutoff_date,))

            # Delete old sessions
            cursor.execute("""
                DELETE FROM rca_sessions WHERE created_at < ?
            """, (cutoff_date,))

            # Optionally clean up old patterns
            pattern_cutoff = datetime.now() - timedelta(days=days_to_keep * 2)
            cursor.execute("""
                DELETE FROM rca_patterns WHERE last_seen < ?
            """, (pattern_cutoff,))

    def get_integration_health(self) -> dict:
        """
        Get health status of TaskMaster integration

        Returns:
            Health status information

        """
        try:
            with self._get_cursor() as cursor:
                # Test database connection
                cursor.execute("SELECT 1")
                connection_ok = True
                connection_error = None
        except Exception as e:
            connection_ok = False
            connection_error = str(e)

        # Get table statistics
        stats: dict[str, Any] = {}
        if connection_ok:
            try:
                with self._get_cursor() as cursor:
                    for table in ["rca_sessions", "rca_evidence", "rca_performance", "rca_patterns"]:
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                        stats[table] = cursor.fetchone()["count"]
            except Exception as e:
                stats["error"] = str(e)

        return {
            "database_connection": {
                "status": "healthy" if connection_ok else "unhealthy",
                "error": connection_error
            },
            "table_statistics": stats,
            "integration_capabilities": {
                "session_management": True,
                "evidence_storage": True,
                "performance_tracking": True,
                "pattern_analysis": True,
                "historical_analysis": True
            }
        }

    def close(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
