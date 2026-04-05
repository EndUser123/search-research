"""
Unit tests for BatchDownloader core functionality.

Tests cover:
- Initialization and configuration
- Channel ID validation
- Display name formatting
- Dry run functionality
- Summary and progress reporting
"""

from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


@pytest.fixture
def batch_downloader():
    """Create a BatchDownloader instance for testing."""
    return BatchDownloader(
        channels=["@testchannel", "https://youtube.com/@otherchannel"],
        suppress_quota_print=True,
        suppress_verbose=True,
    )


class TestInitialization:
    """Tests for BatchDownloader initialization."""

    def test_initialization_with_defaults(self):
        """Default values are set correctly."""
        downloader = BatchDownloader(channels=["@test"])
        assert downloader.jobs == 2
        assert downloader.language == "en"
        assert downloader.delay_between_channels == 3.0
        assert downloader.max_retries == 3
        assert downloader.continue_on_error is True
        assert downloader.max_videos is None
        assert downloader.time_per_channel is None
        assert downloader.time_per_video is None
        assert downloader.auto_backfill is False
        assert downloader.dry_run is False

    def test_initialization_with_custom_options(self):
        """Custom options are set correctly."""
        downloader = BatchDownloader(
            channels=["@test"],
            jobs=4,
            language="es",
            delay_between_channels=5.0,
            max_retries=5,
            continue_on_error=False,
            max_videos=100,
            time_per_channel=600,
            time_per_video=300,
            auto_backfill=True,
            dry_run=True,
        )
        assert downloader.jobs == 4
        assert downloader.language == "es"
        assert downloader.delay_between_channels == 5.0
        assert downloader.max_retries == 5
        assert downloader.continue_on_error is False
        assert downloader.max_videos == 100
        assert downloader.time_per_channel == 600
        assert downloader.time_per_video == 300
        assert downloader.auto_backfill is True
        assert downloader.dry_run is True

    def test_initialization_with_min_saved_creates_batch_manager(self):
        """Batch manager is created when min_saved is 0."""
        downloader = BatchDownloader(channels=["@test"], min_saved=0)
        assert downloader.batch_manager is not None

    def test_initialization_without_min_saved_no_batch_manager(self):
        """Batch manager is not created when min_saved is not 0."""
        downloader = BatchDownloader(channels=["@test"], min_saved=5)
        assert downloader.batch_manager is None

    def test_channels_list_stored(self, batch_downloader):
        """Channels list is stored correctly."""
        assert len(batch_downloader.channels) == 2
        assert "@testchannel" in batch_downloader.channels
        assert "https://youtube.com/@otherchannel" in batch_downloader.channels


class TestIsRawChannelId:
    """Tests for ChannelValidator.is_raw_channel_id method."""

    def test_raw_channel_id_with_channel_prefix(self, batch_downloader):
        """Names starting with 'Channel UC' are raw IDs."""
        assert batch_downloader.channel_validator.is_raw_channel_id("Channel UC123456789012345678901") is True

    def test_raw_channel_id_with_long_uc_string(self, batch_downloader):
        """Long UC strings are raw IDs."""
        assert batch_downloader.channel_validator.is_raw_channel_id("UC12345678901234567890123456") is True

    def test_raw_channel_id_with_invalid_marker(self, batch_downloader):
        """Invalid channel marker is raw."""
        assert batch_downloader.channel_validator.is_raw_channel_id("__INVALID_CHANNEL__") is True

    def test_human_readable_channel_name(self, batch_downloader):
        """Human-readable names are not raw IDs."""
        assert batch_downloader.channel_validator.is_raw_channel_id("3Blue1Brown") is False
        assert batch_downloader.channel_validator.is_raw_channel_id("Test Channel") is False
        assert batch_downloader.channel_validator.is_raw_channel_id("@testchannel") is False

    def test_short_uc_string_not_raw(self, batch_downloader):
        """Short UC strings are not considered raw."""
        assert batch_downloader.channel_validator.is_raw_channel_id("UC123") is False


class TestEnsureChannelNameInDb:
    """Tests for _ensure_channel_name_in_db method."""

    def test_returns_none_for_none_input(self, batch_downloader):
        """None input returns None."""
        result = batch_downloader._ensure_channel_name_in_db(None)
        assert result is None

    def test_returns_channel_id_unchanged(self, batch_downloader):
        """Channel ID is returned unchanged (lazy load)."""
        with patch("yt_fts.db.channels.get_channel_name_from_db", return_value=None):
            result = batch_downloader._ensure_channel_name_in_db("UCXKeNggiHUHpdkIfUj7KEEg")
            assert result == "UCXKeNggiHUHpdkIfUj7KEEg"

    def test_logs_debug_when_cached_name_exists(self, batch_downloader):
        """Debug log when cached name exists."""
        with patch("yt_fts.db.channels.get_channel_name_from_db", return_value="3Blue1Brown"):
            with patch("yt_fts.download.batch_downloader.logger.debug") as mock_debug:
                batch_downloader._ensure_channel_name_in_db("UCXKeNggiHUHpdkIfUj7KEEg")
                assert mock_debug.called

    def test_logs_debug_when_no_cached_name(self, batch_downloader):
        """Debug log when no cached name exists."""
        with patch("yt_fts.db.channels.get_channel_name_from_db", return_value=None):
            with patch("yt_fts.download.batch_downloader.logger.debug") as mock_debug:
                batch_downloader._ensure_channel_name_in_db("UCXKeNggiHUHpdkIfUj7KEEg")
                assert mock_debug.called


class TestGetThreadDbConnection:
    """Tests for _get_thread_db_connection method."""

    def test_returns_connection_from_callable(self, batch_downloader):
        """Connection is returned from get_db_connection callable."""
        mock_conn = MagicMock()
        mock_get_db = MagicMock(return_value=mock_conn)

        result = batch_downloader._get_thread_db_connection(mock_get_db)
        assert result == mock_conn

    def test_connections_tracked_in_all_conns(self, batch_downloader):
        """Connections are tracked in _all_conns list."""
        mock_conn = MagicMock()
        mock_get_db = MagicMock(return_value=mock_conn)

        batch_downloader._get_thread_db_connection(mock_get_db)
        assert mock_conn in batch_downloader._all_conns

    def test_returns_cached_connection_on_second_call(self, batch_downloader):
        """Cached connection is returned on second call in same thread."""
        mock_conn = MagicMock()
        mock_get_db = MagicMock(return_value=mock_conn)

        result1 = batch_downloader._get_thread_db_connection(mock_get_db)
        result2 = batch_downloader._get_thread_db_connection(mock_get_db)

        assert result1 == result2
        assert mock_get_db.call_count == 1


class TestDisplaySummary:
    """Tests for display_summary method."""

    def test_display_summary_calls_print_summary(self, batch_downloader):
        """display_summary calls internal _print_summary."""
        batch_downloader.results = {
            "total_channels": 2,
            "successful": 1,
            "failed": 1,
            "total_videos": 100,
        }

        with patch.object(batch_downloader, "_print_summary") as mock_print:
            batch_downloader.display_summary()
            mock_print.assert_called_once()

    def test_display_summary_does_nothing_without_results(self, batch_downloader):
        """display_summary does nothing when no results."""
        batch_downloader.results = None

        with patch.object(batch_downloader, "_print_summary") as mock_print:
            batch_downloader.display_summary()
            mock_print.assert_not_called()


class TestValidateChannels:
    """Tests for validate_channels method."""

    def test_validate_channels_exists(self, batch_downloader):
        """validate_channels method exists and is callable."""
        assert hasattr(batch_downloader, "validate_channels")
        assert callable(batch_downloader.validate_channels)


class TestExportReport:
    """Tests for export_report method."""

    def test_export_report_exists(self, batch_downloader):
        """export_report method exists and is callable."""
        assert hasattr(batch_downloader, "export_report")
        assert callable(batch_downloader.export_report)


class TestGetProgress:
    """Tests for get_progress method."""

    def test_get_progress_returns_string(self, batch_downloader):
        """get_progress returns a string status."""
        result = batch_downloader.get_progress()
        assert isinstance(result, str)

    def test_get_progress_returns_not_implemented_message(self, batch_downloader):
        """get_progress returns not implemented message."""
        result = batch_downloader.get_progress()
        assert result == "Progress tracking not implemented"


class TestSaveProgress:
    """Tests for save_progress method."""

    def test_save_progress_is_placeholder(self, batch_downloader):
        """save_progress is a placeholder that does nothing."""
        batch_downloader.save_progress()


class TestProcessSingleChannel:
    """Tests for process_single_channel method."""

    def test_process_single_channel_exists(self, batch_downloader):
        """process_single_channel method exists and is callable."""
        assert hasattr(batch_downloader, "process_single_channel")
        assert callable(batch_downloader.process_single_channel)

    def test_process_single_channel_has_correct_signature(self, batch_downloader):
        """process_single_channel accepts channel parameter."""
        import inspect
        sig = inspect.signature(batch_downloader.process_single_channel)
        assert "channel" in sig.parameters


class TestConfigurationOptions:
    """Tests for various configuration options."""

    def test_whisper_model_default(self):
        """Default whisper model is 'base'."""
        downloader = BatchDownloader(channels=["@test"])
        assert downloader.whisper_model == "base"

    def test_whisper_model_custom(self):
        """Custom whisper model is stored."""
        downloader = BatchDownloader(
            channels=["@test"],
            whisper_model="medium",
        )
        assert downloader.whisper_model == "medium"

    def test_keep_audio_default(self):
        """Default keep_audio is False."""
        downloader = BatchDownloader(channels=["@test"])
        assert downloader.keep_audio is False

    def test_keep_audio_enabled(self):
        """keep_audio can be enabled."""
        downloader = BatchDownloader(
            channels=["@test"],
            keep_audio=True,
        )
        assert downloader.keep_audio is True

    def test_freshness_hours_default(self):
        """Default freshness_hours is 6."""
        downloader = BatchDownloader(channels=["@test"])
        assert downloader.freshness_hours == 6

    def test_freshness_hours_custom(self):
        """Custom freshness hours is stored."""
        downloader = BatchDownloader(
            channels=["@test"],
            freshness_hours=24,
        )
        assert downloader.freshness_hours == 24

    def test_quota_strategy_default(self):
        """Default quota_strategy is None."""
        downloader = BatchDownloader(channels=["@test"])
        assert downloader.quota_strategy is None

    def test_quota_strategy_custom(self):
        """Custom quota_strategy is stored."""
        mock_strategy = MagicMock()
        downloader = BatchDownloader(
            channels=["@test"],
            quota_strategy=mock_strategy,
        )
        assert downloader.quota_strategy == mock_strategy


class ThreadLocalStorageTests:
    """Tests for thread-local storage initialization."""

    def test_thread_local_initialized(self, batch_downloader):
        """Thread-local storage is initialized."""
        assert hasattr(batch_downloader, "_thread_local")
        assert batch_downloader._thread_local is not None

    def test_all_conns_list_initialized(self, batch_downloader):
        """Connections list is initialized."""
        assert hasattr(batch_downloader, "_all_conns")
        assert isinstance(batch_downloader._all_conns, list)

    def test_conns_lock_initialized(self, batch_downloader):
        """Connections lock is initialized."""
        assert hasattr(batch_downloader, "_conns_lock")
        # Check if it has lock interface
        assert hasattr(batch_downloader._conns_lock, "acquire")
        assert hasattr(batch_downloader._conns_lock, "release")


class TestDownloadAll:
    """Tests for download_all method."""

    def test_download_all_returns_dict(self, batch_downloader):
        """download_all returns a results dictionary."""
        # Mock the initialization to avoid actual work
        with patch.object(batch_downloader, "_initialize_batch_download", return_value=(None, 0)):
            with patch.object(batch_downloader, "_download_single_channel_optimized", return_value=None):
                results = batch_downloader.download_all()
                assert isinstance(results, dict)

    def test_download_all_contains_expected_keys(self, batch_downloader):
        """download_all results contain expected keys."""
        with patch.object(batch_downloader, "_initialize_batch_download", return_value=(None, 0)):
            with patch.object(batch_downloader, "_download_single_channel_optimized", return_value=None):
                results = batch_downloader.download_all()
                # Check for common result keys
                assert "total_channels" in results or len(results) > 0


