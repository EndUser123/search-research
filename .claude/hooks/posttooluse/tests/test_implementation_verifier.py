#!/usr/bin/env python3
"""
ImplementationVerifier Hook Tests

Tests for the PostToolUse hook that verifies Write/Edit operations
actually create claimed files on disk.

Test Strategy (TDD RED → GREEN → REFACTOR):
- RED: Write these tests first, watch them fail
- GREEN: Implement ImplementationVerifier to make tests pass
- REFACTOR: Clean up implementation while tests still pass
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import real implementation for GREEN phase testing
from posttooluse.implementation_verifier import ImplementationVerifier


class TestImplementationVerifierInterface:
    """Tests for PostToolUseHook interface compliance."""

    def test_env_var_defined(self):
        """Hook should have IMPLEMENTATION_VERIFIER_ENABLED env_var."""
        hook = ImplementationVerifier()
        assert hook.env_var == "IMPLEMENTATION_VERIFIER_ENABLED"

    def test_default_enabled(self):
        """Hook should be enabled by default."""
        hook = ImplementationVerifier()
        assert hook.default_enabled is True

    def test_tool_matcher_write_and_edit(self):
        """Hook should match Write and Edit tools."""
        hook = ImplementationVerifier()
        assert hook.tool_matcher == {"Write", "Edit"}

    def test_matches_tool_write(self):
        """Hook should match Write tool."""
        hook = ImplementationVerifier()
        assert hook.matches_tool("Write") is True

    def test_matches_tool_edit(self):
        """Hook should match Edit tool."""
        hook = ImplementationVerifier()
        assert hook.matches_tool("Edit") is True

    def test_does_not_match_other_tools(self):
        """Hook should not match other tools like Read."""
        hook = ImplementationVerifier()
        assert hook.matches_tool("Read") is False
        assert hook.matches_tool("Grep") is False


class TestImplementationVerifierFileExistence:
    """Tests for file existence verification logic."""

    def test_file_exists_after_write(self):
        """
        SCENARIO: Write tool creates a file that exists on disk.
        EXPECTED: Hook passes verification.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")

            hook = ImplementationVerifier()
            tool_input = {"file_path": str(test_file)}
            result = hook.process("Write", tool_input, {})

            # This should pass - file exists
            assert result["passed"] is True

    def test_file_not_created_after_write(self):
        """
        SCENARIO: Write tool claims to write file but file doesn't exist.
        EXPECTED: Hook blocks with warning injection.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "does_not_exist.txt"

            hook = ImplementationVerifier()
            tool_input = {"file_path": str(nonexistent)}
            result = hook.process("Write", tool_input, {})

            # This SHOULD fail but fake implementation returns passed=True
            # This test will fail in RED phase, forcing correct implementation
            assert result["passed"] is False, "Expected hook to fail when file doesn't exist"
            assert "injection" in result, "Expected warning injection for missing file"

    def test_file_exists_after_edit(self):
        """
        SCENARIO: Edit tool modifies a file that exists on disk.
        EXPECTED: Hook passes verification.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("original content")

            hook = ImplementationVerifier()
            tool_input = {"file_path": str(test_file)}
            result = hook.process("Edit", tool_input, {})

            # This should pass - file exists
            assert result["passed"] is True

    def test_file_not_found_after_edit(self):
        """
        SCENARIO: Edit tool claims to edit file but file doesn't exist.
        EXPECTED: Hook blocks with warning injection.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "does_not_exist.txt"

            hook = ImplementationVerifier()
            tool_input = {"file_path": str(nonexistent)}
            result = hook.process("Edit", tool_input, {})

            # This SHOULD fail but fake implementation returns passed=True
            assert result["passed"] is False, "Expected hook to fail when file doesn't exist"
            assert "injection" in result, "Expected warning injection for missing file"

    def test_no_file_path_in_tool_input(self):
        """
        SCENARIO: Tool input has no file_path field.
        EXPECTED: Hook passes (skip verification gracefully).
        """
        hook = ImplementationVerifier()
        tool_input = {}  # No file_path
        result = hook.process("Write", tool_input, {})

        # Should pass - nothing to verify
        assert result["passed"] is True


class TestImplementationVerifierDisabled:
    """Tests for hook disable functionality."""

    def test_hook_disabled_by_env_var(self):
        """
        SCENARIO: IMPLEMENTATION_VERIFIER_ENABLED=false
        EXPECTED: Hook is disabled and doesn't verify.
        """
        # Set env var to disable
        os.environ["IMPLEMENTATION_VERIFIER_ENABLED"] = "false"

        hook = ImplementationVerifier()
        enabled = hook._check_enabled()

        # Should be disabled
        assert enabled is False

        # Clean up
        del os.environ["IMPLEMENTATION_VERIFIER_ENABLED"]


class TestImplementationVerifierEdgeCases:
    """Tests for edge cases and error handling."""

    def test_filePath_variant_accepted(self):
        """
        SCENARIO: Tool input uses 'filePath' (camelCase) instead of 'file_path'.
        EXPECTED: Hook accepts both variants.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")

            hook = ImplementationVerifier()
            tool_input = {"filePath": str(test_file)}  # camelCase variant
            result = hook.process("Write", tool_input, {})

            # Should handle camelCase variant
            assert result["passed"] is True

    def test_relative_path_accepted(self):
        """
        SCENARIO: Tool input uses relative path.
        EXPECTED: Hook resolves relative to current directory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file in temp dir
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")

            # Change to temp dir so relative path works
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                hook = ImplementationVerifier()
                tool_input = {"file_path": "test.txt"}  # relative path
                result = hook.process("Write", tool_input, {})

                # Should handle relative path
                assert result["passed"] is True
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v"])
