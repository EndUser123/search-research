"""Tests for search router.

All tests migrated to async to use search_async() directly.
"""

import asyncio

import pytest
from search_research import AsyncSearchRouter, Mode, UnifiedAsyncRouter


@pytest.fixture
def async_router():
    """Fixture providing UnifiedAsyncRouter instance."""
    return UnifiedAsyncRouter()


class TestAsyncSearchRouter:
    """Tests for AsyncSearchRouter (async tests)."""

    def test_init(self):
        """Test router initialization."""
        router = AsyncSearchRouter()
        assert router.mode == Mode.FAST.value
        assert router.cache_ttl == 3600
        assert router.enable_cache is True

    def test_init_with_options(self):
        """Test router initialization with options."""
        router = AsyncSearchRouter(cache_ttl=1800, enable_cache=False)
        assert router.cache_ttl == 1800
        assert router.enable_cache is False

    @pytest.mark.asyncio
    async def test_search_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        router = AsyncSearchRouter()
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await router.search_async("")

    @pytest.mark.asyncio
    async def test_search_whitespace_query_raises(self):
        """Test that whitespace-only query raises ValueError."""
        router = AsyncSearchRouter()
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await router.search_async("   ")

    @pytest.mark.asyncio
    async def test_search_returns_list(self, sample_query):
        """Test that search_async returns a list."""
        router = AsyncSearchRouter()
        results = await router.search_async(sample_query)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_limit(self, sample_query):
        """Test search_async with limit parameter."""
        router = AsyncSearchRouter()
        results = await router.search_async(sample_query, limit=5)
        assert len(results) <= 5  # Once implemented


class TestUnifiedRouter:
    """Tests for UnifiedAsyncRouter."""

    def test_init_default_mode(self):
        """Test router initialization with default mode."""
        router = UnifiedAsyncRouter()
        assert router.mode == "auto"

    def test_init_local_only_mode(self):
        """Test router initialization with local-only mode."""
        router = UnifiedAsyncRouter(mode="local-only")
        assert router.mode == "local-only"

    def test_init_web_fallback_mode(self):
        """Test router initialization with web-fallback mode."""
        router = UnifiedAsyncRouter(mode="web-fallback")
        assert router.mode == "web-fallback"

    def test_init_unified_mode(self):
        """Test router initialization with unified mode."""
        router = UnifiedAsyncRouter(mode="unified")
        assert router.mode == "unified"

    @pytest.mark.asyncio
    async def test_search_async_is_coroutine(self, sample_query):
        """Test that search_async returns a coroutine."""
        router = UnifiedAsyncRouter()
        result = router.search_async(sample_query)
        assert asyncio.iscoroutine(result)
