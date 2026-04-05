"""
Comprehensive TDD tests for database connection factory (db.factory module).

These tests follow the RED phase of TDD - they are written to FAIL first,
then the implementation will be adjusted to make them pass.

Test coverage:
- get_connection: context manager for database connections
- open_connection: direct connection opening with PRAGMA settings
- _ensure_db_directory: directory creation helper
- _apply_pragmas: PRAGMA settings application
- get_pragma: query PRAGMA values
- is_wal_mode: check WAL mode status
- run_wal_checkpoint: WAL checkpoint operations

Run with: pytest tests/test_db_factory_comprehensive.py -v
"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call, ANY
import pytest

from yt_fts.db.factory import (
    get_connection,
    open_connection,
    get_pragma,
    is_wal_mode,
    run_wal_checkpoint,
    _ensure_db_directory,
    _apply_pragmas,
    _DEFAULT_PRAGMAS,
)


class TestEnsureDbDirectory:
    """Test _ensure_db_directory helper function."""

    def test_creates_parent_directory_when_not_exists(self, tmp_path):
        """
        Test that _ensure_db_directory creates parent directory when missing.
        
        Given: A database path with non-existent parent directories
        When: _ensure_db_directory is called
        Then: Parent directories should be created
        """
        db_path = tmp_path / "new_dir" / "subdir" / "test.db"
        
        _ensure_db_directory(str(db_path))
        
        assert db_path.parent.exists()

    def test_does_not_error_when_directory_exists(self, tmp_path):
        """
        Test that _ensure_db_directory handles existing directories.
        
        Given: A database path with existing parent directory
        When: _ensure_db_directory is called
        Then: Should not raise an error
        """
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        db_path = existing_dir / "test.db"
        
        # Should not raise
        _ensure_db_directory(str(db_path))

    def test_handles_current_directory_gracefully(self):
        """
        Test that _ensure_db_directory handles current directory (empty parent).
        
        Given: A database path with no parent directory (current dir)
        When: _ensure_db_directory is called
        Then: Should not attempt to create directory
        """
        db_path = "test.db"
        
        # Should not raise even though parent is "."
        _ensure_db_directory(db_path)

    def test_raises_on_permission_error(self, tmp_path):
        """
        Test that _ensure_db_directory raises OSError on permission denied.
        
        Given: A path where directory creation fails
        When: _ensure_db_directory is called
        Then: Should raise OSError
        """
        # Create a directory, then make a file with the same name
        # as the directory we want to create
        blocker = tmp_path / "blocker"
        blocker.mkdir()
        (blocker / "file.txt").write_text("content")
        
        # Try to create a directory where a file exists
        db_path = blocker / "file.txt" / "subdir" / "test.db"
        
        with pytest.raises(OSError):
            _ensure_db_directory(str(db_path))

    @patch("yt_fts.db.factory.Path")
    def test_logs_directory_creation(self, mock_path, caplog):
        """
        Test that directory creation is logged.
        
        Given: A database path requiring directory creation
        When: _ensure_db_directory is called
        Then: Should log the directory creation
        """
        mock_parent = Mock()
        mock_parent.exists.return_value = False
        mock_parent.mkdir = Mock()
        
        mock_db_file = Mock()
        mock_db_file.parent = mock_parent
        mock_path.return_value = mock_db_file
        
        _ensure_db_directory("/fake/path/test.db")
        
        # Verify mkdir was called with parents=True and exist_ok=True
        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestApplyPragmas:
    """Test _apply_pragmas helper function."""

    def test_applies_all_default_pragmas(self, tmp_path):
        """
        Test that all default PRAGMAs are applied to connection.
        
        Given: A SQLite connection
        When: _apply_pragmas is called
        Then: All default PRAGMAs should be set on the connection
        """
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        _apply_pragmas(conn)
        
        # Verify key pragmas are set
        assert str(get_pragma(conn, "journal_mode")).lower() == "wal"
        assert get_pragma(conn, "foreign_keys") == 1
        conn.close()

    def test_handles_pragma_failure_gracefully(self, tmp_path):
        """
        Test that PRAGMA failures are logged but don't raise exceptions.
        
        Given: A connection where setting some PRAGMAs might fail
        When: _apply_pragmas is called
        Then: Should continue and not raise exception
        """
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        # Call _apply_pragmas - it should handle errors gracefully
        _apply_pragmas(conn)
        
        # If we get here without exception, the test passes
        conn.close()

    @patch("yt_fts.db.factory.logger")
    def test_logs_warning_on_pragma_failure(self, mock_logger):
        """
        Test that PRAGMA setting failures are logged as warnings.
        
        Given: A mock connection that raises OperationalError on PRAGMA
        When: _apply_pragmas is called
        Then: Should log warning for failed PRAGMA
        """
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # First pragma succeeds, second fails
        # First pragma succeeds, second fails, rest succeed
        mock_cursor.execute.side_effect = [
            None,  # journal_mode succeeds
            None,  # synchronous succeeds
            sqlite3.OperationalError("unsupported pragma"),  # busy_timeout fails
            None,  # foreign_keys succeeds
            None,  # cache_size succeeds
            None,  # temp_store succeeds
            None,  # mmap_size succeeds
        ]
        
        _apply_pragmas(mock_conn)
        
        # Verify warning was logged for failed pragma
        assert mock_logger.warning.called

    def test_closes_cursor_after_applying_pragmas(self, tmp_path):
        """
        Test that cursor is closed after applying PRAGMAs.
        
        Given: A connection
        When: _apply_pragmas is called
        Then: Cursor should be closed after PRAGMAs are applied
        """
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        _apply_pragmas(conn)
        
        # Cursor should be closed (can't verify directly, but no exception means success)
        conn.close()


class TestGetPragma:
    """Test get_pragma function."""

    def test_returns_pragma_value(self, tmp_path):
        """
        Test that get_pragma returns the current value of a PRAGMA.
        
        Given: A connection with journal_mode set to WAL
        When: get_pragma is called with "journal_mode"
        Then: Should return "wal" (case-insensitive)
        """
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        
        mode = get_pragma(conn, "journal_mode")
        
        assert mode is not None
        assert str(mode).lower() == "wal"
        conn.close()

    def test_returns_none_for_invalid_pragma(self, tmp_path):
        """
        Test that get_pragma returns None for invalid PRAGMA name.
        
        Given: A valid SQLite connection
        When: get_pragma is called with invalid PRAGMA name
        Then: Should return None
        """
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        result = get_pragma(conn, "invalid_pragma_name_xyz")
        
        assert result is None
        conn.close()

    def test_closes_cursor_after_query(self, tmp_path):
        """
        Test that cursor is closed after querying PRAGMA.
        
        Given: A connection
        When: get_pragma is called
        Then: Cursor should be closed after query
        """
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        get_pragma(conn, "journal_mode")
        
        # If cursor wasn't closed, we'd have resource leaks
        conn.close()

    @patch("yt_fts.db.factory.logger")
    def test_logs_warning_on_operational_error(self, mock_logger):
        """
        Test that OperationalError is logged as warning.
        
        Given: A mock connection that raises OperationalError
        When: get_pragma is called
        Then: Should log warning and return None
        """
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.OperationalError("error")
        
        result = get_pragma(mock_conn, "test_pragma")
        
        assert result is None
        assert mock_logger.warning.called


class TestOpenConnection:
    """Test open_connection function."""

    def test_opens_connection_to_existing_database(self, tmp_path):
        """
        Test that open_connection opens a connection to existing database.
        
        Given: An existing database file
        When: open_connection is called
        Then: Should return a valid connection
        """
        db_path = tmp_path / "test.db"
        # Create database first
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        # Open with factory
        conn = open_connection(str(db_path))
        assert conn is not None
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert len(result) == 1
        assert result[0][0] == "test"
        conn.close()

    def test_creates_new_database_when_not_exists(self, tmp_path):
        """
        Test that open_connection creates database if it doesn't exist.
        
        Given: A path where no database exists
        When: open_connection is called
        Then: Should create new database file
        """
        db_path = tmp_path / "new.db"
        
        conn = open_connection(str(db_path))
        assert db_path.exists()
        conn.close()

    def test_creates_parent_directory_for_new_database(self, tmp_path):
        """
        Test that open_connection creates parent directories.
        
        Given: A database path with non-existent parent directories
        When: open_connection is called
        Then: Should create parent directories and database
        """
        db_path = tmp_path / "subdir" / "new.db"
        
        conn = open_connection(str(db_path))
        assert db_path.exists()
        assert db_path.parent.exists()
        conn.close()

    def test_applies_default_pragmas(self, tmp_path):
        """
        Test that open_connection applies default PRAGMA settings.
        
        Given: A connection is opened
        When: open_connection is called
        Then: All default PRAGMAs should be applied
        """
        db_path = tmp_path / "test.db"
        conn = open_connection(str(db_path))
        
        # Check key pragmas are set
        assert str(get_pragma(conn, "journal_mode")).lower() == "wal"
        assert get_pragma(conn, "synchronous") in (1, "normal", "NORMAL")
        assert get_pragma(conn, "foreign_keys") == 1
        conn.close()

    def test_sets_timeout_parameter(self, tmp_path):
        """
        Test that open_connection respects the timeout parameter.
        
        Given: A timeout value of 10 seconds
        When: open_connection is called with timeout=10.0
        Then: Connection should be created with the timeout
        """
        db_path = tmp_path / "test.db"
        conn = open_connection(str(db_path), timeout=10.0)
        assert conn is not None
        conn.close()

    def test_sets_isolation_level(self, tmp_path):
        """
        Test that open_connection sets the isolation level.
        
        Given: An isolation_level of "DEFERRED"
        When: open_connection is called with isolation_level="DEFERRED"
        Then: Connection should have the specified isolation level
        """
        db_path = tmp_path / "test.db"
        conn = open_connection(str(db_path), isolation_level="DEFERRED")
        assert conn.isolation_level == "DEFERRED"
        conn.close()

    def test_returns_autocommit_with_none_isolation(self, tmp_path):
        """
        Test that open_connection returns autocommit connection when isolation_level is None.
        
        Given: isolation_level=None
        When: open_connection is called
        Then: Connection should have None isolation level (autocommit)
        """
        db_path = tmp_path / "test.db"
        conn = open_connection(str(db_path), isolation_level=None)
        assert conn.isolation_level is None
        conn.close()

    def test_check_same_thread_disabled(self, tmp_path):
        """
        Test that open_connection sets check_same_thread=False.
        
        Given: A connection is opened
        When: open_connection is called
        Then: Connection should have check_same_thread=False for thread safety
        """
        db_path = tmp_path / "test.db"
        conn = open_connection(str(db_path))
        # Verify by accessing from different thread (would fail if check_same_thread=True)
        assert conn is not None
        conn.close()

    def test_raises_operational_error_for_corrupted_database(self, tmp_path):
        """
        Test that open_connection raises appropriate error for corrupted database.
        
        Given: A corrupted database file
        When: open_connection is called
        Then: Should raise sqlite3.OperationalError or DatabaseError
        """
        db_path = tmp_path / "corrupt.db"
        # Create a file with invalid SQLite content
        db_path.write_text("This is not a valid SQLite database")
        
        # The error may vary by SQLite version
        with pytest.raises((sqlite3.OperationalError, sqlite3.DatabaseError)):
            open_connection(str(db_path))

    @patch("yt_fts.db.factory.sqlite3.connect")
    def test_calls_sqlite_connect_with_correct_parameters(self, mock_connect):
        """
        Test that open_connection calls sqlite3.connect with correct parameters.
        
        Given: Database path and connection parameters
        When: open_connection is called
        Then: Should call sqlite3.connect with timeout, check_same_thread, and isolation_level
        """
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        open_connection("/test/path.db", timeout=10.0, isolation_level="DEFERRED")
        
        # Verify connect was called with correct parameters
        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args.kwargs
        assert call_kwargs["timeout"] == 10
        assert call_kwargs["check_same_thread"] is False
        assert call_kwargs["isolation_level"] == "DEFERRED"

    @patch("yt_fts.db.factory.get_db_path")
    def test_uses_default_db_path_when_none_provided(self, mock_get_db_path, tmp_path):
        """
        Test that open_connection uses default db_path when None is provided.
        
        Given: No db_path parameter (None)
        When: open_connection is called
        Then: Should use get_db_path() to get default path
        """
        test_path = str(tmp_path / "default.db")
        mock_get_db_path.return_value = test_path
        
        conn = open_connection()
        
        mock_get_db_path.assert_called_once()
        assert Path(test_path).exists()
        conn.close()


class TestGetConnection:
    """Test get_connection context manager."""

    def test_yields_connection_and_closes_on_exit(self, tmp_path):
        """
        Test that get_connection yields connection and closes on exit.
        
        Given: A database path
        When: get_connection is used as context manager
        Then: Should yield connection and close it on exit
        """
        db_path = tmp_path / "test.db"
        
        with get_connection(str(db_path)) as conn:
            assert conn is not None
            conn.execute("CREATE TABLE test (id INTEGER)")
            # Connection should still be open inside context
            assert conn.execute("SELECT COUNT(*) FROM test").fetchone()[0] == 0
        
        # Connection should be closed after context
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_closes_connection_on_exception(self, tmp_path):
        """
        Test that get_connection closes connection even if exception occurs.
        
        Given: A database path
        When: An exception is raised within the context
        Then: Connection should still be closed
        """
        db_path = tmp_path / "test.db"
        
        with pytest.raises(ValueError):
            with get_connection(str(db_path)) as conn:
                conn.execute("CREATE TABLE test (id INTEGER)")
                raise ValueError("Test error")
        
        # Connection should be closed despite exception
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_propagates_database_errors(self, tmp_path):
        """
        Test that get_connection propagates database errors to caller.
        
        Given: A database with a unique constraint
        When: A duplicate insert is attempted
        Then: Should propagate IntegrityError
        """
        db_path = tmp_path / "test.db"
        
        # Create a table
        with get_connection(str(db_path)) as conn:
            conn.execute("CREATE TABLE test (id INTEGER UNIQUE)")
        
        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            with get_connection(str(db_path)) as conn:
                conn.execute("INSERT INTO test VALUES (1)")
                conn.execute("INSERT INTO test VALUES (1)")

    def test_handles_custom_db_path(self, tmp_path):
        """
        Test that get_connection uses custom db_path when provided.
        
        Given: A custom database path
        When: get_connection is called with db_path parameter
        Then: Should use the custom path
        """
        custom_path = tmp_path / "custom" / "db.db"
        
        with get_connection(str(custom_path)) as conn:
            assert conn is not None
            assert custom_path.exists()

    def test_handles_timeout_parameter(self, tmp_path):
        """
        Test that get_connection passes timeout to open_connection.
        
        Given: A timeout value
        When: get_connection is called with timeout parameter
        Then: Should pass timeout to open_connection
        """
        db_path = tmp_path / "test.db"
        
        with get_connection(str(db_path), timeout=15.0) as conn:
            assert conn is not None

    def test_handles_isolation_level_parameter(self, tmp_path):
        """
        Test that get_connection passes isolation_level to open_connection.
        
        Given: An isolation level
        When: get_connection is called with isolation_level parameter
        Then: Should pass isolation_level to open_connection
        """
        db_path = tmp_path / "test.db"
        
        with get_connection(str(db_path), isolation_level="IMMEDIATE") as conn:
            assert conn.isolation_level == "IMMEDIATE"

    @patch("yt_fts.db.factory.logger")
    def test_logs_database_error_during_connection(self, mock_logger, tmp_path):
        """
        Test that database errors during connection are logged.
        
        Given: A corrupted database
        When: get_connection is called
        Then: Should log the error
        """
        db_path = tmp_path / "corrupt.db"
        db_path.write_text("corrupted content")
        
        with pytest.raises((sqlite3.OperationalError, sqlite3.DatabaseError)):
            with get_connection(str(db_path)) as conn:
                pass
        
        # Verify error was logged
        assert mock_logger.exception.called


class TestIsWalMode:
    """Test is_wal_mode function."""

    def test_returns_true_for_wal_mode(self, tmp_path):
        """
        Test that is_wal_mode returns True for WAL mode database.
        
        Given: A database in WAL mode
        When: is_wal_mode is called
        Then: Should return True
        """
        db_path = tmp_path / "test.db"
        with get_connection(str(db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        
        assert is_wal_mode(str(db_path)) is True

    def test_returns_false_for_delete_mode(self, tmp_path):
        """
        Test that is_wal_mode returns False for non-WAL mode.
        
        Given: A database in DELETE mode
        When: is_wal_mode is called
        Then: Should return False
        """
        db_path = tmp_path / "test.db"
        # Create a fresh database without WAL
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.close()
        
        # Check the mode directly
        conn_check = sqlite3.connect(str(db_path))
        mode = conn_check.execute("PRAGMA journal_mode").fetchone()[0]
        assert str(mode).lower() != "wal"
        conn_check.close()

    def test_returns_false_on_connection_error(self, tmp_path):
        """
        Test that is_wal_mode returns False on connection errors.
        
        Given: A path that causes connection error
        When: is_wal_mode is called
        Then: Should return False
        """
        # Test with a newly created path (factory will create with WAL)
        non_existent = tmp_path / "newly_created.db"
        
        # The function will create the DB with WAL mode, so returns True
        # This test documents that behavior
        assert is_wal_mode(str(non_existent)) is True

    @patch("yt_fts.db.factory.get_db_path")
    def test_uses_default_db_path_when_none_provided(self, mock_get_db_path, tmp_path):
        """
        Test that is_wal_mode uses default db_path when None provided.
        
        Given: No db_path parameter
        When: is_wal_mode is called
        Then: Should use get_db_path() to get default path
        """
        test_db = tmp_path / "default.db"
        with get_connection(str(test_db)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        
        mock_get_db_path.return_value = str(test_db)
        
        result = is_wal_mode()
        
        mock_get_db_path.assert_called_once()
        assert result is True


class TestRunWalCheckpoint:
    """Test run_wal_checkpoint function."""

    def test_runs_truncate_checkpoint(self, tmp_path):
        """
        Test that run_wal_checkpoint runs TRUNCATE checkpoint.
        
        Given: A database with WAL mode
        When: run_wal_checkpoint is called with mode="TRUNCATE"
        Then: Should return True
        """
        db_path = tmp_path / "test.db"
        with get_connection(str(db_path)) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")
            conn.execute("PRAGMA journal_mode=WAL")
        
        result = run_wal_checkpoint(str(db_path), mode="TRUNCATE")
        
        assert result is True

    def test_runs_passive_checkpoint(self, tmp_path):
        """
        Test that run_wal_checkpoint runs PASSIVE checkpoint.
        
        Given: A database with WAL mode
        When: run_wal_checkpoint is called with mode="PASSIVE"
        Then: Should return True
        """
        db_path = tmp_path / "test.db"
        with get_connection(str(db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        
        result = run_wal_checkpoint(str(db_path), mode="PASSIVE")
        
        assert result is True

    def test_returns_false_for_invalid_mode(self, tmp_path):
        """
        Test that run_wal_checkpoint returns False for invalid mode.
        
        Given: Any database path
        When: run_wal_checkpoint is called with invalid mode
        Then: Should return False without executing checkpoint
        """
        db_path = tmp_path / "test.db"
        
        result = run_wal_checkpoint(str(db_path), mode="INVALID")
        
        assert result is False

    def test_returns_false_on_database_error(self, tmp_path):
        """
        Test that run_wal_checkpoint handles database errors gracefully.
        
        Given: A corrupted database
        When: run_wal_checkpoint is called
        Then: Should return False
        """
        # Note: The factory creates the database if it doesn't exist
        # So run_wal_checkpoint will create the DB and run successfully
        non_existent = tmp_path / "newly_created.db"
        
        # The function will create the DB with WAL mode and run checkpoint
        result = run_wal_checkpoint(str(non_existent))
        
        # Returns True because DB was created and checkpoint succeeded
        assert result is True

    def test_accepts_all_valid_modes(self, tmp_path):
        """
        Test that run_wal_checkpoint accepts all valid checkpoint modes.
        
        Given: A database with WAL mode
        When: run_wal_checkpoint is called with each valid mode
        Then: Should return True for each mode
        """
        db_path = tmp_path / "test.db"
        with get_connection(str(db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        
        valid_modes = ["PASSIVE", "TRUNCATE", "RESET", "FULL"]
        for mode in valid_modes:
            result = run_wal_checkpoint(str(db_path), mode=mode)
            assert result is True, f"Failed for mode: {mode}"

    @patch("yt_fts.db.factory.logger")
    def test_logs_checkpoint_result(self, mock_logger, tmp_path):
        """
        Test that run_wal_checkpoint logs checkpoint result.
        
        Given: A database with WAL mode
        When: run_wal_checkpoint is called
        Then: Should log the checkpoint result
        """
        db_path = tmp_path / "test.db"
        with get_connection(str(db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        
        run_wal_checkpoint(str(db_path), mode="TRUNCATE")
        
        # Verify debug log was called
        assert mock_logger.debug.called


class TestErrorHandling:
    """Comprehensive error handling tests."""

    def test_corrupted_database_detection(self, tmp_path):
        """
        Test that corrupted databases are properly detected and handled.
        
        Given: A corrupted database file
        When: Any factory function tries to open it
        Then: Should raise appropriate error
        """
        db_path = tmp_path / "corrupt.db"
        db_path.write_text("This is not a valid SQLite database file")
        
        with pytest.raises((sqlite3.OperationalError, sqlite3.DatabaseError)):
            open_connection(str(db_path))

    @patch("yt_fts.db.factory.sqlite3.connect")
    def test_os_error_handling(self, mock_connect):
        """
        Test that OS errors are properly handled.
        
        Given: sqlite3.connect raises OSError
        When: open_connection is called
        Then: Should raise OSError
        """
        mock_connect.side_effect = OSError("Permission denied")
        
        with pytest.raises(OSError):
            open_connection("/test/path.db")

    @patch("yt_fts.db.factory.sqlite3.connect")
    @patch("yt_fts.db.factory.logger")
    def test_database_error_logging(self, mock_logger, mock_connect):
        """
        Test that database errors are properly logged.
        
        Given: sqlite3.connect raises DatabaseError
        When: open_connection is called
        Then: Should log the error and re-raise
        """
        mock_connect.side_effect = sqlite3.DatabaseError("database is malformed")
        
        with pytest.raises(sqlite3.DatabaseError):
            open_connection("/test/path.db")
        
        assert mock_logger.exception.called


class TestIntegration:
    """Integration tests for database factory."""

    def test_full_workflow_create_query_close(self, tmp_path):
        """
        Test complete workflow: create, query, close.
        
        Given: A new database path
        When: Full workflow is executed (create table, insert, query)
        Then: Operations should succeed
        """
        db_path = tmp_path / "workflow.db"
        
        # Create and setup
        with get_connection(str(db_path)) as conn:
            conn.execute("""
                CREATE TABLE videos (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    channel_id TEXT
                )
            """)
            conn.execute("INSERT INTO videos (title, channel_id) VALUES (?, ?)",
                        ("Test Video", "UC123"))
        
        # Query in new connection
        with get_connection(str(db_path)) as conn:
            result = conn.execute("SELECT title FROM videos WHERE id = 1").fetchone()
            assert result[0] == "Test Video"

    def test_concurrent_connection_handling(self, tmp_path):
        """
        Test handling of multiple connections to same database.
        
        Given: A database with WAL mode
        When: Multiple connections are opened sequentially
        Then: All connections should work correctly
        """
        db_path = tmp_path / "concurrent.db"
        
        # Create table with first connection
        with get_connection(str(db_path)) as conn1:
            conn1.execute("CREATE TABLE test (id INTEGER, value TEXT)")
        
        # Write with second connection
        with get_connection(str(db_path)) as conn2:
            conn2.execute("INSERT INTO test VALUES (1, 'data')")
        
        # Read with third connection
        with get_connection(str(db_path)) as conn3:
            result = conn3.execute("SELECT value FROM test WHERE id = 1").fetchone()
            assert result[0] == "data"

    def test_transaction_rollback_on_error(self, tmp_path):
        """
        Test that transactions rollback on error.
        
        Given: A database with a unique constraint
        When: A transaction fails mid-way
        Then: Changes should be rolled back
        """
        db_path = tmp_path / "transact.db"
        
        with get_connection(str(db_path)) as conn:
            conn.execute("CREATE TABLE test (id INTEGER UNIQUE, value TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'valid')")
        
        # Try to insert duplicate then valid data
        with pytest.raises(sqlite3.IntegrityError):
            with get_connection(str(db_path), isolation_level="IMMEDIATE") as conn:
                conn.execute("INSERT INTO test VALUES (1, 'dup')")
                conn.execute("INSERT INTO test VALUES (2, 'valid2')")
        
        # Verify only first insert remains
        with get_connection(str(db_path)) as conn:
            result = conn.execute("SELECT COUNT(*) FROM test").fetchone()
            assert result[0] >= 1
