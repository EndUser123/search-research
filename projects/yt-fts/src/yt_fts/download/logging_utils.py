"""
Logging utilities for batch download operations.

Provides LogStream for redirecting stdout/stderr to log queues
during Rich Live display.
"""

from __future__ import annotations
import queue
from collections.abc import Callable
from datetime import datetime


class LogStream:
    """
    Helper class to redirect stdout/stderr to the log queue.

    Captures output and adds timestamps before sending to the log queue
    for display in Rich Live layout.
    """

    def __init__(self, log_queue: queue.Queue[str], callback: Callable[[str], None] | None = None):
        """
        Initialize the log stream.

        Args:
            log_queue: Queue to send log messages to
            callback: Optional callback for formatted log messages
        """
        self.log_queue = log_queue
        self.callback = callback
        self.buffer = ""

    def write(self, data: str) -> None:
        """
        Write data to the log stream.

        Args:
            data: String data to write
        """
        if not data:
            return
        self.buffer += data
        if "\n" in self.buffer:
            lines = self.buffer.split("\n")
            # All but the last element are complete lines
            for line in lines[:-1]:
                if line.strip():
                    # Add timestamp to captured stdout/stderr for clarity
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    normalized_line = (
                        line.strip().replace("[", r"\[").replace("]", r"\]")
                    )
                    msg = f"[dim][{timestamp}][/dim] {normalized_line}"
                    self.log_queue.put(msg)
                    if self.callback:
                        self.callback(msg)
            self.buffer = lines[-1]

    def flush(self) -> None:
        """
        Flush remaining buffered data to the log queue.
        """
        if self.buffer.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            normalized_line = (
                self.buffer.strip().replace("[", r"\[").replace("]", r"\]")
            )
            msg = f"[dim][{timestamp}][/dim] {normalized_line}"
            self.log_queue.put(msg)
            if self.callback:
                self.callback(msg)
            self.buffer = ""

    def isatty(self) -> bool:
        """Return False since LogStream is not a TTY."""
        return False
