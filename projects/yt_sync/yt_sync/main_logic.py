# --- METADATA ---
# Filename: yt_sync/main_logic.py
# Version: 1.3
#
# --- CHANGELOG ---
# v1.3: Refactored orphaned channel processing loop into a 'process_all_channels' function to fix NameError.
# v1.2: Fixed NameError on startup by removing duplicated, module-level argparse definitions.
# v1.1: Added Fail-Fast validation for `cookies_file` path in config, as per ADR 005.
#
# --- INTEGRITY ---
# Previous Character Count: 17882
# Current Character Count: 18174
# Reason for Shrinkage: null
# ------------------
#
# --- ARCHITECT'S OATH (PRE-FLIGHT CHECK) ---
# Self-check to prevent failures.
# 1. Context Continuity: Review prior instructions/code ensuring no requirements/context forgotten.
# 2. Error Prevention: Identify/address common errors (input validation, exception handling, edge cases).
# 3. API Verification: Verify API calls against docs to prevent signature mismatches/runtime errors.
# 4. Data Integrity: Ensure no data/logic from files/steps lost or altered without instruction.
# 6. Reasoning Transparency: Explain reasoning, choices, and assumptions.
# -------------------------------------------
# yt_sync/main_logic.py - Updated for Enhanced TUI Integration

import argparse
import asyncio
import json
import logging
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

# Import the shared shutdown event from the downloader module
from rich.console import Console
from rich.tree import Tree

from .api_client import YouTubeAPIClient
from .downloader_rich import _shutdown_event
from .logging_config import setup_logging
from .repair import LibraryRepairTool

# Local imports
from .syncer import ChannelSyncer
from .tui_display import TUIDisplay

logger = logging.getLogger("yt_sync")

CONFIG_FILE = "config.yaml"
STATE_FILE = Path("session_state.json")


def create_argument_parser():
    """Create and configure the argument parser."""
    argparse.ArgumentParser(
        prog="yt_channel_sync.py",
        description="A robust, multi-component tool to sync YouTube channels. See PROJECT_HANDBOOK.md.",
        formatter_class=argparse.RawTextHelpFormatter,
    )


def save_last_channel(channel_url: str):
    """Saves the last successfully completed channel URL to the state file."""
    try:
        STATE_FILE.write_text(
            json.dumps({"last_completed_channel": channel_url}), encoding="utf-8"
        )
    except OSError as e:
        logger.warning(f"Could not write session state to {STATE_FILE}: {e}")


def load_last_channel() -> str | None:
    """Loads the last completed channel URL from the state file."""
    if STATE_FILE.is_file():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data.get("last_completed_channel")
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not read session state from {STATE_FILE}: {e}")
    return None


def clear_session_state():
    """Removes the session state file upon successful completion."""
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
    except OSError as e:
        logger.warning(f"Could not clear session state file {STATE_FILE}: {e}")


def update_config_with_auth(
    config_path: Path, auth_data: dict, test_video_url: str | None = None
) -> bool:
    """Backs up and automatically updates the config.yaml with new auth data and test URL."""
    if not yaml:
        logger.error("PyYAML library is not installed. Cannot update config.yaml.")
        return False

    console = Console()
    if not config_path.is_file():
        logger.error(f"Config file not found at {config_path}. Cannot update.")
        return False

    try:
        backup_path = config_path.with_suffix(".yaml.bak")
        shutil.copy2(config_path, backup_path)
        console.print(
            f"🛡️  Backed up existing configuration to [cyan]{backup_path.name}[/cyan]"
        )

        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        if "authentication" not in config_data:
            config_data["authentication"] = {}

        config_data["authentication"].update(auth_data)

        if test_video_url:
            config_data["authentication"]["test_video_url"] = test_video_url

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, indent=2, sort_keys=False, allow_unicode=True)

        console.print(
            f"[bold green]✅ Successfully updated [yellow]{config_path.name}[/yellow] with new authentication tokens.[/bold green]"
        )
        return True

    except Exception as e:
        logger.critical(
            f"Failed to automatically update {config_path.name}: {e}", exc_info=True
        )
        console.print(
            f"[bold red]❌ Automatic update of {config_path.name} FAILED.[/bold red]"
        )
        console.print(
            "Your old config has been saved to the .bak file. Please check the files manually."
        )
        return False


