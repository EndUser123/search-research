"""Debug context management for yt-fts.

Provides a simple way to enable/disable debug output across the application.
Set via --debug flag in CLI commands.
"""
from __future__ import annotations

import os

# Environment variable key for debug mode
_DEBUG_ENV_KEY = "YT_FTS_DEBUG"


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv(_DEBUG_ENV_KEY, "").lower() in ("1", "true", "yes")


def enable_debug() -> None:
    """Enable debug mode."""
    os.environ[_DEBUG_ENV_KEY] = "1"


def disable_debug() -> None:
    """Disable debug mode."""
    os.environ.pop(_DEBUG_ENV_KEY, None)


def debug_print(msg: str) -> None:
    """Print message only if debug mode is enabled."""
    if is_debug():
        print(msg)
