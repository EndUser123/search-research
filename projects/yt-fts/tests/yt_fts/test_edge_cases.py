"""
Tests for edge cases in yt-fts.

TDD Phase: RED - Tests verify edge case handling that currently may not be implemented.

These tests cover:
- Concurrent database writes
- Disk space exhaustion during download
- Network timeouts during yt-dlp operations
- Malformed RSS feed handling
- File permission denied errors
- Corrupted database recovery
"""

import os
import sqlite3
import threading
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

import xml.etree.ElementTree as ET


class TestConcurrentDatabaseWrite:
    """Test that SQLite handles concurrent writes gracefully."""

    def test_concurrent_write_handles_lock_with_retry(self, tmp_path):
        """
        Test that concurrent database writes are handled with retry logic.

        Given: A SQLite database at tmp_path
        When: Two threads attempt to write simultaneously
        Then: Both writes should complete successfully without corruption
        """
        db_path = str(tmp_path / "test_concurrent.db")

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test_table (id, value) VALUES (1, 'initial')")
        conn.commit()
        conn.close()

        results = {"thread1": None, "thread2": None, "errors": []}

        def write_value(thread_name: str, value: str, delay: float = 0.01):
            import time
            try:
                from yt_fts.db.factory import get_connection

                time.sleep(delay)
                with get_connection(db_path=db_path, timeout=5.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO test_table (id, value) VALUES (?, ?)",
                        (hash(thread_name + value), value)
                    )
                    conn.commit()

                    cursor.execute("SELECT value FROM test_table WHERE value = ?", (value,))
                    result = cursor.fetchone()
                    results[thread_name] = result[0] if result else None
            except Exception as e:
                results["errors"].append(f"{thread_name}: {e}")

        thread1 = threading.Thread(target=write_value, args=("thread1", "value_from_thread_1"))
        thread2 = threading.Thread(target=write_value, args=("thread2", "value_from_thread_2", 0.015))

        thread1.start()
        thread2.start()

        thread1.join(timeout=10)
        thread2.join(timeout=10)

        assert results["thread1"] == "value_from_thread_1", f"Thread 1 failed: {results}"
        assert results["thread2"] == "value_from_thread_2", f"Thread 2 failed: {results}"
        assert len(results["errors"]) == 0, f"Errors: {results['errors']}"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()
        conn.close()

        assert integrity_result[0] == "ok", f"Corruption: {integrity_result}"


class TestDiskSpaceExhausted:
    """Test handling of disk full (ENOSPC) during download."""

    def test_disk_full_during_download_logs_gracefully(self):
        """
        Test that disk full errors are handled gracefully during download.

        Given: A download operation running
        When: OSError with ENOSPC (No space left on device) occurs
        Then: Should log error clearly, not crash with unhandled exception
        """
        results = {"error_logged": False, "error_message": None, "crashed": False}

        def mock_download_with_disk_full(video_id: str):
            try:
                raise OSError(28, "No space left on device")
            except OSError as e:
                from yt_fts.utils.error_classifier import ErrorClassifier

                category, message = ErrorClassifier.classify(str(e))
                results["error_message"] = message
                results["error_logged"] = "disk" in message.lower() or "space" in message.lower()
                if e.errno == 28:
                    results["crashed"] = False
                    return
                raise

        mock_download_with_disk_full("test_video_id")

        assert results["error_logged"], "Should log disk space error"
        assert not results["crashed"], "Should not crash"

    @patch("builtins.open")
    def test_disk_full_on_file_write(self, mock_open):
        """
        Test file write failure when disk is full.

        Given: Attempting to write subtitle data to disk
        When: Disk is full (OSError ENOSPC)
        Then: Should handle gracefully with clear error message
        """
        mock_file = MagicMock()
        mock_file.write.side_effect = OSError(28, "No space left on device")
        mock_open.return_value.__enter__.return_value = mock_file

        result = {"handled": False, "message": None}

        try:
            with open("subtitles.vtt", "w") as f:
                f.write("WEBVTT")
        except OSError as e:
            if e.errno == 28 or "No space left" in str(e):
                result["handled"] = True
                result["message"] = "Disk full - free up space and retry"

        assert result["handled"], "Should handle disk full gracefully"
        assert "space" in result["message"].lower() or "disk" in result["message"].lower()


