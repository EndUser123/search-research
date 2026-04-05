"""Tests for diagnostics module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from yt_fts.diagnostics.checker import DiagnosticChecker, DiagnosticResult, Status
from yt_fts.diagnostics.network import NetworkChecker
from yt_fts.diagnostics.ytdlp import YtdlpChecker
from yt_fts.diagnostics.cookies import CookieChecker
from yt_fts.diagnostics.database import DatabaseChecker


class TestDiagnosticChecker:
    """Test base DiagnosticChecker class."""

    def test_add_result(self):
        """Test adding a diagnostic result."""
        checker = DiagnosticChecker()
        assert len(checker.results) == 0

        checker.add_result(
            category="Test Category",
            status=Status.PASS,
            message="Test passed",
            details=["Detail 1", "Detail 2"],
        )

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "Test Category"
        assert result.status == Status.PASS
        assert result.message == "Test passed"
        assert result.details == ["Detail 1", "Detail 2"]
        assert result.remediation is None

    def test_add_result_with_remediation(self):
        """Test adding a result with remediation."""
        checker = DiagnosticChecker()

        checker.add_result(
            category="Test Category",
            status=Status.FAIL,
            message="Test failed",
            remediation="Fix the thing",
        )

        result = checker.results[0]
        assert result.remediation == "Fix the thing"

    def test_clear_results(self):
        """Test clearing results."""
        checker = DiagnosticChecker()
        checker.add_result(
            category="Test",
            status=Status.PASS,
            message="Test",
        )
        assert len(checker.results) == 1

        checker.results.clear()
        assert len(checker.results) == 0


class TestNetworkChecker:
    """Test network connectivity diagnostics."""

    def test_internet_check(self):
        """Test internet connectivity check."""
        checker = NetworkChecker()
        checker._check_internet()

        # Should have exactly one result
        assert len(checker.results) == 1

        result = checker.results[0]
        assert result.category == "Internet Connection"
        # Either PASS or FAIL depending on network
        assert result.status in (Status.PASS, Status.FAIL)

    def test_dns_check(self):
        """Test DNS resolution check."""
        checker = NetworkChecker()
        checker._check_dns()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "DNS Resolution"

    def test_youtube_reachability_check(self):
        """Test YouTube reachability check."""
        checker = NetworkChecker()
        checker._check_youtube_reachability()

        # Should have one result for YouTube reachability
        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "YouTube Reachability"
        # Should have details for each host checked
        assert len(result.details) > 0

    def test_full_run(self):
        """Test running all network checks."""
        checker = NetworkChecker()
        results = checker.run()

        # Should have 3 results: internet, DNS, YouTube
        assert len(results) == 3


class TestYtdlpChecker:
    """Test yt-dlp diagnostics."""

    def test_ytdlp_installation_check(self):
        """Test yt-dlp installation check."""
        checker = YtdlpChecker()
        checker._check_installation()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "yt-dlp Installation"

    def test_ytdlp_version_check(self):
        """Test yt-dlp version check."""
        checker = YtdlpChecker()
        checker._check_version()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "yt-dlp Version"
        if result.status == Status.PASS:
            # Should have version details
            assert len(result.details) > 0

    def test_full_run(self):
        """Test running all yt-dlp checks."""
        checker = YtdlpChecker()
        results = checker.run()

        # Should have results for installation, version, and maybe functionality
        assert len(results) >= 2


class TestCookieChecker:
    """Test cookie file diagnostics."""

    def test_cookie_file_check(self):
        """Test cookie file check."""
        checker = CookieChecker()
        checker._check_cookie_file()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "Cookie File"

    def test_full_run(self):
        """Test running all cookie checks."""
        checker = CookieChecker()
        results = checker.run()

        assert len(results) == 1


class TestDatabaseChecker:
    """Test database diagnostics."""

    def test_database_file_check(self):
        """Test database file check."""
        checker = DatabaseChecker()
        checker._check_database_file()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.category == "Database File"
        # Either PASS (file exists) or INFO (new installation)
        assert result.status in (Status.PASS, Status.INFO)

    def test_database_connection_skipped_when_no_file(self):
        """Test that connection check is skipped when DB doesn't exist."""
        from unittest.mock import patch
        from pathlib import Path

        checker = DatabaseChecker()

        # Mock get_db_path to return non-existent path
        with patch('yt_fts.diagnostics.database.get_db_path', return_value='/nonexistent/db.sqlite'):
            with patch.object(Path, 'exists', return_value=False):
                checker._check_database_connection()

                # Should not add any results if DB doesn't exist
                assert len(checker.results) == 0

    def test_full_run(self, tmp_path):
        """Test running all database checks with temp database."""
        # Create a temporary test database
        test_db = tmp_path / "test_subtitles.db"

        # Set up a minimal database schema
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Videos (
                video_id TEXT PRIMARY KEY,
                video_title TEXT,
                channel_id TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Channels (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                channel_url TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Subtitles (
                subtitle_id INTEGER PRIMARY KEY,
                video_id TEXT,
                timestamp TEXT,
                text TEXT
            )
        """)
        # Add test data
        cursor.execute("INSERT INTO Videos VALUES ('vid1', 'Test Video', 'ch1', '2024-01-01')")
        cursor.execute("INSERT INTO Channels VALUES ('ch1', 'Test Channel', 'https://youtube.com/ch1')")
        cursor.execute("INSERT INTO Subtitles (video_id, timestamp, text) VALUES ('vid1', '0:00', 'Test subtitle')")
        conn.commit()
        conn.close()

        # Mock get_db_path to return our temp database
        with patch('yt_fts.diagnostics.database.get_db_path', return_value=str(test_db)):
            checker = DatabaseChecker()
            results = checker.run()

        # Should have results for file, connection, and integrity checks
        assert len(results) >= 2

        # Check that file check passed
        file_result = next((r for r in results if r.category == "Database File"), None)
        assert file_result is not None
        assert file_result.status == Status.PASS

        # Check that connection check passed
        conn_result = next((r for r in results if r.category == "Database Connection"), None)
        assert conn_result is not None
        assert conn_result.status == Status.PASS

        # Check that integrity check passed
        integrity_result = next((r for r in results if r.category == "Database Integrity"), None)
        assert integrity_result is not None
        assert integrity_result.status == Status.PASS
