"""Analysis components for search-research.

This module provides analysis capabilities including:
- Gap analysis
- Contradiction detection
- Density calculation
- Topic clustering
- Novelty tracking
"""

from .contradiction_detector import Contradiction, ContradictionDetector
from .density_calculator import DensityCalculator
from .gap_analyzer import CoverageGap, GapAnalyzer, GapType
from .topic_clusterer import NoveltyTracker, TopicClusterer, TopicSignature

__all__ = [
    "GapAnalyzer",
    "CoverageGap",
    "GapType",
    "ContradictionDetector",
    "Contradiction",
    "DensityCalculator",
    "TopicClusterer",
    "TopicSignature",
    "NoveltyTracker",
]
