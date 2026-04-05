"""
Display setup and configuration for batch download operations.

Extracted from batch_download for better modularity.
"""

from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from typing import Literal

from yt_fts.utils.rich_console import get_console

console = get_console()
@dataclass
class DisplaySetup:
    """Configuration for display/output during batch download."""
    rich_mode: Literal["new", "old", None] | None
    rich_formatter: object | None
    quiet_mode: bool
    simple: bool = False
    fzf: bool = False

    def is_rich_enabled(self) -> bool:
        """Check if any Rich mode is enabled."""
        return self.rich_mode is not None

    def is_simple_mode(self) -> bool:
        """Check if simple/fzf mode is enabled."""
        return self.simple or self.fzf


def setup_display_logging(rich_mode: Literal["new", "old", None] | None) -> None:
    """Configure logging for clean Rich UI.

    Args:
        rich_mode: The Rich mode being used
    """
    download_logger = logging.getLogger(
        "yt_fts.download.download_handler.DownloadHandler"
    )

    if rich_mode == "new":
        # Suppress DEBUG/INFO logging for clean Rich UI
        download_logger.setLevel(logging.WARNING)
    else:
        # Default logging level for standard UI
        download_logger.setLevel(logging.DEBUG)


def setup_rich_formatter(
    richo: bool,
    continue_on_error: bool,
) -> object | None:
    """Initialize Rich formatter if --richo flag is used.

    Args:
        richo: Whether to use old Rich formatter
        continue_on_error: Whether to continue on errors (affects verbosity)

    Returns:
        Rich formatter object or None if not available
    """
    if not richo:
        return None

    try:
        from yt_fts.ui.rich_formatter import create_rich_formatter

        rich_formatter = create_rich_formatter(verbose=continue_on_error)
        rich_formatter.print_main_header("YouTube Batch Downloader")
        return rich_formatter

    except ImportError:
        console.print(
            "[yellow]Warning: Rich formatter not available, using basic output[/yellow]"
        )
        return None


def determine_rich_mode(
    rich: bool,
    rich_1: bool,
    richo: bool,
) -> Literal["new", "old", None] | None:
    """Determine which Rich mode to use.

    Args:
        rich: Use new Rich layout
        rich_1: Alias for rich (new layout)
        richo: Use old Rich formatter

    Returns:
        "new", "old", or None
    """
    if rich_1 or rich:
        return "new"
    if richo:
        return "old"
    return None


def should_auto_enable_rich(simple: bool, fzf: bool) -> bool:
    """Decide whether to enable Rich layout automatically."""
    if simple or fzf:
        return False
    if os.getenv("YT_FTS_DISABLE_RICH_AUTO") == "1":
        return False
    return bool(console.is_terminal and console.is_interactive)


def setup_display_mode(
    simple: bool,
    fzf: bool,
    rich: bool,
    rich_1: bool,
    richo: bool,
    continue_on_error: bool,
) -> DisplaySetup:
    """Set up display mode for batch download.

    Args:
        simple: Enable simple output mode
        fzf: Enable fzf output mode
        rich: Enable new Rich layout
        rich_1: Alias for rich (new layout)
        richo: Enable old Rich formatter
        continue_on_error: Affects Rich verbosity

    Returns:
        DisplaySetup configuration object
    """
    # Determine Rich mode
    rich_mode = determine_rich_mode(rich, rich_1, richo)
    if rich_mode is None and should_auto_enable_rich(simple, fzf):
        rich_mode = "new"

    # Setup Rich formatter
    rich_formatter = setup_rich_formatter(richo, continue_on_error)

    # Setup logging
    setup_display_logging(rich_mode)

    # Print header
    if rich_formatter and not is_quiet_mode():
        # Rich formatter already printed header
        pass
    elif richo:
        # Old Rich formatter
        pass
    else:
        console.print("[bold blue]YouTube Batch Downloader for yt-fts[/bold blue]")

    # Show status for non-Rich modes
    if rich_mode is None:
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

    # Check quiet mode
    quiet_mode = os.getenv("YT_FTS_QUIET_MODE") == "1"

    return DisplaySetup(
        rich_mode=rich_mode,
        rich_formatter=rich_formatter,
        quiet_mode=quiet_mode,
        simple=simple,
        fzf=fzf,
    )


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled."""
    return os.getenv("YT_FTS_QUIET_MODE") == "1"


def show_system_status() -> None:
    """Show current system status."""
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


def validate_display_options(
    simple: bool,
    fzf: bool,
    rich: bool,
    richo: bool,
    rich_1: bool,
    json: bool = False,
) -> None:
    """Validate display options for conflicting combinations.

    Args:
        simple: Simple output mode
        fzf: Fzf output mode
        rich: Rich output mode (new)
        richo: Rich output mode (old)
        rich_1: Rich output mode (new, alias)
        json: JSON output mode

    Raises:
        ValueError: If conflicting options are specified
    """
    enabled = [
        name for name, value in [
            ("simple", simple),
            ("fzf", fzf),
            ("rich", rich),
            ("richo", richo),
            ("rich_1", rich_1),
            ("json", json),
        ] if value
    ]

    if len(enabled) > 1:
        msg = (
            f"Conflicting display options: {', '.join(enabled)}. "
            "Only one display mode can be enabled at a time."
        )
        raise ValueError(
            msg
        )
