import asyncio
import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from dataclasses_json import dataclass_json

#!/usr/bin/env python3
"""
CKS Monitoring and Analytics System for CWO12 Enhanced Integration

This module implements comprehensive monitoring and analytics for CKS integration,
providing real-time dashboard updates, historical trend tracking, and intelligent
insights generation for system optimization and compliance monitoring.

Key Features:
- Real-time dashboard with live metrics and alerts
- Historical trend tracking with time-series data
- User experience metrics and compliance score tracking
- Performance analytics with predictive insights
- Alert generation and notification system
- Custom report generation and data visualization
- Integration monitoring for all CKS components

Algorithm Approach: Multi-dimensional analytics combining real-time stream processing,
historical data analysis, predictive modeling, and intelligent alerting for comprehensive
system monitoring and optimization guidance.

Time Complexity: O(n) for data processing where n is number of metrics
Space Complexity: O(n) for time-series storage with intelligent compression

Monitoring Targets:
- Real-time dashboard updates (<1s latency)
- Historical trend tracking (indefinite retention with compression)
- User experience metrics (satisfaction, completion rates)
- Compliance score tracking (continuous monitoring)
- Predictive analytics (trend forecasting)
- Alert response time (<5s for critical alerts)
"""


# Analytics and monitoring imports


# CKS integration imports
try:
    from ..constitutional_compliance.cwo12_cks_compliance_validator import (
        CWO12CKSConstitutionalValidator,
    )
    from ..knowledge_system.cks_constitutional_validator import (
        CKSConstitutionalValidator,
    )
    from ..orchestration.cks_agent_coordinator import CKSAgentCoordinator
    from ..performance.cks_performance_optimizer import CKSPreformanceOptimizer
    from ..resilience.cks_fallback_error_handler import CKSFallbackErrorHandler
except ImportError:
    # Fallback for standalone execution
    pass


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric type enumeration for classification and analysis."""

    COUNTER = "counter"  # Incremental count
    GAUGE = "gauge"  # Current value
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements
    RATIO = "ratio"  # Percentage or ratio
    RATE = "rate"  # Events per time unit


class AlertSeverity(Enum):
    """Alert severity levels for prioritization."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TimeGranularity(Enum):
    """Time granularity for analytics and reporting."""

    REAL_TIME = "real_time"  # Sub-second updates
    MINUTE = "minute"  # 1-minute aggregation
    HOUR = "hour"  # 1-hour aggregation
    DAY = "day"  # 1-day aggregation
    WEEK = "week"  # 1-week aggregation
    MONTH = "month"  # 1-month aggregation


@dataclass_json
@dataclass
class MetricPoint:
    """Individual metric data point with full context."""

    metric_name: str
    metric_type: MetricType
    value: int | float | dict[str, Any]
    timestamp: datetime
    component: str
    operation: str
    user_id: str | None = None
    session_id: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricPoint":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["metric_type"] = MetricType(data["metric_type"])
        return cls(**data)


@dataclass_json
@dataclass
class Alert:
    """Alert definition with comprehensive context."""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    component: str
    metric_name: str
    threshold_value: float
    current_value: float
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    acknowledged_by: str | None = None
    resolved_by: str | None = None
    resolution_time: datetime | None = None
    impact_assessment: str = ""
    recommended_actions: list[str] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass_json
@dataclass
class UserExperienceMetrics:
    """Comprehensive user experience metrics."""

    session_id: str
    user_id: str | None
    start_time: datetime
    end_time: datetime | None
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    avg_response_time_ms: float = 0.0
    satisfaction_score: float | None = None  # 1-5 scale
    completion_rate: float = 0.0
    error_rate: float = 0.0
    bounce_rate: bool = False
    feature_usage: dict[str, int] = field(default_factory=dict)
    compliance_violations: int = 0
    constitutional_score: float = 1.0


@dataclass_json
@dataclass
class ComplianceTrend:
    """Compliance trend data with historical context."""

    timestamp: datetime
    component: str
    compliance_score: float
    violations_count: int
    constitutional_sections: list[str]
    cks_integration_score: float
    workflow_step: str | None = None
    remediation_actions: list[str] = field(default_factory=list)


@dataclass_json
@dataclass
class PerformanceInsight:
    """Performance insight with predictive recommendations."""

    insight_id: str
    category: str  # "performance", "reliability", "efficiency", "scalability"
    severity: AlertSeverity
    title: str
    description: str
    current_metrics: dict[str, float]
    predicted_impact: str
    recommended_actions: list[str]
    estimated_improvement: dict[str, float]
    confidence_score: float
    timestamp: datetime
    applies_to: list[str]  # Components or operations


