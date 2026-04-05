# yt_sync/downloader_rich.py - Enhanced for Advanced TUI Integration

import logging
import queue
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    import yt_dlp
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )
else:
    yt_dlp = Any
    Progress = (
        BarColumn
    ) = (
        TextColumn
    ) = (
        TransferSpeedColumn
    ) = (
        TimeRemainingColumn
    ) = MofNCompleteColumn = SpinnerColumn = TaskID = Console = Any

try:
    import yt_dlp
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )

    RICH_AVAILABLE = True
except ImportError:
    (
        yt_dlp,
        Progress,
        BarColumn,
        TextColumn,
        TransferSpeedColumn,
        TimeRemainingColumn,
        MofNCompleteColumn,
        SpinnerColumn,
        TaskID,
        Console,
    ) = (None,) * 10
    RICH_AVAILABLE = False

from . import utils
from .error_tracker import ErrorTracker

logger = logging.getLogger(__name__)

_shutdown_event = threading.Event()


_shutdown_event = threading.Event()


class QuietYTDLLogger:
    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        spam_keywords = [
            "SABR streaming",
            "DRM protected",
            "formats have been skipped",
            "Some web client",
            "Some tv client",
            "experiment that applies DRM",
        ]
        if not any(spam in msg for spam in spam_keywords):
            logger.debug(f"YT-DLP (suppressed warning): {msg}")


