"""Tests for transcription_worker.py SQL injection protection."""

import os
import tempfile
import sqlite3
import pytest
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
            video_title TEXT NOT NULL
        )
    """)
    
    # Insert test data
    cursor.execute("""
        INSERT INTO Videos (video_id, channel_id, video_title)
        VALUES 
            ('vid1', 'test_channel', '[No Subtitles]'),
            ('vid2', 'test_channel', '[No Subtitles]'),
            ('vid3', 'test_channel', 'Normal Video'),
            ('vid4', 'other_channel', '[No Subtitles]')
    """)
    
    conn.commit()
    conn.close()
    
    yield temp_db_path


class TestGetVideosNeedingTranscription:
    """Test SQL injection protection in LIMIT clause."""

    def test_valid_limit_none(self, test_db):
        """Test that None limit works (no LIMIT clause)."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        result = get_videos_needing_transcription("test_channel", limit=None)
        assert isinstance(result, list)
        # Should return 2 [No Subtitles] videos for test_channel
        assert len(result) == 2

    def test_valid_limit_int(self, test_db):
        """Test that valid integer limit works."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        result = get_videos_needing_transcription("test_channel", limit=1)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_sql_injection_string(self, test_db):
        """Test that SQL injection via string is rejected."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        with pytest.raises(TypeError, match="limit must be int or None"):
            get_videos_needing_transcription("test_channel", limit="1; DROP TABLE Videos; --")

    def test_sql_injection_union(self, test_db):
        """Test that UNION injection is rejected."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        with pytest.raises(TypeError, match="limit must be int or None"):
            get_videos_needing_transcription("test_channel", limit="1 UNION SELECT * FROM Users--")

    def test_string_number_rejected(self, test_db):
        """Test that string numbers are rejected (no type coercion)."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        with pytest.raises(TypeError, match="limit must be int or None"):
            get_videos_needing_transcription("test_channel", limit="10")

    def test_negative_limit_rejected(self, test_db):
        """Test that negative limits are rejected."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        with pytest.raises(ValueError, match="limit must be positive"):
            get_videos_needing_transcription("test_channel", limit=-1)

    def test_zero_limit_works(self, test_db):
        """Test that zero limit works (returns empty list)."""
        from yt_fts.workers.transcription_worker import get_videos_needing_transcription
        
        result = get_videos_needing_transcription("test_channel", limit=0)
        assert result == []
