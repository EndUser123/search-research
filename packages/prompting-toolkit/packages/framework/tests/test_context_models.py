#!/usr/bin/env python3
"""
Unit tests for context_models module.

Tests for PromptingContext, TechniqueApplicability, PerformanceBudget,
and factory functions.
"""

import pytest

from prompting_framework.context_models import (
    ComplexityLevel,
    DomainType,
    PerformanceBudget,
    PromptingContext,
    PromptingTechnique,
    TechniqueApplicability,
    TechniqueCategory,
    TechniqueMetadata,
    TechniqueSelectionResult,
    UserIntent,
    create_architecture_context,
    create_debugging_context,
    create_security_context,
)


class TestPromptingTechnique:
    """Test PromptingTechnique enum."""

    def test_all_techniques_defined(self):
        """Verify all expected techniques are defined."""
        expected_techniques = [
            "chain_of_thought",
            "tree_of_thoughts",
            "react",
            "self_consistency",
            "few_shot",
            "zero_shot",
            "structured_prompting",
            "comparative_analysis",
            "evidence_gathering",
            "verbalized_sampling",
            "self_refine",
            "chain_of_verification",
            "query_fanout",
            "socratic",
        ]
        actual_values = [t.value for t in PromptingTechnique]
        for expected in expected_techniques:
            assert expected in actual_values


class TestComplexityLevel:
    """Test ComplexityLevel enum."""

    def test_all_levels_defined(self):
        """Verify all expected complexity levels are defined."""
        expected_levels = ["simple", "moderate", "complex", "expert"]
        actual_values = [c.value for c in ComplexityLevel]
        assert actual_values == expected_levels


class TestDomainType:
    """Test DomainType enum."""

    def test_all_domains_defined(self):
        """Verify all expected domain types are defined."""
        expected_domains = [
            "general",
            "security",
            "performance",
            "architecture",
            "development",
            "research",
            "analysis",
            "debugging",
        ]
        actual_values = [d.value for d in DomainType]
        assert actual_values == expected_domains


class TestUserIntent:
    """Test UserIntent enum."""

    def test_all_intents_defined(self):
        """Verify all expected user intents are defined."""
        expected_intents = [
            "get_advice",
            "solve_problem",
            "analyze_situation",
            "make_decision",
            "generate_code",
            "debug_issue",
            "research_topic",
            "compare_options",
        ]
        actual_values = [u.value for u in UserIntent]
        assert actual_values == expected_intents


class TestPromptingContext:
    """Test PromptingContext dataclass."""

    def test_create_minimal_context(self):
        """Create a minimal prompting context."""
        context = PromptingContext(
            query="What is Python?",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert context.query == "What is Python?"
        assert context.domain == "general"
        assert context.complexity == "simple"

    def test_complexity_normalization(self):
        """Test complexity normalization in __post_init__."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="SIMPLE",  # Should be normalized to lowercase
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert context.complexity == "simple"

    def test_is_complex_query_simple(self):
        """Simple queries are not complex."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert not context.is_complex_query()

    def test_is_complex_query_complex(self):
        """Complex queries are identified correctly."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="complex",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert context.is_complex_query()

    def test_has_evidence_requirements_from_list(self):
        """Evidence requirements detected from available_evidence."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=["doc1", "doc2"],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert context.has_evidence_requirements()

    def test_has_evidence_requirements_from_constitutional(self):
        """Evidence requirements detected from constitutional requirements."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={"evidence_based": True},
        )
        assert context.has_evidence_requirements()

    def test_has_evidence_requirements_from_domain(self):
        """Evidence requirements detected from security domain."""
        context = PromptingContext(
            query="test",
            domain="security",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert context.has_evidence_requirements()

    def test_requires_safety_validation_from_anti_deception(self):
        """Safety validation required for anti_deception."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={"anti_deception": True},
        )
        assert context.requires_safety_validation()

    def test_requires_safety_validation_from_domain(self):
        """Safety validation required for security domain."""
        context = PromptingContext(
            query="test",
            domain="security",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert context.requires_safety_validation()

    def test_extended_context_fields(self):
        """Test extended context fields work correctly."""
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
            prior_interactions=[{"action": "previous"}],
            user_preferences={"style": "concise"},
            session_context={"id": "session123"},
            environmental_factors={"platform": "cli"},
        )
        assert len(context.prior_interactions) == 1
        assert context.user_preferences["style"] == "concise"
        assert context.session_context["id"] == "session123"
        assert context.environmental_factors["platform"] == "cli"


