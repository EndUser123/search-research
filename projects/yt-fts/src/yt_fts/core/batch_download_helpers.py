"""
Helper functions for batch_download command.

Extracted from download_cli.py to reduce complexity and improve testability.
"""
from __future__ import annotations

from datetime import datetime as dt
import sys
import click
from rich.console import Console

from yt_fts.download.batch_helpers import (
    determine_rich_mode,
    initialize_quota_strategy,
    normalize_output_format,
)

# Get console instance
from yt_fts.utils.rich_console import get_console
console = get_console()


def validate_and_normalize_batch_params(
    debug: bool,
    simple: bool,
    fzf: bool,
    rich: bool,
    rich_1: bool,
    richo: bool,
    no_cookies: bool,
    cookies_from_browser: str,
) -> tuple[str, str | None]:
    """Validate and normalize batch download parameters.
    
    Args:
        debug: Enable debug mode
        simple: Simple output mode
        fzf: fzf output mode
        rich: Rich output mode
        rich_1: Rich v1 output mode
        richo: Rich old output mode
        no_cookies: Disable cookies
        cookies_from_browser: Browser to extract cookies from
    
    Returns:
        Tuple of (output_format, cookies_from_browser)
    """
    from yt_fts.core.validation import validate_display_options
    
    # Enable debug mode if --debug flag was passed
    if debug:
        from yt_fts.utils.debug import enable_debug
        enable_debug()
    
    # Normalize legacy flags to output_format
    output_format = normalize_output_format(simple, fzf, rich, rich_1, richo)
    
    # Handle cookies: --no-cookies overrides --cookies-from-browser
    final_cookies = None if no_cookies else cookies_from_browser
    
    # Validate display options for conflicting combinations
    validate_display_options(
        simple=simple,
        fzf=fzf,
        rich=rich,
        richo=richo,
        rich_1=rich_1,
        json=False,
    )
    
    return output_format, final_cookies


def initialize_batch_logging(
    quota_daily: int,
    quota_conservative_pct: float,
    quota_aggressive_pct: float,
    videos_download_per_channel: int,
    delay: float,
    rich: bool,
    rich_1: bool,
) -> tuple:
    """Initialize batch logging and quota strategy.
    
    Args:
        quota_daily: Daily quota limit
        quota_conservative_pct: Conservative quota percentage
        quota_aggressive_pct: Aggressive quota percentage
        videos_download_per_channel: Videos per channel (0 = metadata only)
        delay: Delay between channels
        rich: Rich mode enabled
        rich_1: Rich v1 mode enabled
    
    Returns:
        Tuple of (quota_strategy, adjusted_delay)
    """
    def log_msg(tag: str, message: str, level: int = 20) -> None:
        timestamp = dt.now().strftime("%H:%M:%S")
        sys.stderr.write(f"[{timestamp}] [{tag}] {message}" + chr(10))
        sys.stderr.flush()
    
    # Quota strategy computation (silent)
    quota_strategy = initialize_quota_strategy(
        quota_daily, quota_conservative_pct, quota_aggressive_pct
    )
    # Quota status message (silent)
    
    # Metadata-only mode: no rate limit, only daily quota - use 0 delay by default
    adjusted_delay = delay
    if videos_download_per_channel == 0 and delay == 60.0:
        adjusted_delay = 0.0
    
    # Configure logging for clean Rich UI (suppress debug messages)
    import logging
    download_logger = logging.getLogger(
        "yt_fts.download.download_handler.DownloadHandler"
    )
    if rich or rich_1:
        download_logger.setLevel(logging.WARNING)
    else:
        download_logger.setLevel(logging.DEBUG)
    
    return quota_strategy, adjusted_delay


def setup_batch_rich_formatter(
    richo: bool,
    continue_on_error: bool,
    rich: bool,
    rich_1: bool,
    from_database_mode: bool,
) -> tuple:
    """Setup Rich formatter for batch download.
    
    Args:
        richo: Enable old Rich formatter
        continue_on_error: Continue on error setting
        rich: Rich mode enabled
        rich_1: Rich v1 mode enabled
        from_database_mode: Loading from database
    
    Returns:
        Tuple of (rich_formatter, rich_mode)
    """
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
            from yt_fts.core.status_display import StatusDisplay
            
            status = StatusDisplay(console)
            console.print("\nCurrent System Status:")
            status.display_minimal_status()
            console.print()
        except ImportError:
            console.print(
                "[dim]Status: Basic mode - install status_display for full info[/dim]"
            )
            console.print()
    
    return rich_formatter, rich_mode