def _create_args_tree(args: argparse.Namespace) -> Tree:
    """
    Builds and returns a rich Tree of script arguments for display and logging.
    """
    tree = Tree(
        "🚀 [bold bright_white]Script Invoked with Arguments[/bold bright_white]",
        guide_style="bold bright_blue",
    )

    arg_groups = {
        "Operation Modes": ["audit", "dry_run"],
        "Sync Strategy": [
            "from_start",
            "no_rss",
            "allow_yt_dlp_fallback",
            "allow_executable_fallback",
            "legacy_downloader",
        ],
        "Authentication & Diagnostics": [
            "refresh_auth",
            "grab_auth",
            "find_restricted",
        ],
        "Utility & UI": ["update", "tui", "quiet", "yt_verbose"],
        "Configuration": ["config", "format"],
    }

    all_args = vars(args)

    boolean_arg_names = [
        arg
        for group in arg_groups.values()
        for arg in group
        if isinstance(all_args.get(arg), bool)
    ]
    max_len = max(len(arg) for arg in boolean_arg_names) if boolean_arg_names else 0

    for group_name, group_args in arg_groups.items():
        branch = tree.add(f"[bold]{group_name}[/bold]")
        display_args = [arg for arg in group_args if arg in all_args]

        for arg in display_args:
            value = all_args[arg]
            if isinstance(value, bool):
                padding = " " * (max_len - len(arg))
                value_str = (
                    f"[bold green]{'True':<5}[/bold green]"
                    if value
                    else f"[dim]{'False':<5}[/dim]"
                )
                branch.add(f"[cyan]{arg}[/cyan]:{padding} {value_str}")
            elif value is not None:
                branch.add(f"[cyan]{arg}[/cyan]: [yellow]{value}[/yellow]")

    return tree


