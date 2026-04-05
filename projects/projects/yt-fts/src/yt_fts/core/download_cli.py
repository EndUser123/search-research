"""
Download CLI commands for yt-fts.

This module contains all download-related commands extracted from cli.py:
- download: Download subtitles from a YouTube channel
- update: Update channel content with automatic embeddings synchronization
- batch-download: Download multiple YouTube channels with advanced features
- embeddings: Generate embeddings for a channel
- embeddings-status: Check embeddings status for all channels
- clean-channels: Clean and optimize YouTube channel lists
- convert-channels: Convert channels.txt format to ensure proper YouTube URLs
"""

import asyncio
import os
import sys
from datetime import datetime as dt
from pathlib import Path

import click

# Load environment variables from .env file if it exists
from yt_fts.utils.config import find_and_load_env, get_db_path

# Skip .env loading for --help to avoid noise
if "--help" not in sys.argv and "-h" not in sys.argv:
    env_path = find_and_load_env()
    if env_path:
        print(f"Loaded environment variables from {env_path}")
    else:
        print("WARNING:  .env file not found in expected locations")

from yt_fts.config import DAILY_QUOTA_LIMIT
from yt_fts.download.batch_downloader import BatchDownloader
from yt_fts.download.batch_helpers import (
    determine_rich_mode,
    find_input_file,
    initialize_quota_strategy,
    load_channels_from_database,
    normalize_output_format,
)
from yt_fts.download.download_handler import DownloadHandler
from yt_fts.download.parallel_processor import ParallelBatchProcessor
from yt_fts.ui.dashboard import MIN_TEXTUAL_VERSION
from yt_fts.utils import get_model_config
from yt_fts.utils.rich_console import get_console

from .batch_loaders import display_batch_startup_summary
from .database import (
    check_if_channel_exists,
    get_channel_id_from_input,
)


def _get_console():
    """Get the console instance for output."""
    return get_console()


console = _get_console()


def _handle_command_result(result: int | None = None) -> None:
    """
    Handle command execution results consistently without sys.exit().

    Args:
        result: Exit code from command execution (0=success, 1=error, 130=interrupt)
                If None, no action is taken (command handles its own flow control)
    """
    if result is not None:
        # Let Click handle the exit code naturally
        # This allows proper cleanup and maintains CLI behavior
        if result != 0:
            # For non-zero exit codes, we'll raise a SystemExit with the code
            # but this is more controlled than direct sys.exit() calls
            raise SystemExit(result)
        # For success (0), we simply return and let Click complete normally


def validate_display_options(
    simple: bool = False,
    fzf: bool = False,
    rich: bool = False,
    richo: bool = False,
    rich_1: bool = False,
    json: bool = False,
) -> None:
    """
    Validate display options for conflicting combinations.

    Args:
        simple: Simple line-by-line output
        fzf: fzf-style output
        rich: New Rich UI with fixed footer layout
        richo: Old Rich UI with progress bars
        rich_1: Alias for rich mode
        json: JSON output format

    Raises:
        click.BadOptionException: When conflicting display options are provided.
    """
    # Count how many display modes are active
    display_modes = []

    if simple:
        display_modes.append("--simple")
    if fzf:
        display_modes.append("--fzf")
    if rich or rich_1:
        display_modes.append("--rich/--rich-1")
    if richo:
        display_modes.append("--richo")

    # Check for multiple display modes (json is mutually exclusive with all)
    if json and display_modes:
        modes = " and ".join(display_modes)
        msg = (
            f"Cannot use --json with {modes}. JSON output is mutually exclusive "
            f"with other display formats."
        )
        raise click.BadOptionException(
            msg
        )

    # Check for multiple non-JSON display modes
    if len(display_modes) > 1:
        modes = " and ".join(display_modes)
        msg = (
            f"Cannot use {modes} together. These display formats are mutually exclusive. "
            f"Choose one: --simple, --fzf, --rich/--rich-1, or --richo"
        )
        raise click.BadOptionException(
            msg
        )


# ============================================================================
# Download Commands
# ============================================================================

@click.command(
    name="download",
    help="""
    Download subtitles from a YouTube channel with enhanced channel resolution.

    Supports multiple input formats:
    @handle (e.g., @TwoMinutePapers)
    Full URL (e.g., https://www.youtube.com/@TwoMinutePapers)
    Channel ID (e.g., UC7YXt_4HIxqvXum5A-PJq3g)
    Channel name (when unique)

    Enhanced features:
    Automatic channel resolution with fallbacks
    Browser cookie support for bypassing rate limits
    Intelligent error handling and recovery
    Progress tracking with detailed status updates
    Duplicate detection and prevention
    """,
)
@click.argument("url", required=True)
@click.option(
    "-p",
    "--playlist",
    is_flag=True,
    required=False,
    help="Download all videos from a playlist",
)
@click.option(
    "-l", "--language", default="en", help="Language of the subtitles to download"
)
@click.option(
    "-j",
    "--jobs",
    type=int,
    default=2,
    help="Number of parallel download jobs (default: 2, recommended: 1-3 to avoid rate limits)",
)
@click.option(
    "--cookies-from-browser",
    default="firefox",
    help="Browser to extract cookies from (default: firefox). Use --no-cookies to disable.",
)
@click.option(
    "--no-cookies",
    is_flag=True,
    default=False,
    help="Disable browser cookies extraction",
)
@click.option(
    "--no-fail-fast",
    "--degrade",
    "no_fail_fast",
    is_flag=True,
    default=False,
    help=(
        "Opt in to degraded mode (alias: --degrade). When set the CLI will NOT fail-fast; "
        "recoverable errors will be reported but processing will continue instead of exiting immediately. "
        "Fail-fast is the default behavior unless this flag is provided."
    ),
)
@click.option(
    "--transcribe-audio-only/--no-transcribe-audio-only",
    default=True,
    help=(
        "Transcribe audio using Whisper when subtitles are not available. "
        "Requires faster-whisper to be installed. (default: enabled)"
    ),
)
@click.option(
    "--whisper-model",
    type=click.Choice(["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]),
    default="base",
    help="Whisper model size for audio transcription (default: base)",
)
@click.option(
    "--keep-audio",
    is_flag=True,
    default=False,
    help="Preserve downloaded audio files after transcription (for debugging/iteration)",
)
@click.option(
    "--simple",
    is_flag=True,
    default=False,
    help="Simple output mode with minimal progress display",
)
@click.option(
    "--fzf",
    is_flag=True,
    default=False,
    help="FZF-compatible output mode",
)
def download(
    url: str,
    playlist: bool,
    language: str,
    jobs: int,
    cookies_from_browser: str | None,
    no_fail_fast: bool,
    transcribe_audio_only: bool,
    whisper_model: str,
    no_cookies: bool,
    keep_audio: bool,
    simple: bool,
    fzf: bool,
) -> None:
    """
    ENHANCED: Download command with UnifiedChannelProcessor integration.

    Supports @handle, URL, channel_id, and name inputs with improved error handling.
    """
    # Handle cookies: --no-cookies overrides --cookies-from-browser
    if no_cookies:
        cookies_from_browser = None

    # Use asyncio to handle async operations in UnifiedChannelProcessor
    exit_code = asyncio.run(
        _download_async(
            url, playlist, language, jobs, cookies_from_browser, no_fail_fast,
            transcribe_audio_only, whisper_model, no_cookies, keep_audio
        )
    )
    _handle_command_result(exit_code)


async def _download_async(
    url: str,
    playlist: bool,
    language: str,
    jobs: int,
    cookies_from_browser: str | None,
    no_fail_fast: bool,
    transcribe_audio_only: bool,
    whisper_model: str,
    no_cookies: bool,
    keep_audio: bool,
) -> int:
    """
    Async implementation of download functionality.
    """
    fail_fast = not bool(no_fail_fast)
    download_handler = DownloadHandler(
        number_of_jobs=jobs,
        language=language,
        cookies_from_browser=cookies_from_browser,
        fail_fast=fail_fast,
        transcribe_audio_only=transcribe_audio_only,
        whisper_model=whisper_model,
        keep_audio=keep_audio,
    )

    try:
        if playlist:
            # Playlist handling (original logic preserved)
            if "playlist?" not in url:
                console.print(
                    f"\n[bold red]Error:[/bold red] Invalid playlist url {url}\n"
                )
                console.print(
                    "YouTube playlists have this format: "
                    '"https://www.youtube.com/playlist?list=<playlist_id>"\n'
                )
                console.print("[yellow]💡 Suggestions:[/yellow]")
                console.print("   Check the playlist URL format")
                console.print("   Ensure the playlist ID is correct")
                return 1  # Return error code instead of sys.exit(1)

            download_handler.download_playlist(url, language, jobs)
            return 0  # Return success code instead of sys.exit(0)

        # ENHANCED: Channel download with UnifiedChannelProcessor
        console.print(f"[blue]🔍 Resolving channel:[/blue] {url}")

        # First validate and resolve the channel using our enhanced processor
        resolved_url = download_handler.validate_channel_url(url)
        if not resolved_url:
            # URL validation failed - error already printed by validate_channel_url
            console.print("[yellow]💡 Try:[/yellow]")
            console.print("   @channelname (handle)")
            console.print("   https://youtube.com/@channelname")
            console.print("   https://youtube.com/channel/CHANNEL_ID")
            return 1

        # Get channel ID using enhanced resolution (async)
        channel_id = await download_handler.get_channel_id(url)
        if not channel_id:
            # Channel resolution failed - error already printed
            return 1

        # Check if channel already exists
        if check_if_channel_exists(channel_id):
            channel_name = await download_handler.get_channel_name(channel_id)
            console.print(
                f"[yellow]WARNING:  Channel already exists:[/yellow] {channel_name or channel_id}"
            )
            console.print(
                "[yellow]💡 Use 'yt-fts update' command instead to update existing channels[/yellow]"
            )
            return 1

        # Continue with download
        console.print(f"[green]Starting download for channel:[/green] {channel_id}")
        download_handler.download_channel(resolved_url)
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]WARNING:  Download interrupted by user[/yellow]")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e!s}")
        console.print("[yellow]💡 Suggestions:[/yellow]")
        console.print("   Check your internet connection")
        console.print("   Verify the channel is public and accessible")
        console.print("   Try again with a different channel")
        console.print("   Run 'yt-fts diagnose' for connection testing")
        return 1


