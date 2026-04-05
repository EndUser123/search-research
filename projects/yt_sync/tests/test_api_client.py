import json
from datetime import date
from unittest.mock import MagicMock, mock_open, patch

import googleapiclient.discovery
import pytest

# Mock googleapiclient before importing the module under test
mock_build = MagicMock()
mock_http_error = type("HttpError", (Exception,), {})

# Patch the imports in the module itself
with (
    patch("yt_sync.api_client.build", new=mock_build),
    patch("yt_sync.api_client.HttpError", new=mock_http_error),
):
    from yt_sync.api_client import DEFAULT_QUOTA, QUOTA_FILE, YouTubeAPIClient


@pytest.fixture
def mock_api_keys():
    return ["key1", "key2"]


@pytest.fixture
def mock_youtube_api_client(mock_api_keys):
    # Patch _read_quota_file and _write_quota_file during initialization
    # to prevent file operations during setup, but allow individual tests to patch them.
    with (
        patch("yt_sync.api_client.YouTubeAPIClient._read_quota_file"),
        patch("yt_sync.api_client.YouTubeAPIClient._write_quota_file"),
    ):
        client = YouTubeAPIClient(mock_api_keys)
        client.services = {}  # Ensure services is clean for each test
        client.quota_exceeded_keys = set()  # Ensure quota_exceeded_keys is clean
        client.estimated_quota = DEFAULT_QUOTA  # Reset quota for tests
        client.quota_spent_session = 0  # Reset session spend
        client.current_key_index = 0  # Reset key index
        mock_build.reset_mock()  # Reset the global mock_build call history
        mock_build.return_value = (
            MagicMock()
        )  # Reset the return value to a default mock
        mock_build.side_effect = None  # Clear any side effects
        return client


@pytest.fixture
def mock_request():
    mock_req = MagicMock()
    mock_req.uri = "https://example.com/api?key=key1"
    return mock_req


