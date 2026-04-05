# yt_sync/downloader.py

import logging
from pathlib import Path
from typing import Any

from .downloader_legacy import LegacyDownloader

# Import our two downloader backends
from .downloader_rich import RichDownloader

logger = logging.getLogger(__name__)


class Downloader:
    """
    This class acts as a factory and router.
    It inspects the command-line arguments and instantiates the appropriate
    downloader backend (either the new 'rich' version or the old 'legacy' version).
    """

    def __new__(
        cls, args: Any, target_dir: Path, archive_file: Path, display: Any = None
    ):
        if args.legacy_downloader:
            logger.info("⚙️ Using legacy subprocess-based downloader")
            return LegacyDownloader(args, target_dir, archive_file, display=display)
        else:
            try:
                # Try to instantiate the rich downloader, which might fail if
                # libraries are missing.
                downloader = RichDownloader(
                    args, target_dir, archive_file, display=display
                )
                return downloader
            except ImportError as e:
                logger.error(f"❌ Rich downloader unavailable: {e}")
                logger.warning("Falling back to legacy subprocess-based downloader")
                logger.info("💡 To fix this, run: pip install rich yt-dlp")
                return LegacyDownloader(args, target_dir, archive_file, display=display)

    # This __init__ is just for type hinting and won't actually be called
    # because __new__ returns an instance of a different class.
    def __init__(
        self, args: Any, target_dir: Path, archive_file: Path, display: Any = None
    ):
        self.args = args
        self.target_dir = target_dir
        self.archive_file = archive_file

    def download_videos(self, video_ids: set[str], metadata: dict[str, dict[str, Any]]):
        # This method will be handled by the instantiated class.
        raise NotImplementedError
