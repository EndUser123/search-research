#!/usr/bin/env python3
"""
Error Handling and Retry Logic for TaskMaster GitHub Integration
Provides robust error handling, retry mechanisms, and comprehensive monitoring
"""

import asyncio
import hashlib
import logging
import sqlite3
import time
import traceback
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""

    GITHUB_API = "github_api"
    DATABASE = "database"
    VALIDATION = "validation"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    TASK_CREATION = "task_creation"
    PARSING = "parsing"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Error event record"""

    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    stack_trace: str
    context: dict[str, Any]
    event_data: dict[str, Any]
    retry_count: int = 0
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class RetryConfig:
    """Configuration for retry logic"""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: list[type[Exception]] = None

    def __post_init__(self):
        if self.retry_on_exceptions is None:
            self.retry_on_exceptions = [
                aiohttp.ClientError,
                asyncio.TimeoutError,
                ConnectionError,
                TimeoutError,
            ]


@dataclass
class MonitoringMetrics:
    """Monitoring and metrics data"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    errors_by_category: dict[str, int] = None
    errors_by_severity: dict[str, int] = None
    average_response_time: float = 0.0
    last_error_timestamp: str | None = None
    uptime_start: str = None

    def __post_init__(self):
        if self.errors_by_category is None:
            self.errors_by_category = defaultdict(int)
        if self.errors_by_severity is None:
            self.errors_by_severity = defaultdict(int)


