"""
Enhanced Error Handling for dnld_telegram

Implements comprehensive error handling patterns with graceful degradation.
Builds on existing TelegramErrorHandler patterns.
"""

import asyncio
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, NamedTuple

from loguru import logger


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    RETRYABLE = "retryable"
    TEMPORARY = "temporary"
    CRITICAL = "critical"


class DegradationStrategy(Enum):
    """Strategies for graceful degradation."""

    REDUCED_QUALITY = "reduced_quality"
    FALLBACK = "fallback"
    SKIP = "skip"
    RETRY = "retry"


@dataclass
class ErrorContext:
    """Context information for error handling."""

    operation: str
    channel_name: str | None = None
    message_id: int | None = None
    attempt: int = 1
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class ErrorHandlingResult(NamedTuple):
    """Result of error handling operation."""

    should_retry: bool
    delay: float
    degradation_strategy: DegradationStrategy
    error_severity: ErrorSeverity
    metadata: dict[str, Any]


class EnhancedErrorHandler:
    """Enhanced error handling with graceful degradation support."""

    # Common error patterns based on existing TelegramErrorHandler
    RETRYABLE_PATTERNS = [
        "Connection lost",
        "network error",
        "disconnected",
        "timeout",
        "FLOOD_WAIT",
        "rate limit",
        "Connection to Telegram failed",
        "Cannot send requests while disconnected",
        "connection lost",
    ]

    TEMPORARY_PATTERNS = [
        "Too Many Requests",
        "flood wait",
        "server error",
        "FLOOD_WAIT_",
    ]

    CRITICAL_PATTERNS = [
        "Invalid object ID",
        "chat id invalid",
        "CHAT_ID_INVALID",
        "Media empty",
        "media not found",
        "FILE_REFERENCE_EXPIRED",
    ]

    # Severity-based retry limits
    MAX_RETRY_ATTEMPTS = {
        ErrorSeverity.RETRYABLE: 5,
        ErrorSeverity.TEMPORARY: 3,
        ErrorSeverity.CRITICAL: 0,
    }

    @classmethod
    def classify_error_severity(
        cls, error_msg: str, context: ErrorContext
    ) -> ErrorSeverity:
        """Classify error severity based on error message and context."""
        error_lower = error_msg.lower()

        # Check for critical patterns first
        if any(pattern.lower() in error_lower for pattern in cls.CRITICAL_PATTERNS):
            return ErrorSeverity.CRITICAL

        # Check for temporary patterns
        if any(pattern.lower() in error_lower for pattern in cls.TEMPORARY_PATTERNS):
            return ErrorSeverity.TEMPORARY

        # Check for retryable patterns
        if any(pattern.lower() in error_lower for pattern in cls.RETRYABLE_PATTERNS):
            return ErrorSeverity.RETRYABLE

        # Default to retryable for unknown errors
        logger.debug(f"Unknown error classified as RETRYABLE: {error_msg}")
        return ErrorSeverity.RETRYABLE

    @classmethod
    def parse_flood_wait_seconds(cls, error_msg: str) -> int | None:
        """Parse FLOOD_WAIT seconds from error message."""
        match = re.search(r"FLOOD_WAIT_(\d+)", error_msg)
        if match:
            return int(match.group(1))
        return None

    @classmethod
    def calculate_retry_delay(
        cls, error_msg: str, context: ErrorContext, severity: ErrorSeverity
    ) -> float:
        """Calculate appropriate retry delay based on error type and context."""
        # Handle specific FLOOD_WAIT delays
        flood_wait_seconds = cls.parse_flood_wait_seconds(error_msg)
        if flood_wait_seconds:
            # Cap flood wait at 300 seconds (5 minutes) max
            return float(min(flood_wait_seconds, 300))

        # Exponential backoff based on severity and attempt count
        if severity == ErrorSeverity.TEMPORARY:
            delay = min(5.0 * (2 ** (context.attempt - 1)), 60.0)  # Max 60 seconds
        elif severity == ErrorSeverity.RETRYABLE:
            delay = min(2.0 * context.attempt, 30.0)  # Max 30 seconds
        else:
            delay = 0.0

        return delay

    @classmethod
    def should_retry_error(
        cls, error_msg: str, context: ErrorContext
    ) -> tuple[bool, float]:
        """Determine if error should be retried and suggested delay."""
        severity = cls.classify_error_severity(error_msg, context)

        # Never retry critical errors
        if severity == ErrorSeverity.CRITICAL:
            return False, 0.0

        # Check attempt limits
        max_attempts = cls.MAX_RETRY_ATTEMPTS.get(severity, 3)
        if context.attempt > max_attempts:
            return False, 0.0

        # Calculate delay
        delay = cls.calculate_retry_delay(error_msg, context, severity)
        return True, delay

    @classmethod
    def select_degradation_strategy(
        cls, error_msg: str, context: ErrorContext
    ) -> DegradationStrategy:
        """Select appropriate degradation strategy based on error and context."""
        severity = cls.classify_error_severity(error_msg, context)

        # Critical errors should be skipped
        if severity == ErrorSeverity.CRITICAL:
            return DegradationStrategy.SKIP

        # High attempt count errors should use fallback
        max_attempts = cls.MAX_RETRY_ATTEMPTS.get(severity, 3)
        if context.attempt > max_attempts:
            return DegradationStrategy.FALLBACK

        # Temporary errors should retry
        if severity == ErrorSeverity.TEMPORARY:
            return DegradationStrategy.RETRY

        # Retryable errors should retry
        return DegradationStrategy.RETRY

    @classmethod
    def apply_fallback_mechanism(
        cls, error_msg: str, context: ErrorContext
    ) -> dict[str, Any]:
        """Apply fallback mechanism for handling persistent errors."""
        severity = cls.classify_error_severity(error_msg, context)

        # Create detailed fallback result
        fallback_result = {
            "status": "fallback_applied",
            "original_error": error_msg,
            "error_severity": severity.value,
            "context": {
                "operation": context.operation,
                "channel_name": context.channel_name,
                "message_id": context.message_id,
                "attempt": context.attempt,
                "timestamp": context.timestamp,
            },
            "fallback_action": "skipped_with_logging",
            "handled_at": time.time(),
        }

        # Log the fallback for monitoring
        logger.warning(
            f"Fallback applied for {context.operation} on message {context.message_id} "
            f"in channel {context.channel_name}: {error_msg} (severity: {severity.value})"
        )

        return fallback_result

    @classmethod
    def handle_error(cls, error_msg: str, context: ErrorContext) -> ErrorHandlingResult:
        """Comprehensive error handling with all strategies."""
        # Classify severity
        severity = cls.classify_error_severity(error_msg, context)

        # Determine retry behavior
        should_retry, delay = cls.should_retry_error(error_msg, context)

        # Select degradation strategy
        degradation_strategy = cls.select_degradation_strategy(error_msg, context)

        # Create metadata
        metadata = {
            "error_parsed": {
                "flood_wait_seconds": cls.parse_flood_wait_seconds(error_msg),
            },
            "retry_info": {
                "max_attempts": cls.MAX_RETRY_ATTEMPTS.get(severity, 3),
                "current_attempt": context.attempt,
            },
        }

        return ErrorHandlingResult(
            should_retry=should_retry,
            delay=delay,
            degradation_strategy=degradation_strategy,
            error_severity=severity,
            metadata=metadata,
        )

    @classmethod
    async def handle_async_error(
        cls, error: Exception, context: ErrorContext
    ) -> ErrorHandlingResult:
        """Handle async error with proper async support."""
        error_msg = str(error)
        result = cls.handle_error(error_msg, context)

        # If retry is needed, apply delay asynchronously
        if result.should_retry and result.delay > 0:
            logger.debug(f"Applying async delay of {result.delay}s for error handling")
            await asyncio.sleep(result.delay)

        return result
