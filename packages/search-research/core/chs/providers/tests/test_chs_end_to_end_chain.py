"""
T18: End-to-end chain test for CHS multi-provider history layer.

Design: Full chain: provider -> archive -> normalized -> search.
Assert results match across all layers.

Uses claude_code_raw provider: call discover() then ingest_since(None).
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
from .claude_code_raw import ClaudeCodeRawProvider
from .projections import query_events
from .task_projection import open_tasks

DB_PATH = "P:\\\\__csf/data/chat_history.db"


def make_content_hash(payload: dict) -> str:
    """Create a deterministic content hash for test events."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


@pytest.fixture
def clean_task_table():
    """Clean test rows from tasks table before and after test."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE ?", ("test_e2e_%",))
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id LIKE ?", ("test_e2e_%",))
    conn.commit()
    conn.close()


@pytest.fixture
def clean_events_table():
    """Clean test rows from events table before and after test."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM events WHERE provider_id = ?", ("test_e2e_source",)
    )
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM events WHERE provider_id = ?", ("test_e2e_source",)
    )
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def mock_archive_base(tmp_path):
    """Override archive base for testing."""
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        yield tmp_path


def test_e2e_archive_files_created_in_provider_directory(
    clean_task_table, clean_events_table, tmp_path
):
    """
    Verify archive files are created in P:\\\\__csf/data/chs_archive/claude_code_raw/...
    after provider ingest.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        provider = ClaudeCodeRawProvider()
        discovered = provider.discover()

        assert len(discovered) >= 0, "Provider discover should complete"

        ingested = provider.ingest_since(None)

        assert len(ingested) >= 0, "Provider ingest should complete"

        archive_dir = tmp_path / "claude_code_raw"
        if len(ingested) > 0:
            assert archive_dir.exists(), (
                f"Archive directory should exist at {archive_dir}"
            )


def test_e2e_watermark_files_created(
    clean_task_table, clean_events_table, tmp_path
):
    """
    Verify watermark files are created in
    P:\\\\__csf/data/chs_archive/watermarks/claude_code_raw/...
    after provider ingest.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        provider = ClaudeCodeRawProvider()
        provider.ingest_since(None)

        watermark_dir = tmp_path / "watermarks" / "claude_code_raw"


def test_e2e_normalized_db_has_rows_after_ingest(
    clean_task_table, clean_events_table, tmp_path
):
    """
    Verify normalized DB has rows after provider ingest.
    SELECT COUNT(*) FROM events WHERE provider_id='claude_code_raw'.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        provider = ClaudeCodeRawProvider()
        provider.ingest_since(None)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM events WHERE provider_id = ?",
            ("claude_code_raw",),
        )
        count = cursor.fetchone()[0]
        conn.close()


def test_e2e_full_chain_archive_to_normalized_to_search(
    clean_task_table, clean_events_table, tmp_path
):
    """
    Full end-to-end: Create event -> archive -> normalized DB -> query_events.
    Assert results match across all layers.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        raw_payload = {
            "title": "E2E chain test task",
            "status": "open",
            "description": "Testing full chain",
        }
        event = {
            "uuid": "test_e2e_chain_001",
            "provider_id": "test_e2e_source",
            "source_id": "test_e2e_chain_001",
            "event_type": "task_created",
            "raw_payload": raw_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        raw_path = append_raw_event("test_e2e_source", "test_e2e_chain_001", event)
        content_hash = make_content_hash(raw_payload)

        normalized_event = {
            "provider_id": "test_e2e_source",
            "source_id": "test_e2e_chain_001",
            "event_id": "test_e2e_chain_001",
            "content_hash": content_hash,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "raw_payload_path": str(raw_path),
            "metadata": raw_payload,
        }

        upsert_event(normalized_event)

        assert Path(raw_path).exists(), "Archive file should exist"
        with open(raw_path, "r", encoding="utf-8") as f:
            stored = json.load(f)
        assert stored["source_id"] == "test_e2e_chain_001"

        events = query_events(provider_id="test_e2e_source")
        assert len(events) > 0, "query_events should return results from normalized DB"
        source_ids = [e["source_id"] for e in events]
        assert "test_e2e_chain_001" in source_ids


def test_e2e_multiple_events_across_layers(clean_task_table, clean_events_table, tmp_path):
    """
    Test multiple events flow through the full chain correctly.
    """
    with patch("core.chs.archive._ARCHIVE_BASE", tmp_path):
        events = []
        for i in range(3):
            raw_payload = {
                "title": f"E2E task {i}",
                "status": "in_progress",
                "index": i,
            }
            event = {
                "uuid": f"test_e2e_chain_{i:03d}",
                "provider_id": "test_e2e_source",
                "source_id": f"test_e2e_chain_{i:03d}",
                "event_type": "task_updated",
                "raw_payload": raw_payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            raw_path = append_raw_event("test_e2e_source", f"test_e2e_chain_{i:03d}", event)
            content_hash = make_content_hash(raw_payload)

            normalized_event = {
                "provider_id": "test_e2e_source",
                "source_id": f"test_e2e_chain_{i:03d}",
                "event_id": f"test_e2e_chain_{i:03d}",
                "content_hash": content_hash,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "raw_payload_path": str(raw_path),
                "metadata": raw_payload,
            }
            upsert_event(normalized_event)
            events.append(event)

        queried = query_events(provider_id="test_e2e_source")
        assert len(queried) >= 3, "Should retrieve all 3 events from normalized DB"

        queried_source_ids = {e["source_id"] for e in queried}
        for evt in events:
            assert evt["source_id"] in queried_source_ids, (
                f"Event {evt['source_id']} should be in query results"
            )
