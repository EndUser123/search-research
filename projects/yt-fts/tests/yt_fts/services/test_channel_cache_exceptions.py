"""Characterization tests for DatabaseCache exception handling.

These tests CAPTURE CURRENT BEHAVIOR before refactoring the silent exception
swallowing in services/channel_cache.py.

Issue: All database errors caught with generic except Exception, no structured logging.
Lines: 213-215, 236-237, 247-248, 262-263, 281-283

Run with: pytest tests/yt_fts/services/test_channel_cache_exceptions.py -v
"""

import sqlite3
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from yt_fts.services.channel_cache import DatabaseCache, CacheEntry


class TestDatabaseCacheGetExceptionHandling:
    """Characterization tests for get() exception handling (line 213-215)."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        # Cleanup happens automatically

    @pytest.fixture
    def cache(self, temp_db_path):
        """Create DatabaseCache instance with temp database."""
        return DatabaseCache(db_path=temp_db_path)

    def test_get_returns_none_on_sqlite_error(self, cache):
        """Fixed: get() returns None and logs when SQLite raises an exception.

        Fixed behavior (line 215-216):
        - Catches specific sqlite3.DatabaseError and sqlite3.OperationalError
        - Logs with logger.exception() (structured logging with traceback)
        - Returns None (cache miss behavior)

        This is CORRECT because:
        - Structured logging enables debugging
        - Caller sees consistent behavior (None for cache miss or error)
        - No KeyError from broken show_message call
        - Traceback captured in logs for root cause analysis
        """
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("database is locked")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                # Fixed behavior returns None
                result = cache.get("test_key")
                assert result is None
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                # Check it logged with proper context
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache get error" in call_args[0]

    def test_get_logs_context_on_error(self, cache):
        """Fixed: get() logs with context (key) on exception."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("database is locked")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                result = cache.get("test_key")
                assert result is None
                # Verify logger.exception was called with key context
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache get error" in call_args[0]
                # Verify key parameter was passed
                assert "test_key" in mock_logger.exception.call_args[0][1]


