"""
Tests for batch_display module.

Tests display setup, Rich mode detection, logging configuration,
and display option validation.
"""
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.core.batch_display import (
    DisplaySetup,
    determine_rich_mode,
    validate_display_options,
    is_quiet_mode,
)


class TestDisplaySetup:
    """Test DisplaySetup dataclass."""

    def test_create_display_setup(self):
        """Test creating a DisplaySetup."""
        setup = DisplaySetup(
            rich_mode="new",
            rich_formatter=None,
            quiet_mode=False,
            simple=False,
            fzf=False,
        )
        assert setup.rich_mode == "new"
        assert setup.rich_formatter is None
        assert setup.quiet_mode is False

    def test_is_rich_enabled_true(self):
        """Test is_rich_enabled returns True when rich_mode is set."""
        setup = DisplaySetup(
            rich_mode="new",
            rich_formatter=None,
            quiet_mode=False,
        )
        assert setup.is_rich_enabled() is True

    def test_is_rich_enabled_false(self):
        """Test is_rich_enabled returns False when rich_mode is None."""
        setup = DisplaySetup(
            rich_mode=None,
            rich_formatter=None,
            quiet_mode=False,
        )
        assert setup.is_rich_enabled() is False

    def test_is_simple_mode_simple(self):
        """Test is_simple_mode returns True for simple mode."""
        setup = DisplaySetup(
            rich_mode=None,
            rich_formatter=None,
            quiet_mode=False,
            simple=True,
        )
        assert setup.is_simple_mode() is True

    def test_is_simple_mode_fzf(self):
        """Test is_simple_mode returns True for fzf mode."""
        setup = DisplaySetup(
            rich_mode=None,
            rich_formatter=None,
            quiet_mode=False,
            fzf=True,
        )
        assert setup.is_simple_mode() is True

    def test_is_simple_mode_false(self):
        """Test is_simple_mode returns False when not simple/fzf."""
        setup = DisplaySetup(
            rich_mode="new",
            rich_formatter=None,
            quiet_mode=False,
            simple=False,
            fzf=False,
        )
        assert setup.is_simple_mode() is False


class TestDetermineRichMode:
    """Test determine_rich_mode function."""

    def test_rich_mode_new_from_rich(self):
        """Test determine_rich_mode returns 'new' for rich flag."""
        assert determine_rich_mode(rich=True, rich_1=False, richo=False) == "new"

    def test_rich_mode_new_from_rich_1(self):
        """Test determine_rich_mode returns 'new' for rich_1 flag."""
        assert determine_rich_mode(rich=False, rich_1=True, richo=False) == "new"

    def test_rich_mode_old_from_richo(self):
        """Test determine_rich_mode returns 'old' for richo flag."""
        assert determine_rich_mode(rich=False, rich_1=False, richo=True) == "old"

    def test_rich_mode_none(self):
        """Test determine_rich_mode returns None when no flags set."""
        assert determine_rich_mode(rich=False, rich_1=False, richo=False) is None

    def test_rich_mode_priority_rich_over_richo(self):
        """Test rich flag takes priority over richo."""
        assert determine_rich_mode(rich=True, rich_1=False, richo=True) == "new"


class TestValidateDisplayOptions:
    """Test validate_display_options function."""

    def test_validate_no_conflicts(self):
        """Test validation passes with single display mode."""
        # Should not raise
        validate_display_options(
            simple=True, fzf=False, rich=False, richo=False, rich_1=False
        )
        validate_display_options(
            simple=False, fzf=True, rich=False, richo=False, rich_1=False
        )

    def test_validate_conflicting_options(self):
        """Test validation raises error for conflicting display modes."""
        with pytest.raises(ValueError) as exc_info:
            validate_display_options(
                simple=True, fzf=True, rich=False, richo=False, rich_1=False
            )
        assert "Conflicting display options" in str(exc_info.value)
        assert "simple" in str(exc_info.value)
        assert "fzf" in str(exc_info.value)

    def test_validate_rich_conflicts(self):
        """Test validation raises error for multiple rich modes."""
        with pytest.raises(ValueError) as exc_info:
            validate_display_options(
                simple=False, fzf=False, rich=True, richo=True, rich_1=False
            )
        assert "rich" in str(exc_info.value)
        assert "richo" in str(exc_info.value)

    def test_validate_all_disabled(self):
        """Test validation passes when all display modes are disabled."""
        validate_display_options(
            simple=False, fzf=False, rich=False, richo=False, rich_1=False
        )


class TestIsQuietMode:
    """Test is_quiet_mode function."""

    def test_is_quiet_mode_true(self, monkeypatch):
        """Test is_quiet_mode returns True when env var is set."""
        monkeypatch.setenv("YT_FTS_QUIET_MODE", "1")
        assert is_quiet_mode() is True

    def test_is_quiet_mode_false(self, monkeypatch):
        """Test is_quiet_mode returns False when env var is not set."""
        monkeypatch.delenv("YT_FTS_QUIET_MODE", raising=False)
        assert is_quiet_mode() is False

    def test_is_quiet_mode_wrong_value(self, monkeypatch):
        """Test is_quiet_mode returns False for wrong env value."""
        monkeypatch.setenv("YT_FTS_QUIET_MODE", "0")
        assert is_quiet_mode() is False

class TestSetupDisplayLogging:
    """Test setup_display_logging function."""

    def test_setup_logging_new_rich_mode(self):
        """Test logging level set to WARNING for new Rich mode."""
        from yt_fts.core.batch_display import setup_display_logging

        download_logger = logging.getLogger(
            "yt_fts.download.download_handler.DownloadHandler"
        )
        original_level = download_logger.level

        try:
            setup_display_logging("new")
            assert download_logger.level >= logging.WARNING
        finally:
            download_logger.setLevel(original_level)

    def test_setup_logging_standard_mode(self):
        """Test logging level set to DEBUG for standard mode."""
        from yt_fts.core.batch_display import setup_display_logging

        download_logger = logging.getLogger(
            "yt_fts.download.download_handler.DownloadHandler"
        )
        original_level = download_logger.level

        try:
            setup_display_logging(None)
            assert download_logger.level == logging.DEBUG
        finally:
            download_logger.setLevel(original_level)


class TestSetupRichFormatter:
    """Test setup_rich_formatter function."""

    @patch("yt_fts.core.batch_display.console")
    def test_setup_rich_formatter_not_richo(self, mock_console):
        """Test setup_rich_formatter returns None when richo=False."""
        from yt_fts.core.batch_display import setup_rich_formatter

        result = setup_rich_formatter(richo=False, continue_on_error=False)
        assert result is None

    @patch("yt_fts.core.batch_display.console")
    @patch("yt_fts.ui.rich_formatter.create_rich_formatter", side_effect=ImportError)
    def test_setup_rich_formatter_import_error(self, mock_create, mock_console):
        """Test setup_rich_formatter handles ImportError gracefully."""
        from yt_fts.core.batch_display import setup_rich_formatter

        result = setup_rich_formatter(richo=True, continue_on_error=False)
        assert result is None
        mock_console.print.assert_called()


class TestShowSystemStatus:
    """Test show_system_status function."""

    @patch("yt_fts.core.batch_display.console")
    @patch("yt_fts.core.status_display.StatusDisplay", side_effect=ImportError)
    def test_show_system_status_import_error(self, mock_status, mock_console):
        """Test show_system_status handles ImportError gracefully."""
        from yt_fts.core.batch_display import show_system_status

        show_system_status()
        mock_console.print.assert_called()
