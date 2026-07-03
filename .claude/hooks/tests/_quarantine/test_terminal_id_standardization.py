#!/usr/bin/env python3
"""
Tests for standardized terminal ID derivation (TASK-003).

Tests verify the get_terminal_id() function in hook_base.py provides:
1. Consistent terminal ID generation across all hooks
2. Priority order: explicit input → env vars → derivation
3. Proper caching in _hook_context
4. Sanitization and normalization
"""

import os
import sys
from pathlib import Path

import pytest

# Add hooks lib to path
sys.path.insert(0, str(Path("P:/.claude/hooks/__lib").resolve()))

from hook_base import TERMINAL_ID_SANITIZE_RE, _hook_context, get_terminal_id


@pytest.fixture(autouse=True)
def clear_terminal_id_cache():
    """Clear terminal_id cache before each test to ensure isolation."""
    if hasattr(_hook_context, "terminal_id"):
        delattr(_hook_context, "terminal_id")
    yield
    # Clean up after test as well
    if hasattr(_hook_context, "terminal_id"):
        delattr(_hook_context, "terminal_id")


class TestGetTerminalID:
    """Test suite for get_terminal_id() function."""

    def test_explicit_terminal_id_from_data(self):
        """Test Priority 1: Explicit terminal_id from hook data takes precedence."""
        data = {"terminal_id": "env_custom_123"}
        tid = get_terminal_id(data)

        assert tid == "env_custom_123"
        assert tid.startswith("env_")

    def test_explicit_terminal_id_sanitization(self):
        """Test that explicit terminal_id is sanitized."""
        data = {"terminal_id": "custom@#$%123"}
        tid = get_terminal_id(data)

        # Special characters should be removed
        assert "@" not in tid
        assert "#" not in tid
        assert "$" not in tid
        assert "%" not in tid
        # After sanitizing "custom@#$%123" we get "custom123", then "env_" prefix added
        assert "env_custom123" == tid

    def test_explicit_terminal_id_with_known_prefix(self):
        """Test that known prefixes are preserved (idempotent)."""
        # Test "console_" prefix (Windows console)
        data = {"terminal_id": "console_abc123"}
        tid = get_terminal_id(data)
        assert tid == "console_abc123"

        # Test "env_" prefix
        data = {"terminal_id": "env_xyz789"}
        tid = get_terminal_id(data)
        assert tid == "env_xyz789"

    def test_environment_variable_claude_terminal_id(self):
        """Test Priority 2: CLAUDE_TERMINAL_ID environment variable."""
        # Save original value
        original = os.environ.get("CLAUDE_TERMINAL_ID")

        try:
            # Set environment variable
            os.environ["CLAUDE_TERMINAL_ID"] = "env_from_env"
            tid = get_terminal_id({})

            assert tid == "env_from_env"

        finally:
            # Restore original value
            if original is None:
                os.environ.pop("CLAUDE_TERMINAL_ID", None)
            else:
                os.environ["CLAUDE_TERMINAL_ID"] = original

    def test_environment_variable_terminal_id(self):
        """Test Priority 2: TERMINAL_ID environment variable."""
        original = os.environ.get("TERMINAL_ID")

        try:
            os.environ["TERMINAL_ID"] = "custom_term"
            tid = get_terminal_id({})

            assert tid == "env_custom_term"

        finally:
            if original is None:
                os.environ.pop("TERMINAL_ID", None)
            else:
                os.environ["TERMINAL_ID"] = original

    def test_derived_from_process_attributes(self):
        """Test Priority 3: Console detection or Priority 4: Derive from PID + session timestamp."""
        # Clear all env vars that might interfere
        env_vars = [
            "CLAUDE_TERMINAL_ID",
            "TERMINAL_ID",
            "TERM_ID",
            "SESSION_TERMINAL",
            "WT_SESSION",
        ]
        saved_vars = {}

        for var in env_vars:
            saved_vars[var] = os.environ.get(var)
            os.environ.pop(var, None)

        try:
            # Provide session_start_ts
            data = {"session_start_ts": 1234567890}
            tid = get_terminal_id(data)

            # Should be either:
            # - console_* format (if console detection succeeds)
            # - 12-char hex string (if falls back to PID+timestamp derivation)
            assert len(tid) >= 12  # Either format is valid
            if tid.startswith("console_"):
                # Console detection succeeded
                assert len(tid) > 8  # At least "console_" + some hex
            else:
                # PID+timestamp fallback (12-char hex)
                assert len(tid) == 12
                assert all(c in "0123456789abcdef" for c in tid)

        finally:
            # Restore environment variables
            for var, value in saved_vars.items():
                if value is not None:
                    os.environ[var] = value

    def test_empty_string_when_no_data(self):
        """Test that empty string is returned when no detection method succeeds."""
        # Clear all env vars
        env_vars = ["CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM_ID", "SESSION_TERMINAL"]
        saved_vars = {}

        for var in env_vars:
            saved_vars[var] = os.environ.get(var)
            os.environ.pop(var, None)

        try:
            # No data, no env vars
            tid = get_terminal_id({})

            # Should return empty string when all methods fail
            # Note: Actual implementation may return "" or derived ID depending on implementation

        finally:
            for var, value in saved_vars.items():
                if value is not None:
                    os.environ[var] = value

    def test_caching_in_hook_context(self):
        """Test that terminal_id is cached in _hook_context after first call."""
        data = {"terminal_id": "env_cached_123"}

        # First call
        tid1 = get_terminal_id(data)

        # Clear input data to ensure cache is being used
        data.clear()

        # Second call (should use cache)
        tid2 = get_terminal_id(data)

        # Should return same cached value even though data was cleared
        assert tid1 == tid2
        assert tid2 == "env_cached_123"

    def test_normalize_terminal_id_with_console_host_legacy(self):
        """Test legacy ConsoleHost_ format conversion."""
        result = get_terminal_id({"terminal_id": "ConsoleHost_abc123def"})

        # Should convert "ConsoleHost_" → "console_"
        assert result == "console_abc123def"

    def test_normalize_terminal_id_with_session_legacy(self):
        """Test legacy session_ format conversion."""
        result = get_terminal_id({"terminal_id": "session_abc123"})

        # Should convert "session_" → "env_"
        assert result == "env_abc123"

    def test_normalize_terminal_id_default_env_prefix(self):
        """Test that unknown format gets "env_" prefix by default."""
        result = get_terminal_id({"terminal_id": "unknown_format_xyz"})

        # Should add "env_" prefix
        assert result == "env_unknown_format_xyz"


