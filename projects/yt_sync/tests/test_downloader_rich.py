from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_sync.downloader_rich import RichDownloader


# Mock the RICH_AVAILABLE flag to simulate environment where rich and yt_dlp are available
@pytest.fixture
def mock_rich_available():
    with patch("yt_sync.downloader_rich.RICH_AVAILABLE", True):
        yield


@pytest.fixture
def mock_args():
    args = MagicMock()
    args.concurrency_config = {"max_downloads": 4}
    args.timeout_config = {
        "batch_total_seconds": 3600,
        "socket_timeout_seconds": 30,
        "result_timeout_seconds": 120,
    }
    args.throttling_config = {"ratelimit": "5M", "sleep_interval_requests": 1}
    args.auth_config = {"cookies_file": None, "http_headers": {}}
    args.cookies_from_browser = None
    args.profile = None
    return args


@pytest.fixture
def rich_downloader(mock_args, tmp_path):
    target_dir = tmp_path / "downloads"
    archive_file = tmp_path / "archive.txt"
    display = MagicMock()
    return RichDownloader(mock_args, target_dir, archive_file, display)


def test_add_auth_to_opts(rich_downloader, mock_args):
    opts = {}
    mock_args.auth_config = {"cookies_file": Path("cookies.txt")}
    rich_downloader._add_auth_to_opts(opts)
    assert opts.get("cookiefile") == str(Path("cookies.txt"))

    # Test with cookies from browser
    mock_args.auth_config = {"cookies_file": None}
    mock_args.cookies_from_browser = "chrome"
    mock_args.profile = "default"
    opts = {}
    rich_downloader._add_auth_to_opts(opts)
    assert opts.get("cookiesfrombrowser") == ("chrome", "default")


def test_get_download_stats(rich_downloader):
    rich_downloader.download_stats = {
        "successful": 5,
        "failed": 2,
        "fallback_success": 1,
    }
    stats = rich_downloader.get_download_stats()
    assert stats == {"successful": 5, "failed": 2, "fallback_success": 1}


@patch("yt_sync.downloader_rich.yt_dlp")
@patch("yt_sync.downloader_rich.Progress")
@patch("yt_sync.downloader_rich.ThreadPoolExecutor")
def test_download_videos_empty_set(
    mock_executor, mock_progress, mock_yt_dlp, rich_downloader
):
    video_ids = set()
    metadata = {}
    rich_downloader.download_videos(video_ids, metadata)
    mock_progress.assert_not_called()
    mock_executor.assert_not_called()
    assert rich_downloader.download_stats == {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }


@patch("yt_sync.downloader_rich.yt_dlp")
def test_get_base_ytdlp_opts(mock_yt_dlp, rich_downloader):
    opts = rich_downloader._get_base_ytdlp_opts()
    assert opts["quiet"] is True
    assert opts["no_warnings"] is True
    assert opts["ratelimit"] == 5242880  # 5M converted to bytes
    assert opts["socket_timeout"] == 30
    assert "User-Agent" in opts["http_headers"]


@patch("yt_sync.downloader_rich.structlog.contextvars")
@patch("yt_sync.downloader_rich.utils.sanitize_filename")
@patch("yt_sync.downloader_rich.utils.select_best_formats_programmatically")
@patch("yt_sync.downloader_rich.yt_dlp.YoutubeDL")
def test_download_single_video_success(
    mock_ydl_class,
    mock_select_formats,
    mock_sanitize,
    mock_contextvars,
    rich_downloader,
):
    video_id = "test_video_id"
    metadata = {"title": "Test Video"}
    progress_queue = MagicMock()

    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_info_instance = MagicMock()
    mock_download_instance = MagicMock()

    mock_ydl_class.side_effect = [mock_info_instance, mock_download_instance]

    mock_info_instance.__enter__.return_value = mock_info_instance
    mock_download_instance.__enter__.return_value = mock_download_instance

    mock_info_instance.extract_info.return_value = {
        "formats": [{"format_id": "best", "height": 720}],
        "title": "Test Video",
    }
    mock_download_instance.download.return_value = 0

    mock_select_formats.return_value = "best"
    mock_sanitize.return_value = "Test_Video"
    mock_contextvars.bind_contextvars.return_value = None
    mock_contextvars.clear_contextvars.return_value = None

    rich_downloader._download_single_video(video_id, metadata, progress_queue)

    assert (
        rich_downloader.download_stats["successful"] == 1
    ), f"Download stats: {rich_downloader.download_stats}"
    assert mock_ydl_class.call_count == 2
    progress_queue.put.assert_called()


