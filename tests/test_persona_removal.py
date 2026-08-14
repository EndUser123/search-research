"""Tests for Persona Memory removal from search-research."""

from search_research import AsyncSearchRouter


def test_persona_backend_not_in_router():
    """Persona Memory backend should NOT be initialized in router."""
    router = AsyncSearchRouter()

    # Persona backend should NOT be in backends
    assert "persona" not in router._backends, (
        "Persona backend should be removed from router._backends"
    )


def test_persona_not_exported_from_local():
    """Persona Memory classes should NOT be exported from local backends."""
    from backends import local

    # These should NOT be exported after removal
    assert not hasattr(local, 'BACKEND_PERSONA'), (
        "BACKEND_PERSONA constant should be removed"
    )
    assert not hasattr(local, 'PersonaMemoryBackend'), (
        "PersonaMemoryBackend class should be removed"
    )
    assert not hasattr(local, 'create_persona_backend'), (
        "create_persona_backend function should be removed"
    )
