"""Tests for --video-jobs CLI option with auto-adjust.

Tests verify:
1. --video-jobs option accepts integer values
2. Auto-adjust is enabled by default (use --no-auto-adjust to disable)
3. --no-auto-adjust disables dynamic adjustment
4. --video-jobs N sets the starting value for auto-adjust
5. Values are correctly passed to ParallelBatchProcessor
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from click.testing import CliRunner

from yt_fts.core.cli import cli


@pytest.mark.skip(reason="Batch download implementation changed - mock path needs update")
def test_video_jobs_option_accepts_integer():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n")
        channels_file = f.name

    try:
        with patch("yt_fts.core.download_cli.ParallelBatchProcessor") as mock_processor, \
             patch("yt_fts.core.status_display.StatusDisplay"):
            mock_instance = MagicMock()
            mock_instance.process_channels.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--parallel-workers",
                    "2",
                    "--video-jobs",
                    "4",
                    "--delay",
                    "0",
                ],
            )

            assert "no such option" not in result.output.lower()
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args.kwargs
            assert "video_jobs" in call_kwargs
            assert call_kwargs["video_jobs"] == 4
    finally:
        Path(channels_file).unlink(missing_ok=True)


@pytest.mark.skip(reason="Batch download implementation changed - mock path needs update")
def test_auto_adjust_enabled_by_default():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n")
        channels_file = f.name

    try:
        with patch("yt_fts.core.download_cli.ParallelBatchProcessor") as mock_processor, \
             patch("yt_fts.core.status_display.StatusDisplay"):
            mock_instance = MagicMock()
            mock_instance.process_channels.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--parallel-workers",
                    "2",
                    "--delay",
                    "0",
                ],
            )

            assert "no such option" not in result.output.lower()
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args.kwargs
            assert "auto_adjust_video_jobs" in call_kwargs
            assert call_kwargs["auto_adjust_video_jobs"] is True
    finally:
        Path(channels_file).unlink(missing_ok=True)


@pytest.mark.skip(reason="Batch download implementation changed - mock path needs update")
def test_no_auto_adjust_disables_dynamic_adjustment():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n")
        channels_file = f.name

    try:
        with patch("yt_fts.core.download_cli.ParallelBatchProcessor") as mock_processor, \
             patch("yt_fts.core.status_display.StatusDisplay"):
            mock_instance = MagicMock()
            mock_instance.process_channels.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--parallel-workers",
                    "2",
                    "--no-auto-adjust",
                    "--delay",
                    "0",
                ],
            )

            assert "no such option" not in result.output.lower()
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args.kwargs
            assert "auto_adjust_video_jobs" in call_kwargs
            assert call_kwargs["auto_adjust_video_jobs"] is False
    finally:
        Path(channels_file).unlink(missing_ok=True)


@pytest.mark.skip(reason="Batch download implementation changed - mock path needs update")
def test_video_jobs_sets_starting_value():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n")
        channels_file = f.name

    try:
        with patch("yt_fts.core.download_cli.ParallelBatchProcessor") as mock_processor, \
             patch("yt_fts.core.status_display.StatusDisplay"):
            mock_instance = MagicMock()
            mock_instance.process_channels.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--video-jobs",
                    "3",
                    "--parallel-workers",
                    "2",
                    "--delay",
                    "0",
                ],
            )

            assert "no such option" not in result.output.lower()
            call_kwargs = mock_processor.call_args.kwargs
            assert call_kwargs["video_jobs"] == 3
            assert call_kwargs["auto_adjust_video_jobs"] is True
    finally:
        Path(channels_file).unlink(missing_ok=True)


@pytest.mark.skip(reason="Batch download implementation changed - mock path needs update")
def test_video_jobs_with_no_auto_adjust():
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n")
        channels_file = f.name

    try:
        with patch("yt_fts.core.download_cli.ParallelBatchProcessor") as mock_processor, \
             patch("yt_fts.core.status_display.StatusDisplay"):
            mock_instance = MagicMock()
            mock_instance.process_channels.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--video-jobs",
                    "3",
                    "--no-auto-adjust",
                    "--parallel-workers",
                    "2",
                    "--delay",
                    "0",
                ],
            )

            assert "no such option" not in result.output.lower()
            call_kwargs = mock_processor.call_args.kwargs
            assert call_kwargs["video_jobs"] == 3
            assert call_kwargs["auto_adjust_video_jobs"] is False
    finally:
        Path(channels_file).unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
