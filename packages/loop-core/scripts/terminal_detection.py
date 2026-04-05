"""Terminal detection utilities for loop-core package.

This module provides terminal ID detection for multi-terminal isolation,
copied from hooks infrastructure to make loop-core standalone.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from threading import local
from typing import Any

# Thread-local cache for terminal ID
_terminal_cache = local()


def get_terminal_id(data: Mapping[str, Any] | None = None) -> str:
    """
    Get terminal ID with 5-priority detection and caching.

    Priority:
    1. Explicit terminal_id from hook input data (overrides cache)
    2. CLAUDE_TERMINAL_ID env var (highest priority env var)
    3. TERMINAL_ID, TERM_ID, SESSION_TERMINAL env vars
    4. Console detection (WT_SESSION, GetConsoleWindow on Windows)
    5. Derive from PID + session timestamp (unique per process)
    6. Return "" if no detection method succeeds

    Args:
        data: Optional hook input data with explicit terminal_id field

    Returns:
        Terminal ID string (format: {source}_{id}) or empty string
    """
    # Priority 1: Explicit terminal_id from data (overrides cache)
    if data and "terminal_id" in data:
        return str(data["terminal_id"])

    # Priority 2: Check cache
    cached_id = getattr(_terminal_cache, "terminal_id", None)
    if cached_id:
        return str(cached_id)

    # Priority 3: Environment variables (explicit override)
    terminal_id = (
        os.environ.get("CLAUDE_TERMINAL_ID") or
        os.environ.get("TERMINAL_ID") or
        os.environ.get("TERM_ID") or
        os.environ.get("SESSION_TERMINAL")
    )

    if terminal_id:
        terminal_id = f"env_{terminal_id}"
    else:
        # Priority 4: Console detection
        terminal_id = _detect_console_terminal()

    # Priority 5: Fallback to PID-based
    if not terminal_id:
        import time
        pid = os.getpid()
        timestamp = int(time.time())
        terminal_id = f"pid_{pid}_{timestamp}"

    # Cache result
    _terminal_cache.terminal_id = terminal_id
    return terminal_id


def _detect_console_terminal() -> str:
    """Detect console terminal ID from environment.

    Returns:
        Terminal ID string (format: console_{id}) or empty string
    """
    # Priority 1: Windows Terminal (WT_SESSION)
    wt_session = os.environ.get("WT_SESSION")
    if wt_session:
        # Extract UUID from WT_SESSION path
        # Format: {guid} or full path
        guid = wt_session.split("\\")[-1].strip("{}")
        return f"console_{guid[:8]}"  # Use first 8 chars of GUID

    # Priority 2: Windows console handle
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            # GetConsoleWindow() returns handle to console window
            kernel32 = ctypes.windll.kernel32
            get_console_window = kernel32.GetConsoleWindow
            get_console_window.restype = wintypes.HWND
            get_console_window.argtypes = []

            hwnd = get_console_window()
            if hwnd:
                return f"console_{hex(hwnd)}"
        except (OSError, AttributeError):
            pass

    return ""
