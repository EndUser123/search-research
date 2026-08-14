"""Tests for SyncSearchWrapper backward compatibility wrapper.

These tests verify that SyncSearchWrapper provides a synchronous API
wrapping AsyncSearchRouter with asyncio.run().

Test file: tests/test_sync_wrapper.py
Run with: pytest tests/test_sync_wrapper.py -v
"""

import asyncio
from unittest.mock import patch

import pytest

from core.router_async import AsyncSearchRouter, SearchResult


class TestSyncSearchWrapperExists:
    """Tests that SyncSearchWrapper class exists and is importable."""

    def test_class_exists(self):
        """Test that SyncSearchWrapper class can be imported."""
        from core.sync_wrapper import SyncSearchWrapper

        assert SyncSearchWrapper is not None

    def test_can_instantiate(self):
        """Test that SyncSearchWrapper can be instantiated."""
        from core.sync_wrapper import SyncSearchWrapper

        wrapper = SyncSearchWrapper()
        assert wrapper is not None


class TestSyncSearchWrapperInit:
    """Tests for SyncSearchWrapper initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        from core.sync_wrapper import SyncSearchWrapper

        wrapper = SyncSearchWrapper()

        # Should have same parameters as AsyncSearchRouter
        assert hasattr(wrapper, 'enable_jmri')
        assert wrapper.enable_jmri is True  # Default value

    def test_init_with_enable_jmri_false(self):
        """Test initialization with enable_jmri=False."""
        from core.sync_wrapper import SyncSearchWrapper

        wrapper = SyncSearchWrapper(enable_jmri=False)

        assert wrapper.enable_jmri is False

    def test_init_emits_deprecation_warning(self):
        """Test that initialization emits DeprecationWarning."""
        from core.sync_wrapper import SyncSearchWrapper

        with pytest.warns(DeprecationWarning, match="SyncSearchWrapper is deprecated"):
            SyncSearchWrapper()

    def test_has_async_router_instance(self):
        """Test that wrapper creates AsyncSearchRouter instance."""
        from core.sync_wrapper import SyncSearchWrapper

        wrapper = SyncSearchWrapper()

        assert hasattr(wrapper, '_async_router')
        assert isinstance(wrapper._async_router, AsyncSearchRouter)


class TestSyncSearchWrapperSearchMethod:
    """Tests for SyncSearchWrapper.search() method."""

    def test_search_method_exists(self):
        """Test that search() method exists and is not async."""
        from core.sync_wrapper import SyncSearchWrapper

        wrapper = SyncSearchWrapper()

        assert hasattr(wrapper, 'search')
        assert callable(wrapper.search)

        # Should NOT be async function
        import inspect
        assert not inspect.iscoroutinefunction(wrapper.search)

    @patch('core.sync_wrapper.asyncio.run')
    def test_search_calls_asyncio_run(self, mock_asyncio_run):
        """Test that search() uses asyncio.run() internally."""
        from core.sync_wrapper import SyncSearchWrapper

        # Mock the return value
        mock_results = [
            SearchResult(
                title="Test Result",
                content="Test content",
                source="TEST",
                score=0.9,
            )
        ]
        mock_asyncio_run.return_value = mock_results

        wrapper = SyncSearchWrapper()
        results = wrapper.search("test query")

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
        assert results == mock_results

    @patch('core.sync_wrapper.asyncio.run')
    def test_search_returns_list_of_search_results(self, mock_asyncio_run):
        """Test that search() returns list of SearchResult objects."""
        from core.sync_wrapper import SyncSearchWrapper

        # Mock the return value
        mock_results = [
            SearchResult(
                title="Result 1",
                content="Content 1",
                source="CDS",
                score=0.95,
            ),
            SearchResult(
                title="Result 2",
                content="Content 2",
                source="GREP",
                score=0.85,
            ),
        ]
        mock_asyncio_run.return_value = mock_results

        wrapper = SyncSearchWrapper()
        results = wrapper.search("test query")

        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].title == "Result 1"
        assert results[1].source == "GREP"

    @patch('core.sync_wrapper.asyncio.run')
    def test_search_passes_query_parameter(self, mock_asyncio_run):
        """Test that search() passes query to async router."""
        from core.sync_wrapper import SyncSearchWrapper

        mock_asyncio_run.return_value = []

        wrapper = SyncSearchWrapper()
        test_query = "FastAPI patterns"
        wrapper.search(test_query)

        # Verify asyncio.run was called with a coroutine
        call_args = mock_asyncio_run.call_args
        assert call_args is not None

        # The coroutine should be the result of router.search_async()
        coroutine = call_args[0][0]
        assert asyncio.iscoroutine(coroutine)

    @patch('core.sync_wrapper.asyncio.run')
    def test_search_passes_limit_parameter(self, mock_asyncio_run):
        """Test that search() passes limit parameter."""
        from core.sync_wrapper import SyncSearchWrapper

        mock_asyncio_run.return_value = []

        wrapper = SyncSearchWrapper()
        wrapper.search("test query", limit=20)

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

    @patch('core.sync_wrapper.asyncio.run')
    def test_search_passes_backends_parameter(self, mock_asyncio_run):
        """Test that search() passes backends parameter."""
        from core.sync_wrapper import SyncSearchWrapper

        mock_asyncio_run.return_value = []

        wrapper = SyncSearchWrapper()
        wrapper.search("test query", backends=["cds", "grep"])

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()


class TestSyncSearchWrapperBackwardCompatibility:
    """Tests for backward compatibility with old AsyncSearchRouter."""

    def test_same_api_as_search_router(self):
        """Test that SyncSearchWrapper has same public API as AsyncSearchRouter."""
        from core.sync_wrapper import SyncSearchWrapper

        from core.router_async import AsyncSearchRouter

        wrapper = SyncSearchWrapper()
        router = AsyncSearchRouter()

        # Both should have search method
        assert hasattr(wrapper, 'search')
        assert hasattr(router, 'search')

        # Both should have same initialization parameters
        # (enable_jmri is the key one for backward compatibility)
        assert hasattr(wrapper, 'enable_jmri')
        assert hasattr(router, 'enable_jmri')

    @patch('core.sync_wrapper.asyncio.run')
    def test_search_returns_same_result_format(self, mock_asyncio_run):
        """Test that search() returns same format as AsyncSearchRouter."""
        from core.sync_wrapper import SyncSearchWrapper

        # Mock result that looks like AsyncSearchRouter output
        mock_results = [
            SearchResult(
                title="Function: fastapi_app",
                content="FastAPI application factory pattern",
                file_path="app.py",
                line_number=42,
                source="CDS",
                score=0.92,
                metadata={"language": "python"},
            )
        ]
        mock_asyncio_run.return_value = mock_results

        wrapper = SyncSearchWrapper()
        results = wrapper.search("test query")

        # Should return SearchResult objects like AsyncSearchRouter
        assert isinstance(results, list)
        assert len(results) == 1
        result = results[0]

        assert isinstance(result, SearchResult)
        assert result.title == "Function: fastapi_app"
        assert result.file_path == "app.py"
        assert result.line_number == 42
        assert result.source == "CDS"
        assert result.score == 0.92


class TestSyncSearchWrapperIntegration:
    """Integration tests for SyncSearchWrapper."""

    @patch('core.sync_wrapper.asyncio.run')
    def test_wraps_async_search_router(self, mock_asyncio_run):
        """Test that SyncSearchWrapper properly wraps AsyncSearchRouter."""
        from core.sync_wrapper import SyncSearchWrapper

        # Create a mock coroutine that simulates async search
        async def mock_search_async(*args, **kwargs):
            return [
                SearchResult(
                    title="Test",
                    content="Content",
                    source="TEST",
                    score=1.0,
                )
            ]

        mock_asyncio_run.side_effect = lambda coro: asyncio.run(coro)

        wrapper = SyncSearchWrapper()

        # Verify internal router is AsyncSearchRouter
        assert isinstance(wrapper._async_router, AsyncSearchRouter)

        # Verify the router has search_async method
        assert hasattr(wrapper._async_router, 'search_async')

    @patch('core.sync_wrapper.asyncio.run')
    def test_delegates_to_search_async(self, mock_asyncio_run):
        """Test that search() delegates to router.search_async()."""
        from core.sync_wrapper import SyncSearchWrapper

        mock_asyncio_run.return_value = []

        wrapper = SyncSearchWrapper()
        wrapper.search("test query", limit=10, backends=["cds"])

        # Verify asyncio.run was called (which runs search_async)
        mock_asyncio_run.assert_called_once()
