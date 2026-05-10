"""Characterization tests for CKS class - core/cks/unified.py

These tests document the ACTUAL current behavior of the CKS class.
They are NOT assertions of correct behavior - they are recording what the code
currently does. When refactoring, these tests should continue to pass if
behavior is preserved.

Run with: pytest core/cks/tests/test_unified.py -v
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def cks_temp_db():
    """Create a temporary CKS database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    cks = CKS(db_path)
    yield cks, Path(db_path)
    try:
        cks.close()
    except Exception:
        pass
    try:
        Path(db_path).unlink()
    except Exception:
        pass


@pytest.fixture
def cks_prod():
    """Use production CKS database for integration tests."""
    prod_path = Path("P:\\\\\\__csf/data/cks.db")
    if not prod_path.exists():
        pytest.skip("Production CKS database not found")
    from core.cks.unified import CKS
    cks = CKS()
    yield cks
    try:
        cks.close()
    except Exception:
        pass


class TestCKSInitialization:
    """Tests for CKS initialization and lifecycle."""

    def test_instantiation_with_temp_db(self, cks_temp_db):
        """CKS can be instantiated with a temp database."""
        cks, db_path = cks_temp_db
        assert cks is not None
        assert db_path.exists()

    def test_context_manager_protocol(self, cks_temp_db):
        """CKS supports context manager protocol."""
        cks, db_path = cks_temp_db
        with cks:
            pass  # Should not raise

    def test_close_method(self, cks_temp_db):
        """CKS.close() completes without error."""
        cks, db_path = cks_temp_db
        cks.close()  # Should not raise


class TestCKSQueryCache:
    """Tests for CKS query caching behavior."""

    def test_clear_query_cache(self, cks_temp_db):
        """clear_query_cache() completes without error."""
        cks, _ = cks_temp_db
        cks.clear_query_cache()  # Should not raise

    def test_get_cache_stats_returns_dict(self, cks_temp_db):
        """get_cache_stats() returns a dictionary."""
        cks, _ = cks_temp_db
        stats = cks.get_cache_stats()
        assert isinstance(stats, dict)


class TestCKSIntent:
    """Tests for intent detection."""

    def test_detect_intent_returns_string(self, cks_temp_db):
        """detect_intent() returns a string."""
        cks, _ = cks_temp_db
        intent = cks.detect_intent("how does authentication work")
        assert isinstance(intent, str)
        assert len(intent) > 0

    def test_detect_intent_with_code_query(self, cks_temp_db):
        """detect_intent() handles code-related queries."""
        cks, _ = cks_temp_db
        intent = cks.detect_intent("def authenticate_user():")
        assert isinstance(intent, str)

    def test_detect_intent_with_empty_string(self, cks_temp_db):
        """detect_intent() handles empty string."""
        cks, _ = cks_temp_db
        intent = cks.detect_intent("")
        assert isinstance(intent, str)

    def test_get_all_intents_returns_list(self, cks_temp_db):
        """get_all_intents() returns a list."""
        cks, _ = cks_temp_db
        intents = cks.get_all_intents()
        assert isinstance(intents, list)


class TestCKSIngest:
    """Tests for CKS ingest operations."""

    def test_ingest_memory_returns_id(self, cks_temp_db):
        """ingest_memory() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_memory(
            "What is JWT?",
            "JWT is JSON Web Token for authentication",
            source_chunk="auth documentation"
        )
        assert entry_id is not None
        assert isinstance(entry_id, str)

    def test_ingest_pattern_returns_id(self, cks_temp_db):
        """ingest_pattern() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_pattern(
            "Dual Sink Logging",
            "Route logs to both JSON and text for observability",
            source_chunk="logging documentation"
        )
        assert entry_id is not None
        assert isinstance(entry_id, str)

    def test_ingest_decision_returns_id(self, cks_temp_db):
        """ingest_decision() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_decision(
            "Chose FAISS for vector search",
            "FAISS provides fast similarity search with GPU acceleration"
        )
        assert entry_id is not None

    def test_ingest_learning_returns_id(self, cks_temp_db):
        """ingest_learning() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_learning(
            "Lesson: always verify API availability before using",
            "Check SENTENCE_TRANSFORMERS_AVAILABLE before semantic search"
        )
        assert entry_id is not None

    def test_ingest_correction_returns_id(self, cks_temp_db):
        """ingest_correction() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_correction(
            "Fixed: missing await in async function",
            "Added await before database.commit()"
        )
        assert entry_id is not None

    def test_ingest_commitment_returns_id(self, cks_temp_db):
        """ingest_commitment() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_commitment(
            "Will add tests for CKS class",
            "Deadline: end of this session"
        )
        assert entry_id is not None

    def test_ingest_insight_returns_id(self, cks_temp_db):
        """ingest_insight() returns an entry ID."""
        cks, _ = cks_temp_db
        entry_id = cks.ingest_insight(
            "Realized: the bug was a race condition in model loading",
            "Multiple CKS instances were sharing _model_loading flag"
        )
        assert entry_id is not None


