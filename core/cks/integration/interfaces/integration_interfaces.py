from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable

"""CSF CKS Integration Interfaces

This module defines the standardized interfaces for the CKS cross-system
integration layer, providing consistent contracts for all external system
clients following CSF constitutional requirements.

Algorithm Approach: Interface Segregation with Dependency Injection
to ensure loose coupling and testability across all integration points.

Design Principles:
- Consistent interface patterns across all systems
- Comprehensive error handling with typed exceptions
- Async/await support for performance optimization
- CSF constitutional compliance built-in
- Solo developer optimization with simple abstractions

"""


# Type variables for generic return types
T = TypeVar("T")
ResultType = TypeVar("ResultType")


class IntegrationStatus(Enum):
    """Enumeration of integration system status values.

    Provides standardized status reporting across all integration clients
    for consistent monitoring and health checks.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class SecurityLevel(Enum):
    """Security classification for integration operations.

    Defines security requirements and validation levels for different
    types of integration operations to ensure CSF compliance.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class IntegrationConfig:
    """Base configuration for all integration clients.

    Provides common configuration parameters and validation rules
    for consistent behavior across all integration points.

    Attributes:
        enabled (bool): Whether the integration is enabled
        timeout_seconds (int): Operation timeout in seconds
        retry_attempts (int): Number of retry attempts for failed operations
        retry_delay_seconds (float): Delay between retry attempts
        security_level (SecurityLevel): Security classification level
        rate_limit_requests_per_minute (int): Rate limiting threshold
        enable_caching (bool): Whether to enable response caching
        cache_duration_hours (int): Cache validity duration
        metadata (Dict[str, Any]): Additional configuration metadata

    """

    enabled: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    rate_limit_requests_per_minute: int = 60
    enable_caching: bool = True
    cache_duration_hours: int = 24
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts cannot be negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        if self.rate_limit_requests_per_minute <= 0:
            raise ValueError("rate_limit_requests_per_minute must be positive")
        if self.cache_duration_hours <= 0:
            raise ValueError("cache_duration_hours must be positive")


@dataclass
class IntegrationResult:
    """Standardized result container for all integration operations.

    Provides consistent result format with comprehensive metadata
    and error handling across all integration clients.

    Attributes:
        success (bool): Whether the operation was successful
        data (Optional[T]): Result data payload
        error (Optional[str]): Error message if operation failed
        status_code (Optional[int]): HTTP or system status code
        metadata (Dict[str, Any]): Operation metadata and diagnostics
        execution_time_seconds (float): Total execution time
        timestamp (datetime): When the operation completed
        cached (bool): Whether result was retrieved from cache
        integration_source (str): Source integration system name

    """

    success: bool
    data: ResultType | None = None
    error: str | None = None
    status_code: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cached: bool = False
    integration_source: str = ""

    @classmethod
    def create_success(
        cls,
        data: ResultType,
        integration_source: str,
        metadata: dict[str, Any] | None = None,
        execution_time_seconds: float = 0.0,
        cached: bool = False,
    ) -> IntegrationResult[ResultType]:
        """Create a successful integration result.

        Parameters
        ----------
        data (ResultType): Successful operation result data
        integration_source (str): Source integration system name
        metadata (Optional[Dict[str, Any]]): Operation metadata
        execution_time_seconds (float): Operation execution time
        cached (bool): Whether result was cached

        Returns
        -------
        IntegrationResult[ResultType]: Successful result instance

        """
        return cls(
            success=True,
            data=data,
            integration_source=integration_source,
            metadata=metadata or {},
            execution_time_seconds=execution_time_seconds,
            cached=cached,
        )

    @classmethod
    def create_error(
        cls,
        error: str,
        integration_source: str,
        status_code: int | None = None,
        metadata: dict[str, Any] | None = None,
        execution_time_seconds: float = 0.0,
    ) -> IntegrationResult[ResultType]:
        """Create an error integration result.

        Parameters
        ----------
        error (str): Error message
        integration_source (str): Source integration system name
        status_code (Optional[int]): HTTP or system status code
        metadata (Optional[Dict[str, Any]]): Operation metadata
        execution_time_seconds (float): Operation execution time

        Returns
        -------
        IntegrationResult[ResultType]: Error result instance

        """
        return cls(
            success=False,
            error=error,
            status_code=status_code,
            integration_source=integration_source,
            metadata=metadata or {},
            execution_time_seconds=execution_time_seconds,
        )


