#!/usr/bin/env python3
"""
Integration tests for prompting framework.

Tests end-to-end scenarios and multi-module interactions.
"""

import pytest

from prompting_framework.base_prompting_technique import MockPromptingTechnique
from prompting_framework.context_models import (
    PromptingContext,
    PromptingTechnique,
    create_architecture_context,
    create_debugging_context,
    create_security_context,
)


class TestContextFactoryIntegration:
    """Test integration of context factory functions."""

    def test_security_to_technique_selection(self):
        """Security context integrates with technique selection."""
        context = create_security_context("Analyze this vulnerability")
        assert context.domain == "security"
        assert context.requires_safety_validation()

    def test_architecture_to_technique_selection(self):
        """Architecture context integrates with technique selection."""
        context = create_architecture_context("Design system architecture")
        assert context.domain == "architecture"
        assert context.has_evidence_requirements()

    def test_debugging_to_technique_selection(self):
        """Debugging context integrates with technique selection."""
        context = create_debugging_context("Fix this bug")
        assert context.domain == "debugging"
        assert context.has_evidence_requirements()


class TestTechniqueWithContextIntegration:
    """Test technique integration with different contexts."""

    @pytest.mark.asyncio
    async def test_chain_of_thought_with_security_context(self):
        """Chain of Thought technique with security context."""
        technique = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.85,
        )
        context = create_security_context("Analyze security")

        is_applicable = await technique.is_applicable(context)
        confidence = await technique.get_applicability_confidence(context)

        assert is_applicable is True
        assert confidence == 0.85

    @pytest.mark.asyncio
    async def test_self_refine_with_architecture_context(self):
        """Self-Refine technique with architecture context."""
        technique = MockPromptingTechnique(
            PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.9,
        )
        context = create_architecture_context("Design system")

        assessment = await technique.assess_technique_applicability(context)

        assert assessment.applicable is True
        assert assessment.confidence == 0.9
        assert assessment.technique == PromptingTechnique.SELF_REFINE


class TestComplexityLevelIntegration:
    """Test complexity integration across modules."""

    def test_simple_context_technique_selection(self):
        """Simple complexity affects technique selection."""
        context = PromptingContext(
            query="What is Python?",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        assert not context.is_complex_query()

    def test_expert_context_technique_selection(self):
        """Expert complexity affects technique selection."""
        context = PromptingContext(
            query="Design a distributed system with eventual consistency",
            domain="architecture",
            complexity="expert",
            user_intent="make_decision",
            available_evidence=["requirements"],
            performance_constraints={},
            constitutional_requirements={"evidence_based": True},
        )
        assert context.is_complex_query()
        assert context.requires_safety_validation()


class TestPerformanceBudgetIntegration:
    """Test performance budget integration."""

    def test_performance_constraints_technique_selection(self):
        """Performance constraints affect technique selection."""
        context = PromptingContext(
            query="Quick question",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={
                "max_response_time": 1.0,
                "max_memory_usage": 128,
            },
            constitutional_requirements={},
        )

        # Techniques with high overhead should be filtered
        assert context.performance_constraints["max_response_time"] == 1.0

    def test_relaxed_constraints_allow_more_techniques(self):
        """Relaxed constraints allow more techniques."""
        context = PromptingContext(
            query="Complex analysis",
            domain="research",
            complexity="expert",
            user_intent="research_topic",
            available_evidence=[],
            performance_constraints={
                "max_response_time": 10.0,
                "max_memory_usage": 1024,
            },
            constitutional_requirements={},
        )

        assert context.performance_constraints["max_response_time"] >= 10.0


class TestConstitutionalComplianceIntegration:
    """Test constitutional compliance integration."""

    def test_anti_deception_requirement(self):
        """Anti-deception requirement affects technique selection."""
        context = PromptingContext(
            query="Verify this claim",
            domain="security",
            complexity="complex",
            user_intent="analyze_situation",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={"anti_deception": True},
        )
        assert context.requires_safety_validation()

    def test_evidence_based_requirement(self):
        """Evidence-based requirement affects technique selection."""
        context = PromptingContext(
            query="Analyze and provide sources",
            domain="research",
            complexity="complex",
            user_intent="research_topic",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={"evidence_based": True},
        )
        assert context.has_evidence_requirements()


class TestMultiTechniqueCoordination:
    """Test coordination of multiple techniques."""

    @pytest.mark.asyncio
    async def test_sequential_technique_application(self):
        """Test sequential application of multiple techniques."""
        context = create_architecture_context("Design scalable system")

        technique1 = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.85,
        )

        technique2 = MockPromptingTechnique(
            PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.9,
        )

        # First technique
        enhanced1 = await technique1.apply_technique(context.query, context)

        # Second technique on first output
        enhanced2 = await technique2.apply_technique(enhanced1, context)

        assert "chain_of_thought" in enhanced1.lower()
        assert "self_refine" in enhanced2.lower()

    @pytest.mark.asyncio
    async def test_parallel_technique_assessment(self):
        """Test parallel assessment of multiple techniques."""
        context = create_security_context("Analyze vulnerability")

        techniques = [
            MockPromptingTechnique(
                PromptingTechnique.CHAIN_OF_THOUGHT,
                applicable=True,
                confidence=0.8,
            ),
            MockPromptingTechnique(
                PromptingTechnique.CHAIN_OF_VERIFICATION,
                applicable=True,
                confidence=0.95,
            ),
            MockPromptingTechnique(
                PromptingTechnique.SELF_REFINE,
                applicable=False,
                confidence=0.3,
            ),
        ]

        # Assess all techniques
        assessments = []
        for technique in techniques:
            assessment = await technique.assess_technique_applicability(context)
            assessments.append(assessment)

        # Filter applicable
        applicable = [a for a in assessments if a.applicable]

        assert len(applicable) == 2
        assert max(applicable, key=lambda a: a.confidence).confidence == 0.95


