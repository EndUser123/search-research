#!/usr/bin/env python3
"""Tests for type_validator.py - Type-based whitelist validation.

Tests the three-layer validation architecture for cleanup violation detection:
- Phase 1: Type-Based Validation (this module)
- Phase 2: Optimal Location Inference (location_optimizer.py)
- Phase 3: Whitelist Bypass Prevention (integrated in cleanup workflow)
"""

import json
import tempfile
from pathlib import Path

import pytest
from __lib.type_validator import (
    check_file_type_violations,
    get_file_category,
    validate_all_policy_types,
    validate_config_whitelist_entries,
    validate_python_whitelist_entries,
)


class TestFileCategorization:
    """Test file categorization by extension."""

    def test_python_file_category(self):
        """Python files (.py, .pyi) are categorized correctly."""
        assert get_file_category("module.py") == "python"
        assert get_file_category("module.pyi") == "python"
        assert get_file_category("test_module.py") == "python"

    def test_config_file_category(self):
        """Configuration files are categorized correctly."""
        assert get_file_category("config.toml") == "config"
        assert get_file_category("setup.cfg") == "config"
        assert get_file_category("pyproject.toml") == "config"
        assert get_file_category(".env.example") == "config"
        # Note: README.md is categorized as "doc", not "config" (docs come before configs)

    def test_doc_file_category(self):
        """Documentation files are categorized correctly."""
        assert get_file_category("docs.md") == "doc"
        assert get_file_category("README.rst") == "doc"
        assert get_file_category("CHANGES.txt") == "doc"

    def test_cache_file_category(self):
        """Cache patterns are categorized correctly."""
        # Note: .pytest_cache is a directory name, returns "unknown" (cache check works for file extensions like .pyc)
        assert get_file_category("module.pyc") == "cache"
        assert get_file_category("module.pyo") == "cache"

    def test_unknown_file_category(self):
        """Unknown extensions return 'unknown' category."""
        assert get_file_category("data.bin") == "unknown"
        assert get_file_category("image.jpg") == "unknown"


class TestConfigWhitelistValidation:
    """Test validation of config whitelist entries."""

    def test_python_file_in_config_whitelist_fails(self):
        """Python modules in config whitelist should fail validation."""
        test_whitelist = ["pyproject.toml", "Stop_behavior_gates.py", "README.md"]

        errors = validate_config_whitelist_entries("test_config", test_whitelist)

        assert len(errors) == 1
        assert errors[0].file_path == "Stop_behavior_gates.py"
        assert errors[0].expected_type == "config file"
        assert errors[0].actual_type == "Python module (.py)"

    def test_setup_py_with_setuptools_imports_passes(self):
        """setup.py with setuptools imports is valid in config whitelist."""
        # Create a temporary setup.py with setuptools imports
        with tempfile.NamedTemporaryFile(mode="w", suffix="setup.py", delete=False) as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("from setuptools import setup\n")
            f.write("setup(\n")
            f.write('    name="test-package",\n')
            f.write('    version="1.0.0",\n')
            f.write(")\n")
            temp_setup = f.name

        try:
            # This should NOT be flagged as an error (has setuptools)
            test_whitelist = ["pyproject.toml", temp_setup, "README.md"]
            errors = validate_config_whitelist_entries("test_config", test_whitelist)

            # setup.py with setuptools should not error
            setup_errors = [e for e in errors if e.file_path == temp_setup]
            assert len(setup_errors) == 0, (
                f"setup.py with setuptools should be valid, got: {setup_errors}"
            )

        finally:
            Path(temp_setup).unlink(missing_ok=True)

    def test_setup_py_without_setuptools_fails(self):
        """setup.py without setuptools imports should fail validation."""
        # Create a temporary setup.py WITHOUT setuptools imports
        with tempfile.NamedTemporaryFile(mode="w", suffix="setup.py", delete=False) as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# This is a module setup.py, not a package\n")
            f.write("def main():\n")
            f.write('    print("Not a package setup")\n')
            temp_setup = f.name

        try:
            test_whitelist = ["pyproject.toml", temp_setup, "README.md"]
            errors = validate_config_whitelist_entries("test_config", test_whitelist)

            # setup.py without setuptools SHOULD error
            setup_errors = [e for e in errors if e.file_path == temp_setup]
            assert len(setup_errors) == 1, "setup.py without setuptools should be flagged"

        finally:
            Path(temp_setup).unlink(missing_ok=True)

    def test_wildcard_patterns_skip_validation(self):
        """Wildcard patterns in whitelist skip validation."""
        test_whitelist = ["*.toml", "test_*.py", "*.md"]

        errors = validate_config_whitelist_entries("test_config", test_whitelist)

        # Wildcard patterns should be skipped
        assert len(errors) == 0


class TestPythonWhitelistValidation:
    """Test validation of Python-specific whitelist entries."""

    def test_config_file_in_python_whitelist_fails(self):
        """Config files in Python whitelist should fail validation."""
        test_whitelist = ["module.py", "config.toml", "test.py"]

        errors = validate_python_whitelist_entries("test_python", test_whitelist)

        assert len(errors) == 1
        assert errors[0].file_path == "config.toml"
        assert errors[0].expected_type == "Python file"

    def test_doc_file_in_python_whitelist_fails(self):
        """Documentation files in Python whitelist should fail validation."""
        test_whitelist = ["module.py", "docs.md", "test.py"]

        errors = validate_python_whitelist_entries("test_python", test_whitelist)

        assert len(errors) == 1
        assert errors[0].file_path == "docs.md"
        assert errors[0].expected_type == "Python file"

    def test_wildcard_patterns_skip_validation(self):
        """Wildcard patterns in whitelist skip validation."""
        test_whitelist = ["module.py", "*.toml", "test_*.py"]

        errors = validate_python_whitelist_entries("test_python", test_whitelist)

        # Wildcard patterns should be skipped
        assert len(errors) == 0


class TestCheckFileTypeViolations:
    """Test violation checking for specific files."""

    def test_python_file_in_config_whitelist_violation(self):
        """Check that .py file in config whitelist is detected as violation."""
        # Create a mock policy
        mock_policy = {
            "workspace_root": {"allowed_config_files": ["pyproject.toml", "Stop_behavior_gates.py"]}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mock_policy, f)
            policy_path = f.name

        try:
            # Note: check_file_type_violations uses path.name for matching, so pass filename only
            violations = check_file_type_violations("Stop_behavior_gates.py", policy_path)

            assert len(violations) == 1
            assert violations[0]["type"] == "TYPE_MISMATCH_CONFIG_WHITELIST"
            assert "Stop_behavior_gates.py" in violations[0]["message"]

        finally:
            Path(policy_path).unlink(missing_ok=True)


class TestValidateAllPolicyTypes:
    """Test validation of complete directory_policy.json."""

    def test_validate_policy_with_invalid_entries(self):
        """Test validation of policy with invalid whitelist entries."""
        # Create a mock policy with a .py file in config whitelist
        mock_policy = {
            "workspace_root": {"allowed_config_files": ["pyproject.toml", "invalid_module.py"]}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mock_policy, f)
            policy_path = f.name

        try:
            result = validate_all_policy_types(policy_path)

            # Should return errors for the invalid .py file
            assert "workspace_root.allowed_config_files" in result
            assert len(result["workspace_root.allowed_config_files"]) > 0

        finally:
            Path(policy_path).unlink(missing_ok=True)

    def test_validate_policy_missing_file(self):
        """Test validation when policy file doesn't exist."""
        result = validate_all_policy_types("nonexistent_policy.json")

        assert "error" in result
        assert len(result["error"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
