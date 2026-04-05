# SPDX-License-Identifier: MIT
"""Assessors for architectural validation.

This module provides assessor classes for evaluating various quality attributes
of software architectures, including sustainability, maintainability, scalability,
and technical debt.

The main class, SustainabilityAssessor, evaluates multiple dimensions of
architecture sustainability and provides actionable recommendations.
"""

from __future__ import annotations

from typing import Any, Final

from archlint.core import ArchitectureContext, SustainabilityAssessment

__all__ = [
    "SustainabilityAssessor",
]


# Constants for sustainability assessment
# Scores are normalized to 0.0-1.0 range to match SustainabilityAssessment dataclass
MIN_SCORE: Final[float] = 0.0
MAX_SCORE: Final[float] = 1.0

# Score thresholds for risk identification
RISK_THRESHOLD_CRITICAL: Final[float] = 0.50  # Below 50%
RISK_THRESHOLD_MODERATE: Final[float] = 0.70  # Below 70%
RECOMMENDATION_THRESHOLD: Final[float] = 0.80  # Below 80%

# Complexity scoring constants
COMPLEXITY_HIGH_THRESHOLD: Final[float] = 20.0
COMPLEXITY_MODERATE_THRESHOLD: Final[float] = 10.0
COMPLEXITY_LOW_THRESHOLD: Final[float] = 5.0
COMPLEXITY_HIGH_PENALTY: Final[float] = 0.3
COMPLEXITY_MODERATE_PENALTY: Final[float] = 0.1
COMPLEXITY_LOW_BONUS: Final[float] = 0.3


