from __future__ import annotations

from collections import Counter, defaultdict
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import timedelta
from pathlib import Path
from typing import Any
import logging
import math
import os
import re
import statistics
import sys

from ...domain_models.chat_models import (
from ..interfaces.chat_interfaces import ITemporalAnalyzer

#!/usr/bin/env python3
"""Temporal Intelligence Layer for CHS
Multi-scale temporal analysis with pattern detection and trend prediction.
"""


# Add CSF NIP paths

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)

    ChatMessage,
    ConversationPattern,
    TemporalMetrics,
    TemporalScale,
)


@dataclass
class TemporalWindow:
    """Temporal window for analysis."""

    start_time: datetime
    end_time: datetime
    scale: TemporalScale
    bucket_count: int = 0

    def contains(self, timestamp: int) -> bool:
        """Check if timestamp is within window."""
        dt = datetime.fromtimestamp(timestamp / 1000)
        return self.start_time <= dt <= self.end_time

    def get_bucket_key(self, timestamp: int) -> str:
        """Get bucket key for timestamp."""
        dt = datetime.fromtimestamp(timestamp / 1000)

        if self.scale == TemporalScale.HOURLY:
            return dt.strftime("%Y-%m-%d %H:00")
        if self.scale == TemporalScale.DAILY:
            return dt.strftime("%Y-%m-%d")
        if self.scale == TemporalScale.WEEKLY:
            return dt.strftime("%Y-W%U")
        if self.scale == TemporalScale.MONTHLY:
            return dt.strftime("%Y-%m")
        if self.scale == TemporalScale.QUARTERLY:
            year = dt.year
            quarter = (dt.month - 1) // 3 + 1
            return f"{year}-Q{quarter}"
        return dt.strftime("%Y-%m-%d")


