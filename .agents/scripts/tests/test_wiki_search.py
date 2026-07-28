#!/usr/bin/env python3
"""
Tests for wiki_search FTS5-only wrapper.

Locks in the FTS5 quoting behavior and implicit-AND semantics.
These tests do NOT import qmd — they test the wrapper directly.
"""

import sys
from pathlib import Path

# Add parent to path so we can import wiki_search
sys.path.insert(0, str(Path(__file__).parent.parent))

from wiki_search import WikiSearch, WikiSearchError, _sanitize_fts5_query

import pytest


class TestSanitizeFts5Query:
    """Test the per-token FTS5 query quoting fix."""

    def test_empty_query(self):
        assert _sanitize_fts5_query("") == '""'

    def test_whitespace_only(self):
        assert _sanitize_fts5_query("   ") == '""'

    def test_single_token(self):
        result = _sanitize_fts5_query("model")
        assert result == '"model"'

    def test_multi_token_implicit_and(self):
        """Multi-word queries should produce separate quoted tokens (implicit-AND)."""
        result = _sanitize_fts5_query("model routing")
        assert result == '"model" "routing"'
        # NOT a phrase query (which would be "model routing" as one quote)
        assert result != '"model routing"'

    def test_hyphenated_token_no_syntax_error(self):
        """Hyphenated tokens must not cause FTS5 syntax errors.

        Without quoting, FTS5 interprets - as NOT operator.
        With quoting, it becomes a phrase query (no error).
        """
        result = _sanitize_fts5_query("build-vs-port")
        assert result == '"build-vs-port"'
        # The key property: no bare hyphens that FTS5 would interpret as operators
        # The entire token is wrapped in quotes, disarming the hyphen

    def test_colon_token(self):
        """Colons are FTS5 column filters — must be quoted."""
        result = _sanitize_fts5_query("foo:bar")
        assert result == '"foo:bar"'

    def test_double_quotes_escaped(self):
        """Double quotes inside tokens must be doubled (FTS5 escape rule)."""
        result = _sanitize_fts5_query('say"hello')
        assert result == '"say""hello"'

    def test_mixed_tokens(self):
        """Mix of normal, hyphenated, and colon tokens."""
        result = _sanitize_fts5_query("model build-vs-port foo:bar")
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
        """Hyphenated query must not raise (the original bug).

        May return 0 results if no document has the phrase — the key is
        no FTS5 syntax error.
        """
        try:
            results = ws.search("build-vs-port", top_k=5)
            # 0 results is acceptable — no document may contain this exact phrase
            # The test passes as long as no exception is raised
        except WikiSearchError:
            pytest.fail("Hyphenated query raised WikiSearchError — quoting fix not working")

    def test_search_multi_word_implicit_and(self, ws):
        """Multi-word query should return non-adjacent matches (implicit-AND).

        If implicit-AND is broken into a phrase query, only documents with
        the exact adjacent phrase would match — significantly fewer results.
        """
        results = ws.search("model routing", top_k=10)
        # With implicit-AND, we expect multiple results (model AND routing anywhere)
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
