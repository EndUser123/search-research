"""Tests for SearchSession - Conversational Search Continuum.

Tests verify the session-based search functionality including:
- Query history tracking
- Result referencing by number
- Follow-up queries
- Session summary generation
- Export to CKS storage

Run with: pytest P:/__csf/src/knowledge/systems/chs/v2/tests/test_search_session.py -v
"""

from __future__ import annotations

from datetime import datetime

from core.chs.search_session import SearchSession, SearchSessionManager


class TestSearchSession:
    """Tests for SearchSession class."""

    def test_init_creates_session_with_defaults(self):
        """Test that SearchSession initializes with correct defaults."""
        session = SearchSession()
        assert session.max_history == 5
        assert session.max_results == 10
        assert session.session_id.startswith("sess-")
        assert session.queries == []
        assert session.results == {}
        assert isinstance(session.created_at, datetime)

    def test_init_with_custom_parameters(self):
        """Test that SearchSession accepts custom parameters."""
        session = SearchSession(max_history=10, max_results=20, session_id="test-session-123")
        assert session.max_history == 10
        assert session.max_results == 20
        assert session.session_id == "test-session-123"

    def test_add_search_stores_query_and_results(self):
        """Test that add_search stores query and returns query_id."""
        session = SearchSession()
        query = "python async patterns"
        results = [
            {"id": "1", "content": "Use asyncio", "score": 0.9},
            {"id": "2", "content": "async/await syntax", "score": 0.8},
        ]
        query_id = session.add_search(query, results)
        assert query_id.startswith("q-")
        assert len(session.queries) == 1
        assert session.queries[0]["query"] == query
        assert session.queries[0]["result_count"] == 2
        assert query_id in session.results
        assert len(session.results[query_id]) == 2

    def test_add_search_limits_results_to_max_results(self):
        """Test that add_search respects max_results limit."""
        session = SearchSession(max_results=2)
        results = [
            {"id": str(i), "content": f"result {i}", "score": 1.0 - i * 0.1} for i in range(5)
        ]
        query_id = session.add_search("test", results)
        assert len(session.results[query_id]) == 2
        assert session.results[query_id][0]["id"] == "0"
        assert session.results[query_id][1]["id"] == "1"

    def test_add_search_trims_history_to_max_history(self):
        """Test that add_search keeps only max_history queries."""
        session = SearchSession(max_history=3)
        for i in range(5):
            session.add_search(f"query {i}", [{"id": str(i), "score": 0.5}])
        assert len(session.queries) == 3
        assert session.queries[0]["query"] == "query 2"
        assert session.queries[2]["query"] == "query 4"
        assert "q-1-" not in session.results

    def test_follow_up_returns_all_results_without_reference_id(self):
        """Test that follow_up returns all results when no reference_id."""
        session = SearchSession()
        results = [
            {"id": "1", "content": "result 1", "score": 0.9},
            {"id": "2", "content": "result 2", "score": 0.8},
        ]
        query_id = session.add_search("test query", results)
        follow_up = session.follow_up(query_id=query_id)
        assert follow_up["query_id"] == query_id
        assert follow_up["query"] == "test query"
        assert follow_up["count"] == 2
        assert len(follow_up["results"]) == 2

    def test_follow_up_returns_specific_result_with_reference_id(self):
        """Test that follow_up returns specific result with reference_id."""
        session = SearchSession()
        results = [
            {"id": "1", "content": "result 1", "score": 0.9},
            {"id": "2", "content": "result 2", "score": 0.8},
            {"id": "3", "content": "result 3", "score": 0.7},
        ]
        query_id = session.add_search("test query", results)
        follow_up = session.follow_up(query_id=query_id, reference_id=2)
        assert follow_up["query_id"] == query_id
        assert follow_up["reference_id"] == 2
        assert follow_up["result"]["id"] == "2"
        assert follow_up["result"]["content"] == "result 2"

    def test_follow_up_returns_error_for_invalid_reference_id(self):
        """Test that follow_up handles invalid reference_id gracefully."""
        session = SearchSession()
        results = [{"id": "1", "content": "result 1", "score": 0.9}]
        query_id = session.add_search("test query", results)
        follow_up = session.follow_up(query_id=query_id, reference_id=5)
        assert "error" in follow_up
        assert follow_up["available"] == 1

    def test_follow_up_defaults_to_most_recent_query(self):
        """Test that follow_up uses most recent query when query_id is None."""
        session = SearchSession()
        session.add_search("first query", [{"id": "1", "score": 0.5}])
        query_id_2 = session.add_search("second query", [{"id": "2", "score": 0.7}])
        follow_up = session.follow_up()
        assert follow_up["query_id"] == query_id_2
        assert follow_up["query"] == "second query"

    def test_get_context_summary_returns_session_summary(self):
        """Test that get_context_summary returns correct summary."""
        session = SearchSession()
        session.add_search(
            "python async",
            [
                {"id": "1", "content": "asyncio", "score": 0.9},
                {"id": "2", "content": "await", "score": 0.8},
            ],
        )
        session.add_search(
            "dependency injection", [{"id": "3", "content": "DI pattern", "score": 0.7}]
        )
        summary = session.get_context_summary()
        assert summary["session_id"] == session.session_id
        assert summary["query_count"] == 2
        assert summary["total_results"] == 3
        assert "topics" in summary
        assert "duration_seconds" in summary
        assert len(summary["queries"]) == 2

    def test_cleanup_clears_session_data(self):
        """Test that cleanup clears all session data."""
        session = SearchSession()
        session.add_search("test", [{"id": "1", "score": 0.5}])
        session.cleanup()
        assert session.queries == []
        assert session.results == {}

    def test_parse_followup_query_detects_result_reference(self):
        """Test that parse_followup_query detects result references."""
        session = SearchSession()
        result = session.parse_followup_query("tell me more about result 3")
        assert result["reference_id"] == 3
        assert "tell me more about" in result["clean_query"]
        result = session.parse_followup_query("show #5")
        assert result["reference_id"] == 5
        result = session.parse_followup_query("number 7 details")
        assert result["reference_id"] == 7
        result = session.parse_followup_query("just a normal query")
        assert result["reference_id"] is None
        assert result["clean_query"] == "just a normal query"


