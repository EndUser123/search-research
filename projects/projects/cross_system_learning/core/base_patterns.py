"""
Base pattern definitions and data structures for cross-system learning.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DomainType(Enum):
    """Supported enhancement domains."""

    SOFTWARE_DEVELOPMENT = "software_development"
    DATA_ANALYSIS = "data_analysis"
    TROUBLESHOOTING = "troubleshooting"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    DESIGN = "design"
    STRATEGY = "strategy"
    EDUCATION = "education"


class PatternStatus(Enum):
    """Pattern lifecycle status."""

    EMERGING = "emerging"
    VALIDATED = "validated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class DomainContext:
    """Context information for domain-specific patterns."""

    domain: DomainType
    subdomain: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    related_domains: set[DomainType] = field(default_factory=set)


@dataclass
class QualityMetrics:
    """Quality assessment metrics for enhancement patterns."""

    success_rate: float = 0.0  # 0.0 to 1.0
    average_improvement: float = 0.0  # Percentage improvement
    reliability_score: float = 0.0  # Consistency of results
    adaptability_score: float = 0.0  # How well it adapts to different contexts
    efficiency_score: float = 0.0  # Resource efficiency
    user_satisfaction: float = 0.0  # User feedback scores
    error_reduction: float = 0.0  # Reduction in error rates
    novelty_score: float = 0.0  # How novel the pattern is
    transferability: float = 0.0  # How well it transfers between domains

    # Historical performance
    total_applications: int = 0
    successful_applications: int = 0
    failed_applications: int = 0

    # Temporal metrics
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def calculate_overall_score(self) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            "success_rate": 0.25,
            "average_improvement": 0.20,
            "reliability_score": 0.15,
            "adaptability_score": 0.15,
            "efficiency_score": 0.10,
            "transferability": 0.15,
        }

        score = sum(
            getattr(self, metric) * weight for metric, weight in weights.items()
        )
        return min(1.0, max(0.0, score))

    def update_success(self, improvement_pct: float = 0.0) -> None:
        """Update metrics after a successful application."""
        self.total_applications += 1
        self.successful_applications += 1
        self.success_rate = self.successful_applications / self.total_applications

        # Update average improvement
        if improvement_pct > 0:
            current_total = self.average_improvement * (
                self.successful_applications - 1
            )
            self.average_improvement = (
                current_total + improvement_pct
            ) / self.successful_applications

        self.last_updated = datetime.now()

    def update_failure(self) -> None:
        """Update metrics after a failed application."""
        self.total_applications += 1
        self.failed_applications += 1
        self.success_rate = self.successful_applications / self.total_applications
        self.last_updated = datetime.now()


@dataclass
class BasePattern(ABC):
    """Base class for all enhancement patterns."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern_type: str = ""
    status: PatternStatus = PatternStatus.EMERGING
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    domain_context: DomainContext = field(
        default_factory=lambda: DomainContext(DomainType.SOFTWARE_DEVELOPMENT)
    )

    # Pattern structure
    template: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    transformation_rules: dict[str, Any] = field(default_factory=dict)

    # Relationships
    parent_patterns: list[str] = field(default_factory=list)
    child_patterns: list[str] = field(default_factory=list)
    related_patterns: list[str] = field(default_factory=list)
    competing_patterns: list[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_applied: datetime | None = None
    creator_system: str = ""
    tags: set[str] = field(default_factory=set)

    @abstractmethod
    def apply(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Apply the pattern to input data."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate pattern structure and content."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert pattern to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "status": self.status.value,
            "quality_metrics": {
                "success_rate": self.quality_metrics.success_rate,
                "average_improvement": self.quality_metrics.average_improvement,
                "overall_score": self.quality_metrics.calculate_overall_score(),
                "total_applications": self.quality_metrics.total_applications,
                "last_updated": self.quality_metrics.last_updated.isoformat(),
            },
            "domain_context": {
                "domain": self.domain_context.domain.value,
                "subdomain": self.domain_context.subdomain,
                "metadata": self.domain_context.metadata,
            },
            "template": self.template,
            "created_at": self.created_at.isoformat(),
            "tags": list(self.tags),
        }


@dataclass
class EnhancementPattern(BasePattern):
    """Specific enhancement pattern for prompt improvement."""

    # Enhancement-specific fields
    target_quality_threshold: float = 0.7  # Minimum quality score to trigger
    enhancement_technique: str = ""  # e.g., "DPEF", "CODE_FRAMEWORK", "CLARITY_BOOST"

    # Enhancement parameters
    complexity_adjustment: float = 0.0  # How much complexity to add/remove
    specificity_level: float = 0.5  # How specific the enhancement should be
    context_preservation: float = 0.8  # How much original context to preserve

    # Quality gates
    quality_gates: dict[str, float] = field(default_factory=dict)
    validation_rules: dict[str, Any] = field(default_factory=dict)

    def apply(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Apply enhancement pattern to prompt."""
        original_prompt = input_data.get("prompt", "")

        # Basic template substitution
        enhanced_prompt = self.template.format(
            original_prompt=original_prompt, **self.variables, **input_data
        )

        # Apply transformation rules
        for rule_name, rule_config in self.transformation_rules.items():
            if rule_config.get("enabled", True):
                enhanced_prompt = self._apply_transformation(
                    enhanced_prompt, rule_name, rule_config
                )

        return {
            "enhanced_prompt": enhanced_prompt,
            "pattern_id": self.id,
            "pattern_name": self.name,
            "technique": self.enhancement_technique,
        }

    def _apply_transformation(
        self, text: str, rule_name: str, rule_config: dict[str, Any]
    ) -> str:
        """Apply a specific transformation rule."""
        transformation_type = rule_config.get("type", "")

        if transformation_type == "prepend":
            prefix = rule_config.get("text", "")
            return f"{prefix}\n\n{text}"
        elif transformation_type == "append":
            suffix = rule_config.get("text", "")
            return f"{text}\n\n{suffix}"
        elif transformation_type == "replace":
            old_text = rule_config.get("old_text", "")
            new_text = rule_config.get("new_text", "")
            return text.replace(old_text, new_text)
        elif transformation_type == "wrap":
            wrapper = rule_config.get("wrapper", "")
            return f"{wrapper}\n{text}\n{wrapper}"

        return text

    def validate(self) -> bool:
        """Validate enhancement pattern structure."""
        if not self.template or not self.enhancement_technique:
            return False

        if self.target_quality_threshold < 0.0 or self.target_quality_threshold > 1.0:
            return False

        if self.complexity_adjustment < -1.0 or self.complexity_adjustment > 1.0:
            return False

        return True


@dataclass
class PatternCluster:
    """Cluster of related enhancement patterns."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Cluster composition
    pattern_ids: list[str] = field(default_factory=list)
    domain_focus: DomainType = DomainType.SOFTWARE_DEVELOPMENT

    # Cluster characteristics
    average_success_rate: float = 0.0
    cluster_strength: float = 0.0  # How cohesive the cluster is
    transfer_potential: float = 0.0  # Transfer potential to other domains

    # Optimization
    optimal_usage_sequence: list[str] = field(default_factory=list)
    complementary_patterns: dict[str, float] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_pattern(self, pattern_id: str, compatibility_score: float = 1.0) -> None:
        """Add a pattern to the cluster."""
        if pattern_id not in self.pattern_ids:
            self.pattern_ids.append(pattern_id)
            self.last_updated = datetime.now()

    def calculate_cluster_metrics(
        self, patterns: dict[str, EnhancementPattern]
    ) -> None:
        """Calculate cluster-wide metrics based on constituent patterns."""
        if not self.pattern_ids:
            return

        # Calculate average success rate
        success_rates = [
            patterns[pid].quality_metrics.success_rate
            for pid in self.pattern_ids
            if pid in patterns
        ]

        if success_rates:
            self.average_success_rate = sum(success_rates) / len(success_rates)

        self.last_updated = datetime.now()


class PatternRelationship:
    """Represents relationships between patterns."""

    def __init__(
        self,
        pattern_a_id: str,
        pattern_b_id: str,
        relationship_type: str,
        strength: float = 0.5,
    ):
        self.pattern_a_id = pattern_a_id
        self.pattern_b_id = pattern_b_id
        self.relationship_type = (
            relationship_type  # e.g., "enhances", "complements", "conflicts"
        )
        self.strength = strength  # 0.0 to 1.0
        self.created_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_a_id": self.pattern_a_id,
            "pattern_b_id": self.pattern_b_id,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
        }
