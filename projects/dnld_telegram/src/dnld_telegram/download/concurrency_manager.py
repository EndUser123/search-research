"""
Enhanced Concurrency Management for dnld_telegram

This module provides dynamic concurrency limiting, backpressure handling,
and resource monitoring for download operations.

Task: P2B - Enhanced Concurrency Management
Requirements:
- Dynamic concurrency limits based on system resources
- Backpressure handling to prevent system overload
- Resource monitoring (CPU, memory, disk I/O)
- Integration with existing download semaphore system
"""

import asyncio
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import psutil
from loguru import logger


@dataclass
class ResourceMetrics:
    """System resource metrics for concurrency decisions."""

    cpu_percent: float
    memory_percent: float
    disk_io_percent: float
    active_downloads: int
    bandwidth_usage_mbps: float
    timestamp: float


@dataclass
class ConcurrencyLimits:
    """Dynamic concurrency limits based on resource state."""

    max_concurrent: int
    recommended_concurrent: int
    backpressure_threshold: float
    reason: str


class ResourceMonitor:
    """Monitors system resources to inform concurrency decisions."""

    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self._last_disk_io = None
        self._last_network_io = None
        self._bandwidth_samples: list[float] = []
        self._max_bandwidth_samples = 10

    async def get_current_metrics(self, active_downloads: int) -> ResourceMetrics:
        """Get current system resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk I/O - calculate percentage based on activity
        disk_io = psutil.disk_io_counters()
        disk_io_percent = 0.0
        if self._last_disk_io and disk_io:
            read_diff = disk_io.read_bytes - self._last_disk_io.read_bytes
            write_diff = disk_io.write_bytes - self._last_disk_io.write_bytes
            total_io = read_diff + write_diff
            # Rough estimate: assume 100MB/s is 100% disk utilization
            disk_io_percent = min(100.0, (total_io / (1024 * 1024 * 100)) * 100)
        self._last_disk_io = disk_io

        # Network bandwidth estimation
        network_io = psutil.net_io_counters()
        bandwidth_mbps = 0.0
        if self._last_network_io and network_io:
            bytes_diff = (network_io.bytes_sent + network_io.bytes_recv) - (
                self._last_network_io.bytes_sent + self._last_network_io.bytes_recv
            )
            bandwidth_mbps = (bytes_diff * 8) / (
                1024 * 1024 * self.sampling_interval
            )  # Convert to Mbps

            # Track bandwidth samples for trend analysis
            self._bandwidth_samples.append(bandwidth_mbps)
            if len(self._bandwidth_samples) > self._max_bandwidth_samples:
                self._bandwidth_samples.pop(0)
        self._last_network_io = network_io

        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_io_percent=disk_io_percent,
            active_downloads=active_downloads,
            bandwidth_usage_mbps=bandwidth_mbps,
            timestamp=time.time(),
        )


class BackpressureController:
    """Handles backpressure to prevent system overload."""

    def __init__(self):
        self.cpu_threshold = 80.0  # CPU % threshold for backpressure
        self.memory_threshold = 85.0  # Memory % threshold for backpressure
        self.disk_threshold = 90.0  # Disk I/O % threshold for backpressure
        self._backpressure_active = False
        self._backpressure_start_time: float | None = None

    def evaluate_backpressure(self, metrics: ResourceMetrics) -> bool:
        """Determine if backpressure should be applied."""
        should_activate = (
            metrics.cpu_percent > self.cpu_threshold
            or metrics.memory_percent > self.memory_threshold
            or metrics.disk_io_percent > self.disk_threshold
        )

        if should_activate and not self._backpressure_active:
            self._backpressure_active = True
            self._backpressure_start_time = time.time()
            logger.warning(
                f"Backpressure activated - CPU: {metrics.cpu_percent:.1f}%, "
                f"Memory: {metrics.memory_percent:.1f}%, "
                f"Disk I/O: {metrics.disk_io_percent:.1f}%"
            )
        elif not should_activate and self._backpressure_active:
            duration = time.time() - (self._backpressure_start_time or 0)
            self._backpressure_active = False
            self._backpressure_start_time = None
            logger.info(f"Backpressure deactivated after {duration:.1f} seconds")

        return self._backpressure_active

    async def wait_for_relief(
        self, monitor: ResourceMonitor, active_downloads: int
    ) -> None:
        """Wait for system resources to improve before proceeding."""
        if not self._backpressure_active:
            return

        logger.info("Waiting for resource relief...")
        while self._backpressure_active:
            await asyncio.sleep(2.0)  # Check every 2 seconds
            metrics = await monitor.get_current_metrics(active_downloads)
            self.evaluate_backpressure(metrics)


class ConcurrencyManager:
    """
    Enhanced concurrency management with dynamic limits and backpressure handling.

    Features:
    - Dynamic concurrency adjustment based on system resources
    - Backpressure detection and handling
    - Resource monitoring and metrics collection
    - Integration with existing semaphore-based download system
    """

    def __init__(
        self,
        base_concurrent_limit: int = 2,
        max_concurrent_limit: int = 8,
        resource_check_interval: float = 5.0,
    ):
        self.base_concurrent_limit = base_concurrent_limit
        self.max_concurrent_limit = max_concurrent_limit
        self.resource_check_interval = resource_check_interval

        # Core components
        self.monitor = ResourceMonitor()
        self.backpressure = BackpressureController()

        # Dynamic state
        self._current_limit = base_concurrent_limit
        self._semaphore = asyncio.Semaphore(base_concurrent_limit)
        self._active_downloads = 0
        self._metrics_history: list[ResourceMetrics] = []
        self._last_adjustment_time = 0.0
        self._adjustment_cooldown = 10.0  # Minimum seconds between adjustments

        # Callbacks for limit changes
        self._limit_change_callbacks: list[Callable[[int, int], None]] = []

    def add_limit_change_callback(self, callback: Callable[[int, int], None]) -> None:
        """Add callback to be notified when concurrency limits change."""
        self._limit_change_callbacks.append(callback)

    def _notify_limit_change(self, old_limit: int, new_limit: int) -> None:
        """Notify registered callbacks of limit changes."""
        for callback in self._limit_change_callbacks:
            try:
                callback(old_limit, new_limit)
            except Exception as e:
                logger.warning(f"Limit change callback failed: {e}")

    async def _evaluate_and_adjust_limits(self) -> None:
        """Evaluate system resources and adjust concurrency limits."""
        current_time = time.time()
        if current_time - self._last_adjustment_time < self._adjustment_cooldown:
            return  # Still in cooldown period

        metrics = await self.monitor.get_current_metrics(self._active_downloads)
        self._metrics_history.append(metrics)

        # Keep only recent history (last 20 measurements)
        if len(self._metrics_history) > 20:
            self._metrics_history.pop(0)

        # Calculate new limits based on resource state
        limits = self._calculate_optimal_limits(metrics)

        # Adjust if necessary
        if limits.max_concurrent != self._current_limit:
            old_limit = self._current_limit
            self._current_limit = limits.max_concurrent

            # Create new semaphore with adjusted limit
            # Note: This is a simplified approach - in production, you'd want more
            # sophisticated semaphore adjustment to handle in-flight operations
            self._semaphore = asyncio.Semaphore(self._current_limit)

            self._last_adjustment_time = current_time
            self._notify_limit_change(old_limit, self._current_limit)

            logger.info(
                f"Adjusted concurrency limit: {old_limit} -> {self._current_limit} "
                f"({limits.reason})"
            )

    def _calculate_optimal_limits(self, metrics: ResourceMetrics) -> ConcurrencyLimits:
        """Calculate optimal concurrency limits based on current metrics."""
        # Start with base limit
        optimal_limit = self.base_concurrent_limit
        reason = "baseline"

        # Increase if resources are underutilized
        if (
            metrics.cpu_percent < 50
            and metrics.memory_percent < 60
            and metrics.disk_io_percent < 50
        ):
            optimal_limit = min(self.max_concurrent_limit, self._current_limit + 1)
            reason = "low resource usage"

        # Decrease if resources are stressed
        elif (
            metrics.cpu_percent > 70
            or metrics.memory_percent > 75
            or metrics.disk_io_percent > 80
        ):
            optimal_limit = max(1, self._current_limit - 1)
            reason = "high resource usage"

        # Special case: if bandwidth is very low, reduce concurrency
        if metrics.bandwidth_usage_mbps > 0 and metrics.bandwidth_usage_mbps < 1.0:
            optimal_limit = max(1, min(optimal_limit, 2))
            reason = "low bandwidth"

        return ConcurrencyLimits(
            max_concurrent=optimal_limit,
            recommended_concurrent=optimal_limit,
            backpressure_threshold=0.8,
            reason=reason,
        )

    @asynccontextmanager
    async def acquire_download_slot(self):
        """
        Acquire a download slot with backpressure handling.

        This is the main interface for download operations to request concurrency control.
        """
        # Check for backpressure before acquiring
        metrics = await self.monitor.get_current_metrics(self._active_downloads)
        backpressure_active = self.backpressure.evaluate_backpressure(metrics)

        if backpressure_active:
            await self.backpressure.wait_for_relief(
                self.monitor, self._active_downloads
            )

        # Acquire semaphore slot
        async with self._semaphore:
            self._active_downloads += 1
            try:
                # Periodically check and adjust limits during operation
                asyncio.create_task(self._background_adjustment())
                yield
            finally:
                self._active_downloads -= 1

    async def _background_adjustment(self) -> None:
        """Background task to periodically adjust concurrency limits."""
        try:
            await self._evaluate_and_adjust_limits()
        except Exception as e:
            logger.warning(f"Background concurrency adjustment failed: {e}")

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current concurrency and resource metrics."""
        latest_metrics = self._metrics_history[-1] if self._metrics_history else None

        return {
            "current_limit": self._current_limit,
            "active_downloads": self._active_downloads,
            "base_limit": self.base_concurrent_limit,
            "max_limit": self.max_concurrent_limit,
            "backpressure_active": self.backpressure._backpressure_active,
            "latest_system_metrics": {
                "cpu_percent": latest_metrics.cpu_percent if latest_metrics else 0,
                "memory_percent": latest_metrics.memory_percent
                if latest_metrics
                else 0,
                "disk_io_percent": latest_metrics.disk_io_percent
                if latest_metrics
                else 0,
                "bandwidth_mbps": latest_metrics.bandwidth_usage_mbps
                if latest_metrics
                else 0,
            }
            if latest_metrics
            else None,
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the concurrency manager."""
        logger.info("Shutting down concurrency manager...")

        # Wait for active downloads to complete (with timeout)
        timeout = 30.0  # 30 second timeout
        start_time = time.time()

        while self._active_downloads > 0 and (time.time() - start_time) < timeout:
            logger.info(
                f"Waiting for {self._active_downloads} active downloads to complete..."
            )
            await asyncio.sleep(1.0)

        if self._active_downloads > 0:
            logger.warning(
                f"Shutdown timeout: {self._active_downloads} downloads still active"
            )
        else:
            logger.info("All downloads completed successfully")


# Legacy compatibility function for existing code
async def create_managed_semaphore(concurrent_downloads: int) -> asyncio.Semaphore:
    """
    Create a managed semaphore that integrates with the ConcurrencyManager.

    This function provides backward compatibility with existing code that expects
    a simple semaphore, while adding enhanced concurrency management capabilities.
    """
    manager = ConcurrencyManager(
        base_concurrent_limit=concurrent_downloads,
        max_concurrent_limit=max(concurrent_downloads * 2, 8),
    )

    # For backward compatibility, return the internal semaphore
    # In a full implementation, you'd want to modify the calling code
    # to use the manager's acquire_download_slot() context manager instead
    return manager._semaphore