def _safe_float(value: Any, default: float = 0.5) -> float:
    """Safely convert a value to float, handling MagicMock and other non-numeric types.

    Args:
        value: The value to convert to float
        default: Default value if conversion fails

    Returns:
        float representation of value, or default if conversion fails
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _adjust_score_for_cyclomatic_complexity(
    base_score: float, context: ArchitectureContext
) -> float:
    """Adjust a base score based on cyclomatic complexity.

    Shared logic for scalability and technical_debt assessment.

    Args:
        base_score: Starting score before complexity adjustment
        context: ArchitectureContext containing complexity_metrics

    Returns:
        Adjusted score between 0.0 and 1.0
    """
    score = base_score
    complexity_metrics = getattr(context, "complexity_metrics", {}) or {}
    if complexity_metrics:
        complexity = _safe_float(complexity_metrics.get("cyclomatic_complexity", 0), 0)
        if complexity > COMPLEXITY_HIGH_THRESHOLD:
            score -= COMPLEXITY_HIGH_PENALTY
        elif complexity > COMPLEXITY_MODERATE_THRESHOLD:
            score -= COMPLEXITY_MODERATE_PENALTY
        elif complexity < COMPLEXITY_LOW_THRESHOLD:
            score += COMPLEXITY_LOW_BONUS

    return max(MIN_SCORE, min(MAX_SCORE, score))
    """Safely convert a value to float, handling MagicMock and other non-numeric types.

    Args:
        value: The value to convert to float
        default: Default value if conversion fails

    Returns:
        float representation of value, or default if conversion fails
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class SustainabilityAssessor:
    """Assesses sustainability aspects of software architecture.

    The SustainabilityAssessor evaluates multiple dimensions of architecture
    sustainability including maintainability, scalability, knowledge transfer,
    and technical debt. It aggregates these individual assessments into an
    overall sustainability score and provides actionable recommendations.

    The assessor uses the provided ArchitectureContext to analyze the
    architecture and generate comprehensive sustainability metrics.

    Example:
        >>> context = ArchitectureContext(
        ...     architecture_id="arch-001",
        ...     name="My Architecture",
        ...     description="Example architecture"
        ... )
        >>> assessor = SustainabilityAssessor(context)
        >>> assessment = assessor.assess_sustainability()
        >>> print(f"Overall score: {assessment.overall_score}")
    """

    def __init__(self, context: ArchitectureContext) -> None:
        """
        Initialize SustainabilityAssessor with architecture context.

        Args:
            context: Architecture context containing information about the
                    architecture to assess, including components, dependencies,
                    patterns, and metrics.
        """
        self.context: ArchitectureContext = context

    def assess(self, context: ArchitectureContext) -> SustainabilityAssessment:
        """
        Perform sustainability assessment (alias for assess_sustainability).

        This method provides the assess() interface expected by ArchitecturalValidator.
        It accepts a context parameter for dependency injection pattern.

        Args:
            context: ArchitectureContext containing architecture information

        Returns:
            SustainabilityAssessment: Complete assessment containing all
                                    individual scores, overall score, and
                                    recommendations for improvement.
        """
        return self.assess_sustainability(context)

    def assess_sustainability(
        self, context: ArchitectureContext | None = None
    ) -> SustainabilityAssessment:
        """
        Perform comprehensive sustainability assessment of the architecture.

        This method evaluates all sustainability dimensions (maintainability,
        scalability, knowledge transfer, and technical debt) and aggregates
        them into an overall score. It also identifies risk factors and
        generates actionable recommendations.

        Args:
            context: Optional ArchitectureContext containing architecture information.
                    If not provided, uses self.context from __init__.

        Returns:
            SustainabilityAssessment: Complete assessment containing all
                                    individual scores, overall score, and
                                    recommendations for improvement.
        """
        # Use passed context if provided, otherwise fall back to self.context
        ctx = context if context is not None else self.context

        maintainability_score = self._assess_maintainability(ctx)
        scalability_score = self._assess_scalability(ctx)
        knowledge_transfer_score = self._assess_knowledge_transfer(ctx)
        technical_debt_score = self._assess_technical_debt(ctx)

        scores: dict[str, float] = {
            "maintainability": maintainability_score,
            "scalability": scalability_score,
            "knowledge_transfer": knowledge_transfer_score,
            "technical_debt": technical_debt_score,
        }

        overall_score = self._calculate_overall_score(scores)
        risk_factors = self._identify_risk_factors(scores)
        recommendations = self._generate_recommendations(scores)

        return SustainabilityAssessment(
            maintainability_score=maintainability_score,
            scalability_score=scalability_score,
            knowledge_transfer_score=knowledge_transfer_score,
            technical_debt_score=technical_debt_score,
            overall_score=overall_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
        )

    def _assess_maintainability(self, context: ArchitectureContext) -> float:
        """
        Assess the maintainability dimension of the architecture.

        Maintainability evaluates how easily the architecture can be modified,
        extended, or corrected. This includes consideration of code organization,
        documentation quality, and adherence to design principles.

        Args:
            context: ArchitectureContext to assess.

        Returns:
            A score between 0.0 and 1.0 representing maintainability,
            where higher values indicate better maintainability.
        """
        score = 0.2

        test_coverage = _safe_float(getattr(context, "test_coverage", None), 0)
        if test_coverage > 0:
            score += test_coverage * 0.5

        doc_coverage = _safe_float(getattr(context, "documentation_coverage", None), 0)
        if doc_coverage > 0:
            score += doc_coverage * 0.3

        return max(MIN_SCORE, min(MAX_SCORE, score))

    def _assess_scalability(self, context: ArchitectureContext) -> float:
        """
        Assess the scalability dimension of the architecture.

        Scalability evaluates the architecture's ability to handle growth
        in users, data volume, or transaction load without significant
        architectural changes.

        Args:
            context: ArchitectureContext to assess.

        Returns:
            A score between 0.0 and 1.0 representing scalability,
            where higher values indicate better scalability.
        """
        return _adjust_score_for_cyclomatic_complexity(0.5, context)

    def _assess_knowledge_transfer(self, context: ArchitectureContext) -> float:
        """
        Assess the knowledge transfer capability of the architecture.

        Knowledge transfer evaluates how easily team members can understand
        and work with the architecture. This includes clarity of design
        patterns, documentation, and code readability.

        Args:
            context: ArchitectureContext to assess.

        Returns:
            A score between 0.0 and 1.0 representing knowledge transfer
            capability, where higher values indicate easier knowledge transfer.
        """
        score = 0.3

        doc_coverage = _safe_float(getattr(context, "documentation_coverage", None), 0)
        if doc_coverage > 0:
            score += doc_coverage * 0.5

        tech_stack = getattr(context, "technology_stack", None) or []
        if tech_stack:
            score += 0.2

        return max(MIN_SCORE, min(MAX_SCORE, score))

    def _assess_technical_debt(self, context: ArchitectureContext) -> float:
        """
        Assess the technical debt dimension of the architecture.

        Technical debt evaluates the accumulated cost of additional rework
        caused by choosing an easy or fast solution now instead of using
        a better approach that would take longer.

        Args:
            context: ArchitectureContext to assess.

        Returns:
            A score between 0.0 and 1.0 representing technical debt health,
            where higher values indicate lower technical debt.
        """
        # Start with complexity-adjusted score (different base than scalability)
        score = _adjust_score_for_cyclomatic_complexity(0.6, context)

        # Additional penalties for dependency issues
        dependencies = getattr(context, "dependencies", None) or {}
        if dependencies:
            # Dependencies can be a dict or list
            if isinstance(dependencies, dict):
                unknown_deps = dependencies.get("unknown", [])
                if unknown_deps:
                    score -= 0.2
            elif isinstance(dependencies, list):
                # List of dependencies - check if it's not empty (may indicate coupling)
                if len(dependencies) > 0:
                    score -= 0.1

        return max(MIN_SCORE, min(MAX_SCORE, score))

    def _calculate_overall_score(self, scores: dict[str, float]) -> float:
        """
        Calculate the overall sustainability score from individual dimension scores.

        The overall score is computed as the arithmetic mean of all individual
        assessment scores.

        Args:
            scores: Dictionary mapping dimension names to their scores.

        Returns:
            The overall sustainability score as a float between 0.0 and 1.0.
        """
        return sum(scores.values()) / len(scores)

    def _identify_risk_factors(self, scores: dict[str, float]) -> list[str]:
        """
        Identify risk factors based on assessment scores and architecture context.

        Risk factors are areas of concern that could negatively impact the
        architecture's sustainability or require immediate attention.

        Args:
            scores: Dictionary mapping dimension names to their assessment scores.

        Returns:
            A list of strings describing identified risk factors. Returns an
            empty list if no significant risks are identified.
        """
        risk_factors: list[str] = []

        for dimension, score in scores.items():
            if score < RISK_THRESHOLD_CRITICAL:
                risk_factors.append(
                    f"Low {dimension} score ({score:.2f}): immediate attention required"
                )
            elif score < RISK_THRESHOLD_MODERATE:
                risk_factors.append(
                    f"Moderate {dimension} score ({score:.2f}): improvement recommended"
                )

        return risk_factors

    def _generate_recommendations(self, scores: dict[str, float]) -> list[str]:
        """
        Generate actionable recommendations based on assessment scores.

        Recommendations are prioritized based on the lowest-scoring dimensions
        to guide improvement efforts effectively.

        Args:
            scores: Dictionary mapping dimension names to their assessment scores.

        Returns:
            A list of strings containing actionable recommendations for
            improving the architecture's sustainability.
        """
        recommendations: list[str] = []

        # Find the lowest-scoring dimension
        lowest_dimension = min(scores.items(), key=lambda item: item[1])

        if lowest_dimension[1] < RECOMMENDATION_THRESHOLD:
            dimension_name, dimension_score = lowest_dimension
            recommendations.append(
                f"Focus on improving {dimension_name}: "
                f"current score is {dimension_score:.2f}"
            )

        return recommendations
