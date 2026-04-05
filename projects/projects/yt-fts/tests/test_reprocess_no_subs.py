"""
Tests for re-processing existing [No Subtitles] videos.

RED PHASE - These tests will FAIL initially because:
1. Current code doesn't re-process existing [No Subtitles] videos
2. After implementation, these tests will pass (GREEN)

Context: Videos marked [No Subtitles] in the database should be
automatically queued for Whisper transcription when their channel is re-scanned.
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest


class TestReprocessNoSubsVideos:
    """Test suite for re-processing existing videos without subtitles."""

    def test_identify_no_subs_videos_for_channel(self):
        """
        Test that we can query for [No Subtitles] videos for a specific channel.

        Given: A channel with videos marked [No Subtitles]
        When: We query for videos needing transcription
        Then: Should return the correct video IDs

        THIS TEST WILL FAIL until implementation is complete.
        """
        # Arrange
        from yt_fts.core.database import get_db_path

        db = sqlite3.connect(get_db_path())
        c = db.cursor()

        # Clean up any existing test data first
        c.execute("DELETE FROM Videos WHERE video_id LIKE 'test_vid%'")
        c.execute("DELETE FROM Channels WHERE channel_id = 'UC_TEST_CHANNEL'")
        db.commit()

        # Create test data
        c.execute("INSERT INTO Channels (channel_id, channel_url, channel_name) VALUES (?, ?, ?)",
                  ("UC_TEST_CHANNEL", "https://www.youtube.com/@test/videos", "Test Channel"))
        c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                  ("test_vid_1", "[No Subtitles]", "https://youtu.be/test_vid_1", "UC_TEST_CHANNEL"))
        c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                  ("test_vid_2", "Normal Video", "https://youtu.be/test_vid_2", "UC_TEST_CHANNEL"))
        c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                  ("test_vid_3", "[No Subtitles]", "https://youtu.be/test_vid_3", "UC_TEST_CHANNEL"))
        db.commit()

        # This function should exist after implementation
        from yt_fts.download.reprocess_no_subs import get_no_subs_videos_for_channel

        # Act
        no_subs_videos = get_no_subs_videos_for_channel("UC_TEST_CHANNEL")

        # Assert - Should return only [No Subtitles] videos
        assert len(no_subs_videos) == 2
        assert "test_vid_1" in no_subs_videos
        assert "test_vid_3" in no_subs_videos
        assert "test_vid_2" not in no_subs_videos

        # Cleanup
        c.execute("DELETE FROM Videos WHERE video_id LIKE 'test_vid%'")
        c.execute("DELETE FROM Channels WHERE channel_id = 'UC_TEST_CHANNEL'")
        db.commit()
        db.close()

    def test_exclude_transcribed_videos(self):
        """
        Test that videos marked [Transcribed] are not re-processed.

        Given: A video marked [Transcribed]
        When: We query for videos needing transcription
        Then: Should NOT be included in results

        THIS TEST WILL FAIL until implementation is complete.
        """
        # Arrange
        from yt_fts.core.database import get_db_path

        db = sqlite3.connect(get_db_path())
        c = db.cursor()

        # Clean up any existing test data first
        c.execute("DELETE FROM Videos WHERE video_id LIKE 'test_vid%'")
        c.execute("DELETE FROM Channels WHERE channel_id LIKE 'UC_TEST%'")
        db.commit()

        c.execute("INSERT INTO Channels (channel_id, channel_url, channel_name) VALUES (?, ?, ?)",
                  ("UC_TEST_CHANNEL2", "https://www.youtube.com/@test2/videos", "Test Channel 2"))
        c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                  ("test_vid_4", "[Transcribed]", "https://youtu.be/test_vid_4", "UC_TEST_CHANNEL2"))
        c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                  ("test_vid_5", "[No Subtitles]", "https://youtu.be/test_vid_5", "UC_TEST_CHANNEL2"))
        db.commit()

        from yt_fts.download.reprocess_no_subs import get_no_subs_videos_for_channel

        # Act
        no_subs_videos = get_no_subs_videos_for_channel("UC_TEST_CHANNEL2")

        # Assert - Should only return [No Subtitles], not [Transcribed]
        assert len(no_subs_videos) == 1
        assert "test_vid_5" in no_subs_videos
        assert "test_vid_4" not in no_subs_videos

        # Cleanup
        c.execute("DELETE FROM Videos WHERE video_id LIKE 'test_vid%'")
        c.execute("DELETE FROM Channels WHERE channel_id LIKE 'UC_TEST%'")
        db.commit()
        db.close()

    def test_limit_no_subs_for_transcription(self):
        """
        Test that we can limit the number of videos to re-process.

        Given: A channel with 10 [No Subtitles] videos
        When: We request re-processing with limit=3
        Then: Should return only 3 video IDs

        THIS TEST WILL FAIL until implementation is complete.
        """
        # Arrange
        from yt_fts.core.database import get_db_path

        db = sqlite3.connect(get_db_path())
        c = db.cursor()

        # Clean up any existing test data first
        c.execute("DELETE FROM Videos WHERE video_id LIKE 'limit_vid%'")
        c.execute("DELETE FROM Channels WHERE channel_id = 'UC_TEST_LIMIT'")
        db.commit()

        c.execute("INSERT INTO Channels (channel_id, channel_url, channel_name) VALUES (?, ?, ?)",
                  ("UC_TEST_LIMIT", "https://www.youtube.com/@testlimit/videos", "Test Limit Channel"))

        # Add 10 [No Subtitles] videos
        for i in range(10):
            c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                     (f"limit_vid_{i}", "[No Subtitles]", f"https://youtu.be/limit_vid_{i}", "UC_TEST_LIMIT"))
        db.commit()

        from yt_fts.download.reprocess_no_subs import get_no_subs_videos_for_channel

        # Act - Limit to 3
        no_subs_videos = get_no_subs_videos_for_channel("UC_TEST_LIMIT", limit=3)

        # Assert - Should return only 3
        assert len(no_subs_videos) == 3

        # Cleanup
        c.execute("DELETE FROM Videos WHERE video_id LIKE 'limit_vid%'")
        c.execute("DELETE FROM Channels WHERE channel_id = 'UC_TEST_LIMIT'")
        db.commit()
        db.close()


class TestTranscriptionQueueFromNoSubs:
    """Test suite for adding [No Subtitles] videos to transcription queue."""

    def test_add_no_subs_to_transcription_queue(self):
        """
        Test that [No Subtitles] videos are added to transcription queue.

        Given: A list of video IDs marked [No Subtitles]
        When: We add them to the transcription queue
        Then: They should be queued for Whisper transcription

        THIS TEST WILL FAIL until implementation is complete.
        """
        # Arrange
        from yt_fts.download.reprocess_no_subs import queue_videos_for_transcription

        video_ids = ["vid1", "vid2", "vid3"]

        # Act - Pass a mock transcription function
        mock_transcribe = MagicMock()
        queue_videos_for_transcription(video_ids, "UC_TEST", transcribe_fn=mock_transcribe)

        # Assert - Each video should be transcribed
        assert mock_transcribe.call_count == 3

    def test_delete_old_no_subs_entry_after_queuing(self):
        """
        Test that old [No Subtitles] entries are deleted after queuing.

        Given: A video marked [No Subtitles] that's being re-processed
        When: It's added to the transcription queue
        Then: The old [No Subtitles] database entry should be deleted

        THIS TEST WILL FAIL until implementation is complete.
        """
        # Arrange
        from yt_fts.core.database import get_db_path

        db = sqlite3.connect(get_db_path())
        c = db.cursor()

        # Clean up any existing test data first
        c.execute("DELETE FROM Videos WHERE video_id = ?", ("test_del_vid",))
        c.execute("DELETE FROM Channels WHERE channel_id = ?", ("UC_TEST_DELETE",))
        db.commit()

        c.execute("INSERT INTO Channels (channel_id, channel_url, channel_name) VALUES (?, ?, ?)",
                  ("UC_TEST_DELETE", "https://www.youtube.com/@testdel/videos", "Test Delete Channel"))
        c.execute("INSERT INTO Videos (video_id, video_title, video_url, channel_id) VALUES (?, ?, ?, ?)",
                  ("test_del_vid", "[No Subtitles]", "https://youtu.be/test_del_vid", "UC_TEST_DELETE"))
        db.commit()

        from yt_fts.download.reprocess_no_subs import queue_videos_for_transcription

        # Act - Queue for transcription (which should delete old entry)
        mock_transcribe = MagicMock()
        queue_videos_for_transcription(["test_del_vid"], "UC_TEST_DELETE", transcribe_fn=mock_transcribe)

        # Assert - Old entry should be deleted
        c.execute("SELECT video_title FROM Videos WHERE video_id = ?", ("test_del_vid",))
        result = c.fetchone()

        # Either deleted entirely, or title changed (depends on implementation)
        assert result is None or result[0] != "[No Subtitles]"

        # Cleanup
        c.execute("DELETE FROM Videos WHERE video_id = 'test_del_vid'")
        c.execute("DELETE FROM Channels WHERE channel_id = 'UC_TEST_DELETE'")
        db.commit()
        db.close()


class TestIntegrationWithBatchDownload:
    """Integration tests for re-processing during batch download."""

    def test_module_exists(self):
        """
        Test that the reprocess_no_subs module exists.

        THIS TEST WILL FAIL until module is created.
        """
        from yt_fts.download import reprocess_no_subs
        assert reprocess_no_subs is not None

    def test_get_no_subs_videos_function_exists(self):
        """
        Test that get_no_subs_videos_for_channel function exists.

        THIS TEST WILL FAIL until function is implemented.
        """
        from yt_fts.download.reprocess_no_subs import get_no_subs_videos_for_channel
        assert callable(get_no_subs_videos_for_channel)

    def test_queue_videos_for_transcription_exists(self):
        """
        Test that queue_videos_for_transcription function exists.

        THIS TEST WILL FAIL until function is implemented.
        """
        from yt_fts.download.reprocess_no_subs import queue_videos_for_transcription
        assert callable(queue_videos_for_transcription)
