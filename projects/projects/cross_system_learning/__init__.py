"""
Cross-System Learning Architecture for Prompt Enhancement Integration

Phase 2 Implementation: Intelligent learning systems that enable enhancement
patterns to be shared and evolved across different prompt enhancement systems.

This module creates the intelligence layer that makes the unified system
smarter than any individual component through:
- Pattern Learning Hub
- Cross-Domain Pattern Transfer
- Memory Integration System
- Adaptive Quality Gates
- HDMA Pattern Recognition
"""

from .adaptive_quality_gates import AdaptiveQualityGates
from .cross_domain_transfer import CrossDomainPatternTransfer
from .hdma_pattern_recognition import HDMAPatternRecognition
from .memory_integration import MemoryIntegrationSystem
from .pattern_learning_hub import PatternLearningHub

__version__ = "1.0.0"
__author__ = "Cross-System Learning Architecture"

# Core exports
__all__ = [
    "PatternLearningHub",
    "CrossDomainPatternTransfer",
    "MemoryIntegrationSystem",
    "AdaptiveQualityGates",
    "HDMAPatternRecognition",
]
