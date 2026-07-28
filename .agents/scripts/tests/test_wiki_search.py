#!/usr/bin/env python3
"""
Tests for wiki_search FTS5-only wrapper.

Locks in the FTS5 quoting behavior, implicit-AND semantics, add_document
safety (DELETE+INSERT), and the full CRUD lifecycle.
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wiki_search import WikiSearch, WikiSearchError, sanitize_fts5_query

import pytest


class TestSanitizeFts5Query:
    """Test the per-token FTS5 query quoting fix."""

    def test_empty_query(self):
        assert sanitize_fts5_query("") == '""'

    def test_whitespace_only(self):
        assert sanitize_fts5_query("   ") == '""'

    def test_single_token(self):
        result = sanitize_fts5_query("model")
        assert result == '"model"'

    def test_multi_token_implicit_and(self):
        """Multi-word queries should produce separate quoted tokens (implicit-AND)."""
        result = sanitize_fts5_query("model routing")
        assert result == '"model" "routing"'
        assert result != '"model routing"'

    def test_hyphenated_token_no_syntax_error(self):
        """Hyphenated tokens must not cause FTS5 syntax errors."""
        result = sanitize_fts5_query("build-vs-port")
        assert result == '"build-vs-port"'

    def test_colon_token(self):
        """Colons are FTS5 column filters — must be quoted."""
        result = sanitize_fts5_query("foo:bar")
        assert result == '"foo:bar"'

    def test_double_quotes_escaped(self):
        """Double quotes inside tokens must be doubled (FTS5 escape rule)."""
        result = sanitize_fts5_query('say"hello')
        assert result == '"say""hello"'

    def test_mixed_tokens(self):
        """Mix of normal, hyphenated, and colon tokens."""
        result = sanitize_fts5_query("model build-vs-port foo:bar")
        assert result == '"model" "build-vs-port" "foo:bar"'


class TestWikiSearchLive:
    """Live tests against the existing qmd.db (read-only)."""

    @pytest.fixture
    def ws(self):
        return WikiSearch(collection="wiki")

    def test_info_returns_counts(self, ws):
        """info() should return document_count > 0 for the wiki collection."""
        info = ws.info()
        assert info["name"] == "wiki"
        assert info["document_count"] > 0
        assert info["engine"] == "sqlite-fts5 (stdlib, no qmd)"

    def test_search_returns_results(self, ws):
        """A common query should return results."""
        results = ws.search("model routing", top_k=5)
        assert len(results) > 0
        assert "doc_id" in results[0]
        assert "score" in results[0]

    def test_search_hyphenated_no_error(self, ws):
        """Hyphenated query must not raise (the original bug)."""
        try:
            results = ws.search("build-vs-port", top_k=5)
        except WikiSearchError:
            pytest.fail("Hyphenated query raised WikiSearchError — quoting fix not working")

    def test_search_multi_word_implicit_and(self, ws):
        """Multi-word query should return non-adjacent matches (implicit-AND)."""
        results = ws.search("model routing", top_k=10)
        assert len(results) >= 2

    def test_search_top_k_respected(self, ws):
        """top_k should limit results."""
        results = ws.search("the", top_k=3)
        assert len(results) <= 3

    def test_search_exclude_doc_id(self, ws):
        """exclude_doc_id should filter out the specified document."""
        results_all = ws.search("model routing", top_k=10)
        if len(results_all) > 0:
            exclude_id = results_all[0]["doc_id"]
            results_excluded = ws.search("model routing", top_k=10, exclude_doc_id=exclude_id)
            excluded_ids = [r["doc_id"] for r in results_excluded]
            assert exclude_id not in excluded_ids

    def test_list_documents(self, ws):
        """list_documents should return paths."""
        docs = ws.list_documents()
        assert len(docs) > 0

    def test_get_document_existing(self, ws):
        """get_document should return metadata for an existing doc."""
        docs = ws.list_documents()
        if docs:
            doc = ws.get_document(docs[0])
            assert doc is not None
            assert "title" in doc

    def test_get_document_nonexistent(self, ws):
        """get_document should return None for a non-existent doc."""
        doc = ws.get_document("nonexistent-slug-12345")
        assert doc is None


class TestAddDocumentSafety:
    """Test add_document uses DELETE+INSERT (not INSERT OR REPLACE).

    These tests use a temporary database to avoid polluting the real wiki.
    """

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with qmd's schema (no triggers —
        add_document manages FTS directly, same as qmd's Python API)."""
        db_path = str(tmp_path / "test_wiki.db")
        conn = __import__("sqlite3").connect(db_path)
        conn.executescript("""
            CREATE TABLE content (
                hash TEXT PRIMARY KEY,
                doc TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                path TEXT NOT NULL,
                title TEXT NOT NULL,
                hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                metadata TEXT NOT NULL DEFAULT '{}',
                UNIQUE(collection, path)
            );
            CREATE VIRTUAL TABLE documents_fts USING fts5(
                filepath, title, body,
                tokenize='porter unicode61'
            );
        """)
        conn.commit()
        conn.close()
        return db_path

    @pytest.fixture
    def temp_md(self, tmp_path):
        """Create a temporary markdown file."""
        p = tmp_path / "test_doc.md"
        p.write_text("# Test Document\n\nThis is test content about model routing.", encoding="utf-8")
        return str(p)

    def test_add_then_search(self, temp_db, temp_md):
        """Document added should be findable by search."""
        ws = WikiSearch(collection="wiki", db_path=temp_db)
        ws.add_document("test-doc", temp_md)
        results = ws.search("model routing", top_k=5)
        assert len(results) > 0
        assert any(r["doc_id"] == "test-doc" for r in results)

    def test_add_replacement_no_orphans(self, temp_db, temp_md):
        """Replacing an existing document should not leave orphaned FTS rows."""
        import sqlite3
        ws = WikiSearch(collection="wiki", db_path=temp_db)
        ws.add_document("test-doc", temp_md)
        # Add again (replace)
        ws.add_document("test-doc", temp_md)
        # Check no orphaned FTS rows
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documents_fts")
        fts_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documents WHERE active=1")
        doc_count = cur.fetchone()[0]
        conn.close()
        assert fts_count == doc_count, f"FTS rows ({fts_count}) != docs ({doc_count}) — orphans!"

    def test_add_nonexistent_file(self, temp_db):
        """Adding a non-existent file should raise WikiSearchError."""
        ws = WikiSearch(collection="wiki", db_path=temp_db)
        with pytest.raises(WikiSearchError, match="not found"):
            ws.add_document("bad", "/nonexistent/path.md")

    def test_delete_document(self, temp_db, temp_md):
        """delete_document should remove from both tables."""
        import sqlite3
        ws = WikiSearch(collection="wiki", db_path=temp_db)
        ws.add_document("test-doc", temp_md)
        ws.delete_document("test-doc")
        # Verify gone
        assert ws.get_document("test-doc") is None

    def test_context_manager(self, temp_db):
        """WikiSearch should support context manager protocol."""
        with WikiSearch(collection="wiki", db_path=temp_db) as ws:
            info = ws.info()
            assert info is not None
        # Connection should be closed after context exit
        assert ws._conn is None


class TestCLIDefaults:
    """Test CLI default format is json (qmd compat)."""

    def test_default_format_is_json(self):
        """The search subparser should default to json format."""
        # Just verify the source code has default="json"
        import wiki_search
        import inspect
        src = inspect.getsource(wiki_search.main)
        assert 'default="json"' in src