class RichDownloader:
    def _add_auth_to_opts(self, opts: dict[str, Any]) -> None:
        """Adds authentication options to a yt-dlp options dictionary."""
        auth_config = getattr(self.args, "auth_config", {})
        if auth_config.get("cookies_file"):
            opts["cookiefile"] = str(auth_config["cookies_file"])
        elif getattr(self.args, "cookies_from_browser", None):
            profile_arg = getattr(self.args, "profile", None)
            opts["cookiesfrombrowser"] = (self.args.cookies_from_browser, profile_arg)

    def __init__(
        self,
        args: Any,
        target_dir: Path,
        archive_file: Path,
        display: Any | None = None,
    ):
        self.args = args
        self.target_dir = target_dir
        self.archive_file = archive_file
        self.display = display
        self.max_workers = self.args.concurrency_config.get("max_downloads", 4)
        self.error_tracker = ErrorTracker()
        self.download_stats = {"successful": 0, "failed": 0, "fallback_success": 0}

        timeout_config = getattr(args, "timeout_config", {})
        self.batch_timeout = timeout_config.get("batch_total_seconds", 3600)
        self.socket_timeout = timeout_config.get("socket_timeout_seconds", 30)
        self.result_timeout = timeout_config.get("result_timeout_seconds", 120)

        assert yt_dlp is not None
        if not RICH_AVAILABLE or not yt_dlp:
            raise ImportError(
                "Required libraries (rich, yt-dlp) are not installed. Please run: pip install rich yt-dlp"
            )

        assert Console is not None
        self.console = Console()

    def get_download_stats(self) -> dict[str, Any]:
        return self.download_stats.copy()

    def download_videos(
        self, video_ids: set[str], metadata: dict[str, dict[str, Any]]
    ) -> None:
        if not video_ids:
            return

        _shutdown_event.clear()
        self.download_stats = {"successful": 0, "failed": 0, "fallback_success": 0}

        video_count = len(video_ids)
        time.time()

        logger.info(
            f"🚀 Starting download of {video_count} videos with {self.max_workers} concurrent workers"
        )

        # Temporarily remove the console handler to prevent it from interfering with the progress display
        progress_queue: queue.Queue = queue.Queue()
        root_logger = logging.getLogger()
        console_handler = next(
            (
                h
                for h in root_logger.handlers
                if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
            ),
            None,
        )
        if console_handler:
            root_logger.removeHandler(console_handler)

        try:
            assert (
                Progress is not None
                and TextColumn is not None
                and BarColumn is not None
                and TransferSpeedColumn is not None
                and TimeRemainingColumn is not None
            )
            progress_columns = (
                TextColumn("[progress.description]{task.description}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            )
            with Progress(
                *progress_columns, console=self.console, transient=True
            ) as progress:
                overall_task = progress.add_task(
                    "[bold green]Overall Progress", total=video_count
                )

                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(
                            self._download_single_video,
                            video_id,
                            metadata.get(video_id, {}),
                            progress_queue,
                        ): video_id
                        for video_id in video_ids
                    }

                    # This loop waits for futures to complete, ensuring the Progress context stays alive.
                    for future in as_completed(futures):
                        video_id = futures[future]
                        try:
                            future.result()
                        except InterruptedError:
                            # This custom exception is raised by our worker if it sees the shutdown event.
                            logger.debug(
                                f"Download for {video_id} was correctly cancelled."
                            )
                        except Exception as e:
                            logger.error(
                                f"Download future for {video_id} raised an exception: {e}"
                            )
                        progress.update(overall_task, advance=1)

        finally:
            if console_handler:
                root_logger.addHandler(console_handler)

        total_success = (
            self.download_stats["successful"] + self.download_stats["fallback_success"]
        )
        logger.info(
            f"Download batch complete: {total_success} successful, {self.download_stats['failed']} failed"
        )
        if self.download_stats["failed"] > 0:
            logger.warning(
                f"⚠️ {self.download_stats['failed']} downloads failed. Check logs for details."
            )

    def _get_base_ytdlp_opts(self) -> dict[str, Any]:
        """Creates a base dictionary of yt-dlp options for the LIBRARY."""
        auth_config = getattr(self.args, "auth_config", {})
        http_headers = auth_config.get("http_headers", {})
        if "user-agent" not in {k.lower() for k in http_headers}:
            http_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

        def parse_ratelimit(limit_str: str | None) -> int | None:
            """Converts human-readable rate limit (e.g., '5M', '512K') to bytes."""
            if not limit_str or not isinstance(limit_str, str):
                return None
            limit_str = limit_str.upper()
            try:
                if limit_str.endswith("K"):
                    return int(float(limit_str[:-1]) * 1024)
                if limit_str.endswith("M"):
                    return int(float(limit_str[:-1]) * 1024 * 1024)
                return int(limit_str)
            except (ValueError, TypeError):
                return None

        return {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "nopart": True,
            "ratelimit": parse_ratelimit(self.args.throttling_config.get("ratelimit")),
            "sleep_interval_requests": self.args.throttling_config.get(
                "sleep_interval_requests"
            ),
            "socket_timeout": self.socket_timeout,
            "retries": 1,
            "ignoreerrors": False,
            "logger": QuietYTDLLogger(),
            "merge_output_format": "mp4",
            "no_overwrites": True,
            "http_headers": http_headers,
            "ignoreconfig": True,
        }

    def _download_single_video(
        self, video_id: str, metadata: dict[str, Any], q: queue.Queue
    ):
        """Downloads a single video and puts progress updates into the queue."""
        assert yt_dlp is not None

        def progress_hook(d: dict[str, Any]):
            # This hook is now only for non-TUI mode.
            if q:
                if d.get("status") in ["downloading", "finished"]:
                    q.put(d)

        status_tuple: tuple[str, str | None] = ("failed", None)
        # Bind context for this specific download task
        structlog.contextvars.bind_contextvars(
            video_id=video_id, title=metadata.get("title", "N/A")
        )
        try:
            if _shutdown_event.is_set():
                raise InterruptedError("Shutdown requested before task start.")
            url = f"https://www.youtube.com/watch?v={video_id}"
            info_opts = self._get_base_ytdlp_opts()
            self._add_auth_to_opts(info_opts)
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                video_info = ydl.extract_info(url, download=False, process=False)
            if not video_info or not isinstance(video_info, dict):
                raise ValueError("yt-dlp library did not return valid video info.")
            formats = video_info.get("formats", [])
            selected_format_id = utils.select_best_formats_programmatically(formats)
            title = video_info.get("title", "Unknown Title")
            sanitized_title = utils.sanitize_filename(title)
            final_filename_template = (
                self.target_dir / f"{sanitized_title} [{video_id}].%(ext)s"
            )
            download_opts = self._get_base_ytdlp_opts()
            self._add_auth_to_opts(download_opts)
            download_opts.update(
                {
                    "outtmpl": str(final_filename_template),
                    "download_archive": str(self.archive_file),
                    # Use a quality-gated format string for upgrades, but fallback to the safe
                    # programmatic selection to ensure new downloads don't fail on weird formats.
                    "format": f"{selected_format_id}/bestvideo[height>=?720]+bestaudio/best",
                    "progress_hooks": [progress_hook],
                }
            )
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([url])
                self.download_stats["successful"] += 1
                status_tuple = ("success", str(final_filename_template))
        except ValueError as e:
            self.download_stats["failed"] += 1
            self.error_tracker.add_error(video_id, "Format Selection Error", str(e))
        except yt_dlp.utils.DownloadError as e:
            self.download_stats["failed"] += 1
            error_msg = str(e).replace("ERROR: ", "").strip()
            self.error_tracker.add_error(video_id, "Download Error", error_msg)
        except InterruptedError:
            self.download_stats["failed"] += 1
            self.error_tracker.add_error(
                video_id, "Interrupted", "Download cancelled by user."
            )
        except Exception:
            self.download_stats["failed"] += 1
            tb_str = traceback.format_exc()
            self.error_tracker.add_error(video_id, "Unexpected Exception", tb_str)
        finally:
            if q:
                q.put(
                    {
                        "status": "finished",
                        "info_dict": {"id": video_id},
                        "result": status_tuple,
                    }
                )
            # Clear context for the next task in this thread
            structlog.contextvars.clear_contextvars()
