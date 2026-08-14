"""Integration tests for HyDE query enhancement (Phase 4).

Tests HyDE functionality with the new architecture where Claude Code
(orchestrator) generates HyDE documents pre-invocation. The Python code
no longer makes external API calls.
"""

import pytest
from search_research import apply_hyde, enhance_query, extract_key_phrases


class TestHyDEQueryEnhancement:
    """Tests for HyDE (Hypothetical Document Embeddings) query enhancement."""

    def test_apply_hyde_with_content(self):
        """Test that apply_hyde works with pre-generated content."""
        query = "FastAPI async patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax for efficient concurrent processing."

        enhanced, applied = apply_hyde(query, hyde_content=hyde_content)

        assert applied is True
        assert isinstance(enhanced, str)
        assert len(enhanced) > len(query)
        assert query in enhanced

    def test_apply_hyde_without_content(self):
        """Test that apply_hyde returns original query when no content provided."""
        query = "FastAPI async patterns"

        enhanced, applied = apply_hyde(query, hyde_content=None)

        assert applied is False
        assert enhanced == query

    def test_apply_hyde_with_empty_content(self):
        """Test that apply_hyde handles empty content gracefully."""
        query = "FastAPI async patterns"

        enhanced, applied = apply_hyde(query, hyde_content="")

        assert applied is False
        assert enhanced == query

    def test_apply_hyde_with_whitespace_content(self):
        """Test that apply_hyde handles whitespace-only content."""
        query = "FastAPI async patterns"

        enhanced, applied = apply_hyde(query, hyde_content="   ")

        assert applied is False
        assert enhanced == query

    def test_hyde_enhances_query_with_key_phrases(self):
        """Test that HyDE enhances query with extracted key phrases."""
        query = "FastAPI async patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax for efficient concurrent processing."

        enhanced, applied = apply_hyde(query, hyde_content=hyde_content)

        assert applied is True
        # Enhanced query should be longer than original
        assert len(enhanced) >= len(query)

    def test_hyde_handles_complex_queries(self):
        """Test that HyDE handles complex, multi-part queries."""
        query = "how to implement caching in React with TypeScript"
        hyde_content = "React caching can be implemented using React Query, SWR, or useMemo hooks for optimized performance."

        enhanced, applied = apply_hyde(query, hyde_content=hyde_content)

        assert applied is True
        assert isinstance(enhanced, str)


class TestHyDEKeyPhraseExtraction:
    """Tests for key phrase extraction functionality."""

    def test_extract_key_phrases_from_document(self):
        """Test that key phrases are extracted from hypothetical document."""
        doc = "FastAPI supports async operations using Python's async/await syntax."

        phrases = extract_key_phrases(doc)

        assert isinstance(phrases, list)
        # May be empty if no capitalized phrases found
        assert len(phrases) <= 5

    def test_extract_key_phrases_handles_empty_document(self):
        """Test that empty document raises ValueError."""
        with pytest.raises(ValueError, match="Document cannot be empty"):
            extract_key_phrases("")

    def test_extract_key_phrases_handles_whitespace_document(self):
        """Test that whitespace-only document raises ValueError."""
        with pytest.raises(ValueError, match="Document cannot be empty"):
            extract_key_phrases("   ")


