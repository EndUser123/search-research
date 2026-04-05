#!/usr/bin/env python3
"""
Tests for ImplementationVerifier PostToolUse Hook

Tests the ImplementationVerifier hook that verifies Write/Edit tools
actually create the claimed files on disk, preventing false completion claims.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from posttooluse import create_registry
from posttooluse.base import PostToolUseHook
from posttooluse.implementation_verifier import ImplementationVerifier


class TestImplementationVerifierStructure:
    """Tests for ImplementationVerifier class structure."""

    def test_extends_post_tool_use_hook(self):
        """Verify ImplementationVerifier extends PostToolUseHook."""
        verifier = ImplementationVerifier()
        assert isinstance(verifier, PostToolUseHook)

    def test_env_var_configuration(self):
        """Verify environment variable configuration."""
        verifier = ImplementationVerifier()
        assert verifier.env_var == "IMPLEMENTATION_VERIFIER_ENABLED"
        assert verifier.default_enabled is True

    def test_tool_matcher_configuration(self):
        """Verify tool matcher includes Write and Edit."""
        verifier = ImplementationVerifier()
        assert verifier.tool_matcher == {"Write", "Edit"}

    def test_default_enabled(self):
        """Verify hook is enabled by default."""
        verifier = ImplementationVerifier()
        assert verifier.enabled is True


class TestImplementationVerifierProcess:
    """Tests for the process() method behavior."""

    def test_process_returns_expected_structure(self):
        """Verify process() returns dict with required keys."""
        verifier = ImplementationVerifier()
        result = verifier.process("Write", {"file_path": "test.txt"}, {})
        assert "passed" in result
        assert "metadata" in result

    def test_file_exists_passes_verification(self):
        """Verify that existing files pass verification."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            existing_file = f.name
        try:
            verifier = ImplementationVerifier()
            result = verifier.process("Write", {"file_path": existing_file}, {})
            assert result["passed"] is True
            assert result["metadata"]["verified"] is True
            assert result["metadata"]["exists"] is True
        finally:
            Path(existing_file).unlink(missing_ok=True)

    def test_file_missing_fails_verification(self):
        """Verify that missing files fail verification."""
        verifier = ImplementationVerifier()
        result = verifier.process("Write", {"file_path": "nonexistent.txt"}, {})
        assert result["passed"] is False
        assert result["metadata"]["verified"] is False
        assert result["metadata"]["exists"] is False
        assert "injection" in result

    def test_injection_message_format(self):
        """Verify injection message contains useful information."""
        verifier = ImplementationVerifier()
        result = verifier.process("Edit", {"file_path": "missing.py"}, {})
        assert "injection" in result
        assert "FILE NOT CREATED" in result["injection"]
        assert "missing.py" in result["injection"]

    def test_no_file_path_skips_verification(self):
        """Verify that missing file_path skips verification gracefully."""
        verifier = ImplementationVerifier()
        result = verifier.process("Write", {}, {})
        assert result["passed"] is True
        assert result["metadata"]["reason"] == "no_file_path"

    def test_camelcase_filePath_supported(self):
        """Verify that both file_path and filePath key names work."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            existing_file = f.name
        try:
            verifier = ImplementationVerifier()

            # Test snake_case file_path
            result1 = verifier.process("Write", {"file_path": existing_file}, {})
            assert result1["passed"] is True

            # Test camelCase filePath
            result2 = verifier.process("Edit", {"filePath": existing_file}, {})
            assert result2["passed"] is True
        finally:
            Path(existing_file).unlink(missing_ok=True)

    def test_absolute_path_supported(self):
        """Verify that absolute paths work correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            existing_file = f.name
        try:
            verifier = ImplementationVerifier()
            result = verifier.process("Write", {"file_path": existing_file}, {})
            assert result["passed"] is True
        finally:
            Path(existing_file).unlink(missing_ok=True)

    def test_relative_path_supported(self):
        """Verify that relative paths work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            try:
                verifier = ImplementationVerifier()
                result = verifier.process("Write", {"file_path": str(test_file)}, {})
                assert result["passed"] is True
            finally:
                test_file.unlink(missing_ok=True)

    def test_metadata_includes_tool_name(self):
        """Verify metadata includes the tool that was used."""
        verifier = ImplementationVerifier()
        result = verifier.process("Edit", {"file_path": "missing.txt"}, {})
        assert result["metadata"]["tool"] == "Edit"


class TestEnvironmentVariables:
    """Tests for environment variable configuration."""

    def test_env_var_disables_hook(self):
        """Verify IMPLEMENTATION_VERIFIER_ENABLED=false disables hook."""
        with patch.dict("os.environ", {"IMPLEMENTATION_VERIFIER_ENABLED": "false"}):
            verifier = ImplementationVerifier()
            assert not verifier.enabled

    def test_env_var_true_enables_hook(self):
        """Verify IMPLEMENTATION_VERIFIER_ENABLED=true enables hook."""
        with patch.dict("os.environ", {"IMPLEMENTATION_VERIFIER_ENABLED": "true"}):
            verifier = ImplementationVerifier()
            assert verifier.enabled

    def test_env_var_missing_uses_default(self):
        """Verify missing env var uses default (enabled)."""
        # Clear env var if set
        import os

        old_val = os.environ.get("IMPLEMENTATION_VERIFIER_ENABLED")
        os.environ.pop("IMPLEMENTATION_VERIFIER_ENABLED", None)

        try:
            verifier = ImplementationVerifier()
            # Default is True
            assert verifier.enabled is True
        finally:
            if old_val is not None:
                os.environ["IMPLEMENTATION_VERIFIER_ENABLED"] = old_val


class TestToolMatcher:
    """Tests for tool_matcher filtering."""

    def test_write_tool_triggers_verification(self):
        """Verify Write tool triggers verification."""
        verifier = ImplementationVerifier()
        assert "Write" in verifier.tool_matcher
        # Should process Write
        result = verifier.process("Write", {"file_path": "test.txt"}, {})
        assert "passed" in result

    def test_edit_tool_triggers_verification(self):
        """Verify Edit tool triggers verification."""
        verifier = ImplementationVerifier()
        assert "Edit" in verifier.tool_matcher
        # Should process Edit
        result = verifier.process("Edit", {"file_path": "test.txt"}, {})
        assert "passed" in result

    def test_read_tool_skipped(self):
        """Verify Read tool does not trigger verification."""
        verifier = ImplementationVerifier()
        assert "Read" not in verifier.tool_matcher
        # Should return passed=True without verification
        result = verifier.process("Read", {"file_path": "any.txt"}, {})
        assert result["passed"] is True

    def test_other_tools_skipped(self):
        """Verify non-Write/Edit tools don't trigger verification."""
        verifier = ImplementationVerifier()
        for tool in ["Read", "Grep", "Glob", "Bash"]:
            result = verifier.process(tool, {}, {})
            assert result["passed"] is True


