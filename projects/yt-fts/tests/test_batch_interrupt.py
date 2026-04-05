"""
Tests for batch_interrupt module.

Tests graceful interrupt handling context manager and setup.
"""
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.core.batch_interrupt import (
    graceful_interrupt_handler,
    setup_interrupt_handler,
)


class TestGracefulInterruptHandler:
    """Test graceful_interrupt_handler context manager."""

    @patch("yt_fts.core.batch_interrupt.console")
    def test_context_manager_calls_download_all(self, mock_console):
        """Test context manager calls download_all on downloader."""
        mock_downloader = MagicMock()
        mock_downloader.download_all = MagicMock()

        # The graceful_interrupt_handler should call download_all
        with graceful_interrupt_handler(mock_downloader):
            pass

        # download_all should have been called by the context manager
        mock_downloader.download_all.assert_called_once()


class TestSetupInterruptHandler:
    """Test setup_interrupt_handler function."""

    @patch("yt_fts.core.batch_interrupt.console")
    def test_setup_handler_returns_handler(self, mock_console):
        """Test setup_interrupt_handler returns handler when available."""
        mock_downloader = MagicMock()

        result = setup_interrupt_handler(mock_downloader)

        # Should return a GracefulInterruptHandler instance (not None)
        assert result is not None
        # The result should be a context manager
        assert hasattr(result, "__enter__")
        assert hasattr(result, "__exit__")

class TestSetupInterruptHandlerImportError:
    """Test setup_interrupt_handler when imports fail."""

    @patch("yt_fts.core.batch_interrupt.console")
    @patch("yt_fts.core.batch_interrupt.GracefulInterruptHandler", side_effect=ImportError)
    def test_setup_handler_import_error(self, mock_handler, mock_console):
        """Test setup_interrupt_handler returns None when import fails."""
        mock_downloader = MagicMock()

        result = setup_interrupt_handler(mock_downloader)

        assert result is None
        mock_console.print.assert_called()


class TestExportReportHandling:
    """Test export_report parameter handling."""

    @patch("yt_fts.core.batch_interrupt.console")
    @patch("yt_fts.core.batch_interrupt.GracefulInterruptHandler", side_effect=ImportError)
    def test_export_report_missing_attribute(self, mock_handler, mock_console):
        """Test export_report when downloader lacks export_report method."""
        mock_downloader = MagicMock()
        mock_downloader.download_all = MagicMock()
        # Remove export_report method to trigger AttributeError path
        del mock_downloader.export_report

        with graceful_interrupt_handler(mock_downloader, export_report="test.json"):
            pass

        # Should print warning about export not available
        mock_console.print.assert_called()
class TestGracefulInterruptHandlerUtilsImportError:
    """Test graceful_interrupt_handler when utils interrupt handler imports fail."""

    @patch("yt_fts.core.batch_interrupt.console")
    @patch("yt_fts.utils.interrupt_handler.GracefulInterruptHandler", side_effect=ImportError)
    def test_handler_import_error(self, mock_handler, mock_console):
        """Test ImportError path when GracefulInterruptHandler not available."""
        mock_downloader = MagicMock()
        mock_downloader.download_all = MagicMock()

        with graceful_interrupt_handler(mock_downloader):
            pass

        # Should still call download_all
        mock_downloader.download_all.assert_called_once()
        # Should print warning
        mock_console.print.assert_called()


class TestSetupInterruptHandlerUtilsImportError:
    """Test setup_interrupt_handler when imports fail."""

    @patch("yt_fts.core.batch_interrupt.console")
    @patch("yt_fts.utils.interrupt_handler.GracefulInterruptHandler", side_effect=ImportError)
    def test_setup_handler_import_error(self, mock_handler, mock_console):
        """Test setup_interrupt_handler returns None when import fails."""
        mock_downloader = MagicMock()

        result = setup_interrupt_handler(mock_downloader)

        assert result is None
        mock_console.print.assert_called()


class TestExportReportHandlingUtilsImport:
    """Test export_report parameter handling with utils interrupt handler."""

    @patch("yt_fts.core.batch_interrupt.console")
    @patch("yt_fts.utils.interrupt_handler.GracefulInterruptHandler", side_effect=ImportError)
    def test_export_report_missing_attribute(self, mock_handler, mock_console):
        """Test export_report when downloader lacks export_report method."""
        mock_downloader = MagicMock()
        mock_downloader.download_all = MagicMock()
        # Remove export_report method to trigger AttributeError path
        del mock_downloader.export_report

        with graceful_interrupt_handler(mock_downloader, export_report="test.json"):
            pass

        # Should print warning about export not available
        mock_console.print.assert_called()