@click.command(
    name="update",
    help="""
    Update channel content with automatic embeddings synchronization.

    Update features:
    Download new videos and subtitles since last update
    Automatic embeddings generation for new content
    Support for all channel input formats (@handle, URL, name, ID)
    Progress tracking and detailed status reporting
    Intelligent retry and error recovery

    Auto-embeddings:
    Automatically generates embeddings for updated content
    Maintains search index consistency
    Supports both local and API-based embeddings
    Progress monitoring with status updates

    Use --channel to update specific channels, or omit to update all channels in library.
    """,
)
@click.option(
    "-c", "--channel", default=None, help="The name or id of the channel to update."
)
@click.option(
    "-l", "--language", default="en", help="Language of the subtitles to download"
)
@click.option(
    "-j",
    "jobs",
    type=int,
    default=8,
    help="Number of parallel download jobs (default: 2, recommended: 1-3 to avoid rate limits)",
)
@click.option(
    "--cookies-from-browser",
    default="firefox",
    help="Browser to extract cookies from (default: firefox). Use --no-cookies to disable.",
)
@click.option(
    "--no-cookies",
    is_flag=True,
    default=False,
    help="Disable browser cookies extraction",
)
@click.option(
    "--transcribe-audio-only/--no-transcribe-audio-only",
    default=True,
    help="Transcribe audio using Whisper when subtitles are not available (default: enabled)",
)
@click.option(
    "--whisper-model",
    type=click.Choice(["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]),
    default="base",
    help="Whisper model size for audio transcription (default: base)",
)
def update(
    channel: str | None, language: str, jobs: int, cookies_from_browser: str | None,
    transcribe_audio_only: bool, whisper_model: str, no_cookies: bool
) -> None:
    """
    ENHANCED: Update command with UnifiedChannelProcessor integration.

    Supports @handle, URL, channel_id, and name inputs with improved error handling.
    """
    # Handle cookies: --no-cookies overrides --cookies-from-browser
    if no_cookies:
        cookies_from_browser = None

    # Use asyncio to handle async operations in UnifiedChannelProcessor
    exit_code = asyncio.run(
        _update_async(channel, language, jobs, cookies_from_browser, transcribe_audio_only, whisper_model, no_cookies)
    )
    _handle_command_result(exit_code)


async def _update_async(
    channel: str | None, language: str, jobs: int, cookies_from_browser: str | None,
    transcribe_audio_only: bool, whisper_model: str, no_cookies: bool
) -> int:
    """
    Async implementation of update functionality.
    """
    update_handler = DownloadHandler(
        language=language,
        number_of_jobs=jobs,
        cookies_from_browser=cookies_from_browser,
        transcribe_audio_only=transcribe_audio_only,
        whisper_model=whisper_model,
    )

    try:
        if channel is not None:
            # ENHANCED: Resolve channel using UnifiedChannelProcessor
            console.print(f"[blue]🔍 Resolving channel for update:[/blue] {channel}")

            # Get channel ID using enhanced resolution
            channel_id = await update_handler.get_channel_id(channel)
            if not channel_id:
                # Channel resolution failed - error already printed
                console.print("[yellow]💡 Suggestions:[/yellow]")
                console.print("   Check the channel exists and is public")
                console.print("   Try the channel's @handle or full URL")
                console.print("   Verify your internet connection")
                return 1

            # Check if channel exists in database
            if not check_if_channel_exists(channel_id):
                channel_name = await update_handler.get_channel_name(channel_id)
                console.print(
                    f"[red]❌ Channel not found:[/red] {channel_name or channel}"
                )
                console.print("[yellow]💡 Suggestions:[/yellow]")
                console.print("   Download the channel first using 'yt-fts download'")
                console.print("   Check if the channel name is correct")
                return 1

            # Update the channel
            console.print(f"[green]Updating channel:[/green] {channel_id}")
            update_handler.update_channel(channel)

            # Auto-update embeddings for the updated channel (NEW!)
            from yt_fts.llm.auto_embeddings import AutoEmbeddingsManager

            auto_manager = AutoEmbeddingsManager()

            console.print(
                "\n🔄 [blue]Checking embeddings status for updated channel...[/blue]"
            )
            if auto_manager.ensure_embeddings_for_channel(channel_id, force_rebuild=True):
                console.print("[green]Embeddings automatically updated![/green]")
            else:
                console.print(
                    "WARNING:  [yellow]Embeddings update failed. Run 'embeddings' command manually if needed.[/yellow]"
                )

            return 0

        # Update all channels (existing logic preserved)
        console.print("[blue]🔄 Updating all channels...[/blue]")
        update_handler.update_all_channels()

        # Auto-update embeddings for all channels that need it (NEW!)
        from yt_fts.llm.auto_embeddings import AutoEmbeddingsManager

        from .db_utils import get_channels

        auto_manager = AutoEmbeddingsManager()
        console.print(
            "\n🔄 [blue]Checking embeddings status for all channels...[/blue]"
        )

        all_channels = get_channels()
        for _, channel_id, channel_name, _ in all_channels:
            if auto_manager.ensure_embeddings_for_channel(channel_id, force_rebuild=True):
                console.print(f"[green]{channel_name}: Embeddings ready.[/green]")
            else:
                console.print(
                    f"WARNING:  [yellow]{channel_name}: Embeddings check failed.[/yellow]"
                )

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]WARNING:  Update interrupted by user[/yellow]")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e!s}")
        console.print("[yellow]💡 Suggestions:[/yellow]")
        console.print("   Check your internet connection")
        console.print("   Verify the channel is public and accessible")
        console.print("   Try again with a different channel")
        console.print("   Run 'yt-fts diagnose' for connection testing")
        return 1


