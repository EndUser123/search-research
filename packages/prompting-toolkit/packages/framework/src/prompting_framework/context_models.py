from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

"""Context and data models for the Adaptive Universal Prompting Framework.

This module defines the core data structures and enums used throughout
the prompting framework for context representation and technique assessment.
"""




class PromptingTechnique(Enum):
    """Available prompting techniques in the framework."""

    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REACT = "react"
    SELF_CONSISTENCY = "self_consistency"
    FEW_SHOT = "few_shot"
    ZERO_SHOT = "zero_shot"
    STRUCTURED_PROMPTING = "structured_prompting"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    EVIDENCE_GATHERING = "evidence_gathering"
    VERBALIZED_SAMPLING = "verbalized_sampling"
    SELF_REFINE = "self_refine"
    CHAIN_OF_VERIFICATION = "chain_of_verification"
    QUERY_FANOUT = "query_fanout"
    SOCRATIC = "socratic"


class ComplexityLevel(Enum):
    """Complexity levels for prompting contexts."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class DomainType(Enum):
    """Domain types for specialized prompting."""

    GENERAL = "general"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    DEBUGGING = "debugging"


class UserIntent(Enum):
    """User intent categories for context analysis."""

    GET_ADVICE = "get_advice"
    SOLVE_PROBLEM = "solve_problem"
    ANALYZE_SITUATION = "analyze_situation"
    MAKE_DECISION = "make_decision"
    GENERATE_CODE = "generate_code"
    DEBUG_ISSUE = "debug_issue"
    RESEARCH_TOPIC = "research_topic"
    COMPARE_OPTIONS = "compare_options"


@dataclass
class PromptingContext:
    """Comprehensive context information for prompting technique selection."""

    query: str
    domain: str
    complexity: str  # "simple", "moderate", "complex", "expert"
    user_intent: str
    available_evidence: list[str]
    performance_constraints: dict[str, Any]
    constitutional_requirements: dict[str, Any]

    # Extended context fields for enhanced analysis
    prior_interactions: list[dict[str, Any]] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    session_context: dict[str, Any] = field(default_factory=dict)
    environmental_factors: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize context data."""
        # Normalize complexity to enum if possible
        complexity_mapping = {
            "simple": ComplexityLevel.SIMPLE,
            "moderate": ComplexityLevel.MODERATE,
            "complex": ComplexityLevel.COMPLEX,
            "expert": ComplexityLevel.EXPERT,
        }

        if self.complexity.lower() in complexity_mapping:
            self.complexity = complexity_mapping[self.complexity.lower()].value

    def is_complex_query(self) -> bool:
        """Determine if this is a complex query requiring advanced techniques."""
        complexity_scores = {
            "simple": 1,
            "moderate": 2,
            "complex": 3,
            "expert": 4,
        }
        return complexity_scores.get(self.complexity, 2) >= 3

    def has_evidence_requirements(self) -> bool:
        """Check if context requires evidence-based techniques."""
        return (
            len(self.available_evidence) > 0
            or self.constitutional_requirements.get("evidence_based", False)
            or self.domain in ["security", "architecture", "research"]
        )

    def requires_safety_validation(self) -> bool:
        """Check if context requires constitutional safety validation."""
        return (
            self.constitutional_requirements.get("anti_deception", False)
            or self.domain in ["security", "performance"]
            or self.complexity in ["complex", "expert"]
        )


@dataclass
class TechniqueApplicability:
    """Represents the applicability assessment of a prompting technique."""

    technique: PromptingTechnique
    applicable: bool
    confidence: float
    reasoning: str
    evidence_requirements: list[str]
    performance_impact: dict[str, float]

    # Extended assessment fields
    constitutional_compliance: dict[str, bool] = field(default_factory=dict)
    domain_specific_factors: dict[str, Any] = field(default_factory=dict)
    risk_assessment: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate applicability data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def is_highly_applicable(self) -> bool:
        """Check if technique is highly applicable."""
        return self.applicable and self.confidence >= 0.8

    def has_performance_risk(self) -> bool:
        """Check if technique poses performance risks."""
        return (
            self.performance_impact.get("response_time", 0) > 2.0
            or self.performance_impact.get("memory_usage", 0) > 100
        )

    def meets_constitutional_requirements(self) -> bool:
        """Check if technique meets all constitutional requirements."""
        return all(self.constitutional_compliance.values())


