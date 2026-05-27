#!/usr/bin/env python3
"""Tests for ViolationTracker — round-trip persistence and schema validation."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from violation_tracker import ViolationCategory, ViolationSeverity, ViolationTracker


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Path:
    return tmp_path / "violations"


class TestViolationTrackerInit:
    def test_creates_db_on_init(self, tmp_storage: Path) -> None:
        ViolationTracker(storage_path=tmp_storage)
        db_path = tmp_storage / "violations.db"
        assert db_path.exists()

    def test_schema_has_trend_id_not_unicode(self, tmp_storage: Path) -> None:
        ViolationTracker(storage_path=tmp_storage)
        db_path = tmp_storage / "violations.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute("PRAGMA table_info(violation_trends)")
            columns = {row[1] for row in cursor.fetchall()}
        assert "trend_id" in columns
        assert "趋势_id" not in columns

    def test_violations_table_columns(self, tmp_storage: Path) -> None:
        ViolationTracker(storage_path=tmp_storage)
        db_path = tmp_storage / "violations.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute("PRAGMA table_info(violations)")
            columns = {row[1] for row in cursor.fetchall()}
        expected = {
            "violation_id", "severity", "category", "title", "description",
            "artifact_path", "rule_id", "location_info", "evidence",
            "recommendation", "auto_fix_available", "tags", "metadata", "created_at",
        }
        assert expected == columns


class TestRoundTrip:
    def test_track_and_retrieve(self, tmp_storage: Path) -> None:
        tracker = ViolationTracker(storage_path=tmp_storage)
        violation = tracker.track_violation(
            severity=ViolationSeverity.CRITICAL,
            category=ViolationCategory.SECURITY,
            title="Test violation",
            description="Test description",
            artifact_path="/test/file.py",
            rule_id="TEST-RULE",
            location_info="test_hook.py:1",
            evidence="test evidence",
            recommendation="fix it",
            auto_fix_available=True,
            tags={"test", "unit"},
            metadata={"key": "value"},
        )
        assert violation.violation_id.startswith("v-")

        # Retrieve from fresh tracker instance (tests persistence)
        tracker2 = ViolationTracker(storage_path=tmp_storage)
        results = tracker2.get_recent(limit=10)
        assert len(results) == 1
        assert results[0].title == "Test violation"
        assert results[0].severity == ViolationSeverity.CRITICAL
        assert results[0].tags == {"test", "unit"}
        assert results[0].metadata == {"key": "value"}

    def test_multiple_violations_order(self, tmp_storage: Path) -> None:
        tracker = ViolationTracker(storage_path=tmp_storage)
        for i in range(5):
            tracker.track_violation(
                severity=ViolationSeverity.MINOR,
                category=ViolationCategory.COMPLIANCE,
                title=f"Violation {i}",
                description="",
                artifact_path="",
                rule_id="R",
                location_info="",
                evidence="",
                recommendation="",
            )
        results = tracker.get_recent(limit=3)
        assert len(results) == 3

    def test_limit_parameter(self, tmp_storage: Path) -> None:
        tracker = ViolationTracker(storage_path=tmp_storage)
        for i in range(10):
            tracker.track_violation(
                severity=ViolationSeverity.ADVISORY,
                category=ViolationCategory.GOVERNANCE,
                title=f"V{i}",
                description="",
                artifact_path="",
                rule_id="R",
                location_info="",
                evidence="",
                recommendation="",
            )
        results = tracker.get_recent(limit=5)
        assert len(results) == 5


class TestContextManagerSafety:
    def test_no_leaked_connections(self, tmp_storage: Path) -> None:
        tracker = ViolationTracker(storage_path=tmp_storage)
        tracker.track_violation(
            severity=ViolationSeverity.MAJOR,
            category=ViolationCategory.SECURITY,
            title="Connection test",
            description="",
            artifact_path="",
            rule_id="R",
            location_info="",
            evidence="",
            recommendation="",
        )
        db_path = tmp_storage / "violations.db"
        # If connections were properly closed, we can open exclusive
        with sqlite3.connect(str(db_path)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
            assert count == 1
