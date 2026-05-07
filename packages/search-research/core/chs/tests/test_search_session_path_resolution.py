"""Tests for SearchSession path resolution (CWD-independence).

These tests verify that _find_cks_database uses config.CKS_DB_PATH as the
authoritative source of truth and does NOT fall back to cwd-dependent paths.

Run: pytest P:\\\\packages/search-research/core/chs/tests/test_search_session_path_resolution.py -v
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import directly to bypass __init__.py which imports modules requiring sentence_transformers
# __file__ = P:\\\\packages/search-research/core/chs/tests/test_xxx.py
# parents[0] = tests/, parents[1] = chs/, parents[2] = core/, parents[3] = search-research/
project_root = Path(__file__).resolve().parents[3]  # P:\\\\packages/search-research
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module file directly, not through the package __init__
import importlib.util

_session_spec = importlib.util.spec_from_file_location(
    "search_session",
    project_root / "core" / "chs" / "search_session.py"
)
_session_module = importlib.util.module_from_spec(_session_spec)
_session_spec.loader.exec_module(_session_module)
SearchSession = _session_module.SearchSession
SearchSessionManager = _session_module.SearchSessionManager


class TestFindCksDatabaseCwdIndependence:
    """Test that _find_cks_database is CWD-independent."""

    def test_candidates_list_does_not_include_cwd_relative_paths(self):
        """Regression: verify no relative paths like 'data/cks.db' remain."""
        import inspect

        source = inspect.getsource(SearchSession._find_cks_database)

        # These patterns would indicate cwd-dependent path resolution
        cwd_dependent_patterns = [
            "Path.cwd()",
            "Path(__file__).parent.parent.parent.parent",
            '"/data/cks.db"',
            "'/data/cks.db'",
            '"data/cks.db"',
            "'data/cks.db'",
            '".data/cks.db"',
            "'data/cks.db'",
        ]

        found_cwd_dependent = []
        for pattern in cwd_dependent_patterns:
            if pattern in source:
                found_cwd_dependent.append(pattern)

        assert not found_cwd_dependent, (
            f"_find_cks_database contains cwd-dependent patterns: {found_cwd_dependent}. "
            f"Path resolution should use config.CKS_DB_PATH, not relative paths."
        )

    def test_uses_config_cks_db_path_from_config_module(self):
        """Verify _find_cks_database imports from core.config."""
        import inspect

        source = inspect.getsource(SearchSession._find_cks_database)

        # Should reference config.CKS_DB_PATH or equivalent
        assert "config" in source.lower() or "CKS_DB_PATH" in source, (
            "_find_cks_database should reference config.CKS_DB_PATH as authoritative source. "
            f"Current source does not mention config: {source[:200]}..."
        )

    def test_exports_to_cks_uses_find_cks_database(self):
        """Regression: verify export_to_cks calls _find_cks_database when no path given."""
        import inspect

        export_source = inspect.getsource(SearchSession.export_to_cks)

        # export_to_cks should call _find_cks_database when cks_db_path is None
        assert "_find_cks_database" in export_source, (
            "export_to_cks should delegate to _find_cks_database for path resolution"
        )


class TestSearchSessionManagerStorageDir:
    """Test that SearchSessionManager uses a non-CWD storage directory."""

    def test_storage_dir_defaults_to_temp(self):
        """Verify storage dir is in tempfile, not cwd."""
        manager = SearchSessionManager()

        # Storage dir should be in temp directory, not cwd
        assert str(Path(tempfile.gettempdir())) in str(manager.storage_dir), (
            f"Storage dir should be in temp directory, not cwd. Got: {manager.storage_dir}"
        )