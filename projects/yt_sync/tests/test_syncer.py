from unittest.mock import MagicMock, patch

from yt_sync.syncer import ChannelSyncer


def test_init():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}
    mock_api_client = MagicMock()
    mock_display = MagicMock()
    mock_error_handler = MagicMock()

    with (
        patch("yt_sync.syncer.APIClient", return_value=mock_api_client),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        # Act
        syncer = ChannelSyncer(
            url=mock_url,
            index=mock_index,
            args=mock_args,
            all_filters=mock_all_filters,
            api_client=mock_api_client,
            display=mock_display,
            error_handler=mock_error_handler,
        )

        # Assert
        assert syncer.url == mock_url
        assert syncer.index == mock_index
        assert syncer.args == mock_args
        assert syncer.all_filters == mock_all_filters
        assert syncer.api_client == mock_api_client
        assert syncer.display == mock_display
        assert syncer.error_handler == mock_error_handler


def test_init_without_optional_params():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}

    with (
        patch("yt_sync.syncer.APIClient"),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        # Act
        syncer = ChannelSyncer(
            url=mock_url, index=mock_index, args=mock_args, all_filters=mock_all_filters
        )

        # Assert
        assert syncer.url == mock_url
        assert syncer.index == mock_index
        assert syncer.args == mock_args
        assert syncer.all_filters == mock_all_filters
        assert syncer.api_client is None
        assert syncer.display is None
        assert syncer.error_handler is None


def test_process():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}
    mock_api_client = MagicMock()
    mock_display = MagicMock()
    mock_error_handler = MagicMock()

    with (
        patch("yt_sync.syncer.APIClient", return_value=mock_api_client),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        syncer = ChannelSyncer(
            url=mock_url,
            index=mock_index,
            args=mock_args,
            all_filters=mock_all_filters,
            api_client=mock_api_client,
            display=mock_display,
            error_handler=mock_error_handler,
        )

        # Mock the _initialize method to return True
        syncer._initialize = MagicMock(return_value=True)

        # Mock the _init_components method
        syncer._init_components = MagicMock()

        # Mock the _run_sync method
        syncer._run_sync = MagicMock()

        # Mock the filterer attribute
        syncer.filterer = MagicMock()
        syncer.filterer.skip = False

        # Mock the auditor attribute
        syncer.auditor = MagicMock()

        # Mock the args.audit attribute
        syncer.args.audit = False

        # Act
        syncer.process()

        # Assert
        syncer._initialize.assert_called_once()
        syncer._init_components.assert_called_once()
        syncer._run_sync.assert_called_once()


def test_process_with_audit():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}
    mock_api_client = MagicMock()
    mock_display = MagicMock()
    mock_error_handler = MagicMock()

    with (
        patch("yt_sync.syncer.APIClient", return_value=mock_api_client),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        syncer = ChannelSyncer(
            url=mock_url,
            index=mock_index,
            args=mock_args,
            all_filters=mock_all_filters,
            api_client=mock_api_client,
            display=mock_display,
            error_handler=mock_error_handler,
        )

        # Mock the _initialize method to return True
        syncer._initialize = MagicMock(return_value=True)

        # Mock the _init_components method
        syncer._init_components = MagicMock()

        # Mock the filterer attribute
        syncer.filterer = MagicMock()
        syncer.filterer.skip = False

        # Mock the auditor attribute
        syncer.auditor = MagicMock()
        # --- FIX: Ensure the mocked method returns the correct tuple structure ---
        syncer.auditor.run_file_system_audit.return_value = (set(), [])

        # --- FIX: Mock the reconciler as well, since _init_components is patched ---
        syncer.reconciler = MagicMock()

        # Set args.audit to True
        syncer.args.audit = True

        # Act
        syncer.process()

        # Assert
        syncer._initialize.assert_called_once()
        syncer._init_components.assert_called_once()
        syncer.auditor.run_file_system_audit.assert_called_once()


def test_init_components():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}
    mock_api_client = MagicMock()
    mock_display = MagicMock()
    mock_error_handler = MagicMock()

    with (
        patch("yt_sync.syncer.APIClient", return_value=mock_api_client),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        syncer = ChannelSyncer(
            url=mock_url,
            index=mock_index,
            args=mock_args,
            all_filters=mock_all_filters,
            api_client=mock_api_client,
            display=mock_display,
            error_handler=mock_error_handler,
        )

        # Mock the _initialize method to return True
        syncer._initialize = MagicMock(return_value=True)

        # Mock the target_dir and primary_name attributes
        syncer.target_dir = MagicMock()
        syncer.primary_name = "test_channel"

        # Act
        syncer._init_components()

        # Assert
        assert syncer.discoverer is not None
        assert syncer.metadata_manager is not None
        assert syncer.filterer is not None
        assert syncer.auditor is not None
        assert syncer.downloader is not None


def test_initialize():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}
    mock_api_client = MagicMock()
    mock_display = MagicMock()
    mock_error_handler = MagicMock()

    with (
        patch("yt_sync.syncer.APIClient", return_value=mock_api_client),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        syncer = ChannelSyncer(
            url=mock_url,
            index=mock_index,
            args=mock_args,
            all_filters=mock_all_filters,
            api_client=mock_api_client,
            display=mock_display,
            error_handler=mock_error_handler,
        )

        # Mock the get_channel_details_from_url method to return a valid response
        mock_details = {
            "handle": "test_handle",
            "title": "Test Channel",
            "id": "test_id",
            "uploads_playlist_id": "test_uploads_playlist_id",
        }
        syncer.api_client.get_channel_details_from_url.return_value = mock_details

        # Mock the args.base_dir attribute
        syncer.args.base_dir = "/test/base/dir"

        # Act
        result = syncer._initialize()

        # Assert
        assert result is True
        assert syncer.primary_name == "test_handle"
        assert syncer.display_name == "Test Channel"
        assert syncer.channel_id == "test_id"
        assert syncer.uploads_playlist_id == "test_uploads_playlist_id"
        assert syncer.target_dir is not None


def test_run_sync():
    # Arrange
    mock_url = "http://example.com"
    mock_index = 1
    mock_args = MagicMock()
    mock_all_filters = {"__default__": {}}
    mock_api_client = MagicMock()
    mock_display = MagicMock()
    mock_error_handler = MagicMock()

    with (
        patch("yt_sync.syncer.APIClient", return_value=mock_api_client),
        patch("yt_sync.syncer.VideoDiscoverer"),
        patch("yt_sync.syncer.MetadataManager"),
        patch("yt_sync.syncer.Auditor"),
        patch("yt_sync.syncer.VideoFilterer"),
        patch("yt_sync.syncer.Downloader"),
    ):
        syncer = ChannelSyncer(
            url=mock_url,
            index=mock_index,
            args=mock_args,
            all_filters=mock_all_filters,
            api_client=mock_api_client,
            display=mock_display,
            error_handler=mock_error_handler,
        )

        # Mock the _initialize method to return True
        syncer._initialize = MagicMock(return_value=True)

        # Mock the _init_components method
        syncer._init_components = MagicMock()

        # Mock the discoverer attribute
        syncer.discoverer = MagicMock()
        syncer.discoverer.get_new_videos_via_rss.return_value = (True, ["video1"])
        syncer.discoverer.get_all_channel_video_ids.return_value = {"video1", "video2"}

        # Mock the filterer attribute
        syncer.filterer = MagicMock()
        syncer.filterer.skip = False

        # Mock the metadata_manager attribute
        syncer.metadata_manager = MagicMock()
        syncer.metadata_manager.load_metadata_for_ids.return_value = {
            "video1": {"title": "Video 1"}
        }

        # Mock the downloader attribute
        syncer.downloader = MagicMock()

        # Mock the archive_file attribute
        syncer.archive_file = MagicMock()

        # Mock the channel_id attribute
        syncer.channel_id = "test_channel_id"

        # Mock the target_dir attribute
        syncer.target_dir = MagicMock()
        syncer.target_dir.iterdir.return_value = []

        # Mock the display_name attribute
        syncer.display_name = "Test Channel"

        # Mock the auditor attribute
        syncer.auditor = MagicMock()
        syncer.auditor.auto_import_existing_files.return_value = 0
        syncer.auditor.read_archive_file.return_value = set()

        # Set dry_run to False
        syncer.args.dry_run = False

        # Mock the filterer.apply_filters method to return the same videos
        syncer.filterer.apply_filters = MagicMock(return_value=set(["video1"]))

        # Act
        syncer._run_sync()

        # Assert
        syncer.discoverer.get_new_videos_via_rss.assert_called_once()
        if syncer.discoverer.get_all_channel_video_ids.call_count > 0:
            syncer.discoverer.get_all_channel_video_ids.assert_called_once()
        syncer.metadata_manager.load_metadata_for_ids.assert_called_once()
        syncer.downloader.download_videos.assert_called_once()
