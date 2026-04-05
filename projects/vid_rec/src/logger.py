# --- INTEGRITY ---
# Previous Character Count: 5503
# Current Character Count: 5400
# Syntax Check: [PASS]
# Logic Validation: [Removed logging call from add_dashboard_handler to prevent UI conflicts.]
# Reason for Change: [To fix an immediate crash caused by a log message conflicting with rich.Live initialization.]
# ------------------
# --- METADATA ---
# Filename: src/logger.py
# Version: 4.2
#
# --- CHANGELOG ---
# v4.2: BUGFIX: Removed the logging statement from `add_dashboard_handler` to
#       prevent a race condition with rich.Live's console takeover.
# v4.1: BUGFIX: Removed the logging statement from `toggle_console_logs`.
# ------------------

import logging
import logging.config
import os
import sys  # Import sys for critical error logging
from collections import deque
from typing import Optional

import structlog
from rich.markup import escape as rich_escape  # Import escape function and alias it

SHOW_CONSOLE_LOGS = True
_logging_initialized = False


class DisplayFilter(logging.Filter):
    def filter(self, record):
        return SHOW_CONSOLE_LOGS


class ExcludeUILogsFilter(logging.Filter):
    """
    A filter to exclude logs from 'vidrec.ui' logger.
    """

    def filter(self, record):
        return not record.name.startswith("vidrec.ui")


def toggle_console_logs(show: Optional[bool] = None) -> bool:
    global SHOW_CONSOLE_LOGS
    if show is None:
        SHOW_CONSOLE_LOGS = not SHOW_CONSOLE_LOGS
    else:
        SHOW_CONSOLE_LOGS = show
    return SHOW_CONSOLE_LOGS


class RichTextRenderer:
    """
    A structlog renderer to format log entries into Rich-compatible strings.
    This is used by the DashboardLogHandler's ProcessorFormatter.
    """

    # Removed _console from __init__ as it's not needed for rendering a string
    def __call__(self, logger, name, event_dict):
        # Escape all values to ensure they don't break Rich markup
        # Note: event_dict is already a copy from ProcessorFormatter's internal handling
        escaped_event_dict = {k: rich_escape(str(v)) for k, v in event_dict.items()}

        timestamp = (
            escaped_event_dict.get("timestamp", "").split("T")[1].split(".")[0]
            if "timestamp" in escaped_event_dict
            else ""
        )
        level = escaped_event_dict.get("level", "").upper()
        event = escaped_event_dict.get("event", "")
        category = escaped_event_dict.get("category", "")
        component = escaped_event_dict.get("component", "")
        file_name = escaped_event_dict.get("file_name", "")
        job_id = escaped_event_dict.get("job_id", "")
        error = escaped_event_dict.get("error", "")
        run_id = escaped_event_dict.get("run_id", "")
        message = escaped_event_dict.get("message", "")  # For non-event logs

        parts = []
        if timestamp:
            parts.append(f"[dim]{timestamp}[/dim]")
        if level:
            parts.append(f"[{level.lower()}]{level:<7}[/]")
        if category:
            parts.append(f"[cyan]{category}[/cyan]")
        if event:
            parts.append(f"[white]{event}[/white]")
        elif message:  # Fallback for generic messages
            parts.append(f"[white]{message}[/white]")
        if component:
            parts.append(f"(from [yellow]{component}[/yellow])")
        if file_name:
            parts.append(f"File: [magenta]{file_name}[/magenta]")
        if job_id:
            parts.append(f"Job: [blue]{job_id}[/blue]")
        if error:
            parts.append(f"[red]Error: {error}[/red]")
        if run_id and "run_id" in event_dict:  # Only show if explicitly in event_dict
            parts.append(f"[dim]Run ID: {run_id}[/dim]")

        formatted_log = " ".join(parts)
        return formatted_log


