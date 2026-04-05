"""
Resilience patterns for handling failures in async operations.

Implements circuit breaker, retry with backoff, and dead letter queue patterns.
"""

import asyncio
import functools
import random
import time
from collections.abc import Callable
from enum import Enum
from typing import Any


class CircuitState(Enum):
    """States for circuit breaker pattern."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern implementation for handling service failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type[Exception] = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type to count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, operation: Callable[..., Any], *args, **kwargs) -> Any:
        """Call operation through circuit breaker.

        Args:
            operation: Async function to call
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result of operation call

        Raises:
            Exception: If circuit is open or operation fails
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (
                time.time() - self.last_failure_time >= self.recovery_timeout
            ):
                # Try to move to half-open state
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker open")

        try:
            # Call the operation
            result = await operation(*args, **kwargs)

            # Success - reset circuit
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED

            return result

        except self.expected_exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = time.time()

            # Check if we should open the circuit
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

            # Re-raise the exception
            raise e


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_factor: float = 2.0,
    jitter: bool = True,
):
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_factor: Factor for exponential backoff
        jitter: Whether to add random jitter to delays
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # If this was the last attempt, don't retry
                    if attempt == max_attempts - 1:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_factor**attempt), max_delay)

                    # Add jitter if requested
                    if jitter:
                        delay *= 0.5 + random.random() * 0.5  # 0.5 to 1.0 multiplier

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # If we get here, all attempts failed
            raise last_exception

        return wrapper

    return decorator


class DeadLetterQueue:
    """Dead letter queue pattern for handling persistently failing operations."""

    def __init__(self, max_retries: int = 3):
        """Initialize dead letter queue.

        Args:
            max_retries: Maximum number of retry attempts before moving to DLQ
        """
        self.max_retries = max_retries
        self.dead_letters: list[dict[str, Any]] = []

    async def process_with_retry(self, operation: Callable[..., Any], item: Any) -> Any:
        """Process item with retry logic, moving to DLQ if persistent failure.

        Args:
            operation: Async function to call with item
            item: Item to process

        Returns:
            Result of successful operation

        Raises:
            Exception: If operation fails after max retries
        """
        retry_count = 0
        last_error = None

        while retry_count <= self.max_retries:
            try:
                return await operation(item)
            except Exception as e:
                last_error = e
                retry_count += 1

                # If we've exceeded max retries, move to DLQ
                if retry_count > self.max_retries:
                    dead_letter = {
                        "item": item,
                        "retry_count": retry_count - 1,
                        "last_error": str(e),
                        "timestamp": time.time(),
                        "exception_type": type(e).__name__,
                    }
                    self.dead_letters.append(dead_letter)
                    raise e

        # This shouldn't be reached, but just in case
        raise last_error

    def get_dead_letters(self) -> list[dict[str, Any]]:
        """Get all items in the dead letter queue.

        Returns:
            List of dead letter items with metadata
        """
        return self.dead_letters.copy()
