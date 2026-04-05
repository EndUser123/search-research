# yt_sync/logging_config.py

import logging
import queue
import sys
from logging.handlers import RotatingFileHandler

import structlog
from structlog.contextvars import merge_contextvars


class TUIQueueHandler(logging.Handler):
    """Custom handler that puts structured log data onto a queue for TUI consumption."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            if isinstance(record.msg, dict):
                self.log_queue.put(record.msg)
        except Exception:
            self.handleError(record)


class ErrorAnalysisHandler(logging.Handler):
    """Collects structured error data for programmatic analysis and reporting."""

    def __init__(self):
        super().__init__()
        self.errors: list = []

    def emit(self, record):
        if isinstance(record.msg, dict) and record.levelno >= logging.WARNING:
            self.errors.append(record.msg)

    def get_errors_for_channel(self, channel_id: str) -> list:
        return [e for e in self.errors if e.get("channel_id") == channel_id]

    def clear_channel_errors(self, channel_id: str):
        self.errors = [e for e in self.errors if e.get("channel_id") != channel_id]


def setup_logging(log_level: str = "INFO", tui_enabled: bool = False):
    """
    Configures the entire logging architecture using structlog.
    Returns the error handler for programmatic access.
    """
    # --- FIX: Detect if running under pytest and disable file logging ---
    is_testing = "pytest" in sys.modules
    # This is the full processor chain for logs originating from structlog
    shared_processors = [
        merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # The final processor in this chain is the one that renders the log record.
        # For stdlib compatibility, this is always ProcessorFormatter.
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure(
        processors=shared_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # This processor chain is for logs originating from the standard library
    # It will be used by the formatters for our handlers.
    [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(
            colors=True, exception_formatter=structlog.dev.plain_traceback
        ),
    ]

    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.setLevel(log_level.upper())

    if not tui_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=True)
            )
        )
        root_logger.addHandler(console_handler)

    # Ensure the logs directory exists
    from pathlib import Path

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Clear previous log file for a clean run
    log_file_path = logs_dir / "yt_sync_structured.log"
    if log_file_path.exists():
        log_file_path.unlink()

    # Only set up file logging if NOT in a test session
    if not is_testing:
        # Use a rotating file handler for robust, production-grade logging.
        # This prevents the log file from growing indefinitely during a single session.
        json_file_handler = RotatingFileHandler(
            log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        json_file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
            )
        )

        human_log_file_path = logs_dir / "yt_sync_human.log"
        human_file_handler = RotatingFileHandler(
            human_log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        human_file_handler.setLevel(
            log_level.upper()
        )  # Set the level for the file handler
        human_file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                # Use ConsoleRenderer with colors=False for a clean, timestamped text log
                processor=structlog.dev.ConsoleRenderer(colors=False)
            )
        )
        root_logger.addHandler(json_file_handler)
        root_logger.addHandler(human_file_handler)

    # Silence the noisy "file_cache is only supported with oauth2client<4.0.0" warning
    # from the Google API client library, as it's not relevant to our implementation.
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

    # We will create and return the error handler separately if needed,
    # but for now, we focus on fixing the core logging.
    return None
