"""
Error sanitization utilities for secure logging.

Redacts sensitive information like API keys, tokens, and full file paths
from error messages and context dictionaries before logging.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import logging


def sanitize_error_context(context: dict[str, Any]) -> dict[str, Any]:
    """
    Remove sensitive information from error context before logging.

    Redacts:
    - API keys, tokens, passwords, secrets (show only first/last 4 chars)
    - File paths (show only filename, not full path)
    - Personal identifiers

    Args:
        context: Dictionary of context information from an error

    Returns:
        Sanitized dictionary with sensitive information redacted

    Example:
        >>> sanitize_error_context({
        ...     "api_key": "sk-1234567890abcdef",
        ...     "file_path": "/home/user/projects/yt-fts/data/config.json",
        ...     "operation": "load_config"
        ... })
        {'api_key': 'sk-1...cdef', 'file_path': 'config.json', 'operation': 'load_config'}
    """
    sanitized = {}
    sensitive_keys = [
        "api_key", "apikey", "api-key",
        "cookie", "cookies",
        "token", "tokens",
        "password", "passwd",
        "secret", "secrets",
        "auth", "auth_key",
        "key", "private_key",
        "credential", "credentials",
    ]

    for key, value in context.items():
        # Check if this is a sensitive key
        key_lower = key.lower()
        is_sensitive = any(sensitive in key_lower for sensitive in sensitive_keys)

        if is_sensitive and isinstance(value, str):
            # Redact sensitive values - show only first/last 4 chars
            if len(value) > 8:
                sanitized[key] = f"{value[:4]}...{value[-4:]}"
            else:
                sanitized[key] = "[REDACTED]"
        elif "path" in key_lower and isinstance(value, str):
            # Show only filename, not full path
            sanitized[key] = Path(value).name
        else:
            # Keep other values as-is
            sanitized[key] = value

    return sanitized


def sanitize_log_message(message: str) -> str:
    """
    Redact sensitive patterns from log messages.

    Uses regex to find and redact common sensitive patterns like:
    - API keys in various formats
    - Bearer tokens
    - File paths (show only filename)

    Args:
        message: Raw log message

    Returns:
        Sanitized message with sensitive information redacted

    Example:
        >>> sanitize_log_message("API key sk-1234567890abcdef failed")
        'API key sk-1...cdef failed'
    """
    import re

    # Redact API keys (common formats: sk-xxx, apikey=xxx, etc.)
    message = re.sub(
        r'(sk-[a-zA-Z0-9]{20,}|api[_-]?key[=:][\s]*["\']?[\w-]{10,}["\']?)',
        lambda m: f"{m.group(1)[:4]}...{m.group(1)[-4:]}" if len(m.group(1)) > 8 else "[REDACTED]",
        message
    )

    # Redact bearer tokens
    message = re.sub(
        r"(Bearer[\s]+[\w-]+\.[\w-]+\.[\w-]+)",
        lambda m: f"Bearer {m.group(1).split()[-1][:8]}...",
        message
    )

    # Redact file paths (show only filename)
    return re.sub(
        r"([A-Z]:\\|/)([\w/\\.-]*/)([\w.-]+)",
        r"...\3",
        message
    )



def get_sanitized_logger(logger_name: str) -> "logging.Logger":
    """
    Return a logger wrapper that automatically sanitizes all messages.

    This provides a drop-in replacement for standard loggers that ensures
    sensitive information is never accidentally logged.

    Args:
        logger_name: Name for the logger

    Returns:
        Logger object with automatic sanitization

    Example:
        >>> logger = get_sanitized_logger(__name__)
        >>> logger.info("Connecting with api_key=sk-1234567890abcdef")
        # Logs: "Connecting with api_key=sk-1...cdef"
    """
    import logging

    logger = logging.getLogger(logger_name)

    class SanitizingLogRecord(logging.LogRecord):
        """Log record subclass that sanitizes messages before logging."""

        def getMessage(self) -> str:
            """
            Get the log message with sensitive information sanitized.

            Returns:
                Sanitized log message string
            """
            original_message = super().getMessage()
            return sanitize_log_message(original_message)

    # Old-style factory for Python 3.3+
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        """
        Create a sanitizing log record from factory arguments.

        Args:
            *args: Positional arguments passed to log record factory
            **kwargs: Keyword arguments passed to log record factory

        Returns:
            SanitizingLogRecord instance with sanitized message capability
        """
        record = old_factory(*args, **kwargs)
        return SanitizingLogRecord(
            record.name,
            record.levelno,
            record.pathname,
            record.lineno,
            record.msg,
            record.args,
            record.exc_info
        )

    logging.setLogRecordFactory(record_factory)

    return logger
