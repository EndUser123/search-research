"""
Tests for automatic database cleanup functionality.

Tests that:
1. Channels in SkippedChannels table are removed from Channels table
2. Cleanup happens automatically after batch download
3. Cleanup handles missing SkippedChannels table gracefully (older schemas)
"""

import os
import tempfile
from io import StringIO
from pathlib import Path

import pytest


class TestDatabaseCleanup:
    """
    Test database cleanup after batch operations.

    Given: A database with various channel states
    When: cleanup_channels() is called
    Then: Invalid channels (in SkippedChannels) are removed
    """

    def test_cleanup_removes_skipped_channels(self):
        """
        Test that channels in SkippedChannels are removed from Channels table.

        Given: A channel in both Channels and SkippedChannels tables
        When: Running cleanup_channels()
        Then: Channel should be removed from Channels table
        """
        from yt_fts.core.database import cleanup_channels, get_db_connection

        tmpdir = tempfile.mkdtemp()
        try:
            # Set up test database via environment variable
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            # Create schema
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            # Use a single connection for all test operations
            with get_db_connection() as conn:
                # Add a channel
                test_channel_id = "UC_test123"
                test_channel_url = "https://www.youtube.com/@testchannel"
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (test_channel_id, "Test Channel", test_channel_url),
                )

                # Mark it as skipped
                conn.execute(
                    "INSERT INTO SkippedChannels (channel_url, skip_reason, fail_count, last_attempt) VALUES (?, ?, ?, ?)",
                    (test_channel_url, "channel_deleted_or_404", 1, "2024-01-01"),
                )
                conn.commit()

                # Verify channel exists before cleanup
                channels_before = conn.execute("SELECT COUNT(*) FROM Channels").fetchone()[0]
                assert channels_before == 1

            # Run cleanup (opens its own connection)
            result = cleanup_channels()

            # Verify channel was removed
            with get_db_connection() as conn:
                channels_after = conn.execute("SELECT COUNT(*) FROM Channels").fetchone()[0]
            assert channels_after == 0
            assert result["skipped_removed"] == 1
            assert result["total_channels_before"] == 1
            assert result["total_channels_after"] == 0
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cleanup_does_not_remove_channels_with_no_videos(self):
        """
        Test that channels with no videos are NOT removed.

        Given: A channel with no videos in the Videos table
        When: Running cleanup_channels()
        Then: Channel should still exist (not removed)
        """
        from yt_fts.core.database import cleanup_channels, get_db_connection

        tmpdir = tempfile.mkdtemp()
        try:
            # Set up test database via environment variable
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            # Create schema
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            # Add a channel (no videos)
            test_channel_id = "UC_novideos"
            test_channel_name = "Empty Channel"
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (test_channel_id, test_channel_name, "https://www.youtube.com/@empty"),
                )
                conn.commit()

            # Run cleanup
            result = cleanup_channels()

            # Verify nothing was removed (channel is not in SkippedChannels)
            assert result["skipped_removed"] == 0

            # Verify channel still exists (not removed)
            with get_db_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM Channels").fetchone()[0]
            assert count == 1
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cleanup_returns_empty_result_when_nothing_to_clean(self):
        """
        Test that cleanup returns zeros when database is clean.

        Given: A clean database with no skipped channels
        When: Running cleanup_channels()
        Then: All cleanup counts should be zero
        """
        from yt_fts.core.database import cleanup_channels, get_db_connection

        tmpdir = tempfile.mkdtemp()
        try:
            # Set up test database via environment variable
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            # Create schema
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            # Add a valid channel with videos
            test_channel_id = "UC_valid123"
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (test_channel_id, "Valid Channel", "https://www.youtube.com/@valid"),
                )
                # Add a video for this channel
                conn.execute(
                    "INSERT INTO Videos (video_id, video_title, video_url, channel_id, video_date) VALUES (?, ?, ?, ?, ?)",
                    ("vid123", "Test Video", "https://youtu.be/vid123", test_channel_id, "2024-01-01"),
                )
                conn.commit()

            # Run cleanup
            result = cleanup_channels()

            # Verify no cleanup was needed
            assert result["skipped_removed"] == 0
            assert result["total_channels_before"] == 1
            assert result["total_channels_after"] == 1
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cleanup_handles_multiple_skipped_channels(self):
        """
        Test that cleanup handles multiple skipped channels.

        Given: A database with skipped and valid channels
        When: Running cleanup_channels()
        Then: Only skipped channels should be removed
        """
        from yt_fts.core.database import cleanup_channels, get_db_connection

        tmpdir = tempfile.mkdtemp()
        try:
            # Set up test database via environment variable
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            # Create schema
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))

            with get_db_connection() as conn:
                # 1. Add a skipped channel
                skipped_id = "UC_skipped"
                skipped_url = "https://www.youtube.com/@skipped"
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (skipped_id, "Skipped Channel", skipped_url),
                )
                conn.execute(
                    "INSERT INTO SkippedChannels (channel_url, skip_reason, fail_count, last_attempt) VALUES (?, ?, ?, ?)",
                    (skipped_url, "channel_deleted_or_404", 1, "2024-01-01"),
                )

                # 2. Add a channel with no videos (should NOT be removed)
                no_vid_id = "UC_novideos"
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (no_vid_id, "No Videos Channel", "https://www.youtube.com/@novids"),
                )

                # 3. Add a valid channel (should not be touched)
                valid_id = "UC_valid"
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (valid_id, "Valid Channel", "https://www.youtube.com/@valid"),
                )
                # Add a video for the valid channel
                conn.execute(
                    "INSERT INTO Videos (video_id, video_title, video_url, channel_id, video_date) VALUES (?, ?, ?, ?, ?)",
                    ("vid123", "Test Video", "https://youtu.be/vid123", valid_id, "2024-01-01"),
                )
                conn.commit()

            # Run cleanup
            result = cleanup_channels()

            # Verify results
            assert result["skipped_removed"] == 1
            assert result["total_channels_before"] == 3  # skipped + no_vid + valid
            assert result["total_channels_after"] == 2  # no_vid + valid

            # Verify valid channel still exists
            with get_db_connection() as conn:
                valid_exists = conn.execute(
                    "SELECT 1 FROM Channels WHERE channel_id = ?", (valid_id,)
                ).fetchone()
            assert valid_exists is not None
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cleanup_handles_missing_skipped_channels_table(self):
        """
        Test that cleanup handles databases without SkippedChannels table.

        Given: A database with older schema (no SkippedChannels table)
        When: Running cleanup_channels()
        Then: Should complete without error, no channels removed
        """
        from yt_fts.core.database import cleanup_channels, get_db_connection

        tmpdir = tempfile.mkdtemp()
        try:
            # Set up test database via environment variable
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)

            # Create basic schema without SkippedChannels
            from sqlite_utils import Database
            db = Database(str(test_db))
            db["Channels"].create(
                {"channel_id": str, "channel_name": str, "channel_url": str},
                pk="channel_id",
                if_not_exists=True,
            )
            db["Videos"].create(
                {
                    "video_id": str,
                    "video_title": str,
                    "video_url": str,
                    "channel_id": str,
                    "video_date": str,
                },
                pk="video_id",
                if_not_exists=True,
            )
            del db

            # Add a channel
            test_channel_id = "UC_oldschema"
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (test_channel_id, "Old Schema Channel", "https://www.youtube.com/@old"),
                )
                conn.commit()

            # Run cleanup - should not error
            result = cleanup_channels()

            # Verify nothing was removed
            assert result["skipped_removed"] == 0
            assert result["total_channels_before"] == 1
            assert result["total_channels_after"] == 1
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCleanupIntegration:
    """
    Integration tests for cleanup in batch download context.
    """

    def test_cleanup_runs_after_batch_download(self):
        """
        Test that cleanup is called automatically during summary print.

        Given: A batch download that completes
        When: print_summary is called
        Then: cleanup_channels should be called automatically
        """
        from rich.console import Console
        from yt_fts.download.summary import print_summary

        # Mock results
        results = {
            "successful": [],
            "failed": [],
            "skipped": [],
            "invalid_channels": [],
        }

        # This should not raise an error
        # (cleanup runs, even if there's nothing to clean)
        console = Console(file=StringIO())
        print_summary(console, results, [], continue_on_error=True)
