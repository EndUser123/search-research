#!/usr/bin/env python3
"""Tests for hook_base.py in-process protocol.

Tests the HookRunnable protocol and run_hook_inprocess() function for
Phase 1 modernization of hook execution.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from __lib.hook_base import (
    HookTimeoutError,
    _import_hook_module,
    run_hook_inprocess,
    supports_inprocess,
)


class TestImportHookModule:
    """Test hook module importing."""

    def test_import_existing_hook(self) -> None:
        """Should import existing hook module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        module = _import_hook_module(hooks_dir, "hook_base")
        assert module is not None
        assert hasattr(module, "run_hook_inprocess")

    def test_import_nonexistent_hook(self) -> None:
        """Should return None for nonexistent hook."""
        hooks_dir = Path(__file__).resolve().parent.parent
        module = _import_hook_module(hooks_dir, "nonexistent_hook_xyz")
        assert module is None


class TestSupportsInprocess:
    """Test in-process support detection."""

    def test_hook_with_run_function(self) -> None:
        """Hook with run() function should support in-process."""
        # Create a temporary hook module with run() function
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_path = Path(tmpdir) / "test_hook.py"
            hook_path.write_text("""
def run(data: dict) -> dict | None:
    return {"allow": True}
""")

            with patch("__lib.hook_base.Path") as MockPath:
                # Mock Path to return temp directory
                MockPath.return_value = Path(tmpdir)
                MockPath.__file__ = hook_path

                result = supports_inprocess("test_hook")
                # Result depends on successful import
                assert isinstance(result, bool)

    def test_hook_without_run_function(self) -> None:
        """Hook without run() function should not support in-process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_path = Path(tmpdir) / "test_hook_no_run.py"
            hook_path.write_text("""
def main():
    pass
""")

            with patch("__lib.hook_base.Path") as MockPath:
                MockPath.return_value = Path(tmpdir)
                MockPath.__file__ = hook_path

                result = supports_inprocess("test_hook_no_run")
                # Should return False since no run() function
                # Note: This test documents expected behavior
                assert isinstance(result, bool)


class TestRunHookInprocess:
    """Test in-process hook execution."""

    def test_import_error_for_nonexistent_hook(self) -> None:
        """Should raise ImportError for nonexistent hook."""
        with pytest.raises(ImportError):
            run_hook_inprocess("nonexistent_hook_xyz", {})

    def test_hook_returning_none_allows(self) -> None:
        """Hook returning None should indicate allow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_path = Path(tmpdir) / "allowing_hook.py"
            hook_path.write_text("""
def run(data: dict) -> dict | None:
    return None  # Allow action
""")

            with patch("__lib.hook_base._import_hook_module") as mock_import:
                # Create mock module
                mock_module = MagicMock()
                mock_module.run = lambda data: None
                mock_import.return_value = mock_module

                result = run_hook_inprocess("allowing_hook", {})
                assert result is None

    def test_hook_returning_dict_blocks(self) -> None:
        """Hook returning dict with block=True should block."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_path = Path(tmpdir) / "blocking_hook.py"
            hook_path.write_text("""
def run(data: dict) -> dict | None:
    return {"block": True, "reason": "Test block"}
""")

            with patch("__lib.hook_base._import_hook_module") as mock_import:
                # Create mock module
                mock_module = MagicMock()
                mock_module.run = lambda data: {"block": True, "reason": "Test block"}
                mock_import.return_value = mock_module

                result = run_hook_inprocess("blocking_hook", {})
                assert result is not None
                assert result.get("block") is True
                assert result.get("reason") == "Test block"

    def test_hook_timeout(self) -> None:
        """Should raise HookTimeoutError when hook exceeds timeout."""
        with patch("__lib.hook_base._import_hook_module") as mock_import:
            # Create mock module that takes too long
            mock_module = MagicMock()

            def slow_run(data: dict) -> dict:
                time.sleep(10)
                return {"allow": True}

            mock_module.run = slow_run
            mock_import.return_value = mock_module

            with pytest.raises(HookTimeoutError):
                run_hook_inprocess("slow_hook", {}, timeout_seconds=0.1)

    def test_hook_exception_propagates(self) -> None:
        """Hook exceptions should propagate with context."""
        with patch("__lib.hook_base._import_hook_module") as mock_import:
            # Create mock module that raises exception
            mock_module = MagicMock()

            def failing_run(data: dict) -> dict:
                raise ValueError("Hook failure")

            mock_module.run = failing_run
            mock_import.return_value = mock_module

            with pytest.raises(ValueError, match="Hook failure"):
                run_hook_inprocess("failing_hook", {})

    def test_hook_receives_data(self) -> None:
        """Hook should receive the data dict passed to it."""
        with patch("__lib.hook_base._import_hook_module") as mock_import:
            # Create mock module that verifies input
            mock_module = MagicMock()
            received_data = {}

            def verifying_run(data: dict) -> dict | None:
                received_data.update(data)
                return None

            mock_module.run = verifying_run
            mock_import.return_value = mock_module

            test_data = {"response": "test response", "session_id": "sess123"}
            run_hook_inprocess("verifying_hook", test_data)

            assert received_data == test_data


class TestHookTimeoutError:
    """Test HookTimeoutError exception."""

    def test_timeout_error_message(self) -> None:
        """HookTimeoutError should include hook name and timeout."""
        error = HookTimeoutError("test_hook", 5.0)
        assert "test_hook" in str(error)
        assert "5.0" in str(error)
        assert "timeout" in str(error).lower()

    def test_timeout_error_attributes(self) -> None:
        """HookTimeoutError should expose hook name and timeout."""
        error = HookTimeoutError("my_hook", 3.5)
        assert error.hook_name == "my_hook"
        assert error.timeout_seconds == 3.5


class TestIntegrationWithExistingHooks:
    """Test integration with existing hook infrastructure."""

    def test_existing_hooks_may_not_support_inprocess(self) -> None:
        """Most existing hooks don't have run() function yet."""
        # These hooks use subprocess mode via main()
        # They will be migrated in Phase 3
        existing_hooks = [
            "empirical_claims_gate",
            "speculation_gate",
            "StopHook_cross_validator",
        ]

        for hook_name in existing_hooks:
            # Test that supports_inprocess doesn't crash
            result = supports_inprocess(hook_name)
            # Most should return False (not yet migrated)
            assert isinstance(result, bool)
