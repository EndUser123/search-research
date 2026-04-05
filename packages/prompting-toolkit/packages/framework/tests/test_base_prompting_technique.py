#!/usr/bin/env python3
"""
Unit tests for base_prompting_technique module.

Tests for BasePromptingTechnique abstract class and MockPromptingTechnique.
"""

import pytest

from prompting_framework.base_prompting_technique import (
    MockPromptingTechnique,
)
from prompting_framework.context_models import (
    PromptingContext,
    PromptingTechnique,
    create_security_context,
)


class TestMockPromptingTechnique:
    """Test MockPromptingTechnique for testing purposes."""

    @pytest.mark.asyncio
    async def test_mock_is_applicable_true(self):
        """Mock technique returns True when configured."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test")
        assert await mock.is_applicable(context) is True

    @pytest.mark.asyncio
    async def test_mock_is_applicable_false(self):
        """Mock technique returns False when configured."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=False,
            confidence=0.8,
        )
        context = create_security_context("test")
        assert await mock.is_applicable(context) is False

    @pytest.mark.asyncio
    async def test_mock_confidence(self):
        """Mock technique returns configured confidence."""
        mock = MockPromptingTechnique(
            PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.92,
        )
        context = create_security_context("test")
        assert await mock.get_applicability_confidence(context) == 0.92

    @pytest.mark.asyncio
    async def test_mock_apply_technique(self):
        """Mock technique enhances prompt with technique name."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")
        enhanced = await mock.apply_technique("test query", context)
        assert "chain_of_thought" in enhanced
        assert "test query" in enhanced


class TestBasePromptingTechniqueCaching:
    """Test caching behavior of BasePromptingTechnique."""

    @pytest.mark.asyncio
    async def test_applicability_cache_hit(self):
        """Second call for same context uses cache."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")

        # First call populates cache
        assessment1 = await mock.assess_technique_applicability(context)
        # Second call should use cache
        assessment2 = await mock.assess_technique_applicability(context)

        assert assessment1 is assessment2  # Same object from cache

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Cache keys are generated correctly."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")

        cache_key = mock._generate_cache_key(context)
        assert "security" in cache_key
        assert "complex" in cache_key
        assert "get_advice" in cache_key


class TestBasePromptingTechniqueValidation:
    """Test validation methods."""

    @pytest.mark.asyncio
    async def test_validate_technique_application_success(self):
        """Validation passes for good enhancement."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")
        enhanced = await mock.apply_technique("test query", context)

        result = await mock.validate_technique_application(
            "test query", enhanced, context
        )

        assert result["success"] is True
        assert result["enhancement_detected"] is True
        assert result["technique_signature_present"] is True
        assert result["context_preservation"] is True
        assert result["quality_score"] > 0

    @pytest.mark.asyncio
    async def test_validate_technique_application_no_enhancement(self):
        """Validation fails when prompt not enhanced."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")

        result = await mock.validate_technique_application(
            "test query", "test query", context  # No enhancement
        )

        assert result["enhancement_detected"] is False
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_has_technique_signature(self):
        """Technique signature detection works."""
        mock = MockPromptingTechnique(
            PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.8,
        )

        enhanced = await mock.apply_technique("test", create_security_context("test"))
        assert mock._has_technique_signature(enhanced) is True

    def test_preserves_context_true(self):
        """Context preservation check passes when query preserved."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")

        assert mock._preserves_context("test query", "enhanced test query", context) is True

    def test_preserves_context_false(self):
        """Context preservation check fails when query lost."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")

        assert mock._preserves_context("test query", "something else", context) is False

    @pytest.mark.asyncio
    async def test_calculate_enhancement_quality(self):
        """Quality score is calculated correctly."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = create_security_context("test query")

        quality = await mock._calculate_enhancement_quality(
            "test query",
            "Enhanced prompt with test query\nMultiple lines for structure",
            context,
        )

        assert 0.0 <= quality <= 1.0


class TestBasePromptingTechniquePerformance:
    """Test performance estimation methods."""

    @pytest.mark.asyncio
    async def test_estimate_performance_impact_simple(self):
        """Performance impact estimated for simple complexity."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="simple",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        impact = await mock._estimate_performance_impact(context)

        assert "response_time" in impact
        assert "memory_usage" in impact
        assert "cpu_usage" in impact
        assert impact["response_time"] >= 0

    @pytest.mark.asyncio
    async def test_estimate_performance_impact_expert(self):
        """Performance impact is higher for expert complexity."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="complex",
            domain="general",
            complexity="expert",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        impact = await mock._estimate_performance_impact(context)

        # Expert complexity should have higher impact than simple
        assert impact["response_time"] > 0.5  # Base is 0.5

    @pytest.mark.asyncio
    async def test_estimate_performance_with_evidence(self):
        """Evidence requirements increase performance impact."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="security",
            complexity="complex",
            user_intent="get_advice",
            available_evidence=["doc1"],
            performance_constraints={},
            constitutional_requirements={"evidence_based": True},
        )

        impact = await mock._estimate_performance_impact(context)

        # Should be higher due to evidence requirements
        assert impact["response_time"] > 0.5


