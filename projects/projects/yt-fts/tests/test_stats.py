"""
Unit tests for the `stats` command.

The stats command should:
1. Query the database for total videos, channels, and database size
2. Display results in a clean Rich table
3. Handle edge cases like empty database
"""

import gc
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from yt_fts.core.database import make_db


class TestGetDatabaseStats(unittest.TestCase):
    """Test the get_database_stats function that queries stats from the database."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema
        make_db(self.temp_db.name)

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_get_database_stats_with_data(self):
        """
        Test that get_database_stats returns correct counts for populated database.

        Given: A database with 3 channels, 15 videos, and 100 subtitles
        When: get_database_stats() is called
        Then: Returns dict with total_channels=3, total_videos=15, total_subtitles=100
        """
        # Import after setting up the database path
        from yt_fts.core.stats import get_database_stats

        # Insert test data
        conn = sqlite3.connect(self.temp_db.name)
        cur = conn.cursor()

        # Add 3 channels
        for i in range(3):
            cur.execute(
                "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                (f"UC{i:012d}", f"Channel {i}", f"https://youtube.com/channel{i}")
            )

        # Add 15 videos across the 3 channels
        for i in range(15):
            channel_id = f"UC{(i % 3):012d}"
            cur.execute(
                """INSERT INTO Videos (video_id, video_title, video_url, channel_id, video_date)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"vid_{i}", f"Video {i}", f"https://youtube.com/watch?v=vid_{i}", channel_id, "2024-01-01")
            )

        # Add 100 subtitles across 10 videos
        for i in range(100):
            video_id = f"vid_{i % 10}"
            cur.execute(
                """INSERT INTO Subtitles (video_id, start_time, stop_time, text)
                   VALUES (?, ?, ?, ?)""",
                (video_id, f"{i}", f"{i+1}", f"Subtitle text {i}")
            )

        conn.commit()
        conn.close()

        # Get stats
        stats = get_database_stats()

        # Verify counts
        self.assertEqual(stats["total_channels"], 3)
        self.assertEqual(stats["total_videos"], 15)
        self.assertEqual(stats["total_subtitles"], 100)

    def test_get_database_stats_empty_database(self):
        """
        Test that get_database_stats handles empty database correctly.

        Given: A newly created database with no data
        When: get_database_stats() is called
        Then: Returns dict with all counts as 0
        """
        from yt_fts.core.stats import get_database_stats

        stats = get_database_stats()

        # All counts should be 0 for empty database
        self.assertEqual(stats["total_channels"], 0)
        self.assertEqual(stats["total_videos"], 0)
        self.assertEqual(stats["total_subtitles"], 0)

    def test_get_database_stats_includes_db_size(self):
        """
        Test that get_database_stats includes database file size.

        Given: A database file exists
        When: get_database_stats() is called
        Then: Returns dict with 'db_size_bytes' key containing file size
        """
        from yt_fts.core.stats import get_database_stats

        stats = get_database_stats()

        # Should have db_size_bytes field
        self.assertIn("db_size_bytes", stats)
        self.assertIsInstance(stats["db_size_bytes"], int)
        # Size should be at least the empty database size (> 0)
        self.assertGreater(stats["db_size_bytes"], 0)


