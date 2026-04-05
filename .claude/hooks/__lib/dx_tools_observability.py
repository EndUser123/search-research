"""
DX Tools Observability Layer

Provides metrics tracking and health checks for Python DX Improvement Tools.
Implements graceful degradation - failures don't break hooks.

Metrics are persisted to JSONL logs for analysis and monitoring.
Health checks verify tool functionality and detect issues early.
"""

import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
if __name__ != "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class DXToolsMetrics:
    """Track and report metrics for DX tools operations.

    Metrics are stored in memory and periodically persisted to JSONL logs.
    Uses thread-safe operations for multi-terminal scenarios.

    Graceful degradation: If logging fails, operations continue silently.
    """

    def __init__(self, metrics_dir: Path | None = None):
        """Initialize metrics tracker.

        Args:
            metrics_dir: Directory for metrics logs. Defaults to logs/ in hooks directory.
        """
        if metrics_dir is None:
            hooks_dir = Path(__file__).resolve().parent.parent
            metrics_dir = hooks_dir / "logs"

        self.metrics_dir = Path(metrics_dir)
        self.metrics_file = self.metrics_dir / "dx_tools_metrics.jsonl"
        self._metrics: dict[str, dict[str, int]] = {}
        self._timers: dict[str, float] = {}
        self._lock = threading.RLock()
        self._verbose = os.environ.get("DX_TOOLS_METRICS_VERBOSE", "false").lower() == "true"

        # Ensure metrics directory exists
        try:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Graceful degradation - continue without metrics logging
            if self._verbose:
                print(f"Warning: Could not create metrics directory: {e}")

    def record_event(self, category: str, event: str, count: int = 1) -> None:
        """Record an event occurrence.

        Args:
            category: Metric category (e.g., "cache", "auth", "performance")
            event: Event name (e.g., "cleared", "blocked", "error")
            count: Number of occurrences (default: 1)
        """
        with self._lock:
            if category not in self._metrics:
                self._metrics[category] = {}
            self._metrics[category][event] = self._metrics[category].get(event, 0) + count

            # Persist immediately for important events
            if category in ("cache", "auth", "error"):
                self._persist()

    def start_timer(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Operation name to track
        """
        with self._lock:
            self._timers[operation] = time.perf_counter()

    def end_timer(self, operation: str) -> float | None:
        """End timing an operation and record duration.

        Args:
            operation: Operation name to track

        Returns:
            Duration in milliseconds, or None if timer wasn't started
        """
        with self._lock:
            if operation not in self._timers:
                return None

            duration_ms = (time.perf_counter() - self._timers[operation]) * 1000
            del self._timers[operation]

            # Record as performance metric
            if "performance" not in self._metrics:
                self._metrics["performance"] = {}
            self._metrics["performance"][f"{operation}_ms"] = (
                self._metrics["performance"].get(f"{operation}_ms", 0) + duration_ms
            )

            return duration_ms

    def get_metrics(self, category: str | None = None) -> dict[str, int]:
        """Get current metrics.

        Args:
            category: Filter by category, or None for all metrics

        Returns:
            Dictionary of metrics (category.event -> count)
        """
        with self._lock:
            if category:
                return self._metrics.get(category, {}).copy()
            return {cat: events.copy() for cat, events in self._metrics.items()}

    def _persist(self) -> bool:
        """Persist metrics to JSONL log file.

        Returns:
            True if persistence succeeded, False otherwise
        """
        try:
            with self._lock:
                # Create log entry with timestamp
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {cat: events.copy() for cat, events in self._metrics.items()},
                }

                # Append to JSONL file
                with open(self.metrics_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")

                return True
        except Exception as e:
            # Graceful degradation - don't break hooks on logging failures
            if self._verbose:
                print(f"Warning: Could not persist metrics: {e}")
            return False

    def flush(self) -> bool:
        """Force persist all metrics now.

        Returns:
            True if persistence succeeded, False otherwise
        """
        return self._persist()


class DXToolsHealth:
    """Health checks for DX tools components.

    Verifies that tools are functioning correctly and detects issues early.
    Provides comprehensive health status reporting.
    """

    @staticmethod
    def check_cache_manager() -> dict[str, Any]:
        """Check cache manager health.

        Returns:
            Health status dictionary with 'overall' key ('healthy' | 'unhealthy' | 'unknown')
        """
        health = {"component": "cache_manager", "overall": "unknown", "checks": {}}

        try:
            # Check if module exists
            from python_cache_manager import clear_package_cache, pre_install_cache_clean

            health["checks"]["module_exists"] = True

            # Check if logs directory is writable
            hooks_dir = Path(__file__).resolve().parent.parent
            logs_dir = hooks_dir / "logs"
            if logs_dir.exists():
                test_file = logs_dir / f".health_check_{os.getpid()}"
                try:
                    test_file.touch()
                    test_file.unlink()
                    health["checks"]["logs_writable"] = True
                except Exception:
                    health["checks"]["logs_writable"] = False
            else:
                health["checks"]["logs_writable"] = None  # N/A - doesn't exist yet

            health["overall"] = "healthy"
        except ImportError:
            health["checks"]["module_exists"] = False
            health["overall"] = "unhealthy"
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["overall"] = "unhealthy"

        return health

    @staticmethod
    def check_authorization_gate() -> dict[str, Any]:
        """Check authorization gate health.

        Returns:
            Health status dictionary with 'overall' key ('healthy' | 'unhealthy' | 'unknown')
        """
        health = {"component": "authorization_gate", "overall": "unknown", "checks": {}}

        try:
            # Check if module exists
            from PreToolUse_authorization_gate import is_project_safe_operation

            health["checks"]["module_exists"] = True

            health["overall"] = "healthy"
        except ImportError:
            health["checks"]["module_exists"] = False
            health["overall"] = "unhealthy"
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["overall"] = "unhealthy"

        return health

    @staticmethod
    def get_health_report() -> dict[str, Any]:
        """Get comprehensive health report for all DX tools.

        Returns:
            Health report with overall status and component details
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall": "unknown",
            "components": [],
        }

        # Check each component
        components = [DXToolsHealth.check_cache_manager(), DXToolsHealth.check_authorization_gate()]

        # Add components to report
        healthy_count = 0
        unhealthy_count = 0

        for component in components:
            report["components"].append(component)
            if component["overall"] == "healthy":
                healthy_count += 1
            elif component["overall"] == "unhealthy":
                unhealthy_count += 1

        # Determine overall status
        if unhealthy_count > 0:
            report["overall"] = "unhealthy"
        elif healthy_count == len(components):
            report["overall"] = "healthy"
        else:
            report["overall"] = "degraded"

        return report

    @staticmethod
    def write_health_report(output_path: Path | None = None) -> bool:
        """Write health report to JSON file.

        Args:
            output_path: Path for health report. Defaults to logs/dx_tools_health.json

        Returns:
            True if write succeeded, False otherwise
        """
        if output_path is None:
            hooks_dir = Path(__file__).resolve().parent.parent
            logs_dir = hooks_dir / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            output_path = logs_dir / "dx_tools_health.json"

        try:
            report = DXToolsHealth.get_health_report()
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            return True
        except Exception as e:
            # Graceful degradation
            verbose = os.environ.get("DX_TOOLS_METRICS_VERBOSE", "false").lower() == "true"
            if verbose:
                print(f"Warning: Could not write health report: {e}")
            return False


# Global singleton instance
_metrics_instance: DXToolsMetrics | None = None
_metrics_lock = threading.Lock()


def get_metrics() -> DXToolsMetrics:
    """Get global metrics singleton instance.

    Returns:
        DXToolsMetrics instance (thread-safe singleton)
    """
    global _metrics_instance

    with _metrics_lock:
        if _metrics_instance is None:
            _metrics_instance = DXToolsMetrics()
        return _metrics_instance


# CLI for manual health checks
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DX Tools Observability CLI")
    parser.add_argument("--health", action="store_true", help="Show health report")
    parser.add_argument("--metrics", action="store_true", help="Show current metrics")
    parser.add_argument("--write-health", action="store_true", help="Write health report to file")

    args = parser.parse_args()

    if args.health:
        report = DXToolsHealth.get_health_report()
        print(json.dumps(report, indent=2))

    if args.metrics:
        metrics = get_metrics()
        print(json.dumps(metrics.get_metrics(), indent=2))

    if args.write_health:
        success = DXToolsHealth.write_health_report()
        print(f"Health report written: {success}")