class TestBasePromptingTechniqueConstitutional:
    """Test constitutional compliance checking."""

    @pytest.mark.asyncio
    async def check_constitutional_compliance_all_pass(self):
        """All requirements pass when no constraints."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        compliance = await mock._check_constitutional_compliance(context)

        assert compliance["anti_deception"] is True
        assert compliance["evidence_based"] is True
        assert compliance["performance_constraints"] is True

    @pytest.mark.asyncio
    async def test_constitutional_performance_constraint_pass(self):
        """Performance constraint passes within limits."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={"max_response_time": 5.0, "max_memory_usage": 512},
            constitutional_requirements={},
        )

        compliance = await mock._check_constitutional_compliance(context)

        assert compliance["performance_constraints"] is True

    @pytest.mark.asyncio
    async def test_constitutional_anti_deception_with_evidence(self):
        """Anti-deception passes when technique supports evidence."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.8,
        )
        # Mock technique doesn't support evidence by default
        mock.supports_evidence_based_reasoning = lambda: True

        context = PromptingContext(
            query="test",
            domain="security",
            complexity="complex",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={"anti_deception": True},
        )

        compliance = await mock._check_constitutional_compliance(context)

        assert compliance["anti_deception"] is True


class TestBasePromptingTechniqueRiskAssessment:
    """Test risk assessment methods."""

    @pytest.mark.asyncio
    async def test_assess_risks_performance(self):
        """Performance risk calculated correctly."""
        mock = MockPromptingTechnique(
            PromptingTechnique.QUERY_FANOUT,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="complex",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={"max_response_time": 5.0},
            constitutional_requirements={},
        )

        risks = await mock._assess_risks(context)

        assert "performance_risk" in risks
        assert "complexity_risk" in risks
        assert "constitutional_risk" in risks
        assert 0.0 <= risks["performance_risk"] <= 1.0

    @pytest.mark.asyncio
    async def test_assess_risks_complexity(self):
        """Complexity risk increases with complexity level."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )

        simple_context = PromptingContext(
            query="test",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        expert_context = PromptingContext(
            query="test",
            domain="general",
            complexity="expert",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        simple_risks = await mock._assess_risks(simple_context)
        expert_risks = await mock._assess_risks(expert_context)

        assert expert_risks["complexity_risk"] > simple_risks["complexity_risk"]


class TestBasePromptingTechniqueCapabilities:
    """Test technique capability methods."""

    def test_supports_evidence_based_reasoning_default(self):
        """Default implementation doesn't support evidence-based reasoning."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock.supports_evidence_based_reasoning() is False

    def test_supports_threat_modeling_default(self):
        """Default implementation doesn't support threat modeling."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock.supports_threat_modeling() is False

    def test_supports_system_design_default(self):
        """Default implementation doesn't support system design."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock.supports_system_design() is False

    def test_supports_scalability_analysis_default(self):
        """Default implementation doesn't support scalability analysis."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock.supports_scalability_analysis() is False

    def test_supports_optimization_default(self):
        """Default implementation doesn't support optimization."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock.supports_optimization() is False

    def test_supports_benchmarking_default(self):
        """Default implementation doesn't support benchmarking."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock.supports_benchmarking() is False

    def test_get_supported_domains_default(self):
        """Default implementation only supports general domain."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=True,
            confidence=0.8,
        )
        assert mock._get_supported_domains() == ["general"]


class TestBasePromptingTechniqueApplicabilityAssessment:
    """Test comprehensive applicability assessment."""

    @pytest.mark.asyncio
    async def test_assess_technique_applicability_complete(self):
        """Full assessment includes all expected fields."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.85,
        )
        context = create_security_context("test query")

        assessment = await mock.assess_technique_applicability(context)

        assert assessment.technique == PromptingTechnique.CHAIN_OF_THOUGHT
        assert assessment.applicable is True
        assert assessment.confidence == 0.85
        assert assessment.reasoning is not None
        assert isinstance(assessment.evidence_requirements, list)
        assert isinstance(assessment.performance_impact, dict)
        assert isinstance(assessment.constitutional_compliance, dict)
        assert isinstance(assessment.domain_specific_factors, dict)
        assert isinstance(assessment.risk_assessment, dict)

    @pytest.mark.asyncio
    async def test_assess_technique_applicability_not_applicable(self):
        """Assessment for non-applicable technique."""
        mock = MockPromptingTechnique(
            PromptingTechnique.FEW_SHOT,
            applicable=False,
            confidence=0.3,
        )
        context = create_security_context("test query")

        assessment = await mock.assess_technique_applicability(context)

        assert assessment.applicable is False
        assert assessment.confidence == 0.3
        assert "not applicable" in assessment.reasoning.lower()


class TestBasePromptingTechniqueDomainFactors:
    """Test domain-specific factor assessment."""

    @pytest.mark.asyncio
    async def test_get_domain_specific_factors_security(self):
        """Security domain gets security-specific factors."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="security",
            complexity="complex",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        factors = await mock._get_domain_specific_factors(context)

        assert "security_validation_required" in factors
        assert factors["security_validation_required"] is True

    @pytest.mark.asyncio
    async def test_get_domain_specific_factors_architecture(self):
        """Architecture domain gets architecture-specific factors."""
        mock = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="architecture",
            complexity="complex",
            user_intent="make_decision",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        factors = await mock._get_domain_specific_factors(context)

        assert "system_design_support" in factors
        assert "scalability_analysis" in factors

    @pytest.mark.asyncio
    async def test_get_domain_specific_factors_performance(self):
        """Performance domain gets performance-specific factors."""
        mock = MockPromptingTechnique(
            PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.8,
        )
        context = PromptingContext(
            query="test",
            domain="performance",
            complexity="moderate",
            user_intent="solve_problem",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        factors = await mock._get_domain_specific_factors(context)

        assert "optimization_support" in factors
        assert "benchmarking_capability" in factors
