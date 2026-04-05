"""
Health check module for yt-fts database.

Provides functions to verify database integrity, check table accessibility,
and aggregate health status for CLI reporting.
"""

import os
import sqlite3

from rich.console import Console
from rich.table import Table

from yt_fts.utils.config import get_config_path, make_config_dir

# Tables to check in the health status
_EXPECTED_TABLES = ["Channels", "Videos", "Subtitles", "SearchHistory", "SavedQueries"]


def _get_db_path_without_creating() -> str | None:
    """Get database path WITHOUT auto-creating it if it doesn't exist.

    This is important for health checks - we want to detect missing databases,
    not create them. Unlike get_db_path() which auto-creates, this returns
    the path where the database *should* be, without touching the filesystem.

    Returns:
        The path where the database should be, or None if it can't be determined.
    """
    # First check if a custom path is set via environment variable
    custom_db_path = os.getenv("YT_FTS_DB_PATH")
    if custom_db_path:
        return custom_db_path

    # Default behavior: use config directory
    config_path = get_config_path()
    if config_path is None:
        config_path = make_config_dir()
        if config_path is None:
            # Fall back to current directory
            return "subtitles.db"

    # Build path in config directory
    from pathlib import Path

    db_path = Path(config_path) / "subtitles.db"
    return str(db_path)


def check_database_exists() -> bool:
    """Check if the database file exists at the expected path.

    Returns:
        True if the database file exists, False otherwise.
    """
    db_path = _get_db_path_without_creating()
    if db_path is None:
        return False
    return os.path.exists(db_path)


def check_database_integrity() -> bool:
    """Check database integrity using PRAGMA integrity_check.

    Returns:
        True if the database passes integrity check, False otherwise.
        Returns False if the database file doesn't exist or is corrupted.
    """
    if not check_database_exists():
        return False

    db_path = _get_db_path_without_creating()
    if db_path is None:
        return False

    try:
        # Use context manager for automatic cleanup
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

        # integrity_check returns "ok" for a healthy database
        return result and result[0] == "ok"
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return False


def check_table_readable(table_name: str) -> bool:
    """Check if a specific table is readable.

    Attempts to query the table to verify it's accessible.
    Handles missing tables gracefully by returning False.

    Args:
        table_name: Name of the table to check.

    Returns:
        True if the table exists and is readable, False otherwise.
    """
    if not check_database_exists():
        return False

    db_path = _get_db_path_without_creating()
    if db_path is None:
        return False

    try:
        # Use context manager for automatic cleanup
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Try to query the table - this will fail if table doesn't exist
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            cursor.fetchone()

        return True
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return False


def get_health_status() -> dict:
    """Get comprehensive health status of the database.

    Aggregates all health checks and determines the overall status
    and appropriate exit code.

    Returns:
        A dictionary containing:
            - status: "healthy", "warning", or "error"
            - exit_code: 0 (healthy), 1 (warning), 2 (error)
            - database_exists: bool
            - database_integrity_ok: bool
            - table_statuses: dict mapping table names to bool
    """
    # Check basic database status
    db_exists = check_database_exists()
    integrity_ok = check_database_integrity()

    # Check each table
    table_statuses = {}
    for table in _EXPECTED_TABLES:
        table_statuses[table] = check_table_readable(table)

    # Determine overall status and exit code
    # Exit code 2: error - missing DB or corruption
    if not db_exists or not integrity_ok:
        return {
            "status": "error",
            "exit_code": 2,
            "database_exists": db_exists,
            "database_integrity_ok": integrity_ok,
            "table_statuses": table_statuses,
        }

    # Exit code 1: warning - some tables are not readable
    tables_ok = all(table_statuses.values())
    if not tables_ok:
        return {
            "status": "warning",
            "exit_code": 1,
            "database_exists": db_exists,
            "database_integrity_ok": integrity_ok,
            "table_statuses": table_statuses,
        }

    # Exit code 0: healthy
    return {
        "status": "healthy",
        "exit_code": 0,
        "database_exists": db_exists,
        "database_integrity_ok": integrity_ok,
        "table_statuses": table_statuses,
    }


def format_health_for_display(health_status: dict) -> Table:
    """Format health status for display in a Rich table.

    Creates a Rich Table with status indicators showing the health
    of the database and its tables.

    Args:
        health_status: Dictionary from get_health_status().

    Returns:
        A rich.table.Table instance with formatted health information.
    """
    from yt_fts.display.rich_table_builder import RichTableBuilder

    # Use RichTableBuilder for cleaner table creation
    builder = RichTableBuilder(title="Database Health Status", header_style="bold magenta")
    builder.add_column("Component", style="cyan")
    builder.add_column("Status", style="bold")

    # Database existence
    db_exists = health_status.get("database_exists", False)
    db_status = "[green]OK[/green]" if db_exists else "[red]MISSING[/red]"
    builder.add_row("Database File", db_status)

    # Database integrity
    integrity_ok = health_status.get("database_integrity_ok", False)
    integrity_status = "[green]OK[/green]" if integrity_ok else "[red]CORRUPTED[/red]"
    builder.add_row("Database Integrity", integrity_status)

    # Table statuses
    builder.add_empty_row()
    builder.add_row("[bold]Tables[/bold]", "")

    table_statuses = health_status.get("table_statuses", {})
    for table_name, is_ok in table_statuses.items():
        status = "[green]OK[/green]" if is_ok else "[red]ERROR[/red]"
        builder.add_row(table_name, status)

    # Overall status
    builder.add_empty_row()
    status = health_status.get("status", "unknown")
    exit_code = health_status.get("exit_code", 2)

    if status == "healthy":
        overall_status = "[green]HEALTHY[/green]"
    elif status == "warning":
        overall_status = "[yellow]WARNING[/yellow]"
    else:
        overall_status = "[red]ERROR[/red]"

    builder.add_row("[bold]Overall[/bold]", overall_status)
    builder.add_row("Exit Code", str(exit_code))

    return builder.build()


def print_health_status(console: Console | None = None) -> int:
    """Print health status to console and return exit code.

    This is the main entry point for the health CLI command.

    Args:
        console: Rich console instance. If None, creates a new one.

    Returns:
        Exit code (0=healthy, 1=warning, 2=error).
    """
    if console is None:
        console = Console()

    health_status = get_health_status()
    table = format_health_for_display(health_status)
    console.print(table)

    return health_status["exit_code"]