class MetricsCollector:
    """High-performance metrics collection and aggregation system."""

    def __init__(self, max_memory_points: int = 10000) -> None:
        """Initialize metrics collector."""
        self.max_memory_points = max_memory_points
        self.metrics_buffer: deque = deque(maxlen=max_memory_points)
        self.aggregated_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "values": deque(maxlen=1000),
            },
        )

        self.collection_stats = {
            "total_collected": 0,
            "collection_rate_per_second": 0.0,
            "last_collection_time": None,
        }

        self._lock = threading.RLock()

    def collect_metric(self, metric_point: MetricPoint) -> None:
        """Collect metric point with aggregation."""
        with self._lock:
            self.metrics_buffer.append(metric_point)
            self._update_aggregations(metric_point)

            # Update collection stats
            self.collection_stats["total_collected"] += 1
            current_time = time.time()
            if self.collection_stats["last_collection_time"]:
                time_diff = current_time - self.collection_stats["last_collection_time"]
                if time_diff > 0:
                    self.collection_stats["collection_rate_per_second"] = (
                        self.collection_stats["collection_rate_per_second"] * 0.9
                        + 1.0 / time_diff * 0.1
                    )
            self.collection_stats["last_collection_time"] = current_time

    def _update_aggregations(self, metric_point: MetricPoint) -> None:
        """Update aggregated metrics for real-time analysis."""
        key = f"{metric_point.component}.{metric_point.metric_name}"

        if isinstance(metric_point.value, (int, float)):
            agg = self.aggregated_metrics[key]
            agg["count"] += 1
            agg["sum"] += metric_point.value
            agg["min"] = min(agg["min"], metric_point.value)
            agg["max"] = max(agg["max"], metric_point.value)
            agg["values"].append(metric_point.value)

    def get_real_time_metrics(self, component: str | None = None) -> dict[str, Any]:
        """Get current real-time metrics with aggregations."""
        with self._lock:
            recent_metrics = []
            cutoff_time = datetime.now(UTC) - timedelta(minutes=5)

            for metric in self.metrics_buffer:
                if metric.timestamp >= cutoff_time:
                    if component is None or metric.component == component:
                        recent_metrics.append(metric)

            # Calculate aggregations
            aggregated_data = {}
            for key, agg in self.aggregated_metrics.items():
                if component is None or key.startswith(component + "."):
                    if agg["count"] > 0:
                        aggregated_data[key] = {
                            "count": agg["count"],
                            "average": agg["sum"] / agg["count"],
                            "min": agg["min"],
                            "max": agg["max"],
                            "recent_values": list(agg["values"])[-10:],  # Last 10 values
                        }

            return {
                "collection_stats": self.collection_stats,
                "recent_metrics_count": len(recent_metrics),
                "aggregated_metrics": aggregated_data,
                "buffer_utilization": len(self.metrics_buffer) / self.max_memory_points,
            }

    def get_metrics_for_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        component: str | None = None,
    ) -> list[MetricPoint]:
        """Get metrics for specific time range."""
        with self._lock:
            filtered_metrics = []
            for metric in self.metrics_buffer:
                if start_time <= metric.timestamp <= end_time:
                    if component is None or metric.component == component:
                        filtered_metrics.append(metric)

            return filtered_metrics


class AlertManager:
    """Intelligent alert management with rule-based and ML-based detection."""

    def __init__(self) -> None:
        """Initialize alert manager."""
        self.alert_rules: dict[str, dict[str, Any]] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.alert_stats = {
            "total_alerts": 0,
            "alerts_by_severity": defaultdict(int),
            "alerts_by_component": defaultdict(int),
            "average_resolution_time_minutes": 0.0,
        }

        self._lock = threading.RLock()

    def add_alert_rule(
        self,
        rule_id: str,
        component: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        title: str,
        description: str,
        recommended_actions: list[str] | None = None,
    ) -> None:
        """Add alert rule for automatic detection."""
        self.alert_rules[rule_id] = {
            "component": component,
            "metric_name": metric_name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "title": title,
            "description": description,
            "recommended_actions": recommended_actions or [],
            "enabled": True,
            "last_evaluation": None,
            "consecutive_violations": 0,
        }

        logger.info(f"Added alert rule: {rule_id} for {component}.{metric_name}")

    def evaluate_alerts(self, metrics: list[MetricPoint]) -> list[Alert]:
        """Evaluate metrics against alert rules and generate alerts."""
        new_alerts = []

        with self._lock:
            # Group metrics by component and name
            metric_values = defaultdict(list)
            for metric in metrics:
                key = f"{metric.component}.{metric.metric_name}"
                if isinstance(metric.value, (int, float)):
                    metric_values[key].append(metric.value)

            # Evaluate each alert rule
            for rule_id, rule in self.alert_rules.items():
                if not rule["enabled"]:
                    continue

                key = f"{rule['component']}.{rule['metric_name']}"
                if key not in metric_values:
                    continue

                latest_value = metric_values[key][-1]  # Get latest value

                # Check condition
                condition_met = self._evaluate_condition(
                    latest_value,
                    rule["condition"],
                    rule["threshold"],
                )

                if condition_met:
                    rule["consecutive_violations"] += 1
                    rule["last_evaluation"] = datetime.now(UTC)

                    # Only create alert if not already active or if this is first violation
                    alert_key = f"{rule_id}_{rule['component']}_{rule['metric_name']}"
                    if alert_key not in self.active_alerts:
                        alert = self._create_alert(rule_id, rule, latest_value)
                        self.active_alerts[alert_key] = alert
                        new_alerts.append(alert)
                        self.alert_history.append(alert)

                        # Update statistics
                        self.alert_stats["total_alerts"] += 1
                        self.alert_stats["alerts_by_severity"][alert.severity.value] += 1
                        self.alert_stats["alerts_by_component"][rule["component"]] += 1

                        logger.warning(
                            f"Alert generated: {alert.title} - {alert.description}",
                        )
                else:
                    # Condition not met, reset consecutive violations
                    rule["consecutive_violations"] = 0

        return new_alerts

    def _evaluate_condition(
        self,
        value: float,
        condition: str,
        threshold: float,
    ) -> bool:
        """Evaluate alert condition."""
        if condition == "gt":
            return value > threshold
        if condition == "lt":
            return value < threshold
        if condition == "eq":
            return value == threshold
        if condition == "gte":
            return value >= threshold
        if condition == "lte":
            return value <= threshold
        return False

    def _create_alert(
        self,
        rule_id: str,
        rule: dict[str, Any],
        current_value: float,
    ) -> Alert:
        """Create alert from rule and current value."""
        alert_id = f"alert_{int(time.time() * 1000000)}_{rule_id}"

        return Alert(
            alert_id=alert_id,
            severity=rule["severity"],
            title=rule["title"],
            description=rule["description"],
            component=rule["component"],
            metric_name=rule["metric_name"],
            threshold_value=rule["threshold"],
            current_value=current_value,
            condition=rule["condition"],
            timestamp=datetime.now(UTC),
            recommended_actions=rule["recommended_actions"],
        )

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge alert."""
        with self._lock:
            for alert in self.active_alerts.values():
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_by = acknowledged_by
                    logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                    return True
            return False

    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve alert and update statistics."""
        with self._lock:
            for alert_key, alert in list(self.active_alerts.items()):
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_by = resolved_by
                    alert.resolution_time = datetime.now(UTC)

                    # Update resolution time statistics
                    resolution_duration = (
                        alert.resolution_time - alert.timestamp
                    ).total_seconds() / 60
                    total_resolved = sum(1 for a in self.alert_history if a.resolution_time)
                    if total_resolved > 0:
                        current_avg = self.alert_stats["average_resolution_time_minutes"]
                        self.alert_stats["average_resolution_time_minutes"] = (
                            current_avg * (total_resolved - 1) + resolution_duration
                        ) / total_resolved

                    # Remove from active alerts
                    del self.active_alerts[alert_key]

                    logger.info(
                        f"Alert {alert_id} resolved by {resolved_by} in {resolution_duration:.1f} minutes",
                    )
                    return True
            return False

    def get_active_alerts(
        self,
        severity: AlertSeverity | None = None,
    ) -> list[Alert]:
        """Get currently active alerts."""
        with self._lock:
            alerts = list(self.active_alerts.values())
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            return alerts

    def get_alert_statistics(self) -> dict[str, Any]:
        """Get alert management statistics."""
        with self._lock:
            return {
                **self.alert_stats,
                "active_alerts_count": len(self.active_alerts),
                "alert_rules_count": len(self.alert_rules),
                "recent_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "component": alert.component,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in list(self.alert_history)[-10:]  # Last 10 alerts
                ],
            }


