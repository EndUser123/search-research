"""
Download exceptions.

Custom exceptions for download operations that need special handling
beyond standard Python exceptions.
"""

from __future__ import annotations
import functools
import threading
from collections.abc import Callable
from typing import Any


class BaseURLFallbackFailed(Exception):
    """
    Exception raised when base URL fallback also fails.

    This exception signals that we've already tried both the /videos URL
    and the base channel URL, so retrying is pointless. The outer retry
    loop should catch this specific exception and not retry.
    """


class DownloadTimeoutException(Exception):
    """Exception raised when download exceeds max time limit."""


class PerVideoTimeoutException(Exception):
    """Exception raised when a single video processing exceeds timeout."""


class ChannelEmptyError(Exception):
    """
    Exception raised when a channel has no accessible videos.

    This is a content error (channel deleted, private, or geo-blocked),
    not a system error. The batch downloader should catch this and skip
    the channel rather than crashing the entire batch.
    """


def timeoutable(timeout_seconds: float | None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that enforces a timeout on a function call.

    Uses threading to interrupt long-running operations. This is necessary
    because yt-dlp calls can hang indefinitely on network operations,
    and socket_timeout alone doesn't catch all cases.

    Args:
        timeout_seconds: Maximum time in seconds, or None for no timeout

    Returns:
        Decorated function that raises PerVideoTimeoutException on timeout

    Example:
        @timeoutable(30)
        def extract_video_info(url):
            return ydl.extract_info(url, download=False)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if timeout_seconds is None:
                return func(*args, **kwargs)

            result = None
            exception = None

            def worker() -> None:
                nonlocal result, exception
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    exception = e

            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            thread.join(timeout=timeout_seconds)

            if thread.is_alive():
                # Thread is still running = timeout exceeded
                # We can't actually kill the thread in Python, but we can
                # stop waiting for it and return/raise. The yt-dlp process
                # may continue in background but will be garbage collected.
                msg = f"Operation exceeded {timeout_seconds}s timeout"
                raise PerVideoTimeoutException(
                    msg
                )

            if exception is not None:
                raise exception

            return result
        return wrapper
    return decorator
