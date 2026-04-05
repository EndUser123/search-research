"""
Dual-sink logging system for clean separation of technical debug logs and user console output.

Provides:
- File-based debug logging with structured JSON format for technical details
- Clean console logging for user interface without noise
- Environment-based configuration for log levels
- Integration with Rich UI without breaking progress bars
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import rich.console
import rich.logging

# Import error sanitization for secure logging (Item 12)
try:
    from .error_sanitizer import sanitize_error_context
except ImportError:
    # Fallback if error_sanitizer not yet available
    def sanitize_error_context(context: dict[str, Any]) -> dict[str, Any]:
        """Fallback error context sanitizer when error_sanitizer module unavailable.

        Args:
            context: The error context to sanitize.

        Returns:
            The context unchanged (fallback behavior).
        """
        return context


class StructuredFileFormatter(logging.Formatter):
    """JSON formatter for structured debug logs.

    Formats log records as JSON objects with timestamp, level, logger name,
    message, module, function, line number, and optional fields like
    channel_id, video_id, operation, retry_count, and duration_ms.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON.

        Args:
            record: The log record to format.

        Returns:
            A JSON string containing the formatted log record.
        """
        data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "channel_id"):
            data["channel_id"] = record.channel_id
        if hasattr(record, "video_id"):
            data["video_id"] = record.video_id
        if hasattr(record, "operation"):
            data["operation"] = record.operation
        if hasattr(record, "retry_count"):
            data["retry_count"] = record.retry_count
        if hasattr(record, "duration_ms"):
            data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        # Add stack trace for debug level
        if record.levelno >= logging.DEBUG and record.stack_info:
            data["stack_trace"] = record.stack_info

        return json.dumps(data, ensure_ascii=False)


class CleanConsoleFormatter(logging.Formatter):
    """Clean formatter for user console output without technical noise.

    Filters debug messages and formats errors, warnings, and info messages
    for clean user-facing console output.
    """

    def __init__(self) -> None:
        """Initialize the clean console formatter."""
        super().__init__()
        # Simple message-only format for clean console output
        self.user_messages = {
            "DOWNLOAD_START": "⬇️  Downloading channel: {channel}",
            "DOWNLOAD_SUCCESS": "✓ Successfully downloaded channel",
            "DOWNLOAD_ERROR": "❌ Download failed: {error}",
            "SEARCH_COMPLETE": "🔍 Search complete: {count} results",
            "EMBEDDING_PROGRESS": "🧠 Processing embeddings: {progress}%",
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for clean console output.

        Args:
            record: The log record to format.

        Returns:
            A formatted string for console display, or empty string for debug logs.
        """
        # Skip debug messages in console (they go to file only)
        if record.levelno == logging.DEBUG:
            return ""

        # For user-facing messages, use simple formatting
        if hasattr(record, "user_message"):
            return record.getMessage()

        # For errors, show clean message without technical details
        if record.levelno >= logging.ERROR:
            if hasattr(record, "user_error"):
                return f"❌ {record.user_error}"
            # For errors without user_error, show exception type and message
            msg = record.getMessage()
            if msg and msg != "None":
                return f"❌ ERROR: {msg}"
            # Fallback to showing the log level with a hint to check logs
            return "❌ ERROR: Check debug logs for details"

        # For warnings and info, show message only
        return record.getMessage()


