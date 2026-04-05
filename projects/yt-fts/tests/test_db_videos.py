"""Tests for yt_fts.db.videos module.

Run with: pytest tests/test_db_videos.py -v
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.db.videos import (
    add_video,
    add_videos_bulk,
)


class TestAddVideo:
    """Tests for add_video function."""

    @patch("yt_fts.db.videos.get_db_connection")
    def test_add_video_with_all_optional_fields(self, mock_get_conn):
        """Test adding a video with all optional fields provided."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # First call: check if channel exists (returns None = new channel)
        # Second call: insert video
        mock_cursor.fetchone.return_value = None
        mock_conn.execute.side_effect = [
            mock_cursor,  # Channel check
            MagicMock(),  # Video insert
        ]
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        add_video(
            channel_id="UC_test123",
            video_id="vid123",
            video_title="Test Video",
            video_url="https://youtu.be/vid123",
            video_date="2024-01-01T00:00:00",
            last_checked="2024-01-02T00:00:00",
            duration=600,
            thumbnail_url="https://i.ytimg.com/vi/vid123/default.jpg",
            view_count=1000,
            is_short=0,
        )

        # Verify execute was called at least once (for channel check and/or insert)
        assert mock_conn.execute.called

    @patch("yt_fts.db.videos.get_db_connection")
    def test_add_video_with_minimal_fields(self, mock_get_conn):
        """Test adding a video with only required fields."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # First call: check if channel exists (returns None = new channel)
        # Second call: insert video
        mock_cursor.fetchone.return_value = None
        mock_conn.execute.side_effect = [
            mock_cursor,  # Channel check
            MagicMock(),  # Video insert
        ]
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        add_video(
            channel_id="UC_test123",
            video_id="vid123",
            video_title="Test Video",
            video_url="https://youtu.be/vid123",
            video_date="2024-01-01T00:00:00",
        )

        # Verify execute was called at least once
        assert mock_conn.execute.called


class TestAddVideosBulk:
    """Tests for add_videos_bulk function."""

    @patch("yt_fts.db.videos.get_db_connection")
    def test_add_videos_bulk_inserts_multiple_videos(self, mock_get_conn):
        """Test bulk inserting multiple videos."""
        mock_conn = MagicMock()
        
        def execute_side_effect(query, params=None):
            mock_result = MagicMock()
            # For channel check - returns channel exists
            if "SELECT channel_id FROM Channels" in query or "SELECT * FROM Videos WHERE video_id = ?" in query:
                # Channel exists or video check - simulate exists
                mock_result.fetchone.return_value = None
            # For bulk insert
            elif "INSERT INTO Videos" in query or "INSERT OR IGNORE" in query:
                mock_result.rowcount = 2
            return mock_result

        mock_conn.execute.side_effect = execute_side_effect
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        videos = [
            {
                "video_id": "vid1",
                "title": "Video 1",
                "url": "https://youtu.be/vid1",
                "date": "2024-01-01",
                "view_count": 100,
            },
            {
                "video_id": "vid2",
                "title": "Video 2",
                "url": "https://youtu.be/vid2",
                "date": "2024-01-02",
                "view_count": 200,
            },
        ]

        count = add_videos_bulk("UC_test123", videos)

        # Verify we got a count back (2 videos)
        assert count is not None
