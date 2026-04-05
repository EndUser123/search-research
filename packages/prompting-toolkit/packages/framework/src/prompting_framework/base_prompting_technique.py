from __future__ import annotations

import abc
import logging
from typing import Any

from .context_models import PromptingContext, PromptingTechnique, TechniqueApplicability

"""Base interface for prompting techniques in the Adaptive Universal Prompting Framework.

This module defines the abstract interface that all prompting techniques must implement,
providing a consistent contract for technique assessment, application, and integration.
"""





class BasePromptingTechnique(abc.ABC):
    """
    Abstract base class for all prompting techniques.

    This class defines the interface that all prompting techniques must implement
    to be compatible with the adaptive universal prompting framework.
    """

    def __init__(self, technique: PromptingTechnique):
        """Initialize the prompting technique."""
        self.technique = technique
        self.logger = logging.getLogger(f"{__name__}.{technique.value}")
        self.performance_cache = {}
        self.applicability_cache = {}

    @abc.abstractmethod
    async def is_applicable(self, context: PromptingContext) -> bool:
        """
        Determine if this technique is applicable for the given context.

        Args:
        ----
            context: The prompting context containing query, domain, and constraints

        Returns:
        -------
            True if the technique should be considered for this context

        """

    @abc.abstractmethod
    async def get_applicability_confidence(self, context: PromptingContext) -> float:
        """
        Get confidence score for technique applicability (0.0 to 1.0).

        Args:
        ----
            context: The prompting context

        Returns:
        -------
            Confidence score where higher values indicate stronger applicability

        """

    @abc.abstractmethod
    async def apply_technique(self, prompt: str, context: PromptingContext) -> str:
        """
        Apply the prompting technique to enhance the prompt.

        Args:
        ----
            prompt: The original prompt to enhance
            context: The prompting context for technique application

        Returns:
        -------
            Enhanced prompt with the technique applied

        """

    async def assess_technique_applicability(
        self,
        context: PromptingContext,
    ) -> TechniqueApplicability:
        """
        Perform comprehensive technique applicability assessment.

        This method combines the abstract methods to provide a complete
        assessment of technique applicability with performance impact analysis.

        Args:
        ----
            context: The prompting context

        Returns:
        -------
            Comprehensive applicability assessment

        """
        # Check cache first
        cache_key = self._generate_cache_key(context)
        if cache_key in self.applicability_cache:
            return self.applicability_cache[cache_key]

        # Assess basic applicability
        is_applicable = await self.is_applicable(context)
        confidence = await self.get_applicability_confidence(context)

        # Generate reasoning and requirements
        reasoning = await self._generate_applicability_reasoning(context, is_applicable, confidence)
        evidence_requirements = await self._get_evidence_requirements(context)
        performance_impact = await self._estimate_performance_impact(context)

        # Assess constitutional compliance
        constitutional_compliance = await self._check_constitutional_compliance(context)

        # Create applicability assessment
        assessment = TechniqueApplicability(
            technique=self.technique,
            applicable=is_applicable,
            confidence=confidence,
            reasoning=reasoning,
            evidence_requirements=evidence_requirements,
            performance_impact=performance_impact,
            constitutional_compliance=constitutional_compliance,
            domain_specific_factors=await self._get_domain_specific_factors(context),
            risk_assessment=await self._assess_risks(context),
        )

        # Cache the result
        self.applicability_cache[cache_key] = assessment

        return assessment

    async def validate_technique_application(
        self,
        original_prompt: str,
        enhanced_prompt: str,
        context: PromptingContext,
    ) -> dict[str, Any]:
        """
        Validate that the technique was applied correctly.

        Args:
        ----
            original_prompt: The original prompt before enhancement
            enhanced_prompt: The prompt after technique application
            context: The prompting context used for application

        Returns:
        -------
            Validation results with success status and details

        """
        validation_result = {
            "success": True,
            "enhancement_detected": len(enhanced_prompt) > len(original_prompt),
            "technique_signature_present": self._has_technique_signature(enhanced_prompt),
            "context_preservation": self._preserves_context(original_prompt, enhanced_prompt, context),
            "quality_score": await self._calculate_enhancement_quality(
                original_prompt,
                enhanced_prompt,
                context,
            ),
        }

        # Overall success if all validations pass
        validation_result["success"] = all(
            [
                validation_result["enhancement_detected"],
                validation_result["technique_signature_present"],
                validation_result["context_preservation"],
                validation_result["quality_score"] > 0.7,
            ],
        )

        return validation_result

    # Helper methods with default implementations
    async def _generate_applicability_reasoning(
        self,
        context: PromptingContext,
        is_applicable: bool,
        confidence: float,
    ) -> str:
        """Generate reasoning for applicability assessment."""
        if not is_applicable:
            return f"Technique {self.technique.value} is not applicable for {context.domain} domain with {context.complexity} complexity"

        factors = []
        if context.is_complex_query():
            factors.append("complex query requiring advanced reasoning")
        if context.has_evidence_requirements():
            factors.append("evidence-based validation required")
        if context.domain in self._get_supported_domains():
            factors.append(f"technique optimized for {context.domain} domain")

        base_reasoning = f"Technique {self.technique.value} is applicable with {confidence:.2f} confidence"
        if factors:
            base_reasoning += f" due to: {', '.join(factors)}"

        return base_reasoning

    async def _get_evidence_requirements(self, context: PromptingContext) -> list[str]:
        """Get evidence requirements for this technique."""
        requirements = []
        if context.constitutional_requirements.get("evidence_based", False):
            requirements.append("evidence_based_reasoning")
        if context.domain == "security":
            requirements.append("security_validation")
        if context.complexity in ["complex", "expert"]:
            requirements.append("comprehensive_analysis")
        return requirements

    async def _estimate_performance_impact(self, context: PromptingContext) -> dict[str, float]:
        """Estimate performance impact of applying this technique."""
        # Base performance characteristics
        base_impact = {
            "response_time": 0.5,  # seconds
            "memory_usage": 50.0,  # MB
            "cpu_usage": 0.1,  # percentage
        }

        # Adjust based on complexity
        complexity_multiplier = {
            "simple": 1.0,
            "moderate": 1.5,
            "complex": 2.0,
            "expert": 3.0,
        }.get(context.complexity, 1.5)

        # Adjust based on evidence requirements
        if context.has_evidence_requirements():
            complexity_multiplier *= 1.3

        return {key: value * complexity_multiplier for key, value in base_impact.items()}

    async def _check_constitutional_compliance(self, context: PromptingContext) -> dict[str, bool]:
        """Check constitutional compliance for this technique."""
        compliance = {}

        # Anti-deception compliance
        compliance["anti_deception"] = (
            not context.constitutional_requirements.get("anti_deception", False)
            or self.supports_evidence_based_reasoning()
        )

        # Evidence-based compliance
        compliance["evidence_based"] = (
            not context.constitutional_requirements.get("evidence_based", False)
            or self.supports_evidence_based_reasoning()
        )

        # Performance compliance
        performance_impact = await self._estimate_performance_impact(context)
        max_time = context.performance_constraints.get("max_response_time", 5.0)
        max_memory = context.performance_constraints.get("max_memory_usage", 512)

        compliance["performance_constraints"] = (
            performance_impact["response_time"] <= max_time and performance_impact["memory_usage"] <= max_memory
        )

        return compliance

    async def _get_domain_specific_factors(self, context: PromptingContext) -> dict[str, Any]:
        """Get domain-specific assessment factors."""
        factors = {}
        if context.domain == "security":
            factors["security_validation_required"] = True
            factors["threat_modeling_support"] = self.supports_threat_modeling()
        elif context.domain == "architecture":
            factors["system_design_support"] = self.supports_system_design()
            factors["scalability_analysis"] = self.supports_scalability_analysis()
        elif context.domain == "performance":
            factors["optimization_support"] = self.supports_optimization()
            factors["benchmarking_capability"] = self.supports_benchmarking()

        return factors

    async def _assess_risks(self, context: PromptingContext) -> dict[str, float]:
        """Assess risks associated with applying this technique."""
        risks = {}

        # Performance risk
        performance_impact = await self._estimate_performance_impact(context)
        max_time = context.performance_constraints.get("max_response_time", 5.0)
        risks["performance_risk"] = min(performance_impact["response_time"] / max_time, 1.0)

        # Complexity risk
        complexity_scores = {"simple": 0.1, "moderate": 0.3, "complex": 0.6, "expert": 0.8}
        risks["complexity_risk"] = complexity_scores.get(context.complexity, 0.3)

        # Constitutional risk
        compliance = await self._check_constitutional_compliance(context)
        risks["constitutional_risk"] = 0.0 if all(compliance.values()) else 0.7

        return risks

    # Technique capability methods (to be overridden by subclasses)
    def supports_evidence_based_reasoning(self) -> bool:
        """Check if technique supports evidence-based reasoning."""
        return False

    def supports_threat_modeling(self) -> bool:
        """Check if technique supports threat modeling."""
        return False

    def supports_system_design(self) -> bool:
        """Check if technique supports system design."""
        return False

    def supports_scalability_analysis(self) -> bool:
        """Check if technique supports scalability analysis."""
        return False

    def supports_optimization(self) -> bool:
        """Check if technique supports optimization."""
        return False

    def supports_benchmarking(self) -> bool:
        """Check if technique supports benchmarking."""
        return False

    def _get_supported_domains(self) -> list[str]:
        """Get list of domains this technique supports."""
        return ["general"]

    # Helper methods
    def _generate_cache_key(self, context: PromptingContext) -> str:
        """Generate cache key for context."""
        return f"{context.domain}:{context.complexity}:{context.user_intent}:{hash(context.query)}"

    def _has_technique_signature(self, enhanced_prompt: str) -> bool:
        """Check if enhanced prompt contains technique signature."""
        # Default implementation looks for technique-specific patterns
        return self.technique.value in enhanced_prompt.lower()

    def _preserves_context(
        self,
        original_prompt: str,
        enhanced_prompt: str,
        context: PromptingContext,
    ) -> bool:
        """Check if enhanced prompt preserves original context."""
        # Simple check: ensure original query is preserved
        return context.query.lower() in enhanced_prompt.lower()

    async def _calculate_enhancement_quality(
        self,
        original_prompt: str,
        enhanced_prompt: str,
        context: PromptingContext,
    ) -> float:
        """Calculate quality score for prompt enhancement."""
        # Simple quality metrics
        length_increase = len(enhanced_prompt) - len(original_prompt)
        structure_score = 1.0 if len(enhanced_prompt.split("\n")) > 1 else 0.5
        context_score = 1.0 if self._preserves_context(original_prompt, enhanced_prompt, context) else 0.0

        # Normalize to 0-1 range
        quality_score = min((length_increase / 100) + structure_score + context_score, 1.0) / 3
        return quality_score


class MockPromptingTechnique(BasePromptingTechnique):
    """Mock implementation of BasePromptingTechnique for testing."""

    def __init__(self, technique: PromptingTechnique, applicable: bool = False, confidence: float = 0.0):
        super().__init__(technique)
        self._applicable = applicable
        self._confidence = confidence

    async def is_applicable(self, context: PromptingContext) -> bool:
        return self._applicable

    async def get_applicability_confidence(self, context: PromptingContext) -> float:
        return self._confidence

    async def apply_technique(self, prompt: str, context: PromptingContext) -> str:
        return f"Enhanced prompt using {self.technique.value}: {prompt}"
