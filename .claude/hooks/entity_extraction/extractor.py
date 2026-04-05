"""
Entity Extractor - Core orchestrator for entity extraction.

Coordinates multiple strategies with fallback chain:
1. Structural extraction (definite entities from code context)
2. Heuristic extraction (pattern-based with blocklist)
3. Semantic validation (optional, embedding-based)

Solo-dev appropriate: No background services, lazy loading, env-var controls.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Set

# Configuration via environment
SEMANTIC_ENABLED = os.environ.get("ENTITY_SEMANTIC_ENABLED", "true").lower() == "true"
DEBUG = os.environ.get("ENTITY_EXTRACTOR_DEBUG", "false").lower() == "true"

# Confidence thresholds
STRUCTURAL_CONFIDENCE = 0.95  # Backticks, file paths - definitely entities
HEURISTIC_CONFIDENCE = 0.70   # Pattern matches with context
SEMANTIC_CONFIDENCE = 0.85    # Embedding-validated entities


@dataclass
class ExtractedEntity:
    """An extracted entity with metadata."""
    text: str
    normalized: str
    source: str  # 'structural', 'heuristic', 'semantic'
    confidence: float
    context: str = ""  # Surrounding text for debugging

    def __hash__(self):
        return hash(self.normalized)

    def __eq__(self, other):
        if isinstance(other, ExtractedEntity):
            return self.normalized == other.normalized
        return self.normalized == str(other).lower()


@dataclass
class ExtractionResult:
    """Result of entity extraction."""
    entities: Set[ExtractedEntity] = field(default_factory=set)
    structural: Set[str] = field(default_factory=set)  # High confidence
    heuristic: Set[str] = field(default_factory=set)   # Medium confidence
    semantic: Set[str] = field(default_factory=set)    # Validated
    rejected: Set[str] = field(default_factory=set)    # Filtered out

    def all_normalized(self) -> Set[str]:
        """Get all entity strings (normalized)."""
        return {e.normalized for e in self.entities}

    def high_confidence(self) -> Set[str]:
        """Get only high-confidence entities."""
        return self.structural | self.semantic


class EntityExtractor:
    """
    Main extractor coordinating multiple strategies.
    
    Usage:
        extractor = EntityExtractor()
        result = extractor.extract(text, context_type='claim')
        entities = result.all_normalized()
    """

    def __init__(self,
                 enable_semantic: bool = None,
                 semantic_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize extractor.
        
        Args:
            enable_semantic: Override env var for semantic extraction
            semantic_model: Sentence-transformers model name
        """
        self._enable_semantic = enable_semantic if enable_semantic is not None else SEMANTIC_ENABLED
        self._semantic_model = semantic_model

        # Lazy-loaded strategies
        self._structural = None
        self._heuristic = None
        self._semantic = None

    @property
    def structural(self):
        """Lazy load structural strategy."""
        if self._structural is None:
            from .strategies import StructuralStrategy
            self._structural = StructuralStrategy()
        return self._structural

    @property
    def heuristic(self):
        """Lazy load heuristic strategy."""
        if self._heuristic is None:
            from .strategies import HeuristicStrategy
            self._heuristic = HeuristicStrategy()
        return self._heuristic

    @property
    def semantic(self):
        """Lazy load semantic strategy (expensive - loads model)."""
        if self._semantic is None and self._enable_semantic:
            try:
                from .strategies import SemanticStrategy
                self._semantic = SemanticStrategy(model_name=self._semantic_model)
            except ImportError as e:
                if DEBUG:
                    print(f"[entity_extractor] Semantic disabled: {e}")
                self._enable_semantic = False
        return self._semantic

    def extract(self,
                text: str,
                context_type: str = 'claim',
                tool_outputs: List[str] = None) -> ExtractionResult:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            context_type: 'claim' (response text) or 'evidence' (tool outputs)
            tool_outputs: Optional list of tool outputs for evidence extraction
            
        Returns:
            ExtractionResult with categorized entities
        """
        result = ExtractionResult()

        if not text:
            return result

        # Stage 1: Structural extraction (highest confidence)
        structural_entities = self.structural.extract(text)
        for entity in structural_entities:
            result.entities.add(ExtractedEntity(
                text=entity,
                normalized=self._normalize(entity),
                source='structural',
                confidence=STRUCTURAL_CONFIDENCE
            ))
            result.structural.add(self._normalize(entity))

        # Stage 2: Heuristic extraction (medium confidence)
        heuristic_candidates = self.heuristic.extract(text)

        for entity in heuristic_candidates:
            normalized = self._normalize(entity)

            # Skip if already found structurally
            if normalized in result.structural:
                continue

            # Check against blocklist
            if self.heuristic.is_blocked(normalized):
                result.rejected.add(normalized)
                continue

            result.heuristic.add(normalized)

        # Stage 3: Semantic validation (optional, validates heuristic)
        if self._enable_semantic and self.semantic and result.heuristic:
            validated = self.semantic.validate(list(result.heuristic), text)

            for entity in validated:
                result.entities.add(ExtractedEntity(
                    text=entity,
                    normalized=entity,
                    source='semantic',
                    confidence=SEMANTIC_CONFIDENCE
                ))
                result.semantic.add(entity)
                result.heuristic.discard(entity)

            # Remaining heuristic entities not validated - lower confidence
            for entity in list(result.heuristic):
                result.entities.add(ExtractedEntity(
                    text=entity,
                    normalized=entity,
                    source='heuristic',
                    confidence=HEURISTIC_CONFIDENCE * 0.7  # Penalty for no semantic validation
                ))
        else:
            # No semantic - trust heuristic at base confidence
            for entity in result.heuristic:
                result.entities.add(ExtractedEntity(
                    text=entity,
                    normalized=entity,
                    source='heuristic',
                    confidence=HEURISTIC_CONFIDENCE
                ))

        if DEBUG:
            print(f"[entity_extractor] Structural: {result.structural}")
            print(f"[entity_extractor] Heuristic: {result.heuristic}")
            print(f"[entity_extractor] Semantic: {result.semantic}")
            print(f"[entity_extractor] Rejected: {result.rejected}")

        return result

    def _normalize(self, entity: str) -> str:
        """Normalize entity for comparison."""
        if not entity:
            return ""
        # Lowercase, forward slashes, strip quotes/whitespace
        normalized = entity.strip('"\'`').replace("\\", "/").lower().strip()
        # Remove trailing parenthesis fragments
        normalized = re.sub(r'\s*\($', '', normalized)
        return normalized


# Module-level convenience function
_default_extractor = None

def extract_entities(text: str, context_type: str = 'claim') -> Set[str]:
    """
    Convenience function for entity extraction.
    
    Returns set of normalized entity strings.
    """
    global _default_extractor
    if _default_extractor is None:
        _default_extractor = EntityExtractor()

    result = _default_extractor.extract(text, context_type)
    return result.all_normalized()
