"""Tests for search_history."""
import pytest, os, tempfile
from pathlib import Path

class TestSaveSearch:
    def test_save_search_creates_entry(self):
        from yt_fts.db.search_history import save_search
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            sid=save_search(query="test",scope="all",result_count=10,channel_id=None)
            assert sid>0
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

    def test_save_search_with_channel(self):
        from yt_fts.db.search_history import save_search
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            sid=save_search(query="test",scope="channel",result_count=5,channel_id="UC123")
            assert sid>0
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestGetSearchHistory:
    def test_get_history_returns_recent(self):
        from yt_fts.db.search_history import save_search,get_search_history
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            save_search("q1","all",10)
            save_search("q2","all",5)
            h=get_search_history(20)
            assert len(h)==2
            assert h[0]["query"]=="q2"
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestSaveQuery:
    def test_save_query_creates(self):
        from yt_fts.db.search_history import save_query,get_saved_query_by_name
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            qid=save_query(name="Q",query="test",scope="all",channel_id=None)
            assert qid>0
            s=get_saved_query_by_name("Q")
            assert s is not None
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

    def test_save_query_updates(self):
        from yt_fts.db.search_history import save_query
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            qid1=save_query(name="Q",query="orig",scope="all")
            qid2=save_query(name="Q",query="upd",scope="channel")
            assert qid1==qid2
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestDeleteSavedQuery:
    def test_delete_exists(self):
        from yt_fts.db.search_history import save_query,delete_saved_query
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            save_query("D","q","all")
            r=delete_saved_query("D")
            assert r is True
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)

class TestClearSearchHistory:
    def test_clear_deletes_all(self):
        from yt_fts.db.search_history import save_search,clear_search_history,get_search_history
        tmpdir=tempfile.mkdtemp()
        try:
            test_db=Path(tmpdir)/"test.db"
            os.environ["YT_FTS_DB_PATH"]=str(test_db)
            from yt_fts.db.maintenance import make_db
            make_db(str(test_db))
            save_search("q1","all",10)
            save_search("q2","all",5)
            c=clear_search_history()
            assert c==2
            assert len(get_search_history())==0
        finally:
            import shutil;shutil.rmtree(tmpdir,ignore_errors=True)
