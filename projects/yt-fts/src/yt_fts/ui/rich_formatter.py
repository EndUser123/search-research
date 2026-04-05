"""
Enhanced Rich formatter for YouTube Full Text Search CLI.
Production-ready implementation from rich-cli-code.md documentation.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from rich.text import Text


class RichYouTubeFormatter:
    """Enhanced formatter for YouTube Full Text Search CLI output."""

    # Consistent color theme
    COLOR_SUCCESS = "green"
    COLOR_ERROR = "red"
    COLOR_WARNING = "yellow"
    COLOR_INFO = "cyan"
    COLOR_MUTED = "dim"
    COLOR_SECTION = "bold cyan"
    COLOR_HIGHLIGHT = "magenta"

    def __init__(self, verbose: bool = False, enable_unicode: bool = True):
        """Initialize the RichYouTubeFormatter with console and tracking state.

        Args:
            verbose: Whether to enable verbose output with additional details.
            enable_unicode: Whether to enable unicode characters in output.

        Attributes:
            verbose: Flag for verbose output mode.
            enable_unicode: Flag for unicode character support.
            error_log: Dictionary tracking deduplicated error messages and counts.
            start_time: Timestamp when the formatter was initialized.
            download_progress: Rich Progress object for download operations.
            resolution_progress: Rich Progress object for channel resolution.
            console: Rich Console instance configured for Windows compatibility.
        """
        self.verbose = verbose
        self.enable_unicode = enable_unicode
        self.error_log: dict[str, int] = {}
        self.start_time = datetime.now(timezone.utc)
        self.download_progress: Progress | None = None
        self.resolution_progress: Progress | None = None

        # Initialize console with optimized settings for Windows
        try:
            self.console = Console(
                force_terminal=False,
                width=120,
                record=False,
                legacy_windows=False,  # Try modern mode first
                file=sys.stdout
            )
        except (OSError, ValueError, TypeError):
            # Fallback to safe mode for Windows
            self.console = Console(
                force_terminal=False,
                width=80,  # Conservative width
                record=False,
                legacy_windows=True,
                file=sys.stdout
            )

    # ========================================================================
    # SECTION: Headers & Phase Management
    # ========================================================================

    def print_main_header(self, title: str = "YouTube Full Text Search") -> None:
        """Print the main application header.

        Args:
            title: The title text to display in the header.
        """
        self.console.print("\n")
        self.console.print(
            f"🚀 {title}",
            style="bold cyan",
            justify="center"
        )
        self.console.print("─" * min(80, self.console.width), style="dim")

    def print_phase(self, phase_num: int, title: str, description: str | None = None) -> None:
        """Print a phase header with optional description.

        Args:
            phase_num: The phase number to display.
            title: The phase title.
            description: Optional description text (only shown in verbose mode).
        """
        self.console.print(f"\n[{self.COLOR_SECTION}]Phase {phase_num}: {title}[/{self.COLOR_SECTION}]")
        if description and self.verbose:
            self.console.print(f"[{self.COLOR_MUTED}]{description}[/{self.COLOR_MUTED}]")

    # ========================================================================
    # SECTION: Configuration Display
    # ========================================================================

    def print_config_section(self, title: str, config: dict[str, Any], compact: bool = False) -> None:
        """Print configuration in a clean, aligned table format.

        Args:
            title: The section title.
            config: Dictionary of configuration key-value pairs.
            compact: Whether to use compact padding.
        """
        self.console.print(f"\n[{self.COLOR_SECTION}]📋 {title}[/{self.COLOR_SECTION}]")

        table = Table(
            show_header=False,
            box=None,
            padding=(0, 2) if not compact else (0, 1),
            pad_edge=False
        )
        table.add_column(style=self.COLOR_MUTED, width=25)
        table.add_column()

        # Filter out None/empty values unless verbose
        items = [(k, v) for k, v in config.items() if v is not None]

        for key, value in items:
            table.add_row(f"• {key}:", str(value))

        self.console.print(table)

    def print_environment_status(self, env_file: str, status: bool = True) -> None:
        """Print environment variable loading status.

        Args:
            env_file: Path to the environment file.
            status: True if loading succeeded, False otherwise.
        """
        if status:
            self.console.print(
                f"✅ [{self.COLOR_SUCCESS}]Loaded environment variables from[{self.COLOR_SUCCESS}] [{self.COLOR_INFO}]{env_file}[/{self.COLOR_INFO}]"
            )
        else:
            self.console.print(
                f"❌ [{self.COLOR_ERROR}]Failed to load environment from[{self.COLOR_ERROR}] [{self.COLOR_INFO}]{env_file}[/{self.COLOR_INFO}]"
            )

    # ========================================================================
    # SECTION: Status Grids
    # ========================================================================

    def print_system_status(self, status_items: list[dict[str, Any]]) -> None:
        """Print a system status grid.

        Args:
            status_items: List of dicts with label, status, and details keys.
        """
        self.console.print(f"\n[{self.COLOR_SECTION}]📊 System Status[/{self.COLOR_SECTION}]")

        table = Table(
            show_header=True,
            header_style="bold white",
            box=ROUNDED,
            padding=(1, 2)
        )

        table.add_column("Component", style=self.COLOR_INFO, width=20)
        table.add_column("Status", style="bold", width=15)
        table.add_column("Details")

        for item in status_items:
            status_text = item.get("status", "Unknown")

            # Infer style from status emoji
            if "✅" in status_text or "Working" in status_text or "⚠️" in status_text or "partial" in status_text.lower():
                pass
            else:
                pass

            table.add_row(
                item.get("label", ""),
                status_text,
                item.get("details", "")
            )

        self.console.print(table)

    # ========================================================================
    # SECTION: Configuration Display
    # ========================================================================

    def _format_compact_config(self, config_items: list[dict[str, str]]) -> str:
        """Format configuration items in a compact, readable format.

        Args:
            config_items: List of dicts with setting and value keys.

        Returns:
            Formatted multi-line string with configuration items.
        """
        lines = []

        # Create key-value pairs from config items
        config_dict = {item["setting"]: item["value"] for item in config_items}

        # Format key configuration in a compact, aligned way
        if "Channels" in config_dict:
            lines.append(f"  📹 Channels: {config_dict['Channels']}")
        if "Jobs" in config_dict:
            lines.append(f"  ⚙️ Jobs: {config_dict['Jobs']}")
        if "Delay" in config_dict:
            lines.append(f"  ⏱️ Delay: {config_dict['Delay']}")
        if "Cookies" in config_dict:
            cookies = config_dict["Cookies"]
            cookie_icon = "✅" if cookies != "None" else "❌"
            lines.append(f"  🍪 Cookies: {cookies} {cookie_icon}")

        return "\n".join(lines)

    def print_deployment_config(self, title: str, config_items: list[dict[str, str]],
                               browser_info: list[str] | None = None, optimal_setup: list[str] | None = None) -> None:
        """Print deployment configuration in a clean, bullet list format."""
        # Clear separation header
        separator = "─" * 60
        self.console.print(f"[cyan]{separator}[/cyan]")

        # Clear application header
        header_text = Text("🚀 YOUTUBE BATCH DOWNLOADER", style="bold blue")
        self.console.print(header_text)
        self.console.print(f"[cyan]{separator}[/cyan]")
        self.console.print()

        # Simple clean bullet list - no borders, universal compatibility
        config_title = Text("⚙️ Configuration:", style="bold cyan")
        self.console.print(config_title)

        # Print each configuration item as a bullet
        for item in config_items:
            setting = item["setting"]
            value = item["value"]

            # Add appropriate emojis and formatting
            if setting == "Channels":
                self.console.print(f"  • 📹 Channels: {value}")
            elif setting == "Jobs":
                self.console.print(f"  • ⚙️ Jobs: {value}")
            elif setting == "Delay":
                self.console.print(f"  • ⏱️ Delay: {value}")
            elif setting == "Cookies":
                cookie_icon = "✅" if value != "None" else "❌"
                self.console.print(f"  • 🍪 Cookies: {value} {cookie_icon}")

        self.console.print()

        # Browser detection info
        if browser_info:
            self.console.print(f"🌐 Browsers: {', '.join(browser_info)}")
            if optimal_setup and "firefox" in browser_info:
                self.console.print("✅ Firefox optimal for cookies (34 vs 7 with Chrome)")

    # ========================================================================
    # SECTION: Browser & Cookie Management
    # ========================================================================

    def print_browser_detection(self, detected_browsers: list[str]) -> None:
        """Print detected browsers with optimal setup guidance.

        Args:
            detected_browsers: List of detected browser names.
        """
        self.console.print(f"\n[{self.COLOR_INFO}]🌐 Browsers detected:[/{self.COLOR_INFO}] {', '.join(detected_browsers)}")

        # Show optimal setup recommendations
        if "firefox" in [b.lower() for b in detected_browsers]:
            self.console.print(f"[{self.COLOR_SUCCESS}]✅ OPTIMAL SETUP: Firefox + RookiePy[/{self.COLOR_SUCCESS}]")
            self.console.print(f"  [{self.COLOR_MUTED}]• 34 cookies extracted vs 7 with Chrome[/{self.COLOR_MUTED}]")
            self.console.print(f"  [{self.COLOR_MUTED}]• Instant extraction (0.00s vs 6+ seconds)[/{self.COLOR_MUTED}]")
            self.console.print(f"  [{self.COLOR_MUTED}]• No admin rights required[/{self.COLOR_MUTED}]")

        if "chrome" in [b.lower() for b in detected_browsers]:
            self.console.print(f"[{self.COLOR_WARNING}]⚠️ Chrome detected - Firefox recommended for 5x better performance[/{self.COLOR_WARNING}]")

    def print_cookie_notice(self, browser: str) -> None:
        """Print browser-specific cookie warnings.

        Args:
            browser: Browser name (chrome or firefox).
        """
        notice_map = {
            "chrome": {
                "title": "⚠️ Chrome Cookie Notice",
                "points": [
                    "Chrome may have cookie decryption issues on Windows (DPAPI)",
                    "Download will work but may encounter rate limiting",
                    "Consider using Firefox for better compatibility"
                ],
                "style": self.COLOR_WARNING
            },
            "firefox": {
                "title": "✅ Firefox Cookies",
                "points": [
                    "Firefox cookies are natively supported on all platforms",
                    "Best choice for yt-dlp compatibility",
                    "RookiePy extracts 34 cookies vs 7 with Chrome"
                ],
                "style": self.COLOR_SUCCESS
            }
        }

        if browser.lower() not in notice_map:
            return

        info = notice_map[browser.lower()]
        content = f"[{info['style']}]{info['title']}[/{info['style']}]\n"
        for point in info["points"]:
            content += f"  → {point}\n"

        panel = Panel(
            content,
            border_style=str(info["style"]),
            padding=(1, 2),
            expand=False
        )
        self.console.print(panel)

    # ========================================================================
    # SECTION: Channel Resolution
    # ========================================================================

    def print_resolution_start(self, channel_count: int, worker_count: int) -> None:
        """Print channel resolution start message.

        Args:
            channel_count: Number of channels to resolve.
            worker_count: Number of parallel workers to use.
        """
        self.console.print(
            f"\n[{self.COLOR_INFO}]🔍 Resolving {channel_count} channels "
            f"(workers: {worker_count})...[/{self.COLOR_INFO}]"
        )
        if self.verbose:
            self.console.print(
                f"[{self.COLOR_MUTED}]Using conservative threading to avoid rate limits[/{self.COLOR_MUTED}]"
            )

    def create_resolution_progress(self, total_channels: int) -> Any:
        """Create a progress bar for channel resolution.

        Args:
            total_channels: Total number of channels to resolve.

        Returns:
            The Rich task ID for updating progress.
        """
        self.resolution_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )

        task = self.resolution_progress.add_task(
            "Resolving channels...",
            total=total_channels
        )

        self.resolution_live = Live(
            self.resolution_progress,
            refresh_per_second=10,
            console=self.console
        )
        self.resolution_live.start()

        return task

    def update_resolution_progress(self, task_id: Any, advance: int = 1, description: str | None = None) -> None:
        """Update resolution progress.

        Args:
            task_id: The Rich task ID returned by create_resolution_progress.
            advance: Number of steps to advance the progress bar.
            description: Optional new description for the task.
        """
        if self.resolution_progress and description:
            self.resolution_progress.update(task_id, advance=advance, description=description)
        elif self.resolution_progress:
            self.resolution_progress.advance(task_id, advance)

    def finish_resolution_progress(self) -> None:
        """Finish resolution progress display."""
        if hasattr(self, "resolution_live"):
            self.resolution_live.stop()

    def print_channel_resolved(self, index: int, total: int, channel: str, resolved_url: str | None = None, duration: float | None = None) -> None:
        """Print individual channel resolution with progress.

        Args:
            index: Current channel index (1-based).
            total: Total number of channels.
            channel: Original channel identifier.
            resolved_url: Resolved URL (if different from input).
            duration: Optional resolution duration in seconds.
        """
        duration_str = f" ({duration:.1f}s)" if duration else ""

        # Create display name
        if resolved_url and resolved_url != channel:
            if "@" in resolved_url:
                handle = resolved_url.split("@")[-1].split("/")[0]
                channel_display = f"{channel} → @{handle}"
            else:
                channel_display = f"{channel} → {resolved_url[:40]}..."
        else:
            channel_display = channel.replace("https://www.youtube.com/", "")

        self.console.print(f"  ✓ [{index}/{total}] {channel_display}{duration_str}")

    def print_resolution_complete(self, successful: int, failed: int, total: int, duration: str | None = None) -> None:
        """Print resolution completion summary.

        Args:
            successful: Number of successfully resolved channels.
            failed: Number of failed resolutions.
            total: Total number of channels.
            duration: Optional duration string.
        """
        self.console.print(f"\n✅ [{self.COLOR_SUCCESS}]Channel Resolution Complete[{self.COLOR_SUCCESS}]")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style=self.COLOR_MUTED, width=15)
        table.add_column(style="bold")

        table.add_row("✓ Successful:", f"{successful}/{total}")
        if failed > 0:
            table.add_row("✗ Failed:", f"{failed}/{total}")
        if duration:
            table.add_row("⏱️  Duration:", duration)

        self.console.print(table)

    # ========================================================================
    # SECTION: Download Progress
    # ========================================================================

    def create_download_progress(self, task_description: str = "Downloading") -> Progress:
        """Create a download progress bar.

        Args:
            task_description: Description text for the progress bar.

        Returns:
            The Rich Progress object for adding tasks.
        """
        self.download_progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{task_description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )

        self.download_live = Live(
            self.download_progress,
            refresh_per_second=4,
            console=self.console
        )
        self.download_live.start()

        return self.download_progress

    def add_download_task(self, task_id: str, total: int, description: str | None = None) -> Any:
        """Add a download task to progress.

        Args:
            task_id: Identifier for the task.
            total: Total items to process for this task.
            description: Optional task description.

        Returns:
            The Rich task ID or None if progress is not initialized.
        """
        if self.download_progress:
            return self.download_progress.add_task(
                description or f"Downloading {task_id}",
                total=total
            )
        return None

    def update_download_task(self, task_id: Any, advance: int = 1) -> None:
        """Update download task progress.

        Args:
            task_id: The Rich task ID returned by add_download_task.
            advance: Number of steps to advance the progress bar.
        """
        if self.download_progress:
            self.download_progress.advance(task_id, advance)

    def finish_download_progress(self) -> None:
        """Finish download progress display."""
        if hasattr(self, "download_live"):
            self.download_live.stop()

    # ========================================================================
    # SECTION: Error Management
    # ========================================================================

    def log_error(self, error_message: str, count: int = 1) -> None:
        """Log an error for later deduplication.

        Args:
            error_message: The error message to log.
            count: Number of occurrences to add (default 1).
        """
        normalized = error_message.strip()
        if normalized in self.error_log:
            self.error_log[normalized] += count
        else:
            self.error_log[normalized] = count

    def print_error_summary(self) -> None:
        """Print deduplicated error summary."""
        if not self.error_log:
            return

        self.console.print(f"\n⚠️ [{self.COLOR_WARNING}]Issues Encountered During Processing[{self.COLOR_WARNING}]")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Count", style="bold red", width=8)
        table.add_column("Error", style=self.COLOR_ERROR)

        for error, count in sorted(self.error_log.items(), key=lambda x: x[1], reverse=True):
            table.add_row(f"×{count}", error[:100] + "..." if len(error) > 100 else error)

        self.console.print(table)

    # ========================================================================
    # SECTION: Completion & Summary
    # ========================================================================

    def print_completion_summary(self, total_channels: int, successful_downloads: int, total_videos: int,
                              total_subtitles: int, duration: str | None = None) -> None:
        """Print final completion summary."""
        self.console.print(f"\n🎉 [{self.COLOR_SUCCESS}]Download Complete![/{self.COLOR_SUCCESS}]")

        # Main results table
        results_table = Table(
            title="Download Results",
            show_header=True,
            header_style="bold white",
            box=ROUNDED,
            padding=(1, 2)
        )

        results_table.add_column("Metric", style=self.COLOR_INFO, width=20)
        results_table.add_column("Value", style="bold", justify="right")
        results_table.add_column("Rate", style=self.COLOR_HIGHLIGHT)

        # Calculate rates
        success_rate = (successful_downloads / total_channels * 100) if total_channels > 0 else 0

        results_table.add_row("Channels Processed", f"{total_channels}")
        results_table.add_row("Successful Downloads", f"{successful_downloads}")
        results_table.add_row("Videos Downloaded", f"{total_videos:,}")
        results_table.add_row("Subtitles Extracted", f"{total_subtitles:,}")
        results_table.add_row("Success Rate", f"{success_rate:.1f}%", f"{success_rate:.0f}%")

        if duration:
            results_table.add_row("Total Duration", duration)

        self.console.print(results_table)

    def print_session_summary(self) -> None:
        """Print overall session summary."""
        total_time = datetime.now(timezone.utc) - self.start_time

        self.console.print(f"\n[{self.COLOR_SECTION}]Session Summary[/{self.COLOR_SECTION}]")

        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column(style=self.COLOR_MUTED, width=20)
        summary_table.add_column()

        summary_table.add_row("Session Duration:", f"{total_time}")
        summary_table.add_row("Start Time:", self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        summary_table.add_row("End Time:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

        if self.error_log:
            total_errors = sum(self.error_log.values())
            summary_table.add_row("Total Issues:", f"{total_errors}")

        self.console.print(summary_table)


# Convenience function for easy import
def create_rich_formatter(verbose: bool = False, enable_unicode: bool = True) -> RichYouTubeFormatter:
    """Create a RichYouTubeFormatter instance with Windows compatibility."""
    return RichYouTubeFormatter(verbose=verbose, enable_unicode=enable_unicode)