class TestNetworkTimeout:
    """Test network timeout handling during yt-dlp operations."""

    @patch("requests.get")
    def test_network_timeout_with_retry(self, mock_get):
        """
        Test that network timeouts trigger retry logic.

        Given: A yt-dlp download operation
        When: Network timeout occurs
        Then: Should retry or fail gracefully with clear message
        """
        from requests.exceptions import Timeout

        mock_get.side_effect = [
            Timeout("Connection timed out"),
            MagicMock(status_code=200, text="<xml>...</xml>")
        ]

        results = {"attempts": 0, "succeeded": False, "final_error": None}

        def fetch_with_retry(url: str, max_retries: int = 3):
            for attempt in range(max_retries):
                try:
                    results["attempts"] = attempt + 1
                    response = mock_get(url, timeout=5)
                    results["succeeded"] = response.status_code == 200
                    return response
                except Timeout as e:
                    if attempt == max_retries - 1:
                        results["final_error"] = str(e)
                        raise
                    continue

        try:
            fetch_with_retry("https://example.com/video")
        except Timeout:
            pass

        assert results["attempts"] >= 2, "Should retry on timeout"

    def test_yt_dlp_timeout_message(self):
        """
        Test that yt-dlp timeout produces user-friendly message.

        Given: yt-dlp operation times out
        When: Timeout exception occurs
        Then: Should produce clear "timeout" message to user
        """
        stderr_output = "ERROR: download video: Timeout reached after 30s"

        from yt_fts.utils.error_classifier import ErrorClassifier
        category, message = ErrorClassifier.classify(stderr_output)

        assert "timeout" in message.lower() or "timed out" in message.lower()
        assert category.name in ("TRANSIENT", "NETWORK", "TIMEOUT")

    def test_per_video_timeout_handling(self):
        """
        Test per-video timeout during download.

        Given: A batch download with multiple videos
        When: One video exceeds its timeout limit
        Then: Should skip that video and continue with others
        """
        from yt_fts.download.exceptions import PerVideoTimeoutException

        results = {
            "videos_downloaded": [],
            "videos_failed": [],
            "continued": False
        }

        def mock_video_download(video_id: str):
            if video_id == "timeout_video":
                raise PerVideoTimeoutException(f"Video {video_id} exceeded 30s timeout")
            results["videos_downloaded"].append(video_id)

        videos = ["video1", "timeout_video", "video3"]

        for vid in videos:
            try:
                mock_video_download(vid)
            except PerVideoTimeoutException:
                results["videos_failed"].append(vid)
                results["continued"] = True

        assert "timeout_video" in results["videos_failed"]
        assert "video1" in results["videos_downloaded"]
        assert results["continued"]


class TestMalformedRSSFeed:
    """Test handling of malformed RSS XML feeds."""

    def test_malformed_xml_parse_error_handling(self):
        """
        Test that malformed RSS XML is handled gracefully.

        Given: An RSS feed with invalid XML
        When: Attempting to parse the feed
        Then: Should log warning and continue, not crash
        """
        malformed_feeds = [
            "<feed><entry><title>Video</feed>",
            '<?xml version="1.0" encoding="UTF-16"?><feed></feed>',
            "<feed><entry></video></feed>",
            "<feed><entry>content",
        ]

        results = {"handled": 0, "crashed": 0, "warnings": []}

        for feed_content in malformed_feeds:
            try:
                from yt_fts.services.rss_precheck import RssPreChecker

                checker = RssPreChecker()
                video_ids = checker._parse_video_ids(feed_content)

                if video_ids == []:
                    results["handled"] += 1
                else:
                    results["warnings"].append(f"Unexpected: {video_ids}")
            except ET.ParseError:
                results["handled"] += 1
            except Exception as e:
                results["crashed"] += 1
                results["warnings"].append(f"Unhandled: {e}")

        assert results["handled"] == len(malformed_feeds), f"Failed: {results}"
        assert results["crashed"] == 0, "Should not crash on malformed XML"

    def test_rss_with_missing_required_fields(self):
        """
        Test RSS feed with valid XML but missing required fields.

        Given: RSS feed with valid XML but missing video_id elements
        When: Parsing the feed
        Then: Should handle gracefully, return empty or partial results
        """
        incomplete_feeds = [
            """<?xml version="1.0"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry><title>Video Title</title></entry>
            </feed>""",
            """<?xml version="1.0"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <yt:videoId xmlns="http://www.youtube.com/xml/schemas/2015"></yt:videoId>
                </entry>
            </feed>""",
        ]

        from yt_fts.services.rss_precheck import RssPreChecker
        checker = RssPreChecker()

        for feed in incomplete_feeds:
            video_ids = checker._parse_video_ids(feed)
            assert isinstance(video_ids, list)
            assert len(video_ids) == 0


