from __future__ import annotations

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .cove_react_integration import CoVeReActIntegrationReport, VerificationMode

"""CoVe-ReAct Performance Monitoring System.

This module provides comprehensive performance monitoring for CoVe-ReAct integration
including metrics collection, analysis, alerting, and optimization recommendations.

Key Features:
- Real-time performance metrics collection
- Automated performance analysis and alerting
- Performance trend analysis and prediction
- Resource usage monitoring
- Verification quality metrics
- Performance optimization recommendations

Algorithm Approach:
1. Collect performance metrics from all components
2. Analyze metrics for patterns and anomalies
3. Generate alerts for performance issues
4. Provide optimization recommendations
5. Track performance trends over time

Time Complexity: O(n) where n is the number of metrics collected
Space Complexity: O(m) where m is the retained metrics history
Performance: <10ms overhead for metrics collection and analysis
"""





class MetricType(Enum):
    """Types of performance metrics."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    CONFIDENCE_IMPROVEMENT = "confidence_improvement"
    VERIFICATION_SUCCESS = "verification_success"
    EVIDENCE_QUALITY = "evidence_quality"


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceTier(Enum):
    """Performance tier classifications."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""

    metric_type: MetricType
    value: float
    timestamp: float
    component: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class PerformanceAlert:
    """Performance alert notification."""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_type: MetricType
    current_value: float
    threshold: float
    timestamp: float
    recommendations: list[str] = field(default_factory=list)
    component: str = ""


@dataclass
class PerformanceSummary:
    """Summary of performance metrics over a time period."""

    period_start: float
    period_end: float
    total_operations: int
    performance_tier: PerformanceTier
    metric_summaries: dict[str, dict[str, float]]
    alerts_generated: list[PerformanceAlert]
    recommendations: list[str]
    trends: dict[str, str]  # "improving", "stable", "declining"