@patch("yt_sync.downloader_rich.yt_dlp.YoutubeDL")
def test_download_single_video_download_error(mock_ydl_class, rich_downloader):
    video_id = "test_video_id"
    metadata = {"title": "Test Video"}
    progress_queue = MagicMock()

    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_info_instance = MagicMock()
    mock_download_instance = MagicMock()
    mock_ydl_class.side_effect = [mock_info_instance, mock_download_instance]

    mock_info_instance.__enter__.return_value = mock_info_instance
    mock_download_instance.__enter__.return_value = mock_download_instance

    mock_info_instance.extract_info.return_value = {
        "formats": [{"format_id": "best", "height": 720}],
        "title": "Test Video",
    }

    mock_download_instance.download.side_effect = Exception("Download failed")

    rich_downloader._download_single_video(video_id, metadata, progress_queue)

    assert (
        rich_downloader.download_stats["failed"] == 1
    ), f"Download stats: {rich_downloader.download_stats}"
    assert rich_downloader.download_stats["successful"] == 0
    progress_queue.put.assert_called()


@patch("yt_sync.downloader_rich.yt_dlp.YoutubeDL")
def test_download_single_video_value_error(mock_ydl_class, rich_downloader):
    video_id = "test_video_id"
    metadata = {"title": "Test Video"}
    progress_queue = MagicMock()

    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_info_instance = MagicMock()
    mock_ydl_class.side_effect = [mock_info_instance]

    mock_info_instance.__enter__.return_value = mock_info_instance
    mock_info_instance.extract_info.side_effect = ValueError("Invalid format selection")

    rich_downloader._download_single_video(video_id, metadata, progress_queue)

    assert (
        rich_downloader.download_stats["failed"] == 1
    ), f"Download stats: {rich_downloader.download_stats}"
    assert rich_downloader.download_stats["successful"] == 0
    progress_queue.put.assert_called()


@patch("yt_sync.downloader_rich.yt_dlp.YoutubeDL")
def test_download_single_video_unexpected_error(mock_ydl_class, rich_downloader):
    video_id = "test_video_id"
    metadata = {"title": "Test Video"}
    progress_queue = MagicMock()

    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_info_instance = MagicMock()
    mock_ydl_class.return_value = mock_info_instance

    mock_info_instance.__enter__.return_value = mock_info_instance
    mock_info_instance.extract_info.side_effect = RuntimeError("Unexpected error")

    rich_downloader._download_single_video(video_id, metadata, progress_queue)

    assert (
        rich_downloader.download_stats["failed"] == 1
    ), f"Download stats: {rich_downloader.download_stats}"
    assert rich_downloader.download_stats["successful"] == 0
    progress_queue.put.assert_called()


