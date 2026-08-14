"""Unit tests for Knowledge Graph (KG) backend."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.backends.local.kg_backend import BACKEND_KG, KGBackend


class TestKGBackendInitialization:
    """Test KG backend initialization and setup."""

    def test_initialization_with_default_path(self):
        """Test backend initializes with default KG path from config."""
        backend = KGBackend()
        assert backend.kg_data_path is not None
        assert isinstance(backend.kg_data_path, Path)

    def test_initialization_with_custom_path(self):
        """Test backend initializes with custom KG path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = KGBackend(kg_data_path=tmpdir)
            assert backend.kg_data_path == Path(tmpdir)

    def test_initialization_state(self):
        """Test backend starts in unindexed state."""
        backend = KGBackend()
        assert backend._indexed is False
        assert len(backend._index) == 0
        assert len(backend._conversation_entities) == 0


class TestKGBackendIndexBuilding:
    """Test knowledge graph index building from JSON files."""

    def test_build_index_with_valid_entities(self):
        """Test index building with valid entities.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create entities.json
            entities_data = [
                {"text": "async", "type": "concept", "category": "programming"},
                {"text": "python", "type": "language", "category": "programming"},
            ]
            entities_path = Path(tmpdir) / "entities.json"
            entities_path.write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            backend.build_index()

            assert backend._indexed is True
            assert len(backend._index) == 2
            assert "async" in backend._index
            assert "python" in backend._index

    def test_build_index_with_valid_conversation_entities(self):
        """Test index building with valid conversation_entities.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create conversation_entities.json
            conv_data = {
                "conv_001": ["async", "python"],
                "conv_002": ["graph", "database"],
            }
            conv_path = Path(tmpdir) / "conversation_entities.json"
            conv_path.write_text(json.dumps(conv_data))

            backend = KGBackend(kg_data_path=tmpdir)
            backend.build_index()

            assert backend._indexed is True
            assert len(backend._conversation_entities) == 2
            assert "conv_001" in backend._conversation_entities
            assert backend._conversation_entities["conv_001"] == ["async", "python"]

    def test_build_index_with_missing_files(self):
        """Test index building gracefully handles missing JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = KGBackend(kg_data_path=tmpdir)
            backend.build_index()

            # Should complete without errors even with missing files
            assert backend._indexed is True
            assert len(backend._index) == 0
            assert len(backend._conversation_entities) == 0

    def test_build_index_with_invalid_json(self):
        """Test index building gracefully handles invalid JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON files
            (Path(tmpdir) / "entities.json").write_text("{invalid json")
            (Path(tmpdir) / "conversation_entities.json").write_text("{invalid json")

            backend = KGBackend(kg_data_path=tmpdir)
            backend.build_index()

            # Should complete without errors
            assert backend._indexed is True
            assert len(backend._index) == 0
            assert len(backend._conversation_entities) == 0


class TestKGEntitySearch:
    """Test entity search functionality."""

    def test_exact_entity_match(self):
        """Test exact entity matching returns correct results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            entities_data = [
                {"text": "async", "type": "concept"},
                {"text": "await", "type": "keyword"},
            ]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("async")

            assert len(results) >= 1
            assert results[0]["score"] >= 0.7, "Exact match should have high score"
            assert "async" in results[0]["title"].lower()

    def test_partial_entity_match(self):
        """Test partial entity matching works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            entities_data = [
                {"text": "knowledge graph", "type": "concept"},
                {"text": "entity extraction", "type": "technique"},
            ]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("graph")

            assert len(results) >= 1
            assert "graph" in results[0]["title"].lower()
            assert results[0]["score"] < 0.8, "Partial match should have lower score than exact"

    def test_no_match_returns_empty(self):
        """Test search with no matches returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "python", "type": "language"}]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("nonexistent")

            assert len(results) == 0

    def test_case_insensitive_search(self):
        """Test search is case-insensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "Async", "type": "concept"}]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results_lower = backend.search("async")
            results_upper = backend.search("ASYNC")

            assert len(results_lower) == len(results_upper)
            assert len(results_lower) >= 1


