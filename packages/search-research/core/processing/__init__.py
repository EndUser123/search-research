"""Processing components for search-research.

This module provides result processing capabilities including:
- Result normalization
"""

from .result_normalizer import NormalizedResult, ResultNormalizer, SourceType

__all__ = [
    "ResultNormalizer",
    "NormalizedResult",
    "SourceType",
]