class TrendAnalyzer:
    """Advanced trend analysis with predictive capabilities."""

    def __init__(self) -> None:
        """Initialize trend analyzer."""
        self.trend_cache: dict[str, dict[str, Any]] = {}
        self.trend_models: dict[str, dict[str, Any]] = {}

    def analyze_trend(
        self,
        metric_points: list[MetricPoint],
        time_window_hours: int = 24,
    ) -> dict[str, Any]:
        """Analyze trend for metric points within time window."""
        if not metric_points:
            return {"trend": "no_data", "confidence": 0.0}

        # Sort by timestamp
        metric_points.sort(key=lambda x: x.timestamp)

        # Extract values and timestamps
        values = [m.value for m in metric_points if isinstance(m.value, (int, float))]
        timestamps = [
            m.timestamp.timestamp() for m in metric_points if isinstance(m.value, (int, float))
        ]

        if len(values) < 2:
            return {"trend": "insufficient_data", "confidence": 0.0}

        # Calculate trend statistics
        return {
            "data_points": len(values),
            "time_window_hours": time_window_hours,
            "current_value": values[-1] if values else None,
            "average_value": statistics.mean(values),
            "median_value": statistics.median(values),
            "min_value": min(values),
            "max_value": max(values),
            "standard_deviation": statistics.stdev(values) if len(values) > 1 else 0.0,
            "trend_direction": self._calculate_trend_direction(values),
            "trend_strength": self._calculate_trend_strength(values),
            "seasonality_detected": self._detect_seasonality(timestamps, values),
            "anomalies_detected": self._detect_anomalies(values),
            "predicted_next_value": self._predict_next_value(values),
            "confidence_score": min(
                1.0,
                len(values) / 100,
            ),  # More data = higher confidence
        }

    def _calculate_trend_direction(self, values: list[float]) -> str:
        """Calculate trend direction using linear regression."""
        if len(values) < 2:
            return "stable"

        # Simple linear regression
        x = list(range(len(values)))
        n = len(values)

        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        # Calculate slope
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

        if abs(slope) < 0.01:
            return "stable"
        if slope > 0:
            return "increasing"
        return "decreasing"

    def _calculate_trend_strength(self, values: list[float]) -> float:
        """Calculate trend strength (0.0-1.0)."""
        if len(values) < 3:
            return 0.0

        # Calculate correlation coefficient for trend strength
        x = list(range(len(values)))
        n = len(values)

        mean_x = sum(x) / n
        mean_y = sum(values) / n

        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        sum_sq_y = sum((values[i] - mean_y) ** 2 for i in range(n))

        denominator = (sum_sq_x * sum_sq_y) ** 0.5

        if denominator == 0:
            return 0.0

        correlation = abs(numerator / denominator)
        return min(1.0, correlation)

    def _detect_seasonality(self, timestamps: list[float], values: list[float]) -> bool:
        """Simple seasonality detection."""
        if len(values) < 24:  # Need at least 24 data points for daily seasonality
            return False

        # Check for periodic patterns (simplified)
        # This is a basic implementation - can be enhanced with proper time series analysis
        return len(values) % 24 == 0  # Very basic heuristic

    def _detect_anomalies(self, values: list[float]) -> list[int]:
        """Detect anomalies using statistical methods."""
        if len(values) < 10:
            return []

        anomalies = []
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)

        # Flag values > 2 standard deviations from mean
        threshold = 2 * std_val

        for i, value in enumerate(values):
            if abs(value - mean_val) > threshold:
                anomalies.append(i)

        return anomalies

    def _predict_next_value(self, values: list[float]) -> float | None:
        """Simple prediction using moving average."""
        if len(values) < 3:
            return None

        # Use exponential moving average for prediction
        alpha = 0.3  # Smoothing factor
        ema = values[0]

        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * ema

        return ema


