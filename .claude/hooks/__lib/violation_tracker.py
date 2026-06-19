#!/usr/bin/env python3
"""
ViolationTracker — Universal sink for all hook violations.

Provides structured violation tracking with severity/category classification,
SQLite persistence, and trending analysis.

Usage:
    from __lib.violation_tracker import ViolationTracker, ViolationSeverity, ViolationCategory

    tracker = ViolationTracker(storage_path=Path("P:/.claude/hooks/hooks/data/violations"))
    violation = tracker.track_violation(
        severity=ViolationSeverity.CRITICAL,
        category=ViolationCategory.SECURITY,
        title="Hook Violation: ROOT_WRITE",
        description="Root protection hook blocked write to P:/",
        artifact_path="P:/some_file.txt",
        rule_id="HOOK-ROOT-PROTECTION",
        location_info="Hook: deny_root_write.py",
        evidence="...",
        recommendation="Use appropriate subdirectory",
        tags={"hook", "root-protection"},
    )
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ViolationSeverity(Enum):
    ADVISORY = "advisory"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class ViolationCategory(Enum):
    COMPLIANCE = "compliance"
    GOVERNANCE = "governance"
    SECURITY = "security"


@dataclass
class Violation:
    """A single hook violation record."""
    violation_id: str
    severity: ViolationSeverity
    category: ViolationCategory
    title: str
    description: str
    artifact_path: str
    rule_id: str
    location_info: str
    evidence: str
    recommendation: str
    auto_fix_available: bool
    tags: set[str]
    metadata: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ViolationTracker:
    """Universal sink for all hook violations."""

    def __init__(
        self,
        storage_path: str | Path,
        auto_categorize: bool = False,
        enable_trending: bool = False,
    ):
        self.storage_path = Path(storage_path)
        self.auto_categorize = auto_categorize
        self.enable_trending = enable_trending
        self._violations: list[Violation] = []
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite backing store."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        db_path = self.storage_path / "violations.db"
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    violation_id TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    artifact_path TEXT,
                    rule_id TEXT,
                    location_info TEXT,
                    evidence TEXT,
                    recommendation TEXT,
                    auto_fix_available INTEGER,
                    tags TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS violation_trends (
                    trend_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT,
                    count INTEGER,
                    period_start TEXT,
                    period_end TEXT
                )
            """)
            conn.commit()

    def track_violation(
        self,
        severity: ViolationSeverity,
        category: ViolationCategory,
        title: str,
        description: str,
        artifact_path: str,
        rule_id: str,
        location_info: str,
        evidence: str,
        recommendation: str,
        auto_fix_available: bool = False,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Violation:
        """Record a violation and persist to SQLite."""
        violation_id = f"v-{uuid.uuid4().hex[:8]}"
        violation = Violation(
            violation_id=violation_id,
            severity=severity,
            category=category,
            title=title,
            description=description,
            artifact_path=artifact_path,
            rule_id=rule_id,
            location_info=location_info,
            evidence=evidence,
            recommendation=recommendation,
            auto_fix_available=auto_fix_available,
            tags=tags or set(),
            metadata=metadata or {},
        )
        self._violations.append(violation)
        self._persist(violation)
        return violation

    def _persist(self, violation: Violation) -> None:
        """Persist violation to SQLite."""
        db_path = self.storage_path / "violations.db"
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                conn.execute(
                    """
                    INSERT INTO violations (
                        violation_id, severity, category, title, description,
                        artifact_path, rule_id, location_info, evidence,
                        recommendation, auto_fix_available, tags, metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        violation.violation_id,
                        violation.severity.value,
                        violation.category.value,
                        violation.title,
                        violation.description,
                        violation.artifact_path,
                        violation.rule_id,
                        violation.location_info,
                        violation.evidence,
                        violation.recommendation,
                        int(violation.auto_fix_available),
                        json.dumps(list(violation.tags)),
                        json.dumps(violation.metadata),
                        violation.created_at,
                    ),
                )
                conn.commit()
        except sqlite3.Error:
            pass  # Fail silently — violation is still in memory

    def get_recent(self, limit: int = 100) -> list[Violation]:
        """Retrieve recent violations from SQLite."""
        db_path = self.storage_path / "violations.db"
        violations = []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                cursor = conn.execute(
                    """
                    SELECT violation_id, severity, category, title, description,
                           artifact_path, rule_id, location_info, evidence,
                           recommendation, auto_fix_available, tags, metadata, created_at
                    FROM violations ORDER BY created_at DESC LIMIT ?
                    """,
                    (limit,),
                )
                for row in cursor.fetchall():
                    violations.append(
                        Violation(
                            violation_id=row[0],
                            severity=ViolationSeverity(row[1]),
                            category=ViolationCategory(row[2]),
                            title=row[3],
                            description=row[4] or "",
                            artifact_path=row[5] or "",
                            rule_id=row[6] or "",
                            location_info=row[7] or "",
                            evidence=row[8] or "",
                            recommendation=row[9] or "",
                            auto_fix_available=bool(row[10]),
                            tags=set(json.loads(row[11])) if row[11] else set(),
                            metadata=json.loads(row[12]) if row[12] else {},
                            created_at=row[13],
                        )
                    )
        except sqlite3.Error:
            pass
        return violations
