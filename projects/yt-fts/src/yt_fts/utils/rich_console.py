"""
Rich console utilities for yt-fts.

Provides standardized console creation with Windows compatibility,
stderr support for progress displays, and fallback behavior.
"""
from __future__ import annotations

import sys
import threading

from rich.console import Console

# Lock for thread-safe console instance caching
_console_cache_lock = threading.Lock()

# Parameterized cache: each unique (width, legacy_windows, force_terminal)
# combination gets its own cached console instance
_console_instances: dict[tuple[int | None, bool, bool], Console] = {}
_stderr_console_instances: dict[tuple[int | None, bool, bool], Console] = {}


def get_console(
    width: int | None = None,
    legacy_windows: bool = False,
    force_terminal: bool = False,
) -> Console:
    """Get a Rich Console instance for stdout output.

    Provides standardized console configuration with Windows compatibility.
    Uses parameterized caching to return the same instance for identical parameters.

    Args:
        width: Terminal width (defaults to console detection).
        legacy_windows: Use legacy Windows mode (default: False).
        force_terminal: Force terminal mode (default: False).

    Returns:
        Configured Rich Console instance (cached per unique parameter combination).
    """
    cache_key = (width, legacy_windows, force_terminal)
    with _console_cache_lock:
        if cache_key not in _console_instances:
            _console_instances[cache_key] = Console(
                width=width,
                legacy_windows=legacy_windows,
                force_terminal=force_terminal,
                file=sys.stdout,
            )
        return _console_instances[cache_key]


def get_stderr_console(
    width: int | None = None,
    legacy_windows: bool = False,
    force_terminal: bool = False,
) -> Console:
    """Get a Rich Console instance for stderr output.

    Use this for progress displays and status updates to avoid
    interfering with stdout data streams.
    Uses parameterized caching to return the same instance for identical parameters.

    Args:
        width: Terminal width (defaults to console detection).
        legacy_windows: Use legacy Windows mode (default: False).
        force_terminal: Force terminal mode (default: False).

    Returns:
        Configured Rich Console instance writing to stderr (cached per unique parameter combination).
    """
    cache_key = (width, legacy_windows, force_terminal)
    with _console_cache_lock:
        if cache_key not in _stderr_console_instances:
            _stderr_console_instances[cache_key] = Console(
                width=width,
                legacy_windows=legacy_windows,
                force_terminal=force_terminal,
                file=sys.stderr,
            )
        return _stderr_console_instances[cache_key]


def reset_console_cache() -> None:
    """Reset the console instance cache.

    Primarily useful for testing to ensure fresh console instances.
    Thread-safe: acquires lock before clearing caches.
    """
    with _console_cache_lock:
        _console_instances.clear()
        _stderr_console_instances.clear()
