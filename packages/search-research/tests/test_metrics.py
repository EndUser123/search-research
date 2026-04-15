"""RED phase tests for MetricsLogger (TASK-1 of search-research instrumentation plan).

These tests document the expected behavior of the metrics system.
Tests are designed to FAIL initially (RED phase) until implementation is complete.

Run with: pytest tests/test_metrics.py -v
"""

import json
import time
from unittest.mock import patch

import pytest


class TestMetricsImport:
    """Acceptance Criterion 1: MetricsLogger importable."""

    def test_metrics_logger_importable(self):
        """MetricsLogger and ComponentName must be importable from search_research.metrics."""
        from search_research.metrics import MetricsLogger, ComponentName

        assert MetricsLogger is not None
        assert ComponentName is not None


class TestComponentNameEnum:
    """Acceptance Criterion 2: ComponentName enum contains required values."""

    def test_component_name_enum_values(self):
        """ComponentName enum must contain all required component values."""
        from search_research.metrics import ComponentName

        expected_components = [
            "QMD_WIKI",
            "YT_IS",
            "CLAUDE_HISTORY",
            "HYDE",
            "SEARCH_PROVIDER",
            "SYNTHESIS",
            "CONTRADICTION",
            "COVERAGE_GATE",
            "CRAG_GRADE",
        ]
        for comp in expected_components:
            assert hasattr(ComponentName, comp), f"ComponentName missing: {comp}"


class TestMetricsLoggerInit:
    """Acceptance Criterion 3: MetricsLogger instantiates correctly."""

    def test_logger_instantiates_with_default_path(self, tmp_path):
        """MetricsLogger(log_path='logs/metrics.jsonl') instantiates without error."""
        from search_research.metrics import MetricsLogger

        log_path = tmp_path / "logs" / "metrics.jsonl"
        logger = MetricsLogger(log_path=str(log_path))
        assert logger is not None

    def test_logger_creates_logs_dir_if_missing(self, tmp_path):
        """MetricsLogger creates logs/ directory if it does not exist."""
        from search_research.metrics import MetricsLogger

        log_path = tmp_path / "logs" / "metrics.jsonl"
        assert not log_path.parent.exists()
        logger = MetricsLogger(log_path=str(log_path))
        assert log_path.parent.exists()


class TestLogComponent:
    """Acceptance Criteria 4-5: log_component appends valid JSONL with all fields."""

    def test_log_component_appends_jsonl(self, tmp_path):
        """log_component() appends one valid JSONL line to logs/metrics.jsonl."""
        from search_research.metrics import MetricsLogger, ComponentName

        log_path = tmp_path / "logs" / "metrics.jsonl"
        logger = MetricsLogger(log_path=str(log_path), max_size_mb=10)

        logger.log_component(
            ComponentName.QMD_WIKI,
            latency_ms=50.0,
            tokens_used=0,
            quality=0.85,
            cache_hit=False,
        )

        logger.flush()
        time.sleep(0.1)  # Allow background writer to flush

        assert log_path.exists(), "metrics.jsonl was not created"
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"

        parsed = json.loads(lines[0])
        assert parsed["component"] == "QMD_WIKI"
        assert parsed["latency_ms"] == 50.0

    def test_log_component_contains_all_fields(self, tmp_path):
        """File written by log_component() contains all required fields."""
        from search_research.metrics import MetricsLogger, ComponentName

        log_path = tmp_path / "logs" / "metrics.jsonl"
        logger = MetricsLogger(log_path=str(log_path), max_size_mb=10)

        logger.log_component(
            ComponentName.QMD_WIKI,
            latency_ms=50.0,
            tokens_used=100,
            quality=0.85,
            cache_hit=False,
            branch="feature/test",
        )

        logger.flush()
        time.sleep(0.1)

        with open(log_path) as f:
            parsed = json.loads(f.readline())

        required_fields = ["timestamp", "component", "latency_ms", "tokens_used", "cache_hit", "output_quality", "branch"]
        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"


class TestFM1PipelineContinuesOnWriteError:
    """Failure Mode FM-1: MetricsLogger write raises OSError - pipeline continues."""

    def test_pipeline_continues_when_write_raises_oserror(self, tmp_path):
        """When write raises OSError, pipeline continues - no exception propagates.

        FM-1: MetricsLogger write raises OSError -> pipeline continues, no exception propagates.
        """
        from search_research.metrics import MetricsLogger, ComponentName

        log_path = tmp_path / "logs" / "metrics.jsonl"
        logger = MetricsLogger(log_path=str(log_path), max_size_mb=10)

        # Mock open to raise OSError on write
        original_open = open
        call_count = [0]

        def mock_open(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:  # Allow first open for init
                raise OSError("Simulated disk error")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            # This must NOT raise - pipeline continues even on OSError
            logger.log_component(
                ComponentName.QMD_WIKI,
                latency_ms=50.0,
                tokens_used=0,
                quality=0.85,
                cache_hit=False,
            )
            # If we get here without exception, pipeline continued successfully
            assert True, "log_component did not raise exception on OSError"


class TestFM5LogRotation:
    """Failure Mode FM-5: metrics.jsonl exceeds max_size_mb -> log rotation."""

    def test_log_rotation_when_file_exceeds_max_size(self, tmp_path):
        """When metrics.jsonl > max_size_mb, writer rotates to metrics.jsonl.YYYYMMDD_HHMMSS.

        FM-5: metrics.jsonl exceeds 10 MB -> log file rotated to metrics.jsonl.YYYYMMDD_HHMMSS.
        """
        from search_research.metrics import MetricsLogger, ComponentName

        log_path = tmp_path / "logs" / "metrics.jsonl"
        # Use very small max_size to trigger rotation easily
        logger = MetricsLogger(log_path=str(log_path), max_size_mb=0.001)  # ~1KB threshold

        # Write enough data to exceed max_size_mb
        for i in range(100):
            logger.log_component(
                ComponentName.QMD_WIKI,
                latency_ms=float(i),
                tokens_used=i,
                quality=0.5,
                cache_hit=False,
            )

        logger.flush()
        time.sleep(0.2)  # Allow background writer to process

        # Check that rotated file exists with timestamp pattern
        log_dir = log_path.parent
        rotated_files = list(log_dir.glob("metrics.jsonl.*"))
        assert len(rotated_files) > 0, "No rotated file found after exceeding max_size_mb"

        # Verify rotated file has timestamp format YYYYMMDD_HHMMSS
        rotated_name = rotated_files[0].name
        assert "metrics.jsonl." in rotated_name
        timestamp_part = rotated_name.replace("metrics.jsonl.", "")
        assert len(timestamp_part) == 15, f"Timestamp format incorrect: {timestamp_part}"
        assert timestamp_part.isdigit(), f"Timestamp should be all digits: {timestamp_part}"


class TestQueueFullSilentDrop:
    """Acceptance Criterion 6: Queue full -> log_component() drops metric silently."""

    def test_queue_full_drops_metric_silently(self, tmp_path):
        """When queue is full, log_component() drops metric silently - pipeline never blocks.

        FM-1 (variant): Queue full -> drop metric silently, pipeline never blocks.
        """
        from search_research.metrics import MetricsLogger, ComponentName

        log_path = tmp_path / "logs" / "metrics.jsonl"
        # Use a very small queue to trigger full condition
        logger = MetricsLogger(log_path=str(log_path), max_size_mb=10, queue_size=2)

        # Fill the queue quickly
        for i in range(10):
            # This should return immediately even if queue is full
            logger.log_component(
                ComponentName.QMD_WIKI,
                latency_ms=float(i),
                tokens_used=0,
                quality=0.5,
                cache_hit=False,
            )

        # If we get here without blocking, the test passes
        # (queue full drops silently, pipeline continues)
        assert True, "log_component did not block when queue was full"


class TestFlush:
    """Acceptance Criterion 7: flush() drains queue on shutdown."""

    def test_flush_drains_queue(self, tmp_path):
        """flush() drains the queue and writes all pending metrics."""
        from search_research.metrics import MetricsLogger, ComponentName

        log_path = tmp_path / "logs" / "metrics.jsonl"
        logger = MetricsLogger(log_path=str(log_path), max_size_mb=10)

        # Log several metrics
        for i in range(5):
            logger.log_component(
                ComponentName.QMD_WIKI,
                latency_ms=float(i),
                tokens_used=i * 10,
                quality=0.5,
                cache_hit=False,
            )

        # flush() should drain the queue
        logger.flush()
        time.sleep(0.2)

        with open(log_path) as f:
            lines = f.readlines()

        assert len(lines) == 5, f"Expected 5 lines after flush, got {len(lines)}"
