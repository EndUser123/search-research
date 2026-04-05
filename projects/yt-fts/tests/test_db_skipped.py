"""Tests for skipped module."""
import pytest,os,tempfile
from pathlib import Path

class TestIsChannelSkipped:
    def test_returns_true_for_skipped(self):
        from yt_fts.db.skipped import is_channel_skipped,add_skipped_channel
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            add_skipped_channel("https://youtu.be/test","channel_deleted_or_404")
            is_skipped,reason=is_channel_skipped("https://youtu.be/test")
            assert is_skipped is True
            assert reason=="channel_deleted_or_404"
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

    def test_returns_false_for_non_skipped(self):
        from yt_fts.db.skipped import is_channel_skipped
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            is_skipped,reason=is_channel_skipped("https://youtu.be/nosuch")
            assert is_skipped is False
            assert reason is None
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestAddSkippedChannel:
    def test_add_skipped_channel(self):
        from yt_fts.db.skipped import add_skipped_channel,is_channel_skipped
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            add_skipped_channel("https://url","deleted",fail_count=1)
            is_skipped,_=is_channel_skipped("https://url")
            assert is_skipped is True
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestRemoveSkippedChannel:
    def test_remove_skipped_channel(self):
        from yt_fts.db.skipped import add_skipped_channel,remove_skipped_channel,is_channel_skipped
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            add_skipped_channel("https://url","deleted")
            result=remove_skipped_channel("https://url")
            assert result is True
            is_skipped,_=is_channel_skipped("https://url")
            assert is_skipped is False
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

    def test_remove_nonexistent_returns_false(self):
        from yt_fts.db.skipped import remove_skipped_channel
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            result=remove_skipped_channel("nosuch")
            assert result is False
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestGetSkippedChannels:
    def test_get_skipped_channels(self):
        from yt_fts.db.skipped import add_skipped_channel,get_skipped_channels
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            add_skipped_channel("url1","deleted")
            add_skipped_channel("url2","invalid")
            channels=get_skipped_channels()
            assert len(channels)==2
            urls={c["channel_url"] for c in channels}
            assert "url1" in urls
            assert "url2" in urls
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestClearSkippedChannels:
    def test_clear_skipped_channels(self):
        from yt_fts.db.skipped import add_skipped_channel,clear_skipped_channels,get_skipped_channels
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            add_skipped_channel("url1","deleted")
            add_skipped_channel("url2","invalid")
            count=clear_skipped_channels()
            assert count==2
            assert len(get_skipped_channels())==0
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestShouldSkipPermanent:
    def test_404_returns_skip(self):
        from yt_fts.db.skipped import should_skip_permanent
        is_skip,reason=should_skip_permanent("HTTP Error 404: Not Found")
        assert is_skip is True
        assert reason=="channel_deleted_or_404"

    def test_400_returns_skip(self):
        from yt_fts.db.skipped import should_skip_permanent
        is_skip,reason=should_skip_permanent("HTTP Error 400: Bad Request")
        assert is_skip is True
        assert reason=="channel_invalid_format"

    def test_empty_returns_skip(self):
        from yt_fts.db.skipped import should_skip_permanent
        is_skip,reason=should_skip_permanent("No videos found for channel")
        assert is_skip is True
        assert reason=="channel_empty_no_videos"

    def test_private_returns_skip(self):
        from yt_fts.db.skipped import should_skip_permanent
        is_skip,reason=should_skip_permanent("Channel is private")
        assert is_skip is True
        assert reason=="channel_private"

    def test_transient_returns_no_skip(self):
        from yt_fts.db.skipped import should_skip_permanent
        is_skip,reason=should_skip_permanent("HTTP Error 500: Internal Server Error")
        assert is_skip is False
        assert reason is None

    def test_empty_msg_returns_no_skip(self):
        from yt_fts.db.skipped import should_skip_permanent
        is_skip,reason=should_skip_permanent("")
        assert is_skip is False
        assert reason is None

class TestMarkChannelInvalid:
    def test_mark_invalid(self):
        from yt_fts.db.skipped import mark_channel_invalid
        from yt_fts.db.infra import get_db_connection
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            with get_db_connection() as conn:
                conn.execute("INSERT INTO Channels (channel_id,channel_name,channel_url) VALUES (?,?,?)",("UC123","Test","url"))
                conn.commit()
            result=mark_channel_invalid("UC123")
            assert result is True
            with get_db_connection() as conn:
                r=conn.execute("SELECT is_valid FROM Channels WHERE channel_id=?",("UC123",)).fetchone()
            assert r[0]==0
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)
