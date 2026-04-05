"""
Agent Factory Module

Provides agent creation and management functionality including critic system
and evaluation pipeline for comprehensive code and architecture analysis.
"""

from .agent_factory import (
    AgentDefinition,
    AgentFactory,
    AgentInstance,
    AgentRole,
    AgentStatus,
    PromptTemplateEngine,
    SessionManager,
    ToolRegistry,
    ToolType,
    create_agent_factory,
)
from .cks_integration import cks_stats, query_cks, store_to_cks
from .critic import (
    CriticIssue,
    CriticResult,
    CriticSystem,
    CriticType,
    QualityScore,
    Severity,
    create_critic,
    evaluate_file,
    evaluate_project,
)
from .evaluation import (
    EvaluationCache,
    EvaluationConfig,
    EvaluationPipeline,
    EvaluationQueue,
    EvaluationReport,
    EvaluationStatus,
    EvaluationTask,
    EvaluationType,
    Priority,
    create_evaluation_pipeline,
    quick_evaluate_code,
    quick_evaluate_file,
    quick_evaluate_project,
)

__all__ = [
    # Agent Factory Core
    "AgentFactory",
    "create_agent_factory",

    # Agent Classes and Enums
    "AgentDefinition",
    "AgentInstance",
    "AgentRole",
    "AgentStatus",
    "ToolType",

    # Management Components
    "ToolRegistry",
    "PromptTemplateEngine",
    "SessionManager",

    # CKS Integration
    "query_cks",
    "store_to_cks",
    "cks_stats",

    # Critic System
    "CriticSystem",
    "CriticResult",
    "CriticIssue",
    "Severity",
    "CriticType",
    "QualityScore",
    "create_critic",
    "evaluate_file",
    "evaluate_project",

    # Evaluation Pipeline
    "EvaluationPipeline",
    "EvaluationTask",
    "EvaluationReport",
    "EvaluationConfig",
    "EvaluationStatus",
    "EvaluationType",
    "Priority",
    "EvaluationQueue",
    "EvaluationCache",
    "create_evaluation_pipeline",
    "quick_evaluate_code",
    "quick_evaluate_file",
    "quick_evaluate_project"
]

__version__ = "1.0.0"