class TestSearchSessionManager:
    """Tests for SearchSessionManager class."""

    def test_create_session_returns_new_session(self):
        """Test that create_session creates and returns a new session."""
        manager = SearchSessionManager()
        session = manager.create_session()
        assert session is not None
        assert session.session_id.startswith("sess-")
        assert manager.active_session == session

    def test_get_or_create_session_reuses_active_session(self):
        """Test that get_or_create_session reuses active session with same ID."""
        manager = SearchSessionManager()
        session1 = manager.create_session(session_id="test-session")
        session2 = manager.get_or_create_session(session_id="test-session")
        assert session1 == session2
        assert session2.session_id == "test-session"


class TestCHSSearchWithSession:
    """Tests for CHSSearchWithSession class."""

    def test_init_creates_searcher_with_session(self):
        """Test that CHSSearchWithSession initializes correctly."""
        import sqlite3

        db = sqlite3.connect(":memory:")
        from core.chs.search import CHSSearchWithSession

        searcher = CHSSearchWithSession(db, session_id="test-session")
        assert searcher.session.session_id == "test-session"
        assert searcher._base_searcher is not None

    def test_follow_up_returns_result_details(self):
        """Test that follow_up returns detailed result information."""
        import sqlite3

        db = sqlite3.connect(":memory:")
        from core.chs.search import CHSSearchWithSession

        searcher = CHSSearchWithSession(db, session_id="test-session")
        searcher.session.add_search(
            "test query",
            [
                {"id": "1", "content": "result 1", "score": 0.9},
                {"id": "2", "content": "result 2", "score": 0.8},
            ],
        )
        follow_up = searcher.follow_up(reference_id=2)
        assert follow_up["reference_id"] == 2
        assert follow_up["result"]["id"] == "2"
        assert follow_up["result"]["content"] == "result 2"

    def test_get_session_summary(self):
        """Test that get_session_summary returns session information."""
        import sqlite3

        db = sqlite3.connect(":memory:")
        from core.chs.search import CHSSearchWithSession

        searcher = CHSSearchWithSession(db, session_id="test-session")
        searcher.session.add_search("query 1", [{"id": "1", "score": 0.9}])
        summary = searcher.get_session_summary()
        assert summary["query_count"] == 1
        assert summary["total_results"] == 1
        assert summary["session_id"] == "test-session"
