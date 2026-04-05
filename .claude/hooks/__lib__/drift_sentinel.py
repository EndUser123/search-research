"""TF-IDF-based drift detection for LLM output vs source documents.

Phase 2 of LLM Behavioral Integrity system.
"""
from __future__ import annotations

import re
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _SKELEARN_AVAILABLE = True
except ImportError:
    _SKELEARN_AVAILABLE = False

# Threshold below which drift is considered detected
_DRIFT_THRESHOLD = 0.75


def extract_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs with 50+ char content.

    Splits on double newlines first, then single newlines.
    Filters out paragraphs shorter than 50 characters.
    """
    if not text:
        return []

    # Split on \n\n first, then on \n for remaining breaks
    parts = re.split(r"\n\n+", text)
    paragraphs: list[str] = []
    for part in parts:
        # Within each double-newline-separated block, also split on single newlines
        sub_parts = re.split(r"\n+", part)
        for sp in sub_parts:
            stripped = sp.strip()
            if len(stripped) >= 50:
                paragraphs.append(stripped)
    return paragraphs


def compute_drift(response_text: str, source_texts: list[str]) -> dict:
    """Compute minimum cosine similarity between response paragraphs and source texts.

    Returns dict with drift_detected (bool) and min_similarity (float).
    Fails open if sklearn unavailable or on errors.
    """
    if not _SKELEARN_AVAILABLE:
        return {"drift_detected": False, "min_similarity": 1.0, "reason": "sklearn unavailable"}

    if not source_texts:
        return {"drift_detected": False, "min_similarity": 1.0, "reason": "no source texts"}

    response_paragraphs = extract_paragraphs(response_text)
    if not response_paragraphs:
        # Fail open: no paragraphs -> no drift detected
        return {"drift_detected": False, "min_similarity": 1.0, "reason": "no paragraphs in response"}

    combined_source = " ".join(source_texts)

    try:
        vectorizer = TfidfVectorizer()
        all_texts = [combined_source] + response_paragraphs
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        source_vector = tfidf_matrix[0]
        response_vectors = tfidf_matrix[1:]

        similarities = cosine_similarity(source_vector, response_vectors)[0]
        min_similarity = float(min(similarities)) if len(similarities) > 0 else 1.0

        return {
            "drift_detected": min_similarity < _DRIFT_THRESHOLD,
            "min_similarity": min_similarity,
        }
    except Exception:
        # Fail open on any error
        return {"drift_detected": False, "min_similarity": 1.0, "reason": "computation error"}


def detect_drift(response_text: str, source_texts: list[str]) -> dict:
    """Main entry point: detect semantic drift in LLM response vs source documents.

    Args:
        response_text: The LLM's generated response
        source_texts: List of source document texts to compare against

    Returns:
        dict with keys:
            drift_detected: bool — True if drift exceeds threshold
            min_similarity: float — minimum cosine similarity across paragraphs
            reason: str — explanation if drift_detected is False (optional)
    """
    return compute_drift(response_text, source_texts)
