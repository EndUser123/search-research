"""SemanticScorer interface and ScorerResult dataclass.

The scorer produces class scores for a prompt. The pipeline uses these scores
to make hierarchical routing decisions (background vs active → reasoning vs coding).

Backends:
  - tfidf: TF-IDF + cosine similarity (default, subprocess-safe, ~1ms)
  - fallback-rules: existing regex/keyword classifier (backward compat)
  - embedding-daemon: future persistent embedding service (seam preserved)
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScorerResult:
    """Result of scoring a prompt against class exemplars."""
    class_scores: dict[str, float]
    top_class: str
    confidence: float
    runner_up: str
    margin: float
    backend: str = "tfidf"


class SemanticScorer:
    """Abstract interface for semantic scoring backends.

    Implementations must provide score(prompt, context) -> ScorerResult.
    The pipeline calls this once per prompt and uses the result for
    hierarchical routing decisions.
    """

    def score(self, prompt: str, context: dict | None = None) -> ScorerResult:
        raise NotImplementedError("Subclass must implement score()")
