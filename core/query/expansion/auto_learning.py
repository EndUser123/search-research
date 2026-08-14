"""Auto-learning query expander that learns from search results."""

import re
from typing import Any, Dict, List
from dataclasses import dataclass


@dataclass
class LearnedMapping:
    """A learned abbreviation or synonym mapping."""

    term: str
    expansion: str
    source_url: str
    confidence: float
    occurrences: int


class AutoLearningQueryExpander:
    """Query expander that learns patterns from successful search results.

    Attributes:
        dry_run: If True, learned mappings are not persisted.
        _learned_mappings: Dictionary of learned term mappings.
    """

    # Pattern to detect "TERM (expansion)" or "TERM (expansion)" patterns
    ABBREV_PATTERN = re.compile(r"\b([A-Z]{2,})\s*\(([^)]+)\)")

    def __init__(self, dry_run: bool = False):
        """Initialize AutoLearningQueryExpander.

        Args:
            dry_run: If True, don't persist learned mappings.
        """
        self.dry_run = dry_run
        self._learned_mappings: Dict[str, LearnedMapping] = {}

    def learn_from_results(
        self,
        query: str,
        successful_results: List[Any],
    ) -> Dict[str, Any]:
        """Learn patterns from successful search results.

        Args:
            query: The original query that was used.
            successful_results: List of SearchResult objects from successful searches.

        Returns:
            Dictionary with learning metadata including unknown_terms,
            learned_mappings, and suggestions.
        """
        unknown_terms = []
        learned_mappings = []
        suggestions = []

        # Process each result for patterns
        for result in successful_results:
            if hasattr(result, "content"):
                content = result.content
            elif isinstance(result, dict):
                content = result.get("content", "")
            else:
                content = str(result)

            # Find abbreviation patterns
            matches = self.ABBREV_PATTERN.findall(content)

            for abbrev, expansion in matches:
                abbrev_lower = abbrev.lower()

                # Skip if we already know this one
                if abbrev_lower not in self._get_known_abbreviations():
                    if abbrev_lower not in self._learned_mappings:
                        learned = LearnedMapping(
                            term=abbrev_lower,
                            expansion=expansion.strip(),
                            source_url=getattr(result, "url", "unknown"),
                            confidence=0.8,
                            occurrences=1,
                        )

                        if not self.dry_run:
                            self._learned_mappings[abbrev_lower] = learned

                        learned_mappings.append({
                            "term": abbrev_lower,
                            "expansion": expansion.strip(),
                        })
                        unknown_terms.append(abbrev_lower)

        return {
            "query": query,
            "unknown_terms": unknown_terms,
            "learned_mappings": learned_mappings,
            "suggestions": suggestions,
            "persisted": not self.dry_run and len(learned_mappings) > 0,
        }

    def get_learned_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get all learned mappings.

        Returns:
            Dictionary of learned term mappings.
        """
        return {
            term: {
                "expansion": mapping.expansion,
                "source_url": mapping.source_url,
                "confidence": mapping.confidence,
                "occurrences": mapping.occurrences,
            }
            for term, mapping in self._learned_mappings.items()
        }

    def list_learned_terms(self) -> List[Dict[str, Any]]:
        """List all learned terms with metadata.

        Returns:
            List of learned term metadata dictionaries.
        """
        return [
            {
                "term": mapping.term,
                "expansion": mapping.expansion,
                "source_url": mapping.source_url,
                "confidence": mapping.confidence,
                "occurrences": mapping.occurrences,
            }
            for mapping in self._learned_mappings.values()
        ]

    def _get_known_abbreviations(self) -> set[str]:
        """Get set of already known abbreviations.

        Returns:
            Set of known abbreviation keys.
        """
        from .abbreviations import get_abbreviation_mappings
        return set(get_abbreviation_mappings().keys())
