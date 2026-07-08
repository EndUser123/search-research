"""TF-IDF semantic scoring backend using sklearn.

Subprocess-safe: no model loading, no cold-start latency.
Fits TfidfVectorizer on exemplar data at init (~1ms for ~36 exemplars).
Computes cosine similarity between prompt and class centroids.

Upgrade seam: swap this class for an EmbeddingBackend that implements
the same SemanticScorer.score() interface to move to persistent embeddings.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .scorer import ScorerResult, SemanticScorer


class TfidfBackend(SemanticScorer):
    """TF-IDF + cosine similarity scorer.

    Fits on exemplar prompts at init time. Each class gets a centroid
    (mean of its exemplar TF-IDF vectors). Prompts are scored by cosine
    similarity to each centroid.
    """

    def __init__(self, exemplars_path: str | Path):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            self._np = np
            self._cosine = cosine_similarity

            with open(exemplars_path, encoding="utf-8") as f:
                self.exemplars = json.load(f)

            # Flatten exemplars into (text, class) pairs
            texts: list[str] = []
            labels: list[str] = []
            for class_name, prompts in self.exemplars.items():
                for p in prompts:
                    texts.append(p)
                    labels.append(class_name)

            self.classes = sorted(set(labels))
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            vectors = self.vectorizer.fit_transform(texts)

            # Precompute class centroids (mean of L2-normalized exemplar vectors)
            self.centroids: dict[str, object] = {}
            for cls in self.classes:
                indices = [i for i, l in enumerate(labels) if l == cls]
                centroid = vectors[indices].mean(axis=0)
                self.centroids[cls] = self._np.asarray(centroid)

            self._ready = True
        except Exception as e:
            self._ready = False
            self._init_error = str(e)
            print(f"[tfidf-backend] init failed: {e}", file=sys.stderr)

    @property
    def ready(self) -> bool:
        return getattr(self, "_ready", False)

    def score(self, prompt: str, context: dict | None = None) -> ScorerResult:
        if not self.ready:
            raise RuntimeError(f"TF-IDF backend not ready: {getattr(self, '_init_error', 'unknown')}")

        prompt_vec = self.vectorizer.transform([prompt])
        scores: dict[str, float] = {}
        for cls in self.classes:
            sim = self._cosine(prompt_vec, self.centroids[cls].reshape(1, -1))[0][0]
            scores[cls] = float(sim)

        # Apply context boost if provided (e.g., previous hint was reasoning).
        # Floor on base score: boost extends a real signal, never creates one.
        # When all base scores are ~0 (short prompts: "proceed", "yes please"),
        # the boost would manufacture a false winner — block it.
        if context and context.get("prev_task_type"):
            prev = context["prev_task_type"]
            boost = context.get("followup_boost", 0.15)
            boost_map = {"reasoning": "reasoning", "coding": "coding",
                         "background": "background", "local-coding": "coding"}
            target = boost_map.get(prev)
            if target and target in scores and scores[target] >= 0.05:
                scores[target] += boost

        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        return ScorerResult(
            class_scores=scores,
            top_class=sorted_scores[0][0],
            confidence=sorted_scores[0][1],
            runner_up=sorted_scores[1][0] if len(sorted_scores) > 1 else "",
            margin=sorted_scores[0][1] - (sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0),
            backend="tfidf",
        )
