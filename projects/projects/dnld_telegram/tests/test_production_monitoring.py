"""
Test suite for Production Monitoring & Health Checks - Task P3C

Requirements tested:
- System health monitoring
- Metrics collection
- Production readiness

Test Categories:
- Unit tests for individual components
- Integration tests for component interaction
- Health check aggregation tests
- Metrics collection tests
"""

import asyncio

import pytest


class TestProductionMonitoring:
    """Test class for Production Monitoring functionality"""

    @pytest.mark.asyncio
    async def test_system_health_aggregation(self):
        """Test aggregated system health check"""
        from src.monitoring.health import SystemHealthChecker

        health_checker = SystemHealthChecker()
        health_report = await health_checker.check_all_systems()

        assert "overall_status" in health_report
        assert "components" in health_report
        assert "timestamp" in health_report

        # Should check key components
        components = health_report["components"]
        assert "database" in components
        assert "download_service" in components
        assert "file_system" in components

        # Each component should have status
        for component_name, component_health in components.items():
            assert "status" in component_health
            assert component_health["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics collection for monitoring"""
        from src.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()

        # Simulate some operations
        await collector.record_download_start("test_file.mp4")
        await asyncio.sleep(0.01)
        await collector.record_download_complete("test_file.mp4", 1024 * 1024)

        # Get current metrics
        metrics = await collector.get_current_metrics()

        assert "active_downloads" in metrics
        assert "completed_downloads" in metrics
        assert "total_bytes_downloaded" in metrics
        assert "average_download_speed" in metrics

        assert metrics["completed_downloads"] >= 1
        assert metrics["total_bytes_downloaded"] >= 1024 * 1024
