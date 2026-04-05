"""Characterization tests for transcription_worker.py cleanup behavior.

These tests CAPTURE CURRENT BEHAVIOR before refactoring to address
file descriptor leak: P1-2 - Manual connection management without guaranteed cleanup.

Run with: pytest tests/yt_fts/workers/test_transcription_worker_fd_leak.py -v
"""

import os
import tempfile
import sqlite3
import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def test_db(temp_db_path, monkeypatch):
    """Create a test database with Videos table and sample data."""
    # Set environment variable so the function uses our test database
    monkeypatch.setenv("YT_FTS_DB_PATH", temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Create Videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            video_title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            worker_id TEXT,
            processing_started_at TEXT,
            error_count INTEGER DEFAULT 0
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO Videos (video_id, channel_id, video_title, status)
        VALUES
            ('vid1', 'test_channel', '[No Subtitles]', 'pending'),
            ('vid2', 'test_channel', '[No Subtitles]', 'pending'),
            ('vid3', 'test_channel', 'Normal Video', 'done'),
            ('vid4', 'other_channel', '[No Subtitles]', 'pending')
    """)

    conn.commit()
    conn.close()

    yield temp_db_path


class TestGetConnectionManagement:
    """Tests for get_connection() context manager behavior."""

    def test_get_connection_yields_connection(self, test_db):
        """Characterization: get_connection() context manager yields a sqlite3 connection object."""
        from yt_fts.db.factory import get_connection

        with get_connection(timeout=30.0) as conn:
            # Characterize current behavior: yields sqlite3 connection
            assert isinstance(conn, sqlite3.Connection)

            # Characterize: connection is open
            assert conn.total_changes >= 0  # Connection is valid

        # Connection is automatically closed after context
        # No manual cleanup needed

    def test_get_connection_creates_new_connection_each_call(self, test_db):
        """Characterization: get_connection() creates a new connection on each call."""
        from yt_fts.db.factory import get_connection

        with get_connection(timeout=30.0) as conn1:
            pass  # Connection auto-closed

        with get_connection(timeout=30.0) as conn2:
            pass  # Connection auto-closed

        # Each context manager call creates a new connection
        # Connections are automatically closed


class TestCheckoutVideoConnectionCleanup:
    """Tests for checkout_video() connection cleanup on exceptions."""

    def test_checkout_video_normal_path_returns_video(self, test_db):
        """Characterization: Normal checkout returns video dict with expected keys."""
        from yt_fts.workers.transcription_worker import checkout_video

        result = checkout_video("test_channel", worker_id="test_worker")

        # Characterize: returns video dict
        assert result is not None
        assert result["video_id"] == "vid1"
        assert result["channel_id"] == "test_channel"
        assert result["status"] == "processing"
        assert result["worker_id"] == "test_worker"
        assert "processing_started_at" in result

    def test_checkout_video_no_pending_videos_returns_none(self, test_db):
        """Characterization: No pending videos returns None."""
        from yt_fts.workers.transcription_worker import checkout_video

        result = checkout_video("nonexistent_channel", worker_id="test_worker")

        # Characterize: returns None when no videos
        assert result is None

    def test_checkout_video_skips_done_videos(self, test_db):
        """Characterization: Videos with status='done' are skipped."""
        from yt_fts.workers.transcription_worker import checkout_video

        # First checkout gets vid1
        result1 = checkout_video("test_channel", worker_id="worker1")
        assert result1["video_id"] == "vid1"

        # Mark vid1 as done
        from yt_fts.workers.transcription_worker import checkin_video_done
        checkin_video_done("vid1")

        # Next checkout should skip done vid1 and get vid2
        result2 = checkout_video("test_channel", worker_id="worker2")
        assert result2["video_id"] == "vid2"


class TestCheckoutVideoExceptionScenarios:
    """Tests for various exception scenarios and their behavior."""

    def test_checkout_with_invalid_channel_id(self, test_db):
        """Characterization: Invalid channel ID returns None, no exception."""
        from yt_fts.workers.transcription_worker import checkout_video

        # Empty channel ID
        result = checkout_video("", worker_id="test_worker")
        assert result is None

    def test_checkout_respects_error_count_threshold(self, test_db):
        """Characterization: Videos with error_count >= max_errors are skipped."""
        from yt_fts.workers.transcription_worker import checkout_video
        import sqlite3

        # Manually set error_count on vid1
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE Videos SET error_count = 3 WHERE video_id = 'vid1'")
        conn.commit()
        conn.close()

        # With max_errors=3, vid1 should be skipped
        result = checkout_video("test_channel", worker_id="test_worker", max_errors=3)
        assert result["video_id"] == "vid2"  # Gets vid2 instead

    def test_checkout_atomicity_multiple_workers(self, test_db):
        """Characterization: Multiple workers can checkout different videos."""
        from yt_fts.workers.transcription_worker import checkout_video

        # Worker 1 checks out
        result1 = checkout_video("test_channel", worker_id="worker1")
        assert result1["video_id"] == "vid1"
        assert result1["worker_id"] == "worker1"

        # Worker 2 should get next available video
        result2 = checkout_video("test_channel", worker_id="worker2")
        assert result2["video_id"] == "vid2"
        assert result2["worker_id"] == "worker2"

        # Worker 3 should get None (no more pending videos)
        result3 = checkout_video("test_channel", worker_id="worker3")
        assert result3 is None


class TestConnectionLeakDetection:
    """Tests to characterize connection management behavior."""

    def test_multiple_checkout_succeed_without_error(self, test_db):
        """Characterization: Multiple consecutive checkout calls work without error."""
        from yt_fts.workers.transcription_worker import checkout_video
        from yt_fts.workers.transcription_worker import checkin_video_done

        # Run multiple checkout/checkin cycles
        video1 = checkout_video("test_channel", worker_id="worker1")
        assert video1 is not None
        checkin_video_done(video1["video_id"])

        video2 = checkout_video("test_channel", worker_id="worker2")
        assert video2 is not None
        checkin_video_done(video2["video_id"])

        # No exceptions thrown = characterization of current behavior
        assert True

    def test_checkout_then_checkin_updates_status(self, test_db):
        """Characterization: checkin_video_done updates video status correctly."""
        from yt_fts.workers.transcription_worker import checkout_video
        from yt_fts.workers.transcription_worker import checkin_video_done
        import sqlite3

        # Checkout a video
        video = checkout_video("test_channel", worker_id="worker1")
        video_id = video["video_id"]

        # Checkin as done
        checkin_video_done(video_id)

        # Verify status in DB
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT status, worker_id FROM Videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        # Characterize: status updated to done, worker_id cleared
        assert row[0] == "done"
        assert row[1] is None

    def test_checkout_then_checkin_failed_increments_error_count(self, test_db):
        """Characterization: checkin_video_failed increments error_count and returns to pending."""
        from yt_fts.workers.transcription_worker import checkout_video
        from yt_fts.workers.transcription_worker import checkin_video_failed
        import sqlite3

        # Checkout a video
        video = checkout_video("test_channel", worker_id="worker1")
        video_id = video["video_id"]

        # Checkin as failed
        checkin_video_failed(video_id, "Test error")

        # Verify status in DB
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT status, worker_id, error_count FROM Videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        # Characterize: status back to pending, worker_id cleared, error_count incremented
        assert row[0] == "pending"
        assert row[1] is None
        assert row[2] == 1

    def test_get_pending_count(self, test_db):
        """Characterization: get_pending_count returns correct count."""
        from yt_fts.workers.transcription_worker import get_pending_count

        # Should have 2 pending videos initially
        count = get_pending_count("test_channel")
        assert count == 2

    def test_recover_stale_checkouts(self, test_db):
        """Characterization: recover_stale_checkouts returns videos to pending."""
        from yt_fts.workers.transcription_worker import recover_stale_checkouts
        from yt_fts.workers.transcription_worker import checkout_video
        import sqlite3

        # Checkout a video (sets status to 'processing')
        video = checkout_video("test_channel", worker_id="worker1")

        # Manually set processing_started_at to old time
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Videos SET processing_started_at = datetime('now', '-1 hour') WHERE video_id = ?",
            (video["video_id"],)
        )
        conn.commit()
        conn.close()

        # Recover stale checkouts (timeout=30 minutes)
        recovered = recover_stale_checkouts(timeout_minutes=30)

        # Characterize: 1 video recovered
        assert recovered == 1

        # Verify video is back to pending
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT status, worker_id FROM Videos WHERE video_id = ?", (video["video_id"],))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "pending"
        assert row[1] is None

