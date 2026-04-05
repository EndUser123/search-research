#!/usr/bin/env python3
"""
Performance Monitoring Dashboard for TSK-006 Persistent Learning Agent Ecosystem
Step 12: Performance Analytics - Performance Dashboard Creation
"""

import json
import logging
import statistics
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agent_factory.agent_factory import AgentFactory
    from agent_factory.cks_integration import cks_stats, query_cks, store_to_cks
    from agent_factory.critic import create_critic
except ImportError as e:
    print(f"Import error: {e}")
    AgentFactory = None

@dataclass
class PerformanceMetric:
    """Single performance metric data point."""
    timestamp: float
    value: float
    unit: str
    component: str
    metric_type: str
    metadata: dict[str, Any] = None

@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    alert_id: str
    component: str
    metric_type: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq'
    severity: str  # 'INFO', 'WARNING', 'CRITICAL'
    message: str
    triggered: bool = False
    triggered_at: float | None = None

class PerformanceMonitor:
    """Real-time performance monitoring and alerting system."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.alerts = []
        self.running = False
        self.monitor_thread = None
        self.logger = logging.getLogger(__name__)

        # Performance thresholds based on benchmarks
        self.thresholds = {
            "agent_creation": {"warning": 100.0, "critical": 500.0},  # ms
            "session_management": {"warning": 300.0, "critical": 500.0},  # ms
            "cks_query": {"warning": 50.0, "critical": 200.0},  # ms
            "cks_store": {"warning": 500.0, "critical": 1000.0},  # ms
            "critic_evaluation": {"warning": 1000.0, "critical": 2000.0},  # ms
            "memory_usage": {"warning": 500.0, "critical": 1000.0},  # MB
            "error_rate": {"warning": 1.0, "critical": 5.0}  # %
        }

        # Initialize alerts
        self._initialize_alerts()

    def _initialize_alerts(self):
        """Initialize performance alerts based on thresholds."""
        alert_configs = [
            {
                "component": "agent_creation",
                "metric_type": "response_time",
                "threshold": self.thresholds["agent_creation"]["warning"],
                "operator": "gt",
                "severity": "WARNING",
                "message": "Agent creation time exceeding warning threshold"
            },
            {
                "component": "agent_creation",
                "metric_type": "response_time",
                "threshold": self.thresholds["agent_creation"]["critical"],
                "operator": "gt",
                "severity": "CRITICAL",
                "message": "Agent creation time exceeding critical threshold"
            },
            {
                "component": "cks_integration",
                "metric_type": "query_time",
                "threshold": self.thresholds["cks_query"]["warning"],
                "operator": "gt",
                "severity": "WARNING",
                "message": "CKS query time exceeding warning threshold"
            },
            {
                "component": "critic_system",
                "metric_type": "evaluation_time",
                "threshold": self.thresholds["critic_evaluation"]["warning"],
                "operator": "gt",
                "severity": "WARNING",
                "message": "Critic evaluation time exceeding warning threshold"
            },
            {
                "component": "system",
                "metric_type": "memory_usage",
                "threshold": self.thresholds["memory_usage"]["warning"],
                "operator": "gt",
                "severity": "WARNING",
                "message": "System memory usage exceeding warning threshold"
            }
        ]

        for i, config in enumerate(alert_configs):
            alert = PerformanceAlert(
                alert_id=f"alert_{i}",
                **config
            )
            self.alerts.append(alert)

    def add_metric(self, component: str, metric_type: str, value: float,
                   unit: str = "ms", metadata: dict[str, Any] = None):
        """Add a performance metric."""
        metric = PerformanceMetric(
            timestamp=time.time(),
            value=value,
            unit=unit,
            component=component,
            metric_type=metric_type,
            metadata=metadata or {}
        )

        key = f"{component}_{metric_type}"
        self.metrics[key].append(metric)

        # Check alerts
        self._check_alerts(component, metric_type, value)

    def _check_alerts(self, component: str, metric_type: str, value: float):
        """Check if any alerts should be triggered."""
        for alert in self.alerts:
            if alert.component == component and alert.metric_type == metric_type:
                triggered = False

                if alert.operator == "gt" and value > alert.threshold:
                    triggered = True
                elif alert.operator == "lt" and value < alert.threshold:
                    triggered = True
                elif alert.operator == "eq" and abs(value - alert.threshold) < 0.001:
                    triggered = True

                if triggered and not alert.triggered:
                    alert.triggered = True
                    alert.triggered_at = time.time()
                    self.logger.warning(f"ALERT TRIGGERED: {alert.message} (value: {value})")
                elif not triggered and alert.triggered:
                    alert.triggered = False
                    alert.triggered_at = None
                    self.logger.info(f"ALERT CLEARED: {alert.message}")

    def start_monitoring(self, interval: float = 5.0):
        """Start continuous performance monitoring."""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"Performance monitoring started with {interval}s interval")

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Test agent creation performance
                self._test_agent_creation()

                # Test CKS performance
                self._test_cks_performance()

                # Test critic performance
                self._test_critic_performance()

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

            time.sleep(5.0)

    def _collect_system_metrics(self):
        """Collect system resource metrics."""
        process = psutil.Process()

        # Memory usage
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.add_metric("system", "memory_usage", memory_mb, "MB")

        # CPU usage
        cpu_percent = process.cpu_percent()
        self.add_metric("system", "cpu_usage", cpu_percent, "%")

        # System memory
        system_memory = psutil.virtual_memory()
        self.add_metric("system", "system_memory_usage", system_memory.percent, "%")

    def _test_agent_creation(self):
        """Test agent creation performance."""
        if not AgentFactory:
            return

        try:
            start_time = time.perf_counter()
            factory = AgentFactory()
            session_id = factory.create_agent(
                'development_agent',
                context={'monitoring_test': True}
            )
            end_time = time.perf_counter()

            creation_time_ms = (end_time - start_time) * 1000
            self.add_metric("agent_creation", "response_time", creation_time_ms, "ms")

            # Test session retrieval
            if session_id:
                start_time = time.perf_counter()
                session = factory.get_agent(session_id)
                end_time = time.perf_counter()

                retrieval_time_ms = (end_time - start_time) * 1000
                self.add_metric("session_management", "response_time", retrieval_time_ms, "ms")

        except Exception as e:
            self.logger.error(f"Error testing agent creation: {e}")
            self.add_metric("agent_creation", "error_count", 1, "count")

    def _test_cks_performance(self):
        """Test CKS performance."""
        try:
            # Test query performance
            start_time = time.perf_counter()
            results = query_cks("monitoring test query", top_n=3, threshold=0.5)
            end_time = time.perf_counter()

            query_time_ms = (end_time - start_time) * 1000
            self.add_metric("cks_integration", "query_time", query_time_ms, "ms")
            self.add_metric("cks_integration", "query_results", len(results), "count")

            # Test store performance
            start_time = time.perf_counter()
            success = store_to_cks(
                "monitoring test question",
                "monitoring test answer",
                metadata={"monitoring": True, "timestamp": datetime.now().isoformat()}
            )
            end_time = time.perf_counter()

            if success:
                store_time_ms = (end_time - start_time) * 1000
                self.add_metric("cks_integration", "store_time", store_time_ms, "ms")

        except Exception as e:
            self.logger.error(f"Error testing CKS performance: {e}")
            self.add_metric("cks_integration", "error_count", 1, "count")

    def _test_critic_performance(self):
        """Test critic system performance."""
        try:
            critic = create_critic()

            sample_code = '''
def monitoring_test_function():
    """Test function for performance monitoring."""
    x = 1 + 1
    return x

class MonitoringTestClass:
    pass
'''

            start_time = time.perf_counter()
            result = critic.evaluate_code(sample_code, "monitoring_test.py")
            end_time = time.perf_counter()

            evaluation_time_ms = (end_time - start_time) * 1000
            self.add_metric("critic_system", "evaluation_time", evaluation_time_ms, "ms")
            self.add_metric("critic_system", "quality_score", result.quality_score.overall, "score")
            self.add_metric("critic_system", "issues_found", len(result.issues), "count")

        except Exception as e:
            self.logger.error(f"Error testing critic performance: {e}")
            self.add_metric("critic_system", "error_count", 1, "count")

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current performance metrics summary."""
        summary = {}

        for key, metric_deque in self.metrics.items():
            if not metric_deque:
                continue

            recent_metrics = list(metric_deque)[-10:]  # Last 10 metrics
            values = [m.value for m in recent_metrics]

            component, metric_type = key.split("_", 1)

            summary[key] = {
                "component": component,
                "metric_type": metric_type,
                "current": values[-1] if values else 0,
                "average": statistics.mean(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "count": len(values),
                "unit": recent_metrics[-1].unit if recent_metrics else "unknown"
            }

        return summary

    def get_alert_status(self) -> dict[str, Any]:
        """Get current alert status."""
        active_alerts = [alert for alert in self.alerts if alert.triggered]

        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "alerts": [asdict(alert) for alert in active_alerts]
        }

    def get_performance_dashboard(self) -> dict[str, Any]:
        """Generate comprehensive performance dashboard data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": self._calculate_system_health(),
            "metrics": self.get_current_metrics(),
            "alerts": self.get_alert_status(),
            "thresholds": self.thresholds,
            "monitoring_status": {
                "running": self.running,
                "metrics_collected": sum(len(deque) for deque in self.metrics.values())
            }
        }

    def _calculate_system_health(self) -> dict[str, Any]:
        """Calculate overall system health score."""
        health_score = 100
        issues = []

        # Check active alerts
        active_alerts = [alert for alert in self.alerts if alert.triggered]

        for alert in active_alerts:
            if alert.severity == "CRITICAL":
                health_score -= 25
                issues.append(f"CRITICAL: {alert.message}")
            elif alert.severity == "WARNING":
                health_score -= 10
                issues.append(f"WARNING: {alert.message}")

        # Check recent performance trends
        for key, metric_deque in self.metrics.items():
            if len(metric_deque) >= 5:
                recent_metrics = list(metric_deque)[-5:]
                values = [m.value for m in recent_metrics]

                # Check for performance degradation
                if len(values) >= 2:
                    trend = values[-1] - values[0]
                    if trend > values[0] * 0.5:  # 50% degradation
                        health_score -= 5
                        issues.append(f"Performance degradation in {key}")

        health_score = max(0, health_score)

        if health_score >= 90:
            status = "EXCELLENT"
        elif health_score >= 75:
            status = "GOOD"
        elif health_score >= 60:
            status = "FAIR"
        elif health_score >= 40:
            status = "POOR"
        else:
            status = "CRITICAL"

        return {
            "score": health_score,
            "status": status,
            "issues": issues
        }

    def save_metrics(self, output_path: str = None) -> str:
        """Save current metrics to file."""
        if not output_path:
            output_path = Path(__file__).parent / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        dashboard_data = self.get_performance_dashboard()

        with open(output_path, 'w') as f:
            json.dump(dashboard_data, f, indent=2)

        return str(output_path)


def main():
    """Main execution function for performance monitor."""
    print("=== TSK-006 Performance Monitor ===")

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create performance monitor
    monitor = PerformanceMonitor()

    try:
        print("Starting performance monitoring...")
        monitor.start_monitoring(interval=5.0)

        # Run for 30 seconds
        print("Monitoring for 30 seconds...")
        time.sleep(30)

        # Generate dashboard
        print("Generating performance dashboard...")
        dashboard = monitor.get_performance_dashboard()

        # Print summary
        print("\n=== Performance Dashboard ===")
        print(f"System Health: {dashboard['system_health']['score']}/100 ({dashboard['system_health']['status']})")
        print(f"Active Alerts: {dashboard['alerts']['active_alerts']}")
        print(f"Metrics Collected: {dashboard['monitoring_status']['metrics_collected']}")

        if dashboard['system_health']['issues']:
            print("\nIssues:")
            for issue in dashboard['system_health']['issues']:
                print(f"  - {issue}")

        print("\nCurrent Metrics:")
        for key, metric in dashboard['metrics'].items():
            print(f"  {key}: {metric['current']:.2f} {metric['unit']} (avg: {metric['average']:.2f})")

        # Save results
        output_file = monitor.save_metrics()
        print(f"\nDashboard saved to: {output_file}")

    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    finally:
        monitor.stop_monitoring()
        print("Performance monitoring stopped")


if __name__ == "__main__":
    main()