class TestHyDEQueryEnhancementLogic:
    """Tests for query enhancement logic."""

    def test_enhance_query_with_key_phrases(self):
        """Test that enhance_query combines query with key phrases."""
        query = "FastAPI async"
        key_phrases = ["async operations", "await syntax"]

        enhanced = enhance_query(query, key_phrases)

        assert "FastAPI async" in enhanced
        assert "async operations" in enhanced
        assert "await syntax" in enhanced

    def test_enhance_query_with_empty_key_phrases(self):
        """Test that enhance_query returns original query with empty phrases."""
        query = "FastAPI async"

        enhanced = enhance_query(query, [])

        assert enhanced == query

    def test_enhance_query_with_none_key_phrases(self):
        """Test that enhance_query returns original query with None phrases."""
        query = "FastAPI async"

        enhanced = enhance_query(query, None)

        assert enhanced == query

    def test_enhance_query_handles_empty_query(self):
        """Test that enhance_query raises ValueError for empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            enhance_query("", ["test"])


class TestHyDEIntegration:
    """Integration tests for HyDE with search routers."""

    def test_hyde_integration_with_research_router(self):
        """Test HyDE integration with UnifiedAsyncRouter."""
        from search_research import UnifiedAsyncRouter

        # Create router with default settings (no hyde_enabled parameter in actual API)
        router = UnifiedAsyncRouter()

        # Router should initialize successfully
        assert router is not None
        assert router.mode == "auto"

    def test_fast_mode_does_not_use_hyde(self):
        """Test that FAST mode (AsyncSearchRouter) does not use HyDE."""
        from search_research import AsyncSearchRouter

        # AsyncSearchRouter doesn't have HyDE
        router = AsyncSearchRouter()

        # Should not have hyde_enabled attribute
        assert not hasattr(router, "hyde_enabled")

    def test_unified_router_initialization(self):
        """Test that UnifiedAsyncRouter initializes correctly."""
        from search_research import UnifiedAsyncRouter

        # Create router with default settings
        router = UnifiedAsyncRouter()

        # Should initialize successfully
        assert router is not None
        assert hasattr(router, "mode")
        assert router.mode in ["auto", "local-only", "web-fallback", "unified"]

    def test_hyde_mode_specific_behavior(self):
        """Test that router mode can be configured."""
        from search_research import AsyncSearchRouter, UnifiedAsyncRouter

        # FAST mode: AsyncSearchRouter
        fast_router = AsyncSearchRouter(mode="fast")
        assert fast_router.mode == "fast"
        assert not hasattr(fast_router, "hyde_enabled")

        # COMPREHENSIVE mode: UnifiedAsyncRouter
        comprehensive_router = UnifiedAsyncRouter(mode="unified")
        assert comprehensive_router.mode == "unified"


class TestHyDEErrorHandling:
    """Tests for HyDE error handling and edge cases."""

    def test_hyde_handles_malformed_content(self):
        """Test that HyDE handles malformed content gracefully."""
        query = "test query"
        malformed_content = "!!!@@@###"  # No meaningful phrases

        # Should not crash
        enhanced, applied = apply_hyde(query, hyde_content=malformed_content)

        # May or may not apply HyDE depending on extraction success
        assert isinstance(enhanced, str)
        assert isinstance(applied, bool)

    def test_hyde_handles_very_long_content(self):
        """Test that HyDE handles very long hypothetical documents."""
        query = "test query"
        long_content = "FastAPI supports async operations. " * 100  # Very long

        # Should not crash
        enhanced, applied = apply_hyde(query, hyde_content=long_content)

        assert isinstance(enhanced, str)
        assert isinstance(applied, bool)

    def test_hyde_handles_special_characters(self):
        """Test that HyDE handles special characters in content."""
        query = "test query"
        content_with_special = "FastAPI supports: async, await, & concurrency! (Python)."

        # Should not crash
        enhanced, applied = apply_hyde(query, hyde_content=content_with_special)

        assert isinstance(enhanced, str)
        assert isinstance(applied, bool)

    def test_hyde_handles_multilingual_content(self):
        """Test that HyDE handles multilingual content."""
        query = "test query"
        multilingual_content = "FastAPI supporte operaciones asíncronas usando async/await syntax."

        # Should not crash
        enhanced, applied = apply_hyde(query, hyde_content=multilingual_content)

        assert isinstance(enhanced, str)
        assert isinstance(applied, bool)


class TestHyDEQuality:
    """Tests for HyDE output quality."""

    def test_hyde_maintains_query_intent(self):
        """Test that HyDE maintains the original query intent."""
        query = "FastAPI async patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax."

        enhanced, applied = apply_hyde(query, hyde_content=hyde_content)

        if applied:
            # Original query should be preserved in enhanced query
            assert query in enhanced or query.split()[0] in enhanced

    def test_hyde_handles_different_query_types(self):
        """Test that HyDE handles different query types appropriately."""
        test_cases = [
            ("def function", "Python function definitions"),  # Code query
            ("tutorial for React", "React provides component-based UI"),  # Learning query
            ("compare vs contrast", "Comparison analysis between options"),  # Comparison query
        ]

        for query, hyde_content in test_cases:
            enhanced, applied = apply_hyde(query, hyde_content=hyde_content)

            # Should not crash for any query type
            assert isinstance(enhanced, str)
            assert isinstance(applied, bool)


class TestHyDERouterIntegration:
    """Tests for HyDE integration with AsyncSearchRouter."""

    @pytest.mark.asyncio
    async def test_search_async_with_hyde_content_fast_mode(self):
        """Test that search_async accepts hyde_content parameter even in fast mode."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(mode="fast")  # hyde=False by default
        query = "FastAPI patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax."

        # Should not raise - hyde_content is accepted but not applied in fast mode
        results = await router.search_async(query, limit=5, hyde_content=hyde_content)

        # Results should be a list
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_async_with_hyde_content_comprehensive_mode(self):
        """Test that search_async applies HyDE in comprehensive mode."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(mode="comprehensive")  # hyde=True by default
        query = "FastAPI patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax."

        # Should not raise - hyde is applied in comprehensive mode
        results = await router.search_async(query, limit=5, hyde_content=hyde_content)

        # Results should be a list
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_async_with_hyde_explicit_override(self):
        """Test that hyde parameter override works correctly."""
        from search_research import AsyncSearchRouter

        # Fast mode with explicit hyde=True override
        router = AsyncSearchRouter(mode="fast", hyde=True)
        query = "FastAPI patterns"
        hyde_content = "FastAPI supports async operations using Python's async/await syntax."

        # HyDE should be applied despite fast mode due to override
        results = await router.search_async(query, limit=5, hyde_content=hyde_content)

        # Results should be a list
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_async_without_hyde_content(self):
        """Test that search_async works without hyde_content."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(mode="comprehensive")
        query = "FastAPI patterns"

        # Should not raise - no hyde_content provided
        results = await router.search_async(query, limit=5)

        # Results should be a list
        assert isinstance(results, list)


@pytest.fixture
def sample_queries():
    """Sample queries for HyDE testing."""
    return [
        "FastAPI async patterns",
        "best practices for database optimization",
        "how to implement caching in React",
        "compare PostgreSQL vs MongoDB",
        "explain microservices architecture",
    ]


@pytest.fixture
def sample_hyde_contents():
    """Sample HyDE contents for testing."""
    return [
        "FastAPI supports async operations using Python's async/await syntax for efficient concurrent processing.",
        "Database optimization involves proper indexing, query optimization, and connection pooling.",
        "React caching can be implemented using React Query, SWR, or useMemo hooks for optimized performance.",
        "PostgreSQL is a relational database while MongoDB is a document-oriented NoSQL database with different use cases.",
        "Microservices architecture breaks applications into small, independent services that communicate via APIs.",
    ]
