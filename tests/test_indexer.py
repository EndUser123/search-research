"""Tests for core.chs.indexer — session summarization at close."""

import pytest
import sqlite3
from unittest.mock import MagicMock, patch

from core.chs.indexer import ChatIndexer, _get_summary_executor


@pytest.fixture
def indexer_mem():
    """In-memory indexer for testing."""
    conn = sqlite3.connect(":memory:")
    # Create minimal schema
    conn.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, path TEXT)")
    conn.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY,
            session_key TEXT,
            project_id INTEGER,
            started_at INTEGER,
            ended_at INTEGER,
            is_closed INTEGER DEFAULT 0,
            summary_short TEXT,
            embedding BLOB,
            embedding_model TEXT,
            embedding_dim INTEGER,
            last_message_timestamp INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            project_id INTEGER,
            timestamp INTEGER,
            role TEXT,
            content TEXT
        )
    """)
    conn.commit()
    return ChatIndexer(conn=conn)


def test_close_idle_sessions_marks_closed(indexer_mem):
    """Sessions past timeout are marked is_closed=1."""
    indexer_mem._get_connection().execute(
        "INSERT INTO sessions (id, session_key, project_id, started_at, last_message_timestamp, is_closed) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "test-session", 1, 1000, 1000, 0),
    )
    indexer_mem._get_connection().commit()

    # Override timeout to 0 so session is immediately idle
    indexer_mem._close_idle_sessions(timeout=0)

    row = indexer_mem._get_connection().execute(
        "SELECT is_closed FROM sessions WHERE id = 1"
    ).fetchone()
    assert row[0] == 1


def test_close_idle_sessions_no_blocking(indexer_mem):
    """_close_idle_sessions returns quickly even with executor."""
    import time
    indexer_mem._get_connection().execute(
        "INSERT INTO sessions (id, session_key, project_id, started_at, last_message_timestamp, is_closed) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "test-session", 1, 1000, 1000, 0),
    )
    indexer_mem._get_connection().commit()

    start = time.monotonic()
    indexer_mem._close_idle_sessions(timeout=0)
    elapsed = time.monotonic() - start
    # Should return immediately without waiting for summarization
    assert elapsed < 1.0


def test_get_summary_executor_singleton():
    """Executor is a singleton."""
    ex1 = _get_summary_executor()
    ex2 = _get_summary_executor()
    assert ex1 is ex2
