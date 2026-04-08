"""Test Claude History backend integration."""

import pytest

from core.router_async import AsyncSearchRouter


@pytest.mark.asyncio
async def test_claude_history_backend_registered():
    """Test that claude-history backend is registered in router."""
    router = AsyncSearchRouter()

    # Trigger backend initialization
    _ = router._create_backends()

    # Check that claude-history is in backends
    assert "claude-history" in router._backends, "claude-history backend should be registered"


@pytest.mark.asyncio
async def test_claude_history_backend_search():
    """Test that claude-history backend can search."""
    router = AsyncSearchRouter()

    try:
        # Try a simple search
        results = await router.search_async("test", limit=5, backends=["claude-history"])

        # Results should be a list (may be empty if no history)
        assert isinstance(results, list), "Results should be a list"

    except FileNotFoundError:
        # CLI not built - skip test
        pytest.skip("claude-history CLI not built")
    except Exception as e:
        # Other errors should fail the test
        pytest.fail(f"Search failed: {e}")


@pytest.mark.asyncio
async def test_claude_history_backend_error_handling():
    """Test that router handles claude-history backend errors gracefully."""
    router = AsyncSearchRouter()

    # If CLI doesn't exist, router should still work (just without this backend)
    # The backend initialization should fail silently
    backends = router._create_backends()

    # Router should have other backends even if claude-history fails
    assert len(backends) > 0, "Router should have at least some backends"
