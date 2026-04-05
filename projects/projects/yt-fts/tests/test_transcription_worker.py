"""
Tests for transcription worker task queue with checkout/check-in pattern.

Tests follow RED → GREEN → REFACTOR TDD workflow.
"""

import pytest
import sqlite3
from pathlib import Path

from yt_fts.core.database import get_db_connection
from yt_fts.workers.transcription_worker import (
    checkout_video,
    checkin_video_done,
    checkin_video_failed,
    get_pending_count,
)


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Create a fresh test database withVideos table."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE Videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            video_title TEXT,
            status TEXT DEFAULT 'pending',
            processing_started_at TEXT,
            worker_id TEXT,
            error_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

    # Mock get_db_path to return test database
    from yt_fts.workers import transcription_worker
    monkeypatch.setattr(transcription_worker, "get_db_path", lambda: str(db_path))

    yield str(db_path)

    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def populated_db(clean_db):
    """Database with test videos."""
    conn = sqlite3.connect(clean_db)
    # Add test videos
    videos = [
        ("vid1", "UC123", "Video 1", "pending", None, None, 0),
        ("vid2", "UC123", "Video 2", "pending", None, None, 0),
        ("vid3", "UC123", "[No Subtitles]", "pending", None, None, 0),
        ("vid4", "UC123", "[No Subtitles]", "done", None, None, 0),  # Already done
        ("vid5", "UC456", "[No Subtitles]", "pending", None, None, 0),  # Different channel
    ]
    conn.executemany(
        "INSERT INTO Videos (video_id, channel_id, video_title, status, processing_started_at, worker_id, error_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        videos
    )
    conn.commit()
    conn.close()
    return clean_db


