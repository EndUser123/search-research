"""
Utility commands for yt-fts CLI.

This module contains utility commands for system maintenance,
health checking, configuration, and diagnostics.
Extracted from cli.py for better organization.
"""

from datetime import datetime, timedelta, timezone
from io import StringIO

import click
from rich.console import Console

from yt_fts.utils.config import get_config_path, get_db_path
from yt_fts.utils.rich_console import get_console

from .database import (
    delete_channel,
    get_channel_id_from_input,
    get_channel_name_from_id,
)

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


@click.command(
    name="health",
    help="""
    Check database health and integrity.

    Verifies:
    - Database file existence
    - Database integrity (PRAGMA integrity_check)
    - Individual table accessibility

    Exit codes:
    - 0: All checks passed (healthy)
    - 1: Some warnings (e.g., partial table issues)
    - 2: Errors (missing DB, corruption)
    """,
)
@click.pass_context
def health(ctx: click.Context) -> None:
    """Check database health and display status."""
    from .health import format_health_for_display, get_health_status

    health_status = get_health_status()
    table = format_health_for_display(health_status)

    # Use string IO to capture Rich output
    string_io = StringIO()
    table_console = Console(file=string_io, force_terminal=False)
    table_console.print(table)

    # Output via Click echo so it's captured by CliRunner
    click.echo(string_io.getvalue(), nl=False)

    exit_code = health_status["exit_code"]
    if exit_code != 0:
        ctx.exit(exit_code)


@click.command(
    name="diagnose",
    help="""
    Diagnose connection issues and test YouTube access with detailed troubleshooting.

    Comprehensive testing includes:
    YouTube API connectivity and accessibility
    Cookie functionality and authentication status
    Rate limiting detection and recommendations
    Network connectivity and DNS resolution
    Browser compatibility testing
    Download speed and performance metrics

    Provides specific recommendations for:
    Cookie extraction and configuration
    Rate limit avoidance strategies
    Network and firewall issues
    Browser-specific problems
    """,
)
@click.option("-u", "--test-url", default="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
@click.option(
    "--cookies-from-browser",
    default=None,
    help="Browser to extract cookies from (recommended: firefox, chrome). Helps avoid rate limits.",
)
@click.option(
    "-j",
    "--jobs",
    type=int,
    default=2,
    help="Number of parallel download jobs to test with",
)
def diagnose(test_url: str, cookies_from_browser: str | None, jobs: int) -> None:
    """Diagnose connection issues and test YouTube access."""
    from yt_fts.download.download_handler import DownloadHandler

    download_handler = DownloadHandler(
        number_of_jobs=jobs, cookies_from_browser=cookies_from_browser
    )

    download_handler.diagnose_403_errors(test_url)
    # Success - let Click handle naturally


@click.command(
    name="delete",
    help="""
    Delete a channel and all its data.

    You must provide the name or the id of the channel you want to delete as an argument.
    The command will ask for confirmation before performing the deletion.
    """,
)
@click.option(
    "-c",
    "--channel",
    default=None,
    required=True,
    help="The name or id of the channel to delete",
)
def delete(channel: str) -> None:
    """Delete a channel and all its data."""
    channel_id = get_channel_id_from_input(channel)
    channel_name = get_channel_name_from_id(channel_id)
    channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

    console.print(f'Deleting channel [bold]"{channel_name}"[/bold]: {channel_url}')
    console.print(
        "[bold]Are you sure you want to delete this channel and all its data?[/bold]"
    )
    confirm = input("(Y/n): ")

    if confirm.lower() == "y":
        delete_channel(channel_id)
        console.print(f'Deleted channel "{channel_name}": "{channel_url}"')
    else:
        print("Exiting")

    # Success - let Click handle naturally


@click.command(
    name="config",
    help="""
    Show configuration and path information.

    Displays:
    Database location and path information
    Configuration directory and settings files
    Environment variable status
    System integration details
    Cache and temporary file locations

    Useful for:
    Troubleshooting configuration issues
    Understanding file locations
    Verifying environment setup
    System administration and maintenance
    """,
)
def config() -> None:
    """Show configuration and path information."""
    db_path = get_db_path()
    config_path = get_config_path()

    console.print(f"Config directory: {config_path}")
    console.print(f"Database path: {db_path}")
    # Success - let Click handle naturally


@click.command(
    name="status",
    help="""
    Show comprehensive system status with detailed monitoring capabilities.

    Status monitoring includes:
    Database statistics and health information
    Browser cookie functionality and testing
    Channel library overview and statistics
    System performance and resource usage
    Download and search operation metrics

    Display modes:
    Basic: Essential system information at a glance
    Detailed (--detailed): Comprehensive system analysis
    Cookie check (--cookie-check): Test browser cookie extraction

    Use cases:
    System health monitoring and troubleshooting
    Performance analysis and optimization
    Configuration verification and testing
    Operation status and progress tracking
    """,
)
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Show detailed status information including performance metrics and system analysis",
)
@click.option(
    "--cookie-check",
    "-c",
    is_flag=True,
    help="Check and test browser cookie extraction functionality",
)
def status(detailed: bool, cookie_check: bool) -> None:
    """Show comprehensive status of yt-fts system."""
    try:
        from .status_display import StatusDisplay, show_status

        status = StatusDisplay()

        if cookie_check:
            from .cookie_extractor import auto_extract_cookies

            console = status.console
            console.print("[bold blue]🍪 Testing cookie extraction...[/bold blue]")

            cookie_file = auto_extract_cookies("firefox", console)
            if cookie_file:
                console.print("[green]Cookie extraction successful![/green]")
            else:
                cookie_file = auto_extract_cookies("chrome", console)
                if cookie_file:
                    console.print(
                        "[green]Chrome cookie extraction successful![/green]"
                    )
                else:
                    console.print(
                        "[red]❌ Cookie extraction failed for both browsers[/red]"
                    )

        # Use optimized status display
        show_status(detailed=detailed, config=False)

    except ImportError:
        print("[dim]Status: Basic mode - install status_display for full info[/dim]")


@click.command(
    name="reset-quota",
    help="""
    Reset YouTube API quota tracking to zero.

    Use this command when:
    You've switched to new API keys
    You want to reset local quota tracking
    You've switched to new API keys
    The tracking has become desynchronized from reality

    Note: This only resets local tracking, not the actual Google API quota.
    The Google API quota resets at midnight Pacific Time regardless of local time.
    """,
)
def reset_quota() -> None:
    """Reset YouTube API quota tracking to zero."""
    from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill
    from yt_fts.utils.rich_console import get_console

    console = get_console()
    console.print("[bold yellow]🔄 Resetting YouTube API Quota Tracking[/bold yellow]")
    console.print("[dim]This resets local tracking only. Google's API quota resets at midnight PT.[/dim]")
    console.print()

    # Show current quota before reset
    quota_info = YouTubeAPIBackfill.get_global_quota_info()
    console.print(f"Current tracked quota: {quota_info['used']:,} used")

    # Reset the quota tracking
    YouTubeAPIBackfill.reset_quota_tracking()

    console.print()
    console.print("[green]✓ Quota tracking reset to 0[/green]")
    console.print()
    console.print("[bold]Note:[/bold] If you still see 'quotaExceeded' errors:")
    console.print("  Wait until midnight Pacific Time for Google's quota reset")
    console.print("  Or add more API keys to your configuration")
    console.print("  Current PT time: " + datetime.now(timezone(timedelta(hours=-8))).strftime("%Y-%m-%d %H:%M:%S %Z"))
    return 0


# List of all utility commands that can be registered
UTILITY_COMMANDS = [
    health,
    diagnose,
    delete,
    config,
    status,
    reset_quota,
]