@click.command(
    name="embeddings-status",
    help="""
            Check embeddings status for all channels and show what needs to be updated.
            Shows detailed information about which channels have embeddings,
            which need updates, and estimated generation times.
        """,
)
def embeddings_status() -> None:
    from yt_fts.llm.auto_embeddings import AutoEmbeddingsManager

    auto_manager = AutoEmbeddingsManager()

    # List all channels with their status
    auto_manager.list_channels_status()

    console.print("\n[bold]💡 Tips:[/bold]")
    console.print(
        "- Use 'vsearch' - embeddings will be generated automatically if needed"
    )
    console.print(
        "- Use 'update' - embeddings will be updated for new content automatically"
    )
    console.print(
        "- Use 'embeddings --channel <name>' - force regenerate embeddings for a channel"
    )


@click.command(
    name="embeddings",
    help="""
    Generate embeddings for a channel using local models or Google's Gemini embeddings API.
    Local embeddings are recommended for better performance and no API costs.
    Requires sentence-transformers for local models or GEMINI_API_KEY for Gemini API.
    """,
)
@click.option(
    "-c",
    "--channel",
    default=None,
    help="The name or id of the channel to generate embeddings for",
)
@click.option(
    "--local",
    is_flag=True,
    help="Use local sentence-transformers model instead of Gemini API (recommended)",
)
@click.option(
    "--model",
    default=None,
    help="Specific model to use. For local: 'sentence-transformers/all-MiniLM-L6-v2' (default), for Gemini: 'text-embedding-004'",
)
@click.option(
    "--api-key",
    default=None,
    help="Gemini API key (only needed for Gemini models). If not provided, the script will attempt to read it from the GEMINI_API_KEY environment variable.",
)
@click.option(
    "-i",
    "--interval",
    default=30,
    type=int,
    help="Interval in seconds to split the transcripts into chunks. Default 30s.",
)
def embeddings(
    channel: str | None,
    local: bool,
    model: str | None,
    api_key: str | None,
    interval: int = 30,
) -> None:
    from yt_fts.llm.simple_embeddings import SimpleEmbeddingsHandler

    channel_id = get_channel_id_from_input(channel)

    # Check if embeddings already exist (using our simple storage)
    embeddings_handler = SimpleEmbeddingsHandler(interval=interval)
    existing_embeddings = embeddings_handler.load_embeddings(channel_id)
    if existing_embeddings:
        console.print(
            f"\n\t[bold][yellow]Warning:[/yellow][/bold] Embeddings already exist for this channel ({len(existing_embeddings['embeddings'])} segments).\n"
        )
        response = input("Do you want to regenerate them? (y/N): ")
        if response.lower() != "y":
            console.print("Embeddings generation cancelled.")
            return  # Success - let Click handle naturally

    # Determine model configuration
    if local or (
        model and ("local" in model.lower() or "sentence-transformers" in model.lower())
    ):
        # Use local model
        model_config = {
            "name": "LOCAL",
            "embedding_model": model or "sentence-transformers/all-MiniLM-L6-v2",
            "chat_model": "local",
            "api_key": "",
            "base_url": "",
        }
        console.print(
            f"[blue]🔧 Using local embeddings model:[/blue] {model_config['embedding_model']}"
        )
    else:
        # Use API model (Gemini by default)
        try:
            model_config = get_model_config(api_key, model)
        except ValueError:
            console.print(
                """
        [bold][red]Error:[/red][/bold] GEMINI_API_KEY environment variable not set. Run:

                export GEMINI_API_KEY=<your_gemini_key> to set the key

        Get your free Gemini API key from: https://makersuite.google.com/app/apikey

        💡 [yellow]Tip:[/yellow] Use --local for faster, free local embeddings instead!
                      """
            )
            msg = "API key configuration error"
            raise click.ClickException(msg)

    embeddings_handler.add_embeddings_to_storage(channel_id, model_config)
    console.print("[green]Embeddings generated successfully![/green]")
    console.print(
        f"[blue]💾[/blue] Stored for channel: {model_config['name']} ({model_config['embedding_model']})"
    )
    # Success - let Click handle naturally


@click.command(
    name="batch-download",
    help="""
    Download multiple YouTube channels with advanced features and intelligent processing.

    Batch processing features:
    Parallel downloading with configurable job count per channel
    Intelligent rate limiting with delays between channels
    Automatic channel resolution for all input formats
    Browser cookie integration for bypassing rate limits
    Comprehensive error handling with retry logic
    Progress tracking with detailed status displays

    Channel input support:
    Files with channel lists (one per line)
    Mixed formats (@handles, URLs, names)
    Direct channel input as argument
    Automatic validation and cleaning

    Advanced options:
    Continue on error mode for resilient processing
    TUI dashboard integration for interactive monitoring
    Export reports for batch operation analysis
    Configurable retry attempts and delays
    Skip initial wait for existing channels

    Examples:
    yt-fts batch-download channels.txt --jobs 2 --cookies-from-browser firefox
    yt-fts batch-download @channel1,@channel2 --continue-on-error
    yt-fts batch-download channels.txt --limit 5 --rich  # Limit to first 5 channels
    yt-fts batch-download channels.txt --tui  # Interactive dashboard
    """,
)
@click.argument("input_file", required=False)

@click.option(
    "-i",
    "--import",
    "import_file",
    type=click.Path(exists=True),
    default=None,
    help="Import channels from file to database before processing",
)
@click.option(
    "--import-only",
    is_flag=True,
    default=False,
    help="Only import channels, don't download any content",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be imported without making changes",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(),
    default=None,
    help="Export valid channels to file after import",
)