class DualSinkLogger:
    """
    Dual-sink logging system that separates technical debug logs from user interface.

    Technical details (exceptions, stack traces, retry logic) → structured JSON file
    User interface (progress, clean messages) → clean console output
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        console: rich.console.Console | None = None,
        debug_enabled: bool | None = None,
    ):
        """
        Initialize dual-sink logging system.

        Args:
            log_dir: Directory for debug log files (default: ~/.config/yt-fts/logs)
            console: Rich console instance (default: creates new console)
            debug_enabled: Force enable/disable debug logging (default: auto-detect)
        """
        self.log_dir = log_dir or self._get_default_log_dir()
        self.console = console or rich.console.Console(stderr=False)
        self.debug_enabled = (
            debug_enabled if debug_enabled is not None else self._detect_debug_mode()
        )

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        self._configure_root_logger()

        # Thread-safe file handler for debug logs
        self.debug_handler: logging.handlers.RotatingFileHandler | None = None
        self.console_handler: rich.logging.RichHandler | None = None

        self._setup_handlers()

    def _get_default_log_dir(self) -> Path:
        """
        Get default log directory based on environment.

        Development mode: Project directory (logs/)
        Production mode: Platform-specific config directory

        Returns:
            Path to the log directory.
        """
        # Check if we're in development mode
        if self._is_development_mode():
            # Use project-relative logs directory for development
            try:
                # Get the project root (where pyproject.toml is located)
                import yt_fts

                module_path = Path(yt_fts.__file__).parent

                # Check if we're in development (src/ layout)
                if module_path.name == "yt_fts":
                    # We're in src/yt_fts/ or similar
                    # Look for pyproject.toml in parent directories
                    project_root = None
                    for check_dir in [module_path.parent, module_path.parent.parent]:
                        if (check_dir / "pyproject.toml").exists():
                            project_root = check_dir
                            break

                    if not project_root:
                        # Fallback: assume src/ layout, go up two levels
                        project_root = module_path.parent.parent
                else:
                    # Not in src/ layout, use module parent
                    project_root = module_path.parent

                log_dir = project_root / "logs"
            except (OSError, ValueError):
                # Fallback to current working directory if detection fails
                log_dir = Path.cwd() / "logs"
        # Production mode: use platform-specific config directory
        elif sys.platform == "win32":
            log_dir = Path(os.environ.get("APPDATA", "")) / "yt-fts" / "logs"
        else:
            log_dir = Path.home() / ".config" / "yt-fts" / "logs"

        return log_dir

    def _is_development_mode(self) -> bool:
        """
        Detect if running in development environment.

        Returns:
            True if running in development environment (has pyproject.toml,
            development environment variables set, or in editable install mode),
            False otherwise.
        """
        # First, check if we're in a project directory with development markers
        cwd = Path.cwd()

        # Check current directory and parent for project markers
        for check_dir in [cwd, cwd.parent, cwd.parent.parent]:
            if (check_dir / "pyproject.toml").exists():
                # Found pyproject.toml - check if it's the yt-fts project
                try:
                    pyproject_path = check_dir / "pyproject.toml"
                    with Path(pyproject_path).open("r") as f:
                        content = f.read()
                        if "yt-fts" in content or "yt_fts" in content:
                            return True
                except Exception:
                    pass

        # Check if we're running from src/ directory (development layout)
        try:
            import yt_fts

            module_path = Path(yt_fts.__file__).parent

            # Check if we're in a src/ layout with pyproject.toml
            if module_path.name == "yt_fts":
                # Look for pyproject.toml in parent or grandparent
                for check_dir in [module_path.parent, module_path.parent.parent]:
                    if (check_dir / "pyproject.toml").exists():
                        return True
        except Exception:
            pass

        # Check for common development environment variables
        dev_indicators = [
            os.environ.get("YT_FTS_DEBUG"),  # Debug flag
            os.environ.get("PYTHONDEVMODE"),  # Python development mode
            os.environ.get("DEV"),  # Generic dev flag
            os.environ.get("VIRTUAL_ENV"),  # In a virtual environment
        ]

        return bool(any(indicator for indicator in dev_indicators if indicator))

    def _detect_debug_mode(self) -> bool:
        """Auto-detect if debug mode should be enabled.

        Returns:
            True if debug mode should be enabled, False otherwise.
        """
        # Check environment variables
        if os.environ.get("YT_FTS_DEBUG"):
            return True
        if os.environ.get("YT_FTS_QUIET_MODE"):
            return False

        # Check if running in development/integrated environment
        if os.environ.get("YT_FTS_WRAPPER_MODE"):
            return False  # Production wrapper mode

        # Default to enabled for development
        return True

    def _configure_root_logger(self) -> None:
        """Configure the root logger to avoid duplicate handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if self.debug_enabled else logging.INFO)

        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()

    def _setup_handlers(self) -> None:
        """Setup file and console handlers."""
        root_logger = logging.getLogger()

        # File handler for structured debug logs
        if self.debug_enabled:
            debug_log_file = (
                self.log_dir
                / f"debug_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
            )
            self.debug_handler = logging.handlers.RotatingFileHandler(
                debug_log_file,
                maxBytes=50 * 1024 * 1024,  # 50MB
                backupCount=5,
                encoding="utf-8",
            )
            self.debug_handler.setLevel(logging.DEBUG)
            self.debug_handler.setFormatter(StructuredFileFormatter())
            root_logger.addHandler(self.debug_handler)

        # Console handler for clean user output
        self.console_handler = rich.logging.RichHandler(
            console=self.console,
            show_time=False,
            show_path=False,
            markup=True,
            rich_tracebacks=False,  # Tracebacks go to file only
            omit_repeated_times=False,
        )
        self.console_handler.setLevel(logging.ERROR)  # Suppress WARNING level logs from RichHandler
        self.console_handler.setFormatter(CleanConsoleFormatter())
        root_logger.addHandler(self.console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the dual-sink configuration.

        Args:
            name: Name for the logger (e.g., "__main__", "user_interface",
                "technical", "operation.download"). Use "technical" for logs
                that should only go to the file.

        Returns:
            A configured logger instance.
        """
        logger = logging.getLogger(name)
        # Suppress technical logger spam in console - only show file logs
        if name == "technical":
            logger.setLevel(logging.CRITICAL)  # Only show CRITICAL (basically nothing)
            # Also propagate to any child loggers
            logger.propagate = (
                False  # Don't propagate to root logger (which has console handler)
            )
        return logger

    def log_user_message(self, level: int, message: str, **kwargs: Any) -> None:
        """
        Log a user-facing message that appears in console with context.

        Args:
            level: Log level (logging.INFO, logging.WARNING, etc.)
            message: Message to display to user
            **kwargs: Additional context for file logs
        """
        logger = logging.getLogger("user_interface")
        logger.log(level, message, extra={"user_message": True, **kwargs})

    def log_technical_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """
        Log technical error details to file only (console gets clean message).

        Automatically sanitizes sensitive information from context before logging.

        Args:
            error: Exception that occurred
            context: Additional context information
        """
        logger = logging.getLogger("technical")
        # Item 12: Sanitize context to remove sensitive information
        extra_context = sanitize_error_context(context or {})
        # Add user_error as a simple message for console display
        error_msg = str(error)
        # Pass both as extra dict (logger will make them attributes)
        extra_context["user_error"] = error_msg
        logger.error(
            "%s",
            error_msg,  # Simple message instead of technical template
            exc_info=error,
            extra=extra_context,
        )

    def log_operation(
        self, operation: str, message: str, level: int = logging.DEBUG, **kwargs: Any
    ) -> None:
        """
        Log operation details for debugging and monitoring.

        Args:
            operation: Operation type (e.g., "download", "search", "resolve")
            message: Description of what's happening
            level: Log level (default: DEBUG for file-only)
            **kwargs: Operation-specific context
        """
        logger = logging.getLogger(f"operation.{operation}")
        logger.log(level, message, extra={"operation": operation, **kwargs})

    def shutdown(self) -> None:
        """Gracefully shutdown logging handlers."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)


# Global logger instance
_global_dual_sink: DualSinkLogger | None = None
_logger_lock = threading.Lock()


def get_dual_sink_logger() -> DualSinkLogger:
    """Get the global dual-sink logger instance (thread-safe).

    Creates the singleton instance on first call.

    Returns:
        The global DualSinkLogger instance.
    """
    global _global_dual_sink

    with _logger_lock:
        if _global_dual_sink is None:
            _global_dual_sink = DualSinkLogger()

    return _global_dual_sink


def get_logger(name: str) -> logging.Logger:
    """Get a logger with dual-sink configuration.

    Convenience function that wraps get_dual_sink_logger().get_logger().

    Args:
        name: Name for the logger.

    Returns:
        A configured logger instance.
    """
    return get_dual_sink_logger().get_logger(name)


def log_user_message(level: int, message: str, **kwargs: Any) -> None:
    """Log a user-facing message.

    Convenience function that wraps get_dual_sink_logger().log_user_message().

    Args:
        level: Log level (logging.INFO, logging.WARNING, etc.).
        message: Message to display to user.
        **kwargs: Additional context for file logs.
    """
    get_dual_sink_logger().log_user_message(level, message, **kwargs)


def log_technical_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log technical error details.

    Convenience function that wraps get_dual_sink_logger().log_technical_error().

    Args:
        error: Exception that occurred.
        context: Additional context information (will be sanitized).
    """
    get_dual_sink_logger().log_technical_error(error, context)


def log_operation(operation: str, message: str, level: int = logging.DEBUG, **kwargs: Any) -> None:
    """Log operation details.

    Convenience function that wraps get_dual_sink_logger().log_operation().

    Args:
        operation: Operation type (e.g., "download", "search", "resolve").
        message: Description of what's happening.
        level: Log level (default: DEBUG for file-only).
        **kwargs: Operation-specific context.
    """
    get_dual_sink_logger().log_operation(operation, message, level, **kwargs)


def shutdown_logging() -> None:
    """Shutdown the global dual-sink logger.

    Closes all logging handlers and clears the global instance.
    """
    global _global_dual_sink

    if _global_dual_sink is not None:
        with _logger_lock:
            if _global_dual_sink is not None:
                _global_dual_sink.shutdown()
                _global_dual_sink = None
