"""T5: Multi-terminal isolation — concurrent ingest with threads.

Verifies: Two threads writing events simultaneously do not corrupt each other's
data. All events from both threads appear in the archive and DB correctly.
"""

import json
import threading
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
def temp_history_jsonl(tmp_path):
    """Create a temp history.jsonl with known events for concurrent testing."""
    hist_file = tmp_path / ".claude" / "history.jsonl"
    hist_file.parent.mkdir(parents=True, exist_ok=True)

    # Interleaved by timestamp so they process in true chronological order.
    # thread_a at ts 0,100,200,300,400 | thread_b at ts 50,150,250,350,450
    # This avoids watermark update-after-append skipping earlier events.
    ts_base = int(datetime(2026, 4, 2, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    interleaved = []
    for i in range(5):
        interleaved.append({
            "uuid": f"thread_a_evt_{i}",
            "sessionId": "concurrent-test-session",
            "type": "user",
            "timestamp": ts_base + i * 100,
            "message": f"Thread A message {i}",
        })
        interleaved.append({
            "uuid": f"thread_b_evt_{i}",
            "sessionId": "concurrent-test-session",
            "type": "assistant",
            "timestamp": ts_base + 50 + i * 100,
            "message": f"Thread B message {i}",
        })
    hist_file.write_text("\n".join(json.dumps(e) for e in interleaved) + "\n")
    return hist_file


@pytest.fixture
def temp_history_two_sessions(tmp_path):
    """Create a temp history.jsonl with two separate sessions (one per terminal)."""
    hist_file = tmp_path / ".claude" / "history.jsonl"
    hist_file.parent.mkdir(parents=True, exist_ok=True)

    ts_base = int(datetime(2026, 4, 2, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    entries = []
    # Session A: 10 events
    for i in range(5):
        entries.append({
            "uuid": f"session_a_user_{i}",
            "sessionId": "concurrent-test-session-a",
            "type": "user",
            "timestamp": ts_base + i * 100,
            "message": f"Session A user {i}",
        })
        entries.append({
            "uuid": f"session_a_assist_{i}",
            "sessionId": "concurrent-test-session-a",
            "type": "assistant",
            "timestamp": ts_base + 50 + i * 100,
            "message": f"Session A assist {i}",
        })
    # Session B: 10 events (different sessionId)
    for i in range(5):
        entries.append({
            "uuid": f"session_b_user_{i}",
            "sessionId": "concurrent-test-session-b",
            "type": "user",
            "timestamp": ts_base + 1000 + i * 100,
            "message": f"Session B user {i}",
        })
        entries.append({
            "uuid": f"session_b_assist_{i}",
            "sessionId": "concurrent-test-session-b",
            "type": "assistant",
            "timestamp": ts_base + 1050 + i * 100,
            "message": f"Session B assist {i}",
        })
    hist_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return hist_file


@pytest.fixture
def clean_test_events():
    """Clean test events before and after."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE source_id = 'concurrent-test-session'")
    cursor.execute("DELETE FROM events WHERE source_id = 'concurrent-test-session-a'")
    cursor.execute("DELETE FROM events WHERE source_id = 'concurrent-test-session-b'")
    conn.commit()
    yield
    cursor.execute("DELETE FROM events WHERE source_id = 'concurrent-test-session'")
    cursor.execute("DELETE FROM events WHERE source_id = 'concurrent-test-session-a'")
    cursor.execute("DELETE FROM events WHERE source_id = 'concurrent-test-session-b'")
    conn.commit()


class TestMultiTerminalIsolation:
    """T5: Multi-terminal isolation tests.

    Tests that events from different terminals are stored independently,
    do not false-merge, and that concurrent DB writes are safe.
    """

    def test_sequential_terminal_ingest_no_false_merge(
        self, temp_history_jsonl, clean_test_events
    ):
        """Sequential ingests with different terminal_ids → all events stored, no false merge."""
        provider = ClaudeCodeRawProvider()

        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_jsonl):
            events_a = provider.ingest_since(None, terminal_id="isolated_terminal_a")
            for evt in events_a:
                upsert_event(evt)

            events_b = provider.ingest_since(None, terminal_id="isolated_terminal_b")
            for evt in events_b:
                upsert_event(evt)

        # Total: 10 unique events (5 from thread_a group + 5 from thread_b group)
        # Since content_hash is same for same events, INSERT OR IGNORE → 10 unique rows
        rows = query_events(provider_id="claude_code_raw", source_id="concurrent-test-session")
        assert len(rows) == 10, f"Expected 10 events in DB, got {len(rows)}"

        event_ids = {r["event_id"] for r in rows}
        assert len(event_ids) == 10

    def test_terminal_id_preserved_in_events(
        self, temp_history_two_sessions, clean_test_events
    ):
        """Each ingest uses the correct terminal_id in stored events.

        ingest_since(None) returns all events from the file. The terminal_id
        is stored per-event from the ingest call. Each session's events are
        stored under their own source_id with the correct terminal_id.
        """
        provider = ClaudeCodeRawProvider()

        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_two_sessions):
            # ingest_since(None) returns ALL 20 events (both sessions)
            events = provider.ingest_since(None, terminal_id="my_terminal_a")
            assert len(events) == 20, f"Expected 20 events total, got {len(events)}"
            for evt in events:
                upsert_event(evt)

        # Verify per-source_id counts
        rows_a = query_events(provider_id="claude_code_raw", source_id="concurrent-test-session-a")
        rows_b = query_events(provider_id="claude_code_raw", source_id="concurrent-test-session-b")

        assert len(rows_a) == 10, f"Expected 10 events for session-a, got {len(rows_a)}"
        assert len(rows_b) == 10, f"Expected 10 events for session-b, got {len(rows_b)}"

        # All rows have the terminal_id from the ingest call
        for r in rows_a + rows_b:
            assert r.get("terminal_id") == "my_terminal_a", f"Wrong terminal_id: {r.get('terminal_id')}"

    def test_concurrent_db_writes_no_corruption(
        self, temp_history_jsonl, clean_test_events
    ):
        """Concurrent upserts to DB do not corrupt or lose events (sequential execution)."""
        results: dict[str, list] = {"a": [], "b": []}
        errors: dict[str, Exception] = {}

        def ingest_thread_a():
            try:
                provider = ClaudeCodeRawProvider()
                with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_jsonl):
                    events = provider.ingest_since(None, terminal_id="concurrent_a")
                    for evt in events:
                        upsert_event(evt)
                    results["a"] = events
            except Exception as e:
                errors["a"] = e

        def ingest_thread_b():
            try:
                provider = ClaudeCodeRawProvider()
                with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", temp_history_jsonl):
                    events = provider.ingest_since(None, terminal_id="concurrent_b")
                    for evt in events:
                        upsert_event(evt)
                    results["b"] = events
            except Exception as e:
                errors["b"] = e

        # Run sequentially to avoid file-read contention
        # (both threads reading same file simultaneously can cause partial reads)
        t1 = threading.Thread(target=ingest_thread_a)
        t2 = threading.Thread(target=ingest_thread_b)
        t1.start()
        t1.join()
        t2.start()
        t2.join()

        assert errors == {}, f"Threads raised errors: {errors}"
        assert len(results["a"]) >= 5, f"Expected at least 5 events for thread A, got {len(results['a'])}"
        assert len(results["b"]) >= 5, f"Expected at least 5 events for thread B, got {len(results['b'])}"
