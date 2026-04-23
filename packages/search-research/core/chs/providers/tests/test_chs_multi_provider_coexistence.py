"""T3: Multi-provider coexistence test.

Verifies that:
- Events from different providers are stored with correct provider_id
- Events with same content from DIFFERENT providers are NOT deduplicated
- Events with same content within SAME provider ARE deduplicated
"""
import pytest
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

from .normalized import upsert_event, get_events_by_hash
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
    cursor.execute("DELETE FROM events WHERE provider_id LIKE 'test_multi_%'")
    cursor.execute("DELETE FROM tasks WHERE provider_id LIKE 'test_multi_%'")
    conn.commit()
    yield conn
    cursor.execute("DELETE FROM events WHERE provider_id LIKE 'test_multi_%'")
    cursor.execute("DELETE FROM tasks WHERE provider_id LIKE 'test_multi_%'")
    conn.commit()
    conn.close()


def make_content_hash(payload: dict) -> str:
    """Compute content_hash as SHA256 of sorted JSON payload."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class TestMultiProviderCoexistence:
    """Tests for multi-provider coexistence."""

    def test_different_providers_same_content_not_deduplicated(
        self, temp_archive_dir, clean_test_events
    ):
        """Same content from different providers must NOT be deduplicated."""
        conn = clean_test_events

        provider_a = "test_multi_claude_code"
        provider_b = "test_multi_codex_desktop"
        source_id = "test_multi_source_123"
        timestamp = datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc).isoformat()

        raw_payload_a = {
            "title": "Test task: multi-provider coexistence check",
            "status": "open",
        }
        raw_payload_b = dict(raw_payload_a)
        hash_a = make_content_hash(raw_payload_a)
        hash_b = make_content_hash(raw_payload_b)

        event_a = {
            "uuid": "test_multi_task_a1",
            "provider_id": provider_a,
            "source_id": source_id,
            "event_type": "task_created",
            "raw_payload": raw_payload_a,
            "timestamp": timestamp,
        }
        event_b = {
            "uuid": "test_multi_task_b1",
            "provider_id": provider_b,
            "source_id": source_id,
            "event_type": "task_created",
            "raw_payload": raw_payload_b,
            "timestamp": timestamp,
        }

        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_a = append_raw_event(provider_a, source_id, event_a)
            path_b = append_raw_event(provider_b, source_id, event_b)

        normalized_a = {
            "provider_id": provider_a,
            "source_id": source_id,
            "event_id": "test_multi_task_a1",
            "content_hash": hash_a,
            "occurred_at": timestamp,
            "raw_payload_path": str(path_a),
            "metadata": raw_payload_a,
        }
        normalized_b = {
            "provider_id": provider_b,
            "source_id": source_id,
            "event_id": "test_multi_task_b1",
            "content_hash": hash_b,
            "occurred_at": timestamp,
            "raw_payload_path": str(path_b),
            "metadata": raw_payload_b,
        }

        upsert_event(normalized_a)
        upsert_event(normalized_b)

        events_a = get_events_by_hash(provider_a, source_id, hash_a)
        events_b = get_events_by_hash(provider_b, source_id, hash_b)

        assert len(events_a) == 1
        assert len(events_b) == 1
        assert events_a[0]["provider_id"] == provider_a
        assert events_b[0]["provider_id"] == provider_b

    def test_same_provider_same_content_is_deduplicated(
        self, temp_archive_dir, clean_test_events
    ):
        """Same content from SAME provider must be deduplicated to one row."""
        conn = clean_test_events

        provider = "test_multi_claude_code"
        source_id = "test_multi_source_456"
        timestamp = datetime(2026, 4, 2, 13, 0, 0, tzinfo=timezone.utc).isoformat()

        raw_payload = {"title": "Test dedup content", "status": "open"}
        content_hash = make_content_hash(raw_payload)

        event_1 = {
            "uuid": "test_multi_task_dedup1",
            "provider_id": provider,
            "source_id": source_id,
            "event_type": "task_created",
            "raw_payload": raw_payload,
            "timestamp": timestamp,
        }
        event_2 = {
            "uuid": "test_multi_task_dedup2",
            "provider_id": provider,
            "source_id": source_id,
            "event_type": "task_created",
            "raw_payload": raw_payload,
            "timestamp": timestamp,
        }

        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_1 = append_raw_event(provider, source_id, event_1)
            path_2 = append_raw_event(provider, source_id, event_2)

        normalized_1 = {
            "provider_id": provider,
            "source_id": source_id,
            "event_id": "test_multi_task_dedup1",
            "content_hash": content_hash,
            "occurred_at": timestamp,
            "raw_payload_path": str(path_1),
            "metadata": raw_payload,
        }
        normalized_2 = {
            "provider_id": provider,
            "source_id": source_id,
            "event_id": "test_multi_task_dedup2",
            "content_hash": content_hash,
            "occurred_at": timestamp,
            "raw_payload_path": str(path_2),
            "metadata": raw_payload,
        }

        upsert_event(normalized_1)
        upsert_event(normalized_2)

        events = get_events_by_hash(provider, source_id, content_hash)
        assert len(events) == 1, f"Expected 1 row after dedup, got {len(events)}"

    def test_provider_ids_are_correctly_separated(
        self, temp_archive_dir, clean_test_events
    ):
        """Verify events from different providers get distinct provider_id values."""
        conn = clean_test_events

        timestamp = datetime(2026, 4, 2, 14, 0, 0, tzinfo=timezone.utc).isoformat()

        raw_a = {"title": "Provider A task", "status": "open"}
        hash_a = make_content_hash(raw_a)
        event_a = {
            "uuid": "test_multi_task_a_separate",
            "provider_id": "test_multi_provider_a",
            "source_id": "test_multi_src_a",
            "event_type": "task_created",
            "raw_payload": raw_a,
            "timestamp": timestamp,
        }

        raw_b = {"title": "Provider B opportunity", "status": "open"}
        hash_b = make_content_hash(raw_b)
        event_b = {
            "uuid": "test_multi_task_b_separate",
            "provider_id": "test_multi_provider_b",
            "source_id": "test_multi_src_b",
            "event_type": "task_created",
            "raw_payload": raw_b,
            "timestamp": timestamp,
        }

        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_dir):
            path_a = append_raw_event("test_multi_provider_a", "test_multi_src_a", event_a)
            path_b = append_raw_event("test_multi_provider_b", "test_multi_src_b", event_b)

        normalized_a = {
            "provider_id": "test_multi_provider_a",
            "source_id": "test_multi_src_a",
            "event_id": "test_multi_task_a_separate",
            "content_hash": hash_a,
            "occurred_at": timestamp,
            "raw_payload_path": str(path_a),
            "metadata": raw_a,
        }
        normalized_b = {
            "provider_id": "test_multi_provider_b",
            "source_id": "test_multi_src_b",
            "event_id": "test_multi_task_b_separate",
            "content_hash": hash_b,
            "occurred_at": timestamp,
            "raw_payload_path": str(path_b),
            "metadata": raw_b,
        }

        upsert_event(normalized_a)
        upsert_event(normalized_b)

        events_a = get_events_by_hash("test_multi_provider_a", "test_multi_src_a", hash_a)
        events_b = get_events_by_hash("test_multi_provider_b", "test_multi_src_b", hash_b)

        assert len(events_a) == 1
        assert len(events_b) == 1
        assert events_a[0]["provider_id"] == "test_multi_provider_a"
        assert events_b[0]["provider_id"] == "test_multi_provider_b"
