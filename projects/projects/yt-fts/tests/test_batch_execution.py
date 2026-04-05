"""
Tests for batch_execution module.

Tests execution path functions for TUI, parallel, and sequential processing.
"""
from unittest.mock import MagicMock, patch
from types import ModuleType

import pytest
import sys

from yt_fts.core.batch_execution import (
    execute_tui_path,
    execute_parallel_path,
    execute_sequential_path,
)


@pytest.fixture(autouse=True)
def setup_missing_modules():
    """Inject mock modules for ui.dashboard and download modules that don't exist yet."""
    # Create mock ui.dashboard module
    mock_ui_dashboard = ModuleType("yt_fts.core.ui.dashboard")
    mock_ui_dashboard.is_textual_compatible = MagicMock(return_value=(True, "0.50.0"))
    mock_ui_dashboard.GoogleStitchUI = MagicMock()
    mock_ui_dashboard.MIN_TEXTUAL_VERSION = "0.50.0"

    # Create parent ui module
    mock_ui = ModuleType("yt_fts.core.ui")
    mock_ui.dashboard = mock_ui_dashboard

    # Create mock download.parallel_batch module
    mock_parallel_batch = ModuleType("yt_fts.download.parallel_batch")
    mock_parallel_batch.ParallelBatchProcessor = MagicMock()

    # Create mock download.summary module
    mock_summary = ModuleType("yt_fts.download.summary")
    mock_summary.print_summary = MagicMock()

    # Create parent download module
    mock_download = ModuleType("yt_fts.download")
    mock_download.parallel_batch = mock_parallel_batch
    mock_download.summary = mock_summary

    # Create batch_downloader module
    mock_batch_downloader = ModuleType("yt_fts.download.batch_downloader")
    mock_batch_downloader.BatchDownloader = MagicMock()

    mock_download.batch_downloader = mock_batch_downloader

    # Inject into sys.modules
    sys.modules["yt_fts.core.ui"] = mock_ui
    sys.modules["yt_fts.core.ui.dashboard"] = mock_ui_dashboard
    sys.modules["yt_fts.download"] = mock_download
    sys.modules["yt_fts.download.parallel_batch"] = mock_parallel_batch
    sys.modules["yt_fts.download.summary"] = mock_summary
    sys.modules["yt_fts.download.batch_downloader"] = mock_batch_downloader

    yield

    # Cleanup
    for mod in [
        "yt_fts.core.ui",
        "yt_fts.core.ui.dashboard",
        "yt_fts.download",
        "yt_fts.download.parallel_batch",
        "yt_fts.download.summary",
        "yt_fts.download.batch_downloader",
    ]:
        sys.modules.pop(mod, None)


class TestExecuteTuiPath:
    """Test execute_tui_path function."""

    @patch("yt_fts.core.batch_execution.console")
    def test_execute_tui_success(self, mock_console):
        """Test TUI executes successfully when compatible."""
        with patch("yt_fts.core.ui.dashboard.is_textual_compatible") as mock_compatible:
            with patch("yt_fts.core.ui.dashboard.GoogleStitchUI") as mock_ui_class:
                mock_compatible.return_value = (True, "0.50.0")
                mock_ui = MagicMock()
                mock_ui.run.return_value = None
                mock_ui_class.return_value = mock_ui

                channels = ["https://youtube.com/channel1"]
                result = execute_tui_path(channels, fail_fast=False)

                assert result is True
                mock_ui.run.assert_called_once()

    @patch("yt_fts.core.batch_execution.console")
    def test_execute_tui_not_compatible(self, mock_console):
        """Test TUI handles incompatible Textual version."""
        with patch("yt_fts.core.ui.dashboard.is_textual_compatible") as mock_compatible:
            mock_compatible.return_value = (False, "0.30.0")

            channels = ["https://youtube.com/channel1"]
            result = execute_tui_path(channels, fail_fast=False)

            assert result is False


class TestExecuteParallelPath:
    """Test execute_parallel_path function."""

    @patch("yt_fts.core.batch_execution.console")
    def test_execute_parallel_success(self, mock_console):
        """Test parallel execution succeeds."""
        with patch("yt_fts.download.parallel_processor.ParallelBatchProcessor") as mock_processor_class:
            with patch("yt_fts.download.summary.print_summary") as mock_print_summary:
                mock_processor = MagicMock()
                mock_processor.process_channels.return_value = {"success": 5, "failed": 0}
                mock_processor_class.return_value = mock_processor

                channels = ["https://youtube.com/channel1"]
                quota_strategy = MagicMock()

                # Create a mock display plugin
                mock_display_plugin = MagicMock()
                mock_display_plugin.get_formatter.return_value = None
                mock_display_plugin.get_name.return_value = "default"

                result = execute_parallel_path(
                    channels=channels,
                    quota_strategy=quota_strategy,
                    language="en",
                    cookies_from_browser="",
                    delay=60.0,
                    max_retries=3,
                    continue_on_error=False,
                    time_per_channel=3600.0,
                    time_per_video=600.0,
                    time_per_batch=7200.0,
                    videos_download_per_channel=0,
                    videos_download_per_batch=0,
                    display_plugin=mock_display_plugin,
                    auto_backfill=False,
                    freshness_hours=24,
                    rich_progress=False,
                    rich_display="default",
                    use_phase2=False,
                    phase2_batch_size=100,
                    fzf=False,
                    parallel_workers=2,
                    fail_fast=False,
                    simple=False,
                    output_format="default",
                )

                assert result is True


class TestExecuteSequentialPath:
    """Test execute_sequential_path function."""

    @patch("yt_fts.core.batch_execution.console")
    def test_execute_sequential_success(self, mock_console):
        """Test sequential execution succeeds."""
        with patch("yt_fts.download.batch_downloader.BatchDownloader") as mock_downloader_class:
            with patch("yt_fts.core.batch_interrupt.graceful_interrupt_handler") as mock_handler:
                mock_downloader = MagicMock()
                mock_downloader_class.return_value = mock_downloader

                # Setup proper context manager mock
                from contextlib import contextmanager

                @contextmanager
                def mock_graceful_handler(downloader, fail_fast, export_report):
                    yield None

                mock_handler.side_effect = mock_graceful_handler

                channels = ["https://youtube.com/channel1"]
                quota_strategy = MagicMock()

                execute_sequential_path(
                    channels=channels,
                    jobs=1,
                    language="en",
                    cookies_from_browser="",
                    delay=60.0,
                    max_retries=3,
                    continue_on_error=False,
                    rich_formatter=None,
                    rich_mode=None,
                    time_per_channel=3600.0,
                    time_per_video=600.0,
                    time_per_batch=7200.0,
                    videos_download_per_channel=0,
                    channels_download_per_batch=0,
                    videos_download_per_batch=0,
                    quota_strategy=quota_strategy,
                    display_plugin="default",
                    auto_backfill=False,
                    freshness_hours=24,
                    transcribe_audio_only=False,
                    whisper_model="base",
                    fail_fast=False,
                    export_report="",
                )

                mock_downloader_class.assert_called_once()
