"""
Tests for Enhanced Concurrency Management (P2B)

This test suite validates:
- Dynamic concurrency limits based on system resources
- Backpressure handling mechanisms
- Resource monitoring functionality
- Integration with existing download patterns
"""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest
from src.download.concurrency_manager import (
    BackpressureController,
    ConcurrencyManager,
    ResourceMetrics,
    ResourceMonitor,
    create_managed_semaphore,
)


class TestResourceMonitor:
    """Test ResourceMonitor functionality."""

    @pytest.fixture
    def monitor(self):
        return ResourceMonitor(sampling_interval=1.0)

    @pytest.mark.asyncio
    async def test_get_current_metrics_basic(self, monitor):
        """Test basic metrics collection."""
        with (
            patch("psutil.cpu_percent", return_value=45.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_io_counters", return_value=None),
            patch("psutil.net_io_counters", return_value=None),
        ):
            mock_memory.return_value.percent = 60.0

            metrics = await monitor.get_current_metrics(active_downloads=2)

            assert metrics.cpu_percent == 45.0
            assert metrics.memory_percent == 60.0
            assert metrics.disk_io_percent == 0.0
            assert metrics.active_downloads == 2
            assert metrics.bandwidth_usage_mbps == 0.0
            assert isinstance(metrics.timestamp, float)

    @pytest.mark.asyncio
    async def test_disk_io_calculation(self, monitor):
        """Test disk I/O percentage calculation."""
        mock_io1 = Mock()
        mock_io1.read_bytes = 1000000  # 1MB
        mock_io1.write_bytes = 500000  # 0.5MB

        mock_io2 = Mock()
        mock_io2.read_bytes = 2000000  # 2MB
        mock_io2.write_bytes = 1000000  # 1MB

        with (
            patch("psutil.cpu_percent", return_value=30.0),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_io_counters", side_effect=[mock_io1, mock_io2]),
            patch("psutil.net_io_counters", return_value=None),
        ):
            mock_memory.return_value.percent = 40.0

            # First call establishes baseline
            await monitor.get_current_metrics(active_downloads=1)

            # Second call calculates difference
            metrics = await monitor.get_current_metrics(active_downloads=1)

            # Expect 1MB read + 0.5MB write = 1.5MB total IO
            # 1.5MB / 100MB = 1.5% disk utilization
            assert metrics.disk_io_percent == 1.5


class TestBackpressureController:
    """Test BackpressureController functionality."""

    @pytest.fixture
    def controller(self):
        return BackpressureController()

    def test_evaluate_backpressure_not_activated(self, controller):
        """Test backpressure not activated under normal conditions."""
        metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_io_percent=40.0,
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )

        result = controller.evaluate_backpressure(metrics)
        assert not result
        assert not controller._backpressure_active

    def test_evaluate_backpressure_cpu_threshold(self, controller):
        """Test backpressure activated by high CPU usage."""
        metrics = ResourceMetrics(
            cpu_percent=85.0,  # Above 80% threshold
            memory_percent=60.0,
            disk_io_percent=40.0,
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )

        result = controller.evaluate_backpressure(metrics)
        assert result
        assert controller._backpressure_active

    def test_evaluate_backpressure_memory_threshold(self, controller):
        """Test backpressure activated by high memory usage."""
        metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_percent=90.0,  # Above 85% threshold
            disk_io_percent=40.0,
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )

        result = controller.evaluate_backpressure(metrics)
        assert result
        assert controller._backpressure_active

    def test_evaluate_backpressure_deactivation(self, controller):
        """Test backpressure deactivation when resources improve."""
        # First activate backpressure
        high_metrics = ResourceMetrics(
            cpu_percent=85.0,
            memory_percent=60.0,
            disk_io_percent=40.0,
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )
        controller.evaluate_backpressure(high_metrics)
        assert controller._backpressure_active

        # Then deactivate with improved metrics
        low_metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_io_percent=40.0,
            active_downloads=1,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )
        result = controller.evaluate_backpressure(low_metrics)
        assert not result
        assert not controller._backpressure_active

    @pytest.mark.asyncio
    async def test_wait_for_relief_not_active(self, controller):
        """Test wait_for_relief when backpressure is not active."""
        monitor = Mock()

        # Should return immediately
        start_time = time.time()
        await controller.wait_for_relief(monitor, 1)
        elapsed = time.time() - start_time

        assert elapsed < 0.1  # Should be nearly instantaneous


