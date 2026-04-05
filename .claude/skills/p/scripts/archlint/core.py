# SPDX-License-Identifier: MIT
"""Core dataclasses for architectural-validator.

This module defines the fundamental data structures used for
architectural validation, compliance checking, and sustainability assessment.

The module provides:
- Enums for compliance levels, sustainability scores, architectural patterns, and severity levels
- Dataclasses for architecture context, compliance violations, sustainability assessments, and validation results
- The ArchitecturalValidator class for coordinating validation workflows

Example:
    >>> from archlint.core import ArchitecturalValidator, ArchitectureContext
    >>> validator = ArchitecturalValidator()
    >>> context = ArchitectureContext(
    ...     architecture_id="arch-001",
    ...     name="My Architecture",
    ...     description="A sample architecture"
    ... )
    >>> result = validator.validate_architecture(context)
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "ComplianceLevel",
    "SustainabilityScore",
    "ArchitecturalPattern",
    "SeverityLevel",
    "ArchitectureContext",
    "ComplianceViolation",
    "SustainabilityAssessment",
    "ArchitectureValidationResult",
    "ArchitecturalValidator",
]


class ComplianceLevel(Enum):
    """Compliance levels for architectural validation.

    This enum defines the possible compliance states that an architecture
    can have after validation. The levels range from fully compliant to
    critical violation, indicating the severity of any compliance issues found.

    Attributes:
        COMPLIANT: Architecture fully complies with all validation rules
        PARTIALLY_COMPLIANT: Architecture has minor compliance issues
        NON_COMPLIANT: Architecture has significant compliance violations
        CRITICAL_VIOLATION: Architecture has critical compliance issues that must be addressed
    """

    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    CRITICAL_VIOLATION = "CRITICAL_VIOLATION"

    def __str__(self) -> str:
        return self.value


class SustainabilityScore(Enum):
    """Sustainability score levels for architecture assessment.

    This enum defines the sustainability categories for an architecture,
    reflecting its long-term viability, maintainability, and adaptability.

    Attributes:
        EXCELLENT: Architecture demonstrates excellent sustainability practices
        GOOD: Architecture has good sustainability with minor improvements possible
        ADEQUATE: Architecture meets minimum sustainability requirements
        POOR: Architecture has significant sustainability concerns
        CRITICAL: Architecture requires immediate attention to sustainability issues
    """

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    ADEQUATE = "ADEQUATE"
    POOR = "POOR"
    CRITICAL = "CRITICAL"

    def __str__(self) -> str:
        return self.value


class ArchitecturalPattern(Enum):
    """Common architectural patterns recognized by the validator.

    This enum defines standard architectural patterns that can be identified
    and validated. Each pattern represents a different approach to organizing
    software architecture.

    Attributes:
        LAYERED: Traditional layered architecture with separation of concerns
        MICROSERVICES: Distributed architecture with independently deployable services
        EVENT_DRIVEN: Architecture centered around event production and consumption
        HEXAGONAL: Ports and adapters architecture for external interface isolation
        CLEAN_ARCHITECTURE: Domain-driven design with clear boundaries
        MONOLITH: Single deployment unit architecture
        PLUGIN: Plugin-based architecture for extensibility
        REPOSITORY: Repository pattern for data access abstraction
        STRATEGY: Strategy pattern for algorithm encapsulation
    """

    LAYERED = "LAYERED"
    MICROSERVICES = "MICROSERVICES"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    HEXAGONAL = "HEXAGONAL"
    CLEAN_ARCHITECTURE = "CLEAN_ARCHITECTURE"
    MONOLITH = "MONOLITH"
    PLUGIN = "PLUGIN"
    REPOSITORY = "REPOSITORY"
    STRATEGY = "STRATEGY"

    def __str__(self) -> str:
        return self.value


class SeverityLevel(Enum):
    """Severity levels for compliance violations.

    This enum defines the severity classification for compliance violations
    found during architectural validation. Severity levels help prioritize
    remediation efforts.

    Attributes:
        CRITICAL: Immediate action required; system may be non-functional
        HIGH: Important issues that should be addressed soon
        MEDIUM: Moderate issues that should be addressed in next iteration
        LOW: Minor issues that can be addressed when convenient
        INFO: Informational notes for consideration, not violations
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ArchitectureContext:
    """Context information about the architecture being validated.

    This dataclass encapsulates the basic metadata and contextual information
    needed to perform architectural validation. It serves as the input to
    validation operations.

    Attributes:
        architecture_id: Unique identifier for the architecture instance
        name: Human-readable name of the architecture
        description: Detailed description of the architecture's purpose and scope
        metadata: Additional key-value pairs for extensible context information
        project_structure: Dictionary representing the project structure
        technology_stack: List of technologies used in the architecture
        dependencies: Dictionary of module dependencies
        design_patterns: List of architectural patterns identified
        scale_requirements: Scale tier (small, medium, large, enterprise)
        maintenance_team_size: Number of people maintaining the architecture
        documentation_coverage: Documentation quality score (0-1)
        test_coverage: Test coverage percentage (0-1)
        complexity_metrics: Dictionary of complexity measurements
        knowledge_preservation: Knowledge management effectiveness data

    Example:
        >>> context = ArchitectureContext(
        ...     architecture_id="arch-001",
        ...     name="E-commerce Platform",
        ...     description="Microservices-based e-commerce system",
        ...     metadata={"version": "2.0", "team": "platform-team"}
        ... )
    """

    architecture_id: str = ""
    name: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    project_structure: dict[str, Any] = field(default_factory=dict)
    technology_stack: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    design_patterns: list[str] = field(default_factory=list)
    scale_requirements: str = "medium"
    maintenance_team_size: int = 5
    documentation_coverage: float = 0.5
    test_coverage: float = 0.5
    complexity_metrics: dict[str, float] = field(default_factory=dict)
    knowledge_preservation: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate field values after initialization.

        Raises:
            ValueError: If documentation_coverage or test_coverage is not in [0.0, 1.0]
        """
        if not 0.0 <= self.documentation_coverage <= 1.0:
            raise ValueError(
                f"documentation_coverage must be between 0 and 1, got {self.documentation_coverage}"
            )
        if not 0.0 <= self.test_coverage <= 1.0:
            raise ValueError(
                f"test_coverage must be between 0 and 1, got {self.test_coverage}"
            )


@dataclass
class ComplianceViolation:
    """Represents a single compliance violation found during validation.

    This dataclass captures all relevant information about a compliance violation,
    including what went wrong, where it occurred, and how to fix it.

    Attributes:
        rule_id: Unique identifier for the compliance rule that was violated
        severity: SeverityLevel indicating the seriousness of the violation
        description: Human-readable description of the violation
        location: Code or architecture location where the violation was found
        recommendation: Suggested fix or remediation approach
        impact_score: Numerical impact assessment from 0.0 (minimal) to 1.0 (critical)

    Raises:
        ValueError: If impact_score is not between 0.0 and 1.0

    Example:
        >>> violation = ComplianceViolation(
        ...     rule_id="ARCH-001",
        ...     severity=SeverityLevel.HIGH,
        ...     description="Business logic directly accesses database",
        ...     location="services/user_service.py:45",
        ...     recommendation="Move database access to repository layer",
        ...     impact_score=0.8
        ... )
    """

    rule_id: str
    severity: SeverityLevel
    description: str
    location: str
    recommendation: str
    impact_score: float

    def __post_init__(self) -> None:
        """Validate field values after initialization.

        Raises:
            ValueError: If impact_score is not in the valid range [0.0, 1.0]
        """
        if not 0.0 <= self.impact_score <= 1.0:
            raise ValueError(
                f"impact_score must be between 0 and 1, got {self.impact_score}"
            )


@dataclass
class SustainabilityAssessment:
    """Assessment of architecture sustainability across multiple dimensions.

    This dataclass provides a comprehensive evaluation of an architecture's
    sustainability, measuring its long-term viability and maintainability.

    Attributes:
        overall_score: Aggregate sustainability score from 0.0 (poor) to 1.0 (excellent)
        maintainability_score: Ease of maintenance and modification (0.0 to 1.0)
        scalability_score: Ability to handle growth (0.0 to 1.0)
        knowledge_transfer_score: Ease of knowledge transfer to new team members (0.0 to 1.0)
        technical_debt_score: Amount of technical debt accumulated (0.0 = low, 1.0 = high)
        risk_factors: List of identified risk factors as strings
        recommendations: List of actionable improvement recommendations

    Raises:
        ValueError: If any score is not in the valid range [0.0, 1.0]

    Example:
        >>> assessment = SustainabilityAssessment(
        ...     overall_score=0.75,
        ...     maintainability_score=0.80,
        ...     scalability_score=0.70,
        ...     knowledge_transfer_score=0.65,
        ...     technical_debt_score=0.30,
        ...     risk_factors=["high_complexity", "low_documentation"],
        ...     recommendations=["improve documentation", "reduce complexity"]
        ... )
    """

    overall_score: float
    maintainability_score: float
    scalability_score: float
    knowledge_transfer_score: float
    technical_debt_score: float
    risk_factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate all score fields are within valid range.

        Raises:
            ValueError: If any score is not in the valid range [0.0, 1.0]
        """
        for field_name in (
            "overall_score",
            "maintainability_score",
            "scalability_score",
            "knowledge_transfer_score",
            "technical_debt_score",
        ):
            score = getattr(self, field_name)
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1, got {score}")


