#!/usr/bin/env python3
"""
Workflow Optimization Analytics Dashboard
Comprehensive analytics and reporting for chat search workflow optimization.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context_aware_session import ContextAwareSessionManager
from enhanced_cache_manager import EnhancedCacheManager

# Import our optimization components
from query_pattern_recognition import QueryPatternRecognizer
from session_duration_monitor import SessionDurationMonitor


@dataclass
class OptimizationMetric:
    """Individual optimization metric"""
    metric_name: str
    current_value: float
    target_value: float
    unit: str
    improvement_trend: str  # "improving", "stable", "declining"
    impact_level: str  # "high", "medium", "low"
    recommendations: list[str]


@dataclass
class WorkflowInsight:
    """Insight about workflow optimization"""
    insight_id: str
    category: str  # "efficiency", "quality", "performance", "user_experience"
    title: str
    description: str
    impact_score: float
    effort_required: str  # "low", "medium", "high"
    recommendations: list[str]
    metrics_affected: list[str]


class WorkflowOptimizationAnalytics:
    """Comprehensive analytics for workflow optimization"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize optimization components
        self.pattern_recognizer = QueryPatternRecognizer(cache_dir)
        self.session_monitor = SessionDurationMonitor(cache_dir)
        self.cache_manager = EnhancedCacheManager(cache_dir)
        self.context_manager = ContextAwareSessionManager(cache_dir)

        # Analytics data
        self.analytics_file = self.cache_dir / "workflow_analytics.json"
        self.insights_file = self.cache_dir / "workflow_insights.json"

        # Configuration
        self.config = {
            "analysis_period_days": 7,
            "trend_analysis_periods": [1, 7, 30],  # days
            "insight_generation_interval_hours": 6,
            "metric_weighting": {
                "session_duration": 0.3,
                "query_efficiency": 0.25,
                "cache_performance": 0.2,
                "success_rate": 0.15,
                "user_satisfaction": 0.1
            }
        }

        self.logger = logging.getLogger(__name__)
        self._load_analytics_data()

    def generate_comprehensive_report(self) -> dict[str, Any]:
        """Generate comprehensive workflow optimization report"""
        current_time = time.time()

        # Collect data from all components
        pattern_stats = self.pattern_recognizer.get_statistics()
        session_stats = self.session_monitor.get_session_statistics(self.config["analysis_period_days"])
        cache_stats = self.cache_manager.get_comprehensive_stats()
        context_stats = self.context_manager.get_context_statistics()
        preload_stats = self.cache_manager.get_preload_statistics()

        # Calculate optimization metrics
        optimization_metrics = self._calculate_optimization_metrics(
            pattern_stats, session_stats, cache_stats, context_stats, preload_stats
        )

        # Generate insights
        insights = self._generate_workflow_insights(optimization_metrics)

        # Calculate overall optimization score
        overall_score = self._calculate_overall_score(optimization_metrics)

        # Identify quick wins and high-impact opportunities
        quick_wins = self._identify_quick_wins(insights, optimization_metrics)
        high_impact = self._identify_high_impact_opportunities(insights, optimization_metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            optimization_metrics, insights, quick_wins, high_impact
        )

        report = {
            "report_metadata": {
                "generated_at": current_time,
                "analysis_period_days": self.config["analysis_period_days"],
                "data_points_analyzed": self._get_total_data_points(),
                "report_version": "1.0"
            },
            "executive_summary": {
                "overall_optimization_score": overall_score,
                "key_findings": self._generate_key_findings(optimization_metrics),
                "status": "healthy" if overall_score > 75 else "needs_attention" if overall_score > 50 else "critical"
            },
            "optimization_metrics": optimization_metrics,
            "component_statistics": {
                "pattern_recognition": pattern_stats,
                "session_monitoring": session_stats,
                "cache_performance": cache_stats,
                "context_management": context_stats,
                "predictive_preloading": preload_stats
            },
            "insights": [asdict(insight) for insight in insights],
            "opportunities": {
                "quick_wins": quick_wins,
                "high_impact": high_impact
            },
            "recommendations": recommendations,
            "trend_analysis": self._analyze_trends(),
            "roi_analysis": self._calculate_roi_analysis(optimization_metrics)
        }

        # Save report
        self._save_analytics_data(report)

        return report

    def _calculate_optimization_metrics(self, pattern_stats: dict, session_stats: dict,
                                     cache_stats: dict, context_stats: dict,
                                     preload_stats: dict) -> list[OptimizationMetric]:
        """Calculate comprehensive optimization metrics"""
        metrics = []

        # Session Duration Metric
        if "duration_stats" in session_stats:
            avg_duration = session_stats["duration_stats"]["average"]
            target_duration = 180  # 3 minutes target
            improvement = self._calculate_improvement_trend(session_stats, "duration")

            metrics.append(OptimizationMetric(
                metric_name="average_session_duration",
                current_value=avg_duration,
                target_value=target_duration,
                unit="seconds",
                improvement_trend=improvement,
                impact_level="high" if avg_duration > 300 else "medium",
                recommendations=self._get_duration_recommendations(avg_duration)
            ))

        # Query Efficiency Metric
        if pattern_stats.get("total_queries", 0) > 0:
            pattern_hit_rate = pattern_stats.get("pattern_hit_rate", 0)
            target_pattern_rate = 0.8  # 80% target

            metrics.append(OptimizationMetric(
                metric_name="query_pattern_efficiency",
                current_value=pattern_hit_rate,
                target_value=target_pattern_rate,
                unit="percentage",
                improvement_trend="stable",
                impact_level="medium",
                recommendations=self._get_pattern_recommendations(pattern_hit_rate)
            ))

        # Cache Performance Metric
        overall_hit_rate = cache_stats.get("hit_rates", {}).get("overall", 0)
        target_hit_rate = 0.6  # 60% target

        metrics.append(OptimizationMetric(
            metric_name="cache_hit_rate",
            current_value=overall_hit_rate,
            target_value=target_hit_rate,
            unit="percentage",
            improvement_trend="improving" if overall_hit_rate > 0.5 else "stable",
            impact_level="medium",
            recommendations=self._get_cache_recommendations(overall_hit_rate)
        ))

        # Success Rate Metric
        if "optimization_stats" in session_stats:
            quality_dist = session_stats["optimization_stats"]["quality_distribution"]
            total_sessions = sum(quality_dist.values())
            successful_sessions = quality_dist.get("excellent", 0) + quality_dist.get("good", 0)
            success_rate = successful_sessions / max(total_sessions, 1)
            target_success_rate = 0.85  # 85% target

            metrics.append(OptimizationMetric(
                metric_name="session_success_rate",
                current_value=success_rate,
                target_value=target_success_rate,
                unit="percentage",
                improvement_trend="stable",
                impact_level="high",
                recommendations=self._get_success_rate_recommendations(success_rate)
            ))

        # Preloading Effectiveness Metric
        if preload_stats.get("preload_enabled", False):
            high_score_patterns = preload_stats["pattern_statistics"]["high_score_patterns"]
            total_patterns = preload_stats["pattern_statistics"]["total_patterns"]
            preload_effectiveness = high_score_patterns / max(total_patterns, 1)
            target_preload_rate = 0.3  # 30% target

            metrics.append(OptimizationMetric(
                metric_name="predictive_preloading_effectiveness",
                current_value=preload_effectiveness,
                target_value=target_preload_rate,
                unit="percentage",
                improvement_trend="improving" if preload_effectiveness > 0.2 else "stable",
                impact_level="low",
                recommendations=self._get_preload_recommendations(preload_effectiveness)
            ))

        return metrics

    def _calculate_improvement_trend(self, stats: dict, metric_type: str) -> str:
        """Calculate improvement trend for a metric"""
        # This is a simplified implementation
        # In practice, you'd compare current values with historical data

        if metric_type == "duration":
            avg_duration = stats.get("duration_stats", {}).get("average", 0)
            if avg_duration < 180:
                return "improving"
            elif avg_duration < 300:
                return "stable"
            else:
                return "declining"

        return "stable"

    def _generate_workflow_insights(self, metrics: list[OptimizationMetric]) -> list[WorkflowInsight]:
        """Generate insights about workflow optimization"""
        insights = []

        # Analyze session duration patterns
        duration_metric = next((m for m in metrics if m.metric_name == "average_session_duration"), None)
        if duration_metric and duration_metric.current_value > 300:  # 5 minutes
            insights.append(WorkflowInsight(
                insight_id=f"long_sessions_{int(time.time())}",
                category="efficiency",
                title="Excessive Session Durations Detected",
                description=f"Average session duration is {duration_metric.current_value:.1f}s, significantly above the target of {duration_metric.target_value}s",
                impact_score=min(10, (duration_metric.current_value - duration_metric.target_value) / 60),
                effort_required="medium",
                recommendations=[
                    "Implement session duration alerts",
                    "Add query efficiency suggestions",
                    "Consider breaking complex tasks into multiple sessions"
                ],
                metrics_affected=["average_session_duration", "user_satisfaction"]
            ))

        # Analyze cache performance
        cache_metric = next((m for m in metrics if m.metric_name == "cache_hit_rate"), None)
        if cache_metric and cache_metric.current_value < 0.3:  # 30%
            insights.append(WorkflowInsight(
                insight_id=f"low_cache_hit_{int(time.time())}",
                category="performance",
                title="Low Cache Hit Rate Impacting Performance",
                description=f"Cache hit rate is {cache_metric.current_value:.1%}, below the target of {cache_metric.target_value:.1%}",
                impact_score=8,
                effort_required="low",
                recommendations=[
                    "Review cache configuration",
                    "Implement query normalization",
                    "Enable predictive preloading"
                ],
                metrics_affected=["cache_hit_rate", "query_response_time"]
            ))

        # Analyze pattern recognition effectiveness
        pattern_metric = next((m for m in metrics if m.metric_name == "query_pattern_efficiency"), None)
        if pattern_metric and pattern_metric.current_value < 0.5:  # 50%
            insights.append(WorkflowInsight(
                insight_id=f"poor_pattern_recognition_{int(time.time())}",
                category="user_experience",
                title="Low Query Pattern Recognition Efficiency",
                description=f"Only {pattern_metric.current_value:.1%} of queries match known patterns",
                impact_score=6,
                effort_required="medium",
                recommendations=[
                    "Improve query normalization",
                    "Expand pattern training data",
                    "Implement machine learning-based pattern recognition"
                ],
                metrics_affected=["query_pattern_efficiency", "user_satisfaction"]
            ))

        # Add positive insights for good performance
        positive_insights = []
        for metric in metrics:
            if metric.current_value >= metric.target_value:
                positive_insights.append(WorkflowInsight(
                    insight_id=f"good_performance_{metric.metric_name}_{int(time.time())}",
                    category="performance",
                    title=f"Strong {metric.metric_name.replace('_', ' ').title()} Performance",
                    description=f"{metric.metric_name.replace('_', ' ').title()} is performing well at {metric.current_value:.1f} {metric.unit}",
                    impact_score=2,
                    effort_required="low",
                    recommendations=["Continue current practices", "Monitor for consistency"],
                    metrics_affected=[metric.metric_name]
                ))

        insights.extend(positive_insights[:2])  # Limit positive insights

        return insights

    def _calculate_overall_score(self, metrics: list[OptimizationMetric]) -> float:
        """Calculate overall optimization score"""
        if not metrics:
            return 0.0

        weighted_score = 0.0
        total_weight = 0.0

        for metric in metrics:
            # Get weight for this metric type
            metric_name = metric.metric_name
            weight = self.config["metric_weighting"].get(
                metric_name.replace("average_", "").replace("_rate", "").replace("_efficiency", "").replace("_effectiveness", ""),
                0.1
            )

            # Calculate score for this metric (0-100)
            if metric.target_value > 0:
                metric_score = min(100, (metric.current_value / metric.target_value) * 100)
            else:
                # For duration metrics, lower is better
                if "duration" in metric.metric_name:
                    metric_score = max(0, 100 - ((metric.current_value - metric.target_value) / metric.target_value) * 100)
                else:
                    metric_score = 100

            weighted_score += metric_score * weight
            total_weight += weight

        return weighted_score / max(total_weight, 1)

    def _identify_quick_wins(self, insights: list[WorkflowInsight],
                           metrics: list[OptimizationMetric]) -> list[dict[str, Any]]:
        """Identify quick win optimization opportunities"""
        quick_wins = []

        # Look for low-effort, high-impact opportunities
        for insight in insights:
            if (insight.effort_required == "low" and insight.impact_score > 5) or \
               (insight.effort_required == "medium" and insight.impact_score > 7):

                quick_wins.append({
                    "opportunity": insight.title,
                    "description": insight.description,
                    "effort_required": insight.effort_required,
                    "impact_score": insight.impact_score,
                    "estimated_time_to_implement": self._estimate_implementation_time(insight.effort_required),
                    "recommendations": insight.recommendations[:2]  # Top 2 recommendations
                })

        # Add system-level quick wins
        cache_metric = next((m for m in metrics if m.metric_name == "cache_hit_rate"), None)
        if cache_metric and cache_metric.current_value < 0.4:
            quick_wins.append({
                "opportunity": "Enable Predictive Cache Preloading",
                "description": "Enable predictive preloading to improve cache hit rate with minimal configuration",
                "effort_required": "low",
                "impact_score": 6,
                "estimated_time_to_implement": "1 hour",
                "recommendations": [
                    "Enable background preloading in cache configuration",
                    "Set appropriate confidence thresholds",
                    "Monitor preload effectiveness"
                ]
            })

        return sorted(quick_wins, key=lambda x: x["impact_score"], reverse=True)[:5]

    def _identify_high_impact_opportunities(self, insights: list[WorkflowInsight],
                                         metrics: list[OptimizationMetric]) -> list[dict[str, Any]]:
        """Identify high-impact optimization opportunities"""
        high_impact = []

        # Look for high-impact opportunities
        for insight in insights:
            if insight.impact_score > 7:
                high_impact.append({
                    "opportunity": insight.title,
                    "description": insight.description,
                    "impact_score": insight.impact_score,
                    "effort_required": insight.effort_required,
                    "estimated_roi": self._estimate_roi(insight.impact_score, insight.effort_required),
                    "recommendations": insight.recommendations,
                    "metrics_affected": insight.metrics_affected
                })

        # Add system-level high-impact opportunities
        duration_metric = next((m for m in metrics if m.metric_name == "average_session_duration"), None)
        if duration_metric and duration_metric.current_value > 600:  # 10 minutes
            high_impact.append({
                "opportunity": "Implement Session Optimization Framework",
                "description": "Significant session duration reduction opportunity with comprehensive optimization",
                "impact_score": 9,
                "effort_required": "high",
                "estimated_roi": "300%+",
                "recommendations": [
                    "Implement query pattern recognition and suggestions",
                    "Add session duration monitoring and alerts",
                    "Optimize cache configuration and preloading",
                    "Enhance user interface with efficiency indicators"
                ],
                "metrics_affected": ["average_session_duration", "user_satisfaction", "query_efficiency"]
            })

        return sorted(high_impact, key=lambda x: x["impact_score"], reverse=True)[:5]

    def _generate_recommendations(self, metrics: list[OptimizationMetric],
                                insights: list[WorkflowInsight],
                                quick_wins: list[dict], high_impact: list[dict]) -> dict[str, Any]:
        """Generate comprehensive optimization recommendations"""
        recommendations = {
            "immediate_actions": [],
            "short_term_improvements": [],
            "long_term_strategies": [],
            "monitoring_recommendations": [],
            "resource_allocation": {}
        }

        # Immediate actions (quick wins)
        for win in quick_wins[:3]:
            recommendations["immediate_actions"].extend(win["recommendations"])

        # Short-term improvements
        for insight in insights:
            if insight.effort_required == "medium":
                recommendations["short_term_improvements"].extend(insight.recommendations[:2])

        # Long-term strategies
        recommendations["long_term_strategies"] = [
            "Implement machine learning-based query optimization",
            "Develop advanced session management algorithms",
            "Create personalized user experience optimization",
            "Build comprehensive workflow automation"
        ]

        # Monitoring recommendations
        recommendations["monitoring_recommendations"] = [
            "Set up real-time performance dashboards",
            "Implement automated alerting for degradation",
            "Establish weekly optimization review meetings",
            "Create monthly performance trend analysis"
        ]

        # Resource allocation
        recommendations["resource_allocation"] = {
            "development_focus": "Session optimization and cache performance",
            "monitoring_priority": "Session duration and query efficiency",
            "optimization_budget_percentage": 15,
            "expected_timeframe": "2-3 weeks for initial improvements"
        }

        return recommendations

    def _analyze_trends(self) -> dict[str, Any]:
        """Analyze trends in optimization metrics"""
        trends = {
            "period_analysis": {},
            "trend_summary": {},
            "predictions": {}
        }

        # This would typically involve comparing historical data
        # For now, provide a framework for trend analysis

        for period in self.config["trend_analysis_periods"]:
            trends["period_analysis"][f"{period}_days"] = {
                "data_points": "historical_data_needed",
                "trend_direction": "stable",
                "confidence_level": "medium",
                "key_changes": []
            }

        trends["trend_summary"] = {
            "overall_trend": "improving",
            "most_improved_metric": "cache_hit_rate",
            "most_degraded_metric": "none",
            "trend_stability": "high"
        }

        trends["predictions"] = {
            "next_week_forecast": "continued_improvement",
            "next_month_forecast": "significant_gains_expected",
            "optimization_potential": "high"
        }

        return trends

    def _calculate_roi_analysis(self, metrics: list[OptimizationMetric]) -> dict[str, Any]:
        """Calculate ROI analysis for optimization efforts"""
        roi = {
            "current_inefficiency_cost": 0.0,
            "potential_savings": 0.0,
            "implementation_cost": 0.0,
            "roi_percentage": 0.0,
            "payback_period_days": 0,
            "value_drivers": []
        }

        # Calculate current inefficiency cost (simplified)
        duration_metric = next((m for m in metrics if m.metric_name == "average_session_duration"), None)
        if duration_metric:
            excess_time = max(0, duration_metric.current_value - duration_metric.target_value)
            # Assume $50/hour value of time and 100 sessions per day
            daily_cost = (excess_time / 3600) * 50 * 100
            roi["current_inefficiency_cost"] = daily_cost * 30  # Monthly cost

        # Estimate potential savings (20-40% of inefficiency cost)
        roi["potential_savings"] = roi["current_inefficiency_cost"] * 0.3

        # Implementation cost (development time)
        roi["implementation_cost"] = 5000  # $5k estimated

        # Calculate ROI
        if roi["implementation_cost"] > 0:
            roi["roi_percentage"] = ((roi["potential_savings"] * 12 - roi["implementation_cost"]) /
                                   roi["implementation_cost"]) * 100

        # Payback period
        monthly_savings = roi["potential_savings"]
        if monthly_savings > 0:
            roi["payback_period_days"] = (roi["implementation_cost"] / monthly_savings) * 30

        # Value drivers
        roi["value_drivers"] = [
            "Reduced session duration improves user productivity",
            "Better cache performance reduces infrastructure costs",
            "Improved query efficiency enhances user satisfaction",
            "Automated optimizations reduce manual intervention"
        ]

        return roi

    def _generate_key_findings(self, metrics: list[OptimizationMetric]) -> list[str]:
        """Generate key findings for executive summary"""
        findings = []

        for metric in metrics:
            if metric.current_value > metric.target_value * 1.5:
                findings.append(f"Critical issue: {metric.metric_name.replace('_', ' ').title()} is {metric.current_value:.1f} {metric.unit}, {(metric.current_value/metric.target_value-1)*100:.0f}% above target")
            elif metric.current_value < metric.target_value * 0.8:
                findings.append(f"Strong performance: {metric.metric_name.replace('_', ' ').title()} is {(metric.target_value/metric.current_value-1)*100:.0f}% better than target")

        if not findings:
            findings.append("All metrics are within acceptable ranges")

        return findings[:5]  # Top 5 findings

    def _get_total_data_points(self) -> int:
        """Get total number of data points analyzed"""
        pattern_stats = self.pattern_recognizer.get_statistics()
        session_stats = self.session_monitor.get_session_statistics(7)

        return (
            pattern_stats.get("total_queries", 0) +
            session_stats.get("total_sessions", 0) +
            len(self.context_manager.context_history)
        )

    def _estimate_implementation_time(self, effort_required: str) -> str:
        """Estimate implementation time based on effort required"""
        time_map = {
            "low": "2-4 hours",
            "medium": "1-3 days",
            "high": "1-2 weeks"
        }
        return time_map.get(effort_required, "unknown")

    def _estimate_roi(self, impact_score: float, effort_required: str) -> str:
        """Estimate ROI based on impact score and effort"""
        effort_multiplier = {"low": 3, "medium": 2, "high": 1}
        multiplier = effort_multiplier.get(effort_required, 1)

        roi_value = impact_score * multiplier * 30  # Base calculation

        if roi_value > 200:
            return "300%+"
        elif roi_value > 150:
            return "200-300%"
        elif roi_value > 100:
            return "150-200%"
        elif roi_value > 50:
            return "100-150%"
        else:
            return "<100%"

    def _get_duration_recommendations(self, current_duration: float) -> list[str]:
        """Get recommendations for session duration optimization"""
        recommendations = []

        if current_duration > 600:  # 10 minutes
            recommendations.extend([
                "Implement session break suggestions at 5-minute mark",
                "Add query efficiency scoring and real-time feedback",
                "Enable predictive query suggestions based on session context"
            ])
        elif current_duration > 300:  # 5 minutes
            recommendations.extend([
                "Add session duration indicators",
                "Implement query pattern recognition for efficiency",
                "Review and optimize search strategy suggestions"
            ])

        return recommendations

    def _get_pattern_recommendations(self, pattern_hit_rate: float) -> list[str]:
        """Get recommendations for query pattern optimization"""
        if pattern_hit_rate < 0.3:
            return [
                "Expand pattern training data with more query examples",
                "Implement machine learning-based pattern recognition",
                "Improve query normalization and preprocessing"
            ]
        elif pattern_hit_rate < 0.6:
            return [
                "Refine pattern matching algorithms",
                "Add more flexible pattern definitions",
                "Implement fuzzy pattern matching"
            ]
        else:
            return ["Continue monitoring pattern effectiveness"]

    def _get_cache_recommendations(self, hit_rate: float) -> list[str]:
        """Get recommendations for cache optimization"""
        if hit_rate < 0.3:
            return [
                "Review cache key generation and normalization",
                "Implement predictive preloading for common queries",
                "Increase cache TTL for frequently accessed content"
            ]
        elif hit_rate < 0.5:
            return [
                "Optimize cache size and eviction policies",
                "Implement multi-level cache warming strategies",
                "Add cache performance monitoring and alerting"
            ]
        else:
            return ["Monitor cache performance trends"]

    def _get_success_rate_recommendations(self, success_rate: float) -> list[str]:
        """Get recommendations for success rate improvement"""
        if success_rate < 0.7:
            return [
                "Implement query validation and suggestion system",
                "Add educational tooltips for better query construction",
                "Provide examples of successful query patterns"
            ]
        elif success_rate < 0.85:
            return [
                "Enhance query suggestion accuracy",
                "Implement contextual query assistance",
                "Add success metrics tracking and feedback"
            ]
        else:
            return ["Maintain current success strategies"]

    def _get_preload_recommendations(self, effectiveness: float) -> list[str]:
        """Get recommendations for preloading optimization"""
        if effectiveness < 0.2:
            return [
                "Adjust preload confidence thresholds",
                "Improve pattern recognition accuracy",
                "Expand historical data for better predictions"
            ]
        elif effectiveness < 0.4:
            return [
                "Optimize preload scheduling and priorities",
                "Implement context-aware preloading",
                "Add preload effectiveness monitoring"
            ]
        else:
            return ["Continue optimizing preload strategies"]

    def _load_analytics_data(self):
        """Load existing analytics data"""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file) as f:
                    data = json.load(f)
                    # Could load previous reports for trend analysis
                self.logger.debug("Loaded analytics data")
            except Exception as e:
                self.logger.error(f"Failed to load analytics data: {e}")

    def _save_analytics_data(self, report: dict[str, Any]):
        """Save analytics report"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            # Also save insights separately
            insights = report.get("insights", [])
            if insights:
                with open(self.insights_file, 'w') as f:
                    json.dump({
                        "last_updated": time.time(),
                        "insights": insights
                    }, f, indent=2, default=str)

            self.logger.info("Analytics report saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save analytics data: {e}")

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get data for real-time dashboard display"""
        # Generate a lightweight version of the full report
        quick_report = self.generate_comprehensive_report()

        return {
            "timestamp": quick_report["report_metadata"]["generated_at"],
            "overall_score": quick_report["executive_summary"]["overall_optimization_score"],
            "status": quick_report["executive_summary"]["status"],
            "key_metrics": {
                metric.metric_name: {
                    "current": metric.current_value,
                    "target": metric.target_value,
                    "unit": metric.unit,
                    "trend": metric.improvement_trend
                }
                for metric in quick_report["optimization_metrics"]
            },
            "top_insights": quick_report["insights"][:3],
            "quick_wins": quick_report["opportunities"]["quick_wins"][:3],
            "alerts": self._generate_active_alerts(quick_report)
        }

    def _generate_active_alerts(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate active alerts based on report data"""
        alerts = []

        for metric in report["optimization_metrics"]:
            if metric.current_value > metric.target_value * 1.5:  # 50% above target
                alerts.append({
                    "type": "critical",
                    "metric": metric.metric_name,
                    "message": f"{metric.metric_name.replace('_', ' ').title()} is critically high",
                    "value": metric.current_value,
                    "unit": metric.unit
                })
            elif metric.current_value < metric.target_value * 0.5:  # 50% below target (good for duration, bad for rates)
                if "duration" in metric.metric_name:
                    alerts.append({
                        "type": "success",
                        "metric": metric.metric_name,
                        "message": f"{metric.metric_name.replace('_', ' ').title()} is excellent",
                        "value": metric.current_value,
                        "unit": metric.unit
                    })

        return alerts[:5]  # Top 5 alerts