class TestDatabaseCachePutExceptionHandling:
    """Characterization tests for put() exception handling (line 236-237)."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name

    @pytest.fixture
    def cache(self, temp_db_path):
        """Create DatabaseCache instance with temp database."""
        return DatabaseCache(db_path=temp_db_path)

    @pytest.fixture
    def test_entry(self):
        """Create test cache entry."""
        return CacheEntry(
            channel_id="UC123",
            channel_url="https://youtube.com/@test",
            channel_name="Test Channel",
            resolution_method="test",
            created_at="2024-01-01T00:00:00Z",
            last_accessed="2024-01-01T00:00:00Z",
            access_count=1,
            ttl_seconds=3600,
            metadata={}
        )

    def test_put_logs_and_continues_on_sqlite_error(self, cache, test_entry):
        """Fixed: put() logs error and continues when SQLite raises an exception.

        Fixed behavior (line 238-239):
        - Catches specific sqlite3.DatabaseError and sqlite3.OperationalError
        - Logs with logger.exception() (structured logging with traceback)
        - Returns None (no exception raised)

        This is CORRECT because:
        - Structured logging enables debugging
        - Cache degradation is graceful (DB errors don't crash app)
        - No KeyError from broken show_message call
        """
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("disk I/O error")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                # Fixed behavior: no exception, just logs and returns
                cache.put("test_key", test_entry)
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache put error" in call_args[0]

    def test_put_logs_context_on_error(self, cache, test_entry):
        """Fixed: put() logs with context (key) on exception."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("disk I/O error")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                cache.put("test_key", test_entry)
                # Verify logger.exception was called with key context
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache put error" in call_args[0]


class TestDatabaseCacheDeleteExceptionHandling:
    """Characterization tests for delete() exception handling (line 247-248)."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name

    @pytest.fixture
    def cache(self, temp_db_path):
        """Create DatabaseCache instance with temp database."""
        return DatabaseCache(db_path=temp_db_path)

    def test_delete_logs_and_continues_on_sqlite_error(self, cache):
        """Fixed: delete() logs error and continues when SQLite raises an exception.

        Fixed behavior (line 249-250):
        - Catches specific sqlite3.DatabaseError and sqlite3.OperationalError
        - Logs with logger.exception() (structured logging with traceback)
        - Returns None (no exception raised)

        This is CORRECT because:
        - Structured logging enables debugging
        - Graceful degradation (DB errors don't crash app)
        - No KeyError from broken show_message call
        """
        with patch("sqlite3.connect", side_effect=sqlite3.DatabaseError("corruption")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                # Fixed behavior: no exception, just logs and returns
                cache.delete("test_key")
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache delete error" in call_args[0]

    def test_delete_logs_context_on_error(self, cache):
        """Fixed: delete() logs with context (key) on exception."""
        with patch("sqlite3.connect", side_effect=sqlite3.DatabaseError("corruption")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                cache.delete("test_key")
                # Verify logger.exception was called with key context
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache delete error" in call_args[0]


class TestDatabaseCacheUpdateAccessExceptionHandling:
    """Characterization tests for _update_access() exception handling (line 262-263)."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name

    @pytest.fixture
    def cache(self, temp_db_path):
        """Create DatabaseCache instance with temp database."""
        return DatabaseCache(db_path=temp_db_path)

    def test_update_access_logs_and_continues_on_sqlite_error(self, cache):
        """Fixed: _update_access() logs error and continues when SQLite raises an exception.

        Fixed behavior (line 264-265):
        - Catches specific sqlite3.DatabaseError and sqlite3.OperationalError
        - Logs with logger.exception() (structured logging with traceback)
        - Returns None (no exception raised)

        This is CORRECT because:
        - Structured logging enables debugging
        - Graceful degradation (access tracking failure doesn't crash app)
        - No KeyError from broken show_message call
        """
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("timeout")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                # Fixed behavior: no exception, just logs and returns
                cache._update_access("test_key")
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache update error" in call_args[0]

    def test_update_access_logs_context_on_error(self, cache):
        """Fixed: _update_access() logs with context (key) on exception."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("timeout")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                cache._update_access("test_key")
                # Verify logger.exception was called with key context
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache update error" in call_args[0]


class TestDatabaseCacheCleanupExpiredExceptionHandling:
    """Characterization tests for cleanup_expired() exception handling (line 281-283)."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name

    @pytest.fixture
    def cache(self, temp_db_path):
        """Create DatabaseCache instance with temp database."""
        return DatabaseCache(db_path=temp_db_path)

    def test_cleanup_expired_returns_zero_on_sqlite_error(self, cache):
        """Fixed: cleanup_expired() returns 0 and logs when SQLite raises an exception.

        Fixed behavior (line 283-285):
        - Catches specific sqlite3.DatabaseError and sqlite3.OperationalError
        - Logs with logger.exception() (structured logging with traceback)
        - Returns 0 (no entries cleaned due to error)

        This is CORRECT because:
        - Structured logging enables debugging
        - Caller can distinguish 0 (error) from 0 (nothing to clean) via logs
        - No KeyError from broken show_message call
        """
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("database locked")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                # Fixed behavior: returns 0 on error
                result = cache.cleanup_expired()
                assert result == 0
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache cleanup error" in call_args[0]

    def test_cleanup_expired_logs_on_error(self, cache):
        """Fixed: cleanup_expired() logs with exception on SQLite error."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("database locked")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                result = cache.cleanup_expired()
                assert result == 0
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache cleanup error" in call_args[0]


class TestClearMethodExceptionHandling:
    """Characterization tests for clear() exception handling (line 293-294)."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name

    @pytest.fixture
    def cache(self, temp_db_path):
        """Create DatabaseCache instance with temp database."""
        return DatabaseCache(db_path=temp_db_path)

    def test_clear_logs_and_continues_on_sqlite_error(self, cache):
        """Fixed: clear() logs error and continues when SQLite raises an exception.

        Fixed behavior (line 295-296):
        - Catches specific sqlite3.DatabaseError and sqlite3.OperationalError
        - Logs with logger.exception() (structured logging with traceback)
        - Returns None (no exception raised)

        This is CORRECT because:
        - Structured logging enables debugging
        - Graceful degradation (DB errors don't crash app)
        - No KeyError from broken show_message call
        """
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("database locked")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                # Fixed behavior: no exception, just logs and returns
                cache.clear()
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache clear error" in call_args[0]

    def test_clear_logs_on_error(self, cache):
        """Fixed: clear() logs with exception on SQLite error."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("database locked")):
            with patch("yt_fts.services.channel_cache.logger") as mock_logger:
                cache.clear()
                # Verify logger.exception was called
                mock_logger.exception.assert_called_once()
                call_args = mock_logger.exception.call_args[0]
                assert "Database cache clear error" in call_args[0]
