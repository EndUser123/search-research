# Tests for db.maintenance module.

import os
import tempfile
from pathlib import Path

import pytest


class TestMakeDb:
    def test_make_db_creates_tables(self):
        from yt_fts.db.maintenance import make_db
        from yt_fts.db.infra import get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            make_db(str(test_db))
            
            with get_db_connection() as conn:
                # Check that main tables exist
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                table_names = {t[0] for t in tables}
                
                assert "Channels" in table_names
                assert "Videos" in table_names
                assert "Subtitles" in table_names
                assert "SkippedChannels" in table_names
                assert "SearchHistory" in table_names
                assert "SavedQueries" in table_names
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestMigrateAddIsValidColumn:
    def test_adds_is_valid_column(self):
        from yt_fts.db.maintenance import migrate_add_is_valid_column
        from yt_fts.db.infra import get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            # The column should already exist from make_db
            result = migrate_add_is_valid_column()
            # Should return False because column already exists
            assert result is False
            
            # Verify column exists
            with get_db_connection() as conn:
                col_exists = conn.execute(
                    "SELECT COUNT(*) FROM pragma_table_info('Channels') WHERE name='is_valid'"
                ).fetchone()
                assert col_exists[0] > 0
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCleanupChannels:
    def test_cleanup_removes_skipped_channels(self):
        from yt_fts.db.maintenance import cleanup_channels
        from yt_fts.db.infra import get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            with get_db_connection() as conn:
                # Add a channel
                conn.execute(
                    "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                    ("UC_test", "Test Channel", "https://youtu.be/test")
                )
                # Add it to skipped
                conn.execute(
                    "INSERT INTO SkippedChannels (channel_url, skip_reason, fail_count, last_attempt) VALUES (?, ?, ?, ?)",
                    ("https://youtu.be/test", "deleted", 1, "2024-01-01")
                )
                conn.commit()
            
            result = cleanup_channels()
            
            # Should have removed the channel
            assert result["skipped_removed"] == 1
            assert result["total_channels_before"] >= 0
            assert result["total_channels_after"] < result["total_channels_before"]
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cleanup_with_no_skipped_channels(self):
        from yt_fts.db.maintenance import cleanup_channels
        from yt_fts.db.infra import get_db_connection
        
        tmpdir = tempfile.mkdtemp()
        try:
            test_db = Path(tmpdir) / "test.db"
            os.environ["YT_FTS_DB_PATH"] = str(test_db)
            
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            
            result = cleanup_channels()
            
            assert result["skipped_removed"] == 0
            assert result["total_channels_after"] == 0
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
