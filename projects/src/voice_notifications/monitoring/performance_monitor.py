"""
Performance Monitoring System for Voice Notifications
Ensures <500ms delivery targets and provides comprehensive metrics
"""

import asyncio
import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil

from ..config.config_manager import VoiceNotificationSystemConfig

logger = logging.getLogger(__name__)

@dataclass
class PerformanceThresholds:
    """Performance monitoring thresholds"""
    target_delivery_ms: float = 500.0
    warning_delivery_ms: float = 750.0
    critical_delivery_ms: float = 1000.0
    max_memory_usage_mb: float = 100.0
    max_cpu_usage_percent: float = 50.0
    max_queue_size: int = 10
    max_concurrent_deliveries: int = 5

@dataclass
class DeliveryPerformanceSnapshot:
    """Snapshot of delivery performance data"""
    timestamp: datetime
    delivery_time_ms: float
    notification_type: str
    engine_used: str
    session_id: str
    priority: str
    was_filtered: bool
    filter_reason: str | None = None
    queue_wait_time_ms: float | None = None
    processing_time_ms: float | None = None

@dataclass
class SystemResourceSnapshot:
    """Snapshot of system resource usage"""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    active_threads: int
    open_files: int

@dataclass
class PerformanceAlert:
    """Performance alert information"""
    timestamp: datetime
    severity: str  # info, warning, critical
    category: str  # delivery, resources, queue, system
    message: str
    metrics: dict[str, Any] = field(default_factory=dict)
    threshold_value: float | None = None
    actual_value: float | None = None

