"""Query expander for generating search query variations."""

import re
from typing import Dict, List

from .synonyms import get_synonym_mappings
from .abbreviations import get_abbreviation_mappings


# Entity-specific terms for different contexts
ENTITY_TERMS: Dict[str, List[str]] = {
    "cks": [
        "constitutional knowledge system",
        "cks entry",
        "semantic search",
        "vector embeddings",
        "knowledge retrieval",
    ],
    "chs": [
        "chat history search",
        "conversation retrieval",
        "session search",
        "hypergraph",
    ],
    "code": [
        "source code",
        "implementation",
        "function",
        "class",
        "module",
    ],
}

# Domain-specific expansions for common technical terms
DOMAIN_EXPANSIONS: Dict[str, List[str]] = {
    "db": ["database", "data storage"],
    "auth": ["authentication", "authorization", "login"],
    "code": ["source code", "implementation", "programming"],
    "error": ["exception", "bug", "issue", "failure"],
    "fast": ["quick", "rapid", "high performance"],
    "create": ["make", "build", "construct", "generate"],
    "build": ["create", "make", "construct", "develop"],
    "fix": ["repair", "resolve", "solve"],
}


class QueryExpander:
    """Expands queries using synonyms, abbreviations, and entity-specific terms.

    Attributes:
        synonyms: Dictionary of term to synonym mappings.
        abbreviations: Dictionary of abbreviation to full form mappings.
        entity_terms: Dictionary of entity-specific term mappings.
    """

    def __init__(self, custom_synonyms: Dict[str, List[str]] | None = None):
        """Initialize QueryExpander with optional custom synonyms.

        Args:
            custom_synonyms: Optional custom synonym mappings to add.
        """
        self.synonyms: Dict[str, List[str]] = get_synonym_mappings()
        self.abbreviations: Dict[str, str] = get_abbreviation_mappings()
        self.entity_terms: Dict[str, List[str]] = ENTITY_TERMS.copy()

        if custom_synonyms:
            for term, syn_list in custom_synonyms.items():
                if term in self.synonyms:
                    self.synonyms[term].extend(syn_list)
                else:
                    self.synonyms[term] = syn_list

    def expand_query(
        self,
        query: str,
        entity_slug: str | None = None,
        max_variations: int = 5,
    ) -> List[str]:
        """Expand a query into multiple variations.

        Args:
            query: The original query string.
            entity_slug: Optional entity context for entity-specific expansion.
            max_variations: Maximum number of query variations to return.

        Returns:
            A list of query variations (includes original).
        """
        # Start with original query
        variations = [query.lower()]
        seen = {query.lower()}

        # 1. Synonym expansion (highest priority)
        for v in self._expand_synonyms(query):
            if v.lower() not in seen:
                variations.append(v.lower())
                seen.add(v.lower())

        # 2. Abbreviation expansion
        for v in self._expand_abbreviations(query):
            if v.lower() not in seen:
                variations.append(v.lower())
                seen.add(v.lower())

        # 3. Entity-specific terms
        if entity_slug:
            for v in self._expand_with_entity_terms(query, entity_slug):
                if v.lower() not in seen:
                    variations.append(v.lower())
                    seen.add(v.lower())

        # 4. Domain-specific expansions
        for v in self._expand_domain_terms(query):
            if v.lower() not in seen:
                variations.append(v.lower())
                seen.add(v.lower())

        # Limit to max_variations
        return variations[:max_variations]

    def _expand_synonyms(self, query: str) -> List[str]:
        """Generate variations using synonym mappings.

        Args:
            query: The query string.

        Returns:
            List of query variations with synonyms.
        """
        variations = []
        query_lower = query.lower()
        words = query_lower.split()

        for i, word in enumerate(words):
            # Check for direct synonym match
            if word in self.synonyms:
                for synonym in self.synonyms[word]:
                    new_query = " ".join(
                        synonym if j == i else words[j]
                        for j in range(len(words))
                    )
                    variations.append(new_query)

        return variations

    def _expand_abbreviations(self, query: str) -> List[str]:
        """Generate variations by expanding abbreviations.

        Args:
            query: The query string.

        Returns:
            List of query variations with expanded abbreviations.
        """
        variations = []
        query_lower = query.lower()
        words = query_lower.split()

        for i, word in enumerate(words):
            # Remove non-alphanumeric chars for matching
            clean_word = re.sub(r"[^a-z0-9]", "", word.lower())

            if clean_word in self.abbreviations:
                expansion = self.abbreviations[clean_word]
                new_query = " ".join(
                    expansion if j == i else words[j]
                    for j in range(len(words))
                )
                variations.append(new_query)

        return variations

    def _expand_with_entity_terms(self, query: str, entity_slug: str) -> List[str]:
        """Generate variations using entity-specific terms.

        Args:
            query: The query string.
            entity_slug: The entity context identifier.

        Returns:
            List of query variations with entity-specific terms.
        """
        variations = []
        entity_slug_lower = entity_slug.lower()

        if entity_slug_lower in self.entity_terms:
            entity_terms = self.entity_terms[entity_slug_lower]

            # Add queries with related concepts appended
            for related_term in entity_terms:
                if related_term.lower() not in query.lower():
                    variations.append(f"{query} {related_term}")

        return variations

    def _expand_domain_terms(self, query: str) -> List[str]:
        """Generate variations using domain-specific expansions.

        Args:
            query: The query string.

        Returns:
            List of domain-specific query variations.
        """
        variations = []
        query_lower = query.lower()

        # Use module-level domain expansions

        words = query_lower.split()

        for i, word in enumerate(words):
            clean_word = re.sub(r"[^a-z0-9]", "", word)

            if clean_word in DOMAIN_EXPANSIONS:
                for expansion in DOMAIN_EXPANSIONS[clean_word]:
                    new_query = " ".join(
                        expansion if j == i else words[j]
                        for j in range(len(words))
                    )
                    variations.append(new_query)

        return variations


def expand_query_if_enabled(query: str, enabled: bool = True) -> List[str]:
    """Convenience function to expand query if enabled.

    Args:
        query: The query string.
        enabled: Whether expansion is enabled.

    Returns:
        List of query variations, or original query in a list if disabled.
    """
    if not enabled:
        return [query]

    expander = QueryExpander()
    return expander.expand_query(query)


def get_query_suggestions(partial: str, limit: int = 5) -> List[str]:
    """Get query suggestions based on partial input.

    Args:
        partial: The partial query string.
        limit: Maximum number of suggestions to return.

    Returns:
        List of query suggestions.
    """
    expander = QueryExpander()
    return expander.expand_query(partial, max_variations=limit)
