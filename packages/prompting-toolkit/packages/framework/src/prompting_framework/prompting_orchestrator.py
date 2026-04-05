"""PromptingOrchestrator - Main orchestration engine for the Adaptive Universal Prompting Framework.

This module provides the central orchestration logic for selecting, applying, and
evaluating prompting techniques based on context.
"""

from __future__ import annotations

import logging
from typing import Any

from .context_models import PromptingContext, PromptingTechnique, TechniqueApplicability
from .base_prompting_technique import BasePromptingTechnique
from .meta_prompt_optimizer import MetaPromptOptimizer, OptimizationConfig, OptimizationStrategy

logger = logging.getLogger(__name__)


class PromptingOrchestrator:
    """
    Main orchestration engine for adaptive prompt technique selection.

    This class manages the lifecycle of prompting techniques including:
    - Discovery of available techniques
    - Applicability assessment for given context
    - Technique application and enhancement
    - Performance optimization via meta-prompt optimizer
    """

    def __init__(self, techniques: list[BasePromptingTechnique] | None = None):
        """Initialize the orchestrator with available techniques."""
        self.techniques = techniques or []
        self.optimizer = MetaPromptOptimizer()
        self.logger = logging.getLogger(f"{__name__}.PromptingOrchestrator")
        self._technique_registry: dict[PromptingTechnique, BasePromptingTechnique] = {}

        # Auto-register provided techniques
        for technique in self.techniques:
            self._technique_registry[technique.technique] = technique

    def register_technique(self, technique: BasePromptingTechnique) -> None:
        """Register a prompting technique with the orchestrator."""
        self._technique_registry[technique.technique] = technique
        self.logger.info(f"Registered technique: {technique.technique.value}")

    async def select_applicable_techniques(
        self,
        context: PromptingContext,
    ) -> list[TechniqueApplicability]:
        """
        Select techniques applicable for the given context.

        Args:
            context: The prompting context containing query, domain, and constraints

        Returns:
            List of applicability assessments for applicable techniques
        """
        applicable = []

        for technique in self._technique_registry.values():
            try:
                is_applicable = await technique.is_applicable(context)
                confidence = await technique.get_applicability_confidence(context)

                if is_applicable:
                    assessment = await technique.assess_technique_applicability(context)
                    applicable.append(assessment)
                    self.logger.debug(
                        f"Technique {technique.technique.value} applicable with confidence {confidence:.2f}"
                    )
            except Exception as e:
                self.logger.warning(f"Error assessing technique {technique.technique.value}: {e}")

        # Sort by confidence score
        applicable.sort(key=lambda a: a.confidence, reverse=True)
        return applicable

    async def apply_technique(
        self,
        technique: BasePromptingTechnique,
        prompt: str,
        context: PromptingContext,
    ) -> str:
        """
        Apply a prompting technique to enhance the prompt.

        Args:
            technique: The technique to apply
            prompt: The original prompt to enhance
            context: The prompting context for technique application

        Returns:
            Enhanced prompt with the technique applied
        """
        self.logger.info(f"Applying technique: {technique.technique.value}")
        enhanced = await technique.apply_technique(prompt, context)
        return enhanced

    async def optimize_prompt(
        self,
        prompt: str,
        context: PromptingContext,
        strategy: OptimizationStrategy = OptimizationStrategy.GENETIC_ALGORITHM,
        iterations: int = 5,
    ) -> str:
        """
        Optimize a prompt using the meta-prompt optimizer.

        Args:
            prompt: The initial prompt to optimize
            context: Context for optimization
            strategy: Optimization strategy to use
            iterations: Number of optimization iterations

        Returns:
            Optimized prompt
        """
        config = OptimizationConfig(
            original_prompt=prompt,
            context=context.domain,
            max_iterations=iterations,
            strategy=strategy,
        )

        result = await self.optimizer.optimize_prompt(config)

        if result.success:
            self.logger.info(f"Prompt optimized: {result.final_prompt[:100]}...")
            return result.final_prompt
        else:
            self.logger.warning(f"Optimization failed: {result.error_message}")
            return prompt

    async def orchestrate_prompt_enhancement(
        self,
        prompt: str,
        context: PromptingContext,
        optimize: bool = True,
    ) -> dict[str, Any]:
        """
        Full orchestration workflow: select, apply, and optimize.

        Args:
            prompt: The original prompt
            context: Prompting context
            optimize: Whether to run meta-optimization

        Returns:
            Dict with enhanced_prompt, techniques_applied, optimization_result
        """
        self.logger.info(f"Orchestrating prompt enhancement for domain: {context.domain}")

        # Step 1: Select applicable techniques
        applicable = await self.select_applicable_techniques(context)

        # Step 2: Apply top techniques
        enhanced = prompt
        techniques_applied = []

        for assessment in applicable[:3]:  # Top 3 techniques
            technique = self._technique_registry.get(assessment.technique)
            if technique:
                enhanced = await self.apply_technique(technique, enhanced, context)
                techniques_applied.append(assessment.technique)

        # Step 3: Optimize if requested
        optimization_result = None
        if optimize and len(enhanced) > len(prompt):
            optimized = await self.optimize_prompt(enhanced, context)
            optimization_result = {"success": True, "improvement": len(optimized) > len(enhanced)}
            enhanced = optimized
        else:
            optimization_result = {"success": False, "reason": "Optimization disabled or no enhancement"}

        return {
            "enhanced_prompt": enhanced,
            "techniques_applied": techniques_applied,
            "applicable_techniques": len(applicable),
            "optimization_result": optimization_result,
        }

    def list_available_techniques(self) -> list[str]:
        """List all registered technique names."""
        return [t.value for t in self._technique_registry.keys()]

    def get_technique_count(self) -> int:
        """Return count of registered techniques."""
        return len(self._technique_registry)


__all__ = ["PromptingOrchestrator"]
