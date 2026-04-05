# yt_sync/syncer.py

from pathlib import Path
from typing import Any

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import utils
from .api_client import YouTubeAPIClient as APIClient
from .auditing import Auditor
from .discovery import VideoDiscoverer
from .downloader import Downloader
from .filtering import VideoFilterer
from .html_reporter import create_failed_downloads_report
from .metadata import MetadataManager
from .quality_checker import TempFileCleaner, VideoQualityChecker
from .reconciler import LibraryReconciler

logger = structlog.get_logger(__name__)
console = Console()


class ChannelSyncer:
    """
    Manages the synchronization process for a single YouTube channel.
    """

    def __init__(
        self,
        url: str,
        index: int,
        args: Any,
        all_filters: dict[str, Any],
        api_client: APIClient | None = None,
        display: Any | None = None,
        error_handler: Any | None = None,
    ) -> None:
        self.url = url
        self.index = index
        self.args = args
        self.all_filters = all_filters
        self.api_client = api_client
        self.display = display
        self.error_handler = error_handler

        self.primary_name: str | None = None
        self.display_name: str | None = None
        self.channel_id: str | None = None
        self.uploads_playlist_id: str | None = None
        self.target_dir: Path | None = None
        self.archive_file: Path | None = None

        self.discoverer: VideoDiscoverer | None = None
        self.metadata_manager: MetadataManager | None = None
        self.auditor: Auditor | None = None
        self.filterer: VideoFilterer | None = None
        self.reconciler: LibraryReconciler | None = None
        self.downloader: Any | None = None

    def process(self) -> None:
        """Main entry point for channel synchronization or auditing."""
        structlog.contextvars.bind_contextvars(channel_url=self.url)

        if not self._initialize():
            logger.error("Failed to initialize channel. Skipping.")
            return

        structlog.contextvars.bind_contextvars(
            channel_id=self.channel_id, channel_name=self.display_name
        )
        if self.display:
            self.display.set_current_channel(
                name=self.display_name,
                index=self.index,
                total=self.display.total_channels,
            )

        self._init_components()

        assert self.filterer is not None, "Filterer was not initialized"
        if self.filterer.skip:
            logger.info(
                f"⏭️ Skipping channel '{self.display_name}' as per 'skip: true' rule in filters file."
            )
            if self.display and self.display.current_channel:
                self.display.add_channel_result(
                    {
                        "name": self.display_name or "Unknown",
                        "status": "skipped",
                        "index": self.display.current_channel.get("index", 0),
                    }
                )
            return

        if self.args.audit:
            assert self.auditor is not None, "Auditor was not initialized"
            assert self.reconciler is not None, "Reconciler was not initialized"
            archived_ids, unmanaged_files = self.auditor.run_file_system_audit()

            self.reconciler.run_reconciliation_audit(archived_ids, unmanaged_files)

        else:
            self._run_sync()
        structlog.contextvars.clear_contextvars()

    def _initialize(self) -> bool:
        """Initializes channel info using the API as the primary method."""
        if not self.api_client:
            logger.warning(
                "API client is not configured. Initialization will rely on yt-dlp if needed."
            )

        try:
            if self.api_client:
                details = self.api_client.get_channel_details_from_url(self.url)
                if details:
                    (
                        self.primary_name,
                        self.display_name,
                        self.channel_id,
                        self.uploads_playlist_id,
                    ) = (
                        details["handle"],
                        details["title"],
                        details["id"],
                        details["uploads_playlist_id"],
                    )
                    logger.info(
                        f"✅ Channel identified: '{self.display_name}' ({self.primary_name})"
                    )
                else:
                    raise ValueError("API did not return channel details.")
            else:
                raise ValueError("API client not available.")

        except Exception as e:
            logger.debug(f"API handshake failed: {e}")
            if self.args.allow_yt_dlp_fallback:
                logger.warning("Falling back to yt-dlp for initialization.")
                try:
                    fallback_info = utils.extract_channel_info_with_ytdlp(self.url)
                    if not fallback_info:
                        raise ValueError("yt-dlp could not extract channel info.")
                    self.primary_name, self.display_name, self.uploads_playlist_id = (
                        fallback_info["handle"],
                        fallback_info["title"],
                        fallback_info["uploads_playlist_id"],
                    )
                    if self.uploads_playlist_id:
                        self.channel_id = "UU" + self.uploads_playlist_id[2:]
                    logger.info(
                        f"✅ Channel identified via fallback: '{self.display_name}' ({self.primary_name})"
                    )
                except Exception as fallback_e:
                    logger.error(f"yt-dlp fallback also failed: {fallback_e}")
                    return False
            else:
                logger.error(
                    "API handshake failed and yt-dlp fallback is not permitted. Skipping channel."
                )
                return False

        assert self.primary_name is not None and self.args.base_dir is not None
        self.target_dir = Path(self.args.base_dir) / utils.sanitize_filename(
            self.primary_name.lstrip("@")
        )
        self.target_dir.mkdir(parents=True, exist_ok=True)
        return True

    def _init_components(self) -> None:
        """Initialize all component classes."""
        assert (
            self.target_dir and self.primary_name
        ), "Cannot init components before initialization"

        metadata_dir = self.target_dir / ".metadata"
        metadata_dir.mkdir(exist_ok=True)
        self.archive_file = metadata_dir / "downloads.txt"

        self.discoverer = VideoDiscoverer(self.args, self.url, self.api_client)
        self.metadata_manager = MetadataManager(
            self.args, metadata_dir, self.api_client
        )

        channel_filters = self.all_filters.get(
            self.primary_name, self.all_filters.get("__default__", {})
        )
        self.filterer = VideoFilterer(channel_filters)

        self.auditor = Auditor(self.args, self.target_dir, self.archive_file)
        self.reconciler = LibraryReconciler(
            self.args,
            self.target_dir,
            self.archive_file,
            self.metadata_manager,
            self.filterer,
            self.discoverer,
            self.uploads_playlist_id,
        )
        self.downloader = Downloader(
            self.args, self.target_dir, self.archive_file, display=self.display
        )

    def _run_sync(self):
        """The main logic for discovering, filtering, and downloading videos for a channel."""
        assert (
            self.discoverer
            and self.auditor
            and self.channel_id
            and self.target_dir
            and self.archive_file
            and self.downloader
            and self.metadata_manager
            and self.filterer
            and self.display_name
        )

        if self.display:
            self.display.set_current_channel(
                self.display_name, self.index, self.display.total_channels
            )

        cleaner = TempFileCleaner(self.target_dir)
        cleaner.cleanup()
        self.auditor.find_and_remove_ghost_entries()

        archived_ids = self.auditor.read_archive_file()

        imported_count = self.auditor.auto_import_existing_files()
        if imported_count > 0:
            archived_ids = self.auditor.read_archive_file()

        needs_full_scan, new_ids_from_rss = self.discoverer.get_new_videos_via_rss(
            self.channel_id, archived_ids
        )

        all_channel_ids: set[str] = set()
        unarchived_ids: set[str] = new_ids_from_rss

        if needs_full_scan:
            all_channel_ids = self.discoverer.get_all_channel_video_ids(
                self.uploads_playlist_id
            )
            if not all_channel_ids:
                logger.error(
                    "Could not retrieve full video list for channel. Skipping."
                )
                return
            unarchived_ids = all_channel_ids - archived_ids
        else:
            all_channel_ids = archived_ids.union(new_ids_from_rss)

        quality_checker = VideoQualityChecker(
            self.args, self.target_dir, self.archive_file
        )
        (
            upgrade_candidates,
            unparsable_files,
        ) = quality_checker.check_for_upgrade_candidates(all_channel_ids)

        if unparsable_files:
            logger.warning(
                f"⚠️ Found {len(unparsable_files)} video files with no parsable [ID] in the filename."
            )
            for f in unparsable_files[:5]:
                logger.warning(f"  - Example unmanaged file: {f.name}")

        if upgrade_candidates:
            quality_checker.prepare_for_upgrade(upgrade_candidates)
            unarchived_ids.update(upgrade_candidates)

        if not unarchived_ids:
            logger.info("✅ All remote videos are already in the archive.")
            self._report_result(
                total_ids=len(all_channel_ids),
                attempted_downloads=0,
                upgrade_candidates=[],
                metadata={},
            )
            return

        logger.info(
            f"📊 Found {len(unarchived_ids)} videos to process ({len(upgrade_candidates)} quality upgrades)."
        )
        if unarchived_ids:
            metadata = self.metadata_manager.load_metadata_for_ids(list(unarchived_ids))
        videos_to_process = set(metadata.keys())

        if self.filterer.rules:
            videos_to_process = self.filterer.apply_filters(videos_to_process, metadata)
            filtered_out = len(unarchived_ids) - len(videos_to_process)
            if filtered_out > 0:
                logger.info(f"🚫 Filters excluded {filtered_out} videos.")

        if not videos_to_process:
            logger.info("✅ No videos to download after filtering.")
            self._report_result(
                total_ids=len(all_channel_ids),
                attempted_downloads=0,
                upgrade_candidates=upgrade_candidates,
                metadata={},
            )
            return

        if self.args.dry_run:
            logger.info(
                f"[DRY RUN] Would attempt to download {len(videos_to_process)} video(s)."
            )
            return

        self.downloader.download_videos(videos_to_process, metadata)
        self._report_result(
            total_ids=len(all_channel_ids),
            attempted_downloads=len(videos_to_process),
            upgrade_candidates=upgrade_candidates,
            metadata=metadata,
        )

    def _report_result(
        self,
        total_ids: int,
        attempted_downloads: int,
        upgrade_candidates: list[str],
        metadata: dict[str, dict[str, Any]],
    ):
        """Reports the result of a sync operation to either the TUI or the console."""
        if self.display:
            assert self.display_name is not None
            download_stats = self.downloader.get_download_stats()
            total_new = attempted_downloads - len(upgrade_candidates)
            result_data = {
                "name": self.display_name,
                "index": self.index,
                "status": "skipped"
                if self.filterer.skip
                else ("updated" if attempted_downloads > 0 else "complete"),
                "new_videos": total_new,
                "upgrades": len(upgrade_candidates),
                "failed": download_stats.get("failed", 0),
            }
            self.display.add_channel_result(result_data)
        else:
            self._print_final_summary(
                total_ids, attempted_downloads, upgrade_candidates, metadata
            )

    def _print_final_summary(
        self,
        total_ids: int,
        attempted_downloads: int,
        upgrade_candidates: list[str],
        metadata: dict[str, dict[str, Any]],
    ):
        """Prints a rich Panel summary to the console when not in TUI mode."""
        assert self.target_dir and self.downloader and self.metadata_manager

        display_path = self.target_dir.relative_to(Path(self.args.base_dir).resolve())
        stored_count = len(utils.get_video_files_in_dir(self.target_dir))
        dir_uri = self.target_dir.resolve().as_uri()
        location_link = f"[link={dir_uri}]{display_path}[/link]"

        download_stats = self.downloader.get_download_stats()
        successful_downloads = download_stats.get("successful", 0) + download_stats.get(
            "fallback_success", 0
        )
        failed_downloads = download_stats.get("failed", 0)

        summary_text = Text()
        summary_text.append("Library Status\n", style="bold bright_white")
        summary_text.append(Text.from_markup(f"  {'Location:':<15} {location_link}\n"))
        summary_text.append(f"  {'API Videos:':<15} {total_ids}\n")
        summary_text.append(f"  {'Stored Videos:':<15} {stored_count}\n")
        if attempted_downloads > 0:
            summary_text.append("\nSession Results\n", style="bold bright_white")
            summary_text.append(
                f"  {'Downloads:':<15} {attempted_downloads} attempted, {successful_downloads} successful, {failed_downloads} failed\n"
            )
        if upgrade_candidates:
            summary_text.append(
                f"  {'Upgrades:':<15} {len(upgrade_candidates)} videos replaced/upgraded\n"
            )
        failed_downloads_for_report = {}
        if self.error_handler and self.channel_id:
            channel_errors = self.error_handler.get_errors_for_channel(self.channel_id)
            if channel_errors:
                for error in channel_errors:
                    vid_id = error.get("video_id")
                    if vid_id:
                        title = error.get("title", f"Unknown Title ({vid_id})")
                        failed_downloads_for_report[vid_id] = title
            # Clear errors for this channel so they don't appear in the next channel's report
            self.error_handler.clear_channel_errors(self.channel_id)
        if failed_downloads_for_report:
            create_failed_downloads_report(
                failed_downloads_for_report, self.display_name, self.target_dir
            )
        completion_rate = (stored_count / total_ids) * 100 if total_ids > 0 else 0.0
        final_status = Text.from_markup(
            f"📈 Channel Completion: [bold]{completion_rate:.1f}%[/bold] ({stored_count}/{total_ids})"
        )
        console.print(
            Panel(
                summary_text,
                title=f"[bold green]✓ Summary: {self.display_name}[/bold green]",
                subtitle=final_status,
                border_style="dim",
                expand=False,
            )
        )
