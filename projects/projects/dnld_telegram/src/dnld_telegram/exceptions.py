"""
Domain-specific exceptions for dnld_telegram.

This module provides specific exception classes to replace generic ValueError usage
throughout the codebase, enabling better error handling and categorization.
"""

import asyncio


class DnldTelegramError(Exception):
    """Base exception for all dnld_telegram specific errors."""

    pass


class ConfigurationError(DnldTelegramError):
    """Raised when configuration parsing or validation fails."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_file: str | None = None,
    ):
        self.config_key = config_key
        self.config_file = config_file
        super().__init__(message)


class ValidationError(DnldTelegramError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, field_name: str | None = None, invalid_value=None
    ):
        self.field_name = field_name
        self.invalid_value = invalid_value
        super().__init__(message)


class ConnectionError(DnldTelegramError):
    """Raised when connection operations fail."""

    def __init__(
        self, message: str, operation: str | None = None, retry_possible: bool = True
    ):
        self.operation = operation
        self.retry_possible = retry_possible
        super().__init__(message)


class UILoadError(DnldTelegramError):
    """Raised when UI components fail to load or initialize."""

    def __init__(
        self,
        message: str,
        ui_type: str | None = None,
        fallback_available: bool = True,
    ):
        self.ui_type = ui_type
        self.fallback_available = fallback_available
        super().__init__(message)


class ParsingError(DnldTelegramError):
    """Raised when parsing operations fail (dates, formats, etc.)."""

    def __init__(self, message: str, parse_type: str | None = None, raw_value=None):
        self.parse_type = parse_type
        self.raw_value = raw_value
        super().__init__(message)


class FileSystemError(DnldTelegramError):
    """Raised when filesystem operations fail in unexpected ways."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
    ):
        self.file_path = file_path
        self.operation = operation
        super().__init__(message)


class ProcessManagementError(DnldTelegramError):
    """Raised when process management operations fail."""

    def __init__(
        self, message: str, pid: int | None = None, operation: str | None = None
    ):
        self.pid = pid
        self.operation = operation
        super().__init__(message)


def categorize_system_error(error: Exception, operation_context: str = "") -> str:
    """
    Categorize system errors for consistent handling.

    Args:
        error: The exception to categorize
        operation_context: Context about what operation was being performed

    Returns:
        str: Error category for handling decisions
    """
    error_msg = str(error).lower()
    type(error).__name__

    # File system related errors
    if isinstance(error, (OSError, IOError, PermissionError)):
        if "permission denied" in error_msg:
            return "permission"
        elif "file not found" in error_msg or "no such file" in error_msg:
            return "file_not_found"
        elif "disk" in error_msg or "space" in error_msg:
            return "disk_space"
        else:
            return "filesystem"

    # Import/module errors
    elif isinstance(error, (ImportError, ModuleNotFoundError)):
        return "import"

    # Network/connection errors
    elif isinstance(error, (ConnectionError, asyncio.TimeoutError)):
        return "network"

    # Parsing errors
    elif isinstance(error, ValueError):
        if "date" in error_msg or "time" in error_msg:
            return "date_parsing"
        elif "invalid literal" in error_msg:
            return "number_parsing"
        elif "connection" in error_msg or "disconnected" in error_msg:
            return "connection"
        else:
            return "validation"

    # Type errors
    elif isinstance(error, TypeError):
        return "type_mismatch"

    # Unknown
    else:
        return "unknown"


def should_retry_error(error_category: str, attempt: int = 1) -> tuple[bool, float]:
    """
    Determine if an error should be retried and with what delay.

    Args:
        error_category: Category from categorize_system_error()
        attempt: Current attempt number

    Returns:
        tuple: (should_retry, delay_seconds)
    """
    if error_category in ["network", "connection"] and attempt < 3:
        return True, min(2.0 * attempt, 10.0)
    elif error_category == "filesystem" and attempt < 2:
        return True, 1.0
    elif error_category in ["permission", "file_not_found", "import", "validation"]:
        return False, 0.0  # Don't retry these
    else:
        return False, 0.0
