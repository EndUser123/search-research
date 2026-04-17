"""Tests for backend health check interface.

Tests health check functionality for all search providers following TDD methodology:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass tests
- REFACTOR: Clean up implementation
"""

import asyncio
from typing import Any

import pytest

from search_research.backend_health import BackendHealthRegistry
from search_research.providers.base_web import BaseWebBackend
from search_research.providers.provider_health import ProviderHealthStatus


class MockHealthyBackend(BaseWebBackend):
    """Mock backend that always returns healthy."""

    @property
    def name(self) -> str:
        return "mock_healthy"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def api_key_env_var(self) -> str:
        return "MOCK_API_KEY"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 5.0,
        **kwargs,
    ) -> list[dict[str, Any]]:
        return [{"title": "Test", "url": "http://test.com", "content": "Test content"}]

    async def check_health(self, timeout: float = 5.0) -> ProviderHealthStatus:
        """Health check that always returns healthy."""
        return ProviderHealthStatus(healthy=True, latency_ms=50.0, error=None)


class MockUnhealthyBackend(BaseWebBackend):
    """Mock backend that always returns unhealthy."""

    @property
    def name(self) -> str:
        return "mock_unhealthy"

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def api_key_env_var(self) -> str:
        return "MISSING_API_KEY"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 5.0,
        **kwargs,
    ) -> list[dict[str, Any]]:
        raise ValueError("API key missing")

    async def check_health(self, timeout: float = 5.0) -> ProviderHealthStatus:
        """Health check that always returns unhealthy."""
        return ProviderHealthStatus(
            healthy=False,
            latency_ms=0.0,
            error="API key not configured"
        )


class MockTimeoutBackend(BaseWebBackend):
    """Mock backend that times out."""

    @property
    def name(self) -> str:
        return "mock_timeout"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def api_key_env_var(self) -> str:
        return "MOCK_API_KEY"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 5.0,
        **kwargs,
    ) -> list[dict[str, Any]]:
        await asyncio.sleep(10)  # Exceed timeout
        return []

    async def check_health(self, timeout: float = 5.0) -> ProviderHealthStatus:
        """Health check that times out."""
        await asyncio.sleep(timeout + 1)
        return ProviderHealthStatus(healthy=False, latency_ms=timeout * 1000, error="Timeout")


class TestHealthCheckInterface:
    """Tests for health check interface on backends."""

    @pytest.mark.asyncio
    async def test_healthy_backend_check(self):
        """Test that healthy backend returns healthy status."""
        backend = MockHealthyBackend()
        status = await backend.check_health(timeout=5.0)

        assert status.healthy is True
        assert status.latency_ms > 0
        assert status.error is None

    @pytest.mark.asyncio
    async def test_unhealthy_backend_check(self):
        """Test that unhealthy backend returns unhealthy status."""
        backend = MockUnhealthyBackend()
        status = await backend.check_health(timeout=5.0)

        assert status.healthy is False
        assert status.error is not None
        assert "API key" in status.error

    @pytest.mark.asyncio
    async def test_timeout_backend_check(self):
        """Test that timeout backend returns unhealthy status."""
        backend = MockTimeoutBackend()
        status = await backend.check_health(timeout=0.1)

        assert status.healthy is False
        assert status.error == "Timeout"

    @pytest.mark.asyncio
    async def test_custom_timeout(self):
        """Test that custom timeout is respected."""
        backend = MockHealthyBackend()
        status = await backend.check_health(timeout=10.0)

        assert status.healthy is True
        assert status.latency_ms < 10000  # Should complete quickly


