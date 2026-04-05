"""
Entity Extraction Module v1.0

Three-tier extraction strategy for claim verification:
1. Structural (high confidence) - backticks, file paths, imports
2. Heuristic (medium confidence) - patterns with context validation  
3. Semantic (validated) - embedding-based classification

Design: Solo-dev appropriate, no background services, optional ML layer.
"""

from .extractor import EntityExtractor, extract_entities
from .strategies import HeuristicStrategy, SemanticStrategy, StructuralStrategy

__all__ = [
    'EntityExtractor',
    'extract_entities',
    'HeuristicStrategy',
    'SemanticStrategy',
    'StructuralStrategy',
]