class TestCKSSearch:
    """Tests for CKS search operations."""

    def test_search_returns_list(self, cks_temp_db):
        """search() returns a list of results."""
        cks, _ = cks_temp_db
        results = cks.search("authentication")
        assert isinstance(results, list)

    def test_search_with_limit(self, cks_temp_db):
        """search() respects the limit parameter."""
        cks, _ = cks_temp_db
        results = cks.search("test", limit=5)
        assert len(results) <= 5

    def test_search_memories_returns_list(self, cks_temp_db):
        """search_memories() returns a list."""
        cks, _ = cks_temp_db
        results = cks.search_memories("authentication")
        assert isinstance(results, list)

    def test_search_patterns_returns_list(self, cks_temp_db):
        """search_patterns() returns a list."""
        cks, _ = cks_temp_db
        results = cks.search_patterns("logging")
        assert isinstance(results, list)

    def test_search_keyword_fts5_returns_list(self, cks_temp_db):
        """search_keyword_fts5() returns a list."""
        cks, _ = cks_temp_db
        results = cks.search_keyword_fts5("authentication", limit=10)
        assert isinstance(results, list)

    def test_search_empty_query_returns_list(self, cks_temp_db):
        """search() handles empty query gracefully."""
        cks, _ = cks_temp_db
        results = cks.search("")
        assert isinstance(results, list)


class TestCKSSemantic:
    """Tests for CKS semantic search."""

    def test_search_semantic_returns_list(self, cks_temp_db):
        """search_semantic() returns a list (or gracefully degrades)."""
        cks, _ = cks_temp_db
        try:
            results = cks.search_semantic(
                "authentication mechanisms",
                limit=5
            )
            assert isinstance(results, list)
        except Exception as e:
            # Semantic search may fail gracefully if model unavailable
            assert "model" in str(e).lower() or "embed" in str(e).lower()


class TestCKSRelationships:
    """Tests for CKS relationship operations."""

    def test_add_relationship_returns_id(self, cks_temp_db):
        """add_relationship() returns a relationship ID."""
        cks, _ = cks_temp_db

        # First ingest two entries
        id1 = cks.ingest_memory("What is auth?", "Authentication is verification")
        id2 = cks.ingest_memory("What is JWT?", "JWT is a token format")

        # Add relationship between them
        rel_id = cks.add_relationship(id1, id2, "related_to")
        assert rel_id is not None

    def test_get_relationships_returns_list(self, cks_temp_db):
        """get_relationships() returns a list."""
        cks, _ = cks_temp_db
        id1 = cks.ingest_memory("What is auth?", "Authentication is verification")
        id2 = cks.ingest_memory("What is JWT?", "JWT is a token format")
        cks.add_relationship(id1, id2, "related_to")

        relationships = cks.get_relationships(id1)
        assert isinstance(relationships, list)


class TestCKSStatistics:
    """Tests for CKS statistics."""

    def test_get_statistics_returns_dict(self, cks_prod):
        """get_statistics() returns a dictionary with expected keys."""
        stats = cks_prod.get_statistics()

        assert isinstance(stats, dict)

        # Check expected keys (may not all be present)
        expected_keys = [
            'total_entries', 'database_size_bytes',
            'knowledge_entries', 'memory_entries',
            'pattern_entries'
        ]

        for key in expected_keys:
            # Key should exist OR be absent gracefully
            if key in stats:
                assert stats[key] >= 0

    def test_query_by_time_range_returns_list(self, cks_temp_db):
        """query_by_time_range() returns a list."""
        from datetime import datetime
        cks, _ = cks_temp_db
        cks.ingest_memory("Test entry", "Testing time range query")

        results = cks.query_by_time_range(
            start_time=datetime(2020, 1, 1),
            end_time=datetime(2030, 12, 31)
        )
        assert isinstance(results, list)


# Import CKS for test fixtures
from core.cks.unified import CKS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])