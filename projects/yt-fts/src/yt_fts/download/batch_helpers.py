"""
Helper functions for batch download operations.

Extracted from batch_download to reduce complexity and improve testability.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import date as date_module
from typing import Any

from sqlite_utils import Database
from yt_fts.db.infra import get_db_connection
from yt_fts.core.database import get_db_path
from yt_fts.download.quota_strategy import create_quota_strategy


def load_channels_from_database() -> tuple[list[str], str]:
    """Load channels from database and return (channels_list, temp_file_path).

    Creates a temporary file with channel URLs for use with BatchDownloader.
    Optimized for large channel databases with streaming approach.

    Returns:
        Tuple of (channels list, temp file path)
    """
    db_path = get_db_path()
    channels = []
    temp_file_path = ""

    # Use direct SQLite connection for better performance with large datasets
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row

            # Create temp file and stream channel URLs to it
            with tempfile.NamedTemporaryFile(
                mode="w", suffix="_channels.txt", delete=False, encoding="utf-8"
            ) as f:
                temp_file_path = f.name

                # Stream results in batches to avoid loading all into memory at once
                cursor = conn.execute(
                    "SELECT channel_url FROM Channels ORDER BY channel_id"
                )

                batch_size = 1000  # Process in batches to avoid memory issues
                batch = []
                total_channels = 0

                for row in cursor:
                    channel_url = row[0]
                    if channel_url:
                        batch.append(channel_url)
                        total_channels += 1

                        # Write batch to file when it reaches batch_size
                        if len(batch) >= batch_size:
                            f.write("\n".join(batch) + "\n")
                            channels.extend(batch)
                            batch = []

                # Write remaining batch
                if batch:
                    f.write("\n".join(batch) + "\n")
                    channels.extend(batch)

            # Performance info removed for cleaner output

    except Exception as e:
        # Fallback to old method if optimized version fails
        print(
            f"[WARNING] Optimized channel loading failed ({e}), using fallback method"
        )
        db = Database(db_path)
        channels = db.execute("SELECT channel_url FROM Channels").fetchall()
        channels = [row[0] for row in channels if row[0]]

        if channels:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix="_channels.txt", delete=False, encoding="utf-8"
            ) as f:
                temp_file_path = f.name
                f.write("\n".join(channels))

    return channels, temp_file_path


def initialize_quota_strategy(
    quota_daily: int,
    quota_conservative_pct: float,
    quota_aggressive_pct: float,
) -> Any:
    """Initialize and return quota strategy based on current usage.

    Returns:
        QuotaStrategy instance configured for current usage
    """
    try:
        db = Database(get_db_path())
        today = str(date_module.today())
        quota_result = db.execute(
            "SELECT quota_used FROM yt_api_quota WHERE date = ?", (today,)
        ).fetchone()
        current_quota_used = quota_result[0] if quota_result and quota_result[0] else 0
    except (OSError, TimeoutError, ValueError, RuntimeError):
        current_quota_used = 0

    return create_quota_strategy(
        daily_quota=quota_daily,
        conservative_pct=quota_conservative_pct,
        aggressive_pct=quota_aggressive_pct,
        quota_used=current_quota_used,
    )


def determine_rich_mode(rich: bool, rich_1: bool, richo: bool) -> str | None:
    """Determine which Rich mode to use based on flags.

    Returns:
        'new' for rich/rich_1, 'old' for richo, None for default
    """
    if rich_1 or rich:
        return "new"
    if richo:
        return "old"
    return None


def find_input_file(input_file: str) -> str | None:
    """Find input file in various locations.

    Args:
        input_file: File path or identifier

    Returns:
        Full path to file if found, None otherwise
    """
    # Check if direct file path
    if os.path.isfile(input_file):
        return input_file

    # Try relative to script directory
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    candidate_path = os.path.join(script_dir, input_file)
    if os.path.isfile(candidate_path):
        return candidate_path

    return None


def normalize_output_format(
    simple: bool, fzf: bool, rich: bool, rich_1: bool, richo: bool
) -> str:
    """Normalize legacy display flags to output_format.

    Returns:
        'simple', 'fzf', or 'rich'
    """
    if simple:
        return "simple"
    if fzf:
        return "fzf"
    if rich or rich_1 or richo:
        return "rich"
    return "rich"