class TestKGANDQueries:
    """Test AND query functionality (multi-entity search)."""

    def test_and_query_finds_conversations(self):
        """Test AND query finds conversations with all entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            entities_data = [{"text": "async", "type": "concept"}]
            conv_data = {
                "conv_001": ["async", "python"],
                "conv_002": ["async", "rag"],
                "conv_003": ["python", "rag"],
            }
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))
            (Path(tmpdir) / "conversation_entities.json").write_text(json.dumps(conv_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("async AND rag")

            assert len(results) >= 1
            # Should find conv_002 which has both async and rag
            assert any("conv_002" in str(r) for r in results)

    def test_and_query_with_no_matches(self):
        """Test AND query with no matching conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "async", "type": "concept"}]
            conv_data = {
                "conv_001": ["async", "python"],
                "conv_002": ["async", "rag"],
            }
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))
            (Path(tmpdir) / "conversation_entities.json").write_text(json.dumps(conv_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("async AND nonexistent")

            assert len(results) == 0

    def test_and_query_normalizes_spaces(self):
        """Test AND query normalizes multiple spaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "async", "type": "concept"}]
            conv_data = {
                "conv_001": ["async", "rag"],
            }
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))
            (Path(tmpdir) / "conversation_entities.json").write_text(json.dumps(conv_data))

            backend = KGBackend(kg_data_path=tmpdir)

            # Test various space patterns
            results1 = backend.search("async AND rag")
            results2 = backend.search("async   AND   rag")
            results3 = backend.search("async AND  rag")

            assert len(results1) == len(results2) == len(results3)

    def test_and_query_requires_all_terms(self):
        """Test AND query requires ALL terms to be present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [
                {"text": "async", "type": "concept"},
                {"text": "python", "type": "language"},
                {"text": "rag", "type": "architecture"},
            ]
            conv_data = {
                "conv_001": ["async", "python"],  # Missing rag
                "conv_002": ["async", "rag"],     # Missing python
                "conv_003": ["async", "python", "rag"],  # Has all three
            }
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))
            (Path(tmpdir) / "conversation_entities.json").write_text(json.dumps(conv_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("async AND python AND rag")

            # Should only find conv_003 which has all three
            assert len(results) >= 1
            assert all("conv_003" in str(r) for r in results)


class TestKGSearchValidation:
    """Test search input validation and edge cases."""

    def test_empty_query_returns_empty(self):
        """Test empty query string returns empty results."""
        backend = KGBackend()
        backend.build_index()

        results = backend.search("")
        assert len(results) == 0

    def test_whitespace_query_returns_empty(self):
        """Test whitespace-only query returns empty results."""
        backend = KGBackend()
        backend.build_index()

        results = backend.search("   ")
        assert len(results) == 0

    def test_none_query_returns_empty(self):
        """Test None query returns empty results."""
        backend = KGBackend()
        backend.build_index()

        results = backend.search(None)
        assert len(results) == 0

    def test_limit_parameter(self):
        """Test search limit parameter works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple entities
            entities_data = [
                {"text": f"entity_{i}", "type": "concept"}
                for i in range(10)
            ]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)

            # Search with limit
            results_limited = backend.search("entity", limit=3)
            results_unlimited = backend.search("entity", limit=100)

            assert len(results_limited) <= 3
            assert len(results_unlimited) >= len(results_limited)


class TestKGBackendConstant:
    """Test KG backend constant definition."""

    def test_backend_kg_constant(self):
        """Test BACKEND_KG constant is defined correctly."""
        assert BACKEND_KG == "KG"
        assert isinstance(BACKEND_KG, str)
        assert len(BACKEND_KG) > 0


class TestKGResultFormatting:
    """Test result formatting and structure."""

    def test_result_has_required_fields(self):
        """Test search results contain all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "async", "type": "concept"}]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("async")

            if results:
                result = results[0]
                # Check required fields exist
                assert "id" in result
                assert "source" in result
                assert "title" in result
                assert "content" in result
                assert "score" in result
                assert isinstance(result["score"], (int, float))
                assert 0.0 <= result["score"] <= 1.0

    def test_result_source_is_kg(self):
        """Test results have correct source identifier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "async", "type": "concept"}]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            results = backend.search("async")

            if results:
                assert results[0]["source"] == BACKEND_KG


class TestKGBackendIntegration:
    """Integration tests for complete KG workflow."""

    def test_full_workflow_search_and_index(self):
        """Test complete workflow: build index then search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup test data
            entities_data = [
                {"text": "async", "type": "concept", "category": "programming"},
                {"text": "rag", "type": "architecture", "category": "ai"},
            ]
            conv_data = {
                "conv_001": ["async", "await"],
                "conv_002": ["rag", "retrieval"],
                "conv_003": ["async", "rag"],
            }

            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))
            (Path(tmpdir) / "conversation_entities.json").write_text(json.dumps(conv_data))

            # Test workflow
            backend = KGBackend(kg_data_path=tmpdir)

            # Single entity search
            results = backend.search("async")
            assert len(results) >= 1

            # AND query
            results = backend.search("async AND rag")
            assert len(results) >= 1

            # Partial match
            results = backend.search("arch")
            assert len(results) >= 1

    def test_auto_index_on_first_search(self):
        """Test that index is built automatically on first search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities_data = [{"text": "auto", "type": "test"}]
            (Path(tmpdir) / "entities.json").write_text(json.dumps(entities_data))

            backend = KGBackend(kg_data_path=tmpdir)
            assert backend._indexed is False

            # First search should trigger auto-index
            results = backend.search("auto")
            assert backend._indexed is True
            assert len(results) >= 1