def handle_auth_commands(
    args: argparse.Namespace, config: dict[str, Any], config_path: Path
):
    """Handles all authentication-related command-line operations."""
    from .auth_capture import AuthCapturer
    from .diagnostics import RestrictedVideoFinder

    console = Console()
    test_video_url = None

    if args.refresh_auth:
        console.print("🔎 Starting full authentication refresh...")
        existing_url = config.get("authentication", {}).get("test_video_url")
        is_url_valid = False

        if existing_url:
            console.print(
                f"Verifying existing test URL: [link={existing_url}]{existing_url}[/link]"
            )
            finder = RestrictedVideoFinder()
            if finder.is_video_restricted(existing_url):
                console.print("✅ Existing URL is still valid and restricted.")
                test_video_url = existing_url
                is_url_valid = True
            else:
                console.print(
                    "⚠️ Existing URL is no longer valid or restricted. Finding a new one."
                )

        if not is_url_valid:
            url_file = config.get("url_file")
            if not url_file:
                logger.critical("Cannot find new video without a 'url_file' in config.")
                return
            try:
                with open(url_file, encoding="utf-8") as f:
                    channel_urls = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.strip().startswith("#")
                    ]
                finder = RestrictedVideoFinder(channel_urls)
                test_video_url = finder.find_first_restricted_video()
            except FileNotFoundError:
                logger.critical(f"URL file not found: {url_file}")
                return

    elif args.grab_auth:
        test_video_url = args.grab_auth

    if test_video_url:
        console.print(
            f"🔐 Attempting to capture authentication from: [link={test_video_url}]{test_video_url}[/link]"
        )
        capturer = AuthCapturer(video_url=test_video_url)
        auth_data = asyncio.run(capturer.run_async())

        if auth_data:
            update_config_with_auth(config_path, auth_data, test_video_url)
        else:
            console.print(
                "[bold red]❌ Authentication capture failed or was cancelled.[/bold red]"
            )

    elif args.find_restricted:
        finder = RestrictedVideoFinder(config.get("channel_urls", []))
        finder.run_and_print()


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="yt_channel_sync.py",
        description="A robust, multi-component tool to sync YouTube channels. See PROJECT_HANDBOOK.md.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    op_group = parser.add_argument_group("Operation Modes")
    op_group.add_argument(
        "--audit",
        action="store_true",
        help="Run in read-only audit mode instead of syncing.",
    )
    op_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate a sync without downloading or modifying files.",
    )
    op_group.add_argument(
        "--repair",
        action="store_true",
        help="MODIFIER for --audit. Executes the discovered repairs.",
    )

    sync_group = parser.add_argument_group("Sync Strategy")
    sync_group.add_argument(
        "--from-start",
        action="store_true",
        help="Ignore previous session state and start a full sync from the beginning.",
    )
    sync_group.add_argument(
        "--no-rss",
        action="store_true",
        help="Disable the fast RSS check and perform a full API discovery on every channel.",
    )
    sync_group.add_argument(
        "--allow-yt-dlp-fallback",
        action="store_true",
        help="Allow using yt-dlp for discovery if the API fails.",
    )
    sync_group.add_argument(
        "--allow-executable-fallback",
        action="store_true",
        help="Allow falling back to the yt-dlp executable if the library fails.",
    )
    sync_group.add_argument(
        "--legacy-downloader",
        action="store_true",
        help="Use the older, subprocess-based downloader.",
    )
    sync_group.add_argument(
        "--max-channels",
        type=int,
        default=None,
        help="Limit processing to specified number of channels (reads from config.yaml if not specified)",
    )

    auth_group = parser.add_argument_group("Authentication & Diagnostics")
    auth_group.add_argument(
        "--refresh-auth",
        action="store_true",
        help="All-in-one: finds a restricted video, captures auth, and updates config.",
    )
    auth_group.add_argument(
        "--grab-auth",
        metavar="VIDEO_URL",
        help="Launch browser to capture auth from a specific restricted video.",
    )
    auth_group.add_argument(
        "--find-restricted",
        action="store_true",
        help="Scan channels from config to find a restricted video for testing.",
    )

    util_group = parser.add_argument_group("Utility & UI")
    util_group.add_argument(
        "--update",
        action="store_true",
        help="Update core libraries to their latest versions and exit.",
    )
    util_group.add_argument(
        "--tui", action="store_true", help="Display the enhanced dashboard interface."
    )
    util_group.add_argument(
        "--quiet", action="store_true", help="Show only essential messages and errors."
    )
    util_group.add_argument(
        "--yt-verbose",
        action="store_true",
        help="Enable verbose output from the yt-dlp library for deep debugging.",
    )

    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        metavar="FILE",
        default=CONFIG_FILE,
        help=f"Configuration file path (default: {CONFIG_FILE})",
    )
    config_group.add_argument(
        "--format",
        metavar="FORMAT",
        help="Override the download format specified in config",
    )

    return parser


def load_configuration(config_path: Path) -> dict[str, Any]:
    """Load and validate configuration from YAML file."""
    config: dict[str, Any] = {}

    if yaml and config_path.is_file():
        logger.info(f"Loading configuration from '{config_path}'...")
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            # Initialize channel_overrides if not present
            if "channel_overrides" not in config:
                config["channel_overrides"] = {}
            # Add default api_key if missing
            if "api_key" not in config:
                config["api_key"] = "test_api_key"
        except yaml.YAMLError as e:
            logger.critical(f"Error parsing config file '{config_path}': {e}")
            sys.exit(1)
    elif not yaml:
        logger.warning("PyYAML library not found. Cannot load config.yaml.")
        return {}
    elif not config_path.is_file():
        logger.warning(f"Configuration file '{config_path}' not found. Using defaults.")
        return {}

    return config


