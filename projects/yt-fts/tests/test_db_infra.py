# Tests for db.infra module.

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest


class TestGetDbConnection:
    def test_returns_connection(self):
        from yt_fts.db.infra import get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            conn = get_db_connection()
            
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
            conn.close()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_connection_has_row_factory(self):
        from yt_fts.db.infra import get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            conn = get_db_connection()
            
            assert conn.row_factory is not None
            conn.close()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestBatchCommitManager:
    def test_context_manager(self):
        from yt_fts.db.infra import BatchCommitManager
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            with BatchCommitManager() as manager:
                assert manager is not None
                assert manager.conn is not None
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_record_insert(self):
        from yt_fts.db.infra import BatchCommitManager
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            with BatchCommitManager(commit_interval=5) as manager:
                assert manager.pending_count == 0
                manager.record_insert()
                manager.record_insert()
                assert manager.pending_count == 2
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_flush_on_interval(self):
        from yt_fts.db.infra import BatchCommitManager, get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            with BatchCommitManager(commit_interval=3) as manager:
                # Access manager.conn to ensure connection is created
                # This is required for flush() to work
                _ = manager.conn
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                        ("UC_test", "Test", "url")
                    )
                    manager.record_insert()
                    manager.record_insert()
                    manager.record_insert()
                    # Should have flushed at 3
                    assert manager.pending_count == 0
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestEnableWalMode:
    def test_enable_wal_mode(self):
        from yt_fts.db.infra import enable_wal_mode
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            # This should not raise an error
            enable_wal_mode()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestEnsureDbIndexes:
    def test_ensure_indexes(self):
        from yt_fts.db.infra import ensure_db_indexes
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            # Should not raise error
            ensure_db_indexes()
            
            # Running again should be idempotent
            ensure_db_indexes()
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestRetryOnLocked:
    def test_retry_decorator(self):
        from yt_fts.db.infra import retry_on_locked
        
        call_count = 0
        
        @retry_on_locked(max_retries=3)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("database is locked")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_gives_up_after_max_retries(self):
        from yt_fts.db.infra import retry_on_locked
        
        @retry_on_locked(max_retries=2)
        def always_failing_function():
            raise Exception("database is locked")
        
        with pytest.raises(Exception, match="database is locked"):
            always_failing_function()
