"""
Services module for yt-fts.

Contains service layer components for channel processing,
export functionality, and other business logic services.
"""
from __future__ import annotations

from typing import Any

# Import main service classes for easier access
from .channel_cleaner import ChannelCleaner
from .channel_file_updater import ChannelFileUpdater
from .rss_precheck import RssCheckResult, RssPreChecker, create_rss_checker
from .unified_channel_processor import UnifiedChannelProcessor

# ExportHandler is imported lazily to avoid circular dependency with core.search
# The circular path: services/__init__ -> export -> core.database -> core.search -> services.export
__all__ = [
    "ChannelCleaner",
    "ChannelFileUpdater",
    "ExportHandler",
    "RssCheckResult",
    "RssPreChecker",
    "UnifiedChannelProcessor",
    "create_rss_checker",
]


def __getattr__(name: str) -> Any:
    """Lazy import for ExportHandler to avoid circular dependency.

    The circular import path:
    - services/__init__.py imports ExportHandler
    - core/search.py imports ExportHandler from services.export
    - When services is imported, __init__.py runs immediately
    - This creates a cycle when combined with other imports

    By using __getattr__, ExportHandler is only imported when actually accessed.
    """
    if name == "ExportHandler":
        from .export import ExportHandler
        return ExportHandler
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