class ErrorHandlingRetryManager:
    """Comprehensive error handling and retry management system"""

    def __init__(self, db_path: Path = Path("P:/.speckit/taskmaster/tasks.db")):
        self.db_path = db_path
        self.error_events: list[ErrorEvent] = []
        self.retry_configs: dict[str, RetryConfig] = {}
        self.metrics = MonitoringMetrics(uptime_start=datetime.now().isoformat())

        # Error handling strategies
        self.error_strategies = {
            ErrorCategory.GITHUB_API: self._handle_github_api_error,
            ErrorCategory.DATABASE: self._handle_database_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.AUTHENTICATION: self._handle_authentication_error,
            ErrorCategory.RATE_LIMITING: self._handle_rate_limiting_error,
            ErrorCategory.TASK_CREATION: self._handle_task_creation_error,
            ErrorCategory.PARSING: self._handle_parsing_error,
        }

        # Default retry configurations
        self._initialize_default_retry_configs()

        # Rate limiting
        self.rate_limits = defaultdict(deque)
        self.rate_limit_window = 300  # 5 minutes
        self.max_requests_per_window = 1000

        # Circuit breaker state
        self.circuit_breakers = defaultdict(dict)
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes

    def _initialize_default_retry_configs(self):
        """Initialize default retry configurations for different operation types"""
        self.retry_configs.update(
            {
                "github_api": RetryConfig(
                    max_retries=3,
                    base_delay=2.0,
                    max_delay=30.0,
                    exponential_base=2.0,
                    retry_on_exceptions=[aiohttp.ClientError, asyncio.TimeoutError],
                ),
                "database": RetryConfig(
                    max_retries=2,
                    base_delay=1.0,
                    max_delay=10.0,
                    exponential_base=1.5,
                    retry_on_exceptions=[sqlite3.Error, ConnectionError],
                ),
                "task_creation": RetryConfig(
                    max_retries=1,
                    base_delay=0.5,
                    max_delay=5.0,
                    exponential_base=2.0,
                    retry_on_exceptions=[Exception],
                ),
                "webhook_processing": RetryConfig(
                    max_retries=2,
                    base_delay=1.0,
                    max_delay=15.0,
                    exponential_base=2.0,
                    retry_on_exceptions=[Exception],
                ),
            }
        )

    async def execute_with_retry(
        self, operation: Callable, operation_type: str, *args, **kwargs
    ) -> Any:
        """
        Execute operation with retry logic and error handling
        """
        retry_config = self.retry_configs.get(operation_type, RetryConfig())

        for attempt in range(retry_config.max_retries + 1):
            try:
                start_time = time.time()
                self.metrics.total_requests += 1

                # Check circuit breaker
                if self._is_circuit_breaker_open(operation_type):
                    raise Exception(f"Circuit breaker open for {operation_type}")

                # Check rate limiting
                self._check_rate_limit(operation_type)

                # Execute operation
                result = await operation(*args, **kwargs)

                # Record success
                response_time = time.time() - start_time
                self._record_success(operation_type, response_time)

                # Reset circuit breaker on success
                self._reset_circuit_breaker(operation_type)

                return result

            except Exception as e:
                error_id = self._generate_error_id()

                # Determine if this exception should be retried
                should_retry = attempt < retry_config.max_retries and any(
                    isinstance(e, exc_type)
                    for exc_type in retry_config.retry_on_exceptions
                )

                # Classify error
                category = self._classify_error(e, operation_type)
                severity = self._determine_severity(e, category, attempt)

                # Record error event
                error_event = ErrorEvent(
                    error_id=error_id,
                    timestamp=datetime.now().isoformat(),
                    severity=severity,
                    category=category,
                    message=str(e),
                    exception_type=type(e).__name__,
                    stack_trace=traceback.format_exc(),
                    context={
                        "operation_type": operation_type,
                        "attempt": attempt + 1,
                        "max_retries": retry_config.max_retries,
                        "should_retry": should_retry,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                    event_data=kwargs.get("event_data", {}),
                    retry_count=attempt,
                )

                self.error_events.append(error_event)
                self._record_error(category, severity)

                # Log error
                logger.error(f"Error in {operation_type} (attempt {attempt + 1}): {e}")

                # Handle error with specific strategy
                await self._handle_error_with_strategy(error_event)

                # Retry if appropriate
                if should_retry:
                    delay = self._calculate_retry_delay(retry_config, attempt)
                    logger.info(
                        f"Retrying {operation_type} in {delay:.2f} seconds (attempt {attempt + 2})"
                    )
                    await asyncio.sleep(delay)
                else:
                    # No more retries, record failure
                    self.metrics.failed_requests += 1
                    self.metrics.last_error_timestamp = error_event.timestamp

                    # Update circuit breaker
                    self._update_circuit_breaker(operation_type)

                    # Store error in database
                    await self._store_error_in_database(error_event)

                    raise e

    def _is_circuit_breaker_open(self, operation_type: str) -> bool:
        """Check if circuit breaker is open for operation type"""
        breaker = self.circuit_breakers[operation_type]

        if not breaker.get("open", False):
            return False

        # Check if timeout has passed
        if breaker.get("opened_at"):
            opened_at = datetime.fromisoformat(breaker["opened_at"])
            if datetime.now() - opened_at > timedelta(
                seconds=self.circuit_breaker_timeout
            ):
                # Reset circuit breaker
                self._reset_circuit_breaker(operation_type)
                return False

        return True

    def _reset_circuit_breaker(self, operation_type: str):
        """Reset circuit breaker for operation type"""
        self.circuit_breakers[operation_type] = {
            "open": False,
            "failure_count": 0,
            "last_failure": None,
            "opened_at": None,
        }

    def _update_circuit_breaker(self, operation_type: str):
        """Update circuit breaker state after failure"""
        breaker = self.circuit_breakers[operation_type]
        breaker["failure_count"] = breaker.get("failure_count", 0) + 1
        breaker["last_failure"] = datetime.now().isoformat()

        if breaker["failure_count"] >= self.circuit_breaker_threshold:
            breaker["open"] = True
            breaker["opened_at"] = datetime.now().isoformat()
            logger.warning(
                f"Circuit breaker opened for {operation_type} due to {breaker['failure_count']} failures"
            )

    def _check_rate_limit(self, operation_type: str):
        """Check and enforce rate limiting"""
        now = time.time()
        window_start = now - self.rate_limit_window

        # Clean old timestamps
        timestamps = self.rate_limits[operation_type]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        # Check limit
        if len(timestamps) >= self.max_requests_per_window:
            raise Exception(f"Rate limit exceeded for {operation_type}")

        # Add current timestamp
        timestamps.append(now)

    def _record_success(self, operation_type: str, response_time: float):
        """Record successful operation"""
        self.metrics.successful_requests += 1

        # Update average response time
        total_requests = self.metrics.total_requests
        current_avg = self.metrics.average_response_time
        self.metrics.average_response_time = (
            current_avg * (total_requests - 1) + response_time
        ) / total_requests

    def _record_error(self, category: ErrorCategory, severity: ErrorSeverity):
        """Record error statistics"""
        self.metrics.errors_by_category[category.value] += 1
        self.metrics.errors_by_severity[severity.value] += 1

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        timestamp = int(time.time() * 1000)
        random_hash = hashlib.md5(f"{timestamp}{time.time_ns()}".encode()).hexdigest()[
            :8
        ]
        return f"err-{timestamp}-{random_hash}"

    def _classify_error(
        self, exception: Exception, operation_type: str
    ) -> ErrorCategory:
        """Classify error into category"""
        exception_type = type(exception).__name__
        message = str(exception).lower()

        if operation_type == "github_api" or "github" in operation_type:
            return ErrorCategory.GITHUB_API
        elif operation_type == "database" or "database" in operation_type:
            return ErrorCategory.DATABASE
        elif "validation" in message or "invalid" in message:
            return ErrorCategory.VALIDATION
        elif (
            "timeout" in message
            or "connection" in message
            or exception_type in ["TimeoutError", "ConnectionError"]
        ):
            return ErrorCategory.NETWORK
        elif "auth" in message or "unauthorized" in message or "permission" in message:
            return ErrorCategory.AUTHENTICATION
        elif "rate" in message or "limit" in message:
            return ErrorCategory.RATE_LIMITING
        elif "json" in message or "parse" in message:
            return ErrorCategory.PARSING
        elif "task" in operation_type:
            return ErrorCategory.TASK_CREATION
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(
        self, exception: Exception, category: ErrorCategory, attempt: int
    ) -> ErrorSeverity:
        """Determine error severity"""
        exception_type = type(exception).__name__
        message = str(exception).lower()

        # Critical severity indicators
        if any(
            keyword in message
            for keyword in ["critical", "fatal", "security", "breach"]
        ):
            return ErrorSeverity.CRITICAL

        # High severity indicators
        if (
            category in [ErrorCategory.DATABASE, ErrorCategory.AUTHENTICATION]
            or attempt >= 3
        ):
            return ErrorSeverity.HIGH

        # Medium severity indicators
        if (
            category in [ErrorCategory.GITHUB_API, ErrorCategory.TASK_CREATION]
            or attempt >= 2
        ):
            return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def _calculate_retry_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        delay = config.base_delay * (config.exponential_base**attempt)
        delay = min(delay, config.max_delay)

        if config.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += (time.time() % (2 * jitter_range)) - jitter_range

        return max(0, delay)

    async def _handle_error_with_strategy(self, error_event: ErrorEvent):
        """Handle error using category-specific strategy"""
        strategy = self.error_strategies.get(
            error_event.category, self._handle_unknown_error
        )
        try:
            await strategy(error_event)
        except Exception as e:
            logger.error(f"Error in error handling strategy: {e}")

    async def _handle_github_api_error(self, error_event: ErrorEvent):
        """Handle GitHub API errors"""
        message = error_event.message.lower()

        if "rate limit" in message:
            # Extract reset time from GitHub API response if available
            reset_time = self._extract_github_rate_limit_reset(error_event.context)
            if reset_time:
                logger.warning(f"GitHub API rate limited until {reset_time}")

        if "unauthorized" in message or "401" in message:
            logger.critical("GitHub API authentication failed - check token")

        if "not found" in message or "404" in message:
            logger.warning("GitHub API resource not found")

    async def _handle_database_error(self, error_event: ErrorEvent):
        """Handle database errors"""
        message = error_event.message.lower()

        if "locked" in message or "busy" in message:
            logger.warning("Database locked - retry may succeed")

        if "corrupt" in message or "disk" in message:
            logger.critical("Database corruption detected")

        if "permission" in message:
            logger.error("Database permission error")

    async def _handle_validation_error(self, error_event: ErrorEvent):
        """Handle validation errors"""
        logger.warning(f"Validation error: {error_event.message}")
        # Validation errors typically shouldn't be retried
        pass

    async def _handle_network_error(self, error_event: ErrorEvent):
        """Handle network errors"""
        logger.warning(f"Network error: {error_event.message}")
        # Network errors are typically retryable
        pass

    async def _handle_authentication_error(self, error_event: ErrorEvent):
        """Handle authentication errors"""
        logger.critical(f"Authentication error: {error_event.message}")
        # Authentication errors should not be retried without intervention
        pass

    async def _handle_rate_limiting_error(self, error_event: ErrorEvent):
        """Handle rate limiting errors"""
        logger.warning(f"Rate limiting error: {error_event.message}")
        # Rate limiting errors benefit from exponential backoff
        pass

    async def _handle_task_creation_error(self, error_event: ErrorEvent):
        """Handle task creation errors"""
        logger.error(f"Task creation error: {error_event.message}")

        # Check for specific task creation issues
        if "duplicate" in error_event.message.lower():
            logger.warning("Duplicate task creation attempted")
        if "validation" in error_event.message.lower():
            logger.warning("Task validation failed")

    async def _handle_parsing_error(self, error_event: ErrorEvent):
        """Handle parsing errors"""
        logger.warning(f"Parsing error: {error_event.message}")
        # Parsing errors are typically not retryable
        pass

    async def _handle_unknown_error(self, error_event: ErrorEvent):
        """Handle unknown errors"""
        logger.error(f"Unknown error: {error_event.message}")
        # Default handling for unknown errors

    def _extract_github_rate_limit_reset(
        self, context: dict[str, Any]
    ) -> str | None:
        """Extract GitHub API rate limit reset time from context"""
        # This would extract reset time from GitHub API response headers
        # Implementation depends on how context is structured
        return None

    async def _store_error_in_database(self, error_event: ErrorEvent):
        """Store error event in database for analysis"""
        try:
            # Store error in database table
            # This would require extending the database schema
            logger.info(f"Storing error {error_event.error_id} in database")
        except Exception as e:
            logger.error(f"Failed to store error in database: {e}")

    def get_error_statistics(self) -> dict[str, Any]:
        """Get comprehensive error statistics"""
        recent_errors = [
            e
            for e in self.error_events
            if datetime.fromisoformat(e.timestamp)
            > datetime.now() - timedelta(hours=24)
        ]

        return {
            "total_errors": len(self.error_events),
            "recent_errors_24h": len(recent_errors),
            "errors_by_category": dict(self.metrics.errors_by_category),
            "errors_by_severity": dict(self.metrics.errors_by_severity),
            "total_requests": self.metrics.total_requests,
            "success_rate": (
                self.metrics.successful_requests
                / max(self.metrics.total_requests, 1)
                * 100
            ),
            "average_response_time": self.metrics.average_response_time,
            "last_error": self.metrics.last_error_timestamp,
            "uptime_hours": (
                (
                    (
                        datetime.now()
                        - datetime.fromisoformat(self.metrics.uptime_start)
                    ).total_seconds()
                    / 3600
                )
                if self.metrics.uptime_start
                else 0
            ),
            "circuit_breakers": {
                op_type: {
                    "open": breaker.get("open", False),
                    "failure_count": breaker.get("failure_count", 0),
                    "opened_at": breaker.get("opened_at"),
                }
                for op_type, breaker in self.circuit_breakers.items()
            },
        }

    def get_recent_errors(
        self, hours: int = 24, severity: ErrorSeverity | None = None
    ) -> list[dict[str, Any]]:
        """Get recent errors with optional severity filter"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_errors = [
            e
            for e in self.error_events
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]

        if severity:
            filtered_errors = [e for e in filtered_errors if e.severity == severity]

        # Sort by timestamp (most recent first)
        filtered_errors.sort(key=lambda e: e.timestamp, reverse=True)

        return [asdict(e) for e in filtered_errors[:50]]  # Limit to 50 most recent

    def resolve_error(self, error_id: str, resolution_notes: str = "") -> bool:
        """Mark an error as resolved"""
        for error in self.error_events:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                logger.info(f"Resolved error {error_id}: {resolution_notes}")
                return True
        return False

    def add_retry_config(self, operation_type: str, config: RetryConfig):
        """Add retry configuration for operation type"""
        self.retry_configs[operation_type] = config
        logger.info(f"Added retry configuration for {operation_type}")

    def update_retry_config(self, operation_type: str, **kwargs):
        """Update existing retry configuration"""
        if operation_type in self.retry_configs:
            config = self.retry_configs[operation_type]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            logger.info(f"Updated retry configuration for {operation_type}")

    def clear_old_errors(self, days: int = 30):
        """Clear old error events to manage memory"""
        cutoff_time = datetime.now() - timedelta(days=days)
        initial_count = len(self.error_events)

        self.error_events = [
            e
            for e in self.error_events
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]

        cleared_count = initial_count - len(self.error_events)
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old error events")

    def get_health_status(self) -> dict[str, Any]:
        """Get overall health status of the error handling system"""
        stats = self.get_error_statistics()

        # Determine overall health
        error_rate = stats["total_errors"] / max(stats["total_requests"], 1)
        recent_error_rate = stats["recent_errors_24h"] / max(24, 1)  # errors per hour

        health_status = "healthy"
        if error_rate > 0.1 or recent_error_rate > 10:
            health_status = "unhealthy"
        elif error_rate > 0.05 or recent_error_rate > 5:
            health_status = "degraded"

        # Check circuit breakers
        open_circuit_breakers = [
            op_type
            for op_type, breaker in self.circuit_breakers.items()
            if breaker.get("open", False)
        ]

        return {
            "status": health_status,
            "error_rate": error_rate,
            "recent_error_rate": recent_error_rate,
            "success_rate": stats["success_rate"],
            "open_circuit_breakers": open_circuit_breakers,
            "uptime_hours": stats["uptime_hours"],
            "last_error": stats["last_error"],
            "recommendations": self._generate_health_recommendations(stats),
        }

    def _generate_health_recommendations(self, stats: dict[str, Any]) -> list[str]:
        """Generate health recommendations based on statistics"""
        recommendations = []

        if stats["success_rate"] < 90:
            recommendations.append(
                "Success rate is below 90% - investigate frequent errors"
            )

        if stats["average_response_time"] > 5.0:
            recommendations.append(
                "Average response time is high - consider performance optimization"
            )

        if stats["errors_by_severity"].get("critical", 0) > 0:
            recommendations.append(
                "Critical errors detected - immediate attention required"
            )

        recent_critical = len(
            [
                e
                for e in self.error_events
                if (
                    e.severity == ErrorSeverity.CRITICAL
                    and datetime.fromisoformat(e.timestamp)
                    > datetime.now() - timedelta(hours=1)
                )
            ]
        )
        if recent_critical > 0:
            recommendations.append(
                f"{recent_critical} critical errors in the last hour"
            )

        return recommendations


# Example usage
async def main():
    """Example usage of error handling and retry manager"""
    manager = ErrorHandlingRetryManager()

    # Example operation that might fail
    async def example_operation(data):
        # Simulate occasional failures
        if data.get("fail", False):
            raise aiohttp.ClientError("Simulated network error")
        return {"status": "success", "data": data}

    try:
        # Execute with retry
        result = await manager.execute_with_retry(
            example_operation,
            "github_api",
            {"test": "data"},
            event_data={"event_type": "test"},
        )
        print(f"Operation succeeded: {result}")

        # Get statistics
        stats = manager.get_error_statistics()
        print(f"Error statistics: {stats}")

        # Get health status
        health = manager.get_health_status()
        print(f"Health status: {health}")

    except Exception as e:
        print(f"Operation failed after retries: {e}")


if __name__ == "__main__":
    asyncio.run(main())
