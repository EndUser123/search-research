#!/usr/bin/env python3
"""Tests for package import verification gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_package_import_gate import (
    _get_package_root,
    _is_package_python_file,
    _verify_imports,
)


class TestPackageImportGate:
    """Test suite for package import verification gate."""

    def test_is_package_python_file_positive(self, tmp_path):
        """Test that Python files in packages/ are detected."""
        # Create a test file in packages/
        test_file = tmp_path / "packages" / "test_pkg" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        result = _is_package_python_file(str(test_file))
        assert result is True

    def test_is_package_python_file_negative_wrong_dir(self, tmp_path):
        """Test that Python files outside packages/ are not detected."""
        test_file = tmp_path / "other_dir" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        result = _is_package_python_file(str(test_file))
        assert result is False

    def test_is_package_python_file_negative_wrong_ext(self, tmp_path):
        """Test that non-Python files are not detected."""
        test_file = tmp_path / "packages" / "test_pkg" / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        result = _is_package_python_file(str(test_file))
        assert result is False

    def test_get_package_root_finds_scripts_dir(self, tmp_path):
        """Test that package root is found when scripts/ exists."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "scripts").mkdir()

        test_file = pkg_root / "scripts" / "test.py"
        test_file.write_text("# test")

        result = _get_package_root(test_file)
        assert result == pkg_root

    def test_get_package_root_finds_hooks_dir(self, tmp_path):
        """Test that package root is found when hooks/ exists."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "hooks").mkdir()

        test_file = pkg_root / "hooks" / "test.py"
        test_file.write_text("# test")

        result = _get_package_root(test_file)
        assert result == pkg_root

    def test_get_package_root_finds_init_py(self, tmp_path):
        """Test that package root is found when __init__.py exists."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "__init__.py").write_text("# test")

        test_file = pkg_root / "test.py"
        test_file.write_text("# test")

        result = _get_package_root(test_file)
        assert result == pkg_root

    def test_verify_imports_valid_file(self, tmp_path):
        """Test import verification for a file with valid imports."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "__init__.py").write_text("# test")

        test_file = pkg_root / "test.py"
        test_file.write_text("# Valid Python file\nx = 1\n")

        success, error = _verify_imports(pkg_root, test_file)
        assert success is True
        assert error == ""

    def test_verify_imports_broken_import(self, tmp_path):
        """Test import verification for a file with broken imports."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "__init__.py").write_text("# test")

        test_file = pkg_root / "test.py"
        # File with a deliberately broken import
        test_file.write_text("from nonexistent_module import DoesNotExist\n")

        success, error = _verify_imports(pkg_root, test_file)
        assert success is False
        assert "ImportError" in error or "ModuleNotFoundError" in error

    def test_run_gate_allows_non_python_files(self, tmp_path):
        """Test that gate allows non-Python files without checking."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_file)},
            "content": "test",
        }

        result = _run_gate_under_test(data, packages_root_override=tmp_path)
        assert result is None  # Should allow

    def test_run_gate_allows_python_files_outside_packages(self, tmp_path):
        """Test that gate allows Python files outside packages/."""
        test_file = tmp_path / "other_dir" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_file)},
            "content": "# test",
        }

        result = _run_gate_under_test(data, packages_root_override=tmp_path)
        assert result is None  # Should allow

    def test_run_gate_blocks_broken_imports(self, tmp_path):
        """Test that gate blocks files with broken imports."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "__init__.py").write_text("# test")

        test_file = pkg_root / "test.py"
        test_file.write_text("from nonexistent import Broken\n")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_file)},
            "content": "from nonexistent import Broken\n",
            "transcript": [{"content": "create test file"}],
        }

        result = _run_gate_under_test(data, packages_root_override=tmp_path)
        assert result is not None  # Should block
        assert result["continue"] is False
        assert "BROKEN IMPORTS" in result["reason"]

    def test_run_gate_allows_with_bypass_flag(self, tmp_path):
        """Test that bypass flag allows broken imports."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "__init__.py").write_text("# test")

        test_file = pkg_root / "test.py"
        test_file.write_text("from nonexistent import Broken\n")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_file)},
            "content": "from nonexistent import Broken\n",
            "transcript": [{"content": "create test file --allow-broken-imports"}],
        }

        result = _run_gate_under_test(data, packages_root_override=tmp_path)
        assert result is None  # Should allow due to bypass flag

    def test_run_gate_allows_read_operations(self, tmp_path):
        """Test that Read operations are not blocked."""
        data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "test.py"},
        }

        result = _run_gate_under_test(data, packages_root_override=tmp_path)
        assert result is None  # Should allow

    def test_run_gate_checks_edit_operations(self, tmp_path):
        """Test that Edit operations are checked."""
        pkg_root = tmp_path / "packages" / "test_pkg"
        pkg_root.mkdir(parents=True)
        (pkg_root / "__init__.py").write_text("# test")

        test_file = pkg_root / "test.py"
        test_file.write_text("# initial\n")
        test_file.touch()

        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(test_file)},
            "transcript": [{"content": "edit test"}],
        }

        result = _run_gate_under_test(data, packages_root_override=tmp_path)
        # Edit on existing file with valid content should not block
        # (We can't easily test the actual edit content, so this tests the path)
        assert result is None or "BROKEN IMPORTS" in result.get("reason", "")


def _run_gate_under_test(data: dict, packages_root_override: Path | None = None) -> dict | None:
    """Helper to run the gate in test context."""
    import PreToolUse_package_import_gate as gate_module
    original_root = gate_module.PACKAGES_ROOT

    try:
        if packages_root_override:
            gate_module.PACKAGES_ROOT = packages_root_override
        return gate_module.run(data)
    finally:
        gate_module.PACKAGES_ROOT = original_root


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
