"""
Unified Error Handler

Consistent error handling across all yt-fts components.
Replaces direct system exit calls with proper exception handling and provides
structured error logging and user-friendly error messages.

Author: CSF NIP Implementation Team
Version: 1.0.0
"""
import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better handling"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    PROCESSING = "processing"
    SYSTEM = "system"
    USER_INPUT = "user_input"

@dataclass
class ErrorResult:
    """Result of error handling operation"""
    success: bool
    error_message: str
    error_code: str | None = None
    category: ErrorCategory | None = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    suggestions: list[str] | None = None
    should_retry: bool = False
    retry_delay: float = 0.0

@dataclass
class RetryConfig:
    """Configuration for retry operations"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class ChannelProcessingError(Exception):
    """Custom exception for channel processing errors"""

    def __init__(self, message: str, error_code: str | None=None, category: ErrorCategory=ErrorCategory.PROCESSING, severity: ErrorSeverity=ErrorSeverity.MEDIUM, recoverable: bool=True, suggestions: list[str] | None=None):
        """Initialize a ChannelProcessingError.

        Args:
            message: The error message describing what went wrong.
            error_code: Optional error code for categorization.
            category: The error category. Defaults to PROCESSING.
            severity: The error severity. Defaults to MEDIUM.
            recoverable: Whether the error is recoverable. Defaults to True.
            suggestions: Optional list of suggestions for resolving the error.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.suggestions = suggestions or []

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging.

        Returns:
            dict[str, Any]: Dictionary representation of the exception including
                type, message, error_code, category, severity, recoverable, and suggestions.
        """
        return {"type": self.__class__.__name__, "message": self.message, "error_code": self.error_code, "category": self.category.value, "severity": self.severity.value, "recoverable": self.recoverable, "suggestions": self.suggestions}

class UnifiedErrorHandler:
    """
    Unified error handling for all yt-fts components.

    Provides consistent error handling, logging, and retry mechanisms
    to replace direct system exit calls and improve user experience.
    """

    def __init__(self, logger: logging.Logger | None=None):
        """
        Initialize the Unified Error Handler.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats = {"total_errors": 0, "errors_by_category": {}, "errors_by_severity": {}, "retry_attempts": 0, "successful_retries": 0}
        self.error_patterns = {ErrorCategory.NETWORK: ["connection", "timeout", "network", "dns", "http", "url", "requests", "socket", "ssl", "certificate"], ErrorCategory.AUTHENTICATION: ["auth", "login", "credential", "token", "permission", "forbidden", "unauthorized", "401", "403"], ErrorCategory.VALIDATION: ["invalid", "malformed", "missing", "required", "format", "syntax", "parse", "validation"], ErrorCategory.PROCESSING: ["processing", "resolution", "extraction", "parsing", "conversion", "transform"], ErrorCategory.SYSTEM: ["memory", "disk", "file", "permission", "os", "system", "runtime", "exception"], ErrorCategory.USER_INPUT: ["input", "parameter", "argument", "option", "command"]}
        self.logger.debug("UnifiedErrorHandler initialized")

    def handle_channel_error(self, error: Exception, context: str, input_value: str | None=None) -> ErrorResult:
        """
        Handle channel processing errors consistently.

        Args:
            error: The exception that occurred
            context: Context where the error occurred
            input_value: Optional input value that caused the error

        Returns:
            ErrorResult: Structured error handling result
        """
        try:
            category = self._categorize_error(error)
            severity = self._determine_severity(error, category)
            error_message = self._generate_error_message(error, context, input_value)
            suggestions = self._generate_suggestions(error, category, input_value)
            should_retry = self._should_retry(error, category)
            self._update_error_stats(category, severity)
            self._log_error(error, context, category, severity, input_value)
            retry_delay = self._calculate_retry_delay(error, category)
            error_result = ErrorResult(success=False, error_message=error_message, error_code=getattr(error, "error_code", None), category=category, severity=severity, suggestions=suggestions, should_retry=should_retry, retry_delay=retry_delay)
            self.logger.debug("Generated error result: %s", error_result)
            return error_result
        except Exception as e:
            self.logger.exception("Error in error handler: %s", e)
            return ErrorResult(success=False, error_message=f"Error handling failed: {error!s}", category=ErrorCategory.SYSTEM, severity=ErrorSeverity.CRITICAL)

    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an operation should be retried.

        Args:
            error: The exception that occurred

        Returns:
            bool: True if retry is recommended
        """
        category = self._categorize_error(error)
        return self._should_retry(error, category)

    async def retry_operation(self, operation: Callable, *args, config: RetryConfig | None=None, **kwargs) -> Any:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: The operation to retry
            *args: Arguments to pass to the operation
            config: Retry configuration
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            Any: Result of the operation

        Raises:
            Exception: The last exception if all retries fail
        """
        if config is None:
            config = RetryConfig()
        last_exception = None
        for attempt in range(config.max_attempts):
            try:
                if attempt > 0:
                    delay = self._calculate_retry_delay(last_exception, self._categorize_error(last_exception) if last_exception else None, attempt, config)
                    self.logger.info("Retrying operation in %ss (attempt %s/%s)", delay, attempt + 1, config.max_attempts)
                    await asyncio.sleep(delay)
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                if attempt > 0:
                    self.error_stats["successful_retries"] += 1
                    self.logger.info("Operation succeeded on attempt %s", attempt + 1)
                return result
            except Exception as e:
                last_exception = e
                self.error_stats["retry_attempts"] += 1
                category = self._categorize_error(e)
                if not self._should_retry(e, category):
                    self.logger.warning("Error not retryable: %s", e)
                    break
                self.logger.warning("Attempt %s failed: %s", attempt + 1, e)
        self.logger.error("Operation failed after %s attempts", config.max_attempts)
        raise last_exception

    def log_error(self, error: Exception, context: dict[str, Any]):
        """
        Log structured error information.

        Args:
            error: The exception to log
            context: Context information as a dictionary
        """
        try:
            category = self._categorize_error(error)
            severity = self._determine_severity(error, category)
            log_data = {"error_type": error.__class__.__name__, "error_message": str(error), "category": category.value, "severity": severity.value, "context": context, "timestamp": time.time()}
            if isinstance(error, ChannelProcessingError):
                log_data.update(error.to_dict())
            if severity == ErrorSeverity.CRITICAL:
                self.logger.critical("Critical error: %s", log_data)
            elif severity == ErrorSeverity.HIGH:
                self.logger.error("High severity error: %s", log_data)
            elif severity == ErrorSeverity.MEDIUM:
                self.logger.warning("Medium severity error: %s", log_data)
            else:
                self.logger.info("Low severity error: %s", log_data)
        except Exception as e:
            self.logger.exception("Failed to log error: %s", e)

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its message and type.

        Args:
            error: The exception to categorize.

        Returns:
            ErrorCategory: The category that best describes the error.
        """
        error_message = str(error).lower()
        error_type = error.__class__.__name__.lower()
        if any(keyword in error_type for keyword in ["connection", "request", "http"]):
            return ErrorCategory.NETWORK
        if any(keyword in error_type for keyword in ["value", "type", "attribute"]):
            return ErrorCategory.VALIDATION
        for category, patterns in self.error_patterns.items():
            if any(pattern in error_message for pattern in patterns):
                return category
        return ErrorCategory.PROCESSING

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on type and category.

        Args:
            error: The exception to evaluate.
            category: The category the error belongs to.

        Returns:
            ErrorSeverity: The severity level of the error.
        """
        if any(keyword in str(error).lower() for keyword in ["critical", "fatal", "system"]):
            return ErrorSeverity.CRITICAL
        if category in [ErrorCategory.SYSTEM, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH
        if category in [ErrorCategory.NETWORK, ErrorCategory.PROCESSING]:
            return ErrorSeverity.MEDIUM
        return ErrorSeverity.LOW

    def _generate_error_message(self, error: Exception, context: str, input_value: str | None=None) -> str:
        """Generate user-friendly error message.

        Args:
            error: The exception that occurred.
            context: Context where the error occurred.
            input_value: Optional input value that caused the error.

        Returns:
            str: A user-friendly error message with context.
        """
        base_message = f"Error in {context}: {error!s}"
        if input_value:
            base_message = f"Error processing '{input_value}' in {context}: {error!s}"
        if isinstance(error, ChannelProcessingError):
            base_message = error.message
        elif "timeout" in str(error).lower():
            base_message += " (operation timed out)"
        elif "connection" in str(error).lower():
            base_message += " (connection issue)"
        return base_message

    def _generate_suggestions(self, error: Exception, category: ErrorCategory, input_value: str | None=None) -> list[str]:
        """Generate helpful suggestions based on error type and category.

        Args:
            error: The exception that occurred.
            category: The category the error belongs to.
            input_value: Optional input value that caused the error.

        Returns:
            list[str]: List of helpful suggestions for resolving the error.
        """
        suggestions = []
        if category == ErrorCategory.NETWORK:
            suggestions.extend(["Check your internet connection", "Try again in a few moments", "Verify the channel URL is accessible"])
        elif category == ErrorCategory.AUTHENTICATION:
            suggestions.extend(["Check your API credentials", "Verify your authentication tokens", "Try refreshing your credentials"])
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend(["Check the input format", "Verify all required fields are provided", "Ensure the channel identifier is valid"])
        elif category == ErrorCategory.PROCESSING:
            suggestions.extend(["Try using a different channel identifier", "Check if the channel is publicly accessible", "Try with a simpler input format"])
        elif category == ErrorCategory.USER_INPUT:
            suggestions.extend(["Check the command syntax", "Verify the input parameters", "Use --help for usage information"])
        if input_value:
            if input_value.startswith("@"):
                suggestions.append("Try the channel's full URL instead")
            elif input_value.startswith("http"):
                suggestions.append("Try the channel's @handle instead")
            else:
                suggestions.append("Try using the channel's @handle or full URL")
        return suggestions[:4]

    def _should_retry(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if an error is retryable.

        Args:
            error: The exception to evaluate.
            category: The category the error belongs to.

        Returns:
            bool: True if the operation should be retried, False otherwise.
        """
        if category in [ErrorCategory.VALIDATION, ErrorCategory.USER_INPUT]:
            return False
        if category in [ErrorCategory.NETWORK, ErrorCategory.PROCESSING]:
            return True
        error_message = str(error).lower()
        no_retry_patterns = ["not found", "forbidden", "unauthorized", "permission denied", "invalid", "malformed", "authentication failed"]
        return not any(pattern in error_message for pattern in no_retry_patterns)

    def _calculate_retry_delay(self, error: Exception, category: ErrorCategory | None=None, attempt: int=0, config: RetryConfig | None=None) -> float:
        """Calculate delay before retry.

        Args:
            error: The exception that occurred.
            category: The category the error belongs to.
            attempt: The current retry attempt number.
            config: Optional retry configuration.

        Returns:
            float: The delay in seconds before the next retry.
        """
        if config is None:
            config = RetryConfig()
        delay = config.base_delay * config.exponential_base ** attempt
        delay = min(delay, config.max_delay)
        if config.jitter:
            import random
            jitter_factor = 0.1 * delay
            delay += random.uniform(-jitter_factor, jitter_factor)
        return max(0, delay)

    def _update_error_stats(self, category: ErrorCategory, severity: ErrorSeverity):
        """Update error statistics.

        Args:
            category: The category of the error.
            severity: The severity level of the error.
        """
        self.error_stats["total_errors"] += 1
        category_name = category.value
        severity_name = severity.value
        self.error_stats["errors_by_category"][category_name] = self.error_stats["errors_by_category"].get(category_name, 0) + 1
        self.error_stats["errors_by_severity"][severity_name] = self.error_stats["errors_by_severity"].get(severity_name, 0) + 1

    def _log_error(self, error: Exception, context: str, category: ErrorCategory, severity: ErrorSeverity, input_value: str | None=None):
        """Log error with structured information.

        Args:
            error: The exception to log.
            context: Context where the error occurred.
            category: The category the error belongs to.
            severity: The severity level of the error.
            input_value: Optional input value that caused the error.
        """
        log_data = {"error_type": error.__class__.__name__, "error_message": str(error), "context": context, "category": category.value, "severity": severity.value, "timestamp": time.time()}
        if input_value:
            log_data["input_value"] = input_value
        if isinstance(error, ChannelProcessingError):
            log_data.update(error.to_dict())
        log_message = f"Error in {context}: {error!s}"
        if input_value:
            log_message = f"Error processing '{input_value}' in {context}: {error!s}"
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical("%s | Details: %s", log_message, log_data)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error("%s | Details: %s", log_message, log_data)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning("%s | Details: %s", log_message, log_data)
        else:
            self.logger.info("%s | Details: %s", log_message, log_data)

    def get_statistics(self) -> dict[str, Any]:
        """Get error handling statistics.

        Returns:
            dict[str, Any]: Dictionary containing error statistics including
                total_errors, errors_by_category, errors_by_severity,
                retry_attempts, successful_retries, and retry_success_rate.
        """
        return {**self.error_stats, "retry_success_rate": self.error_stats["successful_retries"] / max(self.error_stats["retry_attempts"], 1) * 100 if self.error_stats["retry_attempts"] > 0 else 0.0}

    def reset_statistics(self) -> None:
        """Reset error statistics.

        Resets all error counters including total_errors, errors_by_category,
        errors_by_severity, retry_attempts, and successful_retries to zero.
        """
        self.error_stats = {"total_errors": 0, "errors_by_category": {}, "errors_by_severity": {}, "retry_attempts": 0, "successful_retries": 0}

def create_channel_error(message: str, error_code: str | None=None, category: ErrorCategory=ErrorCategory.PROCESSING, severity: ErrorSeverity=ErrorSeverity.MEDIUM, suggestions: list[str] | None=None) -> ChannelProcessingError:
    """Create a ChannelProcessingError with sensible defaults.

    Args:
        message: The error message describing what went wrong.
        error_code: Optional error code for categorization.
        category: The error category. Defaults to PROCESSING.
        severity: The error severity. Defaults to MEDIUM.
        suggestions: Optional list of suggestions for resolving the error.

    Returns:
        ChannelProcessingError: A configured exception instance.
    """
    return ChannelProcessingError(message=message, error_code=error_code, category=category, severity=severity, recoverable=True, suggestions=suggestions)

def create_error_handler_for_cli() -> UnifiedErrorHandler:
    """Create an error handler instance optimized for CLI usage.

    Configures logging for CLI output if not already configured, preventing
    interference with existing Rich or DownloadHandler logging.

    Returns:
        UnifiedErrorHandler: A configured error handler instance ready for CLI use.
    """
    import sys
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stderr)
    return UnifiedErrorHandler()