class UserExperienceTracker:
    """Comprehensive user experience tracking and analysis."""

    def __init__(self) -> None:
        """Initialize user experience tracker."""
        self.active_sessions: dict[str, UserExperienceMetrics] = {}
        self.completed_sessions: deque = deque(maxlen=10000)
        self.aggregated_ux_metrics = defaultdict(
            lambda: {
                "total_sessions": 0,
                "avg_satisfaction": 0.0,
                "avg_completion_rate": 0.0,
                "avg_response_time": 0.0,
                "total_interactions": 0,
                "error_rate": 0.0,
            },
        )

        self._lock = threading.RLock()

    def start_session(self, session_id: str, user_id: str | None = None) -> None:
        """Start tracking user session."""
        with self._lock:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = UserExperienceMetrics(
                    session_id=session_id,
                    user_id=user_id,
                    start_time=datetime.now(UTC),
                )
                logger.debug(f"Started tracking session: {session_id}")

    def end_session(
        self,
        session_id: str,
        satisfaction_score: float | None = None,
    ) -> UserExperienceMetrics | None:
        """End user session and calculate final metrics."""
        with self._lock:
            if session_id not in self.active_sessions:
                return None

            session = self.active_sessions[session_id]
            session.end_time = datetime.now(UTC)

            # Calculate final metrics
            if session.total_interactions > 0:
                session.completion_rate = (
                    session.successful_interactions / session.total_interactions
                )
                session.error_rate = session.failed_interactions / session.total_interactions

            # Set satisfaction score if provided
            if satisfaction_score is not None:
                session.satisfaction_score = satisfaction_score

            # Calculate bounce rate (single interaction session)
            session.bounce_rate = session.total_interactions <= 1

            # Move to completed sessions
            self.completed_sessions.append(session)
            del self.active_sessions[session_id]

            # Update aggregated metrics
            self._update_aggregated_metrics(session)

            logger.debug(
                f"Completed session: {session_id} with {session.total_interactions} interactions",
            )
            return session

    def record_interaction(
        self,
        session_id: str,
        operation: str,
        success: bool,
        response_time_ms: float,
        feature: str | None = None,
        compliance_violation: bool = False,
    ) -> None:
        """Record user interaction in session."""
        with self._lock:
            if session_id not in self.active_sessions:
                self.start_session(session_id)

            session = self.active_sessions[session_id]
            session.total_interactions += 1

            if success:
                session.successful_interactions += 1
            else:
                session.failed_interactions += 1

            # Update average response time
            if session.total_interactions == 1:
                session.avg_response_time_ms = response_time_ms
            else:
                session.avg_response_time_ms = (
                    session.avg_response_time_ms * (session.total_interactions - 1)
                    + response_time_ms
                ) / session.total_interactions

            # Track feature usage
            if feature:
                session.feature_usage[feature] = session.feature_usage.get(feature, 0) + 1

            # Track compliance violations
            if compliance_violation:
                session.compliance_violations += 1

    def _update_aggregated_metrics(self, session: UserExperienceMetrics) -> None:
        """Update aggregated user experience metrics."""
        user_key = session.user_id or "anonymous"

        agg = self.aggregated_ux_metrics[user_key]
        agg["total_sessions"] += 1

        # Update averages (simple incremental update)
        if session.satisfaction_score is not None:
            agg["avg_satisfaction"] = (
                agg["avg_satisfaction"] * (agg["total_sessions"] - 1) + session.satisfaction_score
            ) / agg["total_sessions"]

        agg["avg_completion_rate"] = (
            agg["avg_completion_rate"] * (agg["total_sessions"] - 1) + session.completion_rate
        ) / agg["total_sessions"]

        agg["avg_response_time"] = (
            agg["avg_response_time"] * (agg["total_sessions"] - 1) + session.avg_response_time_ms
        ) / agg["total_sessions"]

        agg["total_interactions"] += session.total_interactions
        agg["error_rate"] = (
            agg["error_rate"] * (agg["total_sessions"] - 1) + session.error_rate
        ) / agg["total_sessions"]

    def get_user_experience_summary(
        self,
        time_window_hours: int = 24,
    ) -> dict[str, Any]:
        """Get user experience summary for time window."""
        with self._lock:
            cutoff_time = datetime.now(UTC) - timedelta(hours=time_window_hours)

            # Filter recent sessions
            recent_sessions = [
                s for s in self.completed_sessions if s.end_time and s.end_time >= cutoff_time
            ]

            if not recent_sessions:
                return {
                    "time_window_hours": time_window_hours,
                    "total_sessions": 0,
                    "avg_satisfaction": 0.0,
                    "avg_completion_rate": 0.0,
                    "avg_response_time_ms": 0.0,
                }

            # Calculate summary metrics
            total_sessions = len(recent_sessions)
            satisfaction_scores = [
                s.satisfaction_score for s in recent_sessions if s.satisfaction_score is not None
            ]
            completion_rates = [s.completion_rate for s in recent_sessions]
            response_times = [s.avg_response_time_ms for s in recent_sessions]
            bounce_count = sum(1 for s in recent_sessions if s.bounce_rate)
            total_violations = sum(s.compliance_violations for s in recent_sessions)

            return {
                "time_window_hours": time_window_hours,
                "total_sessions": total_sessions,
                "active_sessions": len(self.active_sessions),
                "avg_satisfaction": (
                    statistics.mean(satisfaction_scores) if satisfaction_scores else None
                ),
                "avg_completion_rate": (
                    statistics.mean(completion_rates) if completion_rates else 0.0
                ),
                "avg_response_time_ms": (
                    statistics.mean(response_times) if response_times else 0.0
                ),
                "bounce_rate": (bounce_count / total_sessions if total_sessions > 0 else 0.0),
                "compliance_violation_rate": (
                    total_violations / sum(s.total_interactions for s in recent_sessions)
                    if recent_sessions
                    else 0.0
                ),
                "popular_features": self._get_popular_features(recent_sessions),
                "user_satisfaction_distribution": self._get_satisfaction_distribution(
                    satisfaction_scores,
                ),
            }

    def _get_popular_features(
        self,
        sessions: list[UserExperienceMetrics],
    ) -> list[tuple[str, int]]:
        """Get most popular features from sessions."""
        feature_counts = defaultdict(int)
        for session in sessions:
            for feature, count in session.feature_usage.items():
                feature_counts[feature] += count

        return sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    def _get_satisfaction_distribution(
        self,
        satisfaction_scores: list[float],
    ) -> dict[str, int]:
        """Get distribution of satisfaction scores."""
        if not satisfaction_scores:
            return {}

        distribution = defaultdict(int)
        for score in satisfaction_scores:
            if score <= 2.0:
                distribution["poor"] += 1
            elif score <= 3.0:
                distribution["fair"] += 1
            elif score <= 4.0:
                distribution["good"] += 1
            else:
                distribution["excellent"] += 1

        return dict(distribution)