@dataclass
class HealthCheck:
    """Health check result for integration systems.

    Provides comprehensive health status information for monitoring
    and maintaining integration system reliability.

    Attributes:
        status (IntegrationStatus): Current system status
        response_time_ms (float): System response time in milliseconds
        last_check (datetime): When health check was performed
        error_message (Optional[str]): Error message if status is not healthy
        metadata (Dict[str, Any]): Additional health metrics

    """

    status: IntegrationStatus
    response_time_ms: float
    last_check: datetime = field(default_factory=datetime.utcnow)
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Check if the system is healthy."""
        return self.status in (IntegrationStatus.ACTIVE, IntegrationStatus.DEGRADED)


class BaseIntegrationClient(ABC):
    """Abstract base class for all integration clients.

    Defines the standard interface and common functionality that all
    integration clients must implement for CSF compliance.

    Algorithm Approach: Template Method Pattern with standardized
    error handling, retry logic, and health checking.

    CSF Compliance:
    - Solo developer optimization with simple interfaces
    - Evidence-based operations with comprehensive logging
    - Constitutional validation for all operations
    - Force multiplier capabilities through standardized integration

    """

    def __init__(self, config: IntegrationConfig, integration_name: str) -> None:
        """Initialize the integration client with configuration.

        Parameters
        ----------
        config (IntegrationConfig): Client configuration
        integration_name (str): Name of the integration system

        Raises
        ------
        ValueError: If configuration is invalid

        """
        self.config = config
        self.integration_name = integration_name
        self._rate_limiter = {}
        self._cache = {}

        # Performance metrics
        self.operation_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "cache_hits": 0,
            "total_execution_time": 0.0,
            "average_response_time": 0.0,
        }

        if not config.enabled:
            raise ValueError(
                f"Integration {integration_name} is disabled in configuration",
            )

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the integration client and establish connections.

        This method must be called before any other operations.
        Implementations should establish connections, validate credentials,
        and perform any required setup.

        Returns
        -------
        bool: True if initialization successful, False otherwise

        Raises
        ------
        IntegrationException: If initialization fails

        """

    @abstractmethod
    async def health_check(self) -> HealthCheck:
        """Perform health check on the integration system.

        Returns
        -------
        HealthCheck: Health status information

        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources and close connections.

        Must be called when the client is no longer needed to ensure
        proper resource cleanup and prevent memory leaks.

        """

    async def execute_operation(
        self,
        operation_name: str,
        operation_func: Awaitable[T],
        operation_metadata: dict[str, Any] | None = None,
    ) -> IntegrationResult[T]:
        """Execute an integration operation with standard error handling.

        Algorithm Approach: Comprehensive error handling with retry logic,
        rate limiting, caching, and performance monitoring.

        Parameters
        ----------
        operation_name (str): Name of the operation for logging
        operation_func (Awaitable[T]): Async operation function to execute
        operation_metadata (Optional[Dict[str, Any]]): Operation metadata

        Returns
        -------
        IntegrationResult[T]: Standardized operation result

        """
        start_time = datetime.utcnow()
        metadata = operation_metadata or {}

        # Check rate limits
        if not self._check_rate_limit(operation_name):
            return IntegrationResult.create_error(
                error=f"Rate limit exceeded for operation: {operation_name}",
                integration_source=self.integration_name,
                status_code=429,
                metadata=metadata,
            )

        # Check cache first
        cache_key = self._generate_cache_key(operation_name, metadata)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            self.operation_stats["cache_hits"] += 1
            cached_result.cached = True
            return cached_result

        # Execute with retry logic
        for attempt in range(self.config.retry_attempts + 1):
            try:
                self.operation_stats["total_operations"] += 1

                # Execute operation with timeout
                result = await asyncio.wait_for(
                    operation_func,
                    timeout=self.config.timeout_seconds,
                )

                execution_time = (datetime.utcnow() - start_time).total_seconds()

                # Create successful result
                integration_result = IntegrationResult.create_success(
                    data=result,
                    integration_source=self.integration_name,
                    metadata=metadata,
                    execution_time_seconds=execution_time,
                )

                # Update cache
                if self.config.enable_caching:
                    self._cache[cache_key] = integration_result

                # Update statistics
                self.operation_stats["successful_operations"] += 1
                self._update_performance_stats(execution_time)

                return integration_result

            except TimeoutError:
                error_msg = f"Operation timeout: {operation_name}"
                if attempt == self.config.retry_attempts:
                    break
                await asyncio.sleep(self.config.retry_delay_seconds)

            except Exception as e:
                error_msg = f"Operation failed: {operation_name} - {e!s}"
                if attempt == self.config.retry_attempts:
                    self.operation_stats["failed_operations"] += 1
                    break
                await asyncio.sleep(self.config.retry_delay_seconds)

        # Return error result
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return IntegrationResult.create_error(
            error=error_msg,
            integration_source=self.integration_name,
            metadata=metadata,
            execution_time_seconds=execution_time,
        )

    def _check_rate_limit(self, operation_name: str) -> bool:
        """Check if operation exceeds rate limits.

        Parameters
        ----------
        operation_name (str): Name of the operation to check

        Returns
        -------
        bool: True if within rate limits, False otherwise

        """
        current_time = datetime.utcnow()

        # Simple rate limiting implementation
        key = f"{self.integration_name}:{operation_name}"
        if key not in self._rate_limiter:
            self._rate_limiter[key] = {
                "count": 0,
                "window_start": current_time,
            }

        window_start = self._rate_limiter[key]["window_start"]

        # Reset window if more than a minute has passed
        if (current_time - window_start).total_seconds() > 60:
            self._rate_limiter[key] = {
                "count": 0,
                "window_start": current_time,
            }

        # Check rate limit
        if self._rate_limiter[key]["count"] >= self.config.rate_limit_requests_per_minute:
            return False

        self._rate_limiter[key]["count"] += 1
        return True

    def _generate_cache_key(self, operation_name: str, metadata: dict[str, Any]) -> str:
        """Generate cache key for operation and metadata.

        Parameters
        ----------
        operation_name (str): Name of the operation
        metadata (Dict[str, Any]): Operation metadata

        Returns
        -------
        str: Cache key string

        """
        # Simple cache key generation - in production, use proper hashing
        metadata_str = str(sorted(metadata.items()))
        return f"{self.integration_name}:{operation_name}:{hash(metadata_str)}"

    def _check_cache(self, cache_key: str) -> IntegrationResult | None:
        """Check cache for valid result.

        Parameters
        ----------
        cache_key (str): Cache key to lookup

        Returns
        -------
        Optional[IntegrationResult]: Cached result if valid, None otherwise

        """
        if not self.config.enable_caching or cache_key not in self._cache:
            return None

        cached_result = self._cache[cache_key]
        cache_age = datetime.utcnow() - cached_result.timestamp

        # Check if cache entry is still valid
        if cache_age.total_seconds() < self.config.cache_duration_hours * 3600:
            return cached_result

        # Remove expired entry
        del self._cache[cache_key]
        return None

    def _update_performance_stats(self, execution_time: float) -> None:
        """Update performance statistics.

        Parameters
        ----------
        execution_time (float): Operation execution time in seconds

        """
        self.operation_stats["total_execution_time"] += execution_time
        total_ops = self.operation_stats["successful_operations"]
        if total_ops > 0:
            self.operation_stats["average_response_time"] = (
                self.operation_stats["total_execution_time"] / total_ops
            )

    def get_performance_statistics(self) -> dict[str, Any]:
        """Get comprehensive performance statistics.

        Returns
        -------
        Dict[str, Any]: Performance and usage statistics

        """
        stats = self.operation_stats.copy()
        stats.update(
            {
                "integration_name": self.integration_name,
                "cache_size": len(self._cache),
                "rate_limiter_entries": len(self._rate_limiter),
                "success_rate": (
                    self.operation_stats["successful_operations"]
                    / max(self.operation_stats["total_operations"], 1)
                ),
                "last_updated": datetime.utcnow().isoformat(),
            },
        )
        return stats

    def clear_cache(self) -> None:
        """Clear the operation cache."""
        self._cache.clear()

    def reset_statistics(self) -> None:
        """Reset performance statistics."""
        self.operation_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "cache_hits": 0,
            "total_execution_time": 0.0,
            "average_response_time": 0.0,
        }


class IntegrationClientFactory(ABC):
    """Abstract factory for creating integration clients.

    Provides a standardized way to create and configure integration
    clients across all systems while maintaining CSF compliance.
    """

    @abstractmethod
    def create_client(self, config: IntegrationConfig) -> BaseIntegrationClient:
        """Create a configured integration client.

        Parameters
        ----------
        config (IntegrationConfig): Client configuration

        Returns
        -------
        BaseIntegrationClient: Configured integration client

        """

    @abstractmethod
    def get_default_config(self) -> IntegrationConfig:
        """Get default configuration for the integration client.

        Returns
        -------
        IntegrationConfig: Default configuration

        """

    @abstractmethod
    def validate_config(self, config: IntegrationConfig) -> bool:
        """Validate integration client configuration.

        Parameters
        ----------
        config (IntegrationConfig): Configuration to validate

        Returns
        -------
        bool: True if configuration is valid, False otherwise

        """