class TestCheckoutVideo:
    """Tests for checkout_video() - atomic task reservation."""

    def test_checkout_pending_video(self, populated_db):
        """Should mark a pending video as processing and return it."""
        result = checkout_video("UC123", worker_id="worker-1")

        assert result is not None
        assert result["video_id"] in ["vid1", "vid2", "vid3"]
        assert result["status"] == "processing"
        assert result["worker_id"] == "worker-1"
        assert result["processing_started_at"] is not None

    def test_checkout_returns_video_in_order(self, populated_db):
        """Should return videos in order (lowest video_id first)."""
        result = checkout_video("UC123", worker_id="worker-1")

        # Should get vid1 (alphabetically first)
        assert result["video_id"] == "vid1"

    def test_checkout_only_pending_videos(self, populated_db):
        """Should not return videos that are already done."""
        result = checkout_video("UC123", worker_id="worker-1")

        assert result["video_id"] != "vid4"  # vid4 is already done

    def test_checkout_only_for_specified_channel(self, populated_db):
        """Should only return videos for the specified channel."""
        result = checkout_video("UC123", worker_id="worker-1")

        assert result["channel_id"] == "UC123"
        assert result["video_id"] != "vid5"  # vid5 is UC456

    def test_checkout_idempotent_for_same_video(self, populated_db):
        """Once checked out, another worker can't checkout the same video."""
        result1 = checkout_video("UC123", worker_id="worker-1")
        result2 = checkout_video("UC123", worker_id="worker-2")

        # Each worker gets a different video
        assert result1["video_id"] == "vid1"
        assert result2["video_id"] == "vid2"
        assert result1["worker_id"] == "worker-1"
        assert result2["worker_id"] == "worker-2"

    def test_checkout_returns_none_when_no_pending_videos(self, clean_db):
        """Should return None when no videos are pending."""
        # Empty database
        result = checkout_video("UC123", worker_id="worker-1")

        assert result is None

    def test_checkout_returns_none_when_all_videos_done(self, clean_db):
        """Should return None when all videos are already processed."""
        conn = sqlite3.connect(clean_db)
        conn.execute("INSERT INTO Videos (video_id, channel_id, video_title, status) VALUES ('vid1', 'UC123', 'V1', 'done')")
        conn.commit()
        conn.close()

        result = checkout_video("UC123", worker_id="worker-1")

        assert result is None

    def test_checkout_atomic_no_race_condition(self, populated_db):
        """Checkout should be atomic - two workers can't get same video."""
        import threading
        results = []

        def try_checkout(worker_id):
            result = checkout_video("UC123", worker_id=worker_id)
            if result:
                results.append(result["video_id"])

        threads = [
            threading.Thread(target=try_checkout, args=("w1",)),
            threading.Thread(target=try_checkout, args=("w2",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each video should be checked out at most once
        assert len(results) == len(set(results))
        assert len(results) <= 3  # At most 3 pending videos


class TestCheckinVideoDone:
    """Tests for checkin_video_done() - mark processing complete."""

    def test_checkin_done_marks_video_done(self, populated_db):
        """Should mark video as done after successful processing."""
        # First checkout
        video = checkout_video("UC123", worker_id="worker-1")

        # Then checkin as done
        checkin_video_done(video["video_id"])

        # Verify status
        conn = sqlite3.connect(populated_db)
        cursor = conn.execute("SELECT status FROM Videos WHERE video_id = ?", (video["video_id"],))
        status = cursor.fetchone()[0]
        conn.close()

        assert status == "done"

    def test_checkin_done_clears_worker_fields(self, populated_db):
        """Should clear worker_id and processing_started_at."""
        video = checkout_video("UC123", worker_id="worker-1")

        checkin_video_done(video["video_id"])

        conn = sqlite3.connect(populated_db)
        cursor = conn.execute("SELECT worker_id, processing_started_at FROM Videos WHERE video_id = ?", (video["video_id"],))
        worker_id, started_at = cursor.fetchone()
        conn.close()

        assert worker_id is None
        assert started_at is None


class TestCheckinVideoFailed:
    """Tests for checkin_video_failed() - return video to queue."""

    def test_checkin_failed_returns_to_pending(self, populated_db):
        """Should mark video as pending again after failure."""
        video = checkout_video("UC123", worker_id="worker-1")

        checkin_video_failed(video["video_id"], "Network error")

        conn = sqlite3.connect(populated_db)
        cursor = conn.execute("SELECT status, error_count FROM Videos WHERE video_id = ?", (video["video_id"],))
        status, error_count = cursor.fetchone()
        conn.close()

        assert status == "pending"
        assert error_count == 1

    def test_checkin_failed_increments_error_count(self, populated_db):
        """Should increment error_count on each failure."""
        video = checkout_video("UC123", worker_id="worker-1")

        checkin_video_failed(video["video_id"], "Error 1")
        checkin_video_failed(video["video_id"], "Error 2")

        conn = sqlite3.connect(populated_db)
        cursor = conn.execute("SELECT error_count FROM Videos WHERE video_id = ?", (video["video_id"],))
        error_count = cursor.fetchone()[0]
        conn.close()

        assert error_count == 2


class TestGetPendingCount:
    """Tests for get_pending_count() - queue monitoring."""

    def test_pending_count_excludes_processing_and_done(self, populated_db):
        """Should only count pending videos."""
        # Mark one as processing
        checkout_video("UC123", worker_id="worker-1")

        count = get_pending_count("UC123")

        # 3 pending for UC123, minus 1 checked out = 2
        assert count == 2

    def test_pending_count_only_for_channel(self, populated_db):
        """Should only count videos for specified channel."""
        count = get_pending_count("UC123")
        assert count == 3  # vid1, vid2, vid3

        count = get_pending_count("UC456")
        assert count == 1  # only vid5


class TestIntegration:
    """Integration tests for full checkout/process/checkin cycle."""

    def test_full_worker_cycle(self, populated_db):
        """Simulate full worker: checkout → process → checkin done."""
        # Checkout
        video = checkout_video("UC123", worker_id="worker-1")
        assert video is not None

        # Simulate processing (would call Whisper here)
        # ...

        # Checkin done
        checkin_video_done(video["video_id"])

        # Verify video is done
        conn = sqlite3.connect(populated_db)
        cursor = conn.execute("SELECT status FROM Videos WHERE video_id = ?", (video["video_id"],))
        status = cursor.fetchone()[0]
        conn.close()

        assert status == "done"

    def test_worker_failure_cycle(self, populated_db):
        """Simulate worker failure and recovery.

        Note: checkout_video prioritizes fresh videos (error_count=0) over
        retries, so after vid1 fails, vid2 is checked out next. This is
        intentional - give other videos a chance before retrying failures.
        """
        # Checkout first video
        video = checkout_video("UC123", worker_id="worker-1")
        assert video is not None
        assert video["status"] == "processing"

        # Processing fails - video returned to pending with error_count=1
        checkin_video_failed(video["video_id"], "Whisper crashed")

        # Verify failed video is back in pending pool (use sqlite3 directly)
        import sqlite3
        conn = sqlite3.connect(populated_db)
        cursor = conn.execute(
            "SELECT status, error_count FROM Videos WHERE video_id = ?",
            (video["video_id"],)
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Video should still exist in database"
        status, error_count = result
        assert status == "pending", f"Expected pending, got {status}"
        assert error_count == 1, f"Expected error_count=1, got {error_count}"

        # Next checkout should prioritize fresh videos (vid2, vid3) over retry
        video2 = checkout_video("UC123", worker_id="worker-2")
        assert video2 is not None
        # vid2/vid3 have error_count=0, so they come before the failed vid1
        assert video2["video_id"] in ["vid2", "vid3"]
        assert video2["status"] == "processing"