class TemporalIntensityCalculator:
    """Calculate conversation intensity metrics."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def calculate_message_intensity(self, message: ChatMessage) -> float:
        """Calculate intensity score for a single message."""
        intensity = 0.0

        # Base intensity from message length
        length_score = min(len(message.content) / 500, 1.0)  # Normalize to 0-1
        intensity += length_score * 0.3

        # Code content boosts intensity
        code_indicators = [
            "```",
            "python",
            "def ",
            "class ",
            "import ",
            "function",
            "script",
        ]
        code_score = sum(
            1 for indicator in code_indicators if indicator in message.content.lower()
        )
        intensity += min(code_score / len(code_indicators), 1.0) * 0.4

        # Question marks indicate engagement
        question_score = message.content.count("?") / 10  # Normalize
        intensity += min(question_score, 0.3)

        # Exclamation marks indicate urgency/emphasis
        exclamation_score = message.content.count("!") / 5  # Normalize
        intensity += min(exclamation_score, 0.2)

        # Technical terms boost intensity
        tech_terms = [
            "error",
            "fix",
            "bug",
            "issue",
            "problem",
            "solution",
            "debug",
            "optimize",
        ]
        tech_score = sum(1 for term in tech_terms if term in message.content.lower())
        intensity += min(tech_score / len(tech_terms), 1.0) * 0.3

        return min(intensity, 1.0)

    def calculate_conversation_intensity(self, messages: list[ChatMessage]) -> float:
        """Calculate overall conversation intensity."""
        if not messages:
            return 0.0

        intensities = [self.calculate_message_intensity(msg) for msg in messages]
        return statistics.mean(intensities)

    def calculate_engagement_score(
        self, messages: list[ChatMessage], time_window_hours: int = 1
    ) -> float:
        """Calculate engagement score based on message frequency and responsiveness."""
        if len(messages) < 2:
            return 0.0

        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)

        # Calculate response times
        response_times = []
        for i in range(1, len(sorted_messages)):
            time_diff = (
                (sorted_messages[i].timestamp - sorted_messages[i - 1].timestamp)
                / 1000
                / 3600
            )  # hours
            if time_diff <= time_window_hours:
                response_times.append(time_diff)

        if not response_times:
            return 0.0

        # Faster responses = higher engagement
        avg_response_time = statistics.mean(response_times)
        responsiveness_score = max(0, 1 - (avg_response_time / time_window_hours))

        # Message frequency score
        time_span = (
            (sorted_messages[-1].timestamp - sorted_messages[0].timestamp) / 1000 / 3600
        )  # hours
        frequency_score = (
            min(len(messages) / max(time_span, 1), 10) / 10
        )  # Normalize to 0-1

        return (responsiveness_score + frequency_score) / 2


class TrendAnalyzer:
    """Analyze trends in temporal data."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def calculate_linear_trend(self, values: list[float]) -> tuple[float, float, float]:
        """Calculate linear trend (slope, correlation, significance)."""
        if len(values) < 2:
            return 0.0, 0.0, 0.0

        x = list(range(len(values)))
        y = values

        # Calculate linear regression
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))

        # Calculate slope
        slope = (
            (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            if (n * sum_x2 - sum_x**2) != 0
            else 0.0
        )

        # Calculate correlation coefficient
        try:
            correlation = (n * sum_xy - sum_x * sum_y) / math.sqrt(
                (n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)
            )
        except:
            correlation = 0.0

        # Calculate significance (simplified)
        significance = (
            abs(correlation) * math.sqrt(n - 2) / math.sqrt(1 - correlation**2)
            if abs(correlation) < 1
            else 0.0
        )

        return slope, correlation, significance

    def detect_seasonality(
        self, values: list[float], period: int = 7
    ) -> dict[str, Any]:
        """Detect seasonal patterns in data."""
        if len(values) < period * 2:
            return {"detected": False, "strength": 0.0, "pattern": []}

        # Calculate seasonal decomposition
        seasons = []
        for i in range(period):
            seasonal_values = [values[j] for j in range(i, len(values), period)]
            if seasonal_values:
                seasons.append(statistics.mean(seasonal_values))

        # Calculate seasonal strength
        statistics.mean(values)
        seasonal_variance = statistics.variance(seasons) if len(seasons) > 1 else 0
        total_variance = statistics.variance(values)
        seasonal_strength = (
            seasonal_variance / total_variance if total_variance > 0 else 0
        )

        return {
            "detected": seasonal_strength > 0.1,
            "strength": seasonal_strength,
            "pattern": seasons,
            "period": period,
        }

    def identify_change_points(
        self, values: list[float], threshold: float = 0.3
    ) -> list[int]:
        """Identify significant change points in time series."""
        if len(values) < 3:
            return []

        change_points = []

        # Calculate moving average
        window_size = max(3, len(values) // 10)
        moving_avg = []
        for i in range(len(values)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(values), i + window_size // 2 + 1)
            moving_avg.append(statistics.mean(values[start_idx:end_idx]))

        # Find significant deviations from trend
        for i in range(1, len(moving_avg) - 1):
            prev_trend = moving_avg[i] - moving_avg[i - 1]
            next_trend = moving_avg[i + 1] - moving_avg[i]

            # Change point if trend direction changes significantly
            if abs(prev_trend - next_trend) > threshold * (
                max(moving_avg) - min(moving_avg)
            ):
                change_points.append(i)

        return change_points


class ActivityPredictor:
    """Predict future activity patterns."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def linear_predict(
        self, historical_data: list[TemporalMetrics], periods: int = 7
    ) -> list[TemporalMetrics]:
        """Predict future activity using linear regression."""
        if not historical_data:
            return []

        # Extract message counts for prediction
        counts = [metric.message_count for metric in historical_data]

        # Calculate trend
        slope, correlation, _ = TrendAnalyzer().calculate_linear_trend(counts)

        # Generate predictions
        predictions = []
        last_metric = historical_data[-1]

        for i in range(1, periods + 1):
            predicted_count = max(0, counts[-1] + slope * i)

            # Create prediction metric
            prediction = TemporalMetrics(
                time_bucket=self._get_next_bucket(
                    last_metric.time_bucket, last_metric.scale, i
                ),
                scale=last_metric.scale,
                message_count=int(predicted_count),
                intensity_average=last_metric.intensity_average,  # Assume similar intensity
                intensity_peak=last_metric.intensity_peak,
                topic_distribution=last_metric.topic_distribution.copy(),
                context_distribution=last_metric.context_distribution.copy(),
                unique_topics=last_metric.unique_topics,
                engagement_score=last_metric.engagement_score,
                trend_slope=slope,
                trend_significance=abs(correlation),
                seasonality_detected=False,
            )
            predictions.append(prediction)

        return predictions

    def seasonal_predict(
        self, historical_data: list[TemporalMetrics], periods: int = 7
    ) -> list[TemporalMetrics]:
        """Predict future activity using seasonal patterns."""
        if len(historical_data) < 14:  # Need at least 2 cycles
            return self.linear_predict(historical_data, periods)

        # Detect seasonal patterns
        counts = [metric.message_count for metric in historical_data]
        seasonality = TrendAnalyzer().detect_seasonality(counts, period=7)

        if not seasonality["detected"]:
            return self.linear_predict(historical_data, periods)

        # Use seasonal pattern for prediction
        predictions = []
        pattern = seasonality["pattern"]
        last_metric = historical_data[-1]

        for i in range(periods):
            # Use seasonal pattern value
            pattern_index = i % len(pattern)
            seasonal_multiplier = pattern[pattern_index] / statistics.mean(pattern)
            base_count = statistics.mean(counts[-7:])  # Use recent week as base
            predicted_count = max(0, int(base_count * seasonal_multiplier))

            prediction = TemporalMetrics(
                time_bucket=self._get_next_bucket(
                    last_metric.time_bucket, last_metric.scale, i
                ),
                scale=last_metric.scale,
                message_count=predicted_count,
                intensity_average=last_metric.intensity_average,
                intensity_peak=last_metric.intensity_peak,
                topic_distribution=last_metric.topic_distribution.copy(),
                context_distribution=last_metric.context_distribution.copy(),
                unique_topics=last_metric.unique_topics,
                engagement_score=last_metric.engagement_score,
                trend_slope=0.0,
                trend_significance=0.0,
                seasonality_detected=True,
            )
            predictions.append(prediction)

        return predictions

    def _get_next_bucket(
        self, current_bucket: str, scale: TemporalScale, offset: int
    ) -> str:
        """Get next time bucket."""
        current_dt = datetime.strptime(
            current_bucket, "%Y-%m-%d" if scale == TemporalScale.DAILY else "%Y-%m"
        )

        if scale == TemporalScale.DAILY:
            next_dt = current_dt + timedelta(days=offset)
            return next_dt.strftime("%Y-%m-%d")
        if scale == TemporalScale.WEEKLY:
            next_dt = current_dt + timedelta(weeks=offset)
            return next_dt.strftime("%Y-W%U")
        if scale == TemporalScale.MONTHLY:
            # Handle month overflow
            year = current_dt.year
            month = current_dt.month + offset
            while month > 12:
                month -= 12
                year += 1
            return f"{year}-{month:02d}"
        return current_bucket


class EnhancedTemporalAnalyzer(ITemporalAnalyzer):
    """Enhanced temporal analyzer with multi-scale analysis capabilities."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.intensity_calculator = TemporalIntensityCalculator()
        self.trend_analyzer = TrendAnalyzer()
        self.activity_predictor = ActivityPredictor()

    def analyze_conversation_intensity(
        self,
        messages: list[ChatMessage],
        scale: TemporalScale = TemporalScale.DAILY,
    ) -> list[TemporalMetrics]:
        """Analyze conversation intensity over time."""
        if not messages:
            return []

        # Group messages by time buckets
        buckets = self._group_messages_by_time(messages, scale)

        metrics = []
        for bucket_key, bucket_messages in buckets.items():
            # Calculate intensity metrics
            intensities = [
                self.intensity_calculator.calculate_message_intensity(msg)
                for msg in bucket_messages
            ]
            avg_intensity = statistics.mean(intensities) if intensities else 0.0
            peak_intensity = max(intensities) if intensities else 0.0

            # Calculate topic distribution
            topic_distribution = self._calculate_topic_distribution(bucket_messages)

            # Calculate context distribution
            context_distribution = self._calculate_context_distribution(bucket_messages)

            # Calculate unique topics
            unique_topics = len(
                {topic for msg in bucket_messages for topic in msg.semantic_tags}
            )

            # Calculate engagement score
            engagement_score = self.intensity_calculator.calculate_engagement_score(
                bucket_messages
            )

            # Create temporal metric
            metric = TemporalMetrics(
                time_bucket=bucket_key,
                scale=scale,
                message_count=len(bucket_messages),
                intensity_average=avg_intensity,
                intensity_peak=peak_intensity,
                topic_distribution=topic_distribution,
                context_distribution=context_distribution,
                unique_topics=unique_topics,
                engagement_score=engagement_score,
            )

            metrics.append(metric)

        # Sort by time bucket
        metrics.sort(key=lambda m: m.time_bucket)

        # Calculate trend information
        if len(metrics) > 1:
            message_counts = [m.message_count for m in metrics]
            slope, _correlation, significance = (
                self.trend_analyzer.calculate_linear_trend(message_counts)
            )

            for _i, metric in enumerate(metrics):
                metric.trend_slope = slope
                metric.trend_significance = significance
                metric.seasonality_detected = len(metrics) >= 7  # Basic heuristic

        self.logger.info(f"Analyzed intensity for {len(metrics)} {scale.value} buckets")
        return metrics

    def detect_temporal_patterns(
        self, metrics: list[TemporalMetrics]
    ) -> list[ConversationPattern]:
        """Detect patterns in temporal data."""
        patterns = []

        if len(metrics) < 3:
            return patterns

        # Detect intensity patterns
        intensity_patterns = self._detect_intensity_patterns(metrics)
        patterns.extend(intensity_patterns)

        # Detect frequency patterns
        frequency_patterns = self._detect_frequency_patterns(metrics)
        patterns.extend(frequency_patterns)

        # Detect topic patterns
        topic_patterns = self._detect_topic_patterns(metrics)
        patterns.extend(topic_patterns)

        # Detect temporal anomalies
        anomaly_patterns = self._detect_anomaly_patterns(metrics)
        patterns.extend(anomaly_patterns)

        self.logger.info(f"Detected {len(patterns)} temporal patterns")
        return patterns

    def calculate_trends(self, metrics: list[TemporalMetrics]) -> dict[str, float]:
        """Calculate trend metrics."""
        if len(metrics) < 2:
            return {}

        trends = {}

        # Message count trend
        counts = [m.message_count for m in metrics]
        slope, correlation, significance = self.trend_analyzer.calculate_linear_trend(
            counts
        )
        trends["message_count_slope"] = slope
        trends["message_count_correlation"] = correlation
        trends["message_count_significance"] = significance

        # Intensity trend
        intensities = [m.intensity_average for m in metrics]
        slope, correlation, significance = self.trend_analyzer.calculate_linear_trend(
            intensities
        )
        trends["intensity_slope"] = slope
        trends["intensity_correlation"] = correlation
        trends["intensity_significance"] = significance

        # Engagement trend
        engagements = [m.engagement_score for m in metrics]
        slope, correlation, significance = self.trend_analyzer.calculate_linear_trend(
            engagements
        )
        trends["engagement_slope"] = slope
        trends["engagement_correlation"] = correlation
        trends["engagement_significance"] = significance

        # Topic diversity trend
        topic_counts = [m.unique_topics for m in metrics]
        slope, correlation, significance = self.trend_analyzer.calculate_linear_trend(
            topic_counts
        )
        trends["topic_diversity_slope"] = slope
        trends["topic_diversity_correlation"] = correlation
        trends["topic_diversity_significance"] = significance

        return trends

    def identify_anomalies(
        self, metrics: list[TemporalMetrics]
    ) -> list[dict[str, Any]]:
        """Identify temporal anomalies."""
        anomalies = []

        if len(metrics) < 5:
            return anomalies

        # Statistical anomaly detection
        message_counts = [m.message_count for m in metrics]
        mean_count = statistics.mean(message_counts)
        std_count = statistics.stdev(message_counts) if len(message_counts) > 1 else 0

        for metric in metrics:
            # Z-score based anomaly detection
            if std_count > 0:
                z_score = abs((metric.message_count - mean_count) / std_count)
                if z_score > 2.0:  # 2 standard deviations
                    anomalies.append(
                        {
                            "type": "statistical",
                            "time_bucket": metric.time_bucket,
                            "metric": "message_count",
                            "value": metric.message_count,
                            "expected": mean_count,
                            "z_score": z_score,
                            "severity": "high" if z_score > 3.0 else "medium",
                        },
                    )

        # Trend-based anomaly detection
        change_points = self.trend_analyzer.identify_change_points(message_counts)
        for cp_index in change_points:
            if cp_index < len(metrics):
                metric = metrics[cp_index]
                anomalies.append(
                    {
                        "type": "trend_change",
                        "time_bucket": metric.time_bucket,
                        "metric": "trend",
                        "value": metric.message_count,
                        "change_point_index": cp_index,
                        "severity": "medium",
                    },
                )

        # Intensity anomaly detection
        intensities = [m.intensity_average for m in metrics]
        mean_intensity = statistics.mean(intensities)
        std_intensity = statistics.stdev(intensities) if len(intensities) > 1 else 0

        for metric in metrics:
            if std_intensity > 0 and metric.intensity_average > 0:
                z_score = (metric.intensity_average - mean_intensity) / std_intensity
                if z_score > 2.0:
                    anomalies.append(
                        {
                            "type": "intensity",
                            "time_bucket": metric.time_bucket,
                            "metric": "intensity_average",
                            "value": metric.intensity_average,
                            "expected": mean_intensity,
                            "z_score": z_score,
                            "severity": "high" if z_score > 3.0 else "medium",
                        },
                    )

        self.logger.info(f"Identified {len(anomalies)} temporal anomalies")
        return anomalies

    def predict_activity(
        self,
        historical_data: list[TemporalMetrics],
        prediction_periods: int = 7,
    ) -> list[TemporalMetrics]:
        """Predict future activity patterns."""
        if not historical_data:
            return []

        # Choose prediction method based on data characteristics
        if len(historical_data) >= 14:
            # Use seasonal prediction for sufficient data
            predictions = self.activity_predictor.seasonal_predict(
                historical_data, prediction_periods
            )
        else:
            # Use linear prediction for limited data
            predictions = self.activity_predictor.linear_predict(
                historical_data, prediction_periods
            )

        self.logger.info(f"Generated {len(predictions)} activity predictions")
        return predictions

    def _group_messages_by_time(
        self,
        messages: list[ChatMessage],
        scale: TemporalScale,
    ) -> dict[str, list[ChatMessage]]:
        """Group messages by time buckets."""
        buckets = defaultdict(list)

        for message in messages:
            bucket_key = self._get_time_bucket(message.timestamp, scale)
            buckets[bucket_key].append(message)

        return dict(buckets)

    def _get_time_bucket(self, timestamp: int, scale: TemporalScale) -> str:
        """Get time bucket for timestamp."""
        dt = datetime.fromtimestamp(timestamp / 1000)

        if scale == TemporalScale.HOURLY:
            return dt.strftime("%Y-%m-%d %H:00")
        if scale == TemporalScale.DAILY:
            return dt.strftime("%Y-%m-%d")
        if scale == TemporalScale.WEEKLY:
            return dt.strftime("%Y-W%U")
        if scale == TemporalScale.MONTHLY:
            return dt.strftime("%Y-%m")
        if scale == TemporalScale.QUARTERLY:
            year = dt.year
            quarter = (dt.month - 1) // 3 + 1
            return f"{year}-Q{quarter}"
        return dt.strftime("%Y-%m-%d")

    def _calculate_topic_distribution(
        self, messages: list[ChatMessage]
    ) -> dict[str, float]:
        """Calculate topic distribution for messages."""
        topic_counts = Counter()

        for message in messages:
            for tag in message.semantic_tags:
                topic_counts[tag] += 1

        total_topics = sum(topic_counts.values())
        if total_topics == 0:
            return {}

        return {topic: count / total_topics for topic, count in topic_counts.items()}

    def _calculate_context_distribution(
        self, messages: list[ChatMessage]
    ) -> dict[str, int]:
        """Calculate context distribution for messages."""
        context_counts = Counter()

        for message in messages:
            context_counts[message.context.value] += 1

        return dict(context_counts)

    def _detect_intensity_patterns(
        self, metrics: list[TemporalMetrics]
    ) -> list[ConversationPattern]:
        """Detect patterns in conversation intensity."""
        patterns = []

        # High intensity periods
        high_intensity_threshold = statistics.mean(
            [m.intensity_average for m in metrics]
        ) + statistics.stdev(
            [m.intensity_average for m in metrics],
        )

        high_periods = [
            m for m in metrics if m.intensity_average > high_intensity_threshold
        ]
        if high_periods:
            pattern = ConversationPattern(
                pattern_type="high_intensity",
                description=f"Periods with high conversation intensity (> {high_intensity_threshold:.2f})",
                frequency=len(high_periods),
                confidence=0.8,
                time_span_days=7,  # Placeholder
                sample_messages=[m.time_bucket for m in high_periods[:3]],
                temporal_distribution={
                    m.time_bucket: m.intensity_average for m in high_periods
                },
            )
            patterns.append(pattern)

        return patterns

    def _detect_frequency_patterns(
        self, metrics: list[TemporalMetrics]
    ) -> list[ConversationPattern]:
        """Detect patterns in message frequency."""
        patterns = []

        # Peak activity periods
        message_counts = [m.message_count for m in metrics]
        if message_counts:
            threshold = statistics.mean(message_counts) + statistics.stdev(
                message_counts
            )

            peak_periods = [m for m in metrics if m.message_count > threshold]
            if peak_periods:
                pattern = ConversationPattern(
                    pattern_type="high_frequency",
                    description=f"Periods with high message frequency (> {threshold:.1f} messages)",
                    frequency=len(peak_periods),
                    confidence=0.7,
                    time_span_days=7,
                    sample_messages=[m.time_bucket for m in peak_periods[:3]],
                    temporal_distribution={
                        m.time_bucket: m.message_count for m in peak_periods
                    },
                )
                patterns.append(pattern)

        return patterns

    def _detect_topic_patterns(
        self, metrics: list[TemporalMetrics]
    ) -> list[ConversationPattern]:
        """Detect patterns in topic evolution."""
        patterns = []

        # Collect all topics
        all_topics = set()
        for metric in metrics:
            all_topics.update(metric.topic_distribution.keys())

        # Find trending topics
        for topic in list(all_topics)[:5]:  # Limit to top 5 topics
            topic_values = [
                metric.topic_distribution.get(topic, 0) for metric in metrics
            ]
            slope, correlation, _significance = (
                self.trend_analyzer.calculate_linear_trend(topic_values)
            )

            if abs(slope) > 0.01 and abs(correlation) > 0.5:  # Significant trend
                trend_direction = "increasing" if slope > 0 else "decreasing"
                pattern = ConversationPattern(
                    pattern_type="topic_trend",
                    description=f"Topic '{topic}' shows {trend_direction} trend",
                    frequency=sum(1 for v in topic_values if v > 0),
                    confidence=abs(correlation),
                    time_span_days=len(metrics),
                    sample_messages=[
                        f"{topic}: {value:.3f}"
                        for metric, value in zip(metrics, topic_values, strict=False)
                        if value > 0
                    ][:3],
                    trend_direction=trend_direction,
                )
                patterns.append(pattern)

        return patterns

    def _detect_anomaly_patterns(
        self, metrics: list[TemporalMetrics]
    ) -> list[ConversationPattern]:
        """Detect patterns related to anomalies."""
        patterns = []

        anomalies = self.identify_anomalies(metrics)
        if anomalies:
            anomaly_types = Counter([a["type"] for a in anomalies])

            for anomaly_type, count in anomaly_types.items():
                pattern = ConversationPattern(
                    pattern_type="anomaly_pattern",
                    description=f"Recurring {anomaly_type} anomalies detected",
                    frequency=count,
                    confidence=0.9,
                    time_span_days=len(metrics),
                    sample_messages=[
                        f"{a['type']}: {a['time_bucket']}"
                        for a in anomalies
                        if a["type"] == anomaly_type
                    ][:3],
                )
                patterns.append(pattern)

        return patterns
