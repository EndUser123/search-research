"""
Channel loading utilities for batch download operations.

Extracted from batch_download for better modularity.
"""

from __future__ import annotations
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from yt_fts.utils.logging import log_msg
from yt_fts.utils.rich_console import get_console

console = get_console()

def _shorten_display_value(value: str, max_len: int) -> str:
    """Shorten long display values to avoid terminal wrapping."""
    if len(value) <= max_len:
        return value
    if max_len <= 3:
        return value[:max_len]
    return f"...{value[-(max_len - 3):]}"


def display_batch_startup_summary(
    *,
    input_display: str,
    channels_count: int,
    jobs: int,
    parallel_workers: int,
    language: str,
    cookies_from_browser: str | None,
    delay: float,
    max_retries: int,
    continue_on_error: bool,
    fail_fast: bool,
    skip_initial_wait: bool,
) -> None:
    """Display a readable batch-download configuration summary."""
    from rich import box
    from rich.table import Table

    labels = [
        "Input",
        "Channels",
        "Language",
        "Cookies",
        "Delay",
        "Max retries",
        "Continue on error",
        "Fail-fast",
        "Skip initial wait",
    ]
    if parallel_workers > 1:
        labels.extend(["Parallel workers", "Mode"])
    else:
        labels.append("Jobs per channel")
    max_label_len = max(len(label) for label in labels)
    term_width = shutil.get_terminal_size((120, 20)).columns
    max_value_len = max(20, term_width - (max_label_len + 6))
    input_display = _shorten_display_value(input_display, max_value_len)

    table = Table(
        title="Batch Download Configuration",
        box=box.ASCII,
        show_header=False,
        padding=(0, 1),
    )
    table.add_column("Setting", style="dim", no_wrap=True)
    table.add_column("Value")

    table.add_row("Input", input_display)
    table.add_row("Channels", str(channels_count))
    if parallel_workers > 1:
        table.add_row("Parallel workers", str(parallel_workers))
        table.add_row("Mode", "ThreadPoolExecutor")
    else:
        table.add_row("Jobs per channel", str(jobs))
    table.add_row("Language", language)
    table.add_row("Cookies", cookies_from_browser or "None")
    table.add_row("Delay", f"{delay}s")
    table.add_row("Max retries", str(max_retries))
    table.add_row("Continue on error", "Yes" if continue_on_error else "No")
    table.add_row("Fail-fast", "Yes" if fail_fast else "No")
    table.add_row("Skip initial wait", "Yes" if skip_initial_wait else "No")

    console.print("")
    console.print(table)
    console.print("")
    console.print(f"Ready to process {channels_count} channels")
@dataclass
class ChannelLoadResult:
    """Result of channel loading operation."""
    channels: list[str]
    source: str  # "file", "database", "direct"
    raw_count: int = 0
    filtered_count: int = 0
    duplicates_removed: int = 0


    """Log a message with timestamp to stderr."""


def load_channels_from_database() -> str | None:
    """Load channels from database and return temp file path.

    Returns:
        Path to temp file containing channel URLs, or None if no channels found.
    """
    from sqlite_utils import Database

    from yt_fts.core.database import get_db_path


    db = Database(get_db_path())
    channels = db.execute("SELECT channel_url FROM Channels").fetchall()

    if not channels:
        return None

    # Create temp file with channel URLs
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix="_channels.txt",
        delete=False
    ) as f:
        for row in channels:
            f.write(row[0] + "\n")
        return f.name



def load_channels_from_input(
    input_file: str,
    limit: int = 0,
    quiet_mode: bool = False,
) -> ChannelLoadResult:
    """Load and validate channels from input file.

    Args:
        input_file: Path to input file or direct channel input
        limit: Maximum number of channels to load (0 = no limit)
        quiet_mode: If True, suppress progress messages

    Returns:
        ChannelLoadResult containing loaded channels and metadata
    """
    channels = []
    input_file_path = None
    raw_count = 0

    # Try to find the input file in common locations
    if os.path.isfile(input_file):
        input_file_path = input_file
    else:
        # Try relative to the script directory
        script_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        candidate_path = os.path.join(script_dir, input_file)
        if os.path.isfile(candidate_path):
            input_file_path = candidate_path
        else:
            # Try in the data subdirectory
            data_path = os.path.join(script_dir, "data", os.path.basename(input_file))
            if os.path.isfile(data_path):
                input_file_path = data_path

    if input_file_path:
        # Read channels from file
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

        # Show progress
        log_msg("LOAD", f"{input_file_path}")
        log_msg("LOAD", f"  Raw:     {raw_count} lines")
        log_msg("LOAD", f"  Filter:  {filtered_count} valid")

        # Clean channels (remove duplicates, normalize) - uses caching
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

            # Show cache status
            if cache_hit:
                log_msg("LOAD", "  Cache:   hit (using cleaned list)")
            else:
                dup_msg = f' ({stats["duplicates_removed"]} dupes removed)' if stats["duplicates_removed"] > 0 else ""
                inv_msg = f', {stats["invalid_removed"]} invalid' if stats.get("invalid_removed", 0) > 0 else ""
                log_msg("LOAD", f"  Clean:   {len(channels)} channels{dup_msg}{inv_msg}")
            return ChannelLoadResult(
                channels=channels,
                source="file",
                raw_count=raw_count,
                filtered_count=filtered_count,
                duplicates_removed=stats.get("duplicates_removed", 0),
            )

        except Exception as e:
            console.print(f"[yellow]WARNING: Channel cleaning failed: {e}[/yellow]")
            console.print("[dim]Continuing with original channels...[/dim]")

            return ChannelLoadResult(
                channels=channels,
                source="file",
                raw_count=raw_count,
                filtered_count=filtered_count,
            )
    else:
        # Direct channel input
        return ChannelLoadResult(
            channels=[input_file],
            source="direct",
            raw_count=1,
            filtered_count=1,
        )


def load_channels_for_batch(
    input_file: str | None,
    limit: int = 0,
    quiet_mode: bool = False,
) -> tuple[list[str], str]:
    """Load channels for batch processing.

    This is the main entry point that handles:
    1. Loading from database if no input file specified
    2. Loading and cleaning from input file

    Args:
        input_file: Path to input file, or None to load from database
        limit: Maximum number of channels to load
        quiet_mode: If True, suppress progress messages

    Returns:
        Tuple of (channels list, source description)
    """
    # Handle --from-db: create temp file with channels from database
    if not input_file:
        temp_file = load_channels_from_database()
        if temp_file is None:
            console.print("[ERROR  ] No channels found in database.")
            return [], "none"
        input_file = temp_file
        console.print("[INFO   ] Loaded channels from database")

    result = load_channels_from_input(input_file, limit, quiet_mode)
    return result.channels, result.source