class TestTechniqueApplicability:
    """Test TechniqueApplicability dataclass."""

    def test_create_applicability(self):
        """Create a technique applicability assessment."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.85,
            reasoning="Good match for complex reasoning",
            evidence_requirements=["sources"],
            performance_impact={"response_time": 1.0, "memory_usage": 100},
        )
        assert applicability.technique == PromptingTechnique.CHAIN_OF_THOUGHT
        assert applicability.applicable is True
        assert applicability.confidence == 0.85

    def test_confidence_validation_valid(self):
        """Valid confidence values are accepted."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.5,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        assert applicability.confidence == 0.5

    def test_confidence_validation_invalid_low(self):
        """Confidence below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            TechniqueApplicability(
                technique=PromptingTechnique.SELF_REFINE,
                applicable=True,
                confidence=-0.1,
                reasoning="test",
                evidence_requirements=[],
                performance_impact={},
            )

    def test_confidence_validation_invalid_high(self):
        """Confidence above 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            TechniqueApplicability(
                technique=PromptingTechnique.SELF_REFINE,
                applicable=True,
                confidence=1.1,
                reasoning="test",
                evidence_requirements=[],
                performance_impact={},
            )

    def test_is_highly_applicable_true(self):
        """High confidence applicable technique is highly applicable."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.9,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        assert applicability.is_highly_applicable()

    def test_is_highly_applicable_false_not_applicable(self):
        """Non-applicable technique is not highly applicable."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=False,
            confidence=0.9,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        assert not applicability.is_highly_applicable()

    def test_is_highly_applicable_false_low_confidence(self):
        """Low confidence technique is not highly applicable."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.7,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        assert not applicability.is_highly_applicable()

    def test_has_performance_risk_true_response_time(self):
        """High response time indicates performance risk."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.QUERY_FANOUT,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={"response_time": 3.0, "memory_usage": 50},
        )
        assert applicability.has_performance_risk()

    def test_has_performance_risk_true_memory(self):
        """High memory usage indicates performance risk."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.QUERY_FANOUT,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={"response_time": 1.0, "memory_usage": 150},
        )
        assert applicability.has_performance_risk()

    def test_has_performance_risk_false(self):
        """Low impact indicates no performance risk."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={"response_time": 1.0, "memory_usage": 50},
        )
        assert not applicability.has_performance_risk()

    def test_meets_constitutional_requirements_all_pass(self):
        """All constitutional requirements met."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
            constitutional_compliance={"anti_deception": True, "evidence_based": True},
        )
        assert applicability.meets_constitutional_requirements()

    def test_meets_constitutional_requirements_partial_fail(self):
        """Not all constitutional requirements met."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
            constitutional_compliance={"anti_deception": True, "evidence_based": False},
        )
        assert not applicability.meets_constitutional_requirements()


class TestPerformanceBudget:
    """Test PerformanceBudget dataclass."""

    def test_default_values(self):
        """Test default performance budget values."""
        budget = PerformanceBudget()
        assert budget.max_response_time == 5.0
        assert budget.max_memory_usage == 512
        assert budget.max_technique_count == 3
        assert budget.priority_speed_over_quality is False

    def test_custom_values(self):
        """Test custom performance budget values."""
        budget = PerformanceBudget(
            max_response_time=3.0,
            max_memory_usage=256,
            max_technique_count=2,
            priority_speed_over_quality=True,
        )
        assert budget.max_response_time == 3.0
        assert budget.max_memory_usage == 256
        assert budget.max_technique_count == 2
        assert budget.priority_speed_over_quality is True

    def test_allocate_budget_single_technique(self):
        """Allocate budget for a single technique."""
        budget = PerformanceBudget()
        allocated = budget.allocate_budget(1)
        assert allocated["response_time"] == 5.0
        assert allocated["memory_usage"] == 512

    def test_allocate_budget_multiple_techniques(self):
        """Allocate budget across multiple techniques."""
        budget = PerformanceBudget()
        allocated = budget.allocate_budget(2)
        assert allocated["response_time"] == 2.5
        assert allocated["memory_usage"] == 256

    def test_allocate_budget_exceeds_max(self):
        """Budget caps at max_technique_count."""
        budget = PerformanceBudget(max_technique_count=3)
        allocated = budget.allocate_budget(10)
        assert allocated["response_time"] == 5.0 / 3
        assert allocated["memory_usage"] == 512 / 3

    def test_allocate_budget_zero_techniques(self):
        """Zero techniques returns zero allocation."""
        budget = PerformanceBudget()
        allocated = budget.allocate_budget(0)
        assert allocated["response_time"] == 0.0
        assert allocated["memory_usage"] == 0.0


