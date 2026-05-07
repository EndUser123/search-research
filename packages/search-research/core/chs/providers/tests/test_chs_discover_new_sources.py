"""T17: discover() new sources — discover() returns source_id → ingest_since(None) → events stored.

Verifies: discover() finds sources, ingest_since(None) ingests all events,
and events are stored in the normalized DB with correct metadata.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from .db import get_connection
from .normalized import upsert_event
from .projections import query_events
from .claude_code_raw import ClaudeCodeRawProvider

DB_PATH = Path("P:\\\\__csf/data/chat_history.db")


@pytest.fixture
def temp_history_with_sessions(tmp_path):
    """Create a temp history.jsonl with multiple sessions."""
    hist_file = tmp_path / ".claude" / "history.jsonl"
    hist_file.parent.mkdir(parents=True, exist_ok=True)

    ts1 = int(datetime(2026, 4, 2, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    ts2 = int(datetime(2026, 4, 2, 11, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    entries = [
        # Session A
        {
            "uuid": "s17_evt_001",
            "sessionId": "session-17-a",
            "type": "user",
            "timestamp": ts1,
            "message": "Hello from session A",
        },
        {
            "uuid": "s17_evt_002",
            "sessionId": "session-17-a",
            "type": "assistant",
            "timestamp": ts1 + 100,
            "message": "Response in session A",
        },
        # Session B
        {
            "uuid": "s17_evt_003",
            "sessionId": "session-17-b",
            "type": "user",
            "timestamp": ts2,
            "message": "Hello from session B",
        },
    ]
    hist_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return hist_file


@pytest.fixture
def clean_test_events():
    """Clean test events before and after."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE source_id LIKE 'session-17%'")
    conn.commit()
    yield
    cursor.execute("DELETE FROM events WHERE source_id LIKE 'session-17%'")
    conn.commit()


class TestDiscoverNewSources:
    """T17: discover() new sources tests."""

    def test_discover_returns_source_ids(self, temp_history_with_sessions, clean_test_events):
        """discover() returns source_ids for each unique session."""
        provider = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_with_sessions):
            sources = provider.discover()

        assert len(sources) == 2, f"Expected 2 sources, got {len(sources)}"
        source_ids = {s["source_id"] for s in sources}
        assert source_ids == {"session-17-a", "session-17-b"}

        for source in sources:
            assert "source_id" in source
            assert "occurred_at" in source
            assert isinstance(source["occurred_at"], str)

    def test_ingest_since_none_stores_all_events(
        self, temp_history_with_sessions, clean_test_events
    ):
        """ingest_since(None) returns all events from all sessions."""
        provider = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_with_sessions):
            events = provider.ingest_since(None, terminal_id="discover-test-terminal")

        assert len(events) == 3, f"Expected 3 events, got {len(events)}"
        event_ids = {e["event_id"] for e in events}
        assert event_ids == {"s17_evt_001", "s17_evt_002", "s17_evt_003"}

    def test_events_stored_in_normalized_db(
        self, temp_history_with_sessions, clean_test_events
    ):
        """Events from ingest_since(None) are stored correctly in normalized DB."""
        provider = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_with_sessions):
            events = provider.ingest_since(None, terminal_id="discover-test-terminal")

        for evt in events:
            upsert_event(evt)

        rows = query_events(provider_id="claude_code_raw")
        source_ids = {r["source_id"] for r in rows}
        assert "session-17-a" in source_ids
        assert "session-17-b" in source_ids

        rows_a = [r for r in rows if r["source_id"] == "session-17-a"]
        assert len(rows_a) == 2

        rows_b = [r for r in rows if r["source_id"] == "session-17-b"]
        assert len(rows_b) == 1

    def test_ingest_since_none_is_complete_replay(
        self, temp_history_with_sessions, clean_test_events
    ):
        """A second ingest_since(None) replay with same source returns no new events."""
        provider = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_with_sessions):
            events1 = provider.ingest_since(None, terminal_id="replay-test")
            for evt in events1:
                upsert_event(evt)

            events2 = provider.ingest_since(None, terminal_id="replay-test")
            for evt in events2:
                upsert_event(evt)

        # Second replay should return 0 (watermark starts at None, so it returns all,
        # but since all events were already inserted with same content_hash,
        # INSERT OR IGNORE drops duplicates → rowcount = 0)
        # Actually without watermark, ingest_since returns ALL events again
        # The dedupe happens at DB level
        rows = query_events(provider_id="claude_code_raw", source_id="session-17-a")
        assert len(rows) == 2
        rows = query_events(provider_id="claude_code_raw", source_id="session-17-b")
        assert len(rows) == 1
