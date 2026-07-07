"""Classifier package for cc-model-router.

Provides hierarchical prompt classification with semantic scoring,
deterministic overrides, and confidence-based fallback.

Modules:
  scorer: SemanticScorer interface + ScorerResult dataclass
  tfidf_backend: TF-IDF + cosine similarity backend (default)
  deterministic: High-precision override patterns
  pipeline: Hierarchical classification pipeline (Stage A → B → C)
"""
