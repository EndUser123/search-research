import argparse
import asyncio
import os
import signal
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console

from .client import get_client, validate_credentials

# Import from new configuration system
try:
    from .config.integration import get_config_bridge, get_config_manager

    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False

from tqdm.contrib.logging import logging_redirect_tqdm

from .config.logging_config import cleanup_old_logs, set_run_id, setup_logging
from .config.settings import get_channels
from .display import show_enhanced_enumeration_display
from .download import download_all_media_from_channel, download_media_from_message
from .file_discovery_coordinator import FileDiscoveryCoordinator
from .plugins.enumeration import enumerate_media_in_channel
from .progress_factory import create_progress_display
from .reverse_sync import complete_database_filesystem_sync, fix_null_filename_records
from .storage import get_messages_to_download
from .utils import scan_and_organize_existing_files, scan_existing_files


class CLIHandler:
    """Handles command-line argument parsing and validation."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="Continue downloading unfinished media from Telegram channels. Updates enumeration and downloads only new/undownloaded files."
        )

        # Channel selection
        parser.add_argument("--channel", help="Channel to download from")

        # Special modes
        parser.add_argument(
            "--show-sharding-status",
            action="store_true",
            help="Display database sharding status for all channels and exit",
        )

        # Download options
        parser.add_argument(
            "--message-ids",
            nargs="+",
            type=int,
            help="Specific message IDs to download",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of messages to process (default: None, which means no limit)",
        )

        # Operation modes
        parser.add_argument(
            "--enumerate",
            choices=["full", "inc"],
            help="Perform full or incremental enumeration of media without downloading.",
        )
        parser.add_argument(
            "--continue",
            "--resume",
            action="store_true",
            dest="continue_download",
            help="Continue downloading unfinished media (default behavior when no other action specified)",
        )

        # File operations
        parser.add_argument(
            "--scan-existing",
            action="store_true",
            help="Scan for existing files in temp directory",
        )
        parser.add_argument(
            "--scan-and-organize",
            action="store_true",
            help="Scan and organize existing files in temp directory",
        )

        # Media filtering
        parser.add_argument(
            "--media-type",
            choices=["all", "video", "image", "text", "audio", "archive", "other"],
            default="all",
            help="Type of media to download: 'all' (default), 'video', 'image', 'text', 'audio', 'archive', or 'other'",
        )

        # Performance options
        parser.add_argument(
            "--timeout",
            type=int,
            default=None,
            help="Maximum duration in seconds for the entire download operation.",
        )
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="WARNING",
            help="Set the logging level for terminal output (default: WARNING). File logging remains at DEBUG level.",
        )

        # Progress display options
        progress_group = parser.add_argument_group("Progress Display Options")
        progress_group.add_argument(
            "--ui",
            choices=[
                "A",
                "B",
                "tqdm",
                "simple",
                "alive",
                "textual",
                "rich",
                "paneled",
                "quiet",
                "clean",
                "production",
            ],
            default="A",
            dest="progress_mode",
            help="User interface mode. `A` for standard display (default), `B` for enhanced display, `tqdm` for progress bars, `simple` for basic output, `alive` for animated progress, `textual` for TUI, `rich` for rich formatting.",
        )
        progress_group.add_argument(
            "--concurrent-downloads",
            "--max-concurrent",
            type=int,
            default=2,
            metavar="N",
            dest="concurrent_downloads",
            help="Number of concurrent downloads (default: 2, use 1 for cleanest display)",
        )
        progress_group.add_argument(
            "--no-file-progress",
            action="store_true",
            help="Disable individual file progress bars (show only overall progress)",
        )

        # Sync options
        sync_group = parser.add_argument_group("Sync Options")
        sync_group.add_argument(
            "--force-reverse-sync",
            action="store_true",
            help="Force reverse sync even if it appears unnecessary (creates database entries for existing files)",
        )
        sync_group.add_argument(
            "--skip-reverse-sync",
            action="store_true",
            help="Skip reverse sync entirely for faster startup (only use if you know database is up to date)",
        )
        sync_group.add_argument(
            "--bidirectional",
            action="store_true",
            help="Perform complete bidirectional sync: files→database AND database→files verification (applies to all channels if no --channel specified)",
        )
        sync_group.add_argument(
            "--maint",
            "-m",
            action="store_true",
            help="Run comprehensive maintenance: bidirectional sync, scan-and-organize, and database validation for all channels",
        )

        return parser

    def parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments."""
        return self.parser.parse_args()

    def validate_channel(self, channel: str | None, channels: dict[str, Any]) -> None:
        """Validate the specified channel exists."""
        if channel and channel not in channels:
            available_channels = ", ".join(channels.keys())
            raise ValueError(
                f"Invalid channel '{channel}'. Available channels: {available_channels}"
            )


