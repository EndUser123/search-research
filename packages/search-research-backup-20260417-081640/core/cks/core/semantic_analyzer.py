"""Semantic Analyzer for CKS
Uses YAKE for keyword extraction and Regex (or Spacy) for entity detection.
"""

import logging
import re
from typing import Any

# Graceful degradation for YAKE
try:
    import yake

    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """Extracts semantic metadata from text."""

    def __init__(self, language: str = "en", n_gram: int = 2, top_k: int = 10) -> None:
        self.language = language
        self.n = n_gram
        self.top = top_k
        self.kw_extractor = None

        if YAKE_AVAILABLE:
            try:
                self.kw_extractor = yake.KeywordExtractor(
                    lan=language,
                    n=n_gram,
                    dedupLim=0.9,
                    top=top_k,
                    features=None,
                )
            except Exception as e:
                logger.exception(f"Failed to init YAKE: {e}")

    def extract_keywords(self, text: str) -> list[tuple]:
        """Extract keywords using YAKE."""
        if not self.kw_extractor:
            return []  # Fallback to regex word freq if YAKE fails? or empty

        try:
            # YAKE returns list of (keyword, score)
            # Lower score = more relevant
            return self.kw_extractor.extract_keywords(text)
        except Exception as e:
            logger.exception(f"YAKE extraction failed: {e}")
            return []

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """Extract Regex-based entities (Emails, URLs, capitalized phrases)."""
        entities = {
            "emails": [],
            "urls": [],
            "concepts": [],  # Capitalized phrases as naive concept detection
        }

        # Emails
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        entities["emails"] = list(set(re.findall(email_pattern, text)))

        # URLs
        url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
        entities["urls"] = list(set(re.findall(url_pattern, text)))

        # Naive "Concept" detection (Capitalized Words sequence)
        # Only if we don't have YAKE or as supplement
        concept_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        # Filter out common starting words if needed, but basic regex is okay for now
        candidates = re.findall(concept_pattern, text)
        entities["concepts"] = list({c for c in candidates if len(c) > 3})

        return entities

    def analyze(self, text: str) -> dict[str, Any]:
        """Full semantic analysis."""
        keywords = self.extract_keywords(text)
        entities = self.extract_entities(text)

        return {
            "keywords": [k[0] for k in keywords],  # Just the words
            "keyword_scores": {k[0]: k[1] for k in keywords},
            "entities": entities,
        }