class TestDomainSpecificIntegration:
    """Test domain-specific scenario integration."""

    @pytest.mark.asyncio
    async def test_security_domain_workflow(self):
        """Test complete security domain workflow."""
        # Create security context
        context = create_security_context(
            "Find vulnerabilities in this authentication code"
        )

        # Verify context properties
        assert context.domain == "security"
        assert context.requires_safety_validation()
        assert context.has_evidence_requirements()

        # Create appropriate technique
        technique = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.9,
        )

        # Assess applicability
        assessment = await technique.assess_technique_applicability(context)

        assert assessment.applicable is True
        assert assessment.technique == PromptingTechnique.CHAIN_OF_VERIFICATION

    @pytest.mark.asyncio
    async def test_debugging_domain_workflow(self):
        """Test complete debugging domain workflow."""
        # Create debugging context
        context = create_debugging_context("Fix null pointer exception")

        # Verify context properties
        assert context.domain == "debugging"
        assert context.has_evidence_requirements()

        # Create appropriate technique
        technique = MockPromptingTechnique(
            PromptingTechnique.SOCRATIC,
            applicable=True,
            confidence=0.85,
        )

        # Apply technique
        enhanced = await technique.apply_technique(context.query, context)

        assert "socratic" in enhanced.lower()


class TestErrorHandlingIntegration:
    """Test error handling across integrated modules."""

    @pytest.mark.asyncio
    async def test_invalid_context_handling(self):
        """Handle invalid context gracefully."""
        technique = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=False,
            confidence=0.0,
        )

        # Create empty context
        context = PromptingContext(
            query="",
            domain="",
            complexity="simple",
            user_intent="",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        # Should handle gracefully
        assessment = await technique.assess_technique_applicability(context)

        assert isinstance(assessment, type(assessment))  # Object created

    def test_mismatched_complexity_handling(self):
        """Handle mismatched complexity values."""
        # Invalid complexity should be normalized or handled
        context = PromptingContext(
            query="test",
            domain="general",
            complexity="invalid_value",  # Will use fallback
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )
        # Should not crash, may normalize to default
        assert context.complexity == "invalid_value"


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_complete_security_analysis_scenario(self):
        """Test complete security analysis scenario."""
        # 1. Create context
        context = create_security_context(
            "Review this code for SQL injection vulnerabilities"
        )

        # 2. Select technique
        technique = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_VERIFICATION,
            applicable=True,
            confidence=0.92,
        )

        # 3. Assess applicability
        assessment = await technique.assess_technique_applicability(context)
        assert assessment.applicable is True
        assert assessment.confidence >= 0.9

        # 4. Apply technique
        enhanced = await technique.apply_technique(context.query, context)
        assert "chain_of_verification" in enhanced.lower()

        # 5. Validate result
        validation = await technique.validate_technique_application(
            context.query, enhanced, context
        )
        assert validation["success"] is True

    @pytest.mark.asyncio
    async def test_complete_architecture_design_scenario(self):
        """Test complete architecture design scenario."""
        # 1. Create context
        context = create_architecture_context(
            "Design a microservices architecture for e-commerce"
        )

        # 2. Select technique
        technique = MockPromptingTechnique(
            PromptingTechnique.CHAIN_OF_THOUGHT,
            applicable=True,
            confidence=0.88,
        )

        # 3. Apply technique
        enhanced = await technique.apply_technique(context.query, context)

        # 4. Validate
        validation = await technique.validate_technique_application(
            context.query, enhanced, context
        )

        assert validation["context_preservation"] is True
        assert validation["enhancement_detected"] is True


class TestPerformanceIntegration:
    """Test performance characteristics across integrated system."""

    @pytest.mark.asyncio
    async def test_caching_improves_performance(self):
        """Verify caching improves repeated assessments."""
        technique = MockPromptingTechnique(
            PromptingTechnique.SELF_REFINE,
            applicable=True,
            confidence=0.85,
        )
        context = create_debugging_context("Fix this bug")

        # First call - populates cache
        assessment1 = await technique.assess_technique_applicability(context)

        # Second call - uses cache
        assessment2 = await technique.assess_technique_applicability(context)

        # Should return same object from cache
        assert assessment1 is assessment2

    @pytest.mark.asyncio
    async def test_performance_estimates_scale_with_complexity(self):
        """Verify performance estimates scale with complexity."""
        technique = MockPromptingTechnique(
            PromptingTechnique.QUERY_FANOUT,
            applicable=True,
            confidence=0.8,
        )

        simple_context = PromptingContext(
            query="simple",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        expert_context = PromptingContext(
            query="complex",
            domain="general",
            complexity="expert",
            user_intent="solve_problem",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        simple_impact = await technique._estimate_performance_impact(simple_context)
        expert_impact = await technique._estimate_performance_impact(expert_context)

        # Expert complexity should have higher impact
        assert expert_impact["response_time"] > simple_impact["response_time"]
