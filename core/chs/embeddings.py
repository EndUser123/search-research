"""Embeddings integration for CHS v2.

Provides wrapper classes and utility functions for embedding generation
via the semantic daemon named pipe client.

Usage:
    from search_research.core.chs.embeddings import get_embed_client

    client = get_embed_client()
    embeddings = client.embed_texts(["hello world", "test"])
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass
logger = logging.getLogger(__name__)
DEFAULT_EMBEDDING_DIM = 384
MAX_RETRIES = 2
RETRY_DELAY = 0.5

# Module-level cache for direct SentenceTransformer fallback (when daemon unavailable)
_st_model: "SentenceTransformer | None" = None
_st_model_last_used: float = 0.0
_ST_MODEL_TTL_SECONDS: float = 300.0  # 5 minutes


def _get_st_model() -> "SentenceTransformer":
    """Get or create cached SentenceTransformer, unloading after 5 min idle.

    Releases the model to free memory when no embeddings have been requested
    for 5 minutes. Subsequent calls re-load from scratch (~60s cold start).
    """
    global _st_model, _st_model_last_used
    now = time.monotonic()

    if _st_model is not None and (now - _st_model_last_used) > _ST_MODEL_TTL_SECONDS:
        del _st_model
        _st_model = None

    if _st_model is None:
        from sentence_transformers import SentenceTransformer

        _st_model = SentenceTransformer("all-MiniLM-L6-v2")

    _st_model_last_used = time.monotonic()
    return _st_model


def _reset_st_model_cache() -> None:
    """Reset the SentenceTransformer cache. For testing only."""
    global _st_model, _st_model_last_used
    _st_model = None
    _st_model_last_used = 0.0


class EmbedClient:
    """Wrapper class for daemon_client with retry/backoff and fallback.

    This class wraps the DaemonClient to provide embedding generation
    functionality with automatic retry logic and fallback to direct
    SentenceTransformer when the daemon is unavailable.

    Attributes:
        daemon_client: The underlying DaemonClient instance
    """

    def __init__(self, daemon_client):
        """Initialize EmbedClient with a daemon_client instance.

        Args:
            daemon_client: A DaemonClient instance for communicating
                with the semantic daemon via named pipe
        """
        self.daemon_client = daemon_client

    def embed_texts(self, texts: list[str]) -> list[bytes]:
        """Generate embeddings for a list of texts.

        Uses the daemon_client.embed_texts() method with retry logic
        on connection failures. Falls back to direct SentenceTransformer
        (loaded on-demand with 5-minute TTL) if daemon is unavailable.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors as bytes (serialized numpy arrays)

        Raises:
            ConnectionError: If daemon is unavailable and fallback
                is not enabled on the underlying client
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                if hasattr(self.daemon_client, "embed_texts"):
                    result = self.daemon_client.embed_texts(texts)
                    if isinstance(result, bytes):
                        return [result]
                    return result
                else:
                    logger.warning(
                        "daemon_client.embed_texts not available, falling back to direct SentenceTransformer"
                    )
                    return self._direct_embed(texts)
            except ConnectionError as e:
                if attempt < MAX_RETRIES:
                    logger.debug(f"Retry {attempt + 1}/{MAX_RETRIES}: {e}")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.warning(f"All retries exhausted, falling back to direct SentenceTransformer: {e}")
                    return self._direct_embed(texts)
            except Exception as e:
                logger.warning(f"Unexpected error: {e}, falling back to direct SentenceTransformer")
                return self._direct_embed(texts)
        return self._direct_embed(texts)

    def _direct_embed(self, texts: list[str]) -> list[bytes]:
        """Generate embeddings using direct SentenceTransformer (daemon unavailable fallback).

        Loads the SentenceTransformer model on first use and keeps it cached
        for 5 minutes of idle time before unloading to free memory.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors as bytes (serialized numpy arrays)
        """
        model = _get_st_model()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [vec.astype(np.float32).tobytes() for vec in vectors]


def validate_embedding_blob(blob: bytes, expected_dim: int) -> None:
    """Validate an embedding blob has the correct dimensions.

    Args:
        blob: Embedding as bytes (serialized numpy array)
        expected_dim: Expected embedding dimension

    Raises:
        ValueError: If blob size doesn't match expected dimension
    """
    expected_size = expected_dim * 4
    actual_size = len(blob)
    if actual_size != expected_size:
        raise ValueError(
            f"Embedding size mismatch: expected {expected_size} bytes ({expected_dim} * 4 bytes/float32), got {actual_size} bytes"
        )


def validate_embedding_array(array: np.ndarray, expected_dim: int) -> None:
    """Validate an embedding array has correct shape and dtype.

    Args:
        array: Embedding as numpy array
        expected_dim: Expected embedding dimension

    Raises:
        ValueError: If array shape or dtype is incorrect
    """
    if array.shape != (expected_dim,):
        raise ValueError(f"Embedding shape mismatch: expected ({expected_dim},), got {array.shape}")
    if array.dtype != np.float32:
        raise ValueError(f"Embedding dtype must be float32, got {array.dtype}")


def bytes_to_vector(blob: bytes, dim: int) -> np.ndarray:
    """Convert embedding blob bytes to numpy array.

    Args:
        blob: Embedding as bytes (serialized numpy array)
        dim: Expected embedding dimension

    Returns:
        Numpy array of shape (dim,) with dtype float32
    """
    return np.frombuffer(blob, dtype=np.float32, count=dim)


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec_a: First vector (numpy array)
        vec_b: Second vector (numpy array)

    Returns:
        Cosine similarity score between 0.0 and 1.0
        Returns 0.0 if either vector is a zero vector
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    dot_product = np.dot(vec_a, vec_b)
    similarity = dot_product / (norm_a * norm_b)
    return float(similarity)


_embed_client_singleton: EmbedClient | None = None


def get_embed_client() -> EmbedClient:
    """Get the singleton EmbedClient instance.

    Creates a new EmbedClient on first call, returns cached instance
    on subsequent calls.

    Returns:
        The singleton EmbedClient instance
    """
    global _embed_client_singleton
    if _embed_client_singleton is None:
        from search_research.contrib.semantic_daemon.daemon_client import DaemonClient

        daemon_client = DaemonClient(backend_type="chs", auto_start=True, enable_fallback=True)
        _embed_client_singleton = EmbedClient(daemon_client=daemon_client)
    return _embed_client_singleton


def reset_embed_client() -> None:
    """Reset the singleton EmbedClient instance.

    This is primarily for testing purposes.
    """
    global _embed_client_singleton
    _embed_client_singleton = None