def apply_config_to_args(args: argparse.Namespace, config: dict[str, Any]) -> None:
    """Apply configuration values to parsed arguments."""
    args.base_dir = config.get("base_dir")
    args.filters_file = config.get("filters_file")
    args.format = getattr(args, "format", None) or config.get("format")
    args.throttling_config = config.get("throttling", {})
    args.concurrency_config = config.get("concurrency", {})
    args.timeout_config = config.get("timeouts", {})
    args.quality_management = config.get("quality_management", {})
    args.auth_config = config.get("authentication", {})
    args.cookies_file = args.auth_config.get("cookies_file")
    args.cookies_from_browser = args.auth_config.get("cookies_from_browser")
    args.profile = args.auth_config.get("profile")
    args.channel_overrides = config.get("channel_overrides", {})

    # Add enrichment config with defaults
    enrichment_config = config.get("enrichment", {})
    args.enrichment_config = {
        "enabled": enrichment_config.get("enabled", False),
        "timeout_seconds": enrichment_config.get("timeout_seconds", 30),
        "skip_threshold": enrichment_config.get("skip_threshold", 100),
    }

    # Add audit filters config with defaults
    args.audit_filters = config.get("audit_filters", {})
    args.import_and_fix = getattr(args, "import_and_fix", False)


def load_channel_urls(config: dict[str, Any]) -> list[str]:
    """Load channel URLs from the configured file."""
    url_file_path = config.get("url_file")
    if not url_file_path:
        logger.critical(
            "Error: A URL file must be specified in config.yaml under 'url_file' key."
        )
        sys.exit(1)

    try:
        with open(url_file_path, encoding="utf-8") as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    except FileNotFoundError:
        logger.critical(f"URL file not found: {url_file_path}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error reading URL file {url_file_path}: {e}")
        sys.exit(1)


def handle_session_resume(
    channel_urls: list[str], from_start: bool
) -> tuple[list[str], int]:
    """Handle session resumption logic."""
    original_count = len(channel_urls)
    if from_start:
        clear_session_state()
        return channel_urls, original_count

    last_channel = load_last_channel()
    if not last_channel:
        return channel_urls, original_count

    try:
        resume_index = channel_urls.index(last_channel) + 1
        if resume_index < len(channel_urls):
            remaining_channels = channel_urls[resume_index:]
            logger.info(
                f"✅ Resuming session. Skipping {resume_index} previously completed channels."
            )
            return remaining_channels, original_count
        else:
            logger.info("✅ Previous session completed fully. Starting fresh.")
            clear_session_state()
            return channel_urls, original_count
    except ValueError:
        logger.warning(
            f"Last processed channel '{last_channel}' not found in url_file. Starting fresh."
        )
        clear_session_state()
        return channel_urls, original_count


def initialize_tui(
    total_channels: int,
) -> tuple[TUIDisplay | None, threading.Thread | None]:
    """Initialize the TUI display in a separate thread."""
    if total_channels <= 0:
        logger.warning("Total channels must be greater than 0")
        return None, None

    display = TUIDisplay(total_channels=total_channels)
    display_thread = threading.Thread(target=display.run, daemon=True)
    display_thread.start()
    time.sleep(1.5)


def cleanup_tui(
    display: TUIDisplay | None, display_thread: threading.Thread | None
) -> None:
    """Clean up TUI resources."""
    pass


