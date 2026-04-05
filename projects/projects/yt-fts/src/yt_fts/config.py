"""
Centralized configuration for yt-fts.

Single source of truth for all configuration values.
Eliminates hardcoded constants scattered across the codebase.

Usage:
    from yt_fts.config import (
        DAILY_QUOTA_LIMIT,
        QUOTA_PER_KEY,
        NUM_API_KEYS,
        get_db_path,
    )
"""

import json
import os
from pathlib import Path
from typing import Final

# =============================================================================
# API Configuration
# =============================================================================

# YouTube API Keys - loaded from environment
# YOUTUBE_API_KEY, YOUTUBE_API_KEY_2, YOUTUBE_API_KEY_3, YOUTUBE_API_KEY_4
_API_KEY_1: Final[str] = os.getenv("YOUTUBE_API_KEY", "")
_API_KEY_2: Final[str] = os.getenv("YOUTUBE_API_KEY_2", "")
_API_KEY_3: Final[str] = os.getenv("YOUTUBE_API_KEY_3", "")
_API_KEY_4: Final[str] = os.getenv("YOUTUBE_API_KEY_4", "")

# All non-empty API keys
API_KEYS: Final[tuple[str, ...]] = tuple(
    k for k in [_API_KEY_1, _API_KEY_2, _API_KEY_3, _API_KEY_4] if k
)

# Number of available API keys (auto-calculated)
NUM_API_KEYS: Final[int] = len(API_KEYS)

# Quota per API key (YouTube Data API v3 limit)
QUOTA_PER_KEY: Final[int] = 10_000

# Total daily quota (auto-calculated based on available keys)
# This replaces hardcoded values scattered across:
#   - quota_strategy.py (was 20000)
#   - metadata_backfill_api.py (was 10000)
#   - cli.py (was 20000)
DAILY_QUOTA_LIMIT: Final[int] = QUOTA_PER_KEY * NUM_API_KEYS if NUM_API_KEYS > 0 else QUOTA_PER_KEY

# =============================================================================
# Database Configuration
# =============================================================================

# Default database location (platform-specific)
_DEFAULT_DB_PATH: Final[Path] = (
    Path.home() / ".config" / "yt-fts" / "subtitles.db"
)

# Allow override via environment variable
# Used by deploy.ps1 and testing scripts
_DB_PATH_OVERRIDE: Final[str | None] = os.getenv("YT_FTS_DB_PATH")

# Final database path (override takes precedence)
DB_PATH: Final[Path] = Path(_DB_PATH_OVERRIDE) if _DB_PATH_OVERRIDE else _DEFAULT_DB_PATH


def get_db_path() -> str:
    """
    Get the database path as a string.

    This function exists for backward compatibility with existing code
    that imports get_db_path from various modules.

    Returns:
        Path to the SQLite database file
    """
    return str(DB_PATH)


# =============================================================================
# Quota Strategy Configuration
# =============================================================================#

# Quota strategy thresholds (percentages of remaining quota)
CONSERVATIVE_THRESHOLD: Final[float] = 0.24   # Below 24%: conserve quota
AGGRESSIVE_THRESHOLD: Final[float] = 0.72    # Above 72%: use freely

# =============================================================================
# Display Configuration
# =============================================================================#

# Default display plugin
DEFAULT_DISPLAY_PLUGIN: Final[str] = "default"

# Valid display plugin categories
VALID_DISPLAY_CATEGORIES: Final[tuple[str, ...]] = (
    "core",
    "verbose",
    "diagnostic",
    "monitoring",
)

# =============================================================================
# Logging Configuration
# =============================================================================#

# Dual-sink logging: JSON file + clean console
LOG_DIR: Final[Path] = DB_PATH.parent / "logs"
LOG_FILE: Final[Path] = LOG_DIR / "yt_fts.log"
LOG_FORMAT_JSON: Final[str] = "json"
LOG_FORMAT_CONSOLE: Final[str] = "console"

# =============================================================================
# Validation / Debugging
# =============================================================================#

def validate_config() -> dict[str, bool | int | str]:
    """
    Validate configuration and return status.

    Returns:
        Dict with validation results
    """
    return {
        "api_keys_configured": NUM_API_KEYS > 0,
        "num_api_keys": NUM_API_KEYS,
        "daily_quota": DAILY_QUOTA_LIMIT,
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
    }


if __name__ == "__main__":
    # Self-test: print configuration when run directly
    import json

    print("yt-fts Configuration")
    print("=" * 40)
    print(f"API Keys: {NUM_API_KEYS}")
    print(f"Daily Quota: {DAILY_QUOTA_LIMIT:,}")
    print(f"Database: {DB_PATH}")
    print()
    print("Validation:")
    print(json.dumps(validate_config(), indent=2))
