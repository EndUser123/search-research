"""
TUI-specific logging components for the YouTube Sync application.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TUILogHandler(logging.Handler):
    """Enhanced logging handler for TUI applications."""

    def __init__(self, app: Any):
        super().__init__()
        self.app = app
        self.current_channel = None
        self.app_running = True

    def emit(self, record):
        """Emit a log record to the TUI."""
        if not self.app_running or self.app.is_shutting_down:
            return

        try:
            msg = self.format(record)
            level = record.levelname

            self.app.log_store.add_log(msg, level, self.current_channel)

            if self.app.is_running:
                if "MB/s" in msg or "progress" in msg.lower():
                    self.app.call_from_thread(
                        self.app.performance_log.write_line, f"⚡ {msg}"
                    )

                icon = "🚨" if level == "ERROR" else "⚠️" if level == "WARNING" else "ℹ️"
                self.app.call_from_thread(
                    self.app.smart_log.write_line, f"{icon} {msg}"
                )
        except Exception:
            pass

    def set_current_channel(self, channel_name: str):
        """Set the current channel for logging context."""
        self.current_channel = channel_name

    def shutdown(self):
        """Shutdown the handler."""
        self.app_running = False


class TUILogger:
    """Manages TUI-specific logging setup and handlers."""

    def __init__(self, app: Any):
        self.app = app
        self.log_handler: TUILogHandler | None = None

    def setup_logging(self):
        """Set up enhanced logging for the TUI."""
        try:
            smart_log = self.app.query_one("#smart-log")
            performance_log = self.app.query_one("#performance-log")

            self.log_handler = TUILogHandler(self.app)
            formatter = logging.Formatter("[%(levelname)s] %(message)s")
            self.log_handler.setFormatter(formatter)

            root_logger = logging.getLogger()
            root_logger.addHandler(self.log_handler)

        except Exception:
            pass

    def set_current_channel(self, channel_name: str):
        """Set current channel for logging context."""
        if self.log_handler:
            self.log_handler.set_current_channel(channel_name)

    def shutdown(self):
        """Clean up logging resources."""
        if self.log_handler:
            self.log_handler.shutdown()
            root_logger = logging.getLogger()
            if self.log_handler in root_logger.handlers:
                root_logger.removeHandler(self.log_handler)
