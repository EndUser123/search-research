# tests/test_downloader_legacy.py

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_sync.downloader_legacy import LegacyDownloader

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_args():
    """Fixture for mocking command-line arguments or configuration."""
    args = MagicMock()
    args.concurrency_config = {"max_downloads": 4}
    args.optimal_format = "bestvideo+bestaudio/best"
    return args


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture for creating a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_metadata():
    """Fixture for mocking video metadata."""
    return {"video1": {"title": "Test Video 1"}, "video2": {"title": "Test Video 2"}}


def test_legacy_downloader_init(mock_args, temp_dir):
    """Test initialization of LegacyDownloader."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    assert downloader.args == mock_args
    assert downloader.target_dir == temp_dir
    assert downloader.archive_file == archive_file
    assert downloader.max_workers == 4


def test_get_download_stats():
    """Test get_download_stats method returns an empty dictionary."""
    mock_args_instance = MagicMock()
    mock_args_instance.concurrency_config = {"max_downloads": 4}
    downloader = LegacyDownloader(mock_args_instance, Path("."), Path("archive.txt"))
    stats = downloader.get_download_stats()
    assert isinstance(stats, dict)
    assert len(stats) == 0


def test_download_videos_empty_set(mock_args, temp_dir):
    """Test download_videos with an empty set of video IDs."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_ids = set()
    metadata = {}
    with patch.object(
        downloader, "_download_single_video_optimized", return_value=(True, "test.mp4")
    ):
        downloader.download_videos(video_ids, metadata)
    # No assertions needed, just ensure no exceptions are raised


def test_download_videos_single_video(mock_args, temp_dir, mock_metadata):
    """Test download_videos with a single video ID."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_ids = {"video1"}
    with patch.object(
        downloader,
        "_download_single_video_optimized",
        return_value=(True, "test_video1.mp4"),
    ) as mock_download:
        with patch(
            "tqdm.tqdm",
            side_effect=lambda *args, **kwargs: MagicMock(update=lambda x: None),
        ):
            downloader.download_videos(video_ids, mock_metadata)
        mock_download.assert_called_once_with("video1", mock_metadata["video1"])


def test_download_videos_multiple_videos(mock_args, temp_dir, mock_metadata):
    """Test download_videos with multiple video IDs."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_ids = {"video1", "video2"}
    with patch.object(
        downloader,
        "_download_single_video_optimized",
        side_effect=[(True, "test_video1.mp4"), (True, "test_video2.mp4")],
    ) as mock_download:
        with patch(
            "tqdm.tqdm",
            side_effect=lambda *args, **kwargs: MagicMock(update=lambda x: None),
        ):
            downloader.download_videos(video_ids, mock_metadata)
        assert mock_download.call_count == 2


def test_download_videos_exception_handling(mock_args, temp_dir, mock_metadata):
    """Test download_videos handles exceptions during download."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_ids = {"video1"}
    with patch.object(
        downloader,
        "_download_single_video_optimized",
        side_effect=Exception("Download failed"),
    ):
        with patch(
            "tqdm.tqdm",
            side_effect=lambda *args, **kwargs: MagicMock(update=lambda x: None),
        ):
            downloader.download_videos(video_ids, mock_metadata)
    # No assertions needed, just ensure no exceptions are raised outside the method


def test_download_single_video_optimized_success(mock_args, temp_dir):
    """Test _download_single_video_optimized with a successful download."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}
    temp_file = temp_dir / "ytdl_temp_video1.mp4"
    temp_file.touch()  # Create an empty file to simulate download

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=0, stderr=""),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
        patch(
            "yt_sync.downloader_legacy.utils.sanitize_filename",
            return_value="Test_Video_1",
        ),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is True
        assert filename.startswith("Test_Video_1 [video1]")


def test_download_single_video_optimized_failure(mock_args, temp_dir):
    """Test _download_single_video_optimized with a failed download."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=1, stderr="Error"),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is False
        assert filename == ""


def test_download_single_video_optimized_403_error(mock_args, temp_dir):
    """Test _download_single_video_optimized handling HTTP 403 error."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=1, stderr="HTTP Error 403"),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is False
        assert filename == ""


def test_download_single_video_optimized_cookie_error(mock_args, temp_dir):
    """Test _download_single_video_optimized handling cookie database error."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=1, stderr="cookie database"),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is False
        assert filename == ""


def test_download_single_video_optimized_no_file_found(mock_args, temp_dir):
    """Test _download_single_video_optimized when no downloaded file is found."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=0, stderr=""),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
        patch(
            "yt_sync.downloader_legacy.utils.sanitize_filename",
            return_value="Test_Video_1",
        ),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is False
        assert filename == ""


def test_download_single_video_optimized_rename_failure(mock_args, temp_dir):
    """Test _download_single_video_optimized when file rename fails."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}
    temp_file = temp_dir / "ytdl_temp_video1.mp4"
    temp_file.touch()  # Create an empty file to simulate download

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=0, stderr=""),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
        patch(
            "yt_sync.downloader_legacy.utils.sanitize_filename",
            return_value="Test_Video_1",
        ),
        patch("pathlib.Path.rename", side_effect=Exception("Rename failed")),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is False
        assert filename == ""


def test_download_single_video_optimized_filename_conflict(mock_args, temp_dir):
    """Test _download_single_video_optimized handling filename conflicts."""
    archive_file = temp_dir / "archive.txt"
    downloader = LegacyDownloader(mock_args, temp_dir, archive_file)
    video_id = "video1"
    metadata = {"title": "Test Video 1"}
    temp_file = temp_dir / "ytdl_temp_video1.mp4"
    temp_file.touch()  # Create an empty file to simulate download
    existing_file = temp_dir / "Test_Video_1 [video1].mp4"
    existing_file.touch()  # Simulate existing file

    with (
        patch(
            "yt_sync.downloader_legacy.utils.get_optimal_format_selector",
            return_value="bestvideo+bestaudio/best",
        ),
        patch(
            "yt_sync.downloader_legacy.build_command",
            return_value=["yt-dlp", "--format", "bestvideo+bestaudio/best"],
        ),
        patch(
            "yt_sync.downloader_legacy.run_ytdlp_subprocess",
            return_value=MagicMock(returncode=0, stderr=""),
        ),
        patch(
            "tempfile.TemporaryDirectory",
            return_value=MagicMock(__enter__=lambda self: str(temp_dir)),
        ),
        patch(
            "yt_sync.downloader_legacy.utils.sanitize_filename",
            return_value="Test_Video_1",
        ),
    ):
        success, filename = downloader._download_single_video_optimized(
            video_id, metadata
        )
        assert success is True
        assert filename.startswith("Test_Video_1 [video1]_")