@dataclass
class PerformanceBudget:
    """Performance budget for technique selection."""

    max_response_time: float = 5.0  # seconds
    max_memory_usage: float = 512  # MB
    max_technique_count: int = 3
    priority_speed_over_quality: bool = False

    def allocate_budget(self, technique_count: int) -> dict[str, float]:
        """Allocate performance budget across techniques."""
        if technique_count == 0:
            return {"response_time": 0.0, "memory_usage": 0.0}

        per_technique_time = self.max_response_time / min(technique_count, self.max_technique_count)
        per_technique_memory = self.max_memory_usage / min(technique_count, self.max_technique_count)

        return {
            "response_time": per_technique_time,
            "memory_usage": per_technique_memory,
        }


@dataclass
class TechniqueSelectionResult:
    """Result of technique selection process."""

    selected_techniques: list[TechniqueApplicability]
    selection_reasoning: str
    performance_estimate: dict[str, float]
    risk_assessment: dict[str, Any]
    alternatives: list[TechniqueApplicability]

    def get_primary_technique(self) -> TechniqueApplicability | None:
        """Get the primary (highest confidence) technique."""
        if not self.selected_techniques:
            return None

        applicable_techniques = [t for t in self.selected_techniques if t.applicable]
        if not applicable_techniques:
            return None

        return max(applicable_techniques, key=lambda t: t.confidence)

    def has_confident_selection(self) -> bool:
        """Check if we have a confident technique selection."""
        primary = self.get_primary_technique()
        return primary is not None and primary.confidence >= 0.7


# Factory functions for creating common contexts
def create_security_context(query: str, complexity: str = "complex") -> PromptingContext:
    """Create a security-focused prompting context."""
    return PromptingContext(
        query=query,
        domain="security",
        complexity=complexity,
        user_intent="get_advice",
        available_evidence=["security_requirements", "threat_model"],
        performance_constraints={"max_response_time": 3.0, "max_memory_usage": 256},
        constitutional_requirements={"anti_deception": True, "evidence_based": True},
    )


def create_architecture_context(query: str, complexity: str = "complex") -> PromptingContext:
    """Create an architecture-focused prompting context."""
    return PromptingContext(
        query=query,
        domain="architecture",
        complexity=complexity,
        user_intent="make_decision",
        available_evidence=["existing_code", "requirements", "constraints"],
        performance_constraints={"max_response_time": 5.0, "max_memory_usage": 512},
        constitutional_requirements={"evidence_based": True},
    )


def create_debugging_context(query: str, complexity: str = "moderate") -> PromptingContext:
    """Create a debugging-focused prompting context."""
    return PromptingContext(
        query=query,
        domain="debugging",
        complexity=complexity,
        user_intent="solve_problem",
        available_evidence=["error_logs", "stack_trace", "code_context"],
        performance_constraints={"max_response_time": 2.0, "max_memory_usage": 128},
        constitutional_requirements={"evidence_based": True},
    )


class TechniqueCategory(Enum):
    """Categories for prompting techniques."""

    REASONING = "reasoning"
    EXPLORATION = "exploration"
    OPTIMIZATION = "optimization"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"


@dataclass
class TechniqueMetadata:
    """Metadata for a prompting technique."""

    name: str
    category: TechniqueCategory
    description: str
    capabilities: list[str]
    performance_impact: str  # "low", "medium", "high"
    complexity_score: str  # "low", "medium", "high"
    success_rate: float
    avg_processing_time: float
    applicable_contexts: list[str]
    limitations: list[str]
