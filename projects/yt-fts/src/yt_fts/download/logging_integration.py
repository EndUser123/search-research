"""
Integration of dual-sink logging with download components.

This module provides wrappers and patches to integrate the dual-sink logging
system with existing download functionality without breaking changes.
"""

from __future__ import annotations
import functools
import time
from collections.abc import Callable
from typing import Any, Literal

from yt_fts.utils.dual_sink_logger import (
    get_logger,
    log_operation,
    log_technical_error,
    log_user_message,
)

logger = get_logger(__name__)

class LoggedDownloadOperation:
    """
    Context manager for logging download operations with clean separation.
    """

    def __init__(self, operation_name: str, channel: str | None=None, suppress_transient_errors: bool = False, **context: Any) -> None:
        """
        Initialize the logging context manager.

        Args:
            operation_name: Name of the operation being logged.
            channel: Channel identifier.
            **context: Additional context for logging.

        Returns:
            None
        """
        self.operation_name = operation_name
        self.channel = channel
        self.context = context
        self.suppress_transient_errors = suppress_transient_errors
        self.start_time: float | None = None
        self.success = False

    def __enter__(self) -> Any:
        """
        Enter the logging context.

        Returns:
            Self
        """
        self.start_time = time.time()
        log_operation(self.operation_name, f"Starting {self.operation_name}", level=10, channel=self.channel, **self.context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        """
        Exit the logging context and flush logs.

        Args:
            exc_type: Exception type if an error occurred.
            exc_val: Exception value if an error occurred.
            exc_tb: Exception traceback if an error occurred.

        Returns:
            False (don't suppress exceptions)
        """
        duration_ms = (time.time() - (self.start_time or time.time())) * 1000
        self.success = exc_type is None
        context = {**self.context, "duration_ms": duration_ms, "success": self.success}
        if self.success:
            log_operation(self.operation_name, f"Completed {self.operation_name} successfully", level=10, **context)
            if self.channel:
                log_user_message(20, f"✅ Successfully downloaded {self.channel}")
        else:
            target = self.channel or self.context.get("playlist_url") or self.context.get("channel_url", "")
            if len(target) > 60:
                target = target[:57] + "..."
            log_operation(self.operation_name, f"Failed {self.operation_name}", level=10, **context)
            if exc_val:
                import logging
                logger = logging.getLogger(f"{__name__}.technical")
                logger.setLevel(logging.DEBUG)
                logger.debug("Failed %s: %s", self.operation_name, exc_val, exc_info=exc_val, extra={**context, "user_error": str(exc_val)})
            if target and not self.suppress_transient_errors:
                log_user_message(40, f"❌ {self.operation_name} failed: {target}")
        return False

def log_download_progress(channel: str, current: int, total: int, video_title: str | None=None) -> None:
    """Log download progress with clean user output and detailed file logs."""
    percentage = current / total * 100 if total > 0 else 0
    log_user_message(20, f"📊 {channel}: {current}/{total} videos downloaded ({percentage:.1f}%)")
    log_operation("progress", "Video download completed", level=10, channel=channel, video_number=current, total_videos=total, percentage=percentage, video_title=video_title)

def log_retry_attempt(operation: str, error: Exception, attempt: int, max_attempts: int, **context: Any) -> None:
    """Log retry attempts with user-friendly messages and technical details."""
    log_user_message(30, f"⚠️  {operation} failed (attempt {attempt}/{max_attempts}), retrying...")
    log_technical_error(error, {"operation": operation, "attempt": attempt, "max_attempts": max_attempts, "is_retry": True, **context})

def logged_function(operation_name: str | None=None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to automatically log function execution with dual-sink separation.

    Args:
        operation_name: Name for the operation (defaults to function name)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator factory for operation logging.

        Args:
            func: Function to wrap with logging.

        Returns:
            Wrapped function with logging capability.
        """
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function that logs operation progress.

            Returns:
                Result from the wrapped function.

            Raises:
                Exception: Re-raises any exception from wrapped function.
            """
            start_time = time.time()
            log_operation(op_name, f"Starting {op_name}", level=10, function=func.__name__, args_count=len(args), kwargs_keys=list(kwargs.keys()))
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_operation(op_name, f"Completed {op_name} successfully", level=10, duration_ms=duration_ms, result_type=type(result).__name__)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_technical_error(e, {"operation": op_name, "function": func.__name__, "duration_ms": duration_ms, "args_count": len(args), "kwargs_keys": list(kwargs.keys())})
                raise
        return wrapper
    return decorator

class LoggedBatchDownloader:
    """
    Wrapper class to add logging to existing BatchDownloader without modifying its core logic.
    """

    def __init__(self, batch_downloader: Any) -> None:
        """
        Initialize the operation logger.

        Args:
            batch_downloader: Batch downloader instance to wrap.

        Returns:
            None
        """
        self.downloader = batch_downloader
        self.logger = get_logger(f"{__name__}.BatchDownloader")

    def download_all_with_logging(self) -> dict[str, Any]:
        """Download all channels with comprehensive logging."""
        channels = self.downloader.channels
        log_user_message(20, f"🚀 Starting batch download of {len(channels)} channels")
        with LoggedDownloadOperation("batch_download", total_channels=len(channels)):
            valid_channels = self.downloader.validate_channels()
            if len(valid_channels) != len(channels):
                log_user_message(30, f"⚠️  {len(channels) - len(valid_channels)} invalid channels skipped")
            try:
                results = self.downloader.download_all()
                successful = len(results.get("successful", []))
                failed = len(results.get("failed", []))
                log_user_message(20, f"✅ Batch download complete: {successful} successful, {failed} failed")
                log_operation("batch_summary", "Batch download completed", level=20, total_channels=len(channels), successful=successful, failed=failed)
                return results
            except Exception as e:
                log_technical_error(e, {"operation": "batch_download", "total_channels": len(channels), "stage": "execution"})
                log_user_message(40, f"❌ Batch download failed: {e!s}")
                raise
