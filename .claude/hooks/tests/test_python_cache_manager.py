#!/usr/bin/env python3
"""
Tests for python_cache_manager module
"""

# Add __lib to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

import python_cache_manager


class TestClearPackageCache:
    """Tests for clear_package_cache() function."""

    def test_clears_pycache_directories(self, tmp_path):
        """Test that __pycache__ directories are removed."""
        # Create test package structure with __pycache__
        pkg = tmp_path / "test_package"
        pkg.mkdir()
        (pkg / "__pycache__").mkdir()
        (pkg / "__pycache__" / "test.pyc").touch()

        # Create nested __pycache__
        nested = pkg / "submodule"
        nested.mkdir()
        (nested / "__pycache__").mkdir()
        (nested / "__pycache__" / "nested.pyc").touch()

        # Clear cache
        result = python_cache_manager.clear_package_cache(pkg)

        # Verify __pycache__ directories removed
        assert result["cleared_count"] == 2
        assert not (pkg / "__pycache__").exists()
        assert not (nested / "__pycache__").exists()
        assert len(result["paths_cleared"]) == 2
        assert len(result["errors"]) == 0

    def test_clears_pyc_files(self, tmp_path):
        """Test that .pyc files are removed."""
        # Create test package with .pyc files
        pkg = tmp_path / "test_package"
        pkg.mkdir()
        (pkg / "module.pyc").touch()
        (pkg / "test.pyc").touch()

        # Clear cache
        result = python_cache_manager.clear_package_cache(pkg)

        # Verify .pyc files removed
        assert result["cleared_count"] == 2
        assert not (pkg / "module.pyc").exists()
        assert not (pkg / "test.pyc").exists()

    def test_handles_nonexistent_path(self):
        """Test that nonexistent path returns error."""
        result = python_cache_manager.clear_package_cache("/nonexistent/path")

        assert result["cleared_count"] == 0
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()

    def test_handles_source_files_only(self, tmp_path):
        """Test that source .py files are never deleted."""
        # Create package with only source files (no cache)
        pkg = tmp_path / "test_package"
        pkg.mkdir()
        (pkg / "module.py").touch()
        (pkg / "main.py").touch()

        # Clear cache
        result = python_cache_manager.clear_package_cache(pkg)

        # Verify source files preserved
        assert result["cleared_count"] == 0
        assert (pkg / "module.py").exists()
        assert (pkg / "main.py").exists()


class TestPreInstallCacheClean:
    """Tests for pre_install_cache_clean() function."""

    def test_returns_true_on_success(self, tmp_path, capsys):
        """Test that successful cache cleanup returns True and prints message."""
        # Create package with cache
        pkg = tmp_path / "test_package"
        pkg.mkdir()
        (pkg / "__pycache__").mkdir()

        # Clean cache
        result = python_cache_manager.pre_install_cache_clean(pkg)

        # Verify return value and output
        assert result is True
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "cache items" in captured.out.lower()

    def test_returns_false_on_error(self, capsys):
        """Test that failed cache cleanup returns False and prints error."""
        # Use nonexistent path
        result = python_cache_manager.pre_install_cache_clean("/nonexistent")

        # Verify return value and error output
        assert result is False
        captured = capsys.readouterr()
        assert "ERROR" in captured.err  # Errors go to stderr, not stdout

    def test_silent_when_no_cache_found(self, tmp_path, capsys):
        """Test that no output when no cache exists."""
        # Create package without cache
        pkg = tmp_path / "test_package"
        pkg.mkdir()

        # Clean cache
        result = python_cache_manager.pre_install_cache_clean(pkg)

        # Verify success but no message (nothing to clear)
        assert result is True
        captured = capsys.readouterr()
        assert "✓" not in captured.out  # No message when nothing cleared
