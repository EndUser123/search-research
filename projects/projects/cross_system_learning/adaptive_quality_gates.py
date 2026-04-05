"""
Adaptive Quality Gates - Dynamic quality threshold adjustment system based on
cross-system learning and historical performance.

This system provides:
1. Dynamic threshold adjustment based on collective experience
2. Multi-dimensional quality assessment
3. Context-aware gate configuration
4. Learning from success/failure patterns
5. Real-time quality monitoring and alerting
"""

import logging
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .core.base_patterns import DomainType
from .core.memory_structures import QualityMemory
from .memory_integration import MemoryIntegrationSystem, MemoryType


class GateStatus(Enum):
    """Status of quality gates."""

    OPEN = "open"  # Quality threshold met
    CLOSED = "closed"  # Quality threshold not met
    WARNING = "warning"  # Approaching threshold
    MAINTENANCE = "maintenance"  # Gate under adjustment


class QualityDimension(Enum):
    """Dimensions of quality assessment."""

    CLARITY = "clarity"
    COMPLETENESS = "completeness"
    SPECIFICITY = "specificity"
    RELEVANCE = "relevance"
    STRUCTURE = "structure"
    CONSISTENCY = "consistency"
    NOVELTY = "novelty"
    USABILITY = "usability"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"


class AdaptationStrategy(Enum):
    """Strategies for threshold adaptation."""

    CONSERVATIVE = "conservative"  # Slow, stable adjustments
    AGGRESSIVE = "aggressive"  # Fast adjustments based on recent data
    BALANCED = "balanced"  # Mix of historical and recent data
    DOMAIN_SPECIFIC = "domain_specific"  # Adaptation based on domain characteristics
    PERFORMANCE_DRIVEN = "performance_driven"  # Based on system performance metrics


@dataclass
class QualityThreshold:
    """Dynamic quality threshold for a specific dimension."""

    dimension: QualityDimension
    domain: DomainType
    current_threshold: float  # 0.0 to 1.0
    minimum_threshold: float  # Absolute minimum
    maximum_threshold: float  # Absolute maximum
    optimal_threshold: float  # Target optimal value

    # Historical data
    threshold_history: deque = field(default_factory=lambda: deque(maxlen=100))
    adjustment_count: int = 0
    last_adjustment: datetime | None = None

    # Adaptation parameters
    adaptation_rate: float = 0.1  # How quickly threshold adapts
    stability_factor: float = 0.8  # Resistance to change
    confidence_level: float = 0.5  # Confidence in current threshold

    # Performance correlation
    success_correlation: float = 0.0  # Correlation with success rates
    performance_impact: float = 0.0  # Impact on system performance

    def calculate_adjustment_factor(self, recent_performance: float) -> float:
        """Calculate adjustment factor based on recent performance."""
        # Base adjustment from recent performance
        performance_delta = recent_performance - 0.7  # Target 70% success rate
        base_adjustment = performance_delta * self.adaptation_rate

        # Apply stability factor
        adjusted_factor = base_adjustment * (1.0 - self.stability_factor)

        # Apply confidence level
        final_factor = adjusted_factor * self.confidence_level

        return final_factor

    def update_threshold(self, new_value: float, reason: str = "") -> None:
        """Update threshold with validation and history tracking."""
        # Validate new threshold
        new_value = max(self.minimum_threshold, min(self.maximum_threshold, new_value))

        # Record history
        self.threshold_history.append(
            {
                "old_value": self.current_threshold,
                "new_value": new_value,
                "timestamp": datetime.now(),
                "reason": reason,
                "confidence": self.confidence_level,
            }
        )

        # Update threshold
        self.current_threshold = new_value
        self.adjustment_count += 1
        self.last_adjustment = datetime.now()

    def get_statistics(self) -> dict[str, Any]:
        """Get threshold statistics."""
        history_values = [h["new_value"] for h in self.threshold_history]

        return {
            "current_threshold": self.current_threshold,
            "adjustment_count": self.adjustment_count,
            "stability_factor": self.stability_factor,
            "confidence_level": self.confidence_level,
            "success_correlation": self.success_correlation,
            "performance_impact": self.performance_impact,
            "volatility": self._calculate_volatility(),
            "trend": self._calculate_trend(),
        }

    def _calculate_volatility(self) -> float:
        """Calculate threshold volatility."""
        if len(self.threshold_history) < 2:
            return 0.0

        values = [h["new_value"] for h in self.threshold_history]
        mean = sum(values) / len(values)

        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)

    def _calculate_trend(self) -> str:
        """Calculate threshold trend direction."""
        if len(self.threshold_history) < 10:
            return "insufficient_data"

        recent_values = [h["new_value"] for h in list(self.threshold_history)[-10:]]
        older_values = (
            [h["new_value"] for h in list(self.threshold_history)[-20:-10]]
            if len(self.threshold_history) >= 20
            else recent_values[:5]
        )

        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)

        if recent_avg > older_avg + 0.05:
            return "increasing"
        elif recent_avg < older_avg - 0.05:
            return "decreasing"
        else:
            return "stable"


