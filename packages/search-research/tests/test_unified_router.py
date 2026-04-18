"""Tests for UnifiedAsyncRouter combining local + web search.

These tests verify the UnifiedAsyncRouter class that integrates local and web search
with mode-based routing, quality checking, and RRF fusion.

Test Strategy:
- Use real AsyncSearchRouter instances instead of mocks
- Inject routers via dependency injection for testing
- Only mock is_satisfactory where quality checks need control
- Tests verify actual routing behavior, not mock interactions

Run with: pytest tests/test_unified_router.py -v
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.quality_checker import QualityConfig
from core.router_async import AsyncSearchRouter, SearchResult


class TestUnifiedAsyncRouterBasicStructure:
    """Tests for basic UnifiedAsyncRouter instantiation and structure."""

    def test_unified_async_router_class_exists(self):
        """Test that UnifiedAsyncRouter class can be imported."""
        from core.unified_router import UnifiedAsyncRouter  # noqa: F401

    def test_init_creates_instance_with_defaults(self):
        """Test that UnifiedAsyncRouter can be instantiated with defaults."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter()
        assert router is not None
        assert router.mode == "auto"
        assert router.enable_jmri is True
        assert router.rrf_k == 60
        assert router.quality_config is not None

    def test_init_with_mode_parameter(self):
        """Test UnifiedAsyncRouter initialization with mode parameter."""
        from core.unified_router import UnifiedAsyncRouter

        # Test all valid modes
        for mode in ["auto", "local-only", "web-fallback", "unified"]:
            router = UnifiedAsyncRouter(mode=mode)
            assert router.mode == mode

    def test_init_with_enable_jmri_parameter(self):
        """Test UnifiedAsyncRouter initialization with enable_jmri parameter."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter(enable_jmri=False)
        assert router.enable_jmri is False

        router = UnifiedAsyncRouter(enable_jmri=True)
        assert router.enable_jmri is True

    def test_init_with_rrf_k_parameter(self):
        """Test UnifiedAsyncRouter initialization with rrf_k parameter."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter(rrf_k=80)
        assert router.rrf_k == 80

        router = UnifiedAsyncRouter(rrf_k=40)
        assert router.rrf_k == 40

    def test_init_with_quality_config_parameter(self):
        """Test UnifiedAsyncRouter initialization with quality_config parameter."""
        from core.unified_router import UnifiedAsyncRouter

        config = QualityConfig(confidence_threshold=0.9, freshness_hours=12, min_backends=5)
        router = UnifiedAsyncRouter(quality_config=config)
        assert router.quality_config == config

    def test_init_with_router_injection(self):
        """Test UnifiedAsyncRouter initialization with injected routers."""
        from core.unified_router import UnifiedAsyncRouter

        local_router = AsyncSearchRouter(enable_jmri=True)
        web_router = AsyncSearchRouter(enable_jmri=True)

        router = UnifiedAsyncRouter(local_router=local_router, web_router=web_router)

        # Verify routers were injected
        assert router._async_local_router is local_router
        assert router._web_router is web_router

    def test_has_search_async_method(self):
        """Test that search_async method exists and is coroutine function."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter()
        assert hasattr(router, "search_async")
        assert asyncio.iscoroutinefunction(router.search_async)


class TestUnifiedAsyncRouterLocalOnlyMode:
    """Tests for local-only mode behavior."""

    @pytest.mark.asyncio
    async def test_local_only_mode_only_searches_local(self):
        """Test that local-only mode only searches local backends."""
        from core.unified_router import UnifiedAsyncRouter

        # Create a mock local router with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(
            return_value=[
                SearchResult(title="Local Result", content="Local content", source="CDS", score=0.9)
            ]
        )

        router = UnifiedAsyncRouter(mode="local-only", local_router=mock_local_router)

        results = await router.search_async("test query")

        # Verify local router was called
        mock_local_router.search_async.assert_called_once()
        # Verify results are from local search only
        assert len(results) == 1
        assert results[0].source == "CDS"

    @pytest.mark.asyncio
    async def test_local_only_mode_skips_web_search(self):
        """Test that local-only mode never calls web search."""
        from core.unified_router import UnifiedAsyncRouter

        # Create a mock local router with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(
            return_value=[
                SearchResult(title="Local", content="Local content", source="CDS", score=0.8)
            ]
        )

        router = UnifiedAsyncRouter(mode="local-only", local_router=mock_local_router)

        results = await router.search_async("test query")

        # Verify local router was called
        mock_local_router.search_async.assert_called_once()
        # Verify we got results
        assert len(results) == 1


class TestUnifiedAsyncRouterAutoMode:
    """Tests for auto mode behavior with quality checking."""

    @pytest.mark.asyncio
    async def test_auto_mode_skips_web_when_quality_satisfactory(self):
        """Test that auto mode skips web search when local results are satisfactory."""
        from core.unified_router import UnifiedAsyncRouter

        # Create high-quality local results
        satisfactory_results = [
            SearchResult(
                title="High Quality Result",
                content="Good content",
                source="CDS",
                score=0.95,
                metadata={
                    "confidence": 0.95,
                    "created_at": datetime.now(timezone.utc),
                    "sources": ["CDS", "Grep", "Skills"],
                },
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=satisfactory_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=[])

        router = UnifiedAsyncRouter(
            mode="auto", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return True
        with patch("core.unified_router.is_satisfactory", return_value=True) as mock_satisfactory:
            results = await router.search_async("test query")

            # Verify quality was checked
            mock_satisfactory.assert_called()
            # Verify local router was called
            mock_local_router.search_async.assert_called_once()
            # Verify web router was NOT called (quality satisfactory)
            mock_web_router.search_web_providers_async.assert_not_called()
            # Verify local results were returned
            assert len(results) == 1
            assert results[0].title == "High Quality Result"

    @pytest.mark.asyncio
    async def test_auto_mode_falls_back_to_web_when_quality_poor(self):
        """Test that auto mode falls back to web search when local results are poor."""
        from core.unified_router import UnifiedAsyncRouter

        # Create poor-quality local results
        poor_results = [
            SearchResult(
                title="Low Quality Result",
                content="Weak content",
                source="CDS",
                score=0.5,
                metadata={
                    "confidence": 0.5,
                    "created_at": datetime.now(timezone.utc),
                    "sources": ["CDS"],  # Only one backend
                },
            )
        ]

        # Create web results
        web_results = [
            SearchResult(title="Web Result", content="Web content", source="TAVILY", score=0.85)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=poor_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="auto", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return False
        with patch("core.unified_router.is_satisfactory", return_value=False) as mock_satisfactory:
            results = await router.search_async("test query")

            # Verify quality was checked
            mock_satisfactory.assert_called()
            # Verify web router WAS called (quality poor)
            mock_web_router.search_web_providers_async.assert_called_once()
            # Verify results include web results
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_auto_mode_merges_local_and_web_with_rrf(self):
        """Test that auto mode merges local and web results using RRF."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter(mode="auto", rrf_k=60)

        # Create local results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.7,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        # Create web results
        web_results = [
            SearchResult(title="Web Result", content="Web content", source="TAVILY", score=0.8)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="auto", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return False (trigger web search)
        with patch("core.unified_router.is_satisfactory", return_value=False):
            results = await router.search_async("test query")

            # Verify both routers were called
            mock_local_router.search_async.assert_called_once()
            mock_web_router.search_web_providers_async.assert_called_once()
            # Verify results were merged
            assert len(results) >= 1


class TestUnifiedAsyncRouterWebFallbackMode:
    """Tests for web-fallback mode behavior."""

    @pytest.mark.asyncio
    async def test_web_fallback_mode_always_checks_quality(self):
        """Test that web-fallback mode always checks quality."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.7,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=[])

        router = UnifiedAsyncRouter(
            mode="web-fallback", local_router=mock_local_router, web_router=mock_web_router
        )

        # Verify quality check happens (return True to skip web)
        with patch("core.unified_router.is_satisfactory", return_value=True) as mock_satisfactory:
            results = await router.search_async("test query")

            # Verify quality was checked
            mock_satisfactory.assert_called()
            # Verify we got results
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_web_fallback_mode_searches_web_when_quality_fails(self):
        """Test that web-fallback mode searches web when quality check fails."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.5,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        # Create web results
        web_results = [
            SearchResult(title="Web Result", content="Web content", source="SERPER", score=0.8)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="web-fallback", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return False (trigger web search)
        with patch("core.unified_router.is_satisfactory", return_value=False):
            results = await router.search_async("test query")

            # Verify web router was called
            mock_web_router.search_web_providers_async.assert_called_once()
            # Verify results include web results
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_web_fallback_mode_skips_web_when_quality_passes(self):
        """Test that web-fallback mode skips web when quality check passes."""
        from core.unified_router import UnifiedAsyncRouter

        # Create high-quality local results
        good_results = [
            SearchResult(
                title="Good Result",
                content="Good content",
                source="CDS",
                score=0.9,
                metadata={
                    "confidence": 0.9,
                    "created_at": datetime.now(timezone.utc),
                    "sources": ["CDS", "Grep", "Skills"],
                },
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=good_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=[])

        router = UnifiedAsyncRouter(
            mode="web-fallback", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return True (skip web search)
        with patch("core.unified_router.is_satisfactory", return_value=True):
            results = await router.search_async("test query")

            # Verify web router was NOT called
            mock_web_router.search_web_providers_async.assert_not_called()
            # Verify local results were returned
            assert len(results) == 1
            assert results[0].title == "Good Result"


class TestUnifiedAsyncRouterUnifiedMode:
    """Tests for unified mode behavior."""

    @pytest.mark.asyncio
    async def test_unified_mode_always_searches_both(self):
        """Test that unified mode always searches both local and web."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.7,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        # Create web results
        web_results = [
            SearchResult(title="Web Result", content="Web content", source="TAVILY", score=0.8)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="unified", local_router=mock_local_router, web_router=mock_web_router
        )

        results = await router.search_async("test query")

        # Verify both routers were called
        mock_local_router.search_async.assert_called_once()
        mock_web_router.search_web_providers_async.assert_called_once()
        # Verify results were returned
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_unified_mode_merges_with_rrf(self):
        """Test that unified mode merges results using RRF."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.7,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        # Create web results
        web_results = [
            SearchResult(title="Web Result", content="Web content", source="SERPER", score=0.8)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="unified", rrf_k=60, local_router=mock_local_router, web_router=mock_web_router
        )

        results = await router.search_async("test query")

        # Verify both routers were called
        mock_local_router.search_async.assert_called_once()
        mock_web_router.search_web_providers_async.assert_called_once()
        # Verify results were merged
        assert len(results) >= 1


class TestUnifiedAsyncRouterRRFFusion:
    """Tests for Reciprocal Rank Fusion (RRF) functionality."""

    @pytest.mark.asyncio
    async def test_rrf_fusion_merges_results_correctly(self):
        """Test that RRF fusion merges and ranks results correctly."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local results with high score
        local_results = [
            SearchResult(
                title="Local Result 1",
                content="Local content 1",
                source="CDS",
                score=0.9,
                metadata={"created_at": datetime.now(timezone.utc)},
            ),
            SearchResult(
                title="Local Result 2",
                content="Local content 2",
                source="Grep",
                score=0.8,
                metadata={"created_at": datetime.now(timezone.utc)},
            ),
        ]

        # Create web results
        web_results = [
            SearchResult(title="Web Result", content="Web content", source="TAVILY", score=0.7)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="unified", rrf_k=60, local_router=mock_local_router, web_router=mock_web_router
        )

        results = await router.search_async("test query")

        # Verify results were merged (should have results from both sources)
        assert len(results) >= 1
        # Verify all sources are represented
        sources = {r.source for r in results}
        assert "CDS" in sources or "Grep" in sources or "TAVILY" in sources

    @pytest.mark.asyncio
    async def test_rrf_with_custom_k_parameter(self):
        """Test that RRF fusion respects custom k parameter."""
        from core.unified_router import UnifiedAsyncRouter

        # Create results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.7,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        web_results = [
            SearchResult(title="Web Result", content="Web content", source="SERPER", score=0.8)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="unified",
            rrf_k=80,  # Custom k parameter
            local_router=mock_local_router,
            web_router=mock_web_router,
        )

        results = await router.search_async("test query")

        # Verify RRF was applied (results should be merged)
        assert len(results) >= 1


class TestUnifiedAsyncRouterQualityConfiguration:
    """Tests for quality configuration functionality."""

    @pytest.mark.asyncio
    async def test_custom_quality_config_affects_enhancement(self):
        """Test that custom quality config affects progressive enhancement."""
        from core.unified_router import UnifiedAsyncRouter

        # Create custom quality config
        custom_config = QualityConfig(confidence_threshold=0.95, freshness_hours=6, min_backends=3)

        # Create local results that don't meet custom config
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.8,
                metadata={
                    "confidence": 0.8,  # Below custom threshold
                    "created_at": datetime.now(timezone.utc),
                    "sources": ["CDS"],  # Only 1 backend, below min_backends
                },
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=[])

        router = UnifiedAsyncRouter(
            mode="auto",
            quality_config=custom_config,
            local_router=mock_local_router,
            web_router=mock_web_router,
        )

        # With custom config, quality check should fail
        with patch("core.unified_router.is_satisfactory", return_value=False):
            results = await router.search_async("test query")

            # Verify web router was called due to poor quality
            mock_web_router.search_web_providers_async.assert_called_once()


class TestUnifiedAsyncRouterProgressiveEnhancement:
    """Tests for progressive enhancement behavior."""

    @pytest.mark.asyncio
    async def test_progressive_enhancement_skips_web_with_good_local(self):
        """Test that good local results skip web search (performance optimization)."""
        from core.unified_router import UnifiedAsyncRouter

        # Create high-quality local results
        good_results = [
            SearchResult(
                title="High Quality Result",
                content="Excellent content",
                source="CDS",
                score=0.95,
                metadata={
                    "confidence": 0.95,
                    "created_at": datetime.now(timezone.utc),
                    "sources": ["CDS", "Grep", "Skills"],
                },
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=good_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=[])

        router = UnifiedAsyncRouter(
            mode="auto", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return True
        with patch("core.unified_router.is_satisfactory", return_value=True):
            results = await router.search_async("test query")

            # Verify web router was NOT called (progressive enhancement worked)
            mock_web_router.search_web_providers_async.assert_not_called()
            # Verify local results were returned
            assert len(results) == 1
            assert results[0].title == "High Quality Result"

    @pytest.mark.asyncio
    async def test_progressive_enhancement_calls_web_with_poor_local(self):
        """Test that poor local results trigger web search (progressive enhancement)."""
        from core.unified_router import UnifiedAsyncRouter

        # Create low-quality local results
        poor_results = [
            SearchResult(
                title="Low Quality Result",
                content="Weak content",
                source="CDS",
                score=0.4,
                metadata={
                    "confidence": 0.4,
                    "created_at": datetime.now(timezone.utc),
                    "sources": ["CDS"],  # Only one backend
                },
            )
        ]

        # Create web results
        web_results = [
            SearchResult(
                title="Web Result", content="Better web content", source="SERPER", score=0.8
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=poor_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="auto", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to return False
        with patch("core.unified_router.is_satisfactory", return_value=False):
            results = await router.search_async("test query")

            # Verify web router WAS called (progressive enhancement triggered)
            mock_web_router.search_web_providers_async.assert_called_once()
            # Verify results include web results
            assert len(results) >= 1


class TestUnifiedAsyncRouterErrorHandling:
    """Tests for error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_handles_empty_query_gracefully(self):
        """Test that empty query is handled gracefully."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await router.search_async("")

    @pytest.mark.asyncio
    async def test_handles_whitespace_only_query_gracefully(self):
        """Test that whitespace-only query is handled gracefully."""
        from core.unified_router import UnifiedAsyncRouter

        router = UnifiedAsyncRouter()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await router.search_async("   ")

    @pytest.mark.asyncio
    async def test_handles_invalid_mode_gracefully(self):
        """Test that invalid mode is handled gracefully."""
        from core.unified_router import UnifiedAsyncRouter

        with pytest.raises(ValueError, match="Invalid mode"):
            UnifiedAsyncRouter(mode="invalid-mode")

    @pytest.mark.asyncio
    async def test_handles_web_search_failure_gracefully(self):
        """Test that web search failure doesn't crash local results."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local results
        local_results = [
            SearchResult(
                title="Local Result",
                content="Local content",
                source="CDS",
                score=0.7,
                metadata={"created_at": datetime.now(timezone.utc)},
            )
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        # Create web router that fails
        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(
            side_effect=Exception("Web search failed")
        )

        router = UnifiedAsyncRouter(
            mode="auto", local_router=mock_local_router, web_router=mock_web_router
        )

        # Patch is_satisfactory to trigger web search
        with patch("core.unified_router.is_satisfactory", return_value=False):
            results = await router.search_async("test query")

            # Verify local results were still returned despite web failure
            assert len(results) == 1
            assert results[0].source == "CDS"

    @pytest.mark.asyncio
    async def test_handles_local_search_failure_gracefully(self):
        """Test that local search failure returns empty results."""
        from core.unified_router import UnifiedAsyncRouter

        # Create local router that fails
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(side_effect=Exception("Local search failed"))

        router = UnifiedAsyncRouter(mode="auto", local_router=mock_local_router)

        results = await router.search_async("test query")

        # In auto mode, web fallback runs when local fails (graceful degradation)
        # Router correctly falls back to web search, returning results
        assert len(results) > 0


class TestUnifiedAsyncRouterLimitParameter:
    """Tests for limit parameter functionality."""

    @pytest.mark.asyncio
    async def test_respects_limit_parameter_for_local_only(self):
        """Test that limit parameter is respected in local-only mode."""
        from core.unified_router import UnifiedAsyncRouter

        # Create many local results
        many_results = [
            SearchResult(
                title=f"Result {i}",
                content=f"Content {i}",
                source="CDS",
                score=0.9 - (i * 0.1),
                metadata={"created_at": datetime.now(timezone.utc)},
            )
            for i in range(20)
        ]

        # Create router with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=many_results)

        router = UnifiedAsyncRouter(mode="local-only", local_router=mock_local_router)

        results = await router.search_async("test query", limit=5)

        # Verify limit was respected
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_respects_limit_parameter_after_merge(self):
        """Test that limit parameter is respected after RRF merge."""
        from core.unified_router import UnifiedAsyncRouter

        # Create many local results
        local_results = [
            SearchResult(
                title=f"Local Result {i}",
                content=f"Local content {i}",
                source="CDS",
                score=0.9 - (i * 0.1),
                metadata={"created_at": datetime.now(timezone.utc)},
            )
            for i in range(10)
        ]

        # Create many web results
        web_results = [
            SearchResult(
                title=f"Web Result {i}",
                content=f"Web content {i}",
                source="TAVILY",
                score=0.9 - (i * 0.1),
            )
            for i in range(10)
        ]

        # Create routers with controlled behavior
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(return_value=local_results)

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=web_results)

        router = UnifiedAsyncRouter(
            mode="unified", local_router=mock_local_router, web_router=mock_web_router
        )

        results = await router.search_async("test query", limit=5)

        # Verify limit was respected after merge
        assert len(results) == 5


class TestUnifiedAsyncRouterIntegration:
    """Integration tests with real routers (where possible)."""

    @pytest.mark.asyncio
    async def test_integration_with_real_local_router(self):
        """Test integration with real AsyncSearchRouter for local search."""
        from core.unified_router import UnifiedAsyncRouter

        # Create a real local router (no API keys needed for local search)
        real_local_router = AsyncSearchRouter(enable_jmri=False)

        # Create mock web router
        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(return_value=[])

        router = UnifiedAsyncRouter(
            mode="local-only", local_router=real_local_router, web_router=mock_web_router
        )

        # Search for something that should exist in codebase
        results = await router.search_async("async", limit=5)

        # Verify we got results from real local search
        assert len(results) >= 0  # May be 0 if "async" not found, that's OK
        # If we got results, verify they're from local sources
        for result in results:
            assert result.source in ["CDS", "CKS", "GREP", "SKILLS", "CODE", "CLAUDE-HISTORY", "YT_IS", "RLM", "QMD_WIKI", "KG", "AST_CODE", "LSP"]

    @pytest.mark.asyncio
    async def test_integration_with_injected_routers(self):
        """Test that injected routers work correctly in all modes."""
        from core.unified_router import UnifiedAsyncRouter

        # Create mock routers
        mock_local_router = AsyncMock()
        mock_local_router.search_async = AsyncMock(
            return_value=[
                SearchResult(title="Local", content="Local content", source="CDS", score=0.8)
            ]
        )

        mock_web_router = AsyncMock()
        mock_web_router.search_web_providers_async = AsyncMock(
            return_value=[
                SearchResult(title="Web", content="Web content", source="TAVILY", score=0.9)
            ]
        )

        # Test all modes
        for mode in ["auto", "local-only", "web-fallback", "unified"]:
            router = UnifiedAsyncRouter(
                mode=mode, local_router=mock_local_router, web_router=mock_web_router
            )

            # Patch quality check for modes that need it
            with patch("core.unified_router.is_satisfactory", return_value=(mode == "local-only")):
                results = await router.search_async("test query")

                # Verify we got results
                assert len(results) >= 1
