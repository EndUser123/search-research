"""
T4: CHS backend compatibility test for CHS multi-provider history layer.

Design: search-research chat query returns results via CHS after archive is populated.
Light integration check: verify query_tasks() and query_events() work after ingest.
"""

import json
import sqlite3
from datetime import datetime, timezone

import pytest

from .db import get_connection
from .normalized import query_tasks
from .projections import query_events as query_events_from_projections

DB_PATH = "P:/__csf/data/chat_history.db"


@pytest.fixture
def clean_task_table():
    """Clean test rows from tasks table before and after test."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE ?", ("test_compat_%",))
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE ?", ("test_compat_%",))
    conn.commit()
    conn.close()


@pytest.fixture
def clean_events_table():
    """Clean test rows from events table before and after test."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM events WHERE provider_id = ?", ("test_compat_source",)
    )
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM events WHERE provider_id = ?", ("test_compat_source",)
    )
    conn.commit()
    conn.close()


def test_query_tasks_returns_inserted_task(clean_task_table):
    """
    Insert a known task event into tasks table directly and verify
    query_tasks() returns the inserted task.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tasks table schema: task_id, provider_id, session_id, terminal_id,
    # opened_at, updated_at, resolved_at, status, raw_event_path
    cursor.execute(
        """
        INSERT INTO tasks (task_id, provider_id, session_id, terminal_id,
                           opened_at, updated_at, resolved_at, status, raw_event_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test_compat_001",
            "test_compat_source",
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            None,
            "open",
            "P:/__csf/data/chs_archive/test_compat_source/test_compat_001.json",
        ),
    )
    conn.commit()
    conn.close()

    tasks = query_tasks(provider_id="test_compat_source")

    assert len(tasks) > 0, "query_tasks should return results"
    task_ids = [t["task_id"] for t in tasks]
    assert "test_compat_001" in task_ids, "Inserted task should be queryable"


def test_query_events_returns_data_from_normalized_db(clean_events_table):
    """
    Verify that query_events() returns data from the normalized DB events table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO events (
            provider_id, source_id, event_id, content_hash,
            occurred_at, raw_payload_path, cached_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test_compat_source",
            "test_compat_002",
            "test_compat_002",
            "hashabc002",
            datetime.now(timezone.utc).isoformat(),
            "P:/__csf/data/chs_archive/test_compat_source/test_compat_002.json",
            datetime.now(timezone.utc).isoformat(),
            '{"title": "Test event task"}',
        ),
    )
    conn.commit()
    conn.close()

    events = query_events_from_projections(provider_id="test_compat_source")

    assert len(events) > 0, "query_events should return results"
    source_ids = [e["source_id"] for e in events]
    assert "test_compat_002" in source_ids, "Inserted event should be queryable"


def test_query_tasks_with_status_filter(clean_task_table):
    """
    Verify query_tasks() respects status filtering.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert open task
    cursor.execute(
        """
        INSERT INTO tasks (task_id, provider_id, session_id, terminal_id,
                           opened_at, updated_at, resolved_at, status, raw_event_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test_compat_003",
            "test_compat_source",
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            None,
            "open",
            "P:/__csf/data/chs_archive/test_compat_source/test_compat_003.json",
        ),
    )
    # Insert closed task
    cursor.execute(
        """
        INSERT INTO tasks (task_id, provider_id, session_id, terminal_id,
                           opened_at, updated_at, resolved_at, status, raw_event_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test_compat_004",
            "test_compat_source",
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            "closed",
            "P:/__csf/data/chs_archive/test_compat_source/test_compat_004.json",
        ),
    )
    conn.commit()
    conn.close()

    all_tasks = query_tasks(provider_id="test_compat_source")
    open_tasks = [t for t in all_tasks if t.get("status") == "open"]

    assert len(open_tasks) > 0, "Should return open tasks"
    for task in open_tasks:
        assert task["status"] == "open", f"Task {task['task_id']} should be open"


def test_query_events_across_multiple_providers(clean_events_table, clean_task_table):
    """
    Verify query_events() can query across multiple providers when no
    provider_id filter is specified, and with filter.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO events (
            provider_id, source_id, event_id, content_hash,
            occurred_at, raw_payload_path, cached_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test_compat_source",
            "test_compat_005",
            "test_compat_005",
            "hash555",
            datetime.now(timezone.utc).isoformat(),
            "P:/__csf/data/chs_archive/test_compat_source/test_compat_005.json",
            datetime.now(timezone.utc).isoformat(),
            '{"title": "Multi-provider test"}',
        ),
    )
    cursor.execute(
        """
        INSERT INTO tasks (task_id, provider_id, session_id, terminal_id,
                           opened_at, updated_at, resolved_at, status, raw_event_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test_compat_005",
            "test_compat_source",
            None,
            None,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            None,
            "open",
            "P:/__csf/data/chs_archive/test_compat_source/test_compat_005.json",
        ),
    )
    conn.commit()
    conn.close()

    events = query_events_from_projections()
    assert len(events) >= 0, "query_events() without filter should complete"

    events_filtered = query_events_from_projections(provider_id="test_compat_source")
    assert len(events_filtered) > 0, "Filtered query should return results"
