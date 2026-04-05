import os

# Suppress tqdm progress bars for cleaner output
os.environ["TQDM_DISABLE"] = "1"

import builtins
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

# Load environment variables from .env file if it exists
import sys

# Skip for --help to avoid unnecessary noise
if "--help" not in sys.argv and "-h" not in sys.argv:
    from yt_fts.utils.config import find_and_load_env


    env_path = find_and_load_env()
    if env_path:
        print(f"Loaded environment variables from {env_path}")
    else:
        print("WARNING:  .env file not found in expected locations")
# OpenAI import moved to chat command (lazy import to avoid ImportError)
from yt_fts import __version__ as YT_FTS_VERSION
from yt_fts.utils.rich_console import get_console

from .transcribe_cli import transcribe

console = get_console()
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


def _remove_duplicate_results(results: builtins.list[Any]) -> builtins.list[Any]:
    """
    Remove duplicate results from combined FTS and vector search results.
    Prioritizes vector search results over FTS for the same content.
    """
    seen = set()
    unique_results = []

    for result in results:
        # Handle both dict and object formats
        if isinstance(result, dict):
            video_id = result.get("video_id", "")
            start_time = result.get("start_time", result.get("timestamp", ""))
        else:
            video_id = getattr(result, "video_id", "")
            start_time = getattr(result, "start_time", getattr(result, "timestamp", ""))

        # Create a unique identifier based on video_id and timestamp
        identifier = f"{video_id}_{start_time}"

        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(result)

    return unique_results


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


def _display_unified_results(
    results: builtins.list[Any], query: str, has_fts: bool, has_vector: bool
) -> None:
    """
    Display unified search results with clear labeling of search type.
    """
    if not results:
        console.print(f"[yellow]No matches found for query: '{query}'[/yellow]")
        return

    # Group by channel
    channels = {}
    for result in results:
        # Handle both dict and object formats
        if isinstance(result, dict):
            channel_name = result.get("channel_name", result.get("channel", "Unknown"))
        else:
            channel_name = getattr(
                result, "channel_name", getattr(result, "channel", "Unknown")
            )

        if channel_name not in channels:
            channels[channel_name] = []
        channels[channel_name].append(result)

    console.print(f"\n🔍 [bold]Unified Search Results:[/bold] '{query}'")
    if has_fts and has_vector:
        console.print(" Combined full-text + semantic search")
    elif has_fts:
        console.print(" Full-text search results")
    else:
        console.print(" Semantic search results")

    console.print(f"📈 Found {len(results)} matches in {len(channels)} channel(s)\n")

    for channel_name, channel_results in channels.items():
        console.print(f"🔷 {channel_name} ({len(channel_results)} matches)")

        for i, result in enumerate(channel_results, 1):
            # Handle both dict and object formats
            if isinstance(result, dict):
                result_type = result.get("result_type", "fts")
                video_title = result.get("video_title", result.get("title", "Unknown"))
                relevance_score = result.get(
                    "relevance_score", result.get("similarity", 0)
                )
                timestamp = result.get(
                    "timestamp", result.get("start_time", "00:00:00")
                )
                text = result.get("text", "")
                link = result.get("link", "")
            else:
                result_type = getattr(result, "result_type", "fts")
                video_title = getattr(result, "video_title", "Unknown")
                relevance_score = getattr(
                    result, "relevance_score", getattr(result, "similarity", 0)
                )
                timestamp = getattr(
                    result, "timestamp", getattr(result, "start_time", "00:00:00")
                )
                text = getattr(result, "text", "")
                link = getattr(result, "link", "")

            # Determine search type and format accordingly
            if result_type == "vector":
                search_indicator = "🧠"
                score_text = (
                    f" [dim](similarity: {relevance_score:.3f})[/dim]"
                    if relevance_score > 0
                    else ""
                )
            else:
                search_indicator = "🔍"
                score_text = ""

            console.print(
                f"   {search_indicator} [blue]{i}.[/blue] {video_title}{score_text}"
            )
            console.print(
                f"      💬 [grey62][link={link}]{timestamp}[/link][/grey62] → {text[:150]}{'...' if len(text) > 150 else ''}"
            )

        console.print()