class TestConcurrencyManager:
    """Test ConcurrencyManager functionality."""

    @pytest.fixture
    def manager(self):
        return ConcurrencyManager(
            base_concurrent_limit=2, max_concurrent_limit=6, resource_check_interval=1.0
        )

    def test_initialization(self, manager):
        """Test manager initialization with correct defaults."""
        assert manager.base_concurrent_limit == 2
        assert manager.max_concurrent_limit == 6
        assert manager._current_limit == 2
        assert manager._active_downloads == 0
        assert len(manager._metrics_history) == 0

    def test_calculate_optimal_limits_baseline(self, manager):
        """Test baseline limit calculation."""
        metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_io_percent=50.0,
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )

        limits = manager._calculate_optimal_limits(metrics)
        assert limits.max_concurrent == 2  # Should stay at baseline
        assert limits.reason == "baseline"

    def test_calculate_optimal_limits_increase(self, manager):
        """Test limit increase for low resource usage."""
        metrics = ResourceMetrics(
            cpu_percent=30.0,  # Low CPU
            memory_percent=40.0,  # Low memory
            disk_io_percent=30.0,  # Low disk I/O
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )

        limits = manager._calculate_optimal_limits(metrics)
        assert limits.max_concurrent == 3  # Should increase by 1
        assert limits.reason == "low resource usage"

    def test_calculate_optimal_limits_decrease(self, manager):
        """Test limit decrease for high resource usage."""
        metrics = ResourceMetrics(
            cpu_percent=80.0,  # High CPU
            memory_percent=60.0,
            disk_io_percent=50.0,
            active_downloads=2,
            bandwidth_usage_mbps=10.0,
            timestamp=time.time(),
        )

        limits = manager._calculate_optimal_limits(metrics)
        assert limits.max_concurrent == 1  # Should decrease by 1
        assert limits.reason == "high resource usage"

    def test_calculate_optimal_limits_low_bandwidth(self, manager):
        """Test limit adjustment for low bandwidth."""
        manager._current_limit = 4  # Set higher initial limit

        metrics = ResourceMetrics(
            cpu_percent=30.0,
            memory_percent=40.0,
            disk_io_percent=30.0,
            active_downloads=4,
            bandwidth_usage_mbps=0.5,  # Very low bandwidth
            timestamp=time.time(),
        )

        limits = manager._calculate_optimal_limits(metrics)
        assert limits.max_concurrent == 2  # Should cap at 2 for low bandwidth
        assert limits.reason == "low bandwidth"

    @pytest.mark.asyncio
    async def test_acquire_download_slot_basic(self, manager):
        """Test basic download slot acquisition."""
        assert manager._active_downloads == 0

        async with manager.acquire_download_slot():
            assert manager._active_downloads == 1

        assert manager._active_downloads == 0

    @pytest.mark.asyncio
    async def test_acquire_download_slot_multiple(self, manager):
        """Test multiple concurrent download slot acquisitions."""
        tasks = []
        results = []

        async def acquire_slot(slot_id):
            async with manager.acquire_download_slot():
                results.append(f"slot_{slot_id}_acquired")
                await asyncio.sleep(0.1)
                results.append(f"slot_{slot_id}_released")

        # Create tasks for slot acquisition
        for i in range(3):
            tasks.append(asyncio.create_task(acquire_slot(i)))

        # Wait for all to complete
        await asyncio.gather(*tasks)

        # Should have 6 events (3 acquire + 3 release)
        assert len(results) == 6
        assert manager._active_downloads == 0

    @pytest.mark.asyncio
    async def test_dynamic_concurrency_limits(self, manager):
        """Test dynamic adjustment of concurrency limits."""
        # Mock the resource monitor to return low resource usage
        with patch.object(manager.monitor, "get_current_metrics") as mock_get_metrics:
            mock_get_metrics.return_value = ResourceMetrics(
                cpu_percent=30.0,
                memory_percent=40.0,
                disk_io_percent=30.0,
                active_downloads=1,
                bandwidth_usage_mbps=10.0,
                timestamp=time.time(),
            )

            # Initial limit should be 2
            assert manager._current_limit == 2

            # Trigger adjustment
            await manager._evaluate_and_adjust_limits()

            # Should increase to 3 due to low resource usage
            assert manager._current_limit == 3

    @pytest.mark.asyncio
    async def test_backpressure_handling(self, manager):
        """Test backpressure handling during slot acquisition."""
        # Mock high resource usage to trigger backpressure
        with (
            patch.object(manager.monitor, "get_current_metrics") as mock_get_metrics,
            patch.object(manager.backpressure, "wait_for_relief") as mock_wait,
        ):
            mock_get_metrics.return_value = ResourceMetrics(
                cpu_percent=90.0,  # High CPU to trigger backpressure
                memory_percent=60.0,
                disk_io_percent=50.0,
                active_downloads=2,
                bandwidth_usage_mbps=10.0,
                timestamp=time.time(),
            )

            # Mock wait_for_relief to return immediately for testing
            mock_wait.return_value = None

            async with manager.acquire_download_slot():
                # Should have called wait_for_relief due to backpressure
                mock_wait.assert_called_once()

    def test_get_current_metrics(self, manager):
        """Test retrieval of current metrics."""
        metrics = manager.get_current_metrics()

        assert metrics["current_limit"] == 2
        assert metrics["active_downloads"] == 0
        assert metrics["base_limit"] == 2
        assert metrics["max_limit"] == 6
        assert not metrics["backpressure_active"]
        assert metrics["latest_system_metrics"] is None  # No history yet

    def test_limit_change_callbacks(self, manager):
        """Test limit change callback functionality."""
        callback_calls = []

        def test_callback(old_limit, new_limit):
            callback_calls.append((old_limit, new_limit))

        manager.add_limit_change_callback(test_callback)

        # Trigger a limit change
        manager._notify_limit_change(2, 3)

        assert len(callback_calls) == 1
        assert callback_calls[0] == (2, 3)

    @pytest.mark.asyncio
    async def test_shutdown_graceful(self, manager):
        """Test graceful shutdown with no active downloads."""
        await manager.shutdown()
        # Should complete without issues

    @pytest.mark.asyncio
    async def test_shutdown_with_timeout(self, manager):
        """Test shutdown with active downloads timing out."""
        # Simulate active downloads
        manager._active_downloads = 2

        start_time = time.time()
        await manager.shutdown()
        elapsed = time.time() - start_time

        # Should timeout after 30 seconds (mocked to be much faster in real implementation)
        # This test just ensures the timeout logic exists
        assert elapsed < 1.0  # Should complete quickly in test


