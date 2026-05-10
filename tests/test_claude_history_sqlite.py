"""Test direct SQLite search in ClaudeHistoryBackend."""

import pytest

from core.backends.local import ClaudeHistoryBackend


class TestSQLiteDirectSearch:
    """Test direct SQLite search functionality."""

    def test_search_sqlite_direct_returns_results(self, db_backend):
        """Direct SQLite search should return results for valid query."""
        results = db_backend._search_sqlite_direct("test", limit=5)

        # Results should be a list
        assert isinstance(results, list)

        # Each result should have expected keys
        for result in results:
            assert "title" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result

    def test_search_sqlite_direct_empty_query(self, db_backend):
        """Direct SQLite search should handle empty query gracefully."""
        results = db_backend._search_sqlite_direct("", limit=5)

        # Should return empty list for empty query
        assert results == []

    def test_search_sqlite_direct_limit(self, db_backend):
        """Direct SQLite search should respect limit parameter."""
        results = db_backend._search_sqlite_direct("test", limit=2)

        # Should not return more than limit
        assert len(results) <= 2

    def test_search_sqlite_direct_no_database(self, tmp_path):
        """Direct SQLite search should handle missing database gracefully."""
        # Create backend with non-existent database path
        backend = ClaudeHistoryBackend(
            db_path=str(tmp_path / "nonexistent.db"),
            cli_path="dummy.exe",  # Not used for SQLite search
        )

        # Should return empty list, not raise exception
        results = backend._search_sqlite_direct("test", limit=5)
        assert results == []

    def test_search_routes_to_sqlite_when_db_source(self, db_backend):
        """search() should use direct SQLite when source='db'."""
        # This should not raise an error even if CLI doesn't exist
        results = db_backend.search("test", limit=5, source="db")

        # Results should be a list
        assert isinstance(results, list)

    def test_search_result_format_consistency(self, db_backend):
        """Direct SQLite results should match expected format."""
        results = db_backend._search_sqlite_direct("test", limit=1)

        for result in results:
            # Check title format
            assert isinstance(result["title"], str)

            # Check content exists
            assert isinstance(result["content"], str)

            # Check score is numeric
            assert isinstance(result["score"], (int, float))

            # Check metadata structure
            metadata = result["metadata"]
            assert isinstance(metadata, dict)


@pytest.fixture
def db_backend():
    """Create ClaudeHistoryBackend with real database path."""
    return ClaudeHistoryBackend(
        db_path="P:\\\\\\__csf/data/chat_history.db",
        cli_path="P:\\\\\\packages/claude-history/target/release/claude-history.exe",
    )