def configure_structlog():
    # Define shared processors for both structlog and stdlib logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # Merge context variables first
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Configure structlog with proper processor chain
    structlog.configure(
        processors=shared_processors
        + [
            # RichTextRenderer is NOT part of the global chain.
            # It's used by DashboardLogHandler's own formatter.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Note: shared_processors is returned, but configure_structlog is only called once
    # and its main purpose is to configure the global structlog processors.
    # The list below is duplicated in get_logging_config_dict for specific formatters.
    return shared_processors


class DashboardLogHandler(logging.Handler):
    def __init__(self, messages_deque: deque[str]):
        super().__init__()
        self.messages_deque = messages_deque
        self.renderer = RichTextRenderer()  # Instantiate the renderer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Filter out repetitive 'Dashboard updated' messages from the UI
            if (
                isinstance(record.msg, dict)
                and record.msg.get("event") == "Dashboard updated"
                and record.msg.get("category") == "ui"
            ):
                return

            # record.msg will be the event dictionary because this handler is added
            # before structlog.stdlib.ProcessorFormatter.wrap_for_formatter has a chance
            # to convert it to a string for this specific handler.
            formatted_message = self.renderer(
                None, None, record.msg
            )  # Pass event_dict directly to renderer
            self.messages_deque.append(formatted_message)
        except Exception as e:
            # Fallback for any errors during formatting, append raw message
            self.messages_deque.append(
                f"[red]Error formatting log: {rich_escape(str(e))}[/red] [dim]{record.getMessage()}[/dim]"
            )
            # Log to stderr as well, as this is a critical logging system error
            print(
                f"CRITICAL LOGGING ERROR in DashboardLogHandler: {e}", file=sys.stderr
            )
            print(f"Original record: {record.__dict__}", file=sys.stderr)


def get_logging_config_dict(log_level: str, log_file: str):
    # configure_structlog is called implicitly by structlog.get_logger
    # when the first logger is created, but we call it explicitly here
    # to ensure the processors are set up before any loggers are used.
    # We remove the explicit call here as it's handled by setup_logging.
    # configure_structlog() # Removed explicit call

    # Re-obtain shared_processors here for clarity and to ensure correct chain for formatters
    shared_processors_for_formatters = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console_formatter": {
                "()": "structlog.stdlib.ProcessorFormatter",
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": [
                    structlog.stdlib.ExtraAdder(),
                ]
                + shared_processors_for_formatters,
            },
            "json_formatter": {
                "()": "structlog.stdlib.ProcessorFormatter",
                "processor": structlog.processors.JSONRenderer(
                    sort_keys=False, ensure_ascii=False
                ),
                "foreign_pre_chain": [
                    structlog.stdlib.ExtraAdder(),
                ]
                + shared_processors_for_formatters,
            },
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "mode": "w",
                "formatter": "json_formatter",
                "filename": log_file,
                "encoding": "utf-8",
                "filters": ["exclude_ui_logs_filter"],  # Apply the new filter
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console_formatter",
                "level": log_level,
                "filters": ["display_filter"],
            },
        },
        "filters": {  # Define the filters
            "display_filter": {"()": "src.logger.DisplayFilter"},
            "exclude_ui_logs_filter": {"()": "src.logger.ExcludeUILogsFilter"},
        },
        "loggers": {
            "": {
                "handlers": ["file", "console"],
                "level": log_level,
                "propagate": True,
            },
            "vidrec.ui": {
                "handlers": ["file", "console"],
                "level": "CRITICAL",
                "propagate": False,
            },  # Keep level high and propagate false for safety
            "src.state_manager": {"level": "WARNING", "propagate": False},
            "faster_whisper": {"level": "INFO", "propagate": False},
            "pynput": {"level": "WARNING"},
            "h5py": {"level": "WARNING"},
            "numba": {"level": "WARNING"},
            "PIL": {"level": "WARNING"},
            "matplotlib": {"level": "WARNING"},
        },
    }


def setup_logging(log_level: str = "INFO", log_file: str = "logs/vidrec.json"):
    global _logging_initialized
    if _logging_initialized:
        return

    # Ensure structlog is configured globally before any logging handlers are set up
    configure_structlog()

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    abs_log_file = os.path.abspath(log_file)
    print(f"Log file will be written to: {abs_log_file}")

    config_dict = get_logging_config_dict(log_level, abs_log_file)
    logging.config.dictConfig(config_dict)
    _logging_initialized = True
    log = structlog.get_logger("vidrec.logger")
    log.info("Logging configured", log_level=log_level, log_file=abs_log_file)


def add_dashboard_handler(dashboard_deque: deque[str], log_level: str = "INFO"):
    root_logger = logging.getLogger()
    has_dashboard_handler = any(
        isinstance(h, DashboardLogHandler) for h in root_logger.handlers
    )
    if not has_dashboard_handler:
        dashboard_handler = DashboardLogHandler(dashboard_deque)
        dashboard_handler.setLevel(log_level.upper())
        root_logger.addHandler(dashboard_handler)
        # This function must be silent to avoid race conditions with UI toolkits.


def shutdown_logging():
    log = structlog.get_logger("vidrec.logger")
    log.info("Shutting down logging system.")
    logging.shutdown()
