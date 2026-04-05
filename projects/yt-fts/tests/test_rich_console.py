"""
Tests for yt_fts.utils.rich_console module.

Tests console creation with different configurations for stderr/stdout,
Windows compatibility, and fallback behavior.
"""

import sys
from unittest.mock import Mock, patch

import pytest

from yt_fts.utils.rich_console import get_console, get_stderr_console


class TestGetConsole:
    """Test stdout console creation."""

    def test_returns_console_instance(self):
        """Should return a Rich Console instance."""
        result = get_console()

        from rich.console import Console
        assert isinstance(result, Console)

    def test_uses_width_parameter(self):
        """Should respect custom width parameter."""
        result = get_console(width=80)

        assert result.width == 80

    def test_default_width_is_auto_detected(self):
        """Should auto-detect width when not specified (width=None)."""
        result = get_console()

        # Width is auto-detected from terminal, should be positive
        assert result.width > 0
        # In CI/testing environment, width is typically 80
        # This is environment-dependent, so we just verify it's a reasonable value
        assert 40 <= result.width <= 200

    def test_legacy_windows_false_by_default(self):
        """Should use legacy_windows=False by default."""
        result = get_console()

        # Check the internal option
        assert result.legacy_windows is False

    def test_respects_legacy_windows_override(self):
        """Should allow legacy_windows override."""
        result = get_console(legacy_windows=True)

        assert result.legacy_windows is True


class TestGetStderrConsole:
    """Test stderr console creation for progress displays."""

    def test_returns_console_instance(self):
        """Should return a Rich Console instance."""
        result = get_stderr_console()

        from rich.console import Console
        assert isinstance(result, Console)

    def test_uses_stderr_by_default(self):
        """Should output to stderr by default."""
        result = get_stderr_console()

        assert result.file == sys.stderr

    def test_legacy_windows_false(self):
        """Should use legacy_windows=False for stderr console."""
        result = get_stderr_console()

        assert result.legacy_windows is False

    def test_respects_width_parameter(self):
        """Should respect custom width parameter."""
        result = get_stderr_console(width=80)

        assert result.width == 80


class TestConsoleFallbackBehavior:
    """Test default behavior for console configuration."""

    def test_defaults_to_no_stderr_for_stdout(self):
        """Should use stdout (not stderr) for default console."""
        result = get_console()

        assert result.file == sys.stdout
