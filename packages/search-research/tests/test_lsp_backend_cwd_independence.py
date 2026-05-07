"""Tests for LSPSymbolBackend path resolution (CWD-independence).

These tests verify that the LSP backend defaults to an absolute path anchored
to the package location, not relative to process CWD.

Run: pytest P:\\\\packages/search-research/tests/test_lsp_backend_cwd_independence.py -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Import directly to bypass __init__.py which imports modules requiring sentence_transformers
# __file__ = P:\\\\packages/search-research/tests/test_xxx.py
# parents[0] = tests/, parents[1] = search-research/, parents[2] = packages/
project_root = Path(__file__).resolve().parents[1]  # P:\\\\packages/search-research
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module file directly, not through the package __init__
import importlib.util

_lsp_spec = importlib.util.spec_from_file_location(
    "lsp_backend",
    project_root / "core" / "backends" / "local" / "lsp_backend.py"
)
_lsp_module = importlib.util.module_from_spec(_lsp_spec)
_lsp_spec.loader.exec_module(_lsp_module)
LSPSymbolBackend = _lsp_module.LSPSymbolBackend


class TestLSPSymbolBackendCwdIndependence:
    """Test that LSPSymbolBackend is CWD-independent."""

    def test_default_root_paths_are_absolute(self):
        """Regression: default root_paths should be absolute, not relative to cwd."""
        backend = LSPSymbolBackend()  # No root_paths → uses default

        assert backend._indexed is False  # Not yet built

        # All root_paths must be absolute (start with drive letter on Windows or / on Unix)
        for root in backend.root_paths:
            assert root.is_absolute(), (
                f"LSPSymbolBackend default root '{root}' is NOT absolute. "
                f"It will resolve relative to CWD in shared mode. "
                f"Expected path anchored to package root."
            )

    def test_default_root_paths_point_to_package_core(self):
        """Verify default resolves to P:\\\\packages/search-research/core."""
        expected = project_root / "core"
        backend = LSPSymbolBackend()

        # Should resolve to the 'core' subdirectory of the search-research package
        assert len(backend.root_paths) == 1
        assert backend.root_paths[0] == expected, (
            f"Expected default root to be {expected}, got {backend.root_paths[0]}"
        )

    def test_explicit_relative_paths_still_work(self):
        """Verify that explicit root_paths (relative or absolute) still work."""
        # Explicit absolute path should work
        backend_abs = LSPSymbolBackend(root_paths=[str(project_root / "core" / "backends" / "local")])
        assert len(backend_abs.root_paths) == 1
        assert backend_abs.root_paths[0].is_absolute()

        # Explicit relative path should also work (user responsibility)
        backend_rel = LSPSymbolBackend(root_paths=["core/backends/local"])
        assert len(backend_rel.root_paths) == 1

    def test_no_path_cwd_in_source(self):
        """Regression: verify no Path.cwd() in LSPSymbolBackend.__init__."""
        import inspect

        source = inspect.getsource(LSPSymbolBackend.__init__)

        assert "Path.cwd()" not in source, (
            "LSPSymbolBackend.__init__ contains Path.cwd() which causes "
            "CWD-dependent behavior in shared mode."
        )

        # Also check the module-level source
        module_source = inspect.getsource(_lsp_module)
        assert "Path.cwd()" not in module_source


class TestLSPBackendNoCwdDependency:
    """Verify LSP backend behavior across different CWD scenarios."""

    def test_backend_behaves_same_from_different_cwds(self, tmp_path):
        """Regression: LSP backend root resolution should NOT change when CWD changes."""
        # Get expected path (anchored to package)
        expected_root = project_root / "core"

        # Simulate different CWDs
        original_cwd = os.getcwd()

        try:
            # CWD = temp directory (not the project)
            os.chdir(tmp_path)
            backend = LSPSymbolBackend()

            # The root should still resolve to the package, not the temp dir
            assert len(backend.root_paths) == 1
            assert backend.root_paths[0] == expected_root, (
                f"LSP backend resolved to {backend.root_paths[0]} when CWD={tmp_path}. "
                f"Expected {expected_root}. Default path resolution is CWD-dependent!"
            )
        finally:
            os.chdir(original_cwd)