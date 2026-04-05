"""
Utility commands for yt-fts CLI.

This module contains utility commands for system maintenance,
health checking, configuration, and diagnostics.
Extracted from cli.py for better organization.
"""
from __future__ import annotations

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
    name="cleanup-invalid",
    help="""
    Remove channels marked as invalid (is_valid=0) from the database.
    
    Only removes channels that have NO videos or transcripts.
    Channels with existing data are kept but can be reviewed.
    Invalid channels are those that previously failed with 404/400 errors.
    """
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def cleanup_invalid(dry_run: bool = False, force: bool = False) -> None:
    """Remove invalid channels from the database (only those with no videos/transcripts)."""
    from yt_fts.db.infra import get_db_connection

    conn = get_db_connection()
    try:
        # Check if is_valid column exists
        column_exists = conn.execute("""
            SELECT COUNT(*) FROM pragma_table_info('Channels') WHERE name='is_valid'
        """).fetchone()

        if not column_exists or column_exists[0] == 0:
            console.print("[yellow]is_valid column not found. Run migrations first.[/yellow]")
            return

        # Get invalid channels
        invalid_channels = conn.execute("""
            SELECT channel_id, channel_name, channel_url
            FROM Channels
            WHERE is_valid = 0
            ORDER BY channel_name
        """).fetchall()

        if not invalid_channels:
            console.print("[green]No invalid channels found.[/green]")
            return

        console.print(f"Found {len(invalid_channels)} channels marked as invalid:")

        to_delete = []
        to_keep = []

        for channel_id, channel_name, channel_url in invalid_channels:
            # Check if channel has videos/transcripts
            video_count = conn.execute(
                "SELECT COUNT(*) FROM Videos WHERE channel_id = ?", (channel_id,)
            ).fetchone()[0]

            if video_count == 0:
                to_delete.append((channel_id, channel_name, channel_url))
                console.print(f"  [red]-[/red] {channel_name} ({channel_id}) - No videos, safe to remove")
            else:
                to_keep.append((channel_id, channel_name, video_count))
                console.print(f"  [green]+[/green] {channel_name} ({channel_id}) - Has {video_count} videos, keeping")

        console.print("")
        console.print("Summary:")
        console.print(f"  Would delete: {len(to_delete)} channels (no videos)")
        console.print(f"  Would keep: {len(to_keep)} channels (have videos)")

        if not dry_run and to_delete:
            console.print("")
            console.print(f"[bold]About to delete {len(to_delete)} channels...[/bold]")

            if not force:
                confirm = input("Continue? (Y/n): ")
                if confirm.lower() != "y":
                    console.print("Cancelled")
                    return

            for channel_id, channel_name, channel_url in to_delete:
                # Delete from SkippedChannels if present
                conn.execute("DELETE FROM SkippedChannels WHERE channel_url = ?", (channel_url,))
                # Delete from Channels
                conn.execute("DELETE FROM Channels WHERE channel_id = ?", (channel_id,))

            conn.commit()
            console.print(f"[green]Deleted {len(to_delete)} invalid channels[/green]")
        elif dry_run and to_delete:
            console.print("")
            console.print("[dim]Dry run complete. Use --force to actually delete.[/dim]")
    finally:
        conn.close()


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


@click.command(
    name="test-cookies",
    help="""
    Test if browser cookies are valid for YouTube authentication.

    This performs a functional test by attempting to access a members-only
    video using your browser cookies. If cookies are valid, the video becomes
    accessible. If cookies are expired or invalid, the video remains members-only.

    This is more reliable than just checking cookie file existence.

    Exit codes:
    - 0: Cookies are valid and working
    - 1: Cookies are invalid, expired, or not configured
    - 2: Error occurred during test
    """,
)
@click.option(
    "--cookies-from-browser",
    "-b",
    type=click.Choice(["firefox", "chrome"], case_sensitive=False),
    default=None,
    help="Browser to extract cookies from (firefox or chrome)",
)
@click.option(
    "--video-id",
    "-v",
    default=None,
    help="Specific video ID to test (must be a known members-only video)",
)
@click.pass_context
def test_cookies(ctx: click.Context, cookies_from_browser: str | None, video_id: str | None) -> None:
    """Test if browser cookies are valid for YouTube authentication."""
    from yt_fts.download.cookie_auth_tester import (
        test_cookie_authentication,
        CookieTestStatus,
    )

    console.print("[bold blue]🍪 Testing Cookie Authentication[/bold blue]")
    console.print()

    # Run the test
    result = test_cookie_authentication(
        video_id=video_id,
        cookies_from_browser=cookies_from_browser,
    )

    # Display results
    console.print(f"Test video: [cyan]{result.video_id}[/cyan]")
    console.print(f"Availability: [cyan]{result.availability or 'N/A'}[/cyan]")
    console.print()

    if result.status == CookieTestStatus.VALID:
        console.print("[green]✓ Cookies are VALID and working![/green]")
        console.print(f"  {result.message}")
        return  # Success - default exit code 0
    elif result.status == CookieTestStatus.INVALID:
        console.print("[red]✗ Cookies are INVALID or expired[/red]")
        console.print(f"  {result.message}")
        console.print()
        console.print("[bold]To fix:[/bold]")
        console.print("  1. Log into YouTube in your browser")
        console.print("  2. Verify you're still logged in")
        console.print("  3. Try re-running this test")
        ctx.exit(1)
    elif result.status == CookieTestStatus.NO_TEST_VIDEO:
        console.print("[yellow]⚠ No cookies configured[/yellow]")
        console.print(f"  {result.message}")
        console.print()
        console.print("[bold]To enable cookies:[/bold]")
        console.print("  Use: yt-fts test-cookies --cookies-from-browser firefox")
        ctx.exit(1)
    else:  # ERROR
        console.print("[red]✗ Cookie test failed with error[/red]")
        console.print(f"  {result.message}")
        ctx.exit(2)


# List of all utility commands that can be registered
UTILITY_COMMANDS = [
    health,
    diagnose,
    delete,
    config,
    status,
    reset_quota,
    test_cookies,
]