"""Test 3D compatibility tracking in performance monitoring.

Tests TASK-007: Add performance monitoring for cross-category metrics
"""
import os
import sqlite3

# Add modules directory to path
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class Test3DCompatibilityTracking:
    """Test 3D compatibility tracking functionality."""

    def test_track_3d_compatibility_usage(self):
        """Test that 3D compatibility usage is tracked correctly."""
        from performance_monitor import (
            track_3d_compatibility_usage,
        )

        # Use a temporary database for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = Path(tmpdir) / "test_performance.db"

            # Mock the database path
            with mock.patch("performance_monitor.PERF_DB_PATH", test_db_path):
                # Reset the connection to use the test database
                import performance_monitor
                if hasattr(performance_monitor._local, 'perf_conn'):
                    delattr(performance_monitor._local, 'perf_conn')

                # Initialize schema
                from performance_monitor import _init_perf_schema
                _init_perf_schema()

                # Track a 3D compatibility combination
                result = track_3d_compatibility_usage(
                    session_id="test_session",
                    terminal_id="test_terminal",
                    combination=("assumption_surfacing", "multi_agent", "architecture"),
                    enhancement="Assumption Surfacing + Multi-Agent + Architecture",
                    detection_latency_ms=2.5,
                )

                # Verify tracking succeeded
                assert result["logged"] is True
                assert result["combination"] == ("assumption_surfacing", "multi_agent", "architecture")
                assert result["enhancement"] == "Assumption Surfacing + Multi-Agent + Architecture"
                assert result["detection_latency_ms"] == 2.5

                # Verify data was written to database
                conn = sqlite3.connect(str(test_db_path))
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM compatibility_usage_log")
                count = cursor.fetchone()[0]
                assert count == 1

                cursor.execute("""
                    SELECT framework, mode, profile, enhancement, detection_latency_ms
                    FROM compatibility_usage_log
                """)
                row = cursor.fetchone()
                assert row[0] == "assumption_surfacing"
                assert row[1] == "multi_agent"
                assert row[2] == "architecture"
                assert row[3] == "Assumption Surfacing + Multi-Agent + Architecture"
                assert row[4] == 2.5

                conn.close()
                # Close the performance monitor connection to release file lock
                import performance_monitor
                if hasattr(performance_monitor._local, 'perf_conn'):
                    performance_monitor._local.perf_conn.close()
                    delattr(performance_monitor._local, 'perf_conn')

    def test_get_3d_compatibility_usage_summary(self):
        """Test that usage summary is calculated correctly."""
        from performance_monitor import (
            get_3d_compatibility_usage_summary,
            track_3d_compatibility_usage,
        )

        # Use a temporary database for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = Path(tmpdir) / "test_performance.db"

            # Mock the database path
            with mock.patch("performance_monitor.PERF_DB_PATH", test_db_path):
                # Reset the connection to use the test database
                import performance_monitor
                if hasattr(performance_monitor._local, 'perf_conn'):
                    delattr(performance_monitor._local, 'perf_conn')

                # Initialize schema
                from performance_monitor import _init_perf_schema
                _init_perf_schema()

                # Track multiple combinations
                combinations = [
                    ("assumption_surfacing", "multi_agent", "architecture", 2.5),
                    ("chestertons_fence", "sequential", "debug_rca", 1.8),
                    ("assumption_surfacing", "multi_agent", "architecture", 2.3),
                ]

                for framework, mode, profile, latency in combinations:
                    track_3d_compatibility_usage(
                        session_id="test_session",
                        terminal_id="test_terminal",
                        combination=(framework, mode, profile),
                        enhancement=f"{framework} + {mode} + {profile}",
                        detection_latency_ms=latency,
                    )

                # Get usage summary
                summary = get_3d_compatibility_usage_summary(days=7)

                # Verify summary
                assert summary["total_usage"] == 3
                assert len(summary["top_combinations"]) == 2  # 2 unique combinations

                # Most used combination should be assumption_surfacing + multi_agent + architecture
                top_combo = summary["top_combinations"][0]
                assert top_combo["framework"] == "assumption_surfacing"
                assert top_combo["mode"] == "multi_agent"
                assert top_combo["profile"] == "architecture"
                assert top_combo["usage_count"] == 2

                # Verify latency stats
                assert summary["latency_stats"]["avg_latency_ms"] > 0
                assert summary["latency_stats"]["min_latency_ms"] > 0
                assert summary["latency_stats"]["max_latency_ms"] > 0

                # Close the performance monitor connection to release file lock
                import performance_monitor
                if hasattr(performance_monitor._local, 'perf_conn'):
                    performance_monitor._local.perf_conn.close()
                    delattr(performance_monitor._local, 'perf_conn')

    def test_tracking_disabled_when_monitoring_disabled(self):
        """Test that tracking respects PERF_MONITOR_ENABLED flag."""
        from performance_monitor import track_3d_compatibility_usage

        # Disable monitoring
        os.environ["PERF_MONITOR_ENABLED"] = "false"

        result = track_3d_compatibility_usage(
            session_id="test_session",
            terminal_id="test_terminal",
            combination=("test", "test", "test"),
            enhancement="test enhancement",
            detection_latency_ms=1.0,
        )

        # Verify tracking was skipped
        assert result["logged"] is False
        assert "disabled" in result["reason"].lower()

        # Re-enable monitoring
        os.environ["PERF_MONITOR_ENABLED"] = "true"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
