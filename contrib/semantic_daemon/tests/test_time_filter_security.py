"""Tests for time filter SQL injection vulnerability in unified_semantic_daemon.py.

These tests verify that malicious time filter inputs (after/before parameters)
are properly validated and rejected to prevent SQL injection attacks.

Vulnerability Location: unified_semantic_daemon.py:1596-1639
- The `after` and `before` parameters are passed directly to SQL without ISO timestamp validation
- Attack vector: --after "2026-01-01' OR '1'='1" bypasses filtering

Run with: pytest tests/daemons/test_time_filter_security.py -v

RED Phase: This test is EXPECTED TO FAIL until validation is implemented.
"""

import os
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest


class TestTimeFilterSQLInjection:
    """Test suite for SQL injection vulnerability in time filter parameters."""

    @pytest.fixture
    def daemon_instance(self):
        """Create a minimal UnifiedSemanticDaemon instance for testing."""
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Create daemon without starting it (just for method access)
        daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
        daemon._pipe_name = r"\\.\pipe\test_semantic_security"
        daemon._num_workers = 1
        daemon._server_thread = None
        daemon._stop_event = None
        daemon._executor = None
        daemon._cks = None
        daemon._last_chs_index_time = 0
        daemon._last_faiss_update = 0
        daemon._chs_index_thread = None
        daemon._chs_index_complete = None
        daemon._chs_indexing = False
        daemon._last_activity_time = time.time()

        yield daemon

    @pytest.fixture
    def temp_chat_db(self):
        """Create a temporary chat history database with FTS5 index."""
        # Create temp database
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            # Setup database with FTS5 table
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE chat_messages (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    timestamp TEXT,
                    session_id TEXT,
                    role TEXT
                )
            """)

            # Create FTS5 virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE chat_messages_fts USING fts5(
                    content, content='chat_messages', content_rowid='id'
                )
            """)

            # Insert test data
            test_messages = [
                (1, "Test message one", "2026-01-15T10:00:00", "session1", "user"),
                (2, "Test message two", "2026-01-16T11:00:00", "session1", "assistant"),
                (3, "Test message three", "2026-01-17T12:00:00", "session2", "user"),
            ]

            conn.executemany(
                "INSERT INTO chat_messages (id, content, timestamp, session_id, role) VALUES (?, ?, ?, ?, ?)",
                test_messages,
            )

            # Populate FTS5 index
            conn.execute(
                "INSERT INTO chat_messages_fts(rowid, content) SELECT id, content FROM chat_messages"
            )

            conn.commit()
            conn.close()

            yield db_path

        finally:
            # Cleanup - close any connections first
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
            except PermissionError:
                # File may still be locked, will be cleaned up by temp dir
                pass

    def test_sql_injection_after_single_quote_bypass(self, daemon_instance, temp_chat_db):
        """
        Test that single quote injection in 'after' parameter is rejected.

        Given: A malicious user provides an 'after' parameter with SQL injection
        When: The FTS5 search is called with the malicious input
        Then: ValueError should be raised (or input should be sanitized)

        Attack: --after "2026-01-01' OR '1'='1"
        Expected: Input should be validated as ISO timestamp format only
        """
        # Mock the database path to use our temp database
        with patch.object(daemon_instance, "_get_chs_db_path", return_value=Path(temp_chat_db)):
            # Malicious input with SQL injection attempt
            malicious_after = "2026-01-01' OR '1'='1"

            # This should raise ValueError for invalid timestamp format
            # Currently FAILS because no validation exists
            with pytest.raises(
                ValueError, match="Invalid ISO timestamp format|Invalid time filter"
            ):
                result = daemon_instance._fts5_search(
                    query="test", limit=10, params={"after": malicious_after}
                )

    def test_sql_injection_before_boolean_injection(self, daemon_instance, temp_chat_db):
        """
        Test that boolean injection in 'before' parameter is rejected.

        Given: A malicious user provides a 'before' parameter with SQL injection
        When: The FTS5 search is called with the malicious input
        Then: ValueError should be raised (or input should be sanitized)

        Attack: --before "2026-12-31' OR '1'='1'"
        Expected: Input should be validated as ISO timestamp format only
        """
        with patch.object(daemon_instance, "_get_chs_db_path", return_value=Path(temp_chat_db)):
            # Malicious input with boolean injection
            malicious_before = "2026-12-31' OR '1'='1'"

            # This should raise ValueError for invalid timestamp format
            with pytest.raises(
                ValueError, match="Invalid ISO timestamp format|Invalid time filter"
            ):
                result = daemon_instance._fts5_search(
                    query="test", limit=10, params={"before": malicious_before}
                )

    def test_sql_injection_after_comment_injection(self, daemon_instance, temp_chat_db):
        """
        Test that SQL comment injection in 'after' parameter is rejected.

        Given: A malicious user provides an 'after' parameter with comment injection
        When: The FTS5 search is called with the malicious input
        Then: ValueError should be raised (or input should be sanitized)

        Attack: --after "2026-01-01'--"
        Expected: Input should be validated as ISO timestamp format only
        """
        with patch.object(daemon_instance, "_get_chs_db_path", return_value=Path(temp_chat_db)):
            # Malicious input with SQL comment
            malicious_after = "2026-01-01'--"

            # This should raise ValueError for invalid timestamp format
            with pytest.raises(
                ValueError, match="Invalid ISO timestamp format|Invalid time filter"
            ):
                result = daemon_instance._fts5_search(
                    query="test", limit=10, params={"after": malicious_after}
                )

    def test_sql_injection_union_injection(self, daemon_instance, temp_chat_db):
        """
        Test that UNION SELECT injection in 'after' parameter is rejected.

        Given: A malicious user provides an 'after' parameter with UNION injection
        When: The FTS5 search is called with the malicious input
        Then: ValueError should be raised (or input should be sanitized)

        Attack: --after "2026-01-01' UNION SELECT * FROM messages--"
        Expected: Input should be validated as ISO timestamp format only
        """
        with patch.object(daemon_instance, "_get_chs_db_path", return_value=Path(temp_chat_db)):
            # Malicious input with UNION injection attempt
            malicious_after = "2026-01-01' UNION SELECT * FROM messages--"

            # This should raise ValueError for invalid timestamp format
            with pytest.raises(
                ValueError, match="Invalid ISO timestamp format|Invalid time filter"
            ):
                result = daemon_instance._fts5_search(
                    query="test", limit=10, params={"after": malicious_after}
                )

    def test_valid_iso_timestamp_accepted(self, daemon_instance, temp_chat_db):
        """
        Test that valid ISO timestamps are still accepted (positive test).

        Given: A user provides a valid ISO timestamp for 'after' parameter
        When: The FTS5 search is called with the valid input
        Then: Search should execute successfully with time filter applied

        This ensures the fix doesn't break legitimate use cases.
        """
        with patch.object(daemon_instance, "_get_chs_db_path", return_value=Path(temp_chat_db)):
            # Valid ISO timestamp
            valid_after = "2026-01-16T00:00:00"

            # This should work without error
            result = daemon_instance._fts5_search(
                query="test", limit=10, params={"after": valid_after}
            )

            # Should return results (only messages after 2026-01-16)
            assert isinstance(result, list)
            # We expect 1-2 results since we have 3 test messages
            # and we're filtering for messages after 2026-01-16T00:00:00
            assert len(result) >= 1

    def test_combined_after_before_injection_attempts(self, daemon_instance, temp_chat_db):
        """
        Test that injection attempts in both 'after' and 'before' are rejected.

        Given: A malicious user provides malicious inputs for both parameters
        When: The FTS5 search is called with both malicious inputs
        Then: ValueError should be raised (or inputs should be sanitized)

        Attack: --after "2026-01-01' OR '1'='1" --before "2026-12-31' OR '2'='2'"
        Expected: Both inputs should be validated
        """
        with patch.object(daemon_instance, "_get_chs_db_path", return_value=Path(temp_chat_db)):
            # Both parameters malicious
            malicious_params = {
                "after": "2026-01-01' OR '1'='1",
                "before": "2026-12-31' OR '2'='2'",
            }

            # Should raise ValueError for invalid timestamp format
            with pytest.raises(
                ValueError, match="Invalid ISO timestamp format|Invalid time filter"
            ):
                result = daemon_instance._fts5_search(
                    query="test", limit=10, params=malicious_params
                )
