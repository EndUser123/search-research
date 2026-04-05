"""
Quota strategy initialization for batch download operations.

Extracted from batch_download for better modularity.
"""
from datetime import date

from yt_fts.utils.logging import log_msg
from yt_fts.utils.rich_console import get_console

console = get_console()


def initialize_quota_strategy(
    quota_daily: int,
    quota_conservative_pct: float,
    quota_aggressive_pct: float,
) -> object:
    """Initialize quota strategy for the batch download.

    Args:
        quota_daily: Daily quota limit
        quota_conservative_pct: Conservative percentage (0.8 = 80%)
        quota_aggressive_pct: Aggressive percentage (1.2 = 120%)

    Returns:
        QuotaStrategy object configured with current usage
    """
    from sqlite_utils import Database

    from yt_fts.core.database import get_db_path
    from yt_fts.download.quota_strategy import create_quota_strategy

    log_msg("QUOTA", "Computing strategy...")

    # Get current quota usage from database
    try:
        db = Database(get_db_path())
        today = str(date.today())
        quota_result = db.execute(
            "SELECT quota_used FROM yt_api_quota WHERE date = ?", (today,)
        ).fetchone()
        current_quota_used = quota_result[0] if quota_result and quota_result[0] else 0
    except Exception:
        current_quota_used = 0

    quota_strategy = create_quota_strategy(
        daily_quota=quota_daily,
        conservative_pct=quota_conservative_pct,
        aggressive_pct=quota_aggressive_pct,
        quota_used=current_quota_used,
    )

    log_msg("QUOTA", quota_strategy.get_status_message())

    return quota_strategy


def get_metadata_only_delay(default_delay: float, videos_per_channel: int) -> float:
    """Get appropriate delay for metadata-only mode.

    In metadata-only mode, we don't need rate limiting, so use 0 delay
    unless explicitly set otherwise.

    Args:
        default_delay: The configured default delay
        videos_per_channel: Videos to download per channel (0 = metadata-only)

    Returns:
        Appropriate delay for the mode
    """
    # Metadata-only mode: no rate limit, only daily quota - use 0 delay by default
    if videos_per_channel == 0 and default_delay == 60.0:
        return 0.0
    return default_delay
