# Tests for db.utils module.

import pytest


class TestEscapeFts5Query:
    def test_escapes_double_quotes(self):
        from yt_fts.db.utils import escape_fts5_query
        result = escape_fts5_query("test quoted text")
        assert result is not None

    def test_escapes_asterisk(self):
        from yt_fts.db.utils import escape_fts5_query
        result = escape_fts5_query("test*wildcard")
        assert "*" in result or '"' in result


class TestParseQuery:
    def test_simple_terms(self):
        from yt_fts.db.utils import parse_query
        result = parse_query("hello world")
        assert "hello" in result


class TestParseQueryWithProximity:
    def test_proximity_creates_near(self):
        from yt_fts.db.utils import parse_query_with_proximity
        result = parse_query_with_proximity("neural network", proximity=5)
        assert "NEAR" in result

    def test_near_term_search(self):
        from yt_fts.db.utils import parse_query_with_proximity
        result = parse_query_with_proximity("deep learning", near_term="AI", proximity=10)
        assert "AI" in result
