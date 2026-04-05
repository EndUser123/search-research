# tests/test_discovery.py

import io
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest
from yt_sync.discovery import VideoDiscoverer


@pytest.fixture
def mock_args():
    """Fixture for mock arguments."""
    args = MagicMock()
    args.no_rss = False
    args.allow_yt_dlp_fallback = False
    return args


@pytest.fixture
def mock_api_client():
    """Fixture for mock API client."""
    return MagicMock()


@pytest.fixture
def video_discoverer(mock_args, mock_api_client):
    """Fixture for VideoDiscoverer instance."""
    channel_url = "https://www.youtube.com/channel/UCXIr2B-BU4z72wAcjG0OKuw"
    return VideoDiscoverer(mock_args, channel_url, mock_api_client)


def test_get_new_videos_via_rss_no_rss_flag(video_discoverer, mock_args):
    """Test RSS check skipped due to --no-rss flag."""
    mock_args.no_rss = True
    needs_full_scan, new_ids = video_discoverer.get_new_videos_via_rss(
        "channel_id", set()
    )
    assert needs_full_scan is True
    assert new_ids == set()


# --- START OF FIX ---
# The mock for urlopen was incorrect. It should return a file-like object
# that can be used as a context manager. io.BytesIO is perfect for this.


def test_get_new_videos_via_rss_no_new_videos(video_discoverer):
    """Test successful RSS feed retrieval with no new videos."""
    archived_ids = {"video1", "video2"}
    rss_xml = """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
        <entry><yt:videoId>video1</yt:videoId></entry>
        <entry><yt:videoId>video2</yt:videoId></entry>
    </feed>
    """
    mock_response = io.BytesIO(rss_xml.encode("utf-8"))
    with patch("urllib.request.urlopen", return_value=mock_response):
        needs_full_scan, new_ids = video_discoverer.get_new_videos_via_rss(
            "channel_id", archived_ids
        )
        assert needs_full_scan is False
        assert new_ids == set()


def test_get_new_videos_via_rss_partial_new_videos(video_discoverer):
    """Test RSS feed with some new videos."""
    archived_ids = {"video1"}
    rss_xml = """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
        <entry><yt:videoId>video1</yt:videoId></entry>
        <entry><yt:videoId>video3</yt:videoId></entry>
    </feed>
    """
    mock_response = io.BytesIO(rss_xml.encode("utf-8"))
    with patch("urllib.request.urlopen", return_value=mock_response):
        needs_full_scan, new_ids = video_discoverer.get_new_videos_via_rss(
            "channel_id", archived_ids
        )
        assert needs_full_scan is False
        assert new_ids == {"video3"}


def test_get_new_videos_via_rss_all_new_videos(video_discoverer):
    """Test RSS feed with all new videos, triggering full API sync."""
    archived_ids = set()
    rss_xml = """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
        <entry><yt:videoId>video1</yt:videoId></entry>
        <entry><yt:videoId>video2</yt:videoId></entry>
    </feed>
    """
    mock_response = io.BytesIO(rss_xml.encode("utf-8"))
    with patch("urllib.request.urlopen", return_value=mock_response):
        needs_full_scan, new_ids = video_discoverer.get_new_videos_via_rss(
            "channel_id", archived_ids
        )
        assert needs_full_scan is True
        assert new_ids == {"video1", "video2"}


# --- END OF FIX ---


def test_get_new_videos_via_rss_failure(video_discoverer):
    """Test failure to retrieve RSS feed, falling back to full discovery."""
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Failed to fetch RSS"),
    ):
        needs_full_scan, new_ids = video_discoverer.get_new_videos_via_rss(
            "channel_id", set()
        )
        assert needs_full_scan is True
        assert new_ids == set()


def test_get_all_channel_video_ids_api_success(video_discoverer, mock_api_client):
    """Test successful API retrieval of video IDs."""
    mock_api_client.get_all_video_ids_from_playlist.return_value = ["video1", "video2"]
    video_ids = video_discoverer.get_all_channel_video_ids("playlist_id")
    assert video_ids == {"video1", "video2"}
    mock_api_client.get_all_video_ids_from_playlist.assert_called_once_with(
        "playlist_id"
    )


