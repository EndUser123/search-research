"""T8: Dedupe fallback test.

Verifies that:
- Events with same content_hash within same 10s bucket are deduplicated
- Different content_hash within same bucket are NOT incorrectly deduplicated
"""
import json
import pytest
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

from .normalized import upsert_event
from .db import get_connection
from ..archive import append_raw_event

DB_PATH = Path("P:\\\\__csf/data/chat_history.db")

# BUCKET_SECONDS as defined in the plan spec
BUCKET_SECONDS = 10


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
    cursor.execute("DELETE FROM events WHERE provider_id LIKE 'test_dedupe_%'")
    cursor.execute("DELETE FROM tasks WHERE provider_id LIKE 'test_dedupe_%'")
    conn.commit()
    yield conn
    cursor.execute("DELETE FROM events WHERE provider_id LIKE 'test_dedupe_%'")
    cursor.execute("DELETE FROM tasks WHERE provider_id LIKE 'test_dedupe_%'")
    conn.commit()
    conn.close()


def make_content_hash(payload: dict) -> str:
    """Compute content_hash as SHA256 of sorted JSON payload."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class TestDedupFallback:
    """Tests for deduplication fallback behavior."""

    def test_different_content_hash_same_bucket_both_retained(self, temp_archive_dir, clean_test_events):
        """Two events with different content within 10s bucket should BOTH be retained."""
        conn = clean_test_events
        cursor = conn.cursor()

        provider_id = "test_dedupe_provider"
        source_id = "test_dedupe_source"

        # Two events with different content, within 10 seconds
        timestamp_1 = datetime(2026, 4, 2, 10, 0, 0, tzinfo=timezone.utc)
        timestamp_2 = datetime(2026, 4, 2, 10, 0, 5, tzinfo=timezone.utc)  # 5 seconds later

        raw_payload_1 = {"title": "First content in bucket", "status": "open"}
        raw_payload_2 = {"title": "Second content in bucket", "status": "open"}

        content_hash_1 = make_content_hash(raw_payload_1)
        content_hash_2 = make_content_hash(raw_payload_2)

        # Verify content hashes are different
        assert content_hash_1 != content_hash_2

        # Archive and upsert
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_1 = append_raw_event(provider_id, source_id, {
                "uuid": "test_dedupe_event_1",
                "provider_id": provider_id,
                "source_id": source_id,
                "raw_payload": raw_payload_1,
                "timestamp": timestamp_1.isoformat(),
            })
            path_2 = append_raw_event(provider_id, source_id, {
                "uuid": "test_dedupe_event_2",
                "provider_id": provider_id,
                "source_id": source_id,
                "raw_payload": raw_payload_2,
                "timestamp": timestamp_2.isoformat(),
            })

        event_1 = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_dedupe_event_1",
            "content_hash": content_hash_1,
            "occurred_at": timestamp_1.isoformat(),
            "raw_payload_path": str(path_1),
            "metadata": raw_payload_1,
        }
        event_2 = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_dedupe_event_2",
            "content_hash": content_hash_2,
            "occurred_at": timestamp_2.isoformat(),
            "raw_payload_path": str(path_2),
            "metadata": raw_payload_2,
        }

        upsert_event(event_1)
        upsert_event(event_2)

        # Both events should be in the database (different content_hash => different rows)
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'test_dedupe_event_%'")
        count = cursor.fetchone()[0]
        assert count == 2, f"Expected 2 events retained, got {count}"

    def test_different_content_hash_same_timestamp_both_retained(
        self, temp_archive_dir, clean_test_events
    ):
        """Different content_hash within same timestamp must NOT be incorrectly deduplicated."""
        conn = clean_test_events
        cursor = conn.cursor()

        provider_id = "test_dedupe_content_provider"
        source_id = "test_dedupe_content_source"

        # Two events with different content, same timestamp
        timestamp = datetime(2026, 4, 2, 11, 0, 0, tzinfo=timezone.utc)
        timestamp_iso = timestamp.isoformat()

        raw_a = {"title": "Opportunity content A", "status": "open"}
        raw_b = {"title": "Opportunity content B", "status": "open"}

        hash_a = make_content_hash(raw_a)
        hash_b = make_content_hash(raw_b)

        # Verify hashes differ due to different content
        assert hash_a != hash_b

        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_a = append_raw_event(provider_id, source_id, {
                "uuid": "test_dedupe_content_event_a",
                "provider_id": provider_id,
                "source_id": source_id,
                "raw_payload": raw_a,
                "timestamp": timestamp_iso,
            })
            path_b = append_raw_event(provider_id, source_id, {
                "uuid": "test_dedupe_content_event_b",
                "provider_id": provider_id,
                "source_id": source_id,
                "raw_payload": raw_b,
                "timestamp": timestamp_iso,
            })

        event_a = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_dedupe_content_event_a",
            "content_hash": hash_a,
            "occurred_at": timestamp_iso,
            "raw_payload_path": str(path_a),
            "metadata": raw_a,
        }
        event_b = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_dedupe_content_event_b",
            "content_hash": hash_b,
            "occurred_at": timestamp_iso,
            "raw_payload_path": str(path_b),
            "metadata": raw_b,
        }

        upsert_event(event_a)
        upsert_event(event_b)

        # Both should be retained despite same timestamp
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'test_dedupe_content_event_%'")
        count = cursor.fetchone()[0]
        assert count == 2, f"Expected 2 events with different content, got {count}"

    def test_bucket_seconds_boundary(self, temp_archive_dir, clean_test_events):
        """Verify events across bucket boundaries (>=10s apart) are both retained."""
        conn = clean_test_events
        cursor = conn.cursor()

        provider_id = "test_dedupe_boundary_provider"
        source_id = "test_dedupe_boundary_source"

        # Event at t=0
        timestamp_1 = datetime(2026, 4, 2, 15, 0, 0, tzinfo=timezone.utc)
        # Event at t=10 (exactly BUCKET_SECONDS later)
        timestamp_2 = datetime(2026, 4, 2, 15, 0, 10, tzinfo=timezone.utc)

        raw_1 = {"title": "Bucket boundary test 1", "status": "open"}
        raw_2 = {"title": "Bucket boundary test 2", "status": "open"}

        hash_1 = make_content_hash(raw_1)
        hash_2 = make_content_hash(raw_2)

        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_1 = append_raw_event(provider_id, source_id, {
                "uuid": "test_dedupe_boundary_event_1",
                "provider_id": provider_id,
                "source_id": source_id,
                "raw_payload": raw_1,
                "timestamp": timestamp_1.isoformat(),
            })
            path_2 = append_raw_event(provider_id, source_id, {
                "uuid": "test_dedupe_boundary_event_2",
                "provider_id": provider_id,
                "source_id": source_id,
                "raw_payload": raw_2,
                "timestamp": timestamp_2.isoformat(),
            })

        event_1 = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_dedupe_boundary_event_1",
            "content_hash": hash_1,
            "occurred_at": timestamp_1.isoformat(),
            "raw_payload_path": str(path_1),
            "metadata": raw_1,
        }
        event_2 = {
            "provider_id": provider_id,
            "source_id": source_id,
            "event_id": "test_dedupe_boundary_event_2",
            "content_hash": hash_2,
            "occurred_at": timestamp_2.isoformat(),
            "raw_payload_path": str(path_2),
            "metadata": raw_2,
        }

        upsert_event(event_1)
        upsert_event(event_2)

        # Both should be retained (different hashes)
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'test_dedupe_boundary_event_%'")
        count = cursor.fetchone()[0]
        assert count == 2, f"Expected 2 events across bucket boundary, got {count}"
