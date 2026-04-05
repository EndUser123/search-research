#!/usr/bin/env python3
"""
Evidence Store Fixture for Integration Testing

Provides real SQLite database instances for testing, avoiding mocks.
Following anti-mock philosophy from testing_patterns.md.

Fixtures:
- temp_evidence_db: Creates temporary evidence.db with test data
- synthetic_session_context: Generates realistic session context
- synthetic_bash_result: Creates tool execution results
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_evidence_db(tmp_path: Path) -> sqlite3.Connection:
    """
    Create temporary evidence database with real SQLite instance.

    Populated with test data matching production schema.
    Automatically cleaned up after test.

    Yields:
        sqlite3.Connection: Connection to temporary evidence database
    """
    db_path = tmp_path / "evidence_test.db"

    # Create database with production schema
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Initialize schema
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS session_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            pid INTEGER NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS tool_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL DEFAULT '',
            ts TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            command TEXT NOT NULL DEFAULT '',
            cwd TEXT NOT NULL DEFAULT '',
            output_excerpt TEXT NOT NULL DEFAULT '',
            success INTEGER NOT NULL DEFAULT 1,
            entities_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            workflow_type TEXT NOT NULL DEFAULT '',
            workflow_stage TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_session_context_updated
            ON session_context(updated_at);
        CREATE INDEX IF NOT EXISTS idx_tool_events_session
            ON tool_events(session_id, terminal_id);
        CREATE INDEX IF NOT EXISTS idx_tool_events_workflow
            ON tool_events(workflow_type, workflow_stage);
    """
    )

    # Populate with test data
    now = datetime.now(UTC).isoformat()

    # Test session 1 - Skill invocation
    conn.execute(
        """
        INSERT INTO session_context (session_id, terminal_id, updated_at, pid, metadata_json)
        VALUES (?, ?, ?, ?, ?)
    """,
        ("test-session-1", "terminal-A", now, 12345, '{"test": "data"}'),
    )

    # Test session 2 - Concurrent terminal
    conn.execute(
        """
        INSERT INTO session_context (session_id, terminal_id, updated_at, pid, metadata_json)
        VALUES (?, ?, ?, ?, ?)
    """,
        ("test-session-2", "terminal-B", now, 12346, '{"concurrent": true}'),
    )

    # Tool events for session 1
    conn.execute(
        """
        INSERT INTO tool_events
        (session_id, terminal_id, ts, tool_name, command, cwd, output_excerpt,
         success, workflow_type, workflow_stage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "test-session-1",
            "terminal-A",
            now,
            "Bash",
            "pytest test_file.py -v",
            "/project",
            "test_file.py::test_example PASSED",
            1,
            "skill_invocation",
            "execution",
        ),
    )

    conn.execute(
        """
        INSERT INTO tool_events
        (session_id, terminal_id, ts, tool_name, command, cwd, output_excerpt,
         success, workflow_type, workflow_stage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "test-session-1",
            "terminal-A",
            now,
            "Read",
            "file_path=test_file.py",
            "/project",
            "def test_example(): pass",
            1,
            "skill_invocation",
            "preparation",
        ),
    )

    # Tool events for session 2 (concurrent)
    conn.execute(
        """
        INSERT INTO tool_events
        (session_id, terminal_id, ts, tool_name, command, cwd, output_excerpt,
         success, workflow_type, workflow_stage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "test-session-2",
            "terminal-B",
            now,
            "Bash",
            "npm install",
            "/project",
            "added 142 packages in 5s",
            1,
            "tool_chain",
            "execution",
        ),
    )

    conn.commit()

    yield conn

    # Cleanup
    conn.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def synthetic_session_context() -> dict[str, Any]:
    """
    Generate synthetic session context for testing.

    Returns realistic session context matching production format.
    """
    return {
        "session_id": "synthetic-session-123",
        "terminal_id": "synthetic-terminal",
        "updated_at": datetime.now(UTC).isoformat(),
        "pid": 99999,
        "metadata": {"test": True, "synthetic": True},
    }


@pytest.fixture
def synthetic_bash_result() -> dict[str, Any]:
    """
    Generate synthetic Bash tool result for testing.

    Returns realistic tool execution result matching production format.
    """
    return {
        "name": "Bash",
        "command": "pytest tests/test_example.py -v",
        "cwd": "/project",
        "output": "tests/test_example.py::test_example PASSED\n1 passed in 0.15s",
        "output_excerpt": "tests/test_example.py::test_example PASSED",
        "success": True,
        "session_id": "synthetic-session-123",
        "terminal_id": "synthetic-terminal",
        "timestamp": datetime.now(UTC).isoformat(),
        "workflow_type": "skill_invocation",
        "workflow_stage": "execution",
    }


@pytest.fixture
def synthetic_skill_invocation_result() -> dict[str, Any]:
    """
    Generate synthetic Skill tool result for testing.
    """
    return {
        "name": "Skill",
        "skill": "test-skill",
        "input": {"target": "test"},
        "output": "Skill execution completed successfully",
        "success": True,
        "session_id": "synthetic-session-123",
        "terminal_id": "synthetic-terminal",
        "timestamp": datetime.now(UTC).isoformat(),
        "workflow_type": "skill_invocation",
        "workflow_stage": "skill_call",
    }


@pytest.fixture
def empty_evidence_db(tmp_path: Path) -> sqlite3.Connection:
    """
    Create empty temporary evidence database.

    For testing scenarios where no pre-populated data is needed.

    Yields:
        sqlite3.Connection: Connection to empty temporary database
    """
    db_path = tmp_path / "evidence_empty_test.db"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Initialize schema without data
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS session_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            pid INTEGER NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS tool_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL DEFAULT '',
            ts TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            command TEXT NOT NULL DEFAULT '',
            cwd TEXT NOT NULL DEFAULT '',
            output_excerpt TEXT NOT NULL DEFAULT '',
            success INTEGER NOT NULL DEFAULT 1,
            entities_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            workflow_type TEXT NOT NULL DEFAULT '',
            workflow_stage TEXT NOT NULL DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_session_context_updated
            ON session_context(updated_at);
        CREATE INDEX IF NOT EXISTS idx_tool_events_session
            ON tool_events(session_id, terminal_id);
        CREATE INDEX IF NOT EXISTS idx_tool_events_workflow
            ON tool_events(workflow_type, workflow_stage);
    """
    )

    conn.commit()

    yield conn

    # Cleanup
    conn.close()
    db_path.unlink(missing_ok=True)