@dataclass
class ArchitectureValidationResult:
    """Complete result of architectural validation.

    This dataclass encapsulates the complete output of an architectural
    validation process, including scores, violations, and recommendations.

    Attributes:
        compliance_level: Compliance level as a string (e.g., "FULL", "HIGH", "MODERATE")
        compliance_violations: List of ComplianceViolation objects found during validation
        sustainability_assessment: SustainabilityAssessment object with detailed metrics
        scalability_analysis: Dictionary containing scalability analysis results
        maintainability_analysis: Dictionary containing maintainability analysis results
        knowledge_preservation_analysis: Dictionary containing knowledge preservation analysis
        overall_score: Combined score from 0.0 to 1.0 considering all factors
        actionable_recommendations: List of actionable improvement recommendations

    Example:
        >>> result = ArchitectureValidationResult(
        ...     compliance_level="HIGH",
        ...     compliance_violations=[],
        ...     sustainability_assessment=SustainabilityAssessment(overall_score=0.8, ...),
        ...     scalability_analysis={"score": 0.7, "bottlenecks": []},
        ...     maintainability_analysis={"score": 0.8, "issues": []},
        ...     knowledge_preservation_analysis={"score": 0.65, "gaps": []},
        ...     overall_score=0.75,
        ...     actionable_recommendations=["Consider adding caching layer"]
        ... )
    """

    compliance_level: str
    compliance_violations: list[ComplianceViolation]
    sustainability_assessment: SustainabilityAssessment
    scalability_analysis: dict[str, Any]
    maintainability_analysis: dict[str, Any]
    knowledge_preservation_analysis: dict[str, Any]
    overall_score: float
    actionable_recommendations: list[str]


