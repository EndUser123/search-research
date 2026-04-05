"""Tests for telemetry query helper functions."""

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil

import pytest

from yt_fts.debug.telemetry_query import (
    query_recent_events,
    query_by_level,
    query_by_component,
    get_error_summary,
    get_recent_errors,
    get_telemetry_stats,
)
from yt_fts.debug.telemetry import _get_db_path


@pytest.fixture
def temp_telemetry_db():
    """Create a temporary telemetry database with sample data."""
    # Save original db path
    original_db = _get_db_path()
    
    # Create temp directory and db
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test_telemetry.db"
    
    # Patch the db path function to return temp db
    import yt_fts.debug.telemetry_query as tq_module
    original_get_db = tq_module._get_db_path
    tq_module._get_db_path = lambda: temp_db
    
    # Create sample data
    conn = sqlite3.connect(temp_db)
    conn.execute("""
        CREATE TABLE debug_events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT,
            session_id TEXT,
            level TEXT,
            component TEXT,
            event_type TEXT,
            data TEXT,
            traceback TEXT
        )
    """)
    
    now = datetime.now(timezone.utc)
    sample_events = [
        ("id1", (now - timedelta(minutes=5)).isoformat(), "sess1", "ERROR", "download_handler", "download_failed", '{"error": "timeout"}', None),
        ("id2", (now - timedelta(minutes=4)).isoformat(), "sess1", "WARNING", "download_handler", "retry_attempt", '{"attempt": 2}', None),
        ("id3", (now - timedelta(minutes=3)).isoformat(), "sess1", "INFO", "download_handler", "function_entry", '{"function": "get_playlist"}', None),
        ("id4", (now - timedelta(minutes=2)).isoformat(), "sess1", "ERROR", "api_client", "rate_limit", '{"quota": 100}', None),
        ("id5", (now - timedelta(minutes=1)).isoformat(), "sess1", "DEBUG", "database", "query_executed", '{"sql": "SELECT *"}', None),
    ]
    
    for event in sample_events:
        conn.execute("INSERT INTO debug_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)", event)
    conn.commit()
    conn.close()
    
    yield temp_db
    
    # Cleanup
    shutil.rmtree(temp_dir)
    tq_module._get_db_path = original_get_db


class TestQueryRecentEvents:
    def test_returns_events_ordered_by_timestamp(self, temp_telemetry_db):
        events = query_recent_events(limit=3)
        assert len(events) == 3
        # Most recent first
        assert events[0]["event_type"] == "query_executed"
        assert events[1]["event_type"] == "rate_limit"
        assert events[2]["event_type"] == "function_entry"


class TestQueryByLevel:
    def test_filters_by_error_level(self, temp_telemetry_db):
        events = query_by_level("ERROR", limit=10)
        assert len(events) == 2
        assert all(e["level"] == "ERROR" for e in events)
    
    def test_filters_by_warning_level(self, temp_telemetry_db):
        events = query_by_level("WARNING", limit=10)
        assert len(events) == 1
        assert events[0]["level"] == "WARNING"


class TestQueryByComponent:
    def test_filters_by_component(self, temp_telemetry_db):
        events = query_by_component("download_handler", limit=10)
        assert len(events) == 3
        assert all(e["component"] == "download_handler" for e in events)


class TestGetErrorSummary:
    def test_counts_errors_by_component(self, temp_telemetry_db):
        summary = get_error_summary()
        assert len(summary) == 2
        # download_handler has 1 error, api_client has 1 error
        components = {s["component"]: s["count"] for s in summary}
        assert components.get("download_handler") == 1
        assert components.get("api_client") == 1


class TestGetRecentErrors:
    def test_returns_only_errors(self, temp_telemetry_db):
        errors = get_recent_errors(limit=5)
        assert len(errors) == 2
        assert all(e["level"] == "ERROR" for e in errors)
        assert errors[0]["timestamp"] > errors[1]["timestamp"]  # newest first


class TestGetTelemetryStats:
    def test_returns_overall_statistics(self, temp_telemetry_db):
        stats = get_telemetry_stats()
        assert stats["total_events"] == 5
        assert stats["by_level"]["ERROR"] == 2
        assert stats["by_level"]["WARNING"] == 1
        assert stats["by_level"]["INFO"] == 1
        assert stats["by_level"]["DEBUG"] == 1


class TestNonExistentDatabase:
    def test_returns_empty_list_when_db_missing(self):
        import yt_fts.debug.telemetry_query as tq_module
        original_get_db = tq_module._get_db_path
        tq_module._get_db_path = lambda: Path("/nonexistent/telemetry.db")
        
        try:
            result = query_recent_events()
            assert result == []
        finally:
            tq_module._get_db_path = original_get_db