class VoiceNotificationPerformanceMonitor:
    """
    Comprehensive performance monitoring system for voice notifications
    Tracks delivery times, resource usage, and generates alerts
    """

    def __init__(self, config: VoiceNotificationSystemConfig):
        self.config = config
        self.enabled = config.performance.enable_metrics

        # Performance thresholds
        self.thresholds = PerformanceThresholds(
            target_delivery_ms=config.performance.target_delivery_ms,
            warning_delivery_ms=config.performance.slow_delivery_threshold_ms,
            max_concurrent_deliveries=config.performance.max_concurrent_notifications
        )

        # Data storage
        self.delivery_snapshots: deque = deque(maxlen=10000)
        self.resource_snapshots: deque = deque(maxlen=1000)
        self.alerts: deque = deque(maxlen=1000)
        self.hourly_stats: dict[str, Any] = {}
        self.daily_stats: dict[str, Any] = {}

        # Real-time metrics
        self.current_metrics = {
            "deliveries_last_minute": 0,
            "avg_delivery_time_ms": 0.0,
            "success_rate_percent": 100.0,
            "filter_rate_percent": 0.0,
            "queue_size": 0,
            "active_deliveries": 0,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "alerts_count": 0
        }

        # Tracking variables
        self.minute_delivery_counts: deque = deque(maxlen=60)
        self.last_cleanup_time = time.time()
        self.last_stats_reset = datetime.now()

        # Thread safety
        self._lock = threading.RLock()

        # Callbacks for alerts
        self.alert_callbacks: list[Callable] = []

        # Monitoring task
        self.monitoring_task: asyncio.Task | None = None
        self.running = False

        # Performance log file
        self.performance_log_file = None
        if config.performance.performance_log_file:
            self.performance_log_file = Path(config.performance.performance_log_file)
            self.performance_log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Voice notification performance monitor initialized")

    async def start(self) -> None:
        """Start the performance monitoring system"""
        if not self.enabled:
            logger.info("Performance monitoring disabled")
            return

        if self.running:
            logger.warning("Performance monitor already running")
            return

        self.running = True

        # Start background monitoring task
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(),
            name="PerformanceMonitor"
        )

        logger.info("Performance monitoring started")

    async def stop(self) -> None:
        """Stop the performance monitoring system"""
        if not self.running:
            return

        self.running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # Save final statistics
        await self._save_performance_data()

        logger.info("Performance monitoring stopped")

    def record_delivery(self, snapshot: DeliveryPerformanceSnapshot) -> None:
        """Record a delivery performance snapshot"""
        if not self.enabled:
            return

        with self._lock:
            self.delivery_snapshots.append(snapshot)

            # Update real-time metrics
            self._update_delivery_metrics(snapshot)

            # Check performance thresholds
            self._check_delivery_thresholds(snapshot)

            # Log to file if configured
            if self.performance_log_file:
                self._log_delivery_to_file(snapshot)

    def record_system_resources(self) -> None:
        """Record current system resource usage"""
        if not self.enabled:
            return

        try:
            process = psutil.Process()
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            snapshot = SystemResourceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=process.memory_percent(),
                active_threads=threading.active_count(),
                open_files=len(process.open_files())
            )

            with self._lock:
                self.resource_snapshots.append(snapshot)
                self.current_metrics.update({
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb
                })

            # Check resource thresholds
            self._check_resource_thresholds(snapshot)

        except Exception as e:
            logger.error(f"Error recording system resources: {e}")

    def record_queue_metrics(self, queue_size: int, active_deliveries: int) -> None:
        """Record queue-related metrics"""
        if not self.enabled:
            return

        with self._lock:
            self.current_metrics.update({
                "queue_size": queue_size,
                "active_deliveries": active_deliveries
            })

        # Check queue thresholds
        if queue_size > self.thresholds.max_queue_size:
            self._create_alert(
                severity="warning",
                category="queue",
                message=f"Queue size exceeding threshold: {queue_size} > {self.thresholds.max_queue_size}",
                metrics={"queue_size": queue_size},
                threshold_value=self.thresholds.max_queue_size,
                actual_value=queue_size
            )

        if active_deliveries > self.thresholds.max_concurrent_deliveries:
            self._create_alert(
                severity="warning",
                category="queue",
                message=f"Concurrent deliveries exceeding threshold: {active_deliveries} > {self.thresholds.max_concurrent_deliveries}",
                metrics={"active_deliveries": active_deliveries},
                threshold_value=self.thresholds.max_concurrent_deliveries,
                actual_value=active_deliveries
            )

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Add a callback function to receive performance alerts"""
        self.alert_callbacks.append(callback)

    def get_performance_summary(self, minutes: int = 5) -> dict[str, Any]:
        """Get performance summary for the last N minutes"""
        if not self.enabled:
            return {"status": "disabled"}

        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            # Filter recent deliveries
            recent_deliveries = [
                s for s in self.delivery_snapshots
                if s.timestamp >= cutoff_time
            ]

            # Calculate statistics
            if recent_deliveries:
                delivery_times = [s.delivery_time_ms for s in recent_deliveries if s.delivery_time_ms]
                successful_deliveries = [s for s in recent_deliveries if not s.was_filtered]
                filtered_deliveries = [s for s in recent_deliveries if s.was_filtered]

                summary = {
                    "period_minutes": minutes,
                    "total_deliveries": len(recent_deliveries),
                    "successful_deliveries": len(successful_deliveries),
                    "filtered_deliveries": len(filtered_deliveries),
                    "success_rate_percent": (len(successful_deliveries) / len(recent_deliveries)) * 100 if recent_deliveries else 0,
                    "filter_rate_percent": (len(filtered_deliveries) / len(recent_deliveries)) * 100 if recent_deliveries else 0,
                    "delivery_time_stats": {
                        "avg_ms": statistics.mean(delivery_times) if delivery_times else 0,
                        "median_ms": statistics.median(delivery_times) if delivery_times else 0,
                        "min_ms": min(delivery_times) if delivery_times else 0,
                        "max_ms": max(delivery_times) if delivery_times else 0,
                        "p95_ms": statistics.quantiles(delivery_times, n=20)[18] if len(delivery_times) >= 20 else max(delivery_times) if delivery_times else 0
                    },
                    "target_compliance_percent": (
                        len([t for t in delivery_times if t <= self.thresholds.target_delivery_ms]) /
                        len(delivery_times) * 100
                    ) if delivery_times else 100,
                    "alerts_count": len([a for a in self.alerts if a.timestamp >= cutoff_time]),
                    "current_metrics": self.current_metrics.copy()
                }
            else:
                summary = {
                    "period_minutes": minutes,
                    "total_deliveries": 0,
                    "message": "No deliveries in this period",
                    "current_metrics": self.current_metrics.copy()
                }

        return summary

    def get_recent_alerts(self, minutes: int = 60, severity: str | None = None) -> list[PerformanceAlert]:
        """Get recent performance alerts"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]

            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("Performance monitoring loop started")

        while self.running:
            try:
                # Record system resources
                self.record_system_resources()

                # Update real-time metrics
                self._update_real_time_metrics()

                # Cleanup old data
                if time.time() - self.last_cleanup_time > 300:  # Every 5 minutes
                    self._cleanup_old_data()
                    self.last_cleanup_time = time.time()

                # Save performance data periodically
                if datetime.now().minute == 0:  # Every hour
                    await self._save_performance_data()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def _update_delivery_metrics(self, snapshot: DeliveryPerformanceSnapshot) -> None:
        """Update delivery-related metrics"""
        now = datetime.now()
        current_minute = now.replace(second=0, microsecond=0)

        # Count deliveries in last minute
        recent_deliveries = [
            s for s in self.delivery_snapshots
            if s.timestamp >= now - timedelta(minutes=1)
        ]
        self.current_metrics["deliveries_last_minute"] = len(recent_deliveries)

        # Update average delivery time (last 10 deliveries)
        recent_times = [
            s.delivery_time_ms for s in list(self.delivery_snapshots)[-10:]
            if s.delivery_time_ms and not s.was_filtered
        ]
        if recent_times:
            self.current_metrics["avg_delivery_time_ms"] = statistics.mean(recent_times)

        # Update success and filter rates (last 50 deliveries)
        recent_snapshots = list(self.delivery_snapshots)[-50:]
        if recent_snapshots:
            successful = len([s for s in recent_snapshots if not s.was_filtered])
            filtered = len([s for s in recent_snapshots if s.was_filtered])
            total = len(recent_snapshots)

            self.current_metrics["success_rate_percent"] = (successful / total) * 100
            self.current_metrics["filter_rate_percent"] = (filtered / total) * 100

    def _update_real_time_metrics(self) -> None:
        """Update real-time performance metrics"""
        now = datetime.now()

        # Update alerts count (last hour)
        recent_alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= now - timedelta(hours=1)
        ]
        self.current_metrics["alerts_count"] = len(recent_alerts)

    def _check_delivery_thresholds(self, snapshot: DeliveryPerformanceSnapshot) -> None:
        """Check delivery performance against thresholds"""
        if snapshot.was_filtered or not snapshot.delivery_time_ms:
            return

        delivery_time = snapshot.delivery_time_ms

        if delivery_time > self.thresholds.critical_delivery_ms:
            severity = "critical"
        elif delivery_time > self.thresholds.warning_delivery_ms:
            severity = "warning"
        elif delivery_time > self.thresholds.target_delivery_ms:
            severity = "info"
        else:
            return  # Within target, no alert

        self._create_alert(
            severity=severity,
            category="delivery",
            message=f"Slow delivery time: {delivery_time:.1f}ms ({snapshot.notification_type})",
            metrics={
                "delivery_time_ms": delivery_time,
                "notification_type": snapshot.notification_type,
                "engine_used": snapshot.engine_used,
                "session_id": snapshot.session_id
            },
            threshold_value=self.thresholds.target_delivery_ms,
            actual_value=delivery_time
        )

    def _check_resource_thresholds(self, snapshot: SystemResourceSnapshot) -> None:
        """Check system resource usage against thresholds"""
        # Check memory usage
        if snapshot.memory_mb > self.thresholds.max_memory_usage_mb:
            self._create_alert(
                severity="warning",
                category="resources",
                message=f"High memory usage: {snapshot.memory_mb:.1f}MB",
                metrics={"memory_mb": snapshot.memory_mb},
                threshold_value=self.thresholds.max_memory_usage_mb,
                actual_value=snapshot.memory_mb
            )

        # Check CPU usage
        if snapshot.cpu_percent > self.thresholds.max_cpu_usage_percent:
            self._create_alert(
                severity="warning",
                category="resources",
                message=f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                metrics={"cpu_percent": snapshot.cpu_percent},
                threshold_value=self.thresholds.max_cpu_usage_percent,
                actual_value=snapshot.cpu_percent
            )

    def _create_alert(
        self,
        severity: str,
        category: str,
        message: str,
        metrics: dict[str, Any],
        threshold_value: float | None = None,
        actual_value: float | None = None
    ) -> None:
        """Create and record a performance alert"""
        alert = PerformanceAlert(
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=message,
            metrics=metrics,
            threshold_value=threshold_value,
            actual_value=actual_value
        )

        with self._lock:
            self.alerts.append(alert)

        # Log the alert
        log_level = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "critical": logging.ERROR
        }.get(severity, logging.INFO)

        logger.log(log_level, f"Performance Alert [{severity.upper()}] {message}")

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def _log_delivery_to_file(self, snapshot: DeliveryPerformanceSnapshot) -> None:
        """Log delivery performance to file"""
        try:
            log_entry = {
                "timestamp": snapshot.timestamp.isoformat(),
                "delivery_time_ms": snapshot.delivery_time_ms,
                "notification_type": snapshot.notification_type,
                "engine_used": snapshot.engine_used,
                "session_id": snapshot.session_id,
                "priority": snapshot.priority,
                "was_filtered": snapshot.was_filtered,
                "filter_reason": snapshot.filter_reason
            }

            with open(self.performance_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            logger.error(f"Error logging delivery to file: {e}")

    def _cleanup_old_data(self) -> None:
        """Clean up old performance data"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        with self._lock:
            # Clean up old alerts
            self.alerts = deque(
                [alert for alert in self.alerts if alert.timestamp >= cutoff_time],
                maxlen=1000
            )

            # Clean up old resource snapshots
            self.resource_snapshots = deque(
                [snapshot for snapshot in self.resource_snapshots if snapshot.timestamp >= cutoff_time],
                maxlen=1000
            )

    async def _save_performance_data(self) -> None:
        """Save aggregated performance data"""
        try:
            # Calculate hourly statistics
            now = datetime.now()
            hour_start = now.replace(minute=0, second=0, microsecond=0)

            with self._lock:
                hour_deliveries = [
                    s for s in self.delivery_snapshots
                    if s.timestamp >= hour_start
                ]

                if hour_deliveries:
                    delivery_times = [
                        s.delivery_time_ms for s in hour_deliveries
                        if s.delivery_time_ms and not s.was_filtered
                    ]

                    hour_stats = {
                        "hour": hour_start.isoformat(),
                        "total_deliveries": len(hour_deliveries),
                        "successful_deliveries": len([s for s in hour_deliveries if not s.was_filtered]),
                        "filtered_deliveries": len([s for s in hour_deliveries if s.was_filtered]),
                        "avg_delivery_time_ms": statistics.mean(delivery_times) if delivery_times else 0,
                        "target_compliance_percent": (
                            len([t for t in delivery_times if t <= self.thresholds.target_delivery_ms]) /
                            len(delivery_times) * 100
                        ) if delivery_times else 100,
                        "alerts_count": len([a for a in self.alerts if a.timestamp >= hour_start])
                    }

                    self.hourly_stats[hour_start.isoformat()] = hour_stats

            # Optionally save to disk
            if self.performance_log_file:
                stats_file = self.performance_log_file.with_suffix('.stats.json')
                with open(stats_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "hourly_stats": self.hourly_stats,
                        "current_metrics": self.current_metrics
                    }, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving performance data: {e}")

    def get_detailed_report(self) -> dict[str, Any]:
        """Generate detailed performance report"""
        if not self.enabled:
            return {"status": "disabled"}

        with self._lock:
            # Delivery performance analysis
            if self.delivery_snapshots:
                all_deliveries = list(self.delivery_snapshots)
                delivery_times = [
                    s.delivery_time_ms for s in all_deliveries
                    if s.delivery_time_ms and not s.was_filtered
                ]

                # Performance by notification type
                type_stats = defaultdict(list)
                for snapshot in all_deliveries:
                    if not snapshot.was_filtered and snapshot.delivery_time_ms:
                        type_stats[snapshot.notification_type].append(snapshot.delivery_time_ms)

                performance_by_type = {}
                for notif_type, times in type_stats.items():
                    performance_by_type[notif_type] = {
                        "count": len(times),
                        "avg_ms": statistics.mean(times),
                        "median_ms": statistics.median(times),
                        "min_ms": min(times),
                        "max_ms": max(times),
                        "target_compliance_percent": (
                            len([t for t in times if t <= self.thresholds.target_delivery_ms]) /
                            len(times) * 100
                        )
                    }

                # Performance by engine
                engine_stats = defaultdict(list)
                for snapshot in all_deliveries:
                    if not snapshot.was_filtered and snapshot.delivery_time_ms:
                        engine_stats[snapshot.engine_used].append(snapshot.delivery_time_ms)

                performance_by_engine = {}
                for engine, times in engine_stats.items():
                    performance_by_engine[engine] = {
                        "count": len(times),
                        "avg_ms": statistics.mean(times),
                        "median_ms": statistics.median(times)
                    }

                delivery_analysis = {
                    "total_snapshots": len(all_deliveries),
                    "successful_deliveries": len([s for s in all_deliveries if not s.was_filtered]),
                    "filtered_deliveries": len([s for s in all_deliveries if s.was_filtered]),
                    "overall_delivery_time_stats": {
                        "avg_ms": statistics.mean(delivery_times) if delivery_times else 0,
                        "median_ms": statistics.median(delivery_times) if delivery_times else 0,
                        "min_ms": min(delivery_times) if delivery_times else 0,
                        "max_ms": max(delivery_times) if delivery_times else 0,
                        "p95_ms": statistics.quantiles(delivery_times, n=20)[18] if len(delivery_times) >= 20 else max(delivery_times) if delivery_times else 0
                    },
                    "target_compliance_percent": (
                        len([t for t in delivery_times if t <= self.thresholds.target_delivery_ms]) /
                        len(delivery_times) * 100
                    ) if delivery_times else 100,
                    "performance_by_type": performance_by_type,
                    "performance_by_engine": performance_by_engine
                }
            else:
                delivery_analysis = {"message": "No delivery data available"}

            # Resource usage analysis
            if self.resource_snapshots:
                resources = list(self.resource_snapshots)
                cpu_values = [r.cpu_percent for r in resources]
                memory_values = [r.memory_mb for r in resources]

                resource_analysis = {
                    "total_snapshots": len(resources),
                    "cpu_usage": {
                        "avg_percent": statistics.mean(cpu_values),
                        "max_percent": max(cpu_values),
                        "min_percent": min(cpu_values)
                    },
                    "memory_usage": {
                        "avg_mb": statistics.mean(memory_values),
                        "max_mb": max(memory_values),
                        "min_mb": min(memory_values)
                    },
                    "current_cpu": cpu_values[-1] if cpu_values else 0,
                    "current_memory_mb": memory_values[-1] if memory_values else 0
                }
            else:
                resource_analysis = {"message": "No resource data available"}

            # Alert analysis
            recent_alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= datetime.now() - timedelta(hours=24)
            ]

            alert_analysis = {
                "total_alerts_24h": len(recent_alerts),
                "by_severity": {
                    severity: len([a for a in recent_alerts if a.severity == severity])
                    for severity in ["info", "warning", "critical"]
                },
                "by_category": {
                    category: len([a for a in recent_alerts if a.category == category])
                    for category in ["delivery", "resources", "queue", "system"]
                }
            }

            return {
                "monitoring_status": "active",
                "thresholds": asdict(self.thresholds),
                "current_metrics": self.current_metrics.copy(),
                "delivery_analysis": delivery_analysis,
                "resource_analysis": resource_analysis,
                "alert_analysis": alert_analysis,
                "data_retention": {
                    "delivery_snapshots": len(self.delivery_snapshots),
                    "resource_snapshots": len(self.resource_snapshots),
                    "alerts": len(self.alerts)
                }
            }