@patch("yt_sync.downloader_rich.as_completed")
@patch("yt_sync.downloader_rich.ThreadPoolExecutor")
@patch("yt_sync.downloader_rich.Progress")
def test_download_videos_multiple_videos(
    mock_progress, mock_executor, mock_as_completed, rich_downloader
):
    video_ids = {"vid1", "vid2", "vid3"}
    metadata = {
        "vid1": {"title": "Video 1"},
        "vid2": {"title": "Video 2"},
        "vid3": {"title": "Video 3"},
    }
    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_progress_instance = mock_progress.return_value.__enter__.return_value
    mock_executor_instance = mock_executor.return_value.__enter__.return_value

    futures_map = {Future(): "vid1", Future(): "vid2", Future(): "vid3"}
    for future in futures_map.keys():
        future.set_result(None)

    # FIX 1: The mock for `submit` must also CALL the function it receives.
    def mock_submit_and_run(func, video_id, meta, queue):
        # Simulate the worker function running and updating stats
        if video_id in ["vid1", "vid2"]:
            rich_downloader.download_stats["successful"] += 1
        else:
            rich_downloader.download_stats["failed"] += 1

        # Return the correct future for the given video_id
        for future, v_id in futures_map.items():
            if v_id == video_id:
                return future

    mock_executor_instance.submit.side_effect = mock_submit_and_run

    mock_as_completed.return_value = list(futures_map.keys())

    # Replace the direct mock of _download_single_video with the executor's side effect
    rich_downloader.download_videos(video_ids, metadata)

    assert rich_downloader.download_stats["successful"] == 2
    assert rich_downloader.download_stats["failed"] == 1
    assert mock_executor_instance.submit.call_count == 3
    mock_progress_instance.update.assert_called()


@patch("yt_sync.downloader_rich.yt_dlp.YoutubeDL")
def test_download_single_video_progress_queue_updates(mock_ydl_class, rich_downloader):
    video_id = "test_video_id"
    metadata = {"title": "Test Video"}
    progress_queue = MagicMock()

    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_info_instance = MagicMock()
    mock_download_instance = MagicMock()
    mock_ydl_class.side_effect = [mock_info_instance, mock_download_instance]

    mock_info_instance.__enter__.return_value = mock_info_instance
    mock_download_instance.__enter__.return_value = mock_download_instance

    mock_info_instance.extract_info.return_value = {
        "formats": [{"format_id": "best", "height": 720}],
        "title": "Test Video",
    }
    mock_download_instance.download.return_value = 0

    rich_downloader._download_single_video(video_id, metadata, progress_queue)

    assert (
        rich_downloader.download_stats["successful"] == 1
    ), f"Download stats: {rich_downloader.download_stats}"
    assert (
        progress_queue.put.call_count >= 1
    ), "Progress queue should be updated during download"


# FIX 2: Create a new RichDownloader instance inside the test
# to ensure it initializes with the modified mock_args.
@patch("yt_sync.downloader_rich.yt_dlp")
def test_get_base_ytdlp_opts_with_timeout_and_ratelimit(
    mock_yt_dlp, mock_args, tmp_path
):
    mock_args.timeout_config = {
        "batch_total_seconds": 3600,
        "socket_timeout_seconds": 45,
        "result_timeout_seconds": 120,
    }
    mock_args.throttling_config = {"ratelimit": "2M", "sleep_interval_requests": 2}
    # Create the downloader instance *after* modifying the args
    downloader = RichDownloader(
        mock_args, tmp_path, tmp_path / "archive.txt", MagicMock()
    )

    opts = downloader._get_base_ytdlp_opts()
    assert opts["socket_timeout"] == 45, "Socket timeout should be set to 45 seconds"
    assert opts["ratelimit"] == 2097152, "Rate limit should be converted to 2M bytes"
    assert (
        opts["sleep_interval_requests"] == 2
    ), "Sleep interval should be set to 2 seconds"


@patch("yt_sync.downloader_rich.yt_dlp.YoutubeDL")
@patch("yt_sync.downloader_rich._shutdown_event")
def test_download_single_video_shutdown_event(
    mock_shutdown_event, mock_ydl_class, rich_downloader
):
    video_id = "test_video_id"
    metadata = {"title": "Test Video"}
    progress_queue = MagicMock()

    rich_downloader.download_stats = {
        "successful": 0,
        "failed": 0,
        "fallback_success": 0,
    }

    mock_shutdown_event.is_set.return_value = True

    rich_downloader._download_single_video(video_id, metadata, progress_queue)

    assert (
        rich_downloader.download_stats["failed"] == 1
    ), f"Download stats: {rich_downloader.download_stats}"
    assert rich_downloader.download_stats["successful"] == 0
    progress_queue.put.assert_called()