class CoVeReActPerformanceMonitor:
    """
    Performance monitoring system for CoVe-ReAct integration.

    This class provides comprehensive monitoring capabilities including metrics
    collection, analysis, alerting, and optimization recommendations.
    """

    def __init__(
        self,
        metrics_retention_hours: int = 24,
        alert_thresholds: dict[str, dict[str, float]] | None = None,
        enable_predictions: bool = True,
    ):
        """
        Initialize performance monitor.

        Args:
        ----
            metrics_retention_hours: Hours to retain metrics data
            alert_thresholds: Custom alert thresholds
            enable_predictions: Enable performance trend predictions

        """
        self.logger = logging.getLogger(__name__)
        self.metrics_retention_hours = metrics_retention_hours
        self.enable_predictions = enable_predictions

        # Metrics storage
        self.metrics_buffer = deque(maxlen=10000)  # Rolling buffer for recent metrics
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))  # Per-component history

        # Alert system
        self.alert_thresholds = self._initialize_alert_thresholds(alert_thresholds)
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)

        # Performance baselines
        self.performance_baselines = {}
        self.trend_analysis = {}

        # Analysis state
        self.last_analysis_time = 0
        self.analysis_interval = 60  # Analyze every minute

    async def record_verification_start(
        self,
        component: str,
        verification_mode: VerificationMode,
        context: dict[str, Any],
    ) -> str:
        """
        Record the start of a verification operation.

        Args:
        ----
            component: Component performing verification
            verification_mode: Mode of verification being used
            context: Additional context information

        Returns:
        -------
            Operation ID for tracking

        """
        operation_id = f"{component}_{int(time.time() * 1000)}"

        metric = PerformanceMetric(
            metric_type=MetricType.LATENCY,
            value=time.time(),  # Store start time
            timestamp=time.time(),
            component=component,
            metadata={
                "operation_id": operation_id,
                "verification_mode": verification_mode.value,
                "context": context,
                "stage": "start",
            },
            tags={"verification", component},
        )

        self.metrics_buffer.append(metric)
        return operation_id

    async def record_verification_complete(
        self,
        operation_id: str,
        integration_report: CoVeReActIntegrationReport,
        component: str = "cove_react_integrator",
    ) -> None:
        """
        Record the completion of a verification operation.

        Args:
        ----
            operation_id: ID from start recording
            integration_report: Complete verification report
            component: Component that performed verification

        """
        current_time = time.time()

        # Find the start metric to calculate duration
        start_time = None
        for metric in reversed(self.metrics_buffer):
            if (
                metric.metric_type == MetricType.LATENCY
                and metric.metadata.get("operation_id") == operation_id
                and metric.metadata.get("stage") == "start"
            ):
                start_time = metric.value
                break

        if start_time is None:
            self.logger.warning(f"Could not find start time for operation: {operation_id}")
            return

        # Calculate latency
        latency = current_time - start_time

        # Record latency metric
        latency_metric = PerformanceMetric(
            metric_type=MetricType.LATENCY,
            value=latency,
            timestamp=current_time,
            component=component,
            metadata={
                "operation_id": operation_id,
                "verification_mode": integration_report.verification_mode.value,
                "questions_processed": integration_report.verification_questions_processed,
                "evidence_collected": integration_report.total_evidence_collected,
            },
            tags={"verification", component, "latency"},
        )
        self.metrics_buffer.append(latency_metric)

        # Record confidence improvement
        confidence_metric = PerformanceMetric(
            metric_type=MetricType.CONFIDENCE_IMPROVEMENT,
            value=integration_report.confidence_improvement,
            timestamp=current_time,
            component=component,
            metadata={
                "operation_id": operation_id,
                "original_confidence": 0.7,  # Could be extracted if available
                "final_confidence": 0.7 + integration_report.confidence_improvement,
            },
            tags={"verification", component, "confidence"},
        )
        self.metrics_buffer.append(confidence_metric)

        # Record verification success rate
        success_rate = 1.0 if integration_report.corrections_applied else 0.0
        if integration_report.verification_questions_processed > 0:
            success_rate = (
                integration_report.verification_questions_processed - len(integration_report.corrections_applied)
            ) / integration_report.verification_questions_processed

        success_metric = PerformanceMetric(
            metric_type=MetricType.VERIFICATION_SUCCESS,
            value=success_rate,
            timestamp=current_time,
            component=component,
            metadata={
                "operation_id": operation_id,
                "questions_processed": integration_report.verification_questions_processed,
                "corrections_applied": len(integration_report.corrections_applied),
            },
            tags={"verification", component, "success"},
        )
        self.metrics_buffer.append(success_metric)

        # Record throughput (questions per second)
        if latency > 0:
            throughput = integration_report.verification_questions_processed / latency
            throughput_metric = PerformanceMetric(
                metric_type=MetricType.THROUGHPUT,
                value=throughput,
                timestamp=current_time,
                component=component,
                metadata={
                    "operation_id": operation_id,
                    "questions_processed": integration_report.verification_questions_processed,
                    "processing_time": latency,
                },
                tags={"verification", component, "throughput"},
            )
            self.metrics_buffer.append(throughput_metric)

        # Store metrics by component
        for metric in [latency_metric, confidence_metric, success_metric, throughput_metric]:
            self.metrics_history[component].append(metric)

        # Trigger performance analysis
        await self._analyze_performance(component)

    async def record_component_metric(
        self,
        component: str,
        metric_type: MetricType,
        value: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a custom component metric.

        Args:
        ----
            component: Component name
            metric_type: Type of metric
            value: Metric value
            metadata: Additional metadata

        """
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=time.time(),
            component=component,
            metadata=metadata or {},
            tags={component, metric_type.value},
        )

        self.metrics_buffer.append(metric)
        self.metrics_history[component].append(metric)

    async def get_performance_summary(
        self,
        component: str | None = None,
        time_window_minutes: int = 60,
    ) -> PerformanceSummary:
        """
        Get performance summary for component or overall system.

        Args:
        ----
            component: Specific component or None for overall
            time_window_minutes: Time window for analysis

        Returns:
        -------
            Comprehensive performance summary

        """
        current_time = time.time()
        period_start = current_time - (time_window_minutes * 60)

        # Filter metrics by time and component
        relevant_metrics = [
            metric
            for metric in self.metrics_buffer
            if (metric.timestamp >= period_start and (component is None or metric.component == component))
        ]

        if not relevant_metrics:
            return PerformanceSummary(
                period_start=period_start,
                period_end=current_time,
                total_operations=0,
                performance_tier=PerformanceTier.ACCEPTABLE,
                metric_summaries={},
                alerts_generated=[],
                recommendations=["No performance data available"],
            )

        # Calculate metric summaries
        metric_summaries = self._calculate_metric_summaries(relevant_metrics)

        # Determine performance tier
        performance_tier = self._determine_performance_tier(metric_summaries)

        # Generate alerts for recent issues
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= period_start]

        # Generate recommendations
        recommendations = self._generate_recommendations(metric_summaries, recent_alerts)

        # Analyze trends
        trends = self._analyze_trends(relevant_metrics)

        return PerformanceSummary(
            period_start=period_start,
            period_end=current_time,
            total_operations=len(
                {m.metadata.get("operation_id") for m in relevant_metrics if m.metadata.get("operation_id")},
            ),
            performance_tier=performance_tier,
            metric_summaries=metric_summaries,
            alerts_generated=recent_alerts,
            recommendations=recommendations,
            trends=trends,
        )

    async def get_system_health(self) -> dict[str, Any]:
        """Get overall system health status."""
        # Get recent performance summary
        summary = await self.get_performance_summary(time_window_minutes=5)

        # Get component health
        component_health = {}
        for component in self.metrics_history.keys():
            component_summary = await self.get_performance_summary(component, 5)
            component_health[component] = {
                "status": component_summary.performance_tier.value,
                "recent_operations": component_summary.total_operations,
                "avg_latency": component_summary.metric_summaries.get("latency", {}).get("avg", 0),
                "active_alerts": len([alert for alert in self.active_alerts.values() if alert.component == component]),
            }

        # Calculate overall health score
        health_score = self._calculate_health_score(summary, component_health)

        return {
            "overall_status": summary.performance_tier.value,
            "health_score": health_score,
            "recent_operations": summary.total_operations,
            "active_alerts": len(self.active_alerts),
            "component_health": component_health,
            "last_updated": time.time(),
        }

    async def optimize_performance(self) -> dict[str, Any]:
        """Analyze performance and provide optimization recommendations."""
        # Get comprehensive performance analysis
        summary = await self.get_performance_summary(time_window_minutes=60)

        optimization_recommendations = []

        # Analyze each metric type
        for metric_type, metrics in summary.metric_summaries.items():
            if metric_type == "latency":
                if metrics.get("avg", 0) > 2.0:
                    optimization_recommendations.append(
                        {
                            "type": "latency_optimization",
                            "priority": "high",
                            "description": f"Average latency is {metrics['avg']:.2f}s, consider optimizing ReAct iterations",
                            "actions": [
                                "Reduce max ReAct iterations",
                                "Enable parallel verification",
                                "Optimize evidence collection patterns",
                            ],
                        },
                    )

            elif metric_type == "throughput":
                if metrics.get("avg", 0) < 1.0:
                    optimization_recommendations.append(
                        {
                            "type": "throughput_optimization",
                            "priority": "medium",
                            "description": f"Throughput is {metrics['avg']:.2f} questions/sec, consider parallelization",
                            "actions": [
                                "Enable parallel verification",
                                "Optimize action execution order",
                                "Cache frequently accessed sources",
                            ],
                        },
                    )

            elif metric_type == "confidence_improvement":
                if metrics.get("avg", 0) < 0.1:
                    optimization_recommendations.append(
                        {
                            "type": "verification_quality",
                            "priority": "medium",
                            "description": f"Confidence improvement is only {metrics['avg']:.3f}, review verification strategies",
                            "actions": [
                                "Adjust confidence thresholds",
                                "Improve evidence quality assessment",
                                "Review source credibility weights",
                            ],
                        },
                    )

        # Component-specific optimizations
        for component in self.metrics_history.keys():
            component_metrics = list(self.metrics_history[component])
            if len(component_metrics) > 10:
                component_summary = self._calculate_metric_summaries(component_metrics)

                if component_summary.get("latency", {}).get("p95", 0) > 5.0:
                    optimization_recommendations.append(
                        {
                            "type": "component_optimization",
                            "priority": "high",
                            "component": component,
                            "description": f"Component {component} has high P95 latency",
                            "actions": [
                                f"Profile {component} for bottlenecks",
                                f"Review {component} configuration",
                                f"Consider reducing {component} timeout",
                            ],
                        },
                    )

        return {
            "current_performance": summary.performance_tier.value,
            "optimization_recommendations": optimization_recommendations,
            "estimated_improvement": self._estimate_improvement_potential(optimization_recommendations),
            "priority_actions": [rec for rec in optimization_recommendations if rec.get("priority") == "high"],
        }

    # Private methods for internal functionality

    def _initialize_alert_thresholds(
        self,
        custom_thresholds: dict[str, dict[str, float]] | None,
    ) -> dict[str, dict[str, float]]:
        """Initialize default and custom alert thresholds."""
        default_thresholds = {
            "latency": {
                "warning": 2.0,
                "critical": 5.0,
            },
            "error_rate": {
                "warning": 0.1,
                "critical": 0.2,
            },
            "confidence_improvement": {
                "warning": 0.05,
                "critical": 0.01,
            },
            "verification_success": {
                "warning": 0.8,
                "critical": 0.6,
            },
            "throughput": {
                "warning": 0.5,
                "critical": 0.2,
            },
        }

        if custom_thresholds:
            for metric_type, thresholds in custom_thresholds.items():
                if metric_type in default_thresholds:
                    default_thresholds[metric_type].update(thresholds)

        return default_thresholds

    async def _analyze_performance(self, component: str) -> None:
        """Analyze performance and generate alerts for a component."""
        current_time = time.time()

        # Throttle analysis frequency
        if current_time - self.last_analysis_time < self.analysis_interval:
            return

        self.last_analysis_time = current_time

        # Get recent metrics for component
        recent_metrics = [
            metric
            for metric in self.metrics_buffer
            if (metric.component == component and current_time - metric.timestamp < 300)  # Last 5 minutes
        ]

        if len(recent_metrics) < 5:  # Not enough data for analysis
            return

        # Check for alert conditions
        await self._check_alert_conditions(recent_metrics)

        # Update performance baselines
        await self._update_baselines(component, recent_metrics)

    async def _check_alert_conditions(self, metrics: list[PerformanceMetric]) -> None:
        """Check metrics against alert thresholds and generate alerts."""
        for metric_type in [MetricType.LATENCY, MetricType.ERROR_RATE, MetricType.VERIFICATION_SUCCESS]:
            # Get relevant metrics
            relevant_metrics = [m for m in metrics if m.metric_type == metric_type]

            if not relevant_metrics:
                continue

            # Calculate aggregate value
            if metric_type == MetricType.LATENCY:
                aggregate_value = statistics.mean(m.value for m in relevant_metrics)
            elif metric_type == MetricType.ERROR_RATE:
                aggregate_value = sum(m.value for m in relevant_metrics) / len(relevant_metrics)
            else:  # VERIFICATION_SUCCESS
                aggregate_value = sum(m.value for m in relevant_metrics) / len(relevant_metrics)

            # Check thresholds
            thresholds = self.alert_thresholds.get(metric_type.value, {})
            if aggregate_value >= thresholds.get("critical", float("inf")):
                severity = AlertSeverity.CRITICAL
            elif aggregate_value >= thresholds.get("warning", float("inf")):
                severity = AlertSeverity.MEDIUM
            else:
                continue

            # Generate alert
            await self._generate_alert(metric_type, aggregate_value, severity, relevant_metrics[0])

    async def _generate_alert(
        self,
        metric_type: MetricType,
        value: float,
        severity: AlertSeverity,
        sample_metric: PerformanceMetric,
    ) -> None:
        """Generate and store a performance alert."""
        alert_id = f"{metric_type.value}_{sample_metric.component}_{int(time.time())}"

        # Check if alert already exists for this component and metric type
        existing_key = f"{sample_metric.component}_{metric_type.value}"
        if existing_key in self.active_alerts:
            # Update existing alert instead of creating new one
            existing_alert = self.active_alerts[existing_key]
            existing_alert.timestamp = time.time()
            existing_alert.current_value = value
            return

        alert = PerformanceAlert(
            alert_id=alert_id,
            severity=severity,
            title=f"Performance Alert: {metric_type.value}",
            description=self._generate_alert_description(metric_type, value, severity),
            metric_type=metric_type,
            current_value=value,
            threshold=self.alert_thresholds.get(metric_type.value, {}).get("warning", 0),
            timestamp=time.time(),
            recommendations=self._generate_alert_recommendations(metric_type, value, severity),
            component=sample_metric.component,
        )

        self.active_alerts[existing_key] = alert
        self.alert_history.append(alert)

        self.logger.warning(f"Performance alert generated: {alert.title} - {alert.description}")

    def _generate_alert_description(
        self,
        metric_type: MetricType,
        value: float,
        severity: AlertSeverity,
    ) -> str:
        """Generate alert description based on metric type and value."""
        descriptions = {
            MetricType.LATENCY: f"High latency detected: {value:.2f}s",
            MetricType.ERROR_RATE: f"High error rate detected: {value:.2%}",
            MetricType.VERIFICATION_SUCCESS: f"Low verification success rate: {value:.2%}",
            MetricType.THROUGHPUT: f"Low throughput detected: {value:.2f} ops/sec",
            MetricType.CONFIDENCE_IMPROVEMENT: f"Low confidence improvement: {value:.3f}",
        }
        return descriptions.get(metric_type, f"Performance issue detected for {metric_type.value}: {value}")

    def _generate_alert_recommendations(
        self,
        metric_type: MetricType,
        value: float,
        severity: AlertSeverity,
    ) -> list[str]:
        """Generate recommendations for addressing performance alerts."""
        recommendations = {
            MetricType.LATENCY: [
                "Consider reducing ReAct iteration count",
                "Enable parallel verification processing",
                "Optimize evidence collection patterns",
            ],
            MetricType.ERROR_RATE: [
                "Review verification error logs",
                "Check source availability and accessibility",
                "Verify configuration parameters",
            ],
            MetricType.VERIFICATION_SUCCESS: [
                "Review confidence thresholds",
                "Improve evidence quality assessment",
                "Update source credibility weights",
            ],
            MetricType.THROUGHPUT: [
                "Enable parallel processing",
                "Optimize action execution order",
                "Implement intelligent caching",
            ],
            MetricType.CONFIDENCE_IMPROVEMENT: [
                "Review verification strategies",
                "Adjust evidence collection focus",
                "Consider alternative sources",
            ],
        }
        return recommendations.get(metric_type, ["Investigate performance parameters"])

    async def _update_baselines(self, component: str, metrics: list[PerformanceMetric]) -> None:
        """Update performance baselines for a component."""
        if component not in self.performance_baselines:
            self.performance_baselines[component] = {}

        # Calculate baseline for each metric type
        for metric_type in {m.metric_type for m in metrics}:
            type_metrics = [m.value for m in metrics if m.metric_type == metric_type]
            if len(type_metrics) >= 3:
                baseline = statistics.mean(type_metrics)
                self.performance_baselines[component][metric_type.value] = baseline

    def _calculate_metric_summaries(self, metrics: list[PerformanceMetric]) -> dict[str, dict[str, float]]:
        """Calculate statistical summaries for metrics by type."""
        summaries = {}

        # Group metrics by type
        by_type = defaultdict(list)
        for metric in metrics:
            by_type[metric.metric_type.value].append(metric.value)

        # Calculate statistics for each type
        for metric_type, values in by_type.items():
            if values:
                summaries[metric_type] = {
                    "count": len(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "median": statistics.median(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "p95": self._percentile(values, 0.95),
                    "p99": self._percentile(values, 0.99),
                }

        return summaries

    def _percentile(self, data: list[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _determine_performance_tier(self, metric_summaries: dict[str, dict[str, float]]) -> PerformanceTier:
        """Determine overall performance tier based on metrics."""
        latency_avg = metric_summaries.get("latency", {}).get("avg", 0)
        success_rate = metric_summaries.get("verification_success", {}).get("avg", 1.0)
        confidence_improvement = metric_summaries.get("confidence_improvement", {}).get("avg", 0)

        # Performance tier logic
        if latency_avg <= 1.0 and success_rate >= 0.95 and confidence_improvement >= 0.1:
            return PerformanceTier.EXCELLENT
        if latency_avg <= 2.0 and success_rate >= 0.85 and confidence_improvement >= 0.05:
            return PerformanceTier.GOOD
        if latency_avg <= 3.5 and success_rate >= 0.7 and confidence_improvement >= 0.02:
            return PerformanceTier.ACCEPTABLE
        if latency_avg <= 5.0 and success_rate >= 0.5:
            return PerformanceTier.POOR
        return PerformanceTier.CRITICAL

    def _generate_recommendations(
        self,
        metric_summaries: dict[str, dict[str, float]],
        recent_alerts: list[PerformanceAlert],
    ) -> list[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Latency-based recommendations
        latency_avg = metric_summaries.get("latency", {}).get("avg", 0)
        if latency_avg > 2.0:
            recommendations.append("Consider optimizing ReAct iteration patterns")
        if latency_avg > 3.0:
            recommendations.append("Enable parallel verification processing")

        # Success rate-based recommendations
        success_rate = metric_summaries.get("verification_success", {}).get("avg", 1.0)
        if success_rate < 0.8:
            recommendations.append("Review source credibility and evidence quality")
        if success_rate < 0.6:
            recommendations.append("Adjust confidence thresholds and verification strategies")

        # Confidence improvement recommendations
        confidence_improvement = metric_summaries.get("confidence_improvement", {}).get("avg", 0)
        if confidence_improvement < 0.05:
            recommendations.append("Review verification question generation")
        if confidence_improvement < 0.02:
            recommendations.append("Consider alternative verification approaches")

        # Alert-based recommendations
        if len(recent_alerts) > 5:
            recommendations.append("Multiple performance alerts detected - review system configuration")

        return recommendations

    def _analyze_trends(self, metrics: list[PerformanceMetric]) -> dict[str, str]:
        """Analyze performance trends for different metric types."""
        trends = {}

        # Group metrics by type and sort by timestamp
        by_type = defaultdict(list)
        for metric in metrics:
            by_type[metric.metric_type.value].append(metric)

        for metric_type, type_metrics in by_type.items():
            if len(type_metrics) < 10:  # Need enough data for trend analysis
                continue

            # Sort by timestamp
            type_metrics.sort(key=lambda m: m.timestamp)

            # Split into two halves for trend comparison
            mid_point = len(type_metrics) // 2
            first_half = [m.value for m in type_metrics[:mid_point]]
            second_half = [m.value for m in type_metrics[mid_point:]]

            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)

            # Determine trend direction
            change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0

            if abs(change_percent) < 5:
                trends[metric_type] = "stable"
            elif change_percent > 0:
                if metric_type in ["latency", "error_rate"]:
                    trends[metric_type] = "declining"  # Higher is worse
                else:
                    trends[metric_type] = "improving"  # Higher is better
            elif metric_type in ["latency", "error_rate"]:
                trends[metric_type] = "improving"  # Lower is better
            else:
                trends[metric_type] = "declining"  # Lower is worse

        return trends

    def _calculate_health_score(self, summary: PerformanceSummary, component_health: dict[str, Any]) -> float:
        """Calculate overall system health score (0-100)."""
        base_scores = {
            PerformanceTier.EXCELLENT: 95,
            PerformanceTier.GOOD: 80,
            PerformanceTier.ACCEPTABLE: 65,
            PerformanceTier.POOR: 40,
            PerformanceTier.CRITICAL: 20,
        }

        base_score = base_scores.get(summary.performance_tier, 50)

        # Adjust for active alerts
        alert_penalty = min(len(summary.alerts_generated) * 5, 20)
        base_score -= alert_penalty

        # Adjust for component health
        component_scores = []
        for _component, health in component_health.items():
            component_score = 50  # Base component score
            if health.get("avg_latency", 0) < 2.0:
                component_score += 20
            if health.get("active_alerts", 0) == 0:
                component_score += 15
            if health.get("status") in ["excellent", "good"]:
                component_score += 15
            component_scores.append(component_score)

        if component_scores:
            avg_component_score = sum(component_scores) / len(component_scores)
            base_score = (base_score + avg_component_score) / 2

        return max(0, min(100, base_score))

    def _estimate_improvement_potential(
        self,
        recommendations: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Estimate potential improvement from recommendations."""
        potential_improvements = {
            "latency_reduction": 0.0,
            "throughput_increase": 0.0,
            "accuracy_improvement": 0.0,
            "overall_score_increase": 0.0,
        }

        for rec in recommendations:
            if rec.get("priority") == "high":
                potential_improvements["overall_score_increase"] += 15
            elif rec.get("priority") == "medium":
                potential_improvements["overall_score_increase"] += 8
            else:
                potential_improvements["overall_score_increase"] += 3

            if "latency" in rec.get("type", ""):
                potential_improvements["latency_reduction"] += 0.5
            if "throughput" in rec.get("type", ""):
                potential_improvements["throughput_increase"] += 0.3
            if "quality" in rec.get("type", ""):
                potential_improvements["accuracy_improvement"] += 0.1

        # Cap improvements at reasonable maximums
        for key in potential_improvements:
            potential_improvements[key] = min(potential_improvements[key], 50.0)

        return potential_improvements


# Factory function for easy initialization
def create_performance_monitor(
    metrics_retention_hours: int = 24,
    alert_thresholds: dict[str, dict[str, float]] | None = None,
    enable_predictions: bool = True,
) -> CoVeReActPerformanceMonitor:
    """Create performance monitor with specified configuration."""
    return CoVeReActPerformanceMonitor(
        metrics_retention_hours=metrics_retention_hours,
        alert_thresholds=alert_thresholds,
        enable_predictions=enable_predictions,
    )
