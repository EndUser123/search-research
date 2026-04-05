"""Tests for database channel statistics."""

import pytest
from pathlib import Path
import tempfile
import sqlite3

from yt_fts.core.database import get_db_path, get_channel_stats


@pytest.fixture
def temp_db():
    """Create a temporary database with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Override get_db_path for this test
        import yt_fts.core.database as db_module
        original_get_db_path = db_module.get_db_path
        db_module.get_db_path = lambda: str(db_path)

        # Create test database schema
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Create tables
        cur.execute("""
            CREATE TABLE Channels (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                channel_url TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE Videos (
                video_id TEXT PRIMARY KEY,
                channel_id TEXT,
                video_title TEXT,
                thumbnail_url TEXT,
                duration INTEGER,
                view_count INTEGER,
                is_short INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE Subtitles (
                subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                start_time TEXT,
                stop_time TEXT,
                text TEXT
            )
        """)

        # Insert test data
        test_channel_id = "UCtest123"
        cur.execute("INSERT INTO Channels VALUES (?, ?, ?)",
                   (test_channel_id, "Test Channel", "https://youtube.com/@test"))

        # 10 total videos
        for i in range(10):
            cur.execute("INSERT INTO Videos VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (f"video_{i}", test_channel_id, f"Video {i}", "", 0, 0, 0))

        # 6 videos with subtitles
        for i in range(6):
            cur.execute("INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)",
                       (f"video_{i}", "0:00", "0:10", f"Subtitle text {i}"))

        # 2 unavailable videos
        cur.execute("UPDATE Videos SET video_title = '[Unavailable]' WHERE video_id = 'video_6'")
        cur.execute("UPDATE Videos SET video_title = '[Unavailable]' WHERE video_id = 'video_7'")

        # 1 scheduled video
        cur.execute("UPDATE Videos SET video_title = '[Scheduled]' WHERE video_id = 'video_8'")

        # 1 members-only video
        cur.execute("UPDATE Videos SET video_title = '[Members only]' WHERE video_id = 'video_9'")

        conn.commit()
        conn.close()

        yield test_channel_id

        # Cleanup
        db_module.get_db_path = original_get_db_path


def test_get_channel_stats_includes_without_transcripts(temp_db):
    """Test that get_channel_stats returns without_transcripts field."""
    stats = get_channel_stats(temp_db)

    # Should have all expected fields
    assert "total" in stats
    assert "with_transcripts" in stats
    assert "without_transcripts" in stats, "without_transcripts field is missing!"
    assert "scheduled" in stats
    assert "members_only" in stats
    assert "unavailable" in stats
    assert "shorts" in stats

    # Verify counts match test data
    assert stats["total"] == 10, f"Expected 10 total videos, got {stats['total']}"
    assert stats["with_transcripts"] == 6, f"Expected 6 with transcripts, got {stats['with_transcripts']}"
    assert stats["without_transcripts"] == 4, f"Expected 4 without transcripts, got {stats['without_transcripts']}"
    assert stats["unavailable"] == 2, f"Expected 2 unavailable, got {stats['unavailable']}"
    assert stats["scheduled"] == 1, f"Expected 1 scheduled, got {stats['scheduled']}"
    assert stats["members_only"] == 1, f"Expected 1 members only, got {stats['members_only']}"


def test_get_channel_stats_without_transcripts_calculation(temp_db):
    """Test that without_transcripts = total - with_transcripts."""
    stats = get_channel_stats(temp_db)

    expected_without = stats["total"] - stats["with_transcripts"]
    actual_without = stats["without_transcripts"]

    assert actual_without == expected_without, \
        f"without_transcripts ({actual_without}) should equal total ({stats['total']}) - with_transcripts ({stats['with_transcripts']})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