def export_multi_channel_results(results, query, export_type):
    """Export multi-channel search results to CSV."""
    import csv

    if not results:
        console.print("[yellow]No results to export[/yellow]")
        return

    # Generate filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c.isspace()).rstrip()[:20]
    filename = f"{export_type}_{safe_query.replace(' ', '_')}_{timestamp}.csv"

    # Write CSV
    with Path(filename).open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "rank",
            "query",
            "text",
            "video_id",
            "video_title",
            "channel_id",
            "channel_name",
            "start_time",
            "timestamp",
            "link",
            "relevance_score",
            "result_type",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i, result in enumerate(results, 1):
            writer.writerow(
                {
                    "rank": i,
                    "query": query,
                    "text": result.text,
                    "video_id": result.video_id,
                    "video_title": result.video_title,
                    "channel_id": result.channel_id,
                    "channel_name": result.channel_name,
                    "start_time": result.start_time,
                    "timestamp": result.timestamp,
                    "link": result.link,
                    "relevance_score": f"{result.relevance_score:.3f}",
                    "result_type": result.result_type,
                }
            )

    console.print(f"[green]Results exported to:[/green] {filename}")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(YT_FTS_VERSION, message="yt_fts version: %(version)s")
def cli() -> None:
    pass


# ============================================================================
# Register transcribe command
# ============================================================================
cli.add_command(transcribe)

# ============================================================================
# Import and register command modules
# ============================================================================

# Download commands
# Bookmark commands (group)
from .bookmark_cli import bookmark_group

# Content commands
from .content_cli import (
    channel_stats_command as channel_stats,
)
from .content_cli import (
    export_command as export,
)
from .content_cli import (
    list_command as list_cmd,
)
from .content_cli import (
    stats_command as stats,
)
from .content_cli import (
    watch_command as watch,
)
from .content_cli import (
    watch_history_command as watch_history,
)
from .download_cli import (
    batch_download,
    clean_channels,
    convert_channels,
    download,
    embeddings,
    embeddings_status,
    update,
    update_all,
)

# LLM commands
from .llm_cli import llm, summarize

# Playlist commands (group)
from .playlist_cli import playlist_group

# Plugin commands
from .plugin_cli import plugins_cmd

# Preset commands
from .preset_cli import preset_channels

# Search commands
from .search_cli import search, vsearch, watch_search

# Transcription commands
from .transcription_cli import transcribe_no_subs

# Utility commands
from .utility_cli import config, delete, diagnose, health, reset_quota, status

# ============================================================================
# Register all commands with the main CLI group
# ============================================================================

# Download commands
cli.add_command(download)
cli.add_command(update)
cli.add_command(update_all)
cli.add_command(batch_download)
cli.add_command(embeddings)
cli.add_command(embeddings_status)
cli.add_command(clean_channels)
cli.add_command(convert_channels)
cli.add_command(transcribe_no_subs)

# Search commands
cli.add_command(search)
cli.add_command(vsearch)
cli.add_command(watch_search)

# Content commands
cli.add_command(list_cmd)
cli.add_command(export)
cli.add_command(stats)
cli.add_command(channel_stats)
cli.add_command(watch)
cli.add_command(watch_history)

# Utility commands
cli.add_command(health)
cli.add_command(diagnose)
cli.add_command(delete)
cli.add_command(config)
cli.add_command(status)
cli.add_command(reset_quota)

# LLM commands
cli.add_command(llm)
cli.add_command(summarize)

# Preset commands
cli.add_command(preset_channels)

# Plugin commands
cli.add_command(plugins_cmd)

# Playlist and bookmark groups
cli.add_command(playlist_group)
cli.add_command(bookmark_group)

# ============================================================================
# Import and register Batch and Queue command groups
# ============================================================================
from .batch_cli import batch_group, queue_group

cli.add_command(batch_group)
cli.add_command(queue_group)
