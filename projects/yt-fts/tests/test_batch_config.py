"""
Tests for batch_config module.

Tests BatchDownloadConfig dataclass and its methods.
"""
import pytest

from yt_fts.core.batch_config import BatchDownloadConfig


class TestBatchDownloadConfig:
    """Test BatchDownloadConfig dataclass."""

    def test_minimal_config(self):
        """Test creating config with minimal required parameters."""
        config = BatchDownloadConfig(input_file="channels.txt")
        assert config.input_file == "channels.txt"
        assert config.jobs == 1  # default
        assert config.language == "en"  # default
        assert config.delay == 60.0  # default

    def test_from_click_args_filters_none(self):
        """Test from_click_args filters out None values."""
        config = BatchDownloadConfig.from_click_args(
            input_file="channels.txt",
            jobs=4,
            language="es",
            irrelevant_param=None,  # Should be ignored
            another_none=None,
        )
        assert config.input_file == "channels.txt"
        assert config.jobs == 4
        assert config.language == "es"
        assert not hasattr(config, "irrelevant_param")

    def test_from_click_args_with_valid_input(self):
        """Test from_click_args with valid input file."""
        config = BatchDownloadConfig.from_click_args(input_file="channels.txt")
        assert config.input_file == "channels.txt"

    def test_get_effective_output_format_default(self):
        """Test get_effective_output_format returns default when no legacy flags."""
        config = BatchDownloadConfig(input_file="test.txt", output_format="json")
        assert config.get_effective_output_format() == "json"

    def test_get_effective_output_format_simple_override(self):
        """Test simple flag overrides output_format."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            output_format="json",
            simple=True,
        )
        assert config.get_effective_output_format() == "simple"

    def test_get_effective_output_format_fzf_override(self):
        """Test fzf flag overrides output_format."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            output_format="json",
            fzf=True,
        )
        assert config.get_effective_output_format() == "fzf"

    def test_get_effective_output_format_rich_override(self):
        """Test rich flags override output_format."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            output_format="json",
            rich=True,
        )
        assert config.get_effective_output_format() == "rich"

    def test_get_effective_output_format_rich_1_override(self):
        """Test rich_1 flag overrides output_format."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            output_format="json",
            rich_1=True,
        )
        assert config.get_effective_output_format() == "rich"

    def test_get_effective_output_format_richo_override(self):
        """Test richo flag overrides output_format."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            output_format="json",
            richo=True,
        )
        assert config.get_effective_output_format() == "rich"

    def test_get_rich_mode_new_rich(self):
        """Test get_rich_mode returns 'new' for rich flag."""
        config = BatchDownloadConfig(input_file="test.txt", rich=True)
        assert config.get_rich_mode() == "new"

    def test_get_rich_mode_new_rich_1(self):
        """Test get_rich_mode returns 'new' for rich_1 flag."""
        config = BatchDownloadConfig(input_file="test.txt", rich_1=True)
        assert config.get_rich_mode() == "new"

    def test_get_rich_mode_old_richo(self):
        """Test get_rich_mode returns 'old' for richo flag."""
        config = BatchDownloadConfig(input_file="test.txt", richo=True)
        assert config.get_rich_mode() == "old"

    def test_get_rich_mode_none(self):
        """Test get_rich_mode returns None when no rich flags set."""
        config = BatchDownloadConfig(input_file="test.txt")
        assert config.get_rich_mode() is None

    def test_should_use_parallel_true(self):
        """Test should_use_parallel returns True when parallel_workers > 1."""
        config = BatchDownloadConfig(input_file="test.txt", parallel_workers=4)
        assert config.should_use_parallel() is True

    def test_should_use_parallel_false(self):
        """Test should_use_parallel returns False when parallel_workers <= 1."""
        config = BatchDownloadConfig(input_file="test.txt", parallel_workers=1)
        assert config.should_use_parallel() is False

        config.parallel_workers = 0
        assert config.should_use_parallel() is False

    def test_get_fail_fast_default(self):
        """Test get_fail_fast returns True by default."""
        config = BatchDownloadConfig(input_file="test.txt")
        assert config.get_fail_fast() is True

    def test_get_fail_fast_disabled(self):
        """Test get_fail_fast returns False when no_fail_fast is True."""
        config = BatchDownloadConfig(input_file="test.txt", no_fail_fast=True)
        assert config.get_fail_fast() is False

    def test_get_skip_initial_delay_default(self):
        """Test get_skip_initial_delay returns True by default."""
        config = BatchDownloadConfig(input_file="test.txt")
        # Default is no_skip_initial_wait=False, so get_skip_initial_delay returns not False = True
        assert config.get_skip_initial_delay() is True

    def test_get_skip_initial_delay_disabled(self):
        """Test get_skip_initial_delay returns False when no_skip_initial_wait is True."""
        config = BatchDownloadConfig(input_file="test.txt", no_skip_initial_wait=True)
        # no_skip_initial_wait=True, so get_skip_initial_delay returns not True = False
        assert config.get_skip_initial_delay() is False

    def test_is_metadata_only_mode_true(self):
        """Test is_metadata_only_mode returns True for metadata-only settings."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            videos_download_per_channel=0,
            delay=60.0,
        )
        assert config.is_metadata_only_mode() is True

    def test_is_metadata_only_mode_false_videos_set(self):
        """Test is_metadata_only_mode returns False when videos_per_channel > 0."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            videos_download_per_channel=5,
            delay=60.0,
        )
        assert config.is_metadata_only_mode() is False

    def test_is_metadata_only_mode_false_delay_changed(self):
        """Test is_metadata_only_mode returns False when delay != 60.0."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            videos_download_per_channel=0,
            delay=30.0,
        )
        assert config.is_metadata_only_mode() is False

    def test_all_parameters_settable(self):
        """Test that all 41 parameters can be set."""
        config = BatchDownloadConfig(
            input_file="test.txt",
            import_file="import.txt",
            import_only=True,
            dry_run=True,
            output_file="output.txt",
            jobs=4,
            language="es",
            cookies_from_browser="chrome",
            delay=30.0,
            max_retries=5,
            continue_on_error=True,
            no_fail_fast=True,
            no_skip_initial_wait=True,
            time_per_video=300.0,
            time_per_channel=1800.0,
            time_per_batch=3600.0,
            limit=10,
            videos_download_per_channel=5,
            channels_download_per_batch=3,
            videos_download_per_batch=20,
            tui=True,
            export_report="report.json",
            display_plugin="rich",
            rich_progress=True,
            rich_display="compact",
            output_format="json",
            import_progress=True,
            richo=True,
            rich=True,
            rich_1=True,
            simple=True,
            fzf=True,
            quota_daily=5000,
            quota_conservative_pct=0.7,
            quota_aggressive_pct=1.3,
            use_phase2=True,
            phase2_batch_size=50,
            auto_backfill=True,
            freshness_hours=12,
            use_cache=False,
            transcribe_audio_only=True,
            whisper_model="small",
            parallel_workers=2,
        )
        assert config.input_file == "test.txt"
        assert config.jobs == 4
        assert config.parallel_workers == 2
        assert config.quota_daily == 5000
        assert config.use_phase2 is True
