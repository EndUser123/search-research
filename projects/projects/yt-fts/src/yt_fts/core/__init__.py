"""
YT-FTS Core Package

Core functionality for YouTube Full Text Search including:
- CLI interface
- Database operations
- Multi-channel search
- Search functionality

This package provides the foundational components for yt-fts operations.
"""

# Lazy import to avoid circular import with download modules
# from .database import Database  # Database class not available
from typing import Any

from .db_utils import *
from .multi_channel_search import MultiChannelSearchController
from .search import SearchHandler


def __getattr__(name: str) -> Any:
    """Lazy import attribute accessor for the cli module.

    Implements lazy loading to avoid circular import issues with download modules.

    Args:
        name: Name of the attribute to import.

    Returns:
        The requested module attribute.

    Raises:
        AttributeError: If the requested attribute does not exist.
    """
    if name == "cli":
        from .cli import cli
        return cli
    if name == "status_display":
        import importlib
        return importlib.import_module(f"{__name__}.status_display")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

__all__ = ["MultiChannelSearchController", "SearchHandler", "cli", "status_display"]
