"""
Centralized display configuration module for yt-fts.

Provides a unified way to manage display modes and settings across
deploy.ps1, cli.py, and parallel_processor.py.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DisplayMode(str, Enum):
    """
    Display mode enum for yt-fts output.

    Modes:
        FZF: Tab-separated output for fzf/awk pipelining
        RICH: Rich progress bars and tables (requires rich library)
        SIMPLE: Simple line-by-line text output
        VANILLA: Default straight logs without special formatting
        JSON: JSON output for programmatic consumption
    """

    FZF = "fzf"
    RICH = "rich"
    SIMPLE = "simple"
    VANILLA = "vanilla"
    JSON = "json"


@dataclass
class DisplayConfig:
    """
    Centralized display configuration.

    Attributes:
        mode: The primary display mode
        rich_display_mode: For RICH mode, "progress" for bars or "table" for live data
        use_rich_progress: Enable Rich progress display
        use_fzf: Enable FZF mode (tab-separated output)
        use_simple: Enable simple line-by-line output
        console: Optional Rich console instance
    """

    mode: DisplayMode = DisplayMode.VANILLA
    rich_display_mode: str = "progress"  # "progress" or "table"
    use_rich_progress: bool = False
    use_fzf: bool = False
    use_simple: bool = False
    console: Any = None  # Rich Console, optional to avoid hard dependency

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.mode == DisplayMode.RICH and self.rich_display_mode not in ("progress", "table"):
            self.rich_display_mode = "progress"


def validate_display_mode(
    use_rich_progress: bool = False,
    use_fzf: bool = False,
    use_simple: bool = False,
    rich_display: str = "progress",
) -> tuple[DisplayMode, list[str]]:
    """
    Validate display mode flags and detect conflicting options.

    Args:
        use_rich_progress: Rich progress mode enabled
        use_fzf: FZF mode enabled
        use_simple: Simple mode enabled
        rich_display: Rich display mode ("progress" or "table")

    Returns:
        Tuple of (DisplayMode, list of warnings/errors)

    Raises:
        ValueError: If conflicting display modes are specified
    """
    errors = []
    warnings = []

    # Count enabled modes
    enabled_modes = sum([
        use_rich_progress,
        use_fzf,
        use_simple,
    ])

    if enabled_modes > 1:
        conflicts = []
        if use_rich_progress:
            conflicts.append("rich-progress")
        if use_fzf:
            conflicts.append("fzf")
        if use_simple:
            conflicts.append("simple")
        errors.append(
            f"Conflicting display modes: {', '.join(conflicts)}. "
            "Only one display mode can be enabled at a time."
        )

    if errors:
        raise ValueError("\n".join(errors))

    # Determine the display mode
    if use_fzf:
        mode = DisplayMode.FZF
    elif use_rich_progress:
        mode = DisplayMode.RICH
    elif use_simple:
        mode = DisplayMode.SIMPLE
    else:
        mode = DisplayMode.VANILLA

    # Validate rich_display option
    if mode == DisplayMode.RICH and rich_display not in ("progress", "table"):
        warnings.append(
            f"Invalid rich-display mode '{rich_display}'. Using 'progress'."
        )
        rich_display = "progress"

    return mode, warnings


def get_display_mode(
    use_rich_progress: bool = False,
    use_fzf: bool = False,
    use_simple: bool = False,
    rich_display: str = "progress",
) -> DisplayMode:
    """
    Determine the display mode from flags.

    This is a convenience wrapper around validate_display_mode
    that returns only the mode, ignoring warnings.

    Args:
        use_rich_progress: Rich progress mode enabled
        use_fzf: FZF mode enabled
        use_simple: Simple mode enabled
        rich_display: Rich display mode ("progress" or "table")

    Returns:
        The determined DisplayMode

    Raises:
        ValueError: If conflicting display modes are specified
    """
    mode, _warnings = validate_display_mode(
        use_rich_progress=use_rich_progress,
        use_fzf=use_fzf,
        use_simple=use_simple,
        rich_display=rich_display,
    )
    return mode


def create_display_config(
    use_rich_progress: bool = False,
    use_fzf: bool = False,
    use_simple: bool = False,
    rich_display: str = "progress",
    console: Any = None,
) -> DisplayConfig:
    """
    Create a DisplayConfig from flag values.

    Args:
        use_rich_progress: Rich progress mode enabled
        use_fzf: FZF mode enabled
        use_simple: Simple mode enabled
        rich_display: Rich display mode ("progress" or "table")
        console: Optional Rich console instance

    Returns:
        A configured DisplayConfig instance

    Raises:
        ValueError: If conflicting display modes are specified
    """
    mode, warnings = validate_display_mode(
        use_rich_progress=use_rich_progress,
        use_fzf=use_fzf,
        use_simple=use_simple,
        rich_display=rich_display,
    )

    # Print warnings if any
    for warning in warnings:
        print(f"[WARNING] {warning}")

    return DisplayConfig(
        mode=mode,
        rich_display_mode=rich_display,
        use_rich_progress=use_rich_progress,
        use_fzf=use_fzf,
        use_simple=use_simple,
        console=console,
    )