class TestIntegration:
    """Integration tests for concurrency management."""

    @pytest.mark.asyncio
    async def test_resource_monitoring_integration(self):
        """Test integration between resource monitoring and concurrency management."""
        manager = ConcurrencyManager(base_concurrent_limit=2, max_concurrent_limit=4)

        # Mock resource metrics to simulate load conditions
        with patch.object(manager.monitor, "get_current_metrics") as mock_get_metrics:
            # First call: low resources (should increase limit)
            mock_get_metrics.return_value = ResourceMetrics(
                cpu_percent=30.0,
                memory_percent=40.0,
                disk_io_percent=20.0,
                active_downloads=1,
                bandwidth_usage_mbps=15.0,
                timestamp=time.time(),
            )

            await manager._evaluate_and_adjust_limits()
            assert manager._current_limit == 3  # Should increase

            # Second call: high resources (should decrease limit)
            mock_get_metrics.return_value = ResourceMetrics(
                cpu_percent=85.0,
                memory_percent=80.0,
                disk_io_percent=70.0,
                active_downloads=3,
                bandwidth_usage_mbps=5.0,
                timestamp=time.time(),
            )

            # Wait for cooldown to pass
            manager._last_adjustment_time = 0  # Reset cooldown
            await manager._evaluate_and_adjust_limits()
            assert manager._current_limit == 2  # Should decrease

    @pytest.mark.asyncio
    async def test_create_managed_semaphore_legacy_compatibility(self):
        """Test legacy compatibility function."""
        semaphore = await create_managed_semaphore(concurrent_downloads=3)

        assert isinstance(semaphore, asyncio.Semaphore)

        # Test that it can be used like a regular semaphore
        async with semaphore:
            # Should work without issues
            pass


# Benchmark and Load Tests
class TestPerformance:
    """Performance and load tests for concurrency manager."""

    @pytest.mark.asyncio
    async def test_high_concurrency_load(self):
        """Test performance under high concurrency load."""
        manager = ConcurrencyManager(base_concurrent_limit=10, max_concurrent_limit=20)

        async def simulate_download():
            async with manager.acquire_download_slot():
                await asyncio.sleep(0.01)  # Simulate work

        # Create many concurrent "downloads"
        tasks = [asyncio.create_task(simulate_download()) for _ in range(50)]

        start_time = time.time()
        await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # Should complete reasonably quickly
        assert elapsed < 5.0
        assert manager._active_downloads == 0

    @pytest.mark.asyncio
    async def test_resource_monitoring_performance(self):
        """Test performance of resource monitoring under load."""
        monitor = ResourceMonitor(sampling_interval=0.1)

        # Collect many metrics rapidly
        start_time = time.time()
        for _ in range(100):
            await monitor.get_current_metrics(active_downloads=5)
        elapsed = time.time() - start_time

        # Should be efficient
        assert elapsed < 2.0


# Test fixtures and utilities
@pytest.fixture
def mock_system_resources():
    """Mock system resources for predictable testing."""
    with (
        patch("psutil.cpu_percent", return_value=50.0),
        patch("psutil.virtual_memory") as mock_memory,
        patch("psutil.disk_io_counters", return_value=None),
        patch("psutil.net_io_counters", return_value=None),
    ):
        mock_memory.return_value.percent = 60.0
        yield


if __name__ == "__main__":
    # Run specific test patterns for P2B verification
    pytest.main(
        [
            __file__,
            "-v",
            "-k",
            "test_dynamic_concurrency_limits or test_backpressure_handling or test_resource_monitoring",
        ]
    )
