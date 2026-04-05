"""
Tests for database helper functions in videos module.

Tests that:
1. get_channel_info_from_video_id returns correct channel data
2. get_channel_info_from_video_id handles missing videos gracefully
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestGetChannelInfoFromVideoId:
    """
    Test get_channel_info_from_video_id function.

    Given: A database with channels and videos
    When: Querying channel info by video_id
    Then: Should return correct channel name and URL
    """

    def test_returns_channel_name_and_url(self):
        """
        Test that function returns both channel name and URL.

        Given: A video associated with a channel
        When: Calling get_channel_info_from_video_id
        Then: Should return (channel_name, channel_url) tuple
        """
        from yt_fts.core.database import (
            add_channel_info,
            get_channel_info_from_video_id,
        )

        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            # Add a channel
            channel_id = "UC_test123"
            channel_name = "Test Channel"
            channel_url = "https://www.youtube.com/@testchannel"

            add_channel_info(
                channel_id=channel_id,
                channel_name=channel_name,
                channel_url=channel_url,
            )

            # Add a video for this channel (direct insert to avoid schema mismatch in make_db)
            from yt_fts.db.infra import get_db_connection
            video_id = "vid_test123"
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO Videos (video_id, video_title, video_url, channel_id, video_date) VALUES (?, ?, ?, ?, ?)",
                    (video_id, "Test Video", "https://youtu.be/vid_test123", channel_id, "2024-01-01"),
                )
                conn.commit()

            # Query channel info by video_id
            result_name, result_url = get_channel_info_from_video_id(video_id)

            assert result_name == channel_name
            assert result_url == channel_url
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_returns_none_for_nonexistent_video(self):
        """
        Test that function returns (None, None) for non-existent video.

        Given: A database without the requested video_id
        When: Calling get_channel_info_from_video_id
        Then: Should return (None, None)
        """
        from yt_fts.core.database import get_channel_info_from_video_id

        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            # Query with non-existent video_id
            result_name, result_url = get_channel_info_from_video_id("nonexistent_vid")

            assert result_name is None
            assert result_url is None
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_returns_none_for_video_without_channel(self):
        """
        Test that function handles orphaned videos (no channel).

        Given: A video with channel_id that doesn't exist in Channels
        When: Calling get_channel_info_from_video_id
        Then: Should return (None, None)
        """
        from yt_fts.db.infra import get_db_connection
        from yt_fts.core.database import get_channel_info_from_video_id

        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            # Add a video with a channel_id that doesn't exist in Channels table
            video_id = "orphan_vid"
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO Videos (video_id, video_title, video_url, channel_id, video_date) VALUES (?, ?, ?, ?, ?)",
                    (video_id, "Orphan Video", "https://youtu.be/orphan", "UC_ghost", "2024-01-01"),
                )
                conn.commit()

            # Query channel info - should return None since channel doesn't exist
            result_name, result_url = get_channel_info_from_video_id(video_id)

            assert result_name is None
            assert result_url is None
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
