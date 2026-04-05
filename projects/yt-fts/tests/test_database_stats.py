"""Tests for database channel statistics."""

import pytest
from pathlib import Path
import tempfile
import sqlite3
import gc

@pytest.fixture
def temp_db():
    """Create a temporary database with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create test database schema
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Create tables
        cur.execute("""
            CREATE TABLE Channels (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                channel_url TEXT,
                subscriber_count INTEGER DEFAULT 0,
                playlist_count INTEGER DEFAULT 0
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
        cur.execute("INSERT INTO Channels VALUES (?, ?, ?, ?, ?)",
                   (test_channel_id, "Test Channel", "https://youtube.com/@test", 1000, 5))

        # 10 total videos
        for i in range(10):
            cur.execute("INSERT INTO Videos VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (f"video_{i}", test_channel_id, f"Video {i}", "", 0, 0, 0))

        # 6 videos with subtitles
        for i in range(6):
            cur.execute("INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)",
                       (f"video_{i}", "0:00", "0:10", f"Subtitle text {i}"))

        conn.commit()
        conn.close()
        
        gc.collect()

        # Yield both db_path and test_channel_id
        yield str(db_path), test_channel_id


def test_get_channel_stats_includes_without_transcripts(temp_db):
    """Test that get_channel_stats returns without_transcripts field."""
    db_path, test_channel_id = temp_db
    
    # Patch at multiple levels to ensure it works
    import yt_fts.utils.config as config_module
    import yt_fts.db.infra as infra_module
    
    original_config = config_module.get_db_path
    original_infra = infra_module.get_db_path
    
    config_module.get_db_path = lambda: str(db_path)
    infra_module.get_db_path = lambda: str(db_path)
    
    try:
        # Reimport get_channel_stats to avoid cached references
        from importlib import reload
        import yt_fts.db.channels as channels_module
        reload(channels_module)
        from yt_fts.db.channels import get_channel_stats
        
        stats = get_channel_stats(test_channel_id)
    finally:
        config_module.get_db_path = original_config
        infra_module.get_db_path = original_infra
        gc.collect()

    # Verify basic stats
    assert stats["total"] == 10, f"Expected 10 total videos, got {stats['total']}"
    assert stats["with_transcripts"] == 6, f"Expected 6 with transcripts, got {stats['with_transcripts']}"
    assert stats["without_transcripts"] == 4, f"Expected 4 without transcripts, got {stats['without_transcripts']}"


def test_get_channel_stats_without_transcripts_calculation(temp_db):
    """Test that without_transcripts = total - with_transcripts."""
    db_path, test_channel_id = temp_db
    
    import yt_fts.utils.config as config_module
    import yt_fts.db.infra as infra_module
    
    original_config = config_module.get_db_path
    original_infra = infra_module.get_db_path
    
    config_module.get_db_path = lambda: str(db_path)
    infra_module.get_db_path = lambda: str(db_path)
    
    try:
        from importlib import reload
        import yt_fts.db.channels as channels_module
        reload(channels_module)
        from yt_fts.db.channels import get_channel_stats
        
        stats = get_channel_stats(test_channel_id)
    finally:
        config_module.get_db_path = original_config
        infra_module.get_db_path = original_infra
        gc.collect()

    expected_without = stats["total"] - stats["with_transcripts"]
    actual_without = stats["without_transcripts"]

    assert actual_without == expected_without


def test_channel_stats_counts_unique_videos_not_join_rows(temp_db):
    """
    Regression test for SQL COUNT bug.

    Bug: COUNT(v.video_id) with LEFT JOIN to Subtitles counted JOIN rows
    instead of unique videos.

    Example: 2 videos with 4 subtitles each:
    - Wrong: COUNT(v.video_id) returns 8 (2 × 4)
    - Correct: COUNT(DISTINCT v.video_id) returns 2

    This test would have caught the bug in get_channel_stats_with_subs_and_playlists.
    """
    db_path, test_channel_id = temp_db

    # Add more subtitles to expose the bug
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Add additional subtitles to existing videos to create 1:many relationship
    # video_0 gets 4 more subtitles (total 5)
    # video_1 gets 3 more subtitles (total 4)
    for i in range(4):
        cur.execute("INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)",
                   ("video_0", f"0:{i*10}", f"0:{i*10+10}", f"More subtitle {i}"))

    for i in range(3):
        cur.execute("INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)",
                   ("video_1", f"0:{i*10}", f"0:{i*10+10}", f"More subtitle {i}"))

    conn.commit()
    conn.close()

    # Patch database path
    import yt_fts.utils.config as config_module
    import yt_fts.db.infra as infra_module

    original_config = config_module.get_db_path
    original_infra = infra_module.get_db_path

    config_module.get_db_path = lambda: str(db_path)
    infra_module.get_db_path = lambda: str(db_path)

    try:
        from importlib import reload
        import yt_fts.db.channels as channels_module
        reload(channels_module)
        from yt_fts.db.channels import get_channel_stats_with_subs_and_playlists

        stats = get_channel_stats_with_subs_and_playlists(test_channel_id)
    finally:
        config_module.get_db_path = original_config
        infra_module.get_db_path = original_infra
        gc.collect()

    # Verify: 10 unique videos, NOT (10 videos × subtitle rows)
    # video_0: 1 + 4 = 5 subtitles
    # video_1: 1 + 3 = 4 subtitles
    # video_2-5: 1 subtitle each = 4 subtitles
    # Total: 5 + 4 + 4 = 13 subtitle rows
    # But only 10 unique videos!
    assert stats["total"] == 10, (
        f"Expected 10 unique videos, got {stats['total']}. "
        f"This indicates COUNT(v.video_id) bug: counting JOIN rows instead of DISTINCT videos."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
