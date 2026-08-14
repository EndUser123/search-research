"""Query processing subpackage for search_research.

This module provides query processing capabilities including:
- Result normalization (unified schema across providers)
- Query expansion (synonyms, abbreviations, entity terms)
- Intent detection (for backend and mode selection)

Migrated from research_skill package.
"""

from .abbreviations import get_abbreviation_mappings
from .expander import (
    QueryExpander,
    expand_query_if_enabled,
    get_query_suggestions,
)
from .normalizer import (
    NormalizedResult,
    ResultNormalizer,
    SourceType,
)
from .synonyms import get_synonym_mappings

__all__ = [
    # Normalizer
    "NormalizedResult",
    "ResultNormalizer",
    "SourceType",
    # Expander
    "QueryExpander",
    "expand_query_if_enabled",
    "get_query_suggestions",
    # Mappings
    "get_synonym_mappings",
    "get_abbreviation_mappings",
]
