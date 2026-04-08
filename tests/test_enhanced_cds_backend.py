"""Unit tests for Enhanced CDS Backend with jMRI operations."""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.backends.local.cds_backend import CDSBackend
from core.backends.local.enhanced_cds_backend import EnhancedCDSBackend
from core.router_async import AsyncSearchRouter


class TestEnhancedCDSBackendInitialization:
    """Test EnhancedCDSBackend initialization and setup."""

    def test_initialization_with_default_config(self):
        """Test backend initializes with default configuration."""
        backend = EnhancedCDSBackend()
        assert backend._summary_index == {}
        assert backend._indexed is False

    def test_initialization_with_custom_params(self):
        """Test backend initializes with custom parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = EnhancedCDSBackend(
                root_paths=[tmpdir],
                enable_cache=False,
            )
            assert backend.root_paths == [Path(tmpdir)]
            assert backend.enable_cache is False


class TestJMRIDiscover:
    """Test jMRI discover() operation."""

    def test_discover_returns_available_codebases(self):
        """Test discover() returns list of available codebases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Python file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('"""Test module."""\n\ndef test_func():\n    """Test function."""\n    pass\n')

            backend = EnhancedCDSBackend(root_paths=[tmpdir])

            result = backend.discover()

            assert isinstance(result, list)
            assert len(result) >= 1

            # Check structure: dict with 'id', 'type', 'language', 'symbols' keys
            codebase = result[0]
            assert "id" in codebase
            assert "type" in codebase
            assert "language" in codebase
            assert "symbols" in codebase


class TestJMRISearch:
    """Test jMRI search() operation."""

    def test_search_returns_ids_and_summaries_only(self):
        """Test search() returns JMRISearchResult with IDs + summaries only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Python file with docstring
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def test_function():
    '''This is the first sentence. This is the second sentence.

    This additional content should NOT appear in search results.
    '''
    pass
""")

            backend = EnhancedCDSBackend(root_paths=[tmpdir])
            results = backend.search("test_function")

            # Verify returns list
            assert isinstance(results, list)

            if results:
                result = results[0]

                # Verify JMRISearchResult schema: id, summary, score, source
                assert "id" in result
                assert "summary" in result
                assert "score" in result
                assert "source" in result
                assert result["source"] == "cds"

                # CRITICAL: Summary is truncated (first 2 sentences, max 200 chars)
                assert len(result["summary"]) <= 200
                assert "This is the first sentence" in result["summary"]
                # Full docstring content should NOT be in summary
                assert "additional content" not in result["summary"]


class TestJMRIRetrieve:
    """Test jMRI retrieve() operation."""

    def test_retrieve_returns_full_source_with_metadata(self):
        """Test retrieve() returns full source + _meta token accounting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Python file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def test_function():
    '''This is the first sentence. This is the second sentence.

    This additional content should appear in retrieve but not search.
    '''
    pass
""")

            backend = EnhancedCDSBackend(root_paths=[tmpdir])

            # First search to get ID
            search_results = backend.search("test_function")
            assert len(search_results) > 0
            symbol_id = search_results[0]["id"]

            # Retrieve full content
            retrieve_result = backend.retrieve(symbol_id)

            # Verify JMRIRetrieveResult schema: id, source, _meta
            assert "id" in retrieve_result
            assert "source" in retrieve_result
            assert "_meta" in retrieve_result

            # Verify _meta block has token accounting
            _meta = retrieve_result["_meta"]
            assert "naive_tokens" in _meta
            assert "jmri_tokens" in _meta
            assert "tokens_saved" in _meta
            assert "reduction_pct" in _meta

            # Verify token reduction achieved
            assert _meta["naive_tokens"] > 0
            assert _meta["jmri_tokens"] > 0
            assert _meta["tokens_saved"] >= 0
            assert 0.0 <= _meta["reduction_pct"] <= 100.0

            # Verify full source includes complete docstring
            full_source = retrieve_result["source"]
            assert "additional content should appear" in full_source


class TestJMRIMetadata:
    """Test jMRI metadata() operation."""

    def test_metadata_returns_token_statistics(self):
        """Test metadata() returns backend token statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = EnhancedCDSBackend(root_paths=[tmpdir])

            metadata = backend.metadata()

            # Verify returns dict with token stats
            assert isinstance(metadata, dict)
            assert "naive_tokens" in metadata
            assert "jmri_tokens" in metadata
            assert "tokens_saved" in metadata
            assert "reduction_pct" in metadata


class TestAsyncSearchRouterIntegration:
    """Test AsyncSearchRouter integration with EnhancedCDSBackend."""

    def test_router_uses_enhanced_cds_when_jmri_enabled(self):
        """Test AsyncSearchRouter uses EnhancedCDSBackend when enable_jmri=True."""
        router = AsyncSearchRouter(enable_jmri=True)

        # Verify CDS backend is EnhancedCDSBackend
        assert isinstance(router._backends["cds"], EnhancedCDSBackend)

    def test_router_uses_standard_cds_when_jmri_disabled(self):
        """Test AsyncSearchRouter uses CDSBackend when enable_jmri=False (backward compatibility)."""
        router = AsyncSearchRouter(enable_jmri=False)

        # Verify CDS backend is standard CDSBackend
        assert isinstance(router._backends["cds"], CDSBackend)
        # Verify it's NOT EnhancedCDSBackend
        assert not isinstance(router._backends["cds"], EnhancedCDSBackend)

    def test_router_default_jmri_enabled(self):
        """Test AsyncSearchRouter defaults to enable_jmri=True."""
        router = AsyncSearchRouter()

        # Verify default uses EnhancedCDSBackend
        assert isinstance(router._backends["cds"], EnhancedCDSBackend)