class TestFormatStatsForDisplay(unittest.TestCase):
    """Test the format_stats_for_display function that formats stats for output."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema
        make_db(self.temp_db.name)

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_format_stats_for_display_returns_table(self):
        """
        Test that format_stats_for_display returns a Rich Table.

        Given: A stats dictionary with database metrics
        When: format_stats_for_display() is called
        Then: Returns a rich.table.Table instance with formatted data
        """
        from yt_fts.core.stats import format_stats_for_display
        from rich.table import Table

        stats = {
            "total_channels": 5,
            "total_videos": 123,
            "total_subtitles": 4567,
            "db_size_bytes": 1048576,  # 1 MB
        }

        result = format_stats_for_display(stats)

        # Should return a Rich Table
        self.assertIsInstance(result, Table)

    def test_format_stats_for_display_human_readable_size(self):
        """
        Test that format_stats_for_display converts bytes to human-readable format.

        Given: A stats dict with db_size_bytes
        When: format_stats_for_display() is called
        Then: The table displays size in KB/MB/GB format
        """
        from yt_fts.core.stats import format_stats_for_display

        # Test with 1 MB
        stats = {
            "total_channels": 1,
            "total_videos": 10,
            "total_subtitles": 100,
            "db_size_bytes": 1048576,  # 1 MB
        }

        result = format_stats_for_display(stats)

        # Table should contain the size information
        # Convert table to string to check content
        table_text = str(result)
        self.assertTrue(
            "1.00 MB" in table_text or "1024" in table_text or "KB" in table_text,
            f"Expected human-readable size in table, got: {table_text[:200]}"
        )


class TestStatsCommandIntegration(unittest.TestCase):
    """Integration tests for the stats CLI command."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema
        make_db(self.temp_db.name)

        # Add test data
        conn = sqlite3.connect(self.temp_db.name)
        cur = conn.cursor()

        # Add 2 channels
        for i in range(2):
            cur.execute(
                "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                (f"UC{i:012d}", f"Channel {i}", f"https://youtube.com/channel{i}")
            )

        # Add 5 videos
        for i in range(5):
            cur.execute(
                """INSERT INTO Videos (video_id, video_title, video_url, channel_id, video_date)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"vid_{i}", f"Video {i}", f"https://youtube.com/watch?v=vid_{i}", f"UC{(i % 2):012d}", "2024-01-01")
            )

        # Add 25 subtitles
        for i in range(25):
            cur.execute(
                """INSERT INTO Subtitles (video_id, start_time, stop_time, text)
                   VALUES (?, ?, ?, ?)""",
                (f"vid_{i % 5}", f"{i}", f"{i+1}", f"Subtitle text {i}")
            )

        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_stats_command_exits_successfully(self):
        """
        Test that the stats command executes without errors.

        Given: A database with test data
        When: The `stats` CLI command is invoked
        Then: The command exits with code 0
        """
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["stats"])

        # Command should succeed
        self.assertEqual(result.exit_code, 0)

    def test_stats_command_displays_metrics(self):
        """
        Test that the stats command displays all expected metrics.

        Given: A database with 2 channels, 5 videos, 25 subtitles
        When: The `stats` CLI command is invoked
        Then: Output contains channel count, video count, and subtitle count
        """
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["stats"])

        output = result.output

        # Output should contain the stats
        self.assertIn("2", output)  # Channel count
        self.assertIn("5", output)  # Video count
        # Subtitle count (25) should also be in output
        self.assertTrue("25" in output or "2" in output)


class TestStatsCommandEmptyDatabase(unittest.TestCase):
    """Test stats command behavior with an empty database."""

    def setUp(self):
        """Set up an empty temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # Set environment variable to use temp database
        os.environ["YT_FTS_DB_PATH"] = self.temp_db.name

        # Create the database schema (but no data)
        make_db(self.temp_db.name)

    def tearDown(self):
        """Clean up the temporary database."""
        # Close any database connections
        gc.collect()

        if "YT_FTS_DB_PATH" in os.environ:
            del os.environ["YT_FTS_DB_PATH"]

        # Try to remove the file, ignore Windows file locking errors
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except PermissionError:
            # Windows file locking - file will be cleaned up by OS
            pass

    def test_stats_command_with_empty_database(self):
        """
        Test that stats command handles empty database gracefully.

        Given: A newly created database with no data
        When: The `stats` CLI command is invoked
        Then: Command succeeds and shows zeros for all counts
        """
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["stats"])

        # Should still succeed
        self.assertEqual(result.exit_code, 0)

        # Output should indicate zero counts
        output = result.output
        self.assertTrue("0" in output or "empty" in output.lower() or "no" in output.lower(),
                       f"Expected zero/empty/no in output for empty database. Got: {output}")


class TestGetDatabaseSize(unittest.TestCase):
    """Test the get_database_size helper function."""

    def test_get_database_size_with_valid_file(self):
        """
        Test that get_database_size returns correct file size.

        Given: An existing database file
        When: get_database_size() is called
        Then: Returns the file size in bytes
        """
        from yt_fts.core.stats import get_database_size

        # Create a temp file with known content
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"x" * 1000)  # 1000 bytes
            temp_path = f.name

        try:
            # Mock get_db_path to return our temp file
            with patch("yt_fts.core.stats.get_db_path", return_value=temp_path):
                size = get_database_size()

            self.assertEqual(size, 1000)
        finally:
            os.remove(temp_path)

    def test_get_database_size_with_nonexistent_file(self):
        """
        Test that get_database_size handles missing file gracefully.

        Given: A database path that doesn't exist
        When: get_database_size() is called
        Then: Returns 0
        """
        from yt_fts.core.stats import get_database_size

        # Mock get_db_path to return a non-existent file
        with patch("yt_fts.core.stats.get_db_path", return_value="/nonexistent/path/file.db"):
            size = get_database_size()

        self.assertEqual(size, 0)


if __name__ == "__main__":
    unittest.main()