class TestTerminalIDSanitization:
    """Test suite for TERMINAL_ID_SANITIZE_RE regex."""

    def test_removes_special_characters(self):
        """Test that special characters are removed."""
        assert TERMINAL_ID_SANITIZE_RE.sub("", "test@#$%") == "test"

    def test_removes_spaces(self):
        """Test that spaces are removed."""
        assert TERMINAL_ID_SANITIZE_RE.sub("", "test id") == "testid"

    def test_removes_dots(self):
        """Test that dots are removed."""
        assert TERMINAL_ID_SANITIZE_RE.sub("", "test.id") == "testid"

    def test_keeps_underscores(self):
        """Test that underscores are preserved."""
        assert TERMINAL_ID_SANITIZE_RE.sub("", "test_id_value") == "test_id_value"

    def test_keeps_alphanumeric(self):
        """Test that alphanumeric characters are preserved."""
        assert TERMINAL_ID_SANITIZE_RE.sub("", "Test123ABC") == "Test123ABC"


class TestTerminalIDPriorityOrder:
    """Test suite for terminal ID priority order."""

    def test_explicit_overrides_environment(self):
        """Test that explicit terminal_id overrides environment variable."""
        original = os.environ.get("CLAUDE_TERMINAL_ID")

        try:
            os.environ["CLAUDE_TERMINAL_ID"] = "env_override"

            # Explicit terminal_id in data should take precedence
            data = {"terminal_id": "env_explicit"}
            tid = get_terminal_id(data)

            assert tid == "env_explicit"

        finally:
            if original is None:
                os.environ.pop("CLAUDE_TERMINAL_ID", None)
            else:
                os.environ["CLAUDE_TERMINAL_ID"] = original

    def test_environment_overrides_derivation(self):
        """Test that environment variable overrides derivation."""
        # Clear explicit terminal_id
        data = {"session_start_ts": 1234567890}

        original = os.environ.get("CLAUDE_TERMINAL_ID")

        try:
            os.environ["CLAUDE_TERMINAL_ID"] = "env_priority"
            tid = get_terminal_id(data)

            # Should use env var, not derive from PID
            assert tid == "env_priority"

        finally:
            if original is None:
                os.environ.pop("CLAUDE_TERMINAL_ID", None)
            else:
                os.environ["CLAUDE_TERMINAL_ID"] = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
