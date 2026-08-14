"""Utility modules for search research."""

from .clustering import CoverageState, NoveltyTracker, TopicClusterer, TopicSignature
from .cost_tracker import CostTracker
from .density import DensityCalculator
from .gap_analysis import CoverageGap, GapAnalyzer, GapType
from .hyde_measurement import HyDEMeasurement
from .tree_sitter_utils import (
    FallbackBackend,
    LanguageRegistry,
    QueryEngine,
    TreeSitterError,
    TreeSitterParser,
    create_query_engine,
    get_parser,
    is_available,
    parse_code,
    parse_file,
)

__all__ = [
    # Clustering
    "TopicSignature",
    "CoverageState",
    "TopicClusterer",
    "NoveltyTracker",
    # Cost tracking
    "CostTracker",
    # Density analysis
    "DensityCalculator",
    # Gap analysis
    "CoverageGap",
    "GapAnalyzer",
    "GapType",
    # HyDE measurement
    "HyDEMeasurement",
    # Tree-sitter utilities
    "TreeSitterParser",
    "LanguageRegistry",
    "QueryEngine",
    "FallbackBackend",
    "TreeSitterError",
    "is_available",
    "get_parser",
    "parse_code",
    "parse_file",
    "create_query_engine",
]
