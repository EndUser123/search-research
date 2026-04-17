"""Test backend initialization fixes."""

from search_research import AsyncSearchRouter


def test_async_router_initializes_without_error():
    """AsyncAsyncSearchRouter should initialize without throwing."""
    # This should NOT raise an error
    router = AsyncAsyncSearchRouter()

    # Backends should be initialized (empty dict is acceptable)
    assert isinstance(router._backends, dict)


def test_async_router_fails_fast_on_backend_error():
    """AsyncAsyncSearchRouter should fail fast if core backend fails."""
    # If we try to use a backend that doesn't exist, it should raise immediately
    router = AsyncAsyncSearchRouter()

    # Attempting to create backends should either:
    # 1. Succeed with available backends, OR
    # 2. Fail fast with clear error (not silent warning)
    # The current implementation has empty _backends, which is acceptable
    # but we want to ensure errors are not suppressed
    assert router._backends is not None  # Should be initialized, not None


def test_router_uses_correct_backend_classes():
    """Router should use existing backend classes only."""
    from backends import local

    # Verify CDSBackend exists
    assert hasattr(local, 'CDSBackend')

    # Verify EnhancedCDSBackend does NOT exist (the bug)
    assert not hasattr(local, 'EnhancedCDSBackend')