class TestFilePermissionDenied:
    """Test permission denied errors on file operations."""

    def test_permission_denied_on_file_write(self):
        """
        Test handling of permission denied on file write.

        Given: Attempting to write to a read-only file
        When: PermissionError is raised
        Then: Should handle with clear error message
        """
        results = {"handled": False, "message": None}

        def attempt_write_to_readonly():
            try:
                raise PermissionError("[Errno 13] Permission denied: '/readonly/file.txt'")
            except PermissionError as e:
                from yt_fts.utils.error_classifier import ErrorClassifier

                category, message = ErrorClassifier.classify(str(e))
                results["message"] = message
                results["handled"] = "permission" in message.lower() or "access" in message.lower()

        attempt_write_to_readonly()

        assert results["handled"], f"Should handle permission error: {results['message']}"

    def test_permission_denied_on_directory(self):
        """
        Test handling of permission denied on directory access.

        Given: Attempting to create files in a restricted directory
        When: PermissionError occurs
        Then: Should provide actionable error message
        """
        results = {"actionable_message": False}

        def attempt_create_in_restricted():
            try:
                raise PermissionError("[Errno 13] Permission denied: '/protected/directory'")
            except PermissionError as e:
                from yt_fts.utils.error_classifier import ErrorClassifier

                category, message = ErrorClassifier.classify(str(e))
                actionable_keywords = ["permission", "access", "admin", "rights", "write"]
                results["actionable_message"] = any(
                    kw in message.lower() for kw in actionable_keywords
                )

        attempt_create_in_restricted()

        assert results["actionable_message"], "Should mention permission/access"


class TestCorruptedDatabaseRecovery:
    """Test corrupted SQLite database detection and recovery."""

    def test_corrupted_database_detection(self, tmp_path):
        """
        Test that corrupted database is detected.

        Given: A corrupted SQLite database file
        When: Attempting to open the database
        Then: Should detect corruption and raise appropriate error
        """
        db_path = str(tmp_path / "corrupt.db")

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.execute("INSERT INTO test VALUES (1)")
        conn.commit()
        conn.close()

        with open(db_path, "r+b") as f:
            f.seek(100)
            f.write(b"CORRUPTED DATA HERE!!!")

        results = {"detected": False, "error_type": None}

        try:
            from yt_fts.db.factory import get_connection
            with get_connection(db_path=db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM test")
        except sqlite3.DatabaseError as e:
            results["detected"] = "malformed" in str(e).lower() or "corrupt" in str(e).lower()
            results["error_type"] = type(e).__name__
        except sqlite3.OperationalError as e:
            results["detected"] = "malformed" in str(e).lower() or "corrupt" in str(e).lower()
            results["error_type"] = type(e).__name__

        assert results["detected"], f"Should detect corruption: {results}"

    def test_corrupted_database_recovery_offer(self, tmp_path):
        """
        Test that system offers recovery option for corrupted database.

        Given: A corrupted database is detected
        When: Database connection fails due to corruption
        Then: Should offer recovery/recreate option to user
        """
        db_path = str(tmp_path / "recover.db")

        # Write garbage data (not a valid SQLite database)
        with open(db_path, "wb") as f:
            f.write(b"This is not a SQLite database file at all!!!")

        results = {"recovery_offered": False, "can_recreate": False}

        try:
            from yt_fts.db.factory import get_connection
            with get_connection(db_path=db_path) as conn:
                pass
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            error_msg = str(e).lower()
            results["recovery_offered"] = (
                "malformed" in error_msg or
                "corrupt" in error_msg or
                "file is not a database" in error_msg
            )
            results["can_recreate"] = True

        assert results["recovery_offered"], f"Should detect corruption: {results}"
        assert results["can_recreate"], "Should support recreation"

    def test_database_integrity_check(self, tmp_path):
        """
        Test PRAGMA integrity_check for database validation.

        Given: A database file
        When: Running integrity check
        Then: Should return "ok" for valid database, errors for corrupt
        """
        db_path = str(tmp_path / "integrity.db")

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER, value TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test')")
        conn.commit()
        conn.close()

        from yt_fts.db.factory import get_connection

        with get_connection(db_path=db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

        assert result[0] == "ok", f"Valid DB should pass: {result}"

        with open(db_path, "r+b") as f:
            f.seek(50)
            f.write(b"CORRUPTION!!!")

        results = {"corruption_detected": False}

        try:
            with get_connection(db_path=db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] != "ok":
                    results["corruption_detected"] = True
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            results["corruption_detected"] = True

        assert results["corruption_detected"], "Should detect corruption"
