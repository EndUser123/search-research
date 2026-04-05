"""
Error recovery manager for batch downloads with intelligent retry strategies.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur during batch downloads."""

    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    QUOTA_EXCEEDED = "quota_exceeded"
    RESOURCE_NOT_FOUND = "resource_not_found"
    TEMPORARY_FAILURE = "temporary_failure"
    PERMANENT_FAILURE = "permanent_failure"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    SKIP_AND_CONTINUE = "skip_and_continue"
    FAIL_FAST = "fail_fast"
    WAIT_AND_RETRY = "wait_and_retry"
    MANUAL_INTERVENTION = "manual_intervention"


class ErrorRecoveryManager:
    """
    Intelligent error recovery manager for batch download operations.

    Provides context-aware error classification and recovery strategies
    to maximize download success rates while respecting rate limits.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 300.0,
        continue_on_error: bool = True,
    ):
        """
        Initialize the error recovery manager.

        Args:
            max_retries: Maximum number of retry attempts
            base_backoff_seconds: Base delay for exponential backoff
            max_backoff_seconds: Maximum delay between retries
            continue_on_error: Whether to continue processing other items on error
        """
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds
        self.max_backoff = max_backoff_seconds
        self.continue_on_error = continue_on_error

        # Track error patterns for adaptive behavior
        self.error_counts: dict[str, int] = {}
        self.last_error_time: dict[str, float] = {}

    def classify_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> ErrorCategory:
        """
        Classify an error into a category for appropriate handling.

        Args:
            error: The exception that occurred
            context: Additional context about the operation

        Returns:
            ErrorCategory: The classified error category
        """
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network-related errors
        if any(
            keyword in error_msg
            for keyword in [
                "connection",
                "timeout",
                "network",
                "dns",
                "ssl",
                "certificate",
                "connection reset",
                "connection refused",
                "connection aborted",
            ]
        ) or any(keyword in error_type for keyword in ["timeout", "connection"]):
            return ErrorCategory.NETWORK

        # Rate limiting errors
        if any(
            keyword in error_msg
            for keyword in [
                "rate limit",
                "too many requests",
                "quota exceeded",
                "429",
                "temporary ban",
                "blocked",
                "throttled",
            ]
        ):
            return ErrorCategory.RATE_LIMIT

        # Authentication errors
        if any(
            keyword in error_msg
            for keyword in [
                "unauthorized",
                "forbidden",
                "authentication",
                "login",
                "credentials",
                "401",
                "403",
                "invalid api key",
            ]
        ):
            return ErrorCategory.AUTHENTICATION

        # Resource not found
        if any(
            keyword in error_msg
            for keyword in [
                "not found",
                "404",
                "does not exist",
                "deleted",
                "removed",
                "channel not found",
                "video not available",
            ]
        ):
            return ErrorCategory.RESOURCE_NOT_FOUND

        # Quota exceeded (different from rate limiting)
        if any(
            keyword in error_msg
            for keyword in ["quota", "limit exceeded", "api quota", "daily limit"]
        ):
            return ErrorCategory.QUOTA_EXCEEDED

        # Temporary failures
        if any(
            keyword in error_msg
            for keyword in [
                "temporary",
                "retry later",
                "service unavailable",
                "503",
                "502",
                "internal server error",
                "500",
                "maintenance",
            ]
        ):
            return ErrorCategory.TEMPORARY_FAILURE

        # Permanent failures
        if any(
            keyword in error_msg
            for keyword in [
                "permanently",
                "deleted",
                "terminated",
                "suspended",
                "banned",
                "violates",
                "inappropriate",
                "copyright",
            ]
        ):
            return ErrorCategory.PERMANENT_FAILURE

        # System errors
        if any(
            keyword in error_type
            for keyword in ["memory", "disk", "io", "permission", "system"]
        ) or any(
            keyword in error_msg
            for keyword in [
                "disk space",
                "permission denied",
                "out of memory",
                "io error",
            ]
        ):
            return ErrorCategory.SYSTEM_ERROR

        return ErrorCategory.UNKNOWN

    def get_recovery_strategy(
        self,
        error_category: ErrorCategory,
        attempt: int,
        context: dict[str, Any] | None = None,
    ) -> RecoveryStrategy:
        """
        Determine the appropriate recovery strategy for an error.

        Args:
            error_category: The classified error category
            attempt: Current attempt number (0-based)
            context: Additional context

        Returns:
            RecoveryStrategy: Recommended recovery approach
        """
        # Fail fast for permanent failures
        if error_category == ErrorCategory.PERMANENT_FAILURE:
            return RecoveryStrategy.SKIP_AND_CONTINUE

        # Fail fast for authentication issues
        if error_category == ErrorCategory.AUTHENTICATION:
            return RecoveryStrategy.FAIL_FAST

        # Skip and continue for resource not found
        if error_category == ErrorCategory.RESOURCE_NOT_FOUND:
            return RecoveryStrategy.SKIP_AND_CONTINUE

        # System errors may require manual intervention
        if error_category == ErrorCategory.SYSTEM_ERROR:
            if attempt >= self.max_retries:
                return RecoveryStrategy.MANUAL_INTERVENTION
            return RecoveryStrategy.WAIT_AND_RETRY

        # Rate limiting and quota issues need backoff
        if error_category in [ErrorCategory.RATE_LIMIT, ErrorCategory.QUOTA_EXCEEDED]:
            return RecoveryStrategy.EXPONENTIAL_BACKOFF

        # Network and temporary failures can retry with backoff
        if error_category in [ErrorCategory.NETWORK, ErrorCategory.TEMPORARY_FAILURE]:
            if attempt >= self.max_retries:
                return RecoveryStrategy.SKIP_AND_CONTINUE
            return RecoveryStrategy.EXPONENTIAL_BACKOFF

        # Unknown errors - conservative approach
        if attempt >= self.max_retries:
            return RecoveryStrategy.SKIP_AND_CONTINUE
        return RecoveryStrategy.EXPONENTIAL_BACKOFF

    def calculate_backoff_delay(
        self,
        error_category: ErrorCategory,
        attempt: int,
        context: dict[str, Any] | None = None,
    ) -> float:
        """
        Calculate the appropriate backoff delay for retries.

        Args:
            error_category: The error category
            attempt: Current attempt number (0-based)
            context: Additional context

        Returns:
            float: Delay in seconds before next retry
        """
        # Base exponential backoff
        delay = min(self.base_backoff * (2**attempt), self.max_backoff)

        # Adjust based on error category
        if error_category == ErrorCategory.RATE_LIMIT:
            # Longer delays for rate limiting
            delay = min(delay * 2, self.max_backoff)
        elif error_category == ErrorCategory.QUOTA_EXCEEDED:
            # Very long delays for quota issues
            delay = min(delay * 5, self.max_backoff)
        elif error_category == ErrorCategory.NETWORK:
            # Shorter delays for network issues
            delay = min(delay * 0.5, self.max_backoff)

        # Add jitter to prevent thundering herd
        import random

        jitter = random.uniform(0.1, 1.0)
        delay *= jitter

        return delay

    def should_retry(
        self,
        error_category: ErrorCategory,
        attempt: int,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Determine if an operation should be retried.

        Args:
            error_category: The error category
            attempt: Current attempt number (0-based)
            context: Additional context

        Returns:
            bool: Whether to retry the operation
        """
        strategy = self.get_recovery_strategy(error_category, attempt, context)

        if strategy in [
            RecoveryStrategy.FAIL_FAST,
            RecoveryStrategy.SKIP_AND_CONTINUE,
            RecoveryStrategy.MANUAL_INTERVENTION,
        ]:
            return False

        return attempt < self.max_retries

    def execute_with_recovery(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        context: dict[str, Any] | None = None,
        on_error: (
            Callable[[Exception, ErrorCategory, RecoveryStrategy], None] | None
        ) = None,
    ) -> Any:
        """
        Execute an operation with automatic error recovery.

        Args:
            operation: The operation to execute
            operation_name: Name of the operation for logging
            context: Additional context for error handling
            on_error: Callback for error handling

        Returns:
            Any: Result of the operation

        Raises:
            Exception: The last exception if recovery fails
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return operation()

            except Exception as e:
                last_exception = e
                error_category = self.classify_error(e, context)
                strategy = self.get_recovery_strategy(error_category, attempt, context)

                logger.warning(
                    f"Operation '{operation_name}' failed (attempt {attempt + 1}/{self.max_retries + 1}): "
                    f"{error_category.value} - {e}"
                )

                if on_error:
                    on_error(e, error_category, strategy)

                # Check if we should retry
                if not self.should_retry(error_category, attempt, context):
                    break

                # Calculate and apply backoff delay
                if strategy in [
                    RecoveryStrategy.EXPONENTIAL_BACKOFF,
                    RecoveryStrategy.WAIT_AND_RETRY,
                ]:
                    delay = self.calculate_backoff_delay(
                        error_category, attempt, context
                    )
                    logger.info(
                        f"Retrying '{operation_name}' in {delay:.1f} seconds..."
                    )
                    time.sleep(delay)

        # If we get here, all retries failed
        if last_exception:
            raise last_exception

    def get_error_summary(self) -> dict[str, Any]:
        """
        Get a summary of error patterns observed.

        Returns:
            Dict containing error statistics
        """
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "error_categories": list(self.error_counts.keys()),
        }
