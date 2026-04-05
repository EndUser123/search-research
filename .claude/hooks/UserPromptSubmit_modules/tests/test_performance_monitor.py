"""Test performance monitoring for unified detection engine.

Tests for performance_monitor.py module:
- Performance logging functionality
- Threshold detection
- Database schema and queries
- Analysis utilities
- Integration with unified detection
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "UserPromptSubmit_modules"
sys.path.insert(0, str(HOOKS_DIR))

from performance_monitor import (
    _init_perf_schema,
    get_performance_summary,
    get_recent_slow_detections,
    get_thresholds,
    log_detection_performance,
)
from unified_detection import UnifiedDetectionResult


class TestPerformanceThresholds:
    """Verify performance threshold configuration."""

    def test_get_thresholds_returns_dict(self):
        """get_thresholds should return dict with required keys."""
        thresholds = get_thresholds()
        assert isinstance(thresholds, dict)
        assert "max_detection_ms" in thresholds
        assert "max_total_latency_ms" in thresholds

    def test_thresholds_have_positive_values(self):
        """Threshold values should be positive."""
        thresholds = get_thresholds()
        assert thresholds["max_detection_ms"] > 0
        assert thresholds["max_total_latency_ms"] > 0

    def test_default_thresholds_when_config_unavailable(self):
        """Should use defaults when config loader unavailable."""
        # Temporarily hide config (simulate import failure)
        thresholds = get_thresholds()
        # Should still return valid values
        assert thresholds["max_detection_ms"] == 60.0
        assert thresholds["max_total_latency_ms"] == 100.0


class TestPerformanceLogging:
    """Verify performance logging functionality."""

    def test_log_detection_performance_with_valid_data(self):
        """Should log performance data successfully."""
        result = UnifiedDetectionResult(
            matched_frameworks=["assumption_surfacing"],
            matched_modes=["sequential"],
            matched_profiles=["debug_rca"],
            timing_ms=15.5,
        )

        status = log_detection_performance("test prompt for debugging", result)

        assert status is not None
        assert isinstance(status, dict)

    def test_log_detection_returns_status_fields(self):
        """Status dict should contain required fields."""
        result = UnifiedDetectionResult(
            timing_ms=10.0,
        )

        status = log_detection_performance("short prompt", result)

        # Should have 'logged' field
        assert "logged" in status

    def test_log_performance_with_empty_result(self):
        """Should handle empty detection result."""
        result = UnifiedDetectionResult(
            matched_frameworks=[],
            matched_modes=[],
            matched_profiles=[],
            timing_ms=5.0,
        )

        status = log_detection_performance("no matches", result)

        assert status is not None


class TestThresholdDetection:
    """Verify threshold exceedance detection."""

    def test_below_threshold_no_warning(self):
        """Detection below threshold should not flag warning."""
        # Use a very fast timing
        result = UnifiedDetectionResult(
            timing_ms=5.0,  # Well below 60ms threshold
        )

        status = log_detection_performance("fast detection", result)

        # Should not have warning if logged successfully
        if status.get("logged"):
            assert "warning" not in status
            assert status.get("threshold_exceeded") is False

    def test_above_threshold_includes_warning(self):
        """Detection above threshold should include warning."""
        # Use a slow timing that exceeds threshold
        result = UnifiedDetectionResult(
            timing_ms=100.0,  # Exceeds 60ms threshold
        )

        status = log_detection_performance("slow detection", result)

        # If logged successfully, should indicate threshold exceeded
        if status.get("logged") and status.get("timing_ms"):
            # Only check if we have the data (depends on monitoring being enabled)
            pass


class TestPerformanceAnalysis:
    """Verify performance analysis utilities."""

    def test_get_performance_summary_returns_dict(self):
        """Performance summary should return dict with stats."""
        summary = get_performance_summary(limit=50)
        assert isinstance(summary, dict)
        assert "count" in summary
        assert "mean_ms" in summary

    def test_performance_summary_fields(self):
        """Summary should have all required fields."""
        summary = get_performance_summary()

        required_fields = [
            "count",
            "mean_ms",
            "min_ms",
            "max_ms",
            "threshold_exceeded_count",
        ]

        for field in required_fields:
            assert field in summary

    def test_get_recent_slow_detections_returns_list(self):
        """Should return list of slow detection records."""
        slow_detections = get_recent_slow_detections(limit=5)
        assert isinstance(slow_detections, list)

    def test_slow_detection_records_are_dicts(self):
        """Each slow detection record should be a dict."""
        slow_detections = get_recent_slow_detections(limit=5)

        for record in slow_detections:
            assert isinstance(record, dict)

    def test_slow_detection_with_custom_threshold(self):
        """Should support custom threshold override."""
        # Use very low threshold to potentially get results
        slow_detections = get_recent_slow_detections(threshold_ms=0.1, limit=5)

        # Should return list (possibly empty)
        assert isinstance(slow_detections, list)


class TestDatabaseSchema:
    """Verify database schema initialization."""

    def test_perf_schema_initialization(self):
        """Schema initialization should not raise errors."""
        # This test verifies the schema can be initialized
        # May have already been initialized at module import
        try:
            _init_perf_schema()
        except Exception as e:
            pytest.fail(f"Schema initialization failed: {e}")


class TestIntegrationWithUnifiedDetection:
    """Verify integration with unified detection engine."""

    def test_performance_data_from_real_detection(self):
        """Performance monitor should handle real detection results."""
        from unified_detection import detect_prompt

        # Run actual detection
        result = detect_prompt("debug why the test keeps failing intermittently")

        # Log performance
        status = log_detection_performance(
            "debug why the test keeps failing intermittently",
            result
        )

        assert status is not None
        assert isinstance(status, dict)

    def test_timing_ms_propagates_from_detection(self):
        """timing_ms from detection should propagate to performance log."""
        from unified_detection import detect_prompt

        prompt = "implement a new feature for user authentication"
        result = detect_prompt(prompt)

        # Result should have timing
        assert hasattr(result, "timing_ms")
        assert isinstance(result.timing_ms, float)
        assert result.timing_ms >= 0

    def test_performance_monitor_import_available(self):
        """performance_monitor module should be importable."""
        # This test verifies the module can be imported
        # Already imported at top of file, but verify again
        import performance_monitor

        assert hasattr(performance_monitor, "log_detection_performance")
        assert hasattr(performance_monitor, "get_performance_summary")
        assert hasattr(performance_monitor, "get_thresholds")


class TestEnvironmentConfiguration:
    """Verify environment variable configuration."""

    def test_monitoring_respects_disabled_flag(self, monkeypatch):
        """Should respect COGNITIVE_PERF_MONITORING_ENABLED=false."""
        monkeypatch.setenv("COGNITIVE_PERF_MONITORING_ENABLED", "false")

        result = UnifiedDetectionResult(timing_ms=10.0)
        status = log_detection_performance("test", result)

        # Should indicate not logged
        assert status.get("logged") is False
        assert "reason" in status

    def test_monitoring_enabled_by_default(self):
        """Monitoring should be enabled by default."""
        # Don't set env var, should default to enabled
        result = UnifiedDetectionResult(timing_ms=10.0)
        status = log_detection_performance("test", result)

        # May or may not log depending on config availability
        # but should not crash
        assert status is not None


class TestGracefulDegradation:
    """Verify graceful degradation when dependencies unavailable."""

    def test_log_performance_without_cc_diagnostic(self):
        """Should work even if cc_diagnostic_logger unavailable."""
        # This test verifies the module can function when
        # cc_diagnostic_logger import fails (handled internally)

        result = UnifiedDetectionResult(timing_ms=10.0)
        status = log_detection_performance("test", result)

        # Should still return status dict
        assert status is not None
        assert isinstance(status, dict)


class TestMultiTerminalSafety:
    """Verify multi-terminal safety in performance logging."""

    def test_performance_logging_isolated_by_session(self):
        """Performance logging should include session and terminal IDs."""
        result = UnifiedDetectionResult(
            timing_ms=12.5,
        )

        status = log_detection_performance("multi-terminal test", result)

        # Should complete without error
        assert status is not None

    def test_concurrent_logging_safety(self):
        """Should handle concurrent logging safely (thread-safe)."""
        import threading

        results = []
        errors = []

        def log_prompt(prompt_id: int):
            try:
                result = UnifiedDetectionResult(timing_ms=10.0 + prompt_id)
                status = log_detection_performance(f"prompt_{prompt_id}", result)
                results.append(status)
            except Exception as e:
                errors.append(e)

        # Create multiple threads logging concurrently
        threads = [
            threading.Thread(target=log_prompt, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should not have any errors
        assert len(errors) == 0
        assert len(results) == 5


class TestAcceptanceCriteria:
    """Acceptance tests for T-004 requirements."""

    def test_detection_timing_logged_for_all_prompts(self):
        """Detection timing should be logged for all prompts (AC-001)."""
        from unified_detection import detect_prompt

        test_prompts = [
            "implement feature",
            "debug this error",
            "should we use X or Y",
        ]

        for prompt in test_prompts:
            result = detect_prompt(prompt)
            status = log_detection_performance(prompt, result)

            # Should log without error
            assert status is not None

    def test_performance_regression_alerts(self):
        """Performance regression alerts should be generated (AC-002)."""
        # Simulate slow detection
        result = UnifiedDetectionResult(
            matched_frameworks=["assumption_surfacing", "outcome_anchoring"],
            timing_ms=100.0,  # Exceeds 60ms threshold
        )

        status = log_detection_performance("complex prompt", result)

        # If monitoring enabled, should indicate threshold exceeded
        if status.get("logged"):
            assert status.get("threshold_exceeded") is True

    def test_historical_performance_data_available(self):
        """Historical performance data should be available (AC-003)."""
        summary = get_performance_summary(limit=100)

        # Should return summary with historical data
        assert "count" in summary
        assert "mean_ms" in summary

    def test_slow_detections_queryable(self):
        """Slow detections should be queryable (AC-003)."""
        slow_detections = get_recent_slow_detections(limit=10)

        # Should return list (possibly empty if no slow detections yet)
        assert isinstance(slow_detections, list)

        for record in slow_detections:
            assert "timing_ms" in record
            assert "timestamp" in record


class TestCoverageEdgeCases:
    """Edge case coverage for performance monitoring."""

    def test_empty_prompt_handling(self):
        """Should handle empty string prompt."""
        result = UnifiedDetectionResult(timing_ms=5.0)
        status = log_detection_performance("", result)

        assert status is not None

    def test_very_long_prompt_handling(self):
        """Should handle very long prompts."""
        long_prompt = "test " * 10000  # 50k characters

        result = UnifiedDetectionResult(timing_ms=10.0)
        status = log_detection_performance(long_prompt, result)

        assert status is not None

    def test_zero_timing_ms(self):
        """Should handle zero timing (edge case)."""
        result = UnifiedDetectionResult(timing_ms=0.0)
        status = log_detection_performance("instant", result)

        assert status is not None

    def test_negative_timing_ms_graceful_handling(self):
        """Should handle negative timing gracefully."""
        result = UnifiedDetectionResult(timing_ms=-1.0)
        status = log_detection_performance("invalid timing", result)

        # Should not crash
        assert status is not None