class CKSMonitoringAnalytics:
    """Comprehensive CKS Monitoring and Analytics System.

    Provides real-time monitoring, historical analytics, user experience tracking,
    and intelligent insights generation for CKS integration optimization.
    """

    def __init__(self, data_dir: str = ".cks_monitoring") -> None:
        """Initialize CKS monitoring and analytics system."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.trend_analyzer = TrendAnalyzer()
        self.ux_tracker = UserExperienceTracker()

        # Initialize database for persistent storage
        self.db_path = self.data_dir / "monitoring.db"
        self._init_database()

        # Monitoring state
        self.monitoring_active = False
        self.component_monitors: dict[str, dict[str, Any]] = {}

        # Default alert rules
        self._setup_default_alert_rules()

        # Thread safety
        self._lock = threading.RLock()

        logger.info("CKS Monitoring and Analytics System initialized")

    def _init_database(self) -> None:
        """Initialize monitoring database for persistent storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Metrics table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        value REAL,
                        timestamp TEXT NOT NULL,
                        component TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        user_id TEXT,
                        session_id TEXT,
                        tags TEXT,
                        metadata TEXT
                    )
                """,
                )

                # Alerts table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS alerts (
                        alert_id TEXT PRIMARY KEY,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        component TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        threshold_value REAL,
                        current_value REAL,
                        condition TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE,
                        acknowledged_by TEXT,
                        resolved_by TEXT,
                        resolution_time TEXT,
                        impact_assessment TEXT,
                        recommended_actions TEXT,
                        tags TEXT
                    )
                """,
                )

                # User experience table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_experience (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        total_interactions INTEGER DEFAULT 0,
                        successful_interactions INTEGER DEFAULT 0,
                        failed_interactions INTEGER DEFAULT 0,
                        avg_response_time_ms REAL DEFAULT 0.0,
                        satisfaction_score REAL,
                        completion_rate REAL DEFAULT 0.0,
                        error_rate REAL DEFAULT 0.0,
                        bounce_rate BOOLEAN DEFAULT FALSE,
                        feature_usage TEXT,
                        compliance_violations INTEGER DEFAULT 0,
                        constitutional_score REAL DEFAULT 1.0
                    )
                """,
                )

                conn.commit()
                logger.debug("Monitoring database initialized")

        except Exception as e:
            logger.exception(f"Failed to initialize monitoring database: {e}")

    def _setup_default_alert_rules(self) -> None:
        """Set up default alert rules for common monitoring scenarios."""
        default_rules = [
            {
                "rule_id": "high_error_rate",
                "component": "system",
                "metric_name": "error_rate",
                "condition": "gt",
                "threshold": 5.0,
                "severity": AlertSeverity.ERROR,
                "title": "High Error Rate Detected",
                "description": "System error rate exceeds 5% threshold",
                "recommended_actions": [
                    "Check system logs",
                    "Verify component health",
                    "Review recent changes",
                ],
            },
            {
                "rule_id": "low_performance",
                "component": "system",
                "metric_name": "avg_response_time_ms",
                "condition": "gt",
                "threshold": 1000.0,
                "severity": AlertSeverity.WARNING,
                "title": "Performance Degradation",
                "description": "Average response time exceeds 1000ms",
                "recommended_actions": [
                    "Check resource utilization",
                    "Review system load",
                    "Consider scaling",
                ],
            },
            {
                "rule_id": "cache_miss_rate_high",
                "component": "performance_optimizer",
                "metric_name": "cache_miss_rate",
                "condition": "gt",
                "threshold": 20.0,
                "severity": AlertSeverity.WARNING,
                "title": "High Cache Miss Rate",
                "description": "Cache miss rate exceeds 20%",
                "recommended_actions": [
                    "Review cache configuration",
                    "Analyze query patterns",
                    "Consider cache warming",
                ],
            },
            {
                "rule_id": "compliance_score_low",
                "component": "cks_validator",
                "metric_name": "compliance_score",
                "condition": "lt",
                "threshold": 0.8,
                "severity": AlertSeverity.ERROR,
                "title": "Low Compliance Score",
                "description": "CKS compliance score below 80%",
                "recommended_actions": [
                    "Review compliance violations",
                    "Update constitutional rules",
                    "Check validation logic",
                ],
            },
        ]

        for rule in default_rules:
            self.alert_manager.add_alert_rule(**rule)

        logger.info(f"Added {len(default_rules)} default alert rules")

    async def start_monitoring(self) -> None:
        """Start all monitoring and analytics systems."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True

        # Start background monitoring tasks and track references
        self._background_tasks = [
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._analytics_loop()),
            asyncio.create_task(self._alert_evaluation_loop()),
        ]

        logger.info("CKS Monitoring and Analytics started")

    async def stop_monitoring(self) -> None:
        """Stop all monitoring and analytics systems."""
        self.monitoring_active = False

        # Cancel all background tasks
        if hasattr(self, "_background_tasks"):
            for task in self._background_tasks:
                task.cancel()

            # Wait for tasks to complete cancellation
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            self._background_tasks.clear()

        logger.info("CKS Monitoring and Analytics stopped")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for continuous data collection."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                await self._collect_system_metrics()

                # Store recent metrics to database
                await self._persist_metrics()

                # Sleep for collection interval
                await asyncio.sleep(30)  # 30-second collection interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)

    async def _analytics_loop(self) -> None:
        """Background analytics loop for trend analysis and insights."""
        while self.monitoring_active:
            try:
                # Analyze trends
                await self._analyze_trends()

                # Generate insights
                await self._generate_insights()

                # Sleep for analytics interval
                await asyncio.sleep(300)  # 5-minute analytics interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Analytics loop error: {e}")
                await asyncio.sleep(30)

    async def _alert_evaluation_loop(self) -> None:
        """Background loop for continuous alert evaluation."""
        while self.monitoring_active:
            try:
                # Get recent metrics
                recent_time = datetime.now(UTC) - timedelta(minutes=5)
                recent_metrics = self.metrics_collector.get_metrics_for_time_range(
                    recent_time,
                    datetime.now(UTC),
                )

                # Evaluate alerts
                new_alerts = self.alert_manager.evaluate_alerts(recent_metrics)

                # Send notifications for new alerts
                for alert in new_alerts:
                    await self._send_alert_notification(alert)

                # Sleep for alert evaluation interval
                await asyncio.sleep(60)  # 1-minute alert evaluation interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Alert evaluation loop error: {e}")
                await asyncio.sleep(10)

    async def _collect_system_metrics(self) -> None:
        """Collect system-wide metrics."""
        current_time = datetime.now(UTC)

        # Collect metrics from all registered components
        for component_name, component_data in self.component_monitors.items():
            try:
                if "metrics_callback" in component_data:
                    metrics = component_data["metrics_callback"]()

                    for metric_name, value in metrics.items():
                        metric_point = MetricPoint(
                            metric_name=metric_name,
                            metric_type=MetricType.GAUGE,
                            value=value,
                            timestamp=current_time,
                            component=component_name,
                            operation="monitoring",
                        )

                        self.metrics_collector.collect_metric(metric_point)

            except Exception as e:
                logger.exception(f"Failed to collect metrics from {component_name}: {e}")

    async def _persist_metrics(self) -> None:
        """Persist recent metrics to database."""
        try:
            cutoff_time = datetime.now(UTC) - timedelta(minutes=1)
            recent_metrics = self.metrics_collector.get_metrics_for_time_range(
                cutoff_time,
                datetime.now(UTC),
            )

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for metric in recent_metrics:
                    cursor.execute(
                        """
                        INSERT INTO metrics (
                            metric_name, metric_type, value, timestamp, component,
                            operation, user_id, session_id, tags, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            metric.metric_name,
                            metric.metric_type.value,
                            (
                                float(metric.value)
                                if isinstance(metric.value, (int, float))
                                else None
                            ),
                            metric.timestamp.isoformat(),
                            metric.component,
                            metric.operation,
                            metric.user_id,
                            metric.session_id,
                            json.dumps(metric.tags),
                            json.dumps(metric.metadata) if metric.metadata else None,
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.exception(f"Failed to persist metrics: {e}")

    async def _analyze_trends(self) -> None:
        """Analyze trends for all metrics."""
        time_window = datetime.now(UTC) - timedelta(hours=24)

        # Get unique component-metric combinations
        with self._lock:
            components = set(self.component_monitors.keys())

        for component in components:
            recent_metrics = self.metrics_collector.get_metrics_for_time_range(
                time_window,
                datetime.now(UTC),
                component,
            )

            if not recent_metrics:
                continue

            # Group by metric name
            metric_groups = defaultdict(list)
            for metric in recent_metrics:
                metric_groups[metric.metric_name].append(metric)

            # Analyze trends for each metric
            for metric_name, metrics in metric_groups.items():
                try:
                    trend_analysis = self.trend_analyzer.analyze_trend(metrics)

                    # Create insight if significant trend detected
                    if (
                        trend_analysis["confidence_score"] > 0.7
                        and trend_analysis["trend_direction"] != "stable"
                    ):
                        insight = self._create_trend_insight(
                            component,
                            metric_name,
                            trend_analysis,
                        )

                        if insight:
                            await self._process_insight(insight)

                except Exception as e:
                    logger.exception(
                        f"Trend analysis failed for {component}.{metric_name}: {e}",
                    )

    async def _generate_insights(self) -> None:
        """Generate performance and optimization insights."""
        try:
            # Get current metrics
            real_time_metrics = self.metrics_collector.get_real_time_metrics()

            # Generate insights based on current state
            insights = []

            # Performance insights
            if "avg_response_time_ms" in real_time_metrics["aggregated_metrics"]:
                avg_response = real_time_metrics["aggregated_metrics"]["avg_response_time_ms"][
                    "average"
                ]
                if avg_response > 500:  # >500ms
                    insights.append(
                        PerformanceInsight(
                            insight_id=f"perf_insight_{int(time.time())}",
                            category="performance",
                            severity=AlertSeverity.WARNING,
                            title="High Response Time Detected",
                            description=f"Average response time is {avg_response:.1f}ms, above optimal threshold",
                            current_metrics={"avg_response_time_ms": avg_response},
                            predicted_impact="User experience degradation and reduced throughput",
                            recommended_actions=[
                                "Check resource utilization",
                                "Analyze slow queries",
                                "Consider performance optimization",
                            ],
                            estimated_improvement={
                                "response_time_improvement_percent": 30.0,
                            },
                            confidence_score=0.8,
                            timestamp=datetime.now(UTC),
                            applies_to=["system"],
                        ),
                    )

            # Reliability insights
            error_rate_metrics = real_time_metrics["aggregated_metrics"].get(
                "error_rate",
                {},
            )
            if error_rate_metrics.get("average", 0) > 2.0:  # >2% error rate
                insights.append(
                    PerformanceInsight(
                        insight_id=f"reliability_insight_{int(time.time())}",
                        category="reliability",
                        severity=AlertSeverity.ERROR,
                        title="Elevated Error Rate",
                        description=f"Error rate is {error_rate_metrics['average']:.1f}%, above acceptable threshold",
                        current_metrics={"error_rate": error_rate_metrics["average"]},
                        predicted_impact="System reliability issues and user dissatisfaction",
                        recommended_actions=[
                            "Review error logs",
                            "Check component health",
                            "Implement additional error handling",
                        ],
                        estimated_improvement={"error_rate_reduction_percent": 50.0},
                        confidence_score=0.9,
                        timestamp=datetime.now(UTC),
                        applies_to=["system"],
                    ),
                )

            # Process generated insights
            for insight in insights:
                await self._process_insight(insight)

        except Exception as e:
            logger.exception(f"Insight generation failed: {e}")

    def _create_trend_insight(
        self,
        component: str,
        metric_name: str,
        trend_analysis: dict[str, Any],
    ) -> PerformanceInsight | None:
        """Create insight from trend analysis."""
        if trend_analysis["confidence_score"] < 0.5:
            return None

        trend_direction = trend_analysis["trend_direction"]

        if metric_name == "compliance_score" and trend_direction == "decreasing":
            return PerformanceInsight(
                insight_id=f"compliance_trend_{int(time.time())}",
                category="compliance",
                severity=AlertSeverity.ERROR,
                title="Declining Compliance Score Trend",
                description=f"Compliance score showing {trend_direction} trend with {trend_analysis['confidence_score']:.1%} confidence",
                current_metrics={"compliance_score": trend_analysis["current_value"]},
                predicted_impact="Potential compliance violations and constitutional breaches",
                recommended_actions=[
                    "Review recent changes",
                    "Audit compliance rules",
                    "Strengthen validation processes",
                ],
                estimated_improvement={"compliance_score_improvement": 0.1},
                confidence_score=trend_analysis["confidence_score"],
                timestamp=datetime.now(UTC),
                applies_to=[component],
            )

        return None

    async def _process_insight(self, insight: PerformanceInsight) -> None:
        """Process generated insight (storage, notification, etc.)."""
        try:
            # Store insight to database
            await self._store_insight(insight)

            # Generate alert if high severity
            if insight.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
                alert = Alert(
                    alert_id=f"insight_alert_{insight.insight_id}",
                    severity=insight.severity,
                    title=insight.title,
                    description=insight.description,
                    component=insight.applies_to[0] if insight.applies_to else "system",
                    metric_name="insight",
                    threshold_value=0.0,
                    current_value=insight.confidence_score,
                    condition="insight",
                    timestamp=insight.timestamp,
                    recommended_actions=insight.recommended_actions,
                )

                self.alert_manager.active_alerts[alert.alert_id] = alert
                await self._send_alert_notification(alert)

            logger.info(f"Processed insight: {insight.title}")

        except Exception as e:
            logger.exception(f"Failed to process insight: {e}")

    async def _store_insight(self, insight: PerformanceInsight) -> None:
        """Store insight to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS insights (
                        insight_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        current_metrics TEXT,
                        predicted_impact TEXT,
                        recommended_actions TEXT,
                        estimated_improvement TEXT,
                        confidence_score REAL,
                        timestamp TEXT NOT NULL,
                        applies_to TEXT
                    )
                """,
                )

                cursor.execute(
                    """
                    INSERT INTO insights (
                        insight_id, category, severity, title, description,
                        current_metrics, predicted_impact, recommended_actions,
                        estimated_improvement, confidence_score, timestamp, applies_to
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        insight.insight_id,
                        insight.category,
                        insight.severity.value,
                        insight.title,
                        insight.description,
                        json.dumps(insight.current_metrics),
                        insight.predicted_impact,
                        json.dumps(insight.recommended_actions),
                        json.dumps(insight.estimated_improvement),
                        insight.confidence_score,
                        insight.timestamp.isoformat(),
                        json.dumps(insight.applies_to),
                    ),
                )

                conn.commit()

        except Exception as e:
            logger.exception(f"Failed to store insight: {e}")

    async def _send_alert_notification(self, alert: Alert) -> None:
        """Send alert notification (can be extended with various channels)."""
        try:
            # Log alert
            logger.warning(
                f"ALERT: {alert.title} - {alert.description} "
                f"(Severity: {alert.severity.value}, Component: {alert.component})",
            )

            # Here you can extend with various notification channels:
            # - Email notifications
            # - Slack/webhook notifications
            # - SMS alerts
            # - Dashboard notifications

        except Exception as e:
            logger.exception(f"Failed to send alert notification: {e}")

    def register_component_monitoring(
        self,
        component_name: str,
        metrics_callback: Callable[[], dict[str, float]],
        health_check: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        """Register component for monitoring."""
        with self._lock:
            self.component_monitors[component_name] = {
                "metrics_callback": metrics_callback,
                "health_check": health_check,
                "registered_at": datetime.now(UTC).isoformat(),
            }

            # Register with health monitor if available
            if health_check:
                # This would integrate with the health monitor from the fallback handler
                pass

        logger.info(f"Registered component monitoring for: {component_name}")

    async def collect_metric(
        self,
        metric_name: str,
        metric_type: MetricType,
        value: int | float | dict[str, Any],
        component: str,
        operation: str,
        user_id: str | None = None,
        session_id: str | None = None,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Collect metric point."""
        metric_point = MetricPoint(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(UTC),
            component=component,
            operation=operation,
            user_id=user_id,
            session_id=session_id,
            tags=tags or {},
            metadata=metadata or {},
        )

        self.metrics_collector.collect_metric(metric_point)

    async def track_user_interaction(
        self,
        session_id: str,
        operation: str,
        success: bool,
        response_time_ms: float,
        user_id: str | None = None,
        feature: str | None = None,
        compliance_violation: bool = False,
    ) -> None:
        """Track user interaction for experience metrics."""
        # Start session if not already tracking
        if session_id not in self.ux_tracker.active_sessions:
            self.ux_tracker.start_session(session_id, user_id)

        # Record interaction
        self.ux_tracker.record_interaction(
            session_id,
            operation,
            success,
            response_time_ms,
            feature,
            compliance_violation,
        )

        # Collect metrics
        await self.collect_metric(
            metric_name="user_interaction",
            metric_type=MetricType.COUNTER,
            value=1,
            component="user_experience",
            operation=operation,
            user_id=user_id,
            session_id=session_id,
            tags={"success": str(success), "feature": feature or "unknown"},
        )

    async def end_user_session(
        self,
        session_id: str,
        satisfaction_score: float | None = None,
    ) -> UserExperienceMetrics | None:
        """End user session and collect final metrics."""
        session = self.ux_tracker.end_session(session_id, satisfaction_score)

        if session:
            # Collect session metrics
            await self.collect_metric(
                metric_name="session_completed",
                metric_type=MetricType.COUNTER,
                value=1,
                component="user_experience",
                operation="session_end",
                session_id=session_id,
                metadata={
                    "total_interactions": session.total_interactions,
                    "completion_rate": session.completion_rate,
                    "avg_response_time_ms": session.avg_response_time_ms,
                    "satisfaction_score": session.satisfaction_score,
                },
            )

        return session

    def get_real_time_dashboard(self) -> dict[str, Any]:
        """Get comprehensive real-time dashboard data."""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "system_metrics": self.metrics_collector.get_real_time_metrics(),
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in self.alert_manager.get_active_alerts()
            ],
            "alert_statistics": self.alert_manager.get_alert_statistics(),
            "user_experience": self.ux_tracker.get_user_experience_summary(
                time_window_hours=1,
            ),
            "component_status": {
                name: {
                    "monitored": True,
                    "last_update": data.get("registered_at"),
                    "health": "unknown",  # Would be populated by health checks
                }
                for name, data in self.component_monitors.items()
            },
            "monitoring_status": {
                "active": self.monitoring_active,
                "registered_components": len(self.component_monitors),
                "metrics_collected": self.metrics_collector.collection_stats["total_collected"],
                "collection_rate": self.metrics_collector.collection_stats[
                    "collection_rate_per_second"
                ],
            },
        }

    def get_analytics_report(
        self,
        start_time: datetime,
        end_time: datetime,
        components: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate comprehensive analytics report for time range."""
        # Get metrics for time range
        metrics = self.metrics_collector.get_metrics_for_time_range(
            start_time,
            end_time,
        )

        if components:
            metrics = [m for m in metrics if m.component in components]

        # Analyze trends
        trend_analyses = {}
        for component in {m.component for m in metrics}:
            component_metrics = [m for m in metrics if m.component == component]
            for metric_name in {m.metric_name for m in component_metrics}:
                metric_points = [m for m in component_metrics if m.metric_name == metric_name]
                if len(metric_points) >= 3:  # Need minimum data for trend analysis
                    trend_key = f"{component}.{metric_name}"
                    trend_analyses[trend_key] = self.trend_analyzer.analyze_trend(
                        metric_points,
                    )

        # Get user experience data
        ux_summary = self.ux_tracker.get_user_experience_summary(
            time_window_hours=int((end_time - start_time).total_seconds() / 3600),
        )

        # Get alert history
        alert_history = list(self.alert_manager.alert_history)
        time_range_alerts = [
            alert for alert in alert_history if start_time <= alert.timestamp <= end_time
        ]

        return {
            "report_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_hours": (end_time - start_time).total_seconds() / 3600,
            },
            "metrics_summary": {
                "total_metrics": len(metrics),
                "unique_components": len({m.component for m in metrics}),
                "metric_types": list({m.metric_type.value for m in metrics}),
                "data_points_by_component": {
                    component: len([m for m in metrics if m.component == component])
                    for component in {m.component for m in metrics}
                },
            },
            "trend_analyses": trend_analyses,
            "user_experience": ux_summary,
            "alert_summary": {
                "total_alerts": len(time_range_alerts),
                "alerts_by_severity": {
                    severity.value: len(
                        [a for a in time_range_alerts if a.severity == severity],
                    )
                    for severity in AlertSeverity
                },
                "alerts_by_component": {
                    component: len(
                        [a for a in time_range_alerts if a.component == component],
                    )
                    for component in {a.component for a in time_range_alerts}
                },
                "average_resolution_time_minutes": self.alert_manager.alert_stats[
                    "average_resolution_time_minutes"
                ],
            },
            "performance_insights": self._generate_period_insights(
                metrics,
                time_range_alerts,
            ),
            "recommendations": self._generate_recommendations(
                trend_analyses,
                ux_summary,
                time_range_alerts,
            ),
        }

    def _generate_period_insights(
        self,
        metrics: list[MetricPoint],
        alerts: list[Alert],
    ) -> list[dict[str, Any]]:
        """Generate insights for the reporting period."""
        insights = []

        # Performance insights
        response_time_metrics = [m for m in metrics if m.metric_name == "avg_response_time_ms"]
        if response_time_metrics:
            avg_response = statistics.mean(
                [
                    float(m.value)
                    for m in response_time_metrics
                    if isinstance(m.value, (int, float))
                ],
            )
            if avg_response > 200:  # >200ms average
                insights.append(
                    {
                        "type": "performance",
                        "severity": "warning",
                        "title": "Elevated Average Response Time",
                        "description": f"Average response time of {avg_response:.1f}ms during reporting period",
                        "impact": "User experience degradation",
                        "recommendation": "Investigate performance bottlenecks and optimize slow operations",
                    },
                )

        # Reliability insights
        if alerts:
            critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
            if len(critical_alerts) > 0:
                insights.append(
                    {
                        "type": "reliability",
                        "severity": "critical",
                        "title": "Critical Alerts Detected",
                        "description": f"{len(critical_alerts)} critical alerts during reporting period",
                        "impact": "System reliability and availability concerns",
                        "recommendation": "Immediate attention required for critical issues",
                    },
                )

        return insights

    def _generate_recommendations(
        self,
        trend_analyses: dict[str, dict[str, Any]],
        ux_summary: dict[str, Any],
        alerts: list[Alert],
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []

        # Performance recommendations
        degrading_trends = [
            key
            for key, analysis in trend_analyses.items()
            if analysis.get("trend_direction") == "decreasing"
            and analysis.get("confidence_score", 0) > 0.7
        ]

        if degrading_trends:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "high",
                    "title": "Address Performance Degradation",
                    "description": f"Degrading trends detected in: {', '.join(degrading_trends)}",
                    "actions": [
                        "Investigate root causes of performance degradation",
                        "Implement performance monitoring and alerting",
                        "Consider system optimization or scaling",
                    ],
                    "estimated_impact": "Improved system performance and user experience",
                },
            )

        # User experience recommendations
        if ux_summary.get("avg_completion_rate", 1.0) < 0.8:
            recommendations.append(
                {
                    "category": "user_experience",
                    "priority": "medium",
                    "title": "Improve Task Completion Rate",
                    "description": f"Current completion rate is {ux_summary.get('avg_completion_rate', 0):.1%}, below optimal",
                    "actions": [
                        "Review and simplify complex workflows",
                        "Provide better user guidance and feedback",
                        "Improve error handling and recovery mechanisms",
                    ],
                    "estimated_impact": "Higher user satisfaction and task completion rates",
                },
            )

        # Alert management recommendations
        if len(alerts) > 10:  # High alert volume
            recommendations.append(
                {
                    "category": "monitoring",
                    "priority": "medium",
                    "title": "Optimize Alert Configuration",
                    "description": f"High alert volume ({len(alerts)} alerts) during reporting period",
                    "actions": [
                        "Review and adjust alert thresholds",
                        "Implement alert grouping and correlation",
                        "Consider adding automated resolution procedures",
                    ],
                    "estimated_impact": "Reduced alert noise and improved response efficiency",
                },
            )

        return recommendations


# Export main classes
__all__ = [
    "Alert",
    "AlertManager",
    "AlertSeverity",
    "CKSMonitoringAnalytics",
    "ComplianceTrend",
    "MetricPoint",
    "MetricType",
    "MetricsCollector",
    "PerformanceInsight",
    "TimeGranularity",
    "TrendAnalyzer",
    "UserExperienceMetrics",
    "UserExperienceTracker",
]
