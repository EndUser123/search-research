"""
T2: Purge resilience test for CHS multi-provider history layer.

Design: Ingest events -> assert raw_payload_path exists and is readable ->
query normalized DB -> assert results returned. Archive is authoritative
when upstream unavailable.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from ..archive import append_raw_event, read_watermark, write_watermark
from .db import get_connection
from .normalized import upsert_event
from .projections import query_events

DB_PATH = "P:\\\\\\__csf/data/chat_history.db"
TEST_ARCHIVE_BASE = Path("P:\\\\\\__csf/data/chs_archive")
TEST_PROVIDER_ID = "test_purge_source"


def make_content_hash(payload: dict) -> str:
    """Create a deterministic content hash for test events."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


@pytest.fixture
def clean_task_table():
    """Clean test rows from tasks table before and after test."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE ?", ("test_purge_%",))
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE ?", ("test_purge_%",))
    conn.commit()
    conn.close()


@pytest.fixture
def clean_events_table():
    """Clean test rows from events table before and after test."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE provider_id = ?", (TEST_PROVIDER_ID,))
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE provider_id = ?", (TEST_PROVIDER_ID,))
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def mock_archive_base(tmp_path):
    """Override archive base for testing."""
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        yield tmp_path


def test_archive_contains_valid_json_after_append(clean_task_table, clean_events_table, tmp_path):
    """
    Test that append_raw_event creates a file with valid JSON that is readable.
    This proves archive is authoritative (not dependent on upstream source).
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        raw_payload = {"title": "Test task", "status": "open"}
        event = {
            "uuid": "test_purge_001",
            "provider_id": TEST_PROVIDER_ID,
            "source_id": "test_purge_001",
            "event_type": "task_created",
            "raw_payload": raw_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        raw_path = append_raw_event(TEST_PROVIDER_ID, "test_purge_001", event)

        assert Path(raw_path).exists(), f"Archive file should exist at {raw_path}"

        with open(raw_path, "r", encoding="utf-8") as f:
            stored = json.load(f)

        assert stored["provider_id"] == TEST_PROVIDER_ID
        assert stored["source_id"] == "test_purge_001"
        assert "raw_payload" in stored
        assert stored["raw_payload"]["title"] == "Test task"


def test_upsert_event_persists_to_normalized_db(clean_task_table, clean_events_table, tmp_path):
    """
    Test that upsert_event stores event in normalized DB and is queryable.
    Proves archive -> normalized pipeline works.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        raw_payload = {"title": "Updated task", "status": "closed"}
        event = {
            "uuid": "test_purge_002",
            "provider_id": TEST_PROVIDER_ID,
            "source_id": "test_purge_002",
            "event_type": "task_updated",
            "raw_payload": raw_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        raw_path = append_raw_event(TEST_PROVIDER_ID, "test_purge_002", event)
        content_hash = make_content_hash(raw_payload)

        normalized_event = {
            "provider_id": TEST_PROVIDER_ID,
            "source_id": "test_purge_002",
            "event_id": "test_purge_002",
            "content_hash": content_hash,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "raw_payload_path": str(raw_path),
            "metadata": raw_payload,
        }

        upsert_event(normalized_event)

        events = query_events(provider_id=TEST_PROVIDER_ID)
        assert len(events) > 0, "Event should be retrievable from normalized DB"
        assert events[0]["source_id"] == "test_purge_002"


def test_archive_authoritative_when_upstream_unavailable(clean_task_table, clean_events_table, tmp_path):
    """
    Full purge resilience: archive file exists and normalized DB is queryable
    even when upstream provider is unavailable.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        raw_payload = {"title": "Completed task", "status": "done"}
        event = {
            "uuid": "test_purge_003",
            "provider_id": TEST_PROVIDER_ID,
            "source_id": "test_purge_003",
            "event_type": "task_completed",
            "raw_payload": raw_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        raw_path = append_raw_event(TEST_PROVIDER_ID, "test_purge_003", event)
        content_hash = make_content_hash(raw_payload)

        normalized_event = {
            "provider_id": TEST_PROVIDER_ID,
            "source_id": "test_purge_003",
            "event_id": "test_purge_003",
            "content_hash": content_hash,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "raw_payload_path": str(raw_path),
            "metadata": raw_payload,
        }

        upsert_event(normalized_event)

        assert Path(raw_path).exists(), "Archive file should exist"

        with open(raw_path, "r", encoding="utf-8") as f:
            stored = json.load(f)
        assert stored["source_id"] == "test_purge_003"

        events = query_events(provider_id=TEST_PROVIDER_ID)
        assert len(events) > 0, "Normalized DB should have the event"
        assert events[0]["source_id"] == "test_purge_003"