@dataclass
class QualityGate:
    """Comprehensive quality gate for enhancement assessment."""

    gate_id: str
    name: str
    description: str
    domain: DomainType
    thresholds: dict[QualityDimension, QualityThreshold]
    status: GateStatus = GateStatus.OPEN

    # Gate configuration
    weightings: dict[QualityDimension, float] = field(default_factory=dict)
    required_dimensions: set[QualityDimension] = field(default_factory=set)
    optional_dimensions: set[QualityDimension] = field(default_factory=set)

    # Performance tracking
    evaluation_history: deque = field(default_factory=lambda: deque(maxlen=500))
    success_rate: float = 0.0
    average_score: float = 0.0
    last_evaluation: datetime | None = None

    # Learning parameters
    adaptation_strategy: AdaptationStrategy = AdaptationStrategy.BALANCED
    learning_rate: float = 0.1
    confidence_threshold: float = 0.6

    # Context awareness
    context_sensitivity: float = 0.5  # How much context affects evaluation
    current_context: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def evaluate(
        self,
        quality_data: dict[QualityDimension, float],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate quality against gate thresholds."""
        evaluation_time = datetime.now()

        # Update context if provided
        if context:
            self.current_context = context

        # Calculate dimension scores
        dimension_scores = {}
        passed_dimensions = set()
        failed_dimensions = set()
        warning_dimensions = set()

        overall_score = 0.0
        total_weight = 0.0

        for dimension, threshold in self.thresholds.items():
            actual_score = quality_data.get(dimension, 0.0)
            weight = self.weightings.get(dimension, 1.0)

            # Apply context adjustment
            if (
                context
                and dimension in threshold.threshold_history
                and len(threshold.threshold_history) > 0
            ):
                context_adjustment = self._calculate_context_adjustment(
                    dimension, context
                )
                adjusted_threshold = threshold.current_threshold * (
                    1.0 + context_adjustment * self.context_sensitivity
                )
            else:
                adjusted_threshold = threshold.current_threshold

            # Determine status
            if actual_score >= adjusted_threshold:
                dimension_scores[dimension] = {
                    "actual": actual_score,
                    "threshold": adjusted_threshold,
                    "status": "pass",
                    "margin": actual_score - adjusted_threshold,
                }
                passed_dimensions.add(dimension)
            elif actual_score >= adjusted_threshold * 0.9:  # 90% of threshold
                dimension_scores[dimension] = {
                    "actual": actual_score,
                    "threshold": adjusted_threshold,
                    "status": "warning",
                    "margin": actual_score - adjusted_threshold,
                }
                warning_dimensions.add(dimension)
            else:
                dimension_scores[dimension] = {
                    "actual": actual_score,
                    "threshold": adjusted_threshold,
                    "status": "fail",
                    "margin": actual_score - adjusted_threshold,
                }
                failed_dimensions.add(dimension)

            overall_score += actual_score * weight
            total_weight += weight

        # Calculate final score
        final_score = overall_score / total_weight if total_weight > 0 else 0.0

        # Determine gate status
        if failed_dimensions:
            if self.required_dimensions.issubset(passed_dimensions):
                gate_status = GateStatus.WARNING
            else:
                gate_status = GateStatus.CLOSED
        elif warning_dimensions:
            gate_status = GateStatus.WARNING
        else:
            gate_status = GateStatus.OPEN

        # Create evaluation result
        evaluation_result = {
            "gate_id": self.gate_id,
            "timestamp": evaluation_time,
            "final_score": final_score,
            "gate_status": gate_status.value,
            "dimension_scores": dimension_scores,
            "passed_dimensions": list(passed_dimensions),
            "failed_dimensions": list(failed_dimensions),
            "warning_dimensions": list(warning_dimensions),
            "required_dimensions_met": self.required_dimensions.issubset(
                passed_dimensions
            ),
            "context_applied": context is not None,
        }

        # Update gate statistics
        self._update_statistics(evaluation_result)

        return evaluation_result

    def _calculate_context_adjustment(
        self, dimension: QualityDimension, context: dict[str, Any]
    ) -> float:
        """Calculate context-based threshold adjustment."""
        adjustment = 0.0

        # Complexity adjustment
        complexity = context.get("complexity", 0.5)
        if dimension in [QualityDimension.CLARITY, QualityDimension.SIMPLICITY]:
            adjustment -= (
                complexity - 0.5
            ) * 0.2  # Higher complexity = lower clarity threshold
        elif dimension in [QualityDimension.ROBUSTNESS, QualityDimension.COMPLETENESS]:
            adjustment += (
                complexity - 0.5
            ) * 0.2  # Higher complexity = higher robustness threshold

        # Time pressure adjustment
        time_pressure = context.get("time_pressure", 0.5)
        if dimension in [QualityDimension.EFFICIENCY, QualityDimension.SIMPLICITY]:
            adjustment -= (
                time_pressure - 0.5
            ) * 0.15  # High time pressure = lower efficiency threshold

        # Expertise level adjustment
        expertise = context.get("expertise_level", 0.5)
        if dimension in [QualityDimension.CLARITY, QualityDimension.COMPLETENESS]:
            adjustment += (
                expertise - 0.5
            ) * 0.1  # Higher expertise = higher clarity threshold

        # Domain-specific adjustments
        domain_context = context.get("domain_context", {})
        if self.domain.value in domain_context:
            domain_adjustments = domain_context[self.domain.value]
            if dimension.value in domain_adjustments:
                adjustment += domain_adjustments[dimension.value]

        return max(-0.3, min(0.3, adjustment))  # Limit adjustment range

    def _update_statistics(self, evaluation_result: dict[str, Any]) -> None:
        """Update gate statistics with new evaluation."""
        # Add to history
        self.evaluation_history.append(evaluation_result)
        self.last_evaluation = evaluation_result["timestamp"]

        # Update success rate
        success_count = sum(
            1
            for eval in self.evaluation_history
            if eval["gate_status"] == GateStatus.OPEN.value
        )
        self.success_rate = success_count / len(self.evaluation_history)

        # Update average score
        scores = [eval["final_score"] for eval in self.evaluation_history]
        self.average_score = sum(scores) / len(scores)

        self.last_updated = datetime.now()

    def adapt_thresholds(self, performance_data: dict[str, Any]) -> None:
        """Adapt thresholds based on performance data."""
        recent_success_rate = performance_data.get("recent_success_rate", 0.7)
        system_performance = performance_data.get("system_performance", 0.7)
        user_satisfaction = performance_data.get("user_satisfaction", 0.7)

        overall_performance = (
            recent_success_rate + system_performance + user_satisfaction
        ) / 3.0

        for dimension, threshold in self.thresholds.items():
            # Calculate dimension-specific performance
            dimension_performance = self._calculate_dimension_performance(
                dimension, performance_data
            )

            # Determine adaptation based on strategy
            if self.adaptation_strategy == AdaptationStrategy.CONSERVATIVE:
                adjustment_factor = self._conservative_adaptation(
                    threshold, dimension_performance, overall_performance
                )
            elif self.adaptation_strategy == AdaptationStrategy.AGGRESSIVE:
                adjustment_factor = self._aggressive_adaptation(
                    threshold, dimension_performance, overall_performance
                )
            elif self.adaptation_strategy == AdaptationStrategy.BALANCED:
                adjustment_factor = self._balanced_adaptation(
                    threshold, dimension_performance, overall_performance
                )
            elif self.adaptation_strategy == AdaptationStrategy.PERFORMANCE_DRIVEN:
                adjustment_factor = self._performance_driven_adaptation(
                    threshold, dimension_performance, overall_performance
                )
            else:
                adjustment_factor = self._domain_specific_adaptation(
                    threshold, dimension_performance, overall_performance
                )

            # Apply adjustment
            new_threshold = threshold.current_threshold + adjustment_factor
            threshold.update_threshold(
                new_threshold,
                f"Performance-driven adaptation (overall: {overall_performance:.2f})",
            )

            # Update confidence level
            if abs(adjustment_factor) < 0.01:
                threshold.confidence_level = min(1.0, threshold.confidence_level + 0.05)
            else:
                threshold.confidence_level = max(0.1, threshold.confidence_level - 0.02)

    def _calculate_dimension_performance(
        self, dimension: QualityDimension, performance_data: dict[str, Any]
    ) -> float:
        """Calculate performance metrics for a specific dimension."""
        # Get dimension-specific performance data
        dimension_data = performance_data.get("dimensions", {}).get(dimension.value, {})

        # Default to overall performance if no specific data
        return dimension_data.get(
            "performance", performance_data.get("overall_performance", 0.7)
        )

    def _conservative_adaptation(
        self, threshold: QualityThreshold, dimension_perf: float, overall_perf: float
    ) -> float:
        """Conservative adaptation strategy."""
        # Very small adjustments, high stability
        performance_gap = dimension_perf - 0.7
        return (
            performance_gap
            * threshold.adaptation_rate
            * 0.1
            * (1.0 - threshold.stability_factor)
        )

    def _aggressive_adaptation(
        self, threshold: QualityThreshold, dimension_perf: float, overall_perf: float
    ) -> float:
        """Aggressive adaptation strategy."""
        # Fast adjustments based on recent performance
        performance_gap = dimension_perf - 0.7
        return (
            performance_gap
            * threshold.adaptation_rate
            * (1.0 - threshold.stability_factor)
        )

    def _balanced_adaptation(
        self, threshold: QualityThreshold, dimension_perf: float, overall_perf: float
    ) -> float:
        """Balanced adaptation strategy."""
        # Mix of conservative and aggressive
        performance_gap = dimension_perf - 0.7
        historical_weight = 0.6
        recent_weight = 0.4

        # Consider historical performance (from threshold history)
        if len(threshold.threshold_history) > 0:
            historical_performance = threshold.success_correlation
        else:
            historical_performance = 0.7

        weighted_performance = (
            historical_performance * historical_weight + dimension_perf * recent_weight
        )
        performance_gap = weighted_performance - 0.7

        return (
            performance_gap
            * threshold.adaptation_rate
            * (1.0 - threshold.stability_factor * 0.5)
        )

    def _performance_driven_adaptation(
        self, threshold: QualityThreshold, dimension_perf: float, overall_perf: float
    ) -> float:
        """Performance-driven adaptation strategy."""
        # Adjust based on system performance impact
        performance_gap = dimension_perf - 0.7

        # Factor in performance impact
        impact_factor = 1.0 + threshold.performance_impact

        return (
            performance_gap
            * threshold.adaptation_rate
            * impact_factor
            * (1.0 - threshold.stability_factor)
        )

    def _domain_specific_adaptation(
        self, threshold: QualityThreshold, dimension_perf: float, overall_perf: float
    ) -> float:
        """Domain-specific adaptation strategy."""
        # Base adaptation
        performance_gap = dimension_perf - 0.7
        base_adjustment = (
            performance_gap
            * threshold.adaptation_rate
            * (1.0 - threshold.stability_factor)
        )

        # Apply domain-specific factors
        domain_factors = {
            DomainType.SOFTWARE_DEVELOPMENT: {
                QualityDimension.ROBUSTNESS: 1.2,
                QualityDimension.EFFICIENCY: 1.1,
                QualityDimension.CLARITY: 1.0,
            },
            DomainType.DATA_ANALYSIS: {
                QualityDimension.ACCURACY: 1.3,
                QualityDimension.COMPLETENESS: 1.1,
                QualityDimension.CLARITY: 0.9,
            },
            DomainType.DOCUMENTATION: {
                QualityDimension.CLARITY: 1.3,
                QualityDimension.COMPLETENESS: 1.2,
                QualityDimension.STRUCTURE: 1.1,
            },
            DomainType.TROUBLESHOOTING: {
                QualityDimension.SPECIFICITY: 1.2,
                QualityDimension.ROBUSTNESS: 1.1,
                QualityDimension.EFFICIENCY: 1.0,
            },
        }

        domain_factor = domain_factors.get(self.domain, {}).get(
            threshold.dimension, 1.0
        )

        return base_adjustment * domain_factor

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive gate statistics."""
        dimension_stats = {}
        for dimension, threshold in self.thresholds.items():
            dimension_stats[dimension.value] = threshold.get_statistics()

        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "domain": self.domain.value,
            "status": self.status.value,
            "success_rate": self.success_rate,
            "average_score": self.average_score,
            "evaluation_count": len(self.evaluation_history),
            "last_evaluation": self.last_evaluation.isoformat()
            if self.last_evaluation
            else None,
            "adaptation_strategy": self.adaptation_strategy.value,
            "dimension_thresholds": dimension_stats,
            "context_sensitivity": self.context_sensitivity,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class AdaptiveQualityGates:
    """Main system for managing adaptive quality gates."""

    def __init__(
        self, quality_memory: QualityMemory, memory_integration: MemoryIntegrationSystem
    ):
        self.quality_memory = quality_memory
        self.memory_integration = memory_integration
        self.logger = logging.getLogger(__name__)

        # Gate management
        self.quality_gates: dict[str, QualityGate] = {}
        self.domain_gates: dict[DomainType, list[str]] = defaultdict(list)

        # Global configuration
        self.global_adaptation_strategy = AdaptationStrategy.BALANCED
        self.default_adaptation_rate = 0.1
        self.min_confidence_threshold = 0.5
        self.max_confidence_threshold = 0.95

        # Performance monitoring
        self.performance_monitoring = {
            "enabled": True,
            "evaluation_frequency": timedelta(minutes=15),
            "adaptation_frequency": timedelta(hours=6),
            "alert_thresholds": {
                "low_success_rate": 0.6,
                "high_volatility": 0.15,
                "stagnation_threshold": 0.02,
            },
        }

        # Learning integration
        self.learning_enabled = True
        self.cross_domain_learning = True
        self.pattern_influence = 0.3  # How much learned patterns influence gates

        # Threading
        self.lock = threading.RLock()
        self._shutdown = False
        self._background_threads: list[threading.Thread] = []

        # Initialize default gates
        self._initialize_default_gates()

        # Start background tasks
        self._start_background_tasks()

    def _initialize_default_gates(self) -> None:
        """Initialize default quality gates for each domain."""
        for domain in DomainType:
            gate_id = f"default_{domain.value}_gate"
            gate = self._create_default_gate(gate_id, domain)
            self.quality_gates[gate_id] = gate
            self.domain_gates[domain].append(gate_id)

    def _create_default_gate(self, gate_id: str, domain: DomainType) -> QualityGate:
        """Create a default quality gate for a domain."""
        # Define domain-specific thresholds
        default_thresholds = self._get_domain_thresholds(domain)

        # Create quality thresholds
        thresholds = {}
        for dimension, config in default_thresholds.items():
            thresholds[dimension] = QualityThreshold(
                dimension=dimension,
                domain=domain,
                current_threshold=config["default"],
                minimum_threshold=config["minimum"],
                maximum_threshold=config["maximum"],
                optimal_threshold=config["optimal"],
                adaptation_rate=self.default_adaptation_rate,
            )

        # Define weightings
        weightings = self._get_domain_weightings(domain)

        # Define required dimensions
        required_dimensions = self._get_required_dimensions(domain)

        # Create gate
        gate = QualityGate(
            gate_id=gate_id,
            name=f"Default {domain.value.replace('_', ' ').title()} Quality Gate",
            description=f"Default quality assessment for {domain.value} enhancements",
            domain=domain,
            thresholds=thresholds,
            weightings=weightings,
            required_dimensions=required_dimensions,
            adaptation_strategy=self.global_adaptation_strategy,
        )

        return gate

    def _get_domain_thresholds(
        self, domain: DomainType
    ) -> dict[QualityDimension, dict[str, float]]:
        """Get default threshold configurations for a domain."""
        base_thresholds = {
            QualityDimension.CLARITY: {
                "default": 0.7,
                "minimum": 0.3,
                "maximum": 1.0,
                "optimal": 0.8,
            },
            QualityDimension.COMPLETENESS: {
                "default": 0.6,
                "minimum": 0.2,
                "maximum": 1.0,
                "optimal": 0.8,
            },
            QualityDimension.SPECIFICITY: {
                "default": 0.6,
                "minimum": 0.3,
                "maximum": 1.0,
                "optimal": 0.7,
            },
            QualityDimension.RELEVANCE: {
                "default": 0.8,
                "minimum": 0.4,
                "maximum": 1.0,
                "optimal": 0.9,
            },
            QualityDimension.STRUCTURE: {
                "default": 0.6,
                "minimum": 0.2,
                "maximum": 1.0,
                "optimal": 0.7,
            },
            QualityDimension.CONSISTENCY: {
                "default": 0.7,
                "minimum": 0.3,
                "maximum": 1.0,
                "optimal": 0.8,
            },
            QualityDimension.NOVELTY: {
                "default": 0.5,
                "minimum": 0.1,
                "maximum": 1.0,
                "optimal": 0.7,
            },
            QualityDimension.EFFICIENCY: {
                "default": 0.6,
                "minimum": 0.2,
                "maximum": 1.0,
                "optimal": 0.8,
            },
            QualityDimension.ROBUSTNESS: {
                "default": 0.6,
                "minimum": 0.2,
                "maximum": 1.0,
                "optimal": 0.7,
            },
            QualityDimension.USABILITY: {
                "default": 0.7,
                "minimum": 0.3,
                "maximum": 1.0,
                "optimal": 0.8,
            },
        }

        # Domain-specific adjustments
        domain_adjustments = {
            DomainType.SOFTWARE_DEVELOPMENT: {
                QualityDimension.ROBUSTNESS: {
                    "default": 0.8,
                    "minimum": 0.4,
                    "optimal": 0.9,
                },
                QualityDimension.EFFICIENCY: {
                    "default": 0.7,
                    "minimum": 0.3,
                    "optimal": 0.8,
                },
            },
            DomainType.DATA_ANALYSIS: {
                QualityDimension.ACCURACY: {
                    "default": 0.8,
                    "minimum": 0.5,
                    "optimal": 0.9,
                },
                QualityDimension.COMPLETENESS: {
                    "default": 0.7,
                    "minimum": 0.4,
                    "optimal": 0.8,
                },
            },
            DomainType.DOCUMENTATION: {
                QualityDimension.CLARITY: {
                    "default": 0.8,
                    "minimum": 0.5,
                    "optimal": 0.9,
                },
                QualityDimension.STRUCTURE: {
                    "default": 0.8,
                    "minimum": 0.4,
                    "optimal": 0.9,
                },
            },
            DomainType.TROUBLESHOOTING: {
                QualityDimension.SPECIFICITY: {
                    "default": 0.8,
                    "minimum": 0.5,
                    "optimal": 0.9,
                },
                QualityDimension.ROBUSTNESS: {
                    "default": 0.7,
                    "minimum": 0.4,
                    "optimal": 0.8,
                },
            },
        }

        # Apply domain adjustments
        if domain in domain_adjustments:
            for dimension, adjustments in domain_adjustments[domain].items():
                if dimension in base_thresholds:
                    base_thresholds[dimension].update(adjustments)

        return base_thresholds

    def _get_domain_weightings(
        self, domain: DomainType
    ) -> dict[QualityDimension, float]:
        """Get dimension weightings for a domain."""
        base_weightings = {
            QualityDimension.CLARITY: 1.0,
            QualityDimension.COMPLETENESS: 1.0,
            QualityDimension.SPECIFICITY: 1.0,
            QualityDimension.RELEVANCE: 1.2,
            QualityDimension.STRUCTURE: 0.8,
            QualityDimension.CONSISTENCY: 0.9,
            QualityDimension.NOVELTY: 0.6,
            QualityDimension.EFFICIENCY: 0.9,
            QualityDimension.ROBUSTNESS: 0.8,
            QualityDimension.USABILITY: 1.0,
        }

        # Domain-specific weighting adjustments
        domain_weightings = {
            DomainType.SOFTWARE_DEVELOPMENT: {
                QualityDimension.ROBUSTNESS: 1.3,
                QualityDimension.EFFICIENCY: 1.2,
                QualityDimension.CONSISTENCY: 1.1,
            },
            DomainType.DATA_ANALYSIS: {
                QualityDimension.ACCURACY: 1.4,
                QualityDimension.COMPLETENESS: 1.2,
                QualityDimension.RELEVANCE: 1.1,
            },
            DomainType.DOCUMENTATION: {
                QualityDimension.CLARITY: 1.4,
                QualityDimension.STRUCTURE: 1.3,
                QualityDimension.COMPLETENESS: 1.2,
            },
            DomainType.TROUBLESHOOTING: {
                QualityDimension.SPECIFICITY: 1.3,
                QualityDimension.ROBUSTNESS: 1.2,
                QualityDimension.EFFICIENCY: 1.1,
            },
        }

        # Apply domain adjustments
        if domain in domain_weightings:
            for dimension, weight in domain_weightings[domain].items():
                if dimension in base_weightings:
                    base_weightings[dimension] = weight

        return base_weightings

    def _get_required_dimensions(self, domain: DomainType) -> set[QualityDimension]:
        """Get required quality dimensions for a domain."""
        base_required = {
            QualityDimension.CLARITY,
            QualityDimension.RELEVANCE,
            QualityDimension.STRUCTURE,
        }

        domain_specific = {
            DomainType.SOFTWARE_DEVELOPMENT: {
                QualityDimension.ROBUSTNESS,
                QualityDimension.EFFICIENCY,
            },
            DomainType.DATA_ANALYSIS: {
                QualityDimension.ACCURACY,
                QualityDimension.COMPLETENESS,
            },
            DomainType.DOCUMENTATION: {
                QualityDimension.CLARITY,
                QualityDimension.STRUCTURE,
            },
            DomainType.TROUBLESHOOTING: {
                QualityDimension.SPECIFICITY,
                QualityDimension.ROBUSTNESS,
            },
        }

        return base_required.union(domain_specific.get(domain, set()))

    def create_gate(
        self,
        gate_id: str,
        name: str,
        description: str,
        domain: DomainType,
        thresholds_config: dict[str, Any],
        **kwargs,
    ) -> str:
        """Create a custom quality gate."""
        with self.lock:
            if gate_id in self.quality_gates:
                raise ValueError(f"Gate {gate_id} already exists")

            # Create thresholds
            thresholds = {}
            for dim_name, config in thresholds_config.items():
                dimension = QualityDimension(dim_name)
                thresholds[dimension] = QualityThreshold(
                    dimension=dimension,
                    domain=domain,
                    current_threshold=config.get("current", 0.7),
                    minimum_threshold=config.get("minimum", 0.3),
                    maximum_threshold=config.get("maximum", 1.0),
                    optimal_threshold=config.get("optimal", 0.8),
                    adaptation_rate=config.get(
                        "adaptation_rate", self.default_adaptation_rate
                    ),
                )

            # Create gate
            gate = QualityGate(
                gate_id=gate_id,
                name=name,
                description=description,
                domain=domain,
                thresholds=thresholds,
                weightings=kwargs.get(
                    "weightings", self._get_domain_weightings(domain)
                ),
                required_dimensions=set(
                    QualityDimension(d) for d in kwargs.get("required_dimensions", [])
                ),
                adaptation_strategy=AdaptationStrategy(
                    kwargs.get("adaptation_strategy", "balanced")
                ),
            )

            self.quality_gates[gate_id] = gate
            self.domain_gates[domain].append(gate_id)

            self.logger.info(f"Created custom quality gate: {gate_id}")
            return gate_id

    def evaluate_quality(
        self,
        gate_id: str,
        quality_data: dict[str, float],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate quality against a specific gate."""
        with self.lock:
            if gate_id not in self.quality_gates:
                raise ValueError(f"Gate {gate_id} not found")

            gate = self.quality_gates[gate_id]

            # Convert string keys to QualityDimension enums
            dimension_data = {}
            for key, value in quality_data.items():
                try:
                    dimension = QualityDimension(key)
                    dimension_data[dimension] = value
                except ValueError:
                    self.logger.warning(f"Unknown quality dimension: {key}")

            # Evaluate
            result = gate.evaluate(dimension_data, context)

            # Store in memory integration
            self.memory_integration.integrate_memory(
                MemoryType.QUALITY_METRICS,
                {
                    "gate_id": gate_id,
                    "evaluation_result": result,
                    "quality_data": quality_data,
                    "context": context,
                },
                source_system="adaptive_quality_gates",
            )

            # Store in quality memory
            self.quality_memory.store_quality_metrics(
                f"gate_evaluation_{gate_id}_{datetime.now().isoformat()}",
                {
                    "gate_id": gate_id,
                    "domain": gate.domain.value,
                    "initial_quality": sum(quality_data.values()) / len(quality_data),
                    "enhanced_quality": result["final_score"],
                    "improvement_percentage": max(
                        0,
                        (
                            result["final_score"]
                            - sum(quality_data.values()) / len(quality_data)
                        )
                        * 100,
                    ),
                    "processing_time": 0.1,
                    "evaluation_passed": result["gate_status"] == GateStatus.OPEN.value,
                },
            )

            return result

    def get_domain_gates(self, domain: DomainType) -> list[QualityGate]:
        """Get all gates for a specific domain."""
        with self.lock:
            gate_ids = self.domain_gates.get(domain, [])
            return [
                self.quality_gates[gate_id]
                for gate_id in gate_ids
                if gate_id in self.quality_gates
            ]

    def adapt_all_gates(
        self, performance_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Adapt thresholds for all gates based on performance data."""
        if performance_data is None:
            performance_data = self._collect_performance_data()

        adaptation_results = {
            "adapted_gates": 0,
            "failed_adaptations": 0,
            "gate_results": {},
        }

        with self.lock:
            for gate_id, gate in self.quality_gates.items():
                try:
                    # Get domain-specific performance data
                    domain_performance = performance_data.get("domains", {}).get(
                        gate.domain.value, performance_data
                    )

                    # Adapt thresholds
                    gate.adapt_thresholds(domain_performance)
                    adaptation_results["adapted_gates"] += 1
                    adaptation_results["gate_results"][gate_id] = {
                        "success": True,
                        "new_average_score": gate.average_score,
                        "success_rate": gate.success_rate,
                    }

                except Exception as e:
                    self.logger.error(f"Failed to adapt gate {gate_id}: {str(e)}")
                    adaptation_results["failed_adaptations"] += 1
                    adaptation_results["gate_results"][gate_id] = {
                        "success": False,
                        "error": str(e),
                    }

        self.logger.info(f"Gate adaptation completed: {adaptation_results}")
        return adaptation_results

    def _collect_performance_data(self) -> dict[str, Any]:
        """Collect performance data from various sources."""
        performance_data = {
            "overall_performance": 0.7,
            "recent_success_rate": 0.7,
            "system_performance": 0.7,
            "user_satisfaction": 0.7,
            "domains": {},
        }

        # Get data from memory integration
        quality_memories = self.memory_integration.retrieve_memories(
            {
                "memory_type": "quality_metrics",
                "time_range": {
                    "start": datetime.now() - timedelta(days=7),
                    "end": datetime.now(),
                },
            },
            limit=100,
        )

        if quality_memories:
            # Calculate overall metrics
            success_count = sum(
                1
                for memory in quality_memories
                if memory.primary_data.get("evaluation_result", {}).get(
                    "evaluation_passed", False
                )
            )
            performance_data["recent_success_rate"] = success_count / len(
                quality_memories
            )

            # Calculate average improvements
            improvements = [
                memory.primary_data.get("improvement_percentage", 0)
                for memory in quality_memories
            ]
            performance_data["overall_performance"] = (
                sum(improvements) / len(improvements) / 100
            )

            # Domain-specific metrics
            domain_metrics = defaultdict(list)
            for memory in quality_memories:
                domain = memory.primary_data.get("domain", "unknown")
                improvement = memory.primary_data.get("improvement_percentage", 0)
                domain_metrics[domain].append(improvement)

            for domain, improvements in domain_metrics.items():
                if improvements:
                    performance_data["domains"][domain] = {
                        "recent_success_rate": sum(improvements)
                        / len(improvements)
                        / 100,
                        "system_performance": performance_data["overall_performance"],
                        "user_satisfaction": performance_data["user_satisfaction"],
                    }

        # Get performance data from quality memory
        for domain in DomainType:
            domain_stats = self.quality_memory.get_domain_performance(domain)
            if domain_stats["total_sessions"] > 0:
                performance_data["domains"][domain.value] = {
                    "recent_success_rate": domain_stats["average_improvement"] / 100,
                    "system_performance": performance_data["overall_performance"],
                    "user_satisfaction": performance_data["user_satisfaction"],
                }

        return performance_data

    def get_gate_statistics(
        self, gate_id: str | None = None
    ) -> Union[dict[str, Any], list[dict[str, Any]]]:
        """Get statistics for specific gate or all gates."""
        with self.lock:
            if gate_id:
                if gate_id not in self.quality_gates:
                    raise ValueError(f"Gate {gate_id} not found")
                return self.quality_gates[gate_id].get_statistics()
            else:
                return [gate.get_statistics() for gate in self.quality_gates.values()]

    def get_system_overview(self) -> dict[str, Any]:
        """Get comprehensive system overview."""
        with self.lock:
            overview = {
                "total_gates": len(self.quality_gates),
                "gates_by_domain": {
                    domain.value: len(gates)
                    for domain, gates in self.domain_gates.items()
                },
                "gate_statuses": defaultdict(int),
                "adaptation_strategies": defaultdict(int),
                "performance_summary": {
                    "overall_success_rate": 0.0,
                    "average_score": 0.0,
                    "total_evaluations": 0,
                },
            }

            # Aggregate gate statistics
            total_evaluations = 0
            total_success_rate = 0.0
            total_average_score = 0.0

            for gate in self.quality_gates.values():
                overview["gate_statuses"][gate.status.value] += 1
                overview["adaptation_strategies"][gate.adaptation_strategy.value] += 1

                total_evaluations += len(gate.evaluation_history)
                total_success_rate += gate.success_rate
                total_average_score += gate.average_score

            # Calculate averages
            if self.quality_gates:
                overview["performance_summary"]["overall_success_rate"] = (
                    total_success_rate / len(self.quality_gates)
                )
                overview["performance_summary"]["average_score"] = (
                    total_average_score / len(self.quality_gates)
                )
                overview["performance_summary"]["total_evaluations"] = total_evaluations

            # Convert defaultdicts to regular dicts
            overview["gate_statuses"] = dict(overview["gate_statuses"])
            overview["adaptation_strategies"] = dict(overview["adaptation_strategies"])

            return overview

    def _start_background_tasks(self) -> None:
        """Start background monitoring and adaptation tasks."""
        # Performance monitoring thread
        monitoring_thread = threading.Thread(
            target=self._background_performance_monitoring, daemon=True
        )
        monitoring_thread.start()
        self._background_threads.append(monitoring_thread)

        # Threshold adaptation thread
        adaptation_thread = threading.Thread(
            target=self._background_threshold_adaptation, daemon=True
        )
        adaptation_thread.start()
        self._background_threads.append(adaptation_thread)

        # Alerting thread
        alerting_thread = threading.Thread(
            target=self._background_alerting, daemon=True
        )
        alerting_thread.start()
        self._background_threads.append(alerting_thread)

    def _background_performance_monitoring(self) -> None:
        """Background performance monitoring."""
        while not self._shutdown:
            try:
                # Collect performance data
                performance_data = self._collect_performance_data()

                # Check for performance issues
                if (
                    performance_data["recent_success_rate"]
                    < self.performance_monitoring["alert_thresholds"][
                        "low_success_rate"
                    ]
                ):
                    self.logger.warning(
                        f"Low success rate detected: {performance_data['recent_success_rate']:.2f}"
                    )

                threading.Event().wait(
                    timeout=self.performance_monitoring[
                        "evaluation_frequency"
                    ].total_seconds()
                )

            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {str(e)}")
                threading.Event().wait(timeout=60)

    def _background_threshold_adaptation(self) -> None:
        """Background threshold adaptation."""
        while not self._shutdown:
            try:
                # Adapt all gates
                self.adapt_all_gates()

                threading.Event().wait(
                    timeout=self.performance_monitoring[
                        "adaptation_frequency"
                    ].total_seconds()
                )

            except Exception as e:
                self.logger.error(f"Error in threshold adaptation: {str(e)}")
                threading.Event().wait(timeout=300)

    def _background_alerting(self) -> None:
        """Background alerting for gate issues."""
        while not self._shutdown:
            try:
                # Check for issues in all gates
                for gate in self.quality_gates.values():
                    stats = gate.get_statistics()

                    # Check for high volatility
                    for dimension_stats in stats["dimension_thresholds"].values():
                        if (
                            dimension_stats["volatility"]
                            > self.performance_monitoring["alert_thresholds"][
                                "high_volatility"
                            ]
                        ):
                            self.logger.warning(
                                f"High volatility detected in gate {gate.gate_id}, dimension {dimension_stats}"
                            )

                    # Check for stagnation
                    if len(gate.evaluation_history) > 50:
                        recent_success_rate = (
                            sum(
                                1
                                for eval in list(gate.evaluation_history)[-20:]
                                if eval["gate_status"] == GateStatus.OPEN.value
                            )
                            / 20
                        )
                        overall_success_rate = gate.success_rate

                        if (
                            abs(recent_success_rate - overall_success_rate)
                            < self.performance_monitoring["alert_thresholds"][
                                "stagnation_threshold"
                            ]
                        ):
                            self.logger.warning(
                                f"Potential stagnation detected in gate {gate.gate_id}"
                            )

                threading.Event().wait(timeout=1800)  # 30 minutes

            except Exception as e:
                self.logger.error(f"Error in background alerting: {str(e)}")
                threading.Event().wait(timeout=300)

    def shutdown(self) -> None:
        """Shutdown the adaptive quality gates system gracefully."""
        self._shutdown = True

        # Wait for background threads to finish
        for thread in self._background_threads:
            if thread.is_alive():
                thread.join(timeout=10)

        # Final adaptation
        self.adapt_all_gates()

        self.logger.info("Adaptive Quality Gates system shutdown complete")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except:
            pass
