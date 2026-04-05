#!/usr/bin/env python3
"""
Tests for PROJECT_SAFE_PATTERNS in authorization gate.
"""

import sys
from pathlib import Path

# Add hooks dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import PreToolUse_authorization_gate as auth_gate


class TestProjectSafePatterns:
    """Tests for PROJECT_SAFE_PATTERNS constant."""

    def test_cache_cleanup_patterns_exist(self):
        """Test that PROJECT_SAFE_PATTERNS is defined."""
        assert hasattr(auth_gate, 'PROJECT_SAFE_PATTERNS')
        assert isinstance(auth_gate.PROJECT_SAFE_PATTERNS, list)
        assert len(auth_gate.PROJECT_SAFE_PATTERNS) > 0

    def test_patterns_match_cache_cleanup(self):
        """Test that patterns match cache cleanup commands."""
        patterns = auth_gate.PROJECT_SAFE_PATTERNS
        # Should match __pycache__ cleanup
        assert any('__pycache__' in str(p) for p in patterns)
        # Should match .pyc cleanup
        assert any('.pyc' in str(p) for p in patterns)


class TestIsProjectSafeOperation:
    """Tests for is_project_safe_operation() function."""

    def test_function_exists(self):
        """Test that is_project_safe_operation() exists."""
        assert hasattr(auth_gate, 'is_project_safe_operation')
        assert callable(auth_gate.is_project_safe_operation)

    def test_pycache_cleanup_under_p_tree(self):
        """Test that cache cleanup under P:/ is recognized as safe."""
        command = "rm -rf P:/packages/test/__pycache__"
        working_dir = "P:/packages/test"
        result = auth_gate.is_project_safe_operation(command, working_dir)
        assert result is True

    def test_pyc_cleanup_under_p_tree(self):
        """Test that .pyc cleanup under P:/ is recognized as safe."""
        command = "find P:/packages/test -name '*.pyc' -delete"
        working_dir = "P:/packages/test"
        result = auth_gate.is_project_safe_operation(command, working_dir)
        assert result is True

    def test_system_path_not_safe(self):
        """Test that operations outside P:/ are not auto-approved."""
        command = "rm -rf /usr/local/lib/python/__pycache__"
        working_dir = "/usr/local/lib/python"
        result = auth_gate.is_project_safe_operation(command, working_dir)
        assert result is False

    def test_destructive_outside_p_not_safe(self):
        """Test that destructive operations outside P:/ require authorization."""
        command = "rm -rf C:/Windows/temp"
        working_dir = "C:/Windows"
        result = auth_gate.is_project_safe_operation(command, working_dir)
        assert result is False


class TestHasExplicitAuthorizationWithCommand:
    """Tests for has_explicit_authorization() with command parameter."""

    def test_safe_command_auto_approves(self):
        """Test that safe cache cleanup commands return True."""
        command = "rm -rf P:/packages/test/__pycache__"
        working_dir = "P:/packages/test"
        # Note: We're testing the extended signature with command parameter
        result = auth_gate.has_explicit_authorization(
            "proceed",  # user message (ignored for safe commands)
            command=command,
            working_dir=working_dir
        )
        assert result is True

    def test_unsafe_command_requires_authorization(self):
        """Test that unsafe commands still require explicit authorization."""
        command = "rm -rf /tmp/test"
        working_dir = "/tmp"
        result = auth_gate.has_explicit_authorization(
            "that looks good",  # confirmatory, not authorization
            command=command,
            working_dir=working_dir
        )
        assert result is False

    def test_unsafe_command_with_authorization(self):
        """Test that unsafe commands pass with explicit authorization."""
        command = "rm -rf /tmp/test"
        working_dir = "/tmp"
        result = auth_gate.has_explicit_authorization(
            "do it",  # explicit authorization
            command=command,
            working_dir=working_dir
        )
        assert result is True
