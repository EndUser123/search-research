"""Query expansion module for research.

This module provides query expansion capabilities including:
- Synonym expansion
- Abbreviation expansion
- Entity-specific term expansion
- Auto-learning from search results
"""

from .expander import QueryExpander, expand_query_if_enabled, get_query_suggestions
from .synonyms import get_synonym_mappings
from .abbreviations import get_abbreviation_mappings, expand_abbreviation
from .auto_learning import AutoLearningQueryExpander

__all__ = [
    "QueryExpander",
    "AutoLearningQueryExpander",
    "expand_query_if_enabled",
    "get_query_suggestions",
    "get_synonym_mappings",
    "get_abbreviation_mappings",
    "expand_abbreviation",
]