class ArchitecturalValidator:
    """Main architectural validator class.

    This class orchestrates the validation of software architectures by
    coordinating compliance checks and sustainability assessments. It serves
    as the primary entry point for architectural validation operations.

    The validator uses dependency injection, accepting optional compliance
    validator and sustainability assessor components. When these are not
    provided, the validator returns default passing scores.

    Example:
        >>> validator = ArchitecturalValidator(
        ...     compliance_validator=my_compliance_checker,
        ...     sustainability_assessor=my_sustainability_checker
        ... )
        >>> context = ArchitectureContext(
        ...     architecture_id="arch-001",
        ...     name="My Architecture",
        ...     description="Test architecture"
        ... )
        >>> result = validator.validate_architecture(context)
        >>> summary = validator.get_validation_summary(result)
    """

    def __init__(
        self,
        compliance_validator: Any | None = None,
        sustainability_assessor: Any | None = None,
    ) -> None:
        """Initialize ArchitecturalValidator with dependencies.

        Args:
            compliance_validator: Optional validator for compliance checks.
                Must implement a validate() method that accepts ArchitectureContext.
            sustainability_assessor: Optional assessor for sustainability metrics.
                Must implement an assess() method that accepts ArchitectureContext.
        """
        self.compliance_validator: Any | None = compliance_validator
        self.sustainability_assessor: Any | None = sustainability_assessor
        self.validation_counter: int = 0
        self._validation_lock = threading.Lock()

    def _is_valid_numeric_score(self, value: Any) -> bool:
        """Check if value is a valid numeric score (int or float, not MagicMock).

        Args:
            value: Value to validate

        Returns:
            True if value is int or float and not MagicMock, False otherwise
        """
        if not isinstance(value, (int, float)):
            return False
        # Reject MagicMock explicitly (can pass isinstance in some Python versions)
        if type(value).__name__ == "MagicMock":
            return False
        return True

    def validate_architecture(
        self, context: ArchitectureContext
    ) -> ArchitectureValidationResult:
        """Validate architecture and return comprehensive result.

        This method orchestrates the validation process by calling the
        compliance validator and sustainability assessor (if provided),
        aggregating their results into a comprehensive validation result.

        Args:
            context: ArchitectureContext containing the architecture to validate

        Returns:
            ArchitectureValidationResult with validation details including scores,
            violations, and recommendations

        Note:
            If compliance_validator is not provided, defaults to compliant with score 1.0.
            If sustainability_assessor is not provided, defaults to score 1.0.
        """
        # Increment validation counter (thread-safe)
        with self._validation_lock:
            self.validation_counter += 1

        # Call compliance validator if available
        compliance_result = (
            self.compliance_validator.validate(context)
            if self.compliance_validator
            else None
        )

        # Call sustainability assessor if available
        sustainability_result = (
            self.sustainability_assessor.assess(context)
            if self.sustainability_assessor
            else None
        )

        # Extract data from compliance result
        if compliance_result:
            compliance_score = getattr(compliance_result, "score", None)
            # EDGE-001 FIX: Reject MagicMock or invalid types explicitly
            if not self._is_valid_numeric_score(compliance_score):
                raise TypeError(
                    f"compliance_score must be int or float, got {type(compliance_score)}"
                )
            raw_violations = (
                compliance_result.violations
                if hasattr(compliance_result, "violations")
                else []
            )
            # Convert violation dicts to ComplianceViolation objects
            violations = self._convert_to_compliance_violations(raw_violations)
        else:
            # FAIL-FAST: No validator configured means validation cannot pass
            compliance_score = 0.0
            violations = []

        # Determine compliance level from score using ComplianceLevel enum
        # COMPLIANCE-001: Check violation count when determining compliance level
        # Having violations should result in PARTIALLY_COMPLIANT or NON_COMPLIANT, not COMPLIANT
        if compliance_score >= 0.9:
            if len(violations) == 0:
                compliance_level = ComplianceLevel.COMPLIANT.value
            else:
                # Downgrade from COMPLIANT to PARTIALLY_COMPLIANT if there are violations
                compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT.value
        elif compliance_score >= 0.7:
            compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT.value
        elif compliance_score >= 0.5:
            compliance_level = ComplianceLevel.NON_COMPLIANT.value
        else:
            compliance_level = ComplianceLevel.CRITICAL_VIOLATION.value

        # Get sustainability assessment
        if sustainability_result:
            sustainability_assessment = (
                sustainability_result
                if isinstance(sustainability_result, SustainabilityAssessment)
                else SustainabilityAssessment(
                    overall_score=0.0,
                    maintainability_score=0.0,
                    scalability_score=0.0,
                    knowledge_transfer_score=0.0,
                    technical_debt_score=1.0,
                )
            )
        else:
            # EDGE-004 FIX: No assessor configured - add explicit risk factor
            # This creates a zero-scored assessment but marks it as incomplete
            sustainability_assessment = SustainabilityAssessment(
                overall_score=0.0,
                maintainability_score=0.0,
                scalability_score=0.0,
                knowledge_transfer_score=0.0,
                technical_debt_score=1.0,
                risk_factors=[
                    "CRITICAL: No sustainability assessor configured - assessment incomplete"
                ],
                recommendations=[
                    "Configure a sustainability_assessor to get complete validation results"
                ],
            )

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            compliance_score, sustainability_assessment.overall_score
        )

        # Create analysis dictionaries
        # TODO: Expand these with detailed analysis when specialized analyzers are available
        scalability_analysis = {
            "score": sustainability_assessment.scalability_score,
            "bottlenecks": [],
        }
        maintainability_analysis = {
            "score": sustainability_assessment.maintainability_score,
            "issues": [],
        }
        knowledge_preservation_analysis = {
            "score": sustainability_assessment.knowledge_transfer_score,
            "gaps": [],
        }

        # Collect recommendations
        actionable_recommendations = list(sustainability_assessment.recommendations)

        # Create result with new structure
        result = ArchitectureValidationResult(
            compliance_level=compliance_level,
            compliance_violations=violations,
            sustainability_assessment=sustainability_assessment,
            scalability_analysis=scalability_analysis,
            maintainability_analysis=maintainability_analysis,
            knowledge_preservation_analysis=knowledge_preservation_analysis,
            overall_score=overall_score,
            actionable_recommendations=actionable_recommendations,
        )

        return result

    def _calculate_overall_score(
        self, compliance_score: float, sustainability_score: float
    ) -> float:
        """Calculate overall score from compliance and sustainability scores.

        The overall score is computed as a simple average of the compliance
        and sustainability scores. This gives equal weight to both dimensions.

        Args:
            compliance_score: Compliance validation score (0.0 to 1.0)
            sustainability_score: Sustainability assessment score (0.0 to 1.0)

        Returns:
            Average of compliance and sustainability scores as a float
        """
        return (compliance_score + sustainability_score) / 2

    def _convert_to_compliance_violations(
        self, raw_violations: list[dict[str, object]]
    ) -> list[ComplianceViolation]:
        """Convert raw violation dictionaries to ComplianceViolation objects.

        This method transforms violation dictionaries from SOLIDValidator into
        ComplianceViolation dataclass instances. It maps the string severity
        to SeverityLevel enum and derives impact_score from severity.

        Args:
            raw_violations: List of violation dictionaries with keys:
                - rule_id: str
                - severity: str (e.g., "critical", "high", "medium", "low", "info")
                - description: str
                - location: str
                - recommendation: str

        Returns:
            List of ComplianceViolation dataclass instances
        """
        compliance_violations: list[ComplianceViolation] = []

        for v in raw_violations:
            # Map string severity to SeverityLevel enum
            severity_str = v.get("severity", "info")
            if isinstance(severity_str, str):
                severity = SeverityLevel(severity_str)
            else:
                severity = SeverityLevel.INFO

            # Derive impact_score from severity
            impact_score_map = {
                SeverityLevel.CRITICAL: 1.0,
                SeverityLevel.HIGH: 0.8,
                SeverityLevel.MEDIUM: 0.6,
                SeverityLevel.LOW: 0.4,
                SeverityLevel.INFO: 0.2,
            }
            impact_score = impact_score_map.get(severity, 0.2)

            # Get required fields with defaults
            rule_id = v.get("rule_id", "UNKNOWN")
            description = v.get("description", "")
            location = v.get("location", "")
            recommendation = v.get("recommendation", "")

            compliance_violations.append(
                ComplianceViolation(
                    rule_id=str(rule_id),
                    severity=severity,
                    description=str(description),
                    location=str(location),
                    recommendation=str(recommendation),
                    impact_score=impact_score,
                )
            )

        return compliance_violations

    def get_validation_summary(
        self, result: ArchitectureValidationResult
    ) -> dict[str, Any]:
        """Generate a summary dictionary from validation result.

        This method extracts key information from a validation result and
        returns it as a dictionary, useful for reporting and serialization.

        Args:
            result: ArchitectureValidationResult to summarize

        Returns:
            Dictionary containing summary information with keys:
                - compliance_level: Compliance level string
                - overall_score: Combined validation score
                - sustainability_overall_score: Sustainability assessment overall score
                - violation_count: Number of violations found
                - recommendation_count: Number of recommendations
        """
        return {
            "compliance_level": result.compliance_level,
            "overall_score": result.overall_score,
            "sustainability_overall_score": result.sustainability_assessment.overall_score,
            "violation_count": len(result.compliance_violations),
            "recommendation_count": len(result.actionable_recommendations),
        }

    def get_validation_count(self) -> int:
        """Get the current validation count.

        Returns:
            The number of times validate_architecture has been called.
        """
        return self.validation_counter
