"""Enhancement components for search-research.

This module provides advanced research capabilities including:
- Dependency analysis
- Learning systems
- Mode orchestration
- Quality prediction
- Cost/benefit optimization
"""

from .enhanced_dependency_analyzer import (
    QueryDependencies,
    ResearchDepth,
    SimplifiedDependencyAnalyzer,
)
from .learning_system import LearningSystem, PatternInsight, ResearchFeedback
from .mode_relationship_mapper import ModeCombination, ModeRelationshipMapper, ResearchMode
from .multi_mode_orchestrator import (
    ExecutionStatus,
    ModeExecutionResult,
    MultiModeOrchestrator,
    OrchestratedResult,
)
from .quality_optimizer import OptimizationResult, QualityPredictor

__all__ = [
    "SimplifiedDependencyAnalyzer",
    "QueryDependencies",
    "ResearchDepth",
    "LearningSystem",
    "PatternInsight",
    "ResearchFeedback",
    "ModeRelationshipMapper",
    "ResearchMode",
    "ModeCombination",
    "MultiModeOrchestrator",
    "ExecutionStatus",
    "ModeExecutionResult",
    "OrchestratedResult",
    "QualityPredictor",
    "OptimizationResult",
]
