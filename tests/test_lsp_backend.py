"""Auto-scaffolded test for lsp_backend."""

import pytest
from core.backends.local.lsp_backend import LSPSymbolBackend


def test_lsp_backend_build_index():
    """Regression: build_index should index symbols from a small directory."""
    backend = LSPSymbolBackend(root_paths=["core/backends/local"])
    backend.build_index()
    assert backend._indexed is True
    assert len(backend._index) > 0, "Should index symbols from core/backends/local"


# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_lsp_backend.py -v
