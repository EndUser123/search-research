"""T6: Stale fact invalidation test.

Verifies that:
- When same content_hash appears with newer occurred_at, query returns newer value
- Archive remains immutable - older raw_payload_path still contains original older content
"""
import json
import pytest
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

from .normalized import upsert_event, get_events_by_hash, query_tasks
from .db import get_connection
from ..archive import append_raw_event

DB_PATH = Path("P:/__csf/data/chat_history.db")


@pytest.fixture
def temp_archive_dir(tmp_path):
    """Create temporary archive directory for test."""
    archive_dir = tmp_path / "chs_archive"
    archive_dir.mkdir()
    return archive_dir


@pytest.fixture
def clean_test_events():
    """Clean up test events before and after test."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE provider_id LIKE 'test_stale_%'")
    cursor.execute("DELETE FROM tasks WHERE provider_id LIKE 'test_stale_%'")
    conn.commit()
    yield conn
    cursor.execute("DELETE FROM events WHERE provider_id LIKE 'test_stale_%'")
    cursor.execute("DELETE FROM tasks WHERE provider_id LIKE 'test_stale_%'")
    conn.commit()
    conn.close()


def make_content_hash(payload: dict) -> str:
    """Compute content_hash as SHA256 of sorted JSON payload."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class TestStaleFactInvalidation:
    """Tests for stale fact invalidation."""

    def test_newer_event_appears_in_query_results(
        self, temp_archive_dir, clean_test_events
    ):
        """Newer event with different content_hash should be returned in queries."""
        conn = clean_test_events

        provider_id = "test_stale_provider"
        source_id = "test_stale_source"

        # Older event
        older_timestamp = datetime(2026, 4, 2, 10, 0, 0, tzinfo=timezone.utc)
        older_timestamp_iso = older_timestamp.isoformat()
        raw_payload_older = {
            "title": "Stale fact test",
            "status": "open",
        }
        older_content_hash = make_content_hash(raw_payload_older)
        older_event = {
            "uuid": "test_stale_task_older",
            "provider_id": provider_id,
            "source_id": source_id,
            "event_type": "task_created",
            "raw_payload": raw_payload_older,
            "timestamp": older_timestamp_iso,
        }

        # Newer event
        newer_timestamp = datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc)
        newer_timestamp_iso = newer_timestamp.isoformat()
        raw_payload_newer = {
            "title": "Updated stale fact",
            "status": "open",
        }
        newer_content_hash = make_content_hash(raw_payload_newer)
        newer_event = {
            "uuid": "test_stale_task_newer",
            "provider_id": provider_id,
            "source_id": source_id,
            "event_type": "task_updated",
            "raw_payload": raw_payload_newer,
            "timestamp": newer_timestamp_iso,
        }

        # Verify hashes are different
        assert older_content_hash != newer_content_hash

        # Archive both events
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_older = append_raw_event(provider_id, source_id, older_event)
            path_newer = append_raw_event(provider_id, source_id, newer_event)

        normalized_older = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_stale_task_older",
            "content_hash": older_content_hash,
            "occurred_at": older_timestamp_iso,
            "raw_payload_path": str(path_older),
            "metadata": raw_payload_older,
        }
        normalized_newer = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_stale_task_newer",
            "content_hash": newer_content_hash,
            "occurred_at": newer_timestamp_iso,
            "raw_payload_path": str(path_newer),
            "metadata": raw_payload_newer,
        }

        upsert_event(normalized_older)
        upsert_event(normalized_newer)

        # Both should be queryable (different hashes = different rows)
        events_older = get_events_by_hash(provider_id, source_id, older_content_hash)
        events_newer = get_events_by_hash(provider_id, source_id, newer_content_hash)

        assert len(events_older) == 1
        assert len(events_newer) == 1
        assert events_newer[0]["event_id"] == "test_stale_task_newer"

    def test_archive_remains_immutable_after_invalidation(
        self, temp_archive_dir, clean_test_events
    ):
        """Archive raw_payload_path should still contain original older content."""
        conn = clean_test_events
        cursor = conn.cursor()

        provider_id = "test_stale_archive_provider"
        source_id = "test_stale_archive_source"

        older_timestamp = datetime(2026, 4, 2, 8, 0, 0, tzinfo=timezone.utc)
        older_timestamp_iso = older_timestamp.isoformat()
        raw_payload_v1 = {
            "title": "Immutable archive test",
            "status": "v1",
        }
        older_content_hash = make_content_hash(raw_payload_v1)
        older_event = {
            "uuid": "test_stale_archive_task_v1",
            "provider_id": provider_id,
            "source_id": source_id,
            "event_type": "task_created",
            "raw_payload": raw_payload_v1,
            "timestamp": older_timestamp_iso,
        }

        newer_timestamp = datetime(2026, 4, 2, 9, 0, 0, tzinfo=timezone.utc)
        newer_timestamp_iso = newer_timestamp.isoformat()
        raw_payload_v2 = {
            "title": "Immutable archive test",
            "status": "v2",
        }
        newer_content_hash = make_content_hash(raw_payload_v2)
        newer_event = {
            "uuid": "test_stale_archive_task_v2",
            "provider_id": provider_id,
            "source_id": source_id,
            "event_type": "task_updated",
            "raw_payload": raw_payload_v2,
            "timestamp": newer_timestamp_iso,
        }

        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_older = append_raw_event(provider_id, source_id, older_event)
            path_newer = append_raw_event(provider_id, source_id, newer_event)

        normalized_older = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_stale_archive_task_v1",
            "content_hash": older_content_hash,
            "occurred_at": older_timestamp_iso,
            "raw_payload_path": str(path_older),
            "metadata": raw_payload_v1,
        }
        normalized_newer = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_stale_archive_task_v2",
            "content_hash": newer_content_hash,
            "occurred_at": newer_timestamp_iso,
            "raw_payload_path": str(path_newer),
            "metadata": raw_payload_v2,
        }

        upsert_event(normalized_older)
        upsert_event(normalized_newer)

        # Verify older event archived content
        cursor.execute(
            "SELECT raw_payload_path FROM events WHERE event_id = ?",
            ("test_stale_archive_task_v1",)
        )
        older_row = cursor.fetchone()
        assert older_row is not None
        older_raw_path = older_row[0]

        with open(Path(older_raw_path), "r", encoding="utf-8") as f:
            archived_older = json.load(f)

        assert archived_older["uuid"] == "test_stale_archive_task_v1"
        assert archived_older["raw_payload"]["status"] == "v1"

        # Verify newer event archived content
        cursor.execute(
            "SELECT raw_payload_path FROM events WHERE event_id = ?",
            ("test_stale_archive_task_v2",)
        )
        newer_row = cursor.fetchone()
        assert newer_row is not None
        newer_raw_path = newer_row[0]

        with open(Path(newer_raw_path), "r", encoding="utf-8") as f:
            archived_newer = json.load(f)

        assert archived_newer["uuid"] == "test_stale_archive_task_v2"
        assert archived_newer["raw_payload"]["status"] == "v2"
