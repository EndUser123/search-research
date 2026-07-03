"""
Tests for DX Tools Observability Layer

Tests metrics tracking and health checks for DX tools.
"""
import json
import sys
from pathlib import Path

# Add __lib to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from dx_tools_observability import DXToolsHealth, DXToolsMetrics, get_metrics


class TestDXToolsMetrics:
    """Test DXToolsMetrics class functionality."""

    def test_record_event(self):
        """Test recording events increments counters."""
        metrics = DXToolsMetrics()

        metrics.record_event("cache", "cleared", 5)
        metrics.record_event("cache", "cleared", 3)
        metrics.record_event("cache", "error", 1)

        result = metrics.get_metrics("cache")
        assert result["cleared"] == 8
        assert result["error"] == 1

    def test_start_end_timer(self):
        """Test timing operations tracks duration."""
        metrics = DXToolsMetrics()

        metrics.start_timer("test_operation")
        metrics.end_timer("test_operation")

        perf_metrics = metrics.get_metrics("performance")
        assert "test_operation_ms" in perf_metrics
        assert perf_metrics["test_operation_ms"] > 0

    def test_get_metrics_with_category(self):
        """Test getting metrics for specific category."""
        metrics = DXToolsMetrics()

        metrics.record_event("auth", "auto_approved", 10)
        metrics.record_event("auth", "blocked", 2)
        metrics.record_event("cache", "cleared", 5)

        auth_metrics = metrics.get_metrics("auth")
        assert auth_metrics["auto_approved"] == 10
        assert auth_metrics["blocked"] == 2
        assert "cleared" not in auth_metrics

    def test_get_metrics_all_categories(self):
        """Test getting all metrics returns copy."""
        metrics = DXToolsMetrics()

        metrics.record_event("cache", "cleared", 5)
        metrics.record_event("auth", "auto_approved", 10)

        all_metrics = metrics.get_metrics()
        assert "cache" in all_metrics
        assert "auth" in all_metrics
        assert all_metrics["cache"]["cleared"] == 5
        assert all_metrics["auth"]["auto_approved"] == 10

    def test_persist_metrics(self, tmp_path):
        """Test metrics are persisted to JSONL file."""
        metrics_file = tmp_path / "test_metrics.jsonl"
        metrics = DXToolsMetrics(metrics_dir=tmp_path)

        metrics.record_event("cache", "cleared", 5)
        metrics.flush()

        # Verify file was created
        assert metrics_file.exists()

        # Verify JSONL format
        with open(metrics_file) as f:
            lines = f.readlines()
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert "timestamp" in entry
            assert "metrics" in entry
            assert entry["metrics"]["cache"]["cleared"] == 5

    def test_health_check_cache_manager(self):
        """Test health check for cache manager component."""
        health = DXToolsHealth.check_cache_manager()

        assert "component" in health
        assert health["component"] == "cache_manager"
        assert "overall" in health
        assert health["overall"] in ("healthy", "unhealthy", "unknown")
        assert "checks" in health

    def test_health_check_authorization_gate(self):
        """Test health check for authorization gate component."""
        health = DXToolsHealth.check_authorization_gate()

        assert "component" in health
        assert health["component"] == "authorization_gate"
        assert "overall" in health
        assert "checks" in health

    def test_get_health_report(self):
        """Test comprehensive health report includes all components."""
        report = DXToolsHealth.get_health_report()

        assert "timestamp" in report
        assert "overall" in report
        assert "components" in report
        assert len(report["components"]) >= 2

    def test_singleton_get_metrics(self):
        """Test get_metrics returns same instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    def test_thread_safety(self):
        """Test metrics are thread-safe."""
        import threading

        metrics = DXToolsMetrics()
        errors = []

        def increment_counter():
            try:
                for _ in range(100):
                    metrics.record_event("test", "counter", 1)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=increment_counter) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify no errors and correct count
        assert len(errors) == 0
        result = metrics.get_metrics("test")
        assert result["counter"] == 1000
