"""
Adaptive Universal Prompting Framework.

A comprehensive framework for adaptive, context-aware prompting technique selection
and optimization within the CSF ecosystem.

This module provides:
- Universal prompting technique orchestration
- Context-aware technique selection
- Performance optimization and caching
- Constitutional compliance enforcement
- Plugin architecture for extensible techniques

Key Components:
- PromptingOrchestrator: Main orchestration engine
- BasePromptingTechnique: Abstract interface for prompting techniques
- PromptingContext: Context information for technique selection
- TechniqueApplicability: Applicability assessment results

Usage:
    from modules.prompting_framework.src.prompting_orchestrator import PromptingOrchestrator

    orchestrator = PromptingOrchestrator()
    context = PromptingContext(
        query="How should I implement this?",
        domain="security",
        complexity="complex",
        user_intent="get_advice",
        available_evidence=["requirements", "existing_code"],
        performance_constraints={"max_response_time": 5.0},
        constitutional_requirements={"anti_deception": True}
    )

    applicable_techniques = await orchestrator.select_applicable_techniques(context)
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "CSF Framework"

from .base_prompting_technique import BasePromptingTechnique
from .context_models import (
    PromptingContext,
    PromptingTechnique,
    TechniqueApplicability,
)
from .meta_prompt_optimizer import (
    EvaluationMetric,
    MetaPromptOptimizer,
    OptimizationConfig,
    OptimizationResult,
    OptimizationStrategy,
    PromptCandidate,
    PromptMutationType,
)
from .prompting_orchestrator import PromptingOrchestrator

__all__ = [
    "BasePromptingTechnique",
    "EvaluationMetric",
    "MetaPromptOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "OptimizationStrategy",
    "PromptCandidate",
    "PromptMutationType",
    "PromptingContext",
    "PromptingOrchestrator",
    "PromptingTechnique",
    "TechniqueApplicability",
]