class ConfigurationManager:
    """Manages application configuration and setup."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.config_bridge = None
        self.config_manager = None
        self.new_config_available = NEW_CONFIG_AVAILABLE

    def setup_environment(self) -> None:
        """Load environment variables and initialize configuration."""
        env_path = self.project_root / ".env"
        load_dotenv(env_path)

        if self.new_config_available:
            try:
                self.config_bridge = get_config_bridge()
                self.config_manager = get_config_manager()
            except Exception as e:
                logger.warning(f"Could not initialize new config system: {e}")

    def setup_logging(self, args: argparse.Namespace) -> None:
        """Initialize logging system."""
        # Generate unique run ID
        run_id = str(uuid.uuid4())
        set_run_id(run_id)

        # Determine log levels
        if self.new_config_available and self.config_bridge:
            try:
                logging_config = self.config_bridge.get_logging_config()
                console_level = args.log_level
                file_level = logging_config.get("file_level", args.log_level)
            except Exception as e:
                logger.warning(f"Could not load logging config: {e}")
                console_level = args.log_level
                file_level = args.log_level
        else:
            console_level = args.log_level
            file_level = args.log_level

        # Setup logging
        if args.progress_mode == "tqdm":
            setup_logging(
                console_level="WARNING", file_level=file_level, ui_type="tqdm"
            )
        else:
            setup_logging(
                console_level=console_level,
                file_level=file_level,
                ui_type=args.progress_mode,
            )

        # Clean up old logs
        cleanup_old_logs()

    def get_ui_config(
        self, progress_mode: str, no_file_progress: bool
    ) -> dict[str, Any]:
        """Get UI configuration."""
        if self.new_config_available and self.config_bridge:
            try:
                return self.config_bridge.get_ui_config(progress_mode)
            except Exception as e:
                logger.warning(f"Could not load UI config: {e}")

        # Fallback configuration
        return {
            "default_mode": progress_mode,
            "show_speed": True,
            "show_eta": True,
            "show_file_progress": not no_file_progress,
            "update_frequency": 0.1,
        }

    def log_config_status(self) -> None:
        """Log configuration system status."""
        if self.new_config_available and self.config_manager:
            try:
                config_summary = self.config_manager.get_effective_config_summary()
                logger.info(f"Using optimal configuration system:\n{config_summary}")
            except Exception as e:
                logger.warning(
                    f"New config system available but failed to load summary: {e}"
                )
        else:
            logger.info("Using legacy configuration system")

    def get_channel_paths(self, channel_name: str) -> tuple[str, str]:
        """Get temp and media paths for a channel."""
        if not self.config_bridge:
            raise RuntimeError("Configuration bridge not available")

        temp_path = str(self.config_bridge.get_channel_temp_path(channel_name))
        media_path = str(self.config_bridge.get_channel_media_path(channel_name))
        return temp_path, media_path


class MaintenanceService:
    """Handles maintenance operations like file organization and database sync."""

    def __init__(self, client):
        self.client = client

    async def run_maintenance(
        self, channels_to_process: list[tuple[str, Any]], args: argparse.Namespace
    ) -> int:
        """Run maintenance operations on specified channels."""
        print("🔧 Starting maintenance operations...")
        print(
            f"📊 Processing {len(channels_to_process)} channel(s): {', '.join([name for name, _ in channels_to_process])}"
        )

        if args.maint:
            print("🚀 COMPREHENSIVE MAINTENANCE MODE")
            print("This will perform:")
            print("  • File scan and organization")
            print("  • Database cleanup (fix invalid records)")
            print("  • Bidirectional sync (files ↔ database)")
            print("  • Comprehensive reporting")
        else:
            print("🔄 BIDIRECTIONAL SYNC MODE")
            print("This will sync files ↔ database in both directions")

        print("⏳ Please wait... this may take several minutes for large databases")
        print("")

        maintenance_stats = self._initialize_stats()

        for ch_name, ch_id in channels_to_process:
            print(f"🔧 Processing channel: {ch_name}")
            try:
                await self._process_channel_maintenance(
                    ch_name, ch_id, args, maintenance_stats
                )
                print(f"  ✅ Channel {ch_name} maintenance complete!")
            except Exception as e:
                print(f"  ❌ Channel {ch_name} maintenance failed: {e}")
                maintenance_stats["total_errors"] += 1
            print()

        self._report_maintenance_summary(
            maintenance_stats, len(channels_to_process), args
        )

        # Check if we should continue with downloads
        if not args.continue_download and not args.enumerate and not args.message_ids:
            logger.info("Maintenance completed. Use --continue to also run downloads.")
            return 0
        return -1  # Continue with downloads

    def _initialize_stats(self) -> dict[str, int]:
        """Initialize maintenance statistics."""
        return {
            "channels_processed": 0,
            "total_orphaned_files": 0,
            "total_missing_files": 0,
            "total_reconciled": 0,
            "total_organized": 0,
            "total_fixed_records": 0,
            "total_errors": 0,
        }

    async def _process_channel_maintenance(
        self, ch_name: str, ch_id: Any, args: argparse.Namespace, stats: dict[str, int]
    ) -> None:
        """Process maintenance for a single channel."""
        # File scan and organization (maintenance mode only)
        if args.maint:
            print("  📁 Step 1/3: Scanning and organizing files...")
            await scan_and_organize_existing_files(ch_name)
            stats["total_organized"] += 1
            print("  ✅ File organization complete")

        # Database cleanup (maintenance mode only)
        if args.maint:
            print("  🔧 Step 2/3: Fixing invalid database records...")
            null_filename_stats = await fix_null_filename_records(ch_name)
            if null_filename_stats["reset_to_pending"] > 0:
                print(
                    f"  ✅ Reset {null_filename_stats['reset_to_pending']} invalid records to pending"
                )
            else:
                print("  ✅ No invalid records found")
            stats["total_fixed_records"] += null_filename_stats["reset_to_pending"]

        # Bidirectional sync
        step_num = "3/3" if args.maint else "1/1"
        print(f"  🔄 Step {step_num}: Running bidirectional sync...")
        sync_results = await complete_database_filesystem_sync(ch_name, dry_run=False)

        # Handle enumeration if needed
        if sync_results.get("file_to_db", {}).get("enumeration_needed", False):
            await self._handle_auto_enumeration(ch_name, ch_id, stats)
            # Re-run sync after enumeration
            print("  🔄 Re-running bidirectional sync after enumeration...")
            sync_results = await complete_database_filesystem_sync(
                ch_name, dry_run=False
            )
            print("  ✅ Post-enumeration sync complete")

        # Collect statistics
        if "summary" in sync_results:
            summary = sync_results["summary"]
            stats["total_orphaned_files"] += summary.get("orphaned_files", 0)
            stats["total_missing_files"] += summary.get("missing_files", 0)
            stats["total_reconciled"] += summary.get("reconciled_total", 0)

        stats["channels_processed"] += 1

    async def _handle_auto_enumeration(
        self, ch_name: str, ch_id: Any, stats: dict[str, int]
    ) -> None:
        """Handle automatic enumeration when needed."""
        print(
            f"  📡 SMART MAINTENANCE: Auto-enumerating channel {ch_name} (no database records found)..."
        )
        try:
            await enumerate_media_in_channel(
                self.client,
                ch_id,
                limit=None,
                channel_name=ch_name,
                incremental=False,
                progress=None,
            )
            print(f"  ✅ Channel enumeration complete for {ch_name}")
        except Exception as e:
            print(f"  ❌ Channel enumeration failed for {ch_name}: {e}")
            logger.error(f"Enumeration failed for {ch_name}: {e}")
            stats["total_errors"] += 1

    def _report_maintenance_summary(
        self, stats: dict[str, int], total_channels: int, args: argparse.Namespace
    ) -> None:
        """Report maintenance operation summary."""
        print("🏁 MAINTENANCE SUMMARY:")
        print("=" * 50)
        print(f"Channels processed: {stats['channels_processed']}/{total_channels}")
        print(f"Orphaned files found: {stats['total_orphaned_files']}")
        print(f"Missing files found: {stats['total_missing_files']}")
        print(f"Files reconciled: {stats['total_reconciled']}")
        if args.maint:
            print(f"Channels organized: {stats['total_organized']}")
            print(f"Invalid records fixed: {stats['total_fixed_records']}")
        if stats["total_errors"] > 0:
            print(f"Errors: ❌ {stats['total_errors']}")
        print("=" * 50)
        print("🎉 Maintenance operations completed!")


class ChannelProcessor:
    """Handles channel processing operations."""

    def __init__(self, client, termination_event: asyncio.Event):
        self.client = client
        self.termination_event = termination_event

    async def process_channels(
        self,
        channels_to_process: list[tuple[str, Any]],
        args: argparse.Namespace,
        config_manager: ConfigurationManager,
        ui_config: dict[str, Any],
        overall_stats: dict[str, Any],
    ) -> None:
        """Process all specified channels."""
        console = Console()

        for current_channel_name, current_chat_id in channels_to_process:
            logger.info(
                f"DEBUG: Starting processing for channel '{current_channel_name}' with chat_id={current_chat_id}"
            )

            if self.termination_event.is_set():
                logger.info(
                    "\n🛑 Termination requested. Stopping before processing more channels..."
                )
                break

            try:
                await asyncio.wait_for(
                    self._process_single_channel(
                        current_channel_name,
                        current_chat_id,
                        args,
                        console,
                        ui_config,
                        config_manager,
                        overall_stats,
                    ),
                    timeout=300.0,  # 5 minute timeout per channel
                )
            except TimeoutError:
                logger.error(
                    f"⏰ Channel '{current_channel_name}' timed out after 5 minutes - skipping to next channel"
                )
                overall_stats["total_errors"] += 1
                continue
            except Exception as e:
                logger.error(
                    f"❌ Error processing channel '{current_channel_name}': {str(e)}"
                )
                overall_stats["total_errors"] += 1
                continue

            # Add channel divider (except for last channel)
            current_index = channels_to_process.index(
                (current_channel_name, current_chat_id)
            )
            if current_index < len(channels_to_process) - 1:
                print("---")

            # If a specific channel was requested, exit after processing it
            if args.channel:
                break

    async def _process_single_channel(
        self,
        channel_name: str,
        chat_id: Any,
        args: argparse.Namespace,
        console: Console,
        ui_config: dict[str, Any],
        config_manager: ConfigurationManager,
        overall_stats: dict[str, Any],
    ) -> None:
        """Process a single channel."""
        # Get channel paths
        current_temp_download_dir, current_save_directory = (
            config_manager.get_channel_paths(channel_name)
        )

        # Map UI modes
        display_mode = (
            "tqdm" if args.progress_mode in ["A", "B"] else args.progress_mode
        )
        progress_display = create_progress_display(
            mode=display_mode,
            show_file_progress=not args.no_file_progress,
            console=console,
            download_dir=current_save_directory,
            config=None,  # Will be set via UI config later
            log_level=args.log_level,
        )

        # Set up progress display
        logger.info(f"{channel_name}, .{os.sep}{current_save_directory}")
        print("⚠️ Press Ctrl+C to stop gracefully ⚠️")

        # Configure display for specific modes
        if args.progress_mode == "paneled":
            static_info = {
                "Channel": channel_name,
                "Chat ID": chat_id,
                "Save Directory": current_save_directory,
                "Temp Directory": current_temp_download_dir,
                "Limit": args.limit,
                "Concurrent Downloads": args.concurrent_downloads,
            }
            _set_info = getattr(progress_display, "set_static_info", None)
            if callable(_set_info):
                try:
                    _set_info(static_info)
                except Exception:
                    pass

        if args.progress_mode == "tqdm":
            _set_channel = getattr(progress_display, "set_channel_name", None)
            if callable(_set_channel):
                try:
                    _set_channel(channel_name)
                except Exception:
                    pass

        # Set global progress display reference
        global current_progress_display
        current_progress_display = progress_display

        async with progress_display:
            logger.info("Connected to Telegram")

        # Process channel operations
        await self._process_channel_operations(
            channel_name,
            chat_id,
            args,
            progress_display,
            current_save_directory,
            current_temp_download_dir,
            overall_stats,
        )

    async def _process_channel_operations(
        self,
        channel_name: str,
        chat_id: Any,
        args: argparse.Namespace,
        progress_display,
        current_save_directory: str,
        current_temp_download_dir: str,
        overall_stats: dict[str, Any],
    ) -> None:
        """Handle the actual channel operations."""
        try:
            # Scan existing files if requested
            if args.scan_and_organize:
                logger.debug(
                    f"Calling scan_and_organize_existing_files with channel_name='{channel_name}'"
                )
                await scan_and_organize_existing_files(channel_name)
            elif args.scan_existing:
                logger.debug(
                    f"Calling scan_existing_files with channel_name='{channel_name}'"
                )
                scan_existing_files(channel_name)

            # Early termination check
            if self.termination_event.is_set():
                return

            # Handle different operation modes
            if args.enumerate:
                await self._handle_enumeration(
                    channel_name, chat_id, args, progress_display
                )

            elif args.message_ids:
                await self._handle_specific_messages(
                    channel_name,
                    chat_id,
                    args,
                    progress_display,
                    current_save_directory,
                )

            else:
                # Default: continue downloading
                await self._handle_download(
                    channel_name,
                    chat_id,
                    args,
                    progress_display,
                    current_save_directory,
                )

            # Update overall statistics
            overall_stats["channels_processed"] += 1
            if progress_display and hasattr(progress_display, "stats"):
                downloaded = progress_display.stats.get("downloaded", 0)
                failed = progress_display.stats.get("failed", 0)
                if isinstance(downloaded, (int, float)):
                    overall_stats["total_downloaded"] += int(downloaded)
                if isinstance(failed, (int, float)):
                    overall_stats["total_errors"] += int(failed)

            logger.info(f"=== Completed Channel: {channel_name} ===\n")

        except Exception as e:
            logger.error(
                f"Error processing channel operations for '{channel_name}': {str(e)}"
            )
            overall_stats["total_errors"] += 1
            raise

    async def _handle_enumeration(
        self,
        channel_name: str,
        chat_id: Any,
        args: argparse.Namespace,
        progress_display,
    ) -> None:
        """Handle enumeration operations."""
        is_incremental = args.enumerate == "inc"
        await enumerate_media_in_channel(
            self.client,
            chat_id,
            args.limit,
            channel_name,
            is_incremental,
            progress_display,
            self.termination_event,
        )

        coordinator = FileDiscoveryCoordinator(
            channel_name, telegram_id=chat_id, client=self.client
        )
        discovery = await coordinator.discover_complete_file_state()
        await coordinator.coordinate_sync_operations(
            discovery, dry_run=False, progress=progress_display
        )

        # Note: Original code has incomplete enumeration logic here
        # This would need the rest of the enumeration handling

    async def _handle_specific_messages(
        self,
        channel_name: str,
        chat_id: Any,
        args: argparse.Namespace,
        progress_display,
        save_directory: str,
    ) -> None:
        """Handle downloading specific messages."""
        progress_display.add_main_task(
            "download",
            f"Downloading specific messages from {channel_name}",
            total=len(args.message_ids),
        )
        progress_display.start_main_task("download")

        for i, message_id in enumerate(args.message_ids):
            if (
                progress_display and progress_display.is_termination_requested()
            ) or self.termination_event.is_set():
                logger.info(
                    f"🛑 Termination requested. Stopping downloads after {i} messages..."
                )
                break
            await download_media_from_message(
                self.client, chat_id, message_id, save_directory, channel_name
            )
            progress_display.update_main_task(
                "download", advance=1, status=f"Downloaded message {message_id}"
            )

        progress_display.complete_main_task(
            "download", f"Messages from {channel_name} complete"
        )

    async def _handle_download(
        self,
        channel_name: str,
        chat_id: Any,
        args: argparse.Namespace,
        progress_display,
        save_directory: str,
    ) -> None:
        """Handle download operations."""
        logger.info(
            f"No specific operation requested, continuing download for {channel_name}"
        )

        # Show enhanced status display
        coordinator = FileDiscoveryCoordinator(
            channel_name, telegram_id=chat_id, client=self.client
        )
        discovery = await coordinator.discover_complete_file_state()
        await coordinator.coordinate_sync_operations(
            discovery, dry_run=False, progress=progress_display
        )

        messages_to_download = await get_messages_to_download(
            channel_name, telegram_id=chat_id
        )

        # Show enumeration display (this is a large block from original code)
        def count_by_ext(files, exts):
            return len([f for f in files if f.get("extension") in exts])

        video_exts = [".mp4", ".mkv", ".avi", ".mov"]
        image_exts = [".jpg", ".jpeg", ".png", ".gif"]
        audio_exts = [".mp3", ".wav", ".flac"]
        text_exts = [".txt", ".pdf", ".doc", ".docx"]

        stats = {
            "channel_name": channel_name,
            "unmatched_files": [f["full_path"] for f in discovery.filesystem_unmatched],
            "fs_total_files": len(discovery.files_on_disk),
            "fs_video_files": count_by_ext(discovery.files_on_disk, video_exts),
            "fs_image_files": count_by_ext(discovery.files_on_disk, image_exts),
            "fs_audio_files": count_by_ext(discovery.files_on_disk, audio_exts),
            "fs_text_files": count_by_ext(discovery.files_on_disk, text_exts),
            "fs_other_files": len(discovery.files_on_disk)
            - count_by_ext(
                discovery.files_on_disk,
                video_exts + image_exts + audio_exts + text_exts,
            ),
            "db_pending_files": len(messages_to_download),
            "matches_found": len(discovery.database_matched),
            "updated_to_completed": 0,
            "errors": 0,
            "db_total_media_files": discovery.total_discoverable,
            "db_video_files": 0,
            "db_image_files": 0,
            "db_audio_files": 0,
            "db_text_files": 0,
            "db_other_files": 0,
            "new_messages": 0,
            "new_media_files": 0,
            "new_video_files": 0,
            "new_image_files": 0,
            "new_audio_files": 0,
            "new_text_files": 0,
            "new_other_files": 0,
            "new_files_to_download": len(messages_to_download),
        }
        show_enhanced_enumeration_display(stats, ui_mode=args.progress_mode)

        logger.info(
            f"DEBUG: About to call download_all_media_from_channel for {channel_name}"
        )
        await download_all_media_from_channel(
            self.client,
            chat_id,
            save_directory,
            args.limit,
            channel_name,
            progress_display,
            args.concurrent_downloads,
            incremental=True,
            media_type_filter=args.media_type,
            force_reverse_sync=args.force_reverse_sync,
            skip_reverse_sync=args.skip_reverse_sync,
        )


class ApplicationRunner:
    """Orchestrates the main application flow."""

    def __init__(self):
        self.termination_event = None
        self.client = None
        self.current_progress_display = None

    async def run(self) -> int:
        """Run the main application."""
        try:
            # Initialize core components
            cli_handler = CLIHandler()
            config_manager = ConfigurationManager()

            # Parse arguments
            args = cli_handler.parse_args()

            # Setup environment and configuration
            config_manager.setup_environment()
            config_manager.setup_logging(args)

            # Load channels
            channels = get_channels()
            config_manager.log_config_status()

            # Handle sharding status display
            if args.show_sharding_status:
                return await self._show_sharding_status(channels)

            # Validate channel
            cli_handler.validate_channel(args.channel, channels)

            # Setup credentials and client
            api_id, api_hash, session_string = validate_credentials()
            self.client = await get_client(api_id, api_hash, session_string)

            # Determine channels to process
            channels_to_process = self._get_channels_to_process(args, channels)

            # Setup directories
            await self._setup_directories(config_manager, channels_to_process)

            # Handle maintenance mode
            maintenance_service = MaintenanceService(self.client)
            maint_result = await maintenance_service.run_maintenance(
                channels_to_process, args
            )
            if maint_result == 0:
                return 0  # Maintenance completed, exit

            # Run main processing
            return await self._run_main_processing(
                args, config_manager, channels_to_process
            )

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return 1

    async def _show_sharding_status(self, channels: dict[str, Any]) -> int:
        """Display database sharding status."""
        from .database.storage import get_storage

        logger.info("=" * 60)
        logger.info("DATABASE SHARDING STATUS REPORT")
        logger.info("=" * 60)

        for channel_name in sorted(channels.keys()):
            try:
                telegram_id = channels[channel_name]
                storage = get_storage(channel_name, telegram_id)
                sharding_status = storage.get_sharding_status()

                logger.info(f"\n📂 Channel: {channel_name}")
                logger.info(f"   Total Size: {sharding_status['total_size_gb']:.2f} GB")
                logger.info(f"   Total Messages: {sharding_status['total_messages']:,}")
                logger.info(
                    f"   Sharded: {'Yes' if sharding_status['is_sharded'] else 'No'}"
                )
                logger.info(f"   Shards: {sharding_status['total_shards']}")

                if sharding_status["needs_sharding"]:
                    logger.warning("   ⚠️ Exceeds sharding threshold (5GB)")
                if sharding_status["total_size_gb"] > 50:
                    logger.warning(
                        "   🔥 Very large database (>50GB) - performance impact expected"
                    )

                if sharding_status["shards"]:
                    logger.info("   Shard Details:")
                    for shard in sharding_status["shards"]:
                        current_marker = " (CURRENT)" if shard["is_current"] else ""
                        logger.info(
                            f"     - {shard['name']}: {shard['size_gb']:.2f}GB, {shard['message_count']:,} msgs{current_marker}"
                        )

            except Exception as e:
                logger.error(f"   Error getting status for {channel_name}: {e}")

        logger.info("\n" + "=" * 60)
        os._exit(0)

    def _get_channels_to_process(
        self, args: argparse.Namespace, channels: dict[str, Any]
    ) -> list[tuple[str, Any]]:
        """Determine which channels to process."""
        logger.info(f"Available channels: {', '.join(channels.keys())}")

        if args.channel:
            logger.debug(f"Using specified channel: {args.channel}")
            return [(args.channel, channels[args.channel])]
        else:
            channel_list = [(name, chat_id) for name, chat_id in channels.items()]
            logger.info(
                f"No channel specified, processing all {len(channel_list)} channels: {', '.join([name for name, _ in channel_list])}"
            )
            return channel_list

    async def _setup_directories(
        self,
        config_manager: ConfigurationManager,
        channels_to_process: list[tuple[str, Any]],
    ) -> None:
        """Setup temporary and media directories for channels."""
        for ch_name, _ in channels_to_process:
            temp_download_dir, media_download_dir = config_manager.get_channel_paths(
                ch_name
            )

            # Clean temp directory
            if os.path.exists(temp_download_dir):
                cleaned_files = 0
                locked_files = 0
                try:
                    for file_name in os.listdir(temp_download_dir):
                        file_path = os.path.join(temp_download_dir, file_name)
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                                cleaned_files += 1
                            except (PermissionError, OSError):
                                locked_files += 1

                    if cleaned_files > 0:
                        logger.info(
                            f"Cleaned up {cleaned_files} temp files from {temp_download_dir}"
                        )
                    if locked_files > 0:
                        logger.debug(f"Skipped {locked_files} locked temp files")

                except Exception as e:
                    logger.debug(
                        f"Could not access temp directory {temp_download_dir}: {e}"
                    )

            # Ensure directories exist
            os.makedirs(temp_download_dir, exist_ok=True)
            os.makedirs(media_download_dir, exist_ok=True)

    async def _run_main_processing(
        self,
        args: argparse.Namespace,
        config_manager: ConfigurationManager,
        channels_to_process: list[tuple[str, Any]],
    ) -> int:
        """Run the main channel processing loop."""
        self.termination_event = asyncio.Event()

        overall_stats = {
            "channels_processed": 0,
            "total_downloaded": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "total_timeouts": 0,
            "channel_details": [],
        }

        ui_config = config_manager.get_ui_config(
            args.progress_mode, args.no_file_progress
        )

        with logging_redirect_tqdm():
            try:
                channel_processor = ChannelProcessor(
                    self.client, self.termination_event
                )
                await channel_processor.process_channels(
                    channels_to_process, args, config_manager, ui_config, overall_stats
                )

                # Show overall summary if multiple channels
                if (
                    len(channels_to_process) > 1
                    and overall_stats["channels_processed"] > 0
                ):
                    self._show_overall_summary(
                        overall_stats, channels_to_process, self.termination_event
                    )

            except KeyboardInterrupt:
                logger.info("🛑 Ctrl+C received - exiting immediately")
                if self.termination_event:
                    self.termination_event.set()
                logger.info("Process terminated by user (Ctrl+C).")

            finally:
                await self._cleanup()

        return 1 if self.termination_event.is_set() else 0

    def _show_overall_summary(
        self,
        overall_stats: dict[str, Any],
        channels_to_process: list[tuple[str, Any]],
        termination_event: asyncio.Event,
    ) -> None:
        """Show overall processing summary."""
        logger.info("\n" + "=" * 50)
        if termination_event.is_set():
            logger.info("📈 PARTIAL RUN SUMMARY (INTERRUPTED)")
        else:
            logger.info("📈 OVERALL RUN SUMMARY")
        logger.info("=" * 50)
        logger.info(
            f"Channels processed: {overall_stats['channels_processed']}/{len(channels_to_process)}"
        )
        if termination_event.is_set():
            remaining_channels = (
                len(channels_to_process) - overall_stats["channels_processed"]
            )
            if remaining_channels > 0:
                logger.info(
                    f"Channels remaining: {remaining_channels} (can resume later)"
                )
        if overall_stats["total_downloaded"] > 0:
            logger.info(
                f"Total files downloaded: ✅ {overall_stats['total_downloaded']}"
            )
        if overall_stats["total_errors"] > 0:
            logger.info(f"Total errors: ❌ {overall_stats['total_errors']}")
        if overall_stats["total_skipped"] > 0:
            logger.info(f"Total skipped: ⏭️ {overall_stats['total_skipped']}")
        if overall_stats["total_timeouts"] > 0:
            logger.info(f"Total timeouts: ⏱️ {overall_stats['total_timeouts']}")
        logger.info("=" * 50)

    async def _cleanup(self) -> None:
        """Clean up resources."""
        # Cleanup progress display
        if self.current_progress_display is not None:
            try:
                logger.debug("Cleaning up progress display...")
                if hasattr(self.current_progress_display, "cleanup"):
                    await self.current_progress_display.cleanup()
                self.current_progress_display = None
                logger.debug("Progress display cleanup completed")
            except Exception as e:
                logger.debug(f"Progress display cleanup error: {e}")

        # Cleanup tqdm handler
        ch = globals().get("cleanup_tqdm_handler", None)
        if ch is not None:
            root_logger, tqdm_handler = ch
            try:
                root_logger.removeHandler(tqdm_handler)
            except Exception:
                pass
            finally:
                globals()["cleanup_tqdm_handler"] = None

        # Disconnect client
        if self.client is not None:
            try:
                await asyncio.wait_for(self.client.disconnect(), timeout=3.0)
            except TimeoutError:
                logger.warning(
                    "Client disconnect timed out after 3 seconds - forcing exit"
                )
            except Exception as e:
                logger.debug(f"Client disconnect error: {e}")


# Add PID management
# import sys
# sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "config"))
# from pid_manager import start_process_management


# Global variables for graceful termination (initialized at runtime)
termination_event = None
client = None
# Global reference to current progress display for clean shutdown
current_progress_display = None

# Global flag to track if shutdown is in progress
shutdown_in_progress = False
FORCE_EXIT_TIMEOUT = 3.0  # seconds


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    global termination_event, shutdown_in_progress

    def signal_handler(_signum, _frame):
        """Handle termination signals with enhanced cleanup and Windows batch fix."""
        global shutdown_in_progress
        import sys
        import threading
        import time

        from loguru import logger

        # Check if this is a second Ctrl+C (force exit)
        if shutdown_in_progress:
            logger.warning("⚡ Second Ctrl+C received - forcing immediate exit...")
            # Disable Windows batch prompt by exiting cleanly
            sys.exit(0)

        shutdown_in_progress = True

        # Use loguru logger for proper timestamp formatting
        logger.info("🛑 Ctrl+C received. Initiating graceful cleanup...")

        # Set termination event to signal all operations to stop
        if termination_event:
            termination_event.set()

        # Enhanced cleanup with timeout
        def graceful_cleanup_with_timeout():
            try:
                logger.info(
                    "✅ Graceful shutdown initiated - waiting for operations to complete..."
                )

                # Immediate exit for responsive shutdown
                time.sleep(0.1)

                logger.info("🚀 First Ctrl+C - exiting immediately")

                # Clean exit to avoid Windows batch prompt
                sys.exit(0)

            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                sys.exit(1)

        # Start cleanup in separate thread
        threading.Thread(target=graceful_cleanup_with_timeout, daemon=True).start()

        # Let asyncio handle graceful shutdown naturally
        # The termination_event.set() above will signal operations to stop

    # Setup signal handlers (Windows and Unix compatible)
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)


async def process_single_channel(
    channel_name,
    chat_id,
    args,
    console,
    ui_config,
    termination_event,
    client,
    overall_stats,
):
    """Process a single channel with proper error handling and timeouts"""
    try:
        # Set up directories for current channel using config system
        config_bridge = get_config_bridge()

        current_temp_download_dir = str(
            config_bridge.get_channel_temp_path(channel_name)
        )
        current_save_directory = str(config_bridge.get_channel_media_path(channel_name))

        # Map UI modes: A = tqdm (default), B = enhanced tqdm
        display_mode = (
            "tqdm" if args.progress_mode in ["A", "B"] else args.progress_mode
        )
        progress_display = create_progress_display(
            mode=display_mode,
            show_file_progress=not args.no_file_progress,
            console=console,
            download_dir=current_save_directory,
            config=ui_config,
            log_level=args.log_level,  # Pass log_level to display
        )

        # Clean channel header format
        logger.info(f"{channel_name}, .{os.sep}{current_save_directory}")

        # Show graceful stop warning before any channel processing
        print("⚠️ Press Ctrl+C to stop gracefully ⚠️")

        # If using paneled mode, set static info for the left pane
        if args.progress_mode == "paneled":
            static_info = {
                "Channel": channel_name,
                "Chat ID": chat_id,
                "Save Directory": current_save_directory,
                "Temp Directory": current_temp_download_dir,
                "Limit": args.limit,
                "Concurrent Downloads": args.concurrent_downloads,
            }
            # Optionally set static info if supported by the display
            _set_info = getattr(progress_display, "set_static_info", None)
            if callable(_set_info):
                try:
                    _set_info(static_info)  # type: ignore[misc]
                except Exception:
                    pass

        # Set channel name for TQDM display
        if args.progress_mode == "tqdm":
            _set_channel = getattr(progress_display, "set_channel_name", None)
            if callable(_set_channel):
                try:
                    _set_channel(channel_name)  # type: ignore[misc]
                except Exception:
                    pass

        # Set global reference for signal handler
        global current_progress_display
        current_progress_display = progress_display

        async with progress_display:
            # Connection is instant, no need for progress bar
            logger.info("Connected to Telegram")

        # Handle channel operations with timeout protection
        return await process_channel_operations(
            channel_name,
            chat_id,
            args,
            progress_display,
            current_save_directory,
            current_temp_download_dir,
            termination_event,
            client,
            overall_stats,
        )

    except Exception as e:
        logger.error(f"Error in process_single_channel for '{channel_name}': {str(e)}")
        raise


async def process_channel_operations(
    channel_name,
    chat_id,
    args,
    progress_display,
    current_save_directory,
    current_temp_download_dir,
    termination_event,
    client,
    overall_stats,
):
    """Handle the actual channel operations (scan, enumerate, download)"""
    try:
        # Scan for existing files if requested
        if args.scan_and_organize:
            logger.debug(
                f"Calling scan_and_organize_existing_files with channel_name='{channel_name}'"
            )
            await scan_and_organize_existing_files(channel_name)
        elif args.scan_existing:
            logger.debug(
                f"Calling scan_existing_files with channel_name='{channel_name}'"
            )
            scan_existing_files(channel_name)

        # Handle other operations with early termination checks
        if termination_event.is_set():
            return

        if args.enumerate:
            is_incremental = args.enumerate == "inc"
            await enumerate_media_in_channel(
                client,
                chat_id,
                args.limit,
                channel_name,
                is_incremental,
                progress_display,
                termination_event,
            )

            coordinator = FileDiscoveryCoordinator(
                channel_name, telegram_id=chat_id, client=client
            )
            discovery = await coordinator.discover_complete_file_state()
            await coordinator.coordinate_sync_operations(
                discovery, dry_run=False, progress=progress_display
            )

            messages_to_download = await get_messages_to_download(
                channel_name, telegram_id=chat_id
            )
            # ... (rest of enumerate logic)

        elif args.message_ids:
            # Download specific messages
            logger.debug(
                f"Calling download_media_from_message with channel_name='{channel_name}'"
            )
            progress_display.add_main_task(
                "download",
                f"Downloading specific messages from {channel_name}",
                total=len(args.message_ids),
            )
            progress_display.start_main_task("download")

            for i, message_id in enumerate(args.message_ids):
                if (
                    progress_display and progress_display.is_termination_requested()
                ) or termination_event.is_set():
                    logger.info(
                        f"🛑 Termination requested. Stopping downloads after {i} messages..."
                    )
                    break
                await download_media_from_message(
                    client, chat_id, message_id, current_save_directory, channel_name
                )
                progress_display.update_main_task(
                    "download", advance=1, status=f"Downloaded message {message_id}"
                )

            progress_display.complete_main_task(
                "download", f"Messages from {channel_name} complete"
            )

        elif args.continue_download:
            # Explicitly continue downloading unfinished media
            logger.debug(f"Continuing download for channel '{channel_name}'")
            await download_all_media_from_channel(
                client,
                chat_id,
                current_save_directory,
                args.limit,
                channel_name,
                progress_display,
                args.concurrent_downloads,
                incremental=True,
                media_type_filter=args.media_type,
                force_reverse_sync=args.force_reverse_sync,
                skip_reverse_sync=args.skip_reverse_sync,
            )
        else:
            # Default behavior: continue downloading unfinished media when no specific operation is requested
            logger.info(
                f"No specific operation requested, continuing download for {channel_name}"
            )

            # Show enhanced status display before downloading (moved from --enumerate flag)
            coordinator = FileDiscoveryCoordinator(
                channel_name, telegram_id=chat_id, client=client
            )
            discovery = await coordinator.discover_complete_file_state()
            await coordinator.coordinate_sync_operations(
                discovery, dry_run=False, progress=progress_display
            )

            messages_to_download = await get_messages_to_download(
                channel_name, telegram_id=chat_id
            )

            def count_by_ext(files, exts):
                return len([f for f in files if f.get("extension") in exts])

            video_exts = [".mp4", ".mkv", ".avi", ".mov"]
            image_exts = [".jpg", ".jpeg", ".png", ".gif"]
            audio_exts = [".mp3", ".wav", ".flac"]
            text_exts = [".txt", ".pdf", ".doc", ".docx"]

            stats = {
                "channel_name": channel_name,
                "unmatched_files": [
                    f["full_path"] for f in discovery.filesystem_unmatched
                ],
                "fs_total_files": len(discovery.files_on_disk),
                "fs_video_files": count_by_ext(discovery.files_on_disk, video_exts),
                "fs_image_files": count_by_ext(discovery.files_on_disk, image_exts),
                "fs_audio_files": count_by_ext(discovery.files_on_disk, audio_exts),
                "fs_text_files": count_by_ext(discovery.files_on_disk, text_exts),
                "fs_other_files": len(discovery.files_on_disk)
                - count_by_ext(
                    discovery.files_on_disk,
                    video_exts + image_exts + audio_exts + text_exts,
                ),
                "db_pending_files": len(messages_to_download),
                "matches_found": len(discovery.database_matched),
                "updated_to_completed": 0,
                "errors": 0,
                "db_total_media_files": discovery.total_discoverable,
                "db_video_files": 0,
                "db_image_files": 0,
                "db_audio_files": 0,
                "db_text_files": 0,
                "db_other_files": 0,
                "new_messages": 0,
                "new_media_files": 0,
                "new_video_files": 0,
                "new_image_files": 0,
                "new_audio_files": 0,
                "new_text_files": 0,
                "new_other_files": 0,
                "new_files_to_download": len(messages_to_download),
            }
            show_enhanced_enumeration_display(stats, ui_mode=args.progress_mode)

            logger.info(
                f"DEBUG: About to call download_all_media_from_channel for {channel_name}"
            )
            await download_all_media_from_channel(
                client,
                chat_id,
                current_save_directory,
                args.limit,
                channel_name,
                progress_display,
                args.concurrent_downloads,
                incremental=True,
                media_type_filter=args.media_type,
                force_reverse_sync=args.force_reverse_sync,
                skip_reverse_sync=args.skip_reverse_sync,
            )

        # Track overall statistics
        overall_stats["channels_processed"] += 1
        if progress_display and hasattr(progress_display, "stats"):
            downloaded = progress_display.stats.get("downloaded", 0)
            failed = progress_display.stats.get("failed", 0)
            if isinstance(downloaded, (int, float)):
                overall_stats["total_downloaded"] += int(downloaded)
            if isinstance(failed, (int, float)):
                overall_stats["total_errors"] += int(failed)

        logger.info(f"=== Completed Channel: {channel_name} ===\n")

    except Exception as e:
        logger.error(
            f"Error processing channel operations for '{channel_name}': {str(e)}"
        )
        overall_stats["total_errors"] += 1
        raise


async def main() -> int:
    """Main entry point for the application."""
    runner = ApplicationRunner()
    return await runner.run()


if __name__ == "__main__":
    import asyncio as _asyncio

    try:
        exit_code = _asyncio.run(main())
        raise SystemExit(exit_code or 0)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        raise SystemExit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        raise SystemExit(1)