class TestTechniqueSelectionResult:
    """Test TechniqueSelectionResult dataclass."""

    def test_get_primary_technique_single(self):
        """Get primary technique from single selection."""
        applicability1 = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        result = TechniqueSelectionResult(
            selected_techniques=[applicability1],
            selection_reasoning="test",
            performance_estimate={},
            risk_assessment={},
            alternatives=[],
        )
        primary = result.get_primary_technique()
        assert primary is not None
        assert primary.technique == PromptingTechnique.CHAIN_OF_THOUGHT

    def test_get_primary_technique_multiple(self):
        """Get highest confidence technique from multiple."""
        applicability1 = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.7,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        applicability2 = TechniqueApplicability(
            technique=PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.9,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        result = TechniqueSelectionResult(
            selected_techniques=[applicability1, applicability2],
            selection_reasoning="test",
            performance_estimate={},
            risk_assessment={},
            alternatives=[],
        )
        primary = result.get_primary_technique()
        assert primary.technique == PromptingTechnique.SELF_REFINE

    def test_get_primary_technique_no_applicable(self):
        """Return None when no techniques are applicable."""
        applicability1 = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=False,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        result = TechniqueSelectionResult(
            selected_techniques=[applicability1],
            selection_reasoning="test",
            performance_estimate={},
            risk_assessment={},
            alternatives=[],
        )
        primary = result.get_primary_technique()
        assert primary is None

    def test_get_primary_technique_empty(self):
        """Return None for empty selection."""
        result = TechniqueSelectionResult(
            selected_techniques=[],
            selection_reasoning="test",
            performance_estimate={},
            risk_assessment={},
            alternatives=[],
        )
        primary = result.get_primary_technique()
        assert primary is None

    def test_has_confident_selection_true(self):
        """Confidence >= 0.7 is considered confident."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        result = TechniqueSelectionResult(
            selected_techniques=[applicability],
            selection_reasoning="test",
            performance_estimate={},
            risk_assessment={},
            alternatives=[],
        )
        assert result.has_confident_selection()

    def test_has_confident_selection_false(self):
        """Confidence < 0.7 is not considered confident."""
        applicability = TechniqueApplicability(
            technique=PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.6,
            reasoning="test",
            evidence_requirements=[],
            performance_impact={},
        )
        result = TechniqueSelectionResult(
            selected_techniques=[applicability],
            selection_reasoning="test",
            performance_estimate={},
            risk_assessment={},
            alternatives=[],
        )
        assert not result.has_confident_selection()


class TestFactoryFunctions:
    """Test context factory functions."""

    def test_create_security_context(self):
        """Create security-focused context."""
        context = create_security_context("Analyze this security vulnerability")
        assert context.domain == "security"
        assert context.complexity == "complex"
        assert "security_requirements" in context.available_evidence
        assert context.constitutional_requirements["anti_deception"] is True
        assert context.constitutional_requirements["evidence_based"] is True

    def test_create_security_context_custom_complexity(self):
        """Create security context with custom complexity."""
        context = create_security_context("Simple security check", complexity="moderate")
        assert context.complexity == "moderate"

    def test_create_architecture_context(self):
        """Create architecture-focused context."""
        context = create_architecture_context("Design a scalable architecture")
        assert context.domain == "architecture"
        assert context.complexity == "complex"
        assert "existing_code" in context.available_evidence
        assert context.constitutional_requirements["evidence_based"] is True

    def test_create_debugging_context(self):
        """Create debugging-focused context."""
        context = create_debugging_context("Fix this bug")
        assert context.domain == "debugging"
        assert context.complexity == "moderate"
        assert "error_logs" in context.available_evidence

    def test_create_debugging_context_custom_complexity(self):
        """Create debugging context with custom complexity."""
        context = create_debugging_context("Simple debug", complexity="simple")
        assert context.complexity == "simple"


class TestTechniqueMetadata:
    """Test TechniqueMetadata dataclass."""

    def test_create_metadata(self):
        """Create technique metadata."""
        metadata = TechniqueMetadata(
            name="Chain of Thought",
            category=TechniqueCategory.REASONING,
            description="Step-by-step reasoning",
            capabilities=["complex_reasoning", "error_detection"],
            performance_impact="medium",
            complexity_score="medium",
            success_rate=0.85,
            avg_processing_time=1.5,
            applicable_contexts=["problem_solving", "analysis"],
            limitations=["requires_time", "may_hallucinate"],
        )
        assert metadata.name == "Chain of Thought"
        assert metadata.category == TechniqueCategory.REASONING
        assert metadata.performance_impact == "medium"
        assert metadata.success_rate == 0.85