@click.option(
    "--jobs",
    "-j",
    default=2,
    type=int,
    help="Number of parallel download jobs per channel (default: 2, recommended: 1-3)",
)
@click.option("--language", "-l", default="en", help="Subtitle language (default: en)")
@click.option(
    "--cookies-from-browser",
    default="firefox",
    type=click.Choice(["firefox", "chrome", "edge", "safari"]),
    help="Browser to extract cookies from (default: firefox). Use --no-cookies to disable.",
)
@click.option(
    "--no-cookies",
    is_flag=True,
    default=False,
    help="Disable browser cookies extraction",
)
@click.option(
    "--delay",
    "-d",
    default=60.0,
    type=float,
    help="Delay between channels in seconds (default: 60.0)",
)
@click.option(
    "--max-retries",
    default=3,
    type=int,
    help="Maximum retry attempts per channel (default: 3)",
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Continue downloading other channels even if some fail",
)
@click.option(
    "--no-fail-fast",
    "--degrade",
    "no_fail_fast",
    is_flag=True,
    default=False,
    help=(
        "Opt in to degraded mode (alias: --degrade). When set the CLI will NOT fail-fast; "
        "recoverable errors will be reported but processing will continue instead of exiting immediately. "
        "Fail-fast is the default behavior unless this flag is provided."
    ),
)
@click.option(
    "--no-skip-initial-wait",
    is_flag=True,
    default=False,
    help=(
        "Opt out of skipping the startup countdown for the first channel. "
        "By default we skip the initial wait when the first channel already exists in the DB."
    ),
)
@click.option(
    "--tui",
    is_flag=True,
    default=False,
    help=(
        "Opt in to launch the interactive dashboard (Textual TUI). "
        f"Requires Textual >= {MIN_TEXTUAL_VERSION}"
    ),
)
@click.option("--export-report", help="Export detailed report to JSON file")
@click.option(
    "--limit",
    type=int,
    help="Limit processing to first N channels from input file",
)
@click.option(
    "--richo",
    is_flag=True,
    default=False,
    help="Enable old Rich UI with progress bars (legacy mode)",
)
@click.option(
    "--rich",
    is_flag=True,
    default=False,
    help="Enable new Rich UI with fixed footer layout (Windows 11 optimized)",
)
@click.option(
    "--rich-1",
    "rich_1",
    is_flag=True,
    default=False,
    help="Enable Rich Layout with fixed footer (uses _download_with_rich_layout)",
)
@click.option(
    "--time-per-video",
    type=float,
    default=None,
    help="Timeout per yt-dlp call in seconds (e.g., 10 for 10 seconds)",
)
@click.option(
    "--time-per-channel",
    type=float,
    default=None,
    help="Maximum time to spend downloading each channel in seconds (e.g., 120 for 2 minutes)",
)
@click.option(
    "--time-per-batch",
    type=float,
    default=None,
    help="Maximum time for entire batch operation in seconds (e.g., 300 for 5 minutes)",
)
@click.option(

    "--videos-download-per-channel",
    type=int,
    default=None,
    help="Videos to download per channel",
)
@click.option(
    "--channels-download-per-batch",
    type=int,
    default=None,
    help="Target number of channels to download",
)
@click.option(
    "--channels-scan-per-batch",
    "limit",
    type=int,
    default=None,
    help="Limit processing to first N channels from input file",
)
@click.option(
    "--display-plugin",
    "-dp",
    "display_plugin",
    type=str,
    default=None,
    help="Display plugin: 1-6 (Gemini), or name",
)
@click.option(
    "--parallel-workers",
    "-w",
    "parallel_workers",
    type=int,
    default=1,
    help=(
        "Number of parallel worker threads for processing channels. "
        "Uses ThreadPoolExecutor for better SQLite concurrency. "
        "Default: 1 (sequential). Recommended: 4-8 for metadata-only mode."
    ),
)
@click.option(
    "--rich-progress/--no-rich-progress",
    "rich_progress",
    is_flag=True,
    default=False,
    help="Use Rich progress bars/table for parallel processing (requires: pip install rich)",
)
@click.option(
    "--rich-display",
    "rich_display",
    type=click.Choice(["progress", "table"], case_sensitive=False),
    default="progress",
    help="Rich display mode: 'progress' for stacked bars, 'table' for live data view (default: progress)",
)
@click.option(
    "--auto-backfill",
    is_flag=True,
    default=False,
    help="Automatically backfill metadata after each channel download",
)
@click.option(
    "--freshness-hours",
    type=int,
    default=6,
    help="Skip channels checked within N hours (default: 6, 0 to disable)",
)
@click.option(
    "--use-cache/--no-cache",
    "use_cache",
    is_flag=True,
    default=True,
    help="Use cached RSS and channel data (default: True)",
)
@click.option(
    "--quota-daily",
    type=int,
    default=DAILY_QUOTA_LIMIT,
    help="Daily API quota limit (auto-calculated from config)",
)
@click.option(
    "--quota-conservative-pct",
    type=float,
    default=0.24,
    help="Conserve API when below this percentage remaining (default: 0.24)",
)
@click.option(
    "--quota-aggressive-pct",
    type=float,
    default=0.72,
    help="Use API freely when above this percentage remaining (default: 0.72)",
)
@click.option(
    "--use-phase2",
    is_flag=True,
    default=False,
    help="Use Phase 2 producer-consumer architecture for faster subtitle downloads (experimental)",
)
@click.option(
    "--phase2-batch-size",
    type=int,
    default=500,
    help="Batch size for Phase 2 subtitle inserts (default: 500)",
)
@click.option(
    "--videos-download-per-batch",
    type=int,
    default=None,
    help="Maximum videos to download across all channels",
)
@click.option(
    "--transcribe-audio-only/--no-transcribe-audio-only",
    default=True,
    help=(
        "Transcribe audio using Whisper when subtitles are not available. "
        "Requires faster-whisper to be installed. (default: enabled)"
    ),
)
@click.option(
    "--whisper-model",
    type=click.Choice(["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]),
    default="base",
    help="Whisper model size for audio transcription (default: base)",
)
@click.option(
    "--keep-audio",
    is_flag=True,
    default=False,
    help="Preserve downloaded audio files after transcription (for debugging/iteration)",
)
@click.option(
    "--clean-file",
    is_flag=True,
    default=False,
    help="Clean channels file in-place: remove invalid entries and duplicates, write back to source file",
)
@click.option("-s", "--simple", is_flag=True, default=False, help="Simple line-by-line output")
@click.option("-f", "--fzf", is_flag=True, default=False, help="fzf-style output")
@click.option(
    "--output-format",
    type=click.Choice(["vanilla", "simple", "fzf", "rich", "json"]),
    default="vanilla",
    help="Output format (default: vanilla)",
)
@click.option(
    "--progress",
    "import_progress",
    is_flag=True,
    default=False,
    help="Show progress bar during channel import",
)
@click.option(
    "--video-jobs",
    "video_jobs",
    type=int,
    default=None,
    help="Number of parallel jobs for VIDEO processing per channel (default: auto-adjusted from 1-8).",
)
@click.option(
    "--no-auto-adjust",
    "no_auto_adjust_video_jobs",
    is_flag=True,
    default=False,
    help="Disable dynamic video_jobs adjustment based on rate limit feedback (enabled by default).",
)
def batch_download(
    input_file: str | None,
    import_file: str | None,
    import_only: bool,
    dry_run: bool,
    output_file: str | None,
    jobs: int,
    language: str,
    cookies_from_browser: str,
    no_cookies: bool,
    delay: float,
    max_retries: int,
    continue_on_error: bool,
    no_fail_fast: bool,
    no_skip_initial_wait: bool,
    tui: bool,
    export_report: str,
    limit: int,
    richo: bool,
    rich: bool,
    rich_1: bool,
    time_per_video: float,
    time_per_channel: float,
    time_per_batch: float,
    videos_download_per_channel: int,
    channels_download_per_batch: int,
    display_plugin: str,
    parallel_workers: int,
    rich_progress: bool,
    rich_display: str,
    auto_backfill: bool,
    freshness_hours: int,
    use_cache: bool,
    videos_download_per_batch: int,
    quota_daily: int,
    quota_conservative_pct: float,
    quota_aggressive_pct: float,
    use_phase2: bool,
    phase2_batch_size: int,
    transcribe_audio_only: bool,
    whisper_model: str,

    keep_audio: bool,
    clean_file: bool,
    simple: bool,
    fzf: bool,
    output_format: str,
    import_progress: bool,
    video_jobs: int | None,
    no_auto_adjust_video_jobs: bool,
) -> None:
    """Batch download multiple YouTube channels from file or direct input."""

    # Normalize legacy flags to output_format
    output_format = normalize_output_format(simple, fzf, rich, rich_1, richo)

    # Handle cookies: --no-cookies overrides --cookies-from-browser
    if no_cookies:
        cookies_from_browser = None

    # Validate display options for conflicting combinations
    validate_display_options(
        simple=simple,
        fzf=fzf,
        rich=rich,
        richo=richo,
        rich_1=rich_1,
        json=False,  # batch-download doesn't have --json option yet
    )

    # Handle channel import (-i/--import flag)
    if import_file:
        from yt_fts.services.channel_intake import ChannelIntakeService

        console.print(f"[cyan]  Importing from:[/cyan] {import_file}")

        service = ChannelIntakeService(console=console, use_progress=import_progress)

        try:
            results, summary = service.process(
                file_path=import_file,
                validate_only=dry_run,
                dry_run=dry_run,

            )

            # Display summary
            console.print("")  # blank line
            console.print("[bold]  Import Summary:[/bold]")
            service.display_summary(summary)

            # Export valid channels if requested
            if output_file:
                count = service.export_valid_channels(results, output_file)
                console.print(f"  [cyan]Exported {count} valid channels to:[/cyan] {output_file}")

            # If import-only, stop here
            if import_only:
                if dry_run:
                    console.print("[yellow]  Dry run complete - no changes made[/yellow]")
                else:
                    console.print(f"  [green]Imported {summary.valid} new channel(s)[/green]")
                return

            # If not actually importing (dry-run), stop here
            if dry_run:
                console.print("[yellow]  Dry run complete - no changes made[/yellow]")
                return

            # Continue with download using the imported channels
            console.print("  [green]Proceeding with download...[/green]")
            console.print("")

        except FileNotFoundError as e:
            console.print(f"[red]  Error: {e}[/red]")
            raise click.ClickException(str(e))
        except Exception as e:
            console.print(f"[red]  Import failed: {e}[/red]")
            raise click.ClickException(str(e))

    # Handle --from-db: create temp file with channels from database
    from_database_mode = False
    if not input_file:
        channels, input_file = load_channels_from_database()
        if not channels:
            print("[ERROR  ] No channels found in database.")
            return
        from_database_mode = True
        print(f"[INFO   ] Loaded {len(channels)} channels from database")

    # Initialize quota strategy
    def log_msg(tag: str, message: str, level: int = 20) -> None:
        timestamp = dt.now().strftime("%H:%M:%S")
        sys.stderr.write(f"[{timestamp}] [{tag}] {message}" + chr(10))
        sys.stderr.flush()

    log_msg("QUOTA", "Computing strategy...")
    quota_strategy = initialize_quota_strategy(
        quota_daily, quota_conservative_pct, quota_aggressive_pct
    )
    log_msg("QUOTA", quota_strategy.get_status_message())

    # Metadata-only mode: no rate limit, only daily quota - use 0 delay by default
    if videos_download_per_channel == 0 and delay == 60.0:
        delay = 0.0

    # Configure logging for clean Rich UI (suppress debug messages)
    import logging

    # Configure the download handler logger based on Rich mode
    download_logger = logging.getLogger(
        "yt_fts.download.download_handler.DownloadHandler"
    )
    if rich or rich_1:
        # Suppress DEBUG/INFO logging for clean Rich UI
        download_logger.setLevel(logging.WARNING)
    else:
        # Default logging level for standard UI
        download_logger.setLevel(logging.DEBUG)

    print(f"[INFO   ] Starting batch download for: {input_file}")

    # Determine which Rich mode to use
    rich_mode = determine_rich_mode(rich, rich_1, richo)

    # Initialize Rich formatter if --richo flag is used
    rich_formatter = None
    if richo:
        try:
            from yt_fts.ui.rich_formatter import create_rich_formatter

            rich_formatter = create_rich_formatter(verbose=continue_on_error)
            rich_formatter.print_main_header("YouTube Batch Downloader")
        except ImportError:
            console.print(
                "[yellow]Warning: Rich formatter not available, using basic output[/yellow]"
            )
            richo = False
    else:
        console.print("[bold blue]YouTube Batch Downloader for yt-fts[/bold blue]")

    # Show current status before starting
    if not rich and not rich_1 and not from_database_mode:
        try:
            from .status_display import StatusDisplay

            status = StatusDisplay(console)
            console.print("\nCurrent System Status:")
            status.display_minimal_status()
            console.print()
        except ImportError:
            console.print(
                "[dim]Status: Basic mode - install status_display for full info[/dim]"
            )
            console.print()

    # Read channels from input file or use direct input
    channels = []

    # Check if input_file is a file path or direct channel input

    # Define quiet_mode early since it's used in the file reading section
    os.getenv("YT_FTS_WRAPPER_MODE")
    quiet_mode = os.getenv("YT_FTS_QUIET_MODE") == "1"

    # Try to find the input file in common locations
    input_file_path = find_input_file(input_file)
    if not input_file_path:
        # Try in the data subdirectory
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_path = os.path.join(script_dir, "data", os.path.basename(input_file))
        if os.path.isfile(data_path):
            input_file_path = data_path

    if input_file_path:
        # Read channels from file (quiet, show summary after)
        with Path(input_file_path).open(encoding="utf-8") as f:
            lines_list = f.readlines()

        raw_count = len(lines_list)
        for line in lines_list:
            line = line.strip()
            if line and not line.startswith("#") and line != ":":
                channels.append(line)

        filtered_count = len(channels)

        # Apply limit if specified
        if limit and limit > 0:
            original_count = len(channels)
            channels = channels[:limit]
            if not quiet_mode:
                console.print(
                    f"[yellow]Limiting to {limit} channels (from {original_count} total)[/yellow]"
                )

        # Show progress in column format
        log_msg("LOAD", f"{input_file_path}")
        log_msg("LOAD", f"  Raw:     {raw_count} lines")
        log_msg("LOAD", f"  Filter:  {filtered_count} valid")
        sys.stderr.flush()

        try:
            from yt_fts.services.channel_cleaner import ChannelCleaner

            cleaner = ChannelCleaner(console)
            cleaned_channels, stats = cleaner.clean_channels_file_cached(
                file_path=input_file_path,
                prefer_handles=False,
                convert_names=True
            )

            channels = cleaned_channels
            cache_hit = stats.get("cache_hit", False)

            # Show final result with column alignment
            if cache_hit:
                log_msg("LOAD", "  Cache:   hit (using cleaned list)")
            else:
                dup_msg = f' ({stats["duplicates_removed"]} dupes removed)' if stats["duplicates_removed"] > 0 else ""
                inv_msg = f', {stats["invalid_removed"]} invalid' if stats.get("invalid_removed", 0) > 0 else ""
                log_msg("LOAD", f"  Clean:   {len(channels)} channels{dup_msg}{inv_msg}")
            sys.stderr.flush()

            # Write cleaned channels back to source file if --clean-file flag is set
            if clean_file:
                try:
                    Path(input_file_path).write_text("\n".join(cleaned_channels) + "\n", encoding="utf-8")
                    log_msg("LOAD", f"  File:    cleaned list written back to {input_file_path}")
                except Exception as write_error:
                    console.print(f"[yellow]WARNING: Failed to write cleaned file: {write_error}[/yellow]")

            # Exit early if dry_run is set (after cleaning)
            if dry_run:
                console.print("[yellow]Dry run complete - no changes made to database[/yellow]")
                return

        except Exception as e:
            console.print(f"[yellow]WARNING: Channel cleaning failed: {e}[/yellow]")
            console.print("[dim]Continuing with original channels...[/dim]")
    else:
        # Direct channel input
        channels = [input_file]

    # Create batch downloader with channels and specified options
    fail_fast = not bool(no_fail_fast)
    skip_initial_delay_on_startup = not bool(no_skip_initial_wait)

    # Show configuration with Rich if enabled
    # wrapper_mode and quiet_mode already defined above

    # Python handles Rich UI when not in quiet mode (allow Rich with wrapper)

    if rich_formatter and not quiet_mode:
        # Display configuration with Rich blue box formatter
        config_items = [
            {"setting": "Mode", "value": "Full Processing" if not tui else "TUI Mode"},
            {"setting": "UI", "value": "Enhanced Rich UI (professional formatting)"},
            {"setting": "Channels", "value": str(len(channels))},
            {"setting": "Jobs", "value": str(jobs)},
            {"setting": "Delay", "value": f"{delay}s"},
            {"setting": "Cookies", "value": cookies_from_browser or "None"},
            {
                "setting": "Input File",
                "value": (
                    input_file
                    if os.path.isfile(input_file)
                    else f"Direct channel: {input_file}"
                ),
            },
        ]

        # Get browser information if available
        browser_info = []
        optimal_setup = []

        # Check for Firefox (optimal setup)

        if os.path.exists(
            os.path.expanduser("~") + "/AppData/Roaming/Mozilla/Firefox/Profiles"
        ) or os.path.exists(
            os.path.expandvars("$APPDATA") + "/Mozilla/Firefox/Profiles"
        ):
            browser_info.append("firefox")
            if cookies_from_browser == "firefox":
                optimal_setup = [
                    "34 cookies extracted vs 7 with Chrome",
                    "Instant extraction (0.00s vs 6+ seconds)",
                    "No admin rights required",
                ]

        # Check for Chrome
        if os.path.exists(
            os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data"
        ) or os.path.exists(
            os.path.expandvars("$LOCALAPPDATA") + "/Google/Chrome/User Data"
        ):
            browser_info.append("chrome")

        rich_formatter.print_deployment_config(
            title="YouTube Batch Downloader - Rich UI Mode",
            config_items=config_items,
            browser_info=browser_info or [],
            optimal_setup=optimal_setup or [],
        )
    elif not quiet_mode and not simple and not fzf:
        if from_database_mode:
            input_display = f"Database: {get_db_path()}"
        elif os.path.isfile(input_file):
            input_display = input_file
        else:
            input_display = f"Direct channel: {input_file}"

        display_batch_startup_summary(
            input_display=input_display,
            channels_count=len(channels),
            jobs=jobs,
            parallel_workers=parallel_workers,
            language=language,
            cookies_from_browser=cookies_from_browser,
            delay=delay,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
            fail_fast=fail_fast,
            skip_initial_wait=skip_initial_delay_on_startup,
        )

    # Helper to load display plugin instance for parallel processor
    def _load_display_plugin(plugin_name: str):
        try:
            from yt_fts.display import create_plugin, load_builtin_plugins
            from yt_fts.display.base import PluginContext
            load_builtin_plugins()
            context = PluginContext(command="download", console=console, options={})
            return create_plugin(plugin_name, context)
        except Exception:
            return None

    # Use parallel processor if --parallel-workers > 1, otherwise use standard BatchDownloader
    if parallel_workers > 1:
        console.print(f"\n[cyan] Using {parallel_workers} parallel worker threads[/cyan]")
        if use_phase2:
            console.print(f"[cyan] Phase 2: Producer-consumer architecture (batch size: {phase2_batch_size})[/cyan]")

        # Load display plugin instance for the parallel processor
        display_plugin_instance = _load_display_plugin(display_plugin)

        processor = ParallelBatchProcessor(
            quota_strategy=quota_strategy,  # Adaptive quota management
            language=language,
            cookies_from_browser=cookies_from_browser,
            delay_between_channels=delay,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
            time_per_channel=time_per_channel,
            time_per_video=time_per_video,
            time_per_batch=time_per_batch,
            min_saved=videos_download_per_channel,
            videos_download_per_batch=videos_download_per_batch,
            display_plugin=display_plugin_instance,
            auto_backfill=auto_backfill,
            freshness_hours=freshness_hours,
            use_rich_progress=rich_progress,
            rich_display_mode=rich_display,
            use_phase2=use_phase2,
            phase2_batch_size=phase2_batch_size,
            use_fzf=fzf,
            use_json=output_format == "json",
            video_jobs=video_jobs if video_jobs is not None else 1,
            auto_adjust_video_jobs=not no_auto_adjust_video_jobs,
        )

        # Process channels in parallel
        console.print(f"Ready to process {len(channels)} channels in parallel\n")

        try:
            results = processor.process_channels(
                channels=channels,
                num_workers=parallel_workers
            )

            # Print results summary
            from yt_fts.download.summary import print_summary
            print_summary(console, results, channels)

            return  # Success

        except Exception as e:
            console.print(f"\n[red]❌ Parallel processing failed: {e}[/red]")
            if fail_fast:
                msg = f"Parallel processing failed: {e}"
                raise click.ClickException(msg)
            console.print("[yellow]Falling back to sequential processing...[/yellow]\n")
                # Continue to sequential processing below

    # Handle display modes: simple, fzf, or default (straight logs)
    if simple or fzf:
        # Disable Rich UI for simple/fzf modes
        rich_mode = None
        rich_1 = False
        rich = False
        richo = False

        print(f"[INFO] Processing {len(channels)} channels")

        if fzf:
            # FZF mode: print clean list
            for ch in channels[:50]:
                print(f"{ch}")
            if len(channels) > 50:
                print(f"... and {len(channels) - 50} more")
        elif simple:
            # Simple mode: minimal progress
            print(f"Starting download of {len(channels)} channels...")

    # Standard sequential processing (original behavior)
    # Use video_jobs if specified, otherwise fall back to jobs
    video_jobs_value = video_jobs if video_jobs is not None else jobs
    if not no_auto_adjust_video_jobs:
        # Auto-adjust is enabled by default (use --no-auto-adjust to disable)
        video_jobs_value = video_jobs if video_jobs is not None else 2

    downloader = BatchDownloader(
        channels=channels,
        jobs=video_jobs_value,
        language=language,
        cookies_from_browser=cookies_from_browser,
        delay_between_channels=delay,
        max_retries=max_retries,
        continue_on_error=continue_on_error,
        rich_formatter=rich_formatter,  # Pass Rich formatter to downloader
        rich_mode=rich_mode,  # Pass Rich mode ('new', 'old', or None)
        time_per_channel=time_per_channel,  # Per-channel timeout
        time_per_video=time_per_video,  # Per-video timeout
        time_per_batch=time_per_batch,  # Total batch timeout
                min_saved=videos_download_per_channel,  # Minimum videos to successfully save
        target_downloads=channels_download_per_batch,  # Target channels to download
        videos_download_per_batch=videos_download_per_batch,  # Max videos across all channels
        quota_strategy=quota_strategy,  # Adaptive quota management
        display_plugin=display_plugin,  # Display plugin
        auto_backfill=auto_backfill,  # Auto backfill metadata
        freshness_hours=freshness_hours,
        transcribe_audio_only=transcribe_audio_only,  # Enable Whisper transcription
        whisper_model=whisper_model,  # Whisper model size
        keep_audio=keep_audio,  # Preserve audio files for debugging
    )
    if rich_formatter and not quiet_mode and not simple and not fzf:
        console.print(f"Ready to process {len(channels)} channels")


    # If user opted into the TUI, launch and exit early
    if tui:
        try:
            from .ui.dashboard import (
                MIN_TEXTUAL_VERSION,
                GoogleStitchUI,
                is_textual_compatible,
            )

            compatible, installed = is_textual_compatible()
            if installed is None:
                console.print(
                    "WARNING:  [yellow]Textual not installed or not importable.[/yellow]"
                )
                console.print(
                    f'💡 Install Textual to use the interactive dashboard, e.g., `pip install "textual>={MIN_TEXTUAL_VERSION}"`'
                )
                if fail_fast:
                    console.print(
                        "🛑 [red]Fail-fast enabled: aborting due to missing Textual.[/red]"
                    )
                    msg = "Missing required dependency: textual"
                    raise click.ClickException(msg)
                console.print(
                    "WARNING:  Proceeding without dashboard because degraded mode is enabled"
                )
                # fallthrough to normal batch behavior
            elif not compatible:
                console.print(
                    f"WARNING:  [yellow]Textual version {installed} is older than the required {MIN_TEXTUAL_VERSION}.[/yellow]"
                )
                console.print(
                    f'💡 Upgrade by running: pip install "textual>={MIN_TEXTUAL_VERSION}"'
                )
                if fail_fast:
                    console.print(
                        "🛑 [red]Fail-fast enabled: aborting due to incompatible Textual version.[/red]"
                    )
                    msg = "Incompatible Textual version"
                    raise click.ClickException(msg)
                console.print(
                    "WARNING:  Proceeding without dashboard because degraded mode is enabled"
                )
                # fallthrough to normal batch behavior
            else:
                console.print(f"🧭 Textual version detected: {installed}")

                console.print("🔷 Launching interactive dashboard (Textual TUI)...")
                GoogleStitchUI(channels=channels).run()
                console.print("🔷 Dashboard exited, bye!")
                return  # Success - let Click handle naturally
        except Exception as e:
            console.print(f"❌ [red]Failed to launch dashboard:[/red] {e!s}")
            if not fail_fast:
                # In non-fail-fast mode, proceed to the batch download after reporting the error
                console.print(
                    "WARNING:  Proceeding with batch download due to non-fail-fast configuration"
                )
            else:
                msg = f"Dashboard launch failed: {e!s}"
                raise click.ClickException(msg)

    # Start batch download with channel list (BatchDownloader now handles channels internally)

    # Import and setup graceful interruption handler
    try:
        from yt_fts.utils.interrupt_handler import GracefulInterruptHandler

        interrupt_handler = GracefulInterruptHandler()

        # Register any existing thread pools if the downloader has them
        if hasattr(downloader, "executor") and downloader.executor:
            from yt_fts.utils.interrupt_handler import register_executor

            register_executor(downloader.executor)

    except ImportError:
        console.print("[yellow]WARNING: Graceful interruption handler not available[/yellow]")
        interrupt_handler = None

    if fail_fast:
        # In fail-fast mode let exceptions bubble to the caller (useful for CI / early failure)
        if interrupt_handler:
            with interrupt_handler:
                downloader.download_all()
        else:
            downloader.download_all()

        if export_report:
            # Note: export_report method may not exist, handle gracefully
            try:
                downloader.export_report(export_report)
            except AttributeError:
                console.print(
                    "[yellow]WARNING: Export report functionality not available[/yellow]"
                )
    else:
        try:
            if interrupt_handler:
                with interrupt_handler:
                    console.print(
                    )
                    console.print(
                        "[dim]Press Ctrl+C to safely interrupt downloads[/dim]\n"
                    )
                    # download_all() is synchronous, no need for AsyncBridge
                    downloader.download_all()
            else:
                # download_all() is synchronous, no need for AsyncBridge
                downloader.download_all()

            if export_report:
                try:
                    downloader.export_report(export_report)
                except AttributeError:
                    console.print(
                        "[yellow]WARNING: Export report functionality not available[/yellow]"
                    )

        except KeyboardInterrupt:
            console.print(
                "\n\n🛑 [bold yellow]Download interrupted by user[/bold yellow]"
            )

            # Enhanced interruption handling
            if interrupt_handler:
                console.print("[green]Graceful shutdown in progress...[/green]")

                # Show progress if available
                if hasattr(downloader, "get_progress"):
                    progress = downloader.get_progress()
                    console.print(f" Progress: {progress}")

                # Save partial progress
                if hasattr(downloader, "save_progress"):
                    try:
                        downloader.save_progress()
                        console.print("💾 [green]Progress saved successfully[/green]")
                    except Exception as e:
                        console.print(
                            f"[yellow]WARNING: Could not save progress: {e}[/yellow]"
                        )

                # Display summary if available
                try:
                    downloader.display_summary()
                except (AttributeError, Exception) as e:
                    console.print(
                        f"[yellow]WARNING: Summary display functionality not available: {e}[/yellow]"
                    )

                console.print("[green]Graceful shutdown complete[/green]")
            else:
                # Fallback to basic handling
                console.print(
                    "[dim]WARNING: Basic interruption handling - consider installing graceful interruption handler[/dim]"
                )

                # Note: display_summary method may not exist, handle gracefully
                try:
                    downloader.display_summary()
                except AttributeError:
                    console.print(
                        "[yellow]WARNING: Summary display functionality not available[/yellow]"
                    )
        except Exception as e:
            console.print(f"\n\n❌ [red]Unexpected error:[/red] {e!s}")
            try:
                downloader.display_summary()
            except AttributeError:
                console.print(
                    "[yellow]WARNING: Summary display functionality not available[/yellow]"
                )


@click.command(
    name="clean-channels",
    help="""
    Clean and optimize YouTube channel lists with intelligent standardization.

    Cleaning features:
    Remove duplicate channels and entries
    Convert between @handles and full URLs
    Validate channel formats and accessibility
    Standardize naming conventions
    Generate comprehensive analysis reports

    Input support:
    Channel files with mixed formats
    Built-in preset AI/automation channel list
    Direct channel input
    Handles comments and empty lines

    Output options:
    Cleaned channel files with statistics
    Analysis-only mode for inspection
    Configurable format preferences
    Backup generation for safety

    Examples:
    yt-fts clean-channels channels.txt                    # Clean existing file
    yt-fts clean-channels --from-preset                    # Use built-in AI channels
    yt-fts clean-channels channels.txt --analyze-only     # Analyze without modifying
    """,
)
@click.argument("input_file", required=False)

@click.option(
    "-i",
    "--import",
    "import_file",
    type=click.Path(exists=True),
    default=None,
    help="Import channels from file to database before processing",
)
@click.option(
    "--import-only",
    is_flag=True,
    default=False,
    help="Only import channels, don't download any content",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be imported without making changes",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(),
    default=None,
    help="Export valid channels to file after import",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file for cleaned channels (default: input_file_cleaned.txt)",
)
@click.option(
    "--prefer-handles/--no-prefer-handles",
    default=True,
    help="Convert URLs to @handles when possible (default: True)",
)
@click.option(
    "--convert-names/--no-convert-names",
    default=True,
    help="Convert plain names to @handles (default: True)",
)
@click.option(
    "--analyze-only", is_flag=True, help="Only analyze the channel list, don't clean it"
)
@click.option(
    "--from-preset",
    is_flag=True,
    help="Use the built-in channel list instead of reading from file",
)
def clean_channels(
    input_file: str,
    output: str,
    prefer_handles: bool,
    convert_names: bool,
    analyze_only: bool,
    from_preset: bool,
) -> None:
    """Clean and optimize YouTube channel lists."""

    from yt_fts.services.channel_cleaner import (
        ChannelCleaner,
        create_channel_list_from_input,
    )

    console = get_console()
    cleaner = ChannelCleaner(console)

    console.print("[bold blue]🧹 YouTube Channel Cleaner[/bold blue]")

    try:
        # Check if input file is provided when not using preset
        if not from_preset and not input_file:
            console.print(
                "❌ [red]Error: Either provide an input file or use --from-preset[/red]"
            )
            console.print("💡 Usage: yt_fts_cli.py clean-channels channels.txt")
            console.print("💡 Or: yt_fts_cli.py clean-channels --from-preset")
            return

        # Get channel list
        if from_preset:
            console.print("[blue]📋 Using built-in channel list...[/blue]")
            channels = create_channel_list_from_input()
            input_name = "built-in list"
        else:
            with Path(input_file).open(encoding="utf-8") as f:
                channels = [line.strip() for line in f if line.strip()]
            input_name = input_file

        console.print(f"📖 Loaded {len(channels)} entries from {input_name}")

        # Analyze the channel list
        analysis = cleaner.analyze_channels(channels)
        cleaner.display_analysis(analysis)

        if analyze_only:
            console.print(
                "\nAnalysis complete. Use without --analyze-only to clean the channels."
            )
            return

        # Clean the channels
        cleaned_channels, stats = cleaner.clean_channels(
            channels, prefer_handles, convert_names
        )

        # Generate output filename
        if output is None:
            if from_preset:
                output = "channels_cleaned.txt"
            else:
                base_path = Path(input_file)
                output = (
                    base_path.parent / f"{base_path.stem}_cleaned{base_path.suffix}"
                )

        # Write cleaned channels to file
        cleaner.generate_clean_file(cleaned_channels, str(output))

        # Display results
        cleaner.display_cleanup_results(cleaned_channels, stats)

        console.print("\n💡 [bold]Next steps:[/bold]")
        console.print(f"   1. Review the cleaned file: [cyan]{output}[/cyan]")
        console.print(
            f"   2. Run batch download: [cyan]yt_fts_cli.py batch-download {output}[/cyan]"
        )

    except FileNotFoundError:
        console.print(f"❌ [red]Error: File not found: {input_file}[/red]")
        console.print(
            "💡 Use --from-preset to clean the built-in channel list instead."
        )
    except Exception as e:
        console.print(f"❌ [red]Error cleaning channels:[/red] {e!s}")


@click.command(
    name="convert-channels",
    help="""
    Convert channels.txt format to ensure proper YouTube URLs.

    Converts various channel formats to standardized YouTube URLs:
    @handles → https://www.youtube.com/@handle
    Channel names → @handles
    Mixed formats → Consistent URLs

    This command ensures your channels.txt file is ready for batch downloads.
    """,
)
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    default="channels_converted.txt",
    help="Output file for converted channels (default: channels_converted.txt)",
)
@click.option(
    "--prefer-handles",
    is_flag=True,
    default=False,
    help="Convert URLs to @handles instead of URLs",
)
@click.option(
    "--backup",
    is_flag=True,
    default=True,
    help="Create backup of original file",
)
def convert_channels(input_file, output, prefer_handles, backup):
    """Convert channels.txt format to ensure proper YouTube URLs."""
    from yt_fts.services.channel_cleaner import ChannelCleaner

    console = get_console()

    console.print("🔄 Converting channels format...")
    console.print(f"Input: {input_file}")
    console.print(f"Output: {output}")

    # Create backup if requested
    if backup:
        backup_file = f"{input_file}.backup"
        try:
            import shutil

            shutil.copy2(input_file, backup_file)
            console.print(f"💾 Backup created: {backup_file}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")

    try:
        # Read input channels
        with Path(input_file).open(encoding="utf-8") as f:
            channels = [line.strip() for line in f.readlines()]

        # Create channel cleaner and convert
        cleaner = ChannelCleaner(console=console)
        cleaned_channels, stats = cleaner.clean_channels(
            channels, prefer_handles=prefer_handles, convert_names=True
        )

        # Write converted channels
        with Path(output).open("w", encoding="utf-8") as f:
            for channel in cleaned_channels:
                f.write(channel + "\n")

        console.print("\n[green]Conversion completed![/green]")
        console.print(f"Original channels: {stats['original_count']}")
        console.print(f"Converted: {stats['cleaned_count']}")
        console.print(f"Duplicates removed: {stats['duplicates_removed']}")
        console.print(f"Invalid removed: {stats['invalid_removed']}")
        console.print(f"Final channels: {stats['final_count']}")

        if prefer_handles:
            console.print(
                "\n[cyan]💡 Tip: Use without --prefer-handles for full URLs (recommended for downloads)[/cyan]"
            )

    except Exception as e:
        console.print(f"[red]❌ Error converting channels:[/red] {e!s}")
        return 1

    return 0


@click.command(
    name="update-all",
    help="""
    Update all channels in the database with latest content.

    Updates all downloaded channels:
    Downloads new videos and subtitles since last update
    Processes all channels in your library automatically
    Automatic embeddings generation for new content
    Progress tracking across all channels
    Intelligent retry and error recovery
    Continue on error mode for resilient processing

    This is ideal for:
    Keeping your library current with latest videos
    Batch updating after extended periods
    Automated maintenance workflows
    """,
)
@click.option(
    "--cookies-from-browser",
    default="firefox",
    help="Browser to extract cookies from (default: firefox). Use --no-cookies to disable.",
)
@click.option(
    "--no-cookies",
    is_flag=True,
    default=False,
    help="Disable browser cookies extraction",
)
@click.option(
    "--jobs",
    "-j",
    type=int,
    default=2,
    help="Number of parallel download jobs per channel (default: 2, recommended: 1-3)",
)
@click.option(
    "--language",
    "-l",
    default="en",
    help="Language of the subtitles to download (default: en)",
)
@click.option(
    "--delay",
    "-d",
    type=float,
    default=60.0,
    help="Delay between processing channels in seconds (default: 60.0)",
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    default=True,
    help="Continue processing other channels if one fails (default: True)",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Maximum number of retry attempts per channel (default: 3)",
)
def update_all(
    cookies_from_browser: str | None,
    jobs: int,
    language: str,
    delay: float,
    continue_on_error: bool,
    max_retries: int,
    no_cookies: bool,
) -> None:
    """Update all channels in the database with latest content."""
    # Handle cookies: --no-cookies overrides --cookies-from-browser
    if no_cookies:
        cookies_from_browser = None

    from rich.progress import Progress

    from yt_fts.download.download_handler import DownloadHandler
    from yt_fts.utils.rich_console import get_console

    from .db_utils import get_all_channel_ids

    console = get_console()

    console.print("🔄 Updating all channels in database...")

    # Get all channels in database
    try:
        channel_ids = get_all_channel_ids()
        if not channel_ids:
            console.print("[yellow]WARNING: No channels found in database.[/yellow]")
            console.print("💡 Use 'yt-fts download' to add channels first.")
            return

        console.print(f"[green] Found {len(channel_ids)} channels to update[/green]")

        # Create progress bar
        with Progress() as progress:
            task_id = progress.add_task(
                f"[cyan]Updating {len(channel_ids)} channels...[/cyan]",
                total=len(channel_ids),
            )

            # Process each channel
            successful_updates = []
            failed_updates = []

            for i, channel_id in enumerate(channel_ids):
                try:
                    console.print(
                        f"[blue]📡 Updating channel {i+1}/{len(channel_ids)}: {channel_id}[/blue]"
                    )

                    # Create download handler for this channel
                    handler = DownloadHandler(
                        number_of_jobs=jobs,
                        language=language,
                        cookies_from_browser=cookies_from_browser,
                        fail_fast=False,
                    )

                    # Update the channel
                    handler.update_channel(channel_id)
                    successful_updates.append(channel_id)

                    progress.advance(task_id)

                except Exception as e:
                    failed_updates.append((channel_id, str(e)))
                    console.print(f"[red]❌ Failed to update {channel_id}: {e}[/red]")
                    progress.advance(task_id)

                    if not continue_on_error:
                        console.print(
                            "[red]Stopping due to error (use --continue-on-error to continue)[/red]"
                        )
                        break

                # Add delay between channels
                if i < len(channel_ids) - 1:
                    import time

                    time.sleep(delay)

            # Summary
            console.print("\n[bold] Update Summary:[/bold]")
            console.print(f"Successful: {len(successful_updates)}")
            console.print(f"❌ Failed: {len(failed_updates)}")
            console.print(
                f" Total processed: {len(successful_updates) + len(failed_updates)}/{len(channel_ids)}"
            )

            if failed_updates and continue_on_error:
                console.print("\n[yellow]WARNING: Failed channels:[/yellow]")
                for channel_id, error in failed_updates[:5]:
                    console.print(f"   {channel_id}: {error}")
                if len(failed_updates) > 5:
                    console.print(f"   ... and {len(failed_updates) - 5} more")

    except Exception as e:
        console.print(f"[red]❌ Error updating channels:[/red] {e!s}")
        _handle_command_result(1)
        return

    console.print("[green]Update completed![/green]")
