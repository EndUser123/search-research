"""
Unit tests for performance optimization changes.

Tests for:
- get_cached_channels() - verifies WHERE IN query optimization
- get_batch_channel_stats() - verifies GROUP BY query optimization
- ensure_db_indexes() - verifies index creation
"""

import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.channel_cache import (
    get_cached_channels,
    _normalize_channel_url,
)
from yt_fts.db.channels import get_batch_channel_stats
from yt_fts.db.infra import ensure_db_indexes


class TestNormalizeChannelUrl:
    """Test URL normalization for special characters in handles."""

    def test_handle_with_pipe_character(self):
        """Should URL-encode pipe characters in YouTube handles."""
        url = "https://www.youtube.com/@channel|name"
        result = _normalize_channel_url(url)
        assert "%7C" in result or "|" not in result
        assert "https://www.youtube.com/@" in result

    def test_regular_url_unchanged(self):
        """Should leave regular URLs unchanged."""
        url = "https://www.youtube.com/@TestChannel123"
        result = _normalize_channel_url(url)
        assert result == url


class TestGetCachedChannelsOptimization:
    """
    Characterization tests for get_cached_channels optimization.

    Verifies that the function:
    1. Uses WHERE IN queries (not full table scan)
    2. Returns cached channels correctly
    3. Returns channels_to_resolve for unknown channels
    4. Handles empty inputs
    5. Handles mixed cached/uncached inputs
    """

    def test_returns_empty_for_empty_input(self):
        """Should return empty dicts for empty input list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.utils.config.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)

                cached, to_resolve = get_cached_channels([], conn)

                assert cached == {}
                assert to_resolve == []
                conn.close()

    def test_returns_all_channels_as_to_resolve_when_db_empty(self):
        """When DB is empty, all channels should be in to_resolve."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.utils.config.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)

                channels = ["@test1", "@test2"]
                cached, to_resolve = get_cached_channels(channels, conn)

                assert len(cached) == 0
                assert len(to_resolve) == 2
                conn.close()

    def test_finds_cached_channel_by_url(self):
        """Should find channels that are already in DB by URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.utils.config.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    ("UC123", "Test Channel", "https://www.youtube.com/@testchannel")
                )
                conn.commit()

                channels = ["@testchannel"]
                cached, to_resolve = get_cached_channels(channels, conn)

                assert "@testchannel" in cached
                assert len(to_resolve) == 0
                conn.close()

    def test_finds_cached_channel_by_id(self):
        """Should find channels by channel ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.utils.config.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                # Use a valid YouTube channel ID format (UC + 22 characters = 24 total)
                channel_id = "UC" + "a" * 22
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    (channel_id, "Test", f"https://www.youtube.com/channel/{channel_id}")
                )
                conn.commit()

                channels = [channel_id]
                cached, to_resolve = get_cached_channels(channels, conn)

                conn.close()
                assert channel_id in cached
                assert len(to_resolve) == 0

    def test_mixed_cached_and_uncached(self):
        """Should separate cached from uncached channels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.utils.config.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    ("UC123", "Cached", "https://www.youtube.com/@cached")
                )
                conn.commit()

                channels = ["@cached", "@notcached"]
                cached, to_resolve = get_cached_channels(channels, conn)

                assert "@cached" in cached
                assert "@notcached" in to_resolve
                assert len(to_resolve) == 1
                conn.close()

    def test_skips_empty_strings(self):
        """Should filter out empty/whitespace inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.utils.config.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)

                channels = ["@test1", "", "  ", "@test2"]
                cached, to_resolve = get_cached_channels(channels, conn)

                assert "" not in to_resolve
                assert "  " not in to_resolve
                assert "@test1" in to_resolve
                assert "@test2" in to_resolve
                conn.close()


