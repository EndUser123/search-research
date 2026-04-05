# tests/test_downloader.py

import logging
from unittest.mock import MagicMock, patch

import pytest
from yt_sync.downloader import Downloader
from yt_sync.downloader_legacy import LegacyDownloader
from yt_sync.downloader_rich import RichDownloader

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_args():
    """Fixture for mocking command-line arguments or configuration."""
    args = MagicMock()
    args.legacy_downloader = False
    args.concurrency_config = {"max_downloads": 4}
    return args


@pytest.fixture
def mock_args_legacy():
    """Fixture for mocking command-line arguments with legacy downloader flag."""
    args = MagicMock()
    args.legacy_downloader = True
    args.concurrency_config = {"max_downloads": 4}
    return args


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture for creating a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_display():
    """Fixture for mocking display object."""
    return MagicMock()


def test_downloader_init_rich(mock_args, temp_dir, mock_display):
    """Test Downloader instantiation with RichDownloader when legacy flag is not set."""
    archive_file = temp_dir / "archive.txt"
    with patch(
        "yt_sync.downloader.RichDownloader", return_value=MagicMock(spec=RichDownloader)
    ) as mock_rich:
        downloader = Downloader(mock_args, temp_dir, archive_file, display=mock_display)
        mock_rich.assert_called_once_with(
            mock_args, temp_dir, archive_file, display=mock_display
        )
        assert isinstance(downloader, RichDownloader)


def test_downloader_init_legacy_flag(mock_args_legacy, temp_dir, mock_display):
    """Test Downloader instantiation with LegacyDownloader when legacy flag is set."""
    archive_file = temp_dir / "archive.txt"
    with patch(
        "yt_sync.downloader.LegacyDownloader",
        return_value=MagicMock(spec=LegacyDownloader),
    ) as mock_legacy:
        downloader = Downloader(
            mock_args_legacy, temp_dir, archive_file, display=mock_display
        )
        mock_legacy.assert_called_once_with(
            mock_args_legacy, temp_dir, archive_file, display=mock_display
        )
        assert isinstance(downloader, LegacyDownloader)


def test_downloader_init_rich_import_error(mock_args, temp_dir, mock_display):
    """Test Downloader fallback to LegacyDownloader when RichDownloader import fails."""
    archive_file = temp_dir / "archive.txt"
    with (
        patch(
            "yt_sync.downloader.RichDownloader",
            side_effect=ImportError("Rich library not found"),
        ),
        patch(
            "yt_sync.downloader.LegacyDownloader",
            return_value=MagicMock(spec=LegacyDownloader),
        ) as mock_legacy,
    ):
        downloader = Downloader(mock_args, temp_dir, archive_file, display=mock_display)
        mock_legacy.assert_called_once_with(
            mock_args, temp_dir, archive_file, display=mock_display
        )
        assert isinstance(downloader, LegacyDownloader)


def test_downloader_download_videos_not_implemented(mock_args, temp_dir):
    """Test that download_videos method raises NotImplementedError in base Downloader class."""
    archive_file = temp_dir / "archive.txt"
    # Instantiate the base Downloader class directly without calling __new__
    downloader = object.__new__(Downloader)
    downloader.__init__(mock_args, temp_dir, archive_file)
    video_ids = {"video1"}
    metadata = {"video1": {"title": "Test Video 1"}}
    with pytest.raises(NotImplementedError):
        downloader.download_videos(video_ids, metadata)
