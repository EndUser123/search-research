"""Auto-scaffolded test for ast_code_backend."""

import pytest
from pathlib import Path

from core.backends.local.ast_code_backend import ASTCodeBackend


def test_ast_code_backend_default_root_path():
    """Regression: default root path should be "." (current dir), not a hardcoded non-existent path."""
    backend = ASTCodeBackend()  # Uses default root path
    assert backend.root_paths == [Path(".")], f"Default should be ['.'], got {backend.root_paths}"
    backend.build_index()
    assert backend._indexed is True
    assert len(backend._entity_index) > 0, "Should index entities with default root path"


# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_ast_code_backend.py -v