class TestBackendHealthRegistry:
    """Tests for backend health registry."""

    def setup_method(self):
        """Reset registry state before each test."""
        registry = BackendHealthRegistry()
        registry._reset()

    def test_get_status_unknown_backend(self):
        """Test getting status for unknown backend returns None."""
        registry = BackendHealthRegistry()
        status = registry.get_status("unknown_backend")

        assert status is None

    def test_is_available_unknown_backend(self):
        """Test that unknown backend is considered available."""
        registry = BackendHealthRegistry()
        available = registry.is_available("unknown_backend")

        assert available is True

    def test_record_success(self):
        """Test recording successful backend result."""
        registry = BackendHealthRegistry()
        registry.record_result("test_backend", success=True)

        status = registry.get_status("test_backend")
        assert status is not None
        assert status.status == "ready"
        assert status.consecutive_failures == 0
        assert status.last_error is None

    def test_record_failure(self):
        """Test recording failed backend result."""
        registry = BackendHealthRegistry()
        registry.record_result("test_backend", success=False, error="Connection failed")

        status = registry.get_status("test_backend")
        assert status is not None
        assert status.status == "degraded"
        assert status.consecutive_failures == 1
        assert status.last_error == "Connection failed"

    def test_record_multiple_failures(self):
        """Test that multiple failures mark backend as down."""
        registry = BackendHealthRegistry()

        # Record 3 failures for SAME backend
        for _ in range(3):
            registry.record_result("test_backend", success=False, error="Failed")

        status = registry.get_status("test_backend")
        assert status is not None
        assert status.status == "down"
        assert status.consecutive_failures == 3
        assert status.should_retry() is False  # Within backoff period

    def test_recovery_after_success(self):
        """Test that success after failure resets health."""
        registry = BackendHealthRegistry()

        # Record failures
        registry.record_result("test_backend", success=False, error="Failed")
        registry.record_result("test_backend", success=False, error="Failed")

        # Record success
        registry.record_result("test_backend", success=True)

        status = registry.get_status("test_backend")
        assert status is not None
        assert status.status == "ready"
        assert status.consecutive_failures == 0
        assert status.last_error is None

    def test_exponential_backoff(self):
        """Test that backoff time increases exponentially."""
        registry = BackendHealthRegistry()

        # Record failures and check backoff times
        expected_backoffs = [5, 10, 20, 40, 80, 160, 300]

        for i, expected_backoff in enumerate(expected_backoffs):
            registry.record_result(f"backend_{i}", success=False, error=f"Failure {i}")
            status = registry.get_status(f"backend_{i}")
            assert status is not None

            # Check that consecutive_failures matches
            assert status.consecutive_failures == 1

    def test_get_all_status(self):
        """Test getting status of all backends."""
        registry = BackendHealthRegistry()

        # Record results for multiple backends
        registry.record_result("backend1", success=True)
        registry.record_result("backend2", success=False, error="Failed")
        registry.record_result("backend3", success=True)

        all_status = registry.get_all_status()
        # Should have at least our 3 backends
        assert len(all_status) >= 3
        assert "backend1" in all_status
        assert "backend2" in all_status
        assert "backend3" in all_status

    def test_is_available_during_backoff(self):
        """Test that backend is not available during backoff period."""
        registry = BackendHealthRegistry()

        # Record 3 failures to trigger down status
        for _ in range(3):
            registry.record_result("test_backend", success=False, error="Failed")

        # Backend should not be available during backoff
        available = registry.is_available("test_backend")
        assert available is False

    def test_is_available_after_backoff(self):
        """Test that backend is available after backoff period."""
        registry = BackendHealthRegistry()

        # Record failures
        for _ in range(3):
            registry.record_result("test_backend", success=False, error="Failed")

        # Manually set next_retry to past
        status = registry.get_status("test_backend")
        if status:
            status.next_retry = 0  # Past timestamp

        # Backend should be available after backoff
        available = registry.is_available("test_backend")
        assert available is True


class TestHealthCheckIntegration:
    """Integration tests for health checks with registry."""

    @pytest.mark.asyncio
    async def test_successful_health_check_updates_registry(self):
        """Test that successful health check updates registry."""
        registry = BackendHealthRegistry()
        backend = MockHealthyBackend()

        # Perform health check
        status = await backend.check_health(timeout=5.0)

        # Record result in registry
        registry.record_result(backend.name, success=status.healthy)

        # Verify registry updated
        health = registry.get_status(backend.name)
        assert health is not None
        assert health.status == "ready"

    @pytest.mark.asyncio
    async def test_failed_health_check_updates_registry(self):
        """Test that failed health check updates registry."""
        registry = BackendHealthRegistry()
        backend = MockUnhealthyBackend()

        # Perform health check
        status = await backend.check_health(timeout=5.0)

        # Record result in registry
        registry.record_result(
            backend.name,
            success=status.healthy,
            error=status.error
        )

        # Verify registry updated
        health = registry.get_status(backend.name)
        assert health is not None
        assert health.status == "degraded"
        assert health.last_error == status.error

    @pytest.mark.asyncio
    async def test_backend_availability_after_health_check(self):
        """Test that backend availability is determined by health check."""
        registry = BackendHealthRegistry()
        backend = MockHealthyBackend()

        # Perform health check and record result
        status = await backend.check_health(timeout=5.0)
        registry.record_result(backend.name, success=status.healthy)

        # Check availability
        available = registry.is_available(backend.name)
        assert available is True