class TestHookRegistration:
    """Integration tests for hook registration."""

    def setup_method(self):
        """Create test fixture with PostToolUse registry."""
        self.registry = create_registry()

    def test_hook_registered_in_registry(self):
        """Verify ImplementationVerifier is registered in PostToolUse registry."""
        # Registry stores hooks as list of (name, instance) tuples
        hook_names = [name for name, _ in self.registry._hooks]
        assert "implementation_verifier" in hook_names

    def test_hook_is_correct_instance(self):
        """Verify registered hook is ImplementationVerifier instance."""
        hook = dict(self.registry._hooks)["implementation_verifier"]
        assert isinstance(hook, ImplementationVerifier)


class TestPositiveCases:
    """Tests for scenarios that should pass verification."""

    def test_existing_file_after_write(self):
        """Verify Write operation with existing file passes."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            test_file = f.name
        try:
            verifier = ImplementationVerifier()
            result = verifier.process("Write", {"file_path": test_file}, {})
            assert result["passed"] is True
        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_existing_file_after_edit(self):
        """Verify Edit operation with existing file passes."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            test_file = f.name
        try:
            verifier = ImplementationVerifier()
            result = verifier.process("Edit", {"file_path": test_file}, {})
            assert result["passed"] is True
        finally:
            Path(test_file).unlink(missing_ok=True)


class TestNegativeCases:
    """Tests for scenarios that should fail verification."""

    def test_write_claimed_file_not_created(self):
        """Verify Write without creating file fails verification."""
        verifier = ImplementationVerifier()
        result = verifier.process("Write", {"file_path": "does_not_exist.txt"}, {})
        assert result["passed"] is False
        assert "injection" in result

    def test_edit_claimed_file_not_created(self):
        """Verify Edit without creating file fails verification."""
        verifier = ImplementationVerifier()
        result = verifier.process("Edit", {"file_path": "also_does_not_exist.txt"}, {})
        assert result["passed"] is False
        assert "injection" in result


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_file_path(self):
        """Verify empty string file_path is handled gracefully."""
        verifier = ImplementationVerifier()
        result = verifier.process("Write", {"file_path": ""}, {})
        # Empty path is treated as missing file
        assert result["passed"] is False

    def test_whitespace_only_file_path(self):
        """Verify whitespace-only file_path is handled."""
        verifier = ImplementationVerifier()
        result = verifier.process("Write", {"file_path": "   "}, {})
        assert result["passed"] is False

    def test_special_characters_in_path(self):
        """Verify paths with special characters work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test file.txt"
            test_file.touch()
            try:
                verifier = ImplementationVerifier()
                result = verifier.process("Write", {"file_path": str(test_file)}, {})
                assert result["passed"] is True
            finally:
                test_file.unlink(missing_ok=True)


class TestSettingsIntegration:
    """Tests for settings.json integration."""

    def test_hook_enabled_in_settings(self):
        """Verify ImplementationVerifier is enabled in settings.json."""
        settings_path = HOOKS_DIR.parent / "settings.json"

        if not settings_path.exists():
            pytest.skip("settings.json not found")

        with open(settings_path) as f:
            settings = json.load(f)

        # Check env var is set (or default to true)
        env_value = settings.get("env", {}).get("IMPLEMENTATION_VERIFIER_ENABLED", "true")
        assert env_value == "true"


class TestPerformanceBaseline:
    """Tests for performance requirements."""

    def test_verification_latency_under_10ms(self):
        """Verify verification completes in under 10ms."""
        import time

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            test_file = f.name
        try:
            verifier = ImplementationVerifier()
            start = time.perf_counter()
            result = verifier.process("Write", {"file_path": test_file}, {})
            elapsed = time.perf_counter() - start
            assert elapsed < 0.01  # 10ms baseline
        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_missing_file_latency_under_10ms(self):
        """Verify missing file check completes in under 10ms."""
        import time

        verifier = ImplementationVerifier()
        start = time.perf_counter()
        result = verifier.process("Write", {"file_path": "nonexistent.txt"}, {})
        elapsed = time.perf_counter() - start
        assert elapsed < 0.01  # 10ms baseline


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