def test_get_all_channel_video_ids_api_failure_with_fallback(
    video_discoverer, mock_api_client, mock_args
):
    """Test API failure with yt-dlp fallback enabled."""
    mock_args.allow_yt_dlp_fallback = True
    mock_api_client.get_all_video_ids_from_playlist.return_value = []
    with patch.object(
        video_discoverer,
        "_get_all_channel_video_ids_ytdlp",
        return_value={"video3", "video4"},
    ) as mock_fallback:
        video_ids = video_discoverer.get_all_channel_video_ids("playlist_id")
        assert video_ids == {"video3", "video4"}
        mock_fallback.assert_called_once()


def test_get_all_channel_video_ids_api_failure_no_fallback(
    video_discoverer, mock_api_client, mock_args
):
    """Test API failure without yt-dlp fallback."""
    mock_args.allow_yt_dlp_fallback = False
    mock_api_client.get_all_video_ids_from_playlist.return_value = []
    video_ids = video_discoverer.get_all_channel_video_ids("playlist_id")
    assert video_ids == set()


@patch("yt_sync.discovery.run_ytdlp_subprocess")
@patch("yt_sync.discovery.build_command")
def test_get_all_channel_video_ids_ytdlp_success(
    mock_build_command, mock_run_subprocess, video_discoverer, mock_args
):
    """Test successful retrieval of video IDs using yt-dlp."""
    mock_args.allow_yt_dlp_fallback = True
    mock_build_command.return_value = ["fake_command"]
    mock_run_subprocess.return_value = MagicMock(
        returncode=0, stdout='{"id": "video1"}\n{"id": "video2"}', stderr=""
    )

    video_ids = video_discoverer._get_all_channel_video_ids_ytdlp()

    assert video_ids == {"video1", "video2"}
    mock_build_command.assert_called_once()
    mock_run_subprocess.assert_called_once_with(["fake_command"])


@patch("yt_sync.discovery.build_command")
def test_get_all_channel_video_ids_ytdlp_command_failure(
    mock_build_command, video_discoverer, mock_args
):
    """Test failure to build yt-dlp command."""
    mock_args.allow_yt_dlp_fallback = True
    mock_build_command.return_value = None

    video_ids = video_discoverer._get_all_channel_video_ids_ytdlp()

    assert video_ids == set()


@patch("yt_sync.discovery.run_ytdlp_subprocess")
@patch("yt_sync.discovery.build_command")
def test_get_all_channel_video_ids_ytdlp_subprocess_failure(
    mock_build_command, mock_run_subprocess, video_discoverer, mock_args
):
    """Test yt-dlp subprocess failure."""
    mock_args.allow_yt_dlp_fallback = True
    mock_build_command.return_value = ["fake_command"]
    mock_run_subprocess.return_value = MagicMock(
        returncode=1, stdout="", stderr="Error occurred"
    )

    video_ids = video_discoverer._get_all_channel_video_ids_ytdlp()

    assert video_ids == set()


@patch("yt_sync.discovery.run_ytdlp_subprocess")
@patch("yt_sync.discovery.build_command")
def test_get_all_channel_video_ids_ytdlp_empty_output(
    mock_build_command, mock_run_subprocess, video_discoverer, mock_args
):
    """Test empty output from yt-dlp."""
    mock_args.allow_yt_dlp_fallback = True
    mock_build_command.return_value = ["fake_command"]
    mock_run_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

    video_ids = video_discoverer._get_all_channel_video_ids_ytdlp()

    assert video_ids == set()


@patch("yt_sync.discovery.run_ytdlp_subprocess")
@patch("yt_sync.discovery.build_command")
def test_get_all_channel_video_ids_ytdlp_json_error(
    mock_build_command, mock_run_subprocess, video_discoverer, mock_args
):
    """Test JSON parsing errors in yt-dlp output."""
    mock_args.allow_yt_dlp_fallback = True
    mock_build_command.return_value = ["fake_command"]
    mock_run_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='{"id": "video1"}\ninvalid_json_line\n{"id": "video2"}',
        stderr="",
    )

    video_ids = video_discoverer._get_all_channel_video_ids_ytdlp()

    assert video_ids == {"video1", "video2"}
