# yt_sync/downloader_legacy.py

import logging
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from . import utils

# --- THE FIX: Import the new, correct functions ---
from .ytdlp_legacy_wrapper import build_command, run_ytdlp_subprocess

logger = logging.getLogger(__name__)
TQDM_LOCK = threading.Lock()


class LegacyDownloader:
    def __init__(self, args: Any, target_dir: Path, archive_file: Path):
        self.args = args
        self.target_dir = target_dir
        self.archive_file = archive_file
        self.max_workers = self.args.concurrency_config.get("max_downloads", 4)

    def get_download_stats(self) -> dict[str, Any]:
        return {}

    def download_videos(self, video_ids: set[str], metadata: dict[str, dict[str, Any]]):
        """Downloads a set of videos using the legacy yt-dlp subprocess wrapper."""
        if not video_ids:
            return

        logger.info(
            f"Downloading {len(video_ids)} new video(s) using up to {self.max_workers} parallel workers..."
        )

        video_list = list(video_ids)

        with tqdm(
            total=len(video_list), desc="Downloading videos", unit="video"
        ) as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self._download_single_video_optimized,
                        video_id,
                        metadata.get(video_id, {}),
                    ): video_id
                    for video_id in video_list
                }

                for future in as_completed(futures):
                    video_id = futures[future]
                    video_metadata = metadata.get(video_id, {})
                    title = video_metadata.get("title", "Unknown Title")

                    try:
                        success, final_filename = future.result()
                        if success:
                            logger.info(
                                f"✔️ [{video_id}] Downloaded & Renamed to: {final_filename}"
                            )
                        else:
                            logger.error(
                                f"❌ [{video_id}] DOWNLOAD FAILED for '{title[:60]}...'. See logs above for details."
                            )
                    except Exception as e:
                        logger.error(
                            f"❌ [{video_id}] An unexpected error occurred during download for '{title[:60]}...': {e}",
                            exc_info=True,
                        )

                    pbar.update(1)

    def _download_single_video_optimized(
        self, video_id: str, metadata: dict[str, Any]
    ) -> (bool, str):
        """Downloads a single video, designed to be thread-safe."""
        title = metadata.get("title", "Unknown Title")
        url = f"https://www.youtube.com/watch?v={video_id}"

        with TQDM_LOCK:
            logger.info(f"📥 Starting download: {title[:60]}... [{video_id}]")

        format_selector = utils.get_optimal_format_selector(self.args)

        with tempfile.TemporaryDirectory(
            prefix=f"ytdl_temp_{video_id[:8]}_", dir=self.target_dir
        ) as temp_dir:
            temp_path = Path(temp_dir)
            temp_filename = f"ytdl_temp_{video_id}"

            download_cmd_args = [
                "--format",
                format_selector,
                "-o",
                str(temp_path / f"{temp_filename}.%(ext)s"),
                "--download-archive",
                str(self.archive_file),
                "--merge-output-format",
                "mp4",
            ]

            # --- THE FIX: Use the new modular functions ---
            command = build_command(
                self.args,
                download_cmd_args,
                url,
                per_call_config={"disable_sleep_interval": True},
            )
            if not command:
                logger.error(f"❌ [{video_id}] Could not build download command.")
                return False, ""

            result = run_ytdlp_subprocess(command)
            # --- END FIX ---

            if result.returncode != 0:
                if "HTTP Error 403" in result.stderr:
                    logger.error(
                        f"❌ [{video_id}] YouTube API access restricted (403 error). Consider using cookies."
                    )
                elif "cookie database" in result.stderr:
                    logger.error(
                        f"❌ [{video_id}] Browser cookie access failed. Ensure browser is completely closed."
                    )
                else:
                    logger.error(
                        f"❌ [{video_id}] Download failed. Stderr: {result.stderr.strip()}"
                    )
                return False, ""

            downloaded_files = list(temp_path.glob(f"{temp_filename}.*"))
            if not downloaded_files:
                logger.error(
                    f"❌ [{video_id}] No downloaded file found in temp directory after successful yt-dlp call."
                )
                return False, ""

            downloaded_file = max(downloaded_files, key=lambda p: p.stat().st_size)

            sanitized_title = utils.sanitize_filename(title)
            final_filename = f"{sanitized_title} [{video_id}]{downloaded_file.suffix}"
            final_path = self.target_dir / final_filename

            counter = 1
            while final_path.exists():
                final_filename = (
                    f"{sanitized_title} [{video_id}]_{counter}{downloaded_file.suffix}"
                )
                final_path = self.target_dir / final_filename
                counter += 1

            try:
                downloaded_file.rename(final_path)
                logger.debug(f"✅ [{video_id}] File moved to: {final_filename}")
                return True, final_filename
            except Exception as e:
                logger.error(f"❌ [{video_id}] Failed to rename/move file: {e}")
                return False, ""
