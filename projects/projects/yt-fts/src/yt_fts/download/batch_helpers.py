"""
Helper functions for batch download operations.

Extracted from batch_download to reduce complexity and improve testability.
"""

import os
import tempfile
from datetime import date as date_module
from typing import Any

from sqlite_utils import Database

from yt_fts.core.database import get_db_path
from yt_fts.download.quota_strategy import create_quota_strategy


def load_channels_from_database() -> tuple[list[str], str]:
    """Load channels from database and return (channels_list, temp_file_path).

    Creates a temporary file with channel URLs for use with BatchDownloader.

    Returns:
        Tuple of (channels list, temp file path)
    """
    db = Database(get_db_path())
    channels = db.execute("SELECT channel_url FROM Channels").fetchall()

    if not channels:
        return [], ""

    # Create temp file with channel URLs
    with tempfile.NamedTemporaryFile(mode="w", suffix="_channels.txt", delete=False) as f:
        for row in channels:
            f.write(row[0] + chr(10))
        input_file = f.name

    return [row[0] for row in channels], input_file


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
    except Exception:
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
