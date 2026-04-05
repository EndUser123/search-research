"""
Evidence Integrator Module

Contains TDDEvidenceIntegrator class for integrating TDD validation
results with the evidence repository system.

Extracted from pre_tool_use.py for better modularity and maintainability.
"""

import datetime
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


class TDDEvidenceIntegrator:
    """
    Integrates TDD validation results with the evidence repository system.
    """

    def __init__(self):
        # Use SystemConfig for evidence database path
        self.evidence_db_path = (
            Path.cwd()
            / "__csf"
            / "data"
            / "evidence_collection"
            / "evidence_records.db"
        )
        self._ensure_evidence_db()

    def _ensure_evidence_db(self):
        """Ensure evidence database exists and has proper schema"""
        self.evidence_db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.evidence_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tdd_enforcement_evidence (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    allowed BOOLEAN NOT NULL,
                    category TEXT NOT NULL,
                    violation_type TEXT,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    suggestions TEXT,
                    test_files TEXT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    tool_name TEXT,
                    enforcement_metadata TEXT
                )
            """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tdd_file_path ON tdd_enforcement_evidence(file_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tdd_timestamp ON tdd_enforcement_evidence(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tdd_allowed ON tdd_enforcement_evidence(allowed)"
            )

    def store_tdd_evidence(
        self,
        validation_result: Any,
        file_path: str,
        operation: str,
        category: Any,
        session_id: str = None,
        tool_name: str = None,
    ) -> str:
        """
        Store TDD validation evidence in the evidence repository.

        Args:
            validation_result: TDD validation result
            file_path: Path to the file being validated
            operation: Operation being performed
            category: File category
            session_id: Optional session ID
            tool_name: Tool that triggered the validation

        Returns:
            Evidence ID
        """
        evidence_id = self._generate_evidence_id(file_path, operation)

        metadata = {
            "file_category": category.value,
            "file_size": self._get_file_size(file_path),
            "validation_timestamp": validation_result.timestamp,
            "tdd_enforcer_version": "1.0.0",
            "enforcement_strategy": "graduated_enforcement",
        }

        with sqlite3.connect(self.evidence_db_path) as conn:
            conn.execute(
                """
                INSERT INTO tdd_enforcement_evidence
                (id, file_path, operation, allowed, category, violation_type, action,
                 reason, suggestions, test_files, timestamp, session_id, tool_name, enforcement_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    evidence_id,
                    file_path,
                    operation,
                    validation_result.allowed,
                    category.value,
                    (
                        validation_result.violation_type.value
                        if validation_result.violation_type
                        else None
                    ),
                    validation_result.action.value,
                    validation_result.reason,
                    json.dumps(validation_result.suggestions),
                    json.dumps(validation_result.test_file_paths),
                    validation_result.timestamp,
                    session_id,
                    tool_name,
                    json.dumps(metadata),
                ),
            )

        return evidence_id

    def _generate_evidence_id(self, file_path: str, operation: str) -> str:
        """Generate unique evidence ID"""
        timestamp = int(datetime.datetime.now().timestamp())
        hash_input = f"tdd_{file_path}_{operation}_{timestamp}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"tdd_evidence_{timestamp}_{hash_value}"

    def _get_file_size(self, file_path: str) -> int:
        """Get file size if it exists"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def get_tdd_enforcement_statistics(self) -> dict[str, Any]:
        """Get TDD enforcement statistics"""
        with sqlite3.connect(self.evidence_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM tdd_enforcement_evidence")
            total_validations = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM tdd_enforcement_evidence WHERE allowed = false"
            )
            blocked_operations = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM tdd_enforcement_evidence WHERE action = 'warn'"
            )
            warnings = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT category, COUNT(*) as count
                FROM tdd_enforcement_evidence
                GROUP BY category
            """
            )
            by_category = dict(cursor.fetchall())

            cursor = conn.execute(
                """
                SELECT violation_type, COUNT(*) as count
                FROM tdd_enforcement_evidence
                WHERE violation_type IS NOT NULL
                GROUP BY violation_type
            """
            )
            violations = dict(cursor.fetchall())

        return {
            "total_validations": total_validations,
            "blocked_operations": blocked_operations,
            "warnings": warnings,
            "compliance_rate": (total_validations - blocked_operations)
            / max(total_validations, 1)
            * 100,
            "by_category": by_category,
            "violations_by_type": violations,
            "evidence_database_path": str(self.evidence_db_path),
        }
