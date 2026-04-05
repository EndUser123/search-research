"""
Fast Channel Resolver - Bypass slow UnifiedChannelProcessor for better performance.

This module provides a much faster alternative to the UnifiedChannelProcessor
for basic channel ID resolution during batch operations.
"""
from __future__ import annotations

import io
import os
import sys
import threading
from typing import Any, Literal

from rich.console import Console

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

# Import shared lock from output_utils to prevent race conditions
# when both modules are used concurrently in multi-threaded environments.
from yt_fts.download.output_utils import _stderr_capture_lock


class StderrCapture:
    """
    Capture stderr for error classification while suppressing visual spam.

    Thread-safe: Uses a global lock to prevent race conditions when multiple
    threads capture stderr concurrently.
    """

    def __init__(self) -> None:
        """
        Initialize stderr capture context manager.

        Sets up buffers and file handles for capturing stderr output
        while suppressing visual display.
        """
        self.devnull: io.TextIOWrapper | None = None
        self.original_stderr: Any | None = None
        self.buffer = io.StringIO()
        self.captured_output: str = ""
        self.saved_stderr_fd: int | None = None

    def __enter__(self) -> "StderrCapture":
        """
        Enter the context and redirect stderr to buffer.

        Returns:
            self: The context manager instance
        """
        # Acquire lock to prevent concurrent stderr modifications
        _stderr_capture_lock.acquire()

        self.buffer = io.StringIO()
        self.captured_output = ""
        self.devnull = open(os.devnull, "w")
        self.original_stderr = sys.stderr
        sys.stderr = self.buffer

        # Also try to redirect at the file descriptor level (for C libraries)
        try:
            import fcntl  # noqa: F401
            assert self.devnull is not None
            self.saved_stderr_fd = os.dup(2)
            os.dup2(self.devnull.fileno(), 2)
        except (ImportError, AttributeError):
            # fcntl not available on Windows, use SetStdHandle instead
            try:
                import ctypes
                assert self.devnull is not None
                ctypes.windll.kernel32.SetStdHandle(-12, self.devnull.fileno())
            except (OSError, AttributeError):
                pass
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        """
        Exit the context and restore stderr.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred

        Returns:
            Literal[False]: Does not suppress exceptions
        """
        # Capture output before any cleanup
        self.captured_output = self.buffer.getvalue()

        try:
            # Restore original stderr
            sys.stderr = self.original_stderr

            # Restore file descriptor only if we saved one
            if self.saved_stderr_fd is not None:
                try:
                    os.dup2(self.saved_stderr_fd, 2)
                    os.close(self.saved_stderr_fd)
                except OSError:
                    pass
        finally:
            # Guaranteed cleanup: always close file handles and release lock
            if self.devnull:
                try:
                    self.devnull.close()
                except OSError:
                    pass
            if self.buffer:
                try:
                    self.buffer.close()
                except OSError:
                    pass
            # Always release the lock, even if an error occurred
            _stderr_capture_lock.release()
        return False

    def get_error_category(self) -> tuple[Any, Any] | tuple[None, None]:
        """
        Classify captured stderr output into error category.

        Returns:
            Tuple of (ErrorCategory, user_message) or (None, None)
                if no output was captured
        """
        if not self.captured_output:
            return None, None
        from yt_fts.utils.error_classifier import ErrorClassifier
        return ErrorClassifier.classify(self.captured_output)


class FastChannelResolver:
    """Fast channel resolver for batch operations."""

    def __init__(self, console: Console | None = None, cookies_from_browser: str | None = None) -> None:
        """
        Initialize fast channel resolver.

        Args:
            console: Rich console for output (defaults to new Console())
            cookies_from_browser: Browser name for cookie extraction
        """
        self.console = console or Console()
        self.cookies_from_browser = cookies_from_browser
        self.cache: dict[str, dict[str, Any]] = {}
        self.stats: dict[str, int] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
        }

    def resolve_channel_id(self, channel_url: str) -> dict[str, Any] | None:
        """
        Resolve a channel URL to get its ID and metadata.

        Args:
            channel_url: YouTube channel URL

        Returns:
            Dict with channel_id, channel_name, and url, or None on failure
        """
        # Check cache first
        if channel_url in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[channel_url]

        self.stats["cache_misses"] += 1

        if not YTDLP_AVAILABLE:
            return None

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "socket_timeout": 15,
        }

        if self.cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)

        try:
            with StderrCapture(), yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)

            if info and "channel_id" in info:
                result = {
                    "channel_id": info["channel_id"],
                    "channel_name": info.get("channel", info.get("uploader", "Unknown")),
                    "url": channel_url,
                }
                self.cache[channel_url] = result
                return result

            self.stats["errors"] += 1
            return None

        except Exception:
            self.stats["errors"] += 1
            return None

    def resolve_batch(self, channel_urls: list[str]) -> dict[str, dict[str, Any] | None]:
        """
        Resolve multiple channel URLs in batch.

        Args:
            channel_urls: List of YouTube channel URLs

        Returns:
            Dict mapping URL to resolve result (or None on failure)
        """
        results: dict[str, dict[str, Any] | None] = {}
        for url in channel_urls:
            results[url] = self.resolve_channel_id(url)
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get resolver statistics."""
        return self.stats.copy()

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self.cache.clear()
