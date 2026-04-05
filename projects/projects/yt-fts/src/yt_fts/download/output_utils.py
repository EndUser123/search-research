"""
Output utilities for suppressing and capturing external process output.

Provides context managers and loggers for handling output from external
tools like yt-dlp that generate verbose stderr spam.
"""
import io
import os
import sys
import threading
from collections.abc import Callable
from typing import Any

# Global lock to prevent concurrent stderr capture in multi-threaded environments.
# Without this, multiple threads modifying sys.stderr creates a race condition
# where one thread closes file handles that another thread is still using.
_stderr_capture_lock = threading.Lock()


class StderrCapture:
    """
    Capture stderr for error classification while suppressing visual spam.

    Captures stderr output to a buffer for later analysis and classification
    into user-friendly error messages.

    Thread-safe: Uses a global lock to prevent race conditions when multiple
    threads capture stderr concurrently.
    """

    def __init__(self) -> None:
        """
        Initialize stderr capture context manager.

        Sets up buffers and file handles for capturing stderr output
        while suppressing visual display.
        """
        self.devnull: Any = None
        self.original_stderr: Any = None
        self.buffer = io.StringIO()
        self.captured_output = ""
        self.saved_stderr_fd: int | None = None  # Track if we have a saved fd to restore

    def __enter__(self) -> Any:
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

        # Redirect Python-level stderr to our buffer
        self.original_stderr = sys.stderr
        sys.stderr = self.buffer

        # Also try to redirect at the file descriptor level (for C libraries like yt-dlp)
        # Check for fcntl availability without importing (platform check)
        try:
            import importlib.util
            fcntl_available = importlib.util.find_spec("fcntl") is not None
        except ImportError:
            fcntl_available = False

        if fcntl_available:
            self.saved_stderr_fd = os.dup(2)
            os.dup2(self.devnull.fileno(), 2)
        else:
            # fcntl not available on Windows - use SetStdHandle
            try:
                import ctypes

                ctypes.windll.kernel32.SetStdHandle(-12, self.devnull.fileno())
            except OSError:
                pass
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the context and restore stderr.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred

        Returns:
            False: Does not suppress exceptions
        """
        try:
            # Capture any buffered output before restoring
            self.captured_output = self.buffer.getvalue()

            # Restore original stderr
            sys.stderr = self.original_stderr

            # Restore file descriptor only if we saved one
            if self.saved_stderr_fd is not None:
                try:
                    os.dup2(self.saved_stderr_fd, 2)
                    os.close(self.saved_stderr_fd)
                except OSError:
                    pass

            if self.devnull:
                self.devnull.close()
            if self.buffer:
                self.buffer.close()
        finally:
            # Always release the lock, even if an error occurred
            _stderr_capture_lock.release()

    def get_error_category(self) -> tuple[Any, Any] | None:
        """
        Get categorized error information from captured stderr.

        Returns:
            Tuple of (category_enum, user_message) or (None, None) if no error
        """
        if not self.captured_output:
            return None, None

        from yt_fts.utils.error_classifier import ErrorClassifier

        return ErrorClassifier.classify(self.captured_output)

    def had_output(self) -> bool:
        """Check if any stderr was captured."""
        return bool(self.captured_output.strip())


class YtdlpSilentLogger:
    """
    Custom logger for yt-dlp that suppresses all output.

    yt-dlp has internal logging that bypasses quiet/no_warnings.
    This logger intercepts and suppresses those messages while
    still allowing critical errors to be captured for classification.
    """

    def __init__(self, callback: Callable[[str], None] | None = None):
        """
        Initialize the silent logger.

        Args:
            callback: Optional callback for captured error messages
        """
        self.callback = callback
        self.buffer = io.StringIO()

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Suppress debug messages."""

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Suppress info messages."""

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Suppress warning messages."""

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Capture error messages for classification."""
        if self.callback:
            self.callback(str(msg))

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Capture critical messages."""
        if self.callback:
            self.callback(str(msg))
