"""T1: Provider ingest idempotency — replay same source twice → no duplicates in normalized DB.

Verifies: ingest_since() called twice with same watermark returns 0 new events
on second call, and query returns only unique events.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from core.chs.db import get_connection
from core.chs.normalized import upsert_event
from core.chs.projections import query_events
from core.chs.providers.claude_code_raw import ClaudeCodeRawProvider

DB_PATH = Path("P:/__csf/data/chat_history.db")


@pytest.fixture
def temp_history_jsonl(tmp_path):
    """Create a temp history.jsonl with known events."""
    hist_file = tmp_path / ".claude" / "history.jsonl"
    hist_file.parent.mkdir(parents=True, exist_ok=True)

    ts = int(datetime(2026, 4, 2, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    entries = [
        {
            "uuid": "evt_001",
            "sessionId": "idempotency-test-session",
            "type": "user",
            "timestamp": ts,
            "message": "Hello world",
        },
        {
            "uuid": "evt_002",
            "sessionId": "idempotency-test-session",
            "type": "assistant",
            "timestamp": ts + 100,
            "message": "Hi there",
        },
    ]
    hist_file.write_text(json.dumps(entries[0]) + "\n" + json.dumps(entries[1]) + "\n")
    return hist_file


@pytest.fixture
def clean_test_events():
    """Clean test events before and after."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE provider_id = 'claude_code_raw' AND source_id LIKE 'idempotency%'")
    conn.commit()
    yield conn
    cursor.execute("DELETE FROM events WHERE provider_id = 'claude_code_raw' AND source_id LIKE 'idempotency%'")
    conn.commit()


class TestIngestIdempotency:
    """T1: Provider ingest idempotency tests."""

    def test_first_ingest_returns_events_second_returns_empty(
        self, temp_history_jsonl, clean_test_events
    ):
        """First ingest_since(None) returns events; second call with same watermark returns nothing."""
        provider = ClaudeCodeRawProvider()

        with patch.object(provider, "discover", return_value=[]):
            with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_jsonl):
                # First ingest — no watermark, returns all events
                events1 = provider.ingest_since(None, terminal_id="test_terminal")
                assert len(events1) == 2, f"Expected 2 events on first ingest, got {len(events1)}"

                # Store events in normalized DB
                for evt in events1:
                    upsert_event(evt)

                # Build watermark from last event
                last_evt = events1[-1]
                watermark = {
                    "last_event_id": last_evt["event_id"],
                    "last_occurred_at": last_evt["occurred_at"],
                    "terminal_id": "test_terminal",
                }

                # Second ingest with watermark — should return nothing new
                events2 = provider.ingest_since(watermark, terminal_id="test_terminal")
                assert len(events2) == 0, f"Expected 0 events on second ingest (idempotent), got {len(events2)}"

    def test_normalized_db_has_no_duplicates_after_replay(
        self, temp_history_jsonl, clean_test_events
    ):
        """After two replays, normalized DB contains only unique events (no duplicates)."""
        provider = ClaudeCodeRawProvider()

        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_jsonl):
            # First ingest
            events1 = provider.ingest_since(None, terminal_id="test_terminal")
            for evt in events1:
                upsert_event(evt)

            last_evt = events1[-1]
            watermark = {
                "last_event_id": last_evt["event_id"],
                "last_occurred_at": last_evt["occurred_at"],
                "terminal_id": "test_terminal",
            }

            # Second ingest (idempotent replay)
            events2 = provider.ingest_since(watermark, terminal_id="test_terminal")
            for evt in events2:
                upsert_event(evt)

        # Query normalized DB — should have exactly 2 unique events
        rows = query_events(provider_id="claude_code_raw", source_id="idempotency-test-session")
        assert len(rows) == 2, f"Expected 2 unique events in DB, got {len(rows)}"

        event_ids = {r["event_id"] for r in rows}
        assert event_ids == {"evt_001", "evt_002"}

    def test_watermark_advance_prevents_reingest(self, temp_history_jsonl, clean_test_events):
        """Advancing watermark to latest event prevents reingest of that event."""
        provider = ClaudeCodeRawProvider()

        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_jsonl):
            # First ingest
            events1 = provider.ingest_since(None, terminal_id="test_wm_advance")
            assert len(events1) == 2

            # Advance watermark past first event but not second
            watermark = {
                "last_event_id": events1[0]["event_id"],  # past evt_001
                "last_occurred_at": events1[0]["occurred_at"],
                "terminal_id": "test_wm_advance",
            }

            # Second ingest with watermark at first event — should skip first, catch second
            events2 = provider.ingest_since(watermark, terminal_id="test_wm_advance")
            # The tie-breaking should return evt_002 since occurred_at is same but event_num is higher
            assert len(events2) == 1
            assert events2[0]["event_id"] == "evt_002"