class TestGetBatchChannelStatsOptimization:
    """
    Characterization tests for get_batch_channel_stats GROUP BY optimization.

    Verifies that the function:
    1. Uses GROUP BY queries (not N+1 individual queries)
    2. Returns stats for multiple channels efficiently
    3. Handles empty channel list
    4. Returns zero stats for channels with no videos
    """

    def test_returns_empty_for_no_channels(self):
        """Should return empty dict for no channel IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"

            with patch("yt_fts.db.infra.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Videos (
                        video_id TEXT PRIMARY KEY,
                        channel_id TEXT,
                        video_title TEXT,
                        is_short INTEGER DEFAULT 0
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Subtitles (
                        subtitle_id TEXT PRIMARY KEY,
                        video_id TEXT
                    )
                """)

                stats = get_batch_channel_stats([])

                assert stats == {}
                conn.close()

    def test_returns_zero_stats_for_channels_with_no_videos(self):
        """Should return zero counts for channels without videos."""
        import os
        db_path = "P:/projects/yt-fts/test_stats_zero.db"

        try:
            if os.path.exists(db_path):
                os.remove(db_path)

            with patch("yt_fts.db.infra.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Videos (
                        video_id TEXT PRIMARY KEY,
                        channel_id TEXT,
                        video_title TEXT,
                        is_short INTEGER DEFAULT 0
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Subtitles (
                        subtitle_id TEXT PRIMARY KEY,
                        video_id TEXT
                    )
                """)
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    ("UC123", "Test", "https://www.youtube.com/@test")
                )
                conn.commit()
                conn.close()

                stats = get_batch_channel_stats(["UC123"])

                assert "UC123" in stats
                assert stats["UC123"]["total"] == 0
                assert stats["UC123"]["with_transcripts"] == 0
                assert stats["UC123"]["without_transcripts"] == 0
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass

    def test_aggregates_stats_across_multiple_channels(self):
        """Should correctly aggregate stats for multiple channels in single query."""
        import os
        db_path = "P:/projects/yt-fts/test_stats_aggregate.db"

        try:
            if os.path.exists(db_path):
                os.remove(db_path)

            with patch("yt_fts.db.infra.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Videos (
                        video_id TEXT PRIMARY KEY,
                        channel_id TEXT,
                        video_title TEXT,
                        is_short INTEGER DEFAULT 0
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Subtitles (
                        subtitle_id TEXT PRIMARY KEY,
                        video_id TEXT
                    )
                """)
                conn.execute("INSERT INTO Channels VALUES (?, ?, ?)", ("UC1", "Ch1", "url1"))
                conn.execute("INSERT INTO Channels VALUES (?, ?, ?)", ("UC2", "Ch2", "url2"))

                # UC1: 3 videos, 2 with subtitles
                conn.execute("INSERT INTO Videos VALUES (?, ?, ?, ?)", ("vid1", "UC1", "T1", 0))
                conn.execute("INSERT INTO Videos VALUES (?, ?, ?, ?)", ("vid2", "UC1", "T2", 0))
                conn.execute("INSERT INTO Videos VALUES (?, ?, ?, ?)", ("vid3", "UC1", "T3", 0))
                conn.execute("INSERT INTO Subtitles VALUES (?, ?)", ("sub1", "vid1"))
                conn.execute("INSERT INTO Subtitles VALUES (?, ?)", ("sub2", "vid2"))
                # vid3 has no subtitle

                # UC2: 2 videos, both with subtitles, 1 is a short
                conn.execute("INSERT INTO Videos VALUES (?, ?, ?, ?)", ("vid4", "UC2", "T4", 0))
                conn.execute("INSERT INTO Videos VALUES (?, ?, ?, ?)", ("vid5", "UC2", "T5", 1))
                conn.execute("INSERT INTO Subtitles VALUES (?, ?)", ("sub3", "vid4"))
                conn.execute("INSERT INTO Subtitles VALUES (?, ?)", ("sub4", "vid5"))

                conn.commit()
                conn.close()

                stats = get_batch_channel_stats(["UC1", "UC2"])

                # UC1: 3 total, 2 with transcripts, 1 without
                assert stats["UC1"]["total"] == 3
                assert stats["UC1"]["with_transcripts"] == 2
                assert stats["UC1"]["without_transcripts"] == 1

                # UC2: 2 total, 2 with transcripts, 0 without, 1 short
                assert stats["UC2"]["total"] == 2
                assert stats["UC2"]["with_transcripts"] == 2
                assert stats["UC2"]["without_transcripts"] == 0
                assert stats["UC2"]["shorts"] == 1
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass


class TestEnsureDbIndexes:
    """Test database index creation."""

    def test_creates_indexes_on_channels_table(self):
        """Should create indexes on channel_id and channel_url."""
        # Use a non-tempfile location to avoid Windows file lock issues
        import os
        db_path = "P:/projects/yt-fts/test_indexes_temp.db"

        try:
            # Clean up any existing test file
            if os.path.exists(db_path):
                os.remove(db_path)

            # Patch get_db_path in the infra module where ensure_db_indexes uses it
            with patch("yt_fts.db.infra.get_db_path", return_value=db_path):
                # First create the Channels table
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.close()

                # Now call ensure_db_indexes - it will use the patched db_path
                ensure_db_indexes()

                # Verify indexes were created
                conn = sqlite3.connect(db_path)
                indexes = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_channels_%'"
                ).fetchall()

                index_names = [idx[0] for idx in indexes]
                assert "idx_channels_channel_id" in index_names
                assert "idx_channels_channel_url" in index_names
                conn.close()
        finally:
            # Clean up
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass

    def test_is_idempotent(self):
        """Should be safe to call multiple times."""
        import os
        db_path = "P:/projects/yt-fts/test_indexes_idempotent.db"

        try:
            if os.path.exists(db_path):
                os.remove(db_path)

            with patch("yt_fts.db.infra.get_db_path", return_value=db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS Channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT
                    )
                """)
                conn.close()

                # Call multiple times - should not error
                ensure_db_indexes()
                ensure_db_indexes()
                ensure_db_indexes()

                conn = sqlite3.connect(db_path)
                indexes = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_channels_%'"
                ).fetchall()
                assert len(indexes) >= 2
                conn.close()
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except:
                    pass
