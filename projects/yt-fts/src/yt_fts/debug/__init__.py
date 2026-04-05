"""
Debug telemetry and diagnostics for yt-fts.

This module provides structured debugging capabilities including:
- Event-based telemetry with persistent storage
- Queryable debug sessions
- Error capture and analysis
"""
from __future__ import annotations

from yt_fts.debug.telemetry import (
    DebugEvent,
    DebugSession,
    get_debug_session,
    clear_debug_session,
    _get_db_path,
)

__all__ = [
    "DebugEvent",
    "DebugSession",
    "get_debug_session",
    "clear_debug_session",
    "_get_db_path",
]