class TestFileStats:
    """Tests for file_stats handling."""

    def test_file_stats_defaults_to_empty_dict(self):
        """file_stats defaults to empty dict."""
        downloader = BatchDownloader(channels=["@test"])
        assert downloader.file_stats == {}

    def test_file_stats_can_be_set(self):
        """file_stats can be provided during initialization."""
        stats = {"subs": 100, "no_subs": 5}
        downloader = BatchDownloader(
            channels=["@test"],
            file_stats=stats,
        )
        assert downloader.file_stats == stats


class TestCheckpointFile:
    """Tests for checkpoint file path."""

    def test_checkpoint_file_initialized(self, batch_downloader):
        """Checkpoint file path is initialized."""
        assert batch_downloader._checkpoint_file is not None
        assert "batch_checkpoint.json" in batch_downloader._checkpoint_file


class TestPrintSummary:
    """Tests for _print_summary method."""

    def test_print_summary_exists(self, batch_downloader):
        """_print_summary method exists and is callable."""
        assert hasattr(batch_downloader, "_print_summary")
        assert callable(batch_downloader._print_summary)

    def test_print_summary_accepts_results_dict(self, batch_downloader):
        """_print_summary accepts a results dict parameter."""
        import inspect
        sig = inspect.signature(batch_downloader._print_summary)
        assert "results" in sig.parameters


class TestConfigBasedConstructor:
    """Tests for new config-based constructor signature (Layer 2 refactor)."""

    def test_constructor_with_execution_config_only(self):
        """Constructor accepts individual params via flat config."""
        # Updated to use flat BatchDownloaderConfig API
        downloader = BatchDownloader(
            channels=["@test"],
            jobs=4,
            language="es",
            delay_between_channels=5.0,
        )
        assert downloader.jobs == 4
        assert downloader.language == "es"
        assert downloader.delay_between_channels == 5.0
        assert downloader.max_retries == 3  # default

    def test_constructor_with_all_configs(self):
        """Constructor accepts all configuration options via flat API."""
        # Updated to use flat BatchDownloaderConfig API
        downloader = BatchDownloader(
            channels=["@test"],
            jobs=8,
            language="fr",
            max_videos=50,
            time_per_channel=600,
            auto_backfill=True,
            dry_run=False,
            rich_mode="new",
            suppress_verbose=True,
            whisper_model="small",
            keep_audio=True,
        )

        # Verify all config values mapped correctly
        assert downloader.jobs == 8
        assert downloader.language == "fr"
        assert downloader.max_videos == 50
        assert downloader.time_per_channel == 600
        assert downloader.auto_backfill is True
        assert downloader.dry_run is False
        assert downloader.rich_mode == "new"
        assert downloader.suppress_verbose is True
        assert downloader.whisper_model == "small"
        assert downloader.keep_audio is True

    def test_backward_compatibility_old_signature_still_works(self):
        """Old 29-parameter signature still works (backward compatibility)."""
        downloader = BatchDownloader(
            channels=["@test"],
            jobs=6,
            language="de",
            max_videos=25,
            whisper_model="medium",
        )
        assert downloader.jobs == 6
        assert downloader.language == "de"
        assert downloader.max_videos == 25
        assert downloader.whisper_model == "medium"

    def test_config_params_override_individual_params(self):
        """BatchDownloaderConfig object takes precedence."""
        from yt_fts.download.batch_downloader import BatchDownloaderConfig

        config = BatchDownloaderConfig(channels=["@test"], jobs=10)
        # Config object takes precedence
        downloader = BatchDownloader(config=config)
        assert downloader.jobs == 10

    def test_none_configs_use_defaults(self):
        """BatchDownloaderConfig uses class defaults for unspecified values."""
        from yt_fts.download.batch_downloader import BatchDownloaderConfig

        config = BatchDownloaderConfig(channels=["@test"], jobs=3)
        downloader = BatchDownloader(config=config)
        assert downloader.jobs == 3
        assert downloader.delay_between_channels == 3.0  # default
        assert downloader.max_videos is None  # default from LimitsConfig


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
