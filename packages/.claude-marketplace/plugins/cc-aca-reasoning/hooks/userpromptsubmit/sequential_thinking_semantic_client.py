"""Semantic trigger detection via daemon-shared embeddings.

This module provides embedding-based semantic trigger detection for sequential thinking,
sharing the model across all terminals via the unified_semantic_daemon.

Fallback chain:
1. Try daemon IPC (compute_embedding action + local cosine similarity)
2. Fall back to direct SentenceTransformer loading if daemon unavailable
3. Fall back to regex-only if semantic computation fails completely

The trigger phrase embeddings are cached locally after first computation to avoid
repeated IPC for the same phrases.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from daemons.daemon_client import DaemonClient

# Ensure __lib is importable (hooks dir is already in sys.path via UserPromptSubmit.py)
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Canonical trigger phrases representing analytical intent
_ANALYTICAL_TRIGGER_PHRASES = [
    # Analysis & evaluation
    "analyze the code for issues",
    "evaluate the design choices",
    "assess the architecture",
    "examine the implementation",
    "investigate the root cause",
    "review the changes",
    "explain why this is happening",
    "understand what went wrong",
    # Problem-solving
    "debug the connection issue",
    "diagnose the performance problem",
    "troubleshoot the error",
    "identify why this fails",
    "find the root cause",
    # Design decisions
    "should we refactor this module",
    "which approach is better",
    "compare these two solutions",
    "what are the tradeoffs",
    # Architecture
    "how should this be structured",
    "design a system for scalability",
    "architect the service properly",
    # Complex reasoning
    "why does the request timeout",
    "how does the caching work",
    "what causes the deadlock",
    # Meta-analytical
    "would this approach work",
    "could this cause issues",
    "should this be handled differently",
]

# Lazy-loaded state
_trigger_embeddings_cache: Optional[list[list[float]]] = None
_trigger_phrases_cache: list[str] = []
_daemon_client: Optional[DaemonClient] = None


def _get_daemon_client() -> DaemonClient:
    """Get or create the DaemonClient singleton."""
    global _daemon_client
    if _daemon_client is None:
        from daemons.daemon_client import DaemonClient

        _daemon_client = DaemonClient(auto_start=True, enable_fallback=True)
    return _daemon_client


def _get_trigger_embeddings() -> tuple[list[list[float]], list[str]]:
    """Get cached trigger phrase embeddings, computing if needed.

    Returns:
        Tuple of (embeddings, phrases) where embeddings is list of embedding vectors.
    """
    global _trigger_embeddings_cache, _trigger_phrases_cache

    if _trigger_embeddings_cache is None:
        _trigger_phrases_cache = list(_ANALYTICAL_TRIGGER_PHRASES)
        embeddings = []

        # Try daemon first - call just to ensure client is initialized
        _get_daemon_client()
        for phrase in _trigger_phrases_cache:
            embedding = _compute_embedding_via_daemon(phrase)
            if embedding:
                embeddings.append(embedding)
            else:
                # Daemon failed, fall back to direct model
                logger.debug("Falling back to direct SentenceTransformer for trigger embeddings")
                return _compute_trigger_embeddings_direct()

        _trigger_embeddings_cache = embeddings

    return _trigger_embeddings_cache, _trigger_phrases_cache


def _compute_embedding_via_daemon(text: str) -> Optional[list[float]]:
    """Compute embedding for text via daemon IPC.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector as list of floats, or None if daemon unavailable.
    """
    client = _get_daemon_client()
    response = client.query("compute_embedding", {"text": text})

    # Check response status - DaemonClient returns status field, not exceptions
    if response.get("status") != "success":
        logger.debug(f"Daemon compute_embedding failed: {response.get('error', 'unknown')}")
        return None

    result = response.get("result", {})
    embedding = result.get("embedding")

    if not embedding or not isinstance(embedding, list):
        logger.debug("Daemon returned malformed embedding response")
        return None

    return embedding


def _compute_embedding_direct(text: str) -> Optional[list[float]]:
    """Compute embedding for text via direct SentenceTransformer.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector as list of floats, or None on failure.
    """
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = model.encode(text, normalize_embeddings=True).tolist()
        return embedding
    except Exception as e:
        logger.debug(f"Direct SentenceTransformer failed: {e}")
        return None


def _compute_trigger_embeddings_direct() -> tuple[list[list[float]], list[str]]:
    """Compute trigger embeddings directly via SentenceTransformer (fallback).

    Returns:
        Tuple of (embeddings, phrases).
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    phrases = list(_ANALYTICAL_TRIGGER_PHRASES)
    embeddings = model.encode(phrases, normalize_embeddings=True).tolist()

    # Update cache
    global _trigger_embeddings_cache, _trigger_phrases_cache
    _trigger_embeddings_cache = embeddings
    _trigger_phrases_cache = phrases

    return embeddings, phrases


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity score (0.0 to 1.0 for normalized vectors).
    """
    dot_product = sum(x * y for x, y in zip(a, b))
    return dot_product


def _compute_prompt_embedding(prompt: str) -> Optional[list[float]]:
    """Compute embedding for a user prompt.

    Args:
        prompt: User prompt to embed.

    Returns:
        Embedding vector as list of floats, or None on failure.
    """
    # Try daemon first
    embedding = _compute_embedding_via_daemon(prompt)
    if embedding:
        return embedding

    # Fall back to direct model
    return _compute_embedding_direct(prompt)


def compute_similarity(prompt: str) -> tuple[float, Optional[str]]:
    """Compute semantic similarity between prompt and trigger phrases.

    Args:
        prompt: User prompt to evaluate.

    Returns:
        Tuple of (max_similarity_score, best_matching_phrase).
        Returns (0.0, None) if no daemon available and direct model fails.
    """
    # Get trigger embeddings
    trigger_embeddings, trigger_phrases = _get_trigger_embeddings()

    # Compute prompt embedding
    prompt_embedding = _compute_prompt_embedding(prompt)
    if prompt_embedding is None:
        # Both daemon and direct model failed
        return 0.0, None

    # Find best matching trigger phrase
    best_score = 0.0
    best_phrase: Optional[str] = None

    for i, trigger_emb in enumerate(trigger_embeddings):
        score = _cosine_similarity(prompt_embedding, trigger_emb)
        if score > best_score:
            best_score = score
            best_phrase = trigger_phrases[i]

    return float(best_score), best_phrase