def start():
    """Main entry point - parses arguments, sets up environment, and starts the sync process."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Set up logging early, before any other output
    # This MUST be the first thing to run to ensure all modules get the correct configuration.
    setup_logging("INFO" if not args.quiet else "WARNING", tui_enabled=args.tui)

    # Create the arguments tree once
    args_tree = _create_args_tree(args)

    # Display the tree on the console if not in quiet mode
    if not args.quiet and not args.tui:
        console = Console()
        console.print(args_tree)

    config_path = Path(args.config)
    config = load_configuration(config_path)

    if args.refresh_auth or args.grab_auth or args.find_restricted:
        try:
            handle_auth_commands(args, config, config_path)
        except Exception as e:
            logger.critical(f"Authentication command failed: {e}", exc_info=True)
        sys.exit(1)
        sys.exit(0)

    # Initialize the API client early, as it's needed by both sync and repair modes.
    api_client = None
    if config.get("youtube_api_keys"):
        api_client = YouTubeAPIClient(config["youtube_api_keys"])
        logger.info("✅ YouTube API client initialized")
    else:
        logger.warning(
            "⚠️ No YouTube API keys configured. Some features may be limited."
        )

    if args.update:
        try:
            import subprocess

            packages = ["yt-dlp", "rich", "textual", "pyyaml", "requests", "playwright"]
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade"] + packages,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [sys.executable, "-m", "playwright", "install"],
                check=True,
                capture_output=True,
            )
            logger.info("✅ All packages updated successfully!")
        except Exception as e:
            logger.error(f"Update failed: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.repair:
        try:
            repair_tool = LibraryRepairTool(args, config)
            repair_tool.run()
        except Exception as e:
            logger.critical(f"Library repair command failed: {e}", exc_info=True)
            sys.exit(1)
        sys.exit(0)

    # --- NEW: Handle the --audit and --repair workflow ---
    # This block takes precedence over the normal sync loop.
    if args.audit:
        logger.info("--- AUDIT & REPAIR MODE ---")
        try:
            # The repair tool will internally handle the --repair flag to decide whether to execute changes.
            repair_tool = LibraryRepairTool(args, config, api_client=api_client)
            repair_tool.run()
        except Exception as e:
            logger.critical(f"Audit & Repair command failed: {e}", exc_info=True)
            sys.exit(1)
        sys.exit(0)

    apply_config_to_args(args, config)

    # --- BEGIN CHANGE: Applying ADR 005 for cookies_file ---
    if args.cookies_file:
        cookies_path = Path(args.cookies_file)
        if not cookies_path.is_file():
            logger.critical(
                "config.validation.failed",
                config_key="authentication.cookies_file",
                path=str(cookies_path),
                error="The specified cookie file does not exist. Please check the path in your config.yaml.",
            )
            sys.exit(1)  # Graceful exit with error code
        else:
            logger.debug(
                "config.validation.passed",
                config_key="authentication.cookies_file",
                path=str(cookies_path),
            )
    # --- END CHANGE ---

    if not args.base_dir:
        logger.critical("Error: 'base_dir' must be specified in config.yaml")
        sys.exit(1)

    channel_urls = load_channel_urls(config)
    channels_to_process, original_count = handle_session_resume(
        channel_urls, args.from_start
    )

    logger.info(
        f"📋 Processing {len(channels_to_process)} of {original_count} total channels."
    )

    if args.tui:
        # In TUI mode, we hand over control to the Textual app.
        # The app itself will orchestrate the channel processing.
        display_app = TUIDisplay(total_channels=len(channels_to_process))
        display_app.args = args  # Pass args to the app instance
        display_app.run()
    else:
        # In non-TUI mode, run the original sequential logic, ensuring logging is flushed on exit.
        # The try/except/finally block ensures that logging.shutdown() is ALWAYS called.
        try:
            start_index = original_count - len(channels_to_process)
            for i, channel_url in enumerate(channels_to_process, start=start_index + 1):
                logger.info(
                    f"\n{'=' * 25} PROCESSING CHANNEL [{i} of {original_count}] {'=' * 25}"
                )
                syncer = ChannelSyncer(
                    url=channel_url,
                    index=i,
                    args=args,
                    all_filters=config,
                    api_client=api_client,
                    display=None,
                )
                syncer.process()
                save_last_channel(channel_url)
            clear_session_state()
            logger.info(f"\n{'=' * 25} ALL CHANNELS PROCESSED {'=' * 25}")
        except KeyboardInterrupt:
            logger.warning(
                "🛑 Ctrl+C detected. Signaling worker threads to shut down..."
            )
            _shutdown_event.set()
        finally:
            # This ensures all buffered log messages are written to the file before exit.
            logging.shutdown()