class TestYouTubeAPIClient:
    def test_init_success(self, mock_api_keys):
        with (
            patch(
                "yt_sync.api_client.YouTubeAPIClient._read_quota_file"
            ) as mock_read_quota,
            patch(
                "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
            ) as mock_write_quota,
        ):
            client = YouTubeAPIClient(mock_api_keys)
            assert client.api_keys == mock_api_keys
            assert client.current_key_index == 0
            assert client.services == {}
            assert client.quota_exceeded_keys == set()
            assert client.estimated_quota == DEFAULT_QUOTA
            assert client.quota_spent_session == 0
            mock_read_quota.assert_called_once()
            mock_write_quota.assert_not_called()  # Should not write on init if read is successful

    def test_init_import_error(self):
        with (
            patch("yt_sync.api_client.build", None),
            patch("yt_sync.api_client.HttpError", None),
        ):
            with pytest.raises(
                ImportError, match="Google API client libraries not found"
            ):
                YouTubeAPIClient(["key1"])

    @patch("yt_sync.api_client.date")
    def test_read_quota_file_exists_today(self, mock_date, mock_youtube_api_client):
        mock_date.today.return_value = date(2023, 1, 1)
        mock_file_content = json.dumps({"date": "2023-01-01", "quota": 5000})
        with (
            patch("builtins.open", mock_open(read_data=mock_file_content)),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
            ) as mock_write_quota,
        ):
            mock_youtube_api_client._read_quota_file()
            assert mock_youtube_api_client.estimated_quota == 5000
            mock_write_quota.assert_not_called()

    @patch("yt_sync.api_client.date")
    def test_read_quota_file_exists_not_today(self, mock_date, mock_youtube_api_client):
        mock_date.today.return_value = date(2023, 1, 2)
        mock_file_content = json.dumps({"date": "2023-01-01", "quota": 5000})
        with (
            patch("builtins.open", mock_open(read_data=mock_file_content)),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
            ) as mock_write_quota,
        ):
            mock_youtube_api_client._read_quota_file()
            assert mock_youtube_api_client.estimated_quota == DEFAULT_QUOTA
            mock_write_quota.assert_called_once()

    @patch("yt_sync.api_client.date")
    def test_read_quota_file_not_exists(self, mock_date, mock_youtube_api_client):
        mock_date.today.return_value = date(2023, 1, 1)
        with (
            patch("pathlib.Path.is_file", return_value=False),
            patch(
                "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
            ) as mock_write_quota,
        ):
            mock_youtube_api_client._read_quota_file()
            assert mock_youtube_api_client.estimated_quota == DEFAULT_QUOTA
            mock_write_quota.assert_called_once()

    @patch("yt_sync.api_client.date")
    def test_read_quota_file_json_decode_error(
        self, mock_date, mock_youtube_api_client
    ):
        mock_date.today.return_value = date(2023, 1, 1)
        with (
            patch("builtins.open", mock_open(read_data="invalid json")),
            patch("pathlib.Path.is_file", return_value=True),
            patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)),
            patch(
                "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
            ) as mock_write_quota,
        ):
            mock_youtube_api_client._read_quota_file()
            assert mock_youtube_api_client.estimated_quota == DEFAULT_QUOTA
            mock_write_quota.assert_called_once()

    @patch("yt_sync.api_client.date")
    def test_read_quota_file_io_error(self, mock_date, mock_youtube_api_client):
        mock_date.today.return_value = date(2023, 1, 1)
        with (
            patch("builtins.open", side_effect=OSError("permission denied")),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
            ) as mock_write_quota,
        ):
            mock_youtube_api_client._read_quota_file()
            assert mock_youtube_api_client.estimated_quota == DEFAULT_QUOTA
            mock_write_quota.assert_called_once()

    @patch("yt_sync.api_client.date")
    def test_write_quota_file_success(self, mock_date, mock_youtube_api_client):
        mock_date.today.return_value = date(2023, 1, 1)
        m_open = mock_open()
        with patch("builtins.open", m_open), patch("json.dump") as mock_json_dump:
            mock_youtube_api_client._write_quota_file()
            m_open.assert_called_once_with(QUOTA_FILE, "w")
            mock_json_dump.assert_called_once_with(
                {"date": "2023-01-01", "quota": DEFAULT_QUOTA}, m_open()
            )

    @patch("yt_sync.api_client.date")
    def test_write_quota_file_io_error(self, mock_date, mock_youtube_api_client):
        mock_date.today.return_value = date(2023, 1, 1)
        with (
            patch("builtins.open", side_effect=OSError("permission denied")),
            patch("yt_sync.api_client.logger") as mock_logger,
        ):
            mock_youtube_api_client._write_quota_file()
            mock_logger.error.assert_called_once_with(
                "Could not write to quota file: permission denied"
            )

    def test_get_service_success_new_key(
        self, mock_youtube_api_client, mock_api_keys, mocker
    ):
        # ARRANGE
        mock_youtube_api_client.api_keys = mock_api_keys
        mock_youtube_api_client.services = {}  # Ensure no existing service
        mock_youtube_api_client._get_next_available_key = MagicMock(
            return_value="key1"
        )  # Mock the key getter

        # Mock the build function imported in yt_sync/api_client.py
        mock_build = mocker.patch("yt_sync.api_client.build")
        mock_service_instance = MagicMock(spec=googleapiclient.discovery.Resource)
        mock_build.return_value = mock_service_instance

        # ACT
        service = mock_youtube_api_client._get_service()

        # ASSERT
        assert isinstance(service, googleapiclient.discovery.Resource)
        mock_build.assert_called_once_with("youtube", "v3", developerKey="key1")
        assert "key1" in mock_youtube_api_client.services

    def test_get_service_success_existing_key(
        self, mock_youtube_api_client, mock_api_keys
    ):
        mock_youtube_api_client.api_keys = mock_api_keys
        mock_youtube_api_client.services = {"key1": MagicMock()}
        mock_youtube_api_client.current_key_index = 0  # Set to use key1 first
        mock_build.reset_mock()

        service = mock_youtube_api_client._get_service()
        assert service is not None
        mock_build.assert_not_called()  # Should use existing service
        assert mock_youtube_api_client.current_key_index == 1

    def test_get_service_all_keys_exceeded(
        self, mock_youtube_api_client, mock_api_keys
    ):
        mock_youtube_api_client.api_keys = mock_api_keys
        mock_youtube_api_client.quota_exceeded_keys = set(mock_api_keys)
        with patch("yt_sync.api_client.logger") as mock_logger:
            service = mock_youtube_api_client._get_service()
            assert service is None
            mock_logger.error.assert_called_once_with(
                "All YouTube API keys have exceeded their quota."
            )

    def test_get_next_available_key_success(
        self, mock_youtube_api_client, mock_api_keys
    ):
        mock_youtube_api_client.api_keys = mock_api_keys
        key = mock_youtube_api_client._get_next_available_key()
        assert key == "key1"
        assert mock_youtube_api_client.current_key_index == 1
        key = mock_youtube_api_client._get_next_available_key()
        assert key == "key2"
        assert (
            mock_youtube_api_client.current_key_index == 2
        )  # After 2 calls, index is 2
        key = (
            mock_youtube_api_client._get_next_available_key()
        )  # Third call to test wrap-around
        assert key == "key1"
        assert (
            mock_youtube_api_client.current_key_index == 1
        )  # After wrap-around, index is 1

    def test_get_next_available_key_no_available_keys(
        self, mock_youtube_api_client, mock_api_keys
    ):
        mock_youtube_api_client.api_keys = mock_api_keys
        mock_youtube_api_client.quota_exceeded_keys = set(mock_api_keys)
        key = mock_youtube_api_client._get_next_available_key()
        assert key is None

    def test_get_next_available_key_skips_exceeded(
        self, mock_youtube_api_client, mock_api_keys
    ):
        mock_youtube_api_client.api_keys = ["key1", "key2", "key3"]
        mock_youtube_api_client.quota_exceeded_keys = {"key2"}

        key = mock_youtube_api_client._get_next_available_key()
        assert key == "key1"
        key = mock_youtube_api_client._get_next_available_key()
        assert key == "key3"
        key = mock_youtube_api_client._get_next_available_key()
        assert key == "key1"  # Cycles back to key1

    def test_execute_request_success(self, mock_youtube_api_client, mock_request):
        mock_request.execute.return_value = {"status": "success"}
        cost = 10

        with patch(
            "yt_sync.api_client.YouTubeAPIClient._write_quota_file"
        ) as mock_write:
            response = mock_youtube_api_client._execute_request(mock_request, cost)
            assert response == {"status": "success"}
            assert mock_youtube_api_client.estimated_quota == DEFAULT_QUOTA - cost
            assert mock_youtube_api_client.quota_spent_session == cost
            mock_write.assert_called_once()

    def test_execute_request_quota_exceeded(
        self, mock_youtube_api_client, mock_request
    ):
        mock_request.execute.side_effect = mock_http_error("quotaExceeded")
        mock_request.uri = (
            "https://www.googleapis.com/youtube/v3/channels?key=key1&part=snippet"
        )

        with (
            pytest.raises(mock_http_error),
            patch("yt_sync.api_client.logger") as mock_logger,
        ):
            mock_youtube_api_client._execute_request(mock_request, 1)
            assert "key1" in mock_youtube_api_client.quota_exceeded_keys
            mock_logger.warning.assert_called_once_with(
                "API key ending in ...key1 has exceeded its quota."
            )

    def test_execute_request_other_http_error(
        self, mock_youtube_api_client, mock_request
    ):
        mock_request.execute.side_effect = mock_http_error("other error")

        with pytest.raises(mock_http_error):
            mock_youtube_api_client._execute_request(mock_request, 1)
        assert (
            mock_youtube_api_client.estimated_quota == DEFAULT_QUOTA
        )  # Quota should not be deducted

    def test_get_quota_report(self, mock_youtube_api_client):
        mock_youtube_api_client.quota_spent_session = 50
        mock_youtube_api_client.estimated_quota = 9950
        report = mock_youtube_api_client.get_quota_report()
        assert report == "Session Spend: 50 | Daily Quota (Est.): 9950"

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch("yt_sync.api_client.YouTubeAPIClient._execute_request")
    def test_get_channel_details_from_url_success(
        self, mock_execute_request, mock_get_service, mock_youtube_api_client
    ):
        mock_get_service.return_value = MagicMock()
        mock_execute_request.return_value = {
            "items": [
                {
                    "id": "channel_id_123",
                    "snippet": {"title": "Test Channel"},
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "uploads_playlist_id_123"}
                    },
                }
            ]
        }

        channel_url = "https://www.youtube.com/@testchannel"
        details = mock_youtube_api_client.get_channel_details_from_url(channel_url)

        assert details == {
            "id": "channel_id_123",
            "handle": "@testchannel",
            "title": "Test Channel",
            "uploads_playlist_id": "uploads_playlist_id_123",
        }
        mock_get_service.assert_called_once()
        mock_execute_request.assert_called_once()

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service", return_value=None)
    def test_get_channel_details_from_url_no_service(
        self, mock_get_service, mock_youtube_api_client
    ):
        details = mock_youtube_api_client.get_channel_details_from_url(
            "https://www.youtube.com/@testchannel"
        )
        assert details is None
        mock_get_service.assert_called_once()

    @patch("yt_sync.api_client.logger")
    def test_get_channel_details_from_url_invalid_url(
        self, mock_logger, mock_youtube_api_client
    ):
        details = mock_youtube_api_client.get_channel_details_from_url(
            "https://www.youtube.com/channel/UC-invalid"
        )
        assert details is None
        mock_logger.error.assert_called_once_with(
            "Could not extract a valid @handle from URL: https://www.youtube.com/channel/UC-invalid"
        )

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch(
        "yt_sync.api_client.YouTubeAPIClient._execute_request",
        return_value={"items": []},
    )
    @patch("yt_sync.api_client.logger")
    def test_get_channel_details_from_url_api_no_items(
        self,
        mock_logger,
        mock_execute_request,
        mock_get_service,
        mock_youtube_api_client,
    ):
        mock_get_service.return_value = MagicMock()
        details = mock_youtube_api_client.get_channel_details_from_url(
            "https://www.youtube.com/@testchannel"
        )
        assert details is None
        mock_logger.error.assert_called_once_with(
            "API returned no items for handle: @testchannel"
        )

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch(
        "yt_sync.api_client.YouTubeAPIClient._execute_request",
        return_value={
            "items": [
                {
                    "id": "channel_id_123",
                    "snippet": {"title": "Test Channel"},
                    "contentDetails": {"relatedPlaylists": {}},  # Missing uploads
                }
            ]
        },
    )
    @patch("yt_sync.api_client.logger")
    def test_get_channel_details_from_url_missing_critical_info(
        self,
        mock_logger,
        mock_execute_request,
        mock_get_service,
        mock_youtube_api_client,
    ):
        mock_get_service.return_value = MagicMock()
        details = mock_youtube_api_client.get_channel_details_from_url(
            "https://www.youtube.com/@testchannel"
        )
        assert details is None
        mock_logger.error.assert_called_once_with(
            "API response for @testchannel was missing critical information."
        )

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch(
        "yt_sync.api_client.YouTubeAPIClient._execute_request",
        side_effect=Exception("API error"),
    )
    @patch("yt_sync.api_client.logger")
    def test_get_channel_details_from_url_api_exception(
        self,
        mock_logger,
        mock_execute_request,
        mock_get_service,
        mock_youtube_api_client,
    ):
        mock_get_service.return_value = MagicMock()
        details = mock_youtube_api_client.get_channel_details_from_url(
            "https://www.youtube.com/@testchannel"
        )
        assert details is None
        mock_logger.error.assert_called_once_with(
            "API error during channel handshake for @testchannel: API error"
        )

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch("yt_sync.api_client.YouTubeAPIClient._execute_request")
    def test_get_all_video_ids_from_playlist_single_page(
        self, mock_execute_request, mock_get_service, mock_youtube_api_client
    ):
        mock_get_service.return_value = MagicMock()
        mock_execute_request.return_value = {
            "items": [
                {"contentDetails": {"videoId": "video1"}},
                {"contentDetails": {"videoId": "video2"}},
            ]
        }

        video_ids = mock_youtube_api_client.get_all_video_ids_from_playlist(
            "playlist_id_123"
        )
        assert video_ids == ["video1", "video2"]
        mock_get_service.assert_called_once()
        mock_execute_request.assert_called_once()

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch("yt_sync.api_client.YouTubeAPIClient._execute_request")
    def test_get_all_video_ids_from_playlist_multi_page(
        self, mock_execute_request, mock_get_service, mock_youtube_api_client
    ):
        mock_get_service.return_value = MagicMock()
        mock_execute_request.side_effect = [
            {
                "items": [{"contentDetails": {"videoId": "video1"}}],
                "nextPageToken": "page2",
            },
            {
                "items": [{"contentDetails": {"videoId": "video2"}}],
                "nextPageToken": None,
            },
        ]

        video_ids = mock_youtube_api_client.get_all_video_ids_from_playlist(
            "playlist_id_123"
        )
        assert video_ids == ["video1", "video2"]
        assert mock_execute_request.call_count == 2

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service", return_value=None)
    def test_get_all_video_ids_from_playlist_no_service(
        self, mock_get_service, mock_youtube_api_client
    ):
        video_ids = mock_youtube_api_client.get_all_video_ids_from_playlist(
            "playlist_id_123"
        )
        assert video_ids == []
        mock_get_service.assert_called_once()

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch(
        "yt_sync.api_client.YouTubeAPIClient._execute_request",
        side_effect=Exception("API error"),
    )
    @patch("yt_sync.api_client.logger")
    def test_get_all_video_ids_from_playlist_api_exception(
        self,
        mock_logger,
        mock_execute_request,
        mock_get_service,
        mock_youtube_api_client,
    ):
        mock_get_service.return_value = MagicMock()
        video_ids = mock_youtube_api_client.get_all_video_ids_from_playlist(
            "playlist_id_123"
        )
        assert video_ids == []
        mock_logger.error.assert_called_once_with(
            "API error fetching playlist items for playlist playlist_id_123: API error"
        )

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch("yt_sync.api_client.YouTubeAPIClient._execute_request")
    def test_get_videos_metadata_success(
        self, mock_execute_request, mock_get_service, mock_youtube_api_client
    ):
        mock_get_service.return_value = MagicMock()
        mock_execute_request.return_value = {
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "title": "Video Title 1",
                        "description": "Desc 1",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "channelTitle": "Channel 1",
                        "channelId": "UC1",
                        "tags": ["tag1"],
                        "categoryId": "10",
                        "thumbnails": {"high": {"url": "thumb1.jpg"}},
                    },
                    "contentDetails": {"duration": "PT1H2M3S"},
                    "statistics": {"viewCount": "100", "likeCount": "10"},
                }
            ]
        }

        video_ids = ["video1"]
        metadata = mock_youtube_api_client.get_videos_metadata(video_ids)

        expected_metadata = {
            "video1": {
                "id": "video1",
                "title": "Video Title 1",
                "description": "Desc 1",
                "duration": 3723,
                "upload_date": "20230101",
                "uploader": "Channel 1",
                "uploader_id": "UC1",
                "view_count": 100,
                "like_count": 10,
                "tags": ["tag1"],
                "categories": ["10"],
                "thumbnail": "thumb1.jpg",
                "_api_source": "youtube_data_v3",
            }
        }
        assert metadata == expected_metadata
        mock_get_service.assert_called_once()
        mock_execute_request.assert_called_once()

    def test_get_videos_metadata_empty_ids(self, mock_youtube_api_client):
        metadata = mock_youtube_api_client.get_videos_metadata([])
        assert metadata == {}

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service", return_value=None)
    def test_get_videos_metadata_no_service(
        self, mock_get_service, mock_youtube_api_client
    ):
        metadata = mock_youtube_api_client.get_videos_metadata(["video1"])
        assert metadata == {}
        mock_get_service.assert_called_once()

    @patch("yt_sync.api_client.YouTubeAPIClient._get_service")
    @patch(
        "yt_sync.api_client.YouTubeAPIClient._execute_request",
        side_effect=Exception("API error"),
    )
    @patch("yt_sync.api_client.logger")
    def test_get_videos_metadata_api_exception(
        self,
        mock_logger,
        mock_execute_request,
        mock_get_service,
        mock_youtube_api_client,
    ):
        mock_get_service.return_value = MagicMock()
        metadata = mock_youtube_api_client.get_videos_metadata(["video1"])
        assert metadata == {}
        mock_logger.error.assert_called_once_with(
            "API error fetching video metadata chunk: API error"
        )

    @pytest.mark.parametrize(
        "duration_str, expected_seconds",
        [
            ("PT1H2M3S", 3723),
            ("PT30M", 1800),
            ("PT10S", 10),
            ("PT1H", 3600),
            ("PT0S", 0),
            ("", 0),
            ("invalid", 0),
            ("P1DT1H", 0),  # Only supports H, M, S
            ("PT0H0M0S", 0),  # Zero values
            ("PT9H59M59S", 35999),  # Max values (9*3600 + 59*60 + 59 = 35999)
            ("PT1H1M1S", 3661),  # Mixed values
            ("PT1H0M0S", 3600),  # Hours only, no minutes/seconds
            ("PT0H1M0S", 60),  # Minutes only, no hours/seconds
            ("PT0H0M1S", 1),  # Seconds only, no hours/minutes
            ("PT0H0M0S", 0),  # All zeros
            ("P1DT2H3M", 0),  # Days not supported
            ("PT-1H-1M-1S", 0),  # Negative values not supported
            ("PT.5H.5M.5S", 0),  # Decimal values not supported
            ("PT1H2", 0),  # Incomplete format
            ("PT1H2Z", 0),  # With timezone
            ("PT1H2+01:00", 0),  # With timezone offset
        ],
    )
    def test_parse_iso_duration(
        self, mock_youtube_api_client, duration_str, expected_seconds
    ):
        assert (
            mock_youtube_api_client._parse_iso_duration(duration_str)
            == expected_seconds
        )
