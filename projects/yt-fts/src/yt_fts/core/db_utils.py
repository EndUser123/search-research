"""
Database utility functions for yt-fts.

This module provides core database functions that were previously in utils.db_utils
but are now properly organized in the core module.
"""
from __future__ import annotations


from yt_fts.db.search import search_all

from .database import (
    escape_fts5_query,
    get_channel_id_from_input,
    get_channels,
)


def get_all_channel_ids() -> list[str]:
    """
    Get all channel IDs from the database.

    Returns:
        List of channel IDs as strings
    """
    channels = get_channels()
    return [str(channel[3]) for channel in channels]  # channel_id is at index 3


# Re-export the main functions that were imported from this module
__all__ = [
    "escape_fts5_query",
    "get_all_channel_ids",
    "get_channel_id_from_input",
    "get_channels",
    "search_all",
]
