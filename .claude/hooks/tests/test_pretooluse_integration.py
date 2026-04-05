#!/usr/bin/env python3
"""
Integration tests for Python DX improvements in PreToolUse.py.

Tests the complete workflow:
1. Safe cache cleanup under P:/ tree auto-approves
2. Hook feedback summary displays correctly
3. Cache manager integration with PreToolUse router
"""

# Add __lib to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))


import hook_feedback_summary
import python_cache_manager


class TestCacheManagerIntegration:
    """Tests for cache manager integration."""

    def test_clears_cache_from_package_directory(self, tmp_path):
        """Test that cache manager clears __pycache__ from package."""
        pkg = tmp_path / "test_package"
        pkg.mkdir()
        (pkg / "__pycache__").mkdir()
        (pkg / "__pycache__" / "test.pyc").touch()

        result = python_cache_manager.clear_package_cache(pkg)

        assert result["cleared_count"] == 1
        assert not (pkg / "__pycache__").exists()
        assert len(result["paths_cleared"]) == 1

    def test_pre_install_cache_clean_returns_bool(self, tmp_path):
        """Test that pre_install_cache_clean returns boolean."""
        pkg = tmp_path / "test_package"
        pkg.mkdir()
        (pkg / "__pycache__").mkdir()

        result = python_cache_manager.pre_install_cache_clean(pkg)

        assert isinstance(result, bool)
        assert result is True


class TestAuthorizationGateIntegration:
    """Tests for authorization gate safe patterns."""

    def test_safe_cache_cleanup_under_p_tree(self):
        """Test that cache cleanup under P:/ auto-approves."""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from PreToolUse_authorization_gate import (
            has_explicit_authorization,
            is_project_safe_operation,
        )

        command = "rm -rf __pycache__"
        working_dir = "P:/packages/reflect-system"

        # Test the low-level function
        assert is_project_safe_operation(command, working_dir) is True

        # Test the high-level authorization check
        result = has_explicit_authorization("", command=command, working_dir=working_dir)
        assert result is True

    def test_system_path_not_safe(self):
        """Test that system paths are NOT auto-approved."""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from PreToolUse_authorization_gate import is_project_safe_operation

        command = "rm -rf /usr/local/lib/python/__pycache__"
        working_dir = "/usr/local/lib/python"

        result = is_project_safe_operation(command, working_dir)
        assert result is False

    def test_unsafe_command_requires_authorization(self):
        """Test that unsafe commands still require authorization."""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from PreToolUse_authorization_gate import has_explicit_authorization

        command = "rm -rf important_data"
        working_dir = "P:/packages/reflect-system"

        result = has_explicit_authorization("", command=command, working_dir=working_dir)
        assert result is False  # Should require explicit authorization


class TestHookFeedbackSummary:
    """Tests for hook feedback summary."""

    def test_authorization_gate_summary_format(self):
        """Test that authorization_gate blocking formats correctly."""
        block_result = {
            "blocking_hook": "authorization_gate",
            "reason": "Destructive command requires explicit authorization",
            "decision": "deny"
        }

        summary = hook_feedback_summary.format_blocking_summary(block_result)

        assert "authorization_gate" in summary
        assert "Destructive command" in summary
        assert "proceed" in summary.lower()  # Guidance included
        assert "⛔" in summary  # Visual indicator

    def test_tdd_gate_summary_format(self):
        """Test that tdd_gate blocking formats correctly."""
        block_result = {
            "blocking_hook": "tdd_gate",
            "reason": "No tests found for code changes",
            "decision": "deny"
        }

        summary = hook_feedback_summary.format_blocking_summary(block_result)

        assert "tdd_gate" in summary
        assert "RED" in summary
        assert "GREEN" in summary

    def test_missing_fields_graceful_handling(self):
        """Test that missing fields are handled gracefully."""
        block_result = {}

        summary = hook_feedback_summary.format_blocking_summary(block_result)

        assert "Unknown hook" in summary
        assert len(summary) > 0  # Should still produce output


class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflow."""

    def test_cache_cleanup_workflow(self, tmp_path):
        """Test complete cache cleanup workflow: detect → clear → verify."""
        # Setup: Create package with cache
        pkg = tmp_path / "my_package"
        pkg.mkdir()
        (pkg / "__pycache__").mkdir()
        (pkg / "__pycache__" / "module.pyc").touch()

        # Simulate "pip install -e" detection and cleanup
        command = "pip install -e P:/packages/my_package"
        if "pip install" in command and "-e" in command:
            # Extract package path (simplified for test)
            result = python_cache_manager.clear_package_cache(pkg)

        # Verify cache was cleared
        assert not (pkg / "__pycache__").exists()

    def test_safe_operation_authorization_flow(self):
        """Test that safe operations flow through authorization correctly."""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from PreToolUse_authorization_gate import has_explicit_authorization

        # Scenario: Safe cache cleanup under P:/
        command = "find . -name __pycache__ -exec rm -rf {} +"
        working_dir = "P:/packages/reflect-system"

        # Should auto-approve without user authorization
        result = has_explicit_authorization("", command=command, working_dir=working_dir)
        assert result is True

    def test_blocking_message_flow(self):
        """Test that blocking messages format correctly for user display."""
        block_result = {
            "blocking_hook": "authorization_gate",
            "reason": "Pattern: rm -rf",
            "decision": "deny"
        }

        summary = hook_feedback_summary.format_blocking_summary(block_result)

        # Verify all required elements present
        assert "╌" in summary  # Box drawing
        assert "⛔" in summary  # Blocking icon
        assert "BLOCKED" in summary  # Status text
        assert "authorization_gate" in summary  # Hook name
        assert "💡" in summary  # Guidance icon
        assert "proceed" in summary.lower()  # Actionable guidance
