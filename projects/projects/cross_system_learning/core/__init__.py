"""
Core components for Cross-System Learning Architecture
"""

from .base_patterns import (
    BasePattern,
    DomainContext,
    EnhancementPattern,
    QualityMetrics,
)
from .learning_engine import (
    FailureAnalyzer,
    LearningEngine,
    PatternExtractor,
    SuccessAnalyzer,
)
from .memory_structures import (
    ConversationMemory,
    MemoryBank,
    PatternMemory,
    QualityMemory,
)

__all__ = [
    "BasePattern",
    "EnhancementPattern",
    "QualityMetrics",
    "DomainContext",
    "MemoryBank",
    "PatternMemory",
    "QualityMemory",
    "ConversationMemory",
    "LearningEngine",
    "PatternExtractor",
    "SuccessAnalyzer",
    "FailureAnalyzer",
]
