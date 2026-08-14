"""Vector Knowledge Manager - FIXED
Implements FAISS + Hybrid Embedding Router with Lazy Loading and Graceful Degradation.
"""

import logging
import uuid
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

# FAISS Vector Store (replaces Qdrant)
try:
    import faiss
    import numpy as np

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from fastembed import TextEmbedding

    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_AVAILABLE = True
except ImportError:
    SENTENCE_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorConfig(BaseSettings):
    """Configuration for Vector Manager (FAISS-based)."""

    index_path: str | None = None
    collection_name: str = "knowledge"
    embedding_model_fast: str = "BAAI/bge-small-en-v1.5"
    embedding_model_quality: str = "all-MiniLM-L6-v2"

    class Config:
        env_prefix = "CKS_VECTOR_"


class EmbeddingRouter:
    """Routes embedding requests. Lazy loads models to save RAM."""

    def __init__(self, config: VectorConfig) -> None:
        self.config = config
        self._fast_model = None
        self._quality_model = None
        self._fast_failed = False  # Circuit breaker

    def _load_fast_model(self) -> None:
        if not self._fast_model and not self._fast_failed and FASTEMBED_AVAILABLE:
            try:
                logger.info(
                    f"Loading FastEmbed model: {self.config.embedding_model_fast}",
                )
                self._fast_model = TextEmbedding(
                    model_name=self.config.embedding_model_fast,
                )
            except Exception as e:
                logger.exception(f"Failed to load FastEmbed: {e}")
                self._fast_failed = True

    def _load_quality_model(self) -> None:
        if not self._quality_model and SENTENCE_AVAILABLE:
            logger.info(
                f"Loading Quality model (SentenceTransformers): {self.config.embedding_model_quality}",
            )
            self._quality_model = SentenceTransformer(
                self.config.embedding_model_quality,
            )

    def embed_query(self, text: str, mode: str = "fast") -> list[float]:
        """Generate embedding with fallback strategies."""
        # Strategy 1: Quality Mode (if requested and available)
        if mode == "quality" and SENTENCE_AVAILABLE:
            self._load_quality_model()
            if self._quality_model:
                return self._quality_model.encode(text).tolist()

        # Strategy 2: Fast Mode (Primary)
        self._load_fast_model()
        if self._fast_model:
            try:
                return next(iter(self._fast_model.embed([text]))).tolist()
            except Exception as e:
                logger.exception(f"FastEmbedding failed: {e}")

        # Fallback to Sentence Transformers if FastEmbed is missing
        if SENTENCE_AVAILABLE:
            self._load_quality_model()
            if self._quality_model:
                return self._quality_model.encode(text).tolist()

        # Strategy 3: Fallback / Degradation
        # If we can't embed, we return a zero-vector so system doesn't crash,
        # but warn so caller knows semantics are lost.
        logger.warning(
            f"Embedding unavailable for '{text[:20]}...'. Using zero vector.",
        )
        return [0.0] * 384

    def embed_documents(
        self,
        texts: list[str],
        mode: str = "fast",
    ) -> list[list[float]]:
        self._load_fast_model()
        if self._fast_model:
            return [v.tolist() for v in self._fast_model.embed(texts)]
        return [[0.0] * 384 for _ in texts]


class VectorKnowledgeManager:
    """Manages Vector Store operations using FAISS."""

    def __init__(self, config: VectorConfig | None = None) -> None:
        self.config = config or VectorConfig()
        self.router = EmbeddingRouter(self.config)
        self.index = None
        self.ids = []
        self.metadata = []
        self.degraded_mode = False
        self._dimension = 384  # Default embedding dimension

        if FAISS_AVAILABLE:
            self._init_faiss()
        else:
            logger.warning(
                "FAISS not installed. Running in DEGRADED mode (no semantic search).",
            )
            self.degraded_mode = True

    def _init_faiss(self) -> None:
        try:
            import pickle

            # Default index path
            if self.config.index_path is None:
                index_path = Path("P:\\\\\\__csf/data/cks_vector.faiss")
            else:
                index_path = Path(self.config.index_path)

            self.index_path = index_path

            # Try to load existing index
            if index_path.exists():
                metadata_path = index_path.with_suffix(".pkl")
                if metadata_path.exists():
                    with open(metadata_path, "rb") as f:
                        data = pickle.load(f)
                        self.ids = data.get("ids", [])
                        self.metadata = data.get("metadata", [])
                        self._dimension = data.get("dimension", 384)

                    # Load FAISS index
                    self.index = faiss.read_index(str(index_path))
                    logger.info(
                        f"Loaded FAISS index from {index_path} with {self.index.ntotal} vectors"
                    )
                else:
                    # Create new index
                    self._create_index()
            else:
                self._create_index()
                index_path.parent.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.exception(f"Failed to initialize FAISS: {e}")
            self.index = None
            self.degraded_mode = True

    def _create_index(self) -> None:
        """Create a new FAISS index."""
        # Use IndexFlatIP (inner product) for cosine similarity with normalized vectors
        self.index = faiss.IndexFlatIP(self._dimension)
        self.ids = []
        self.metadata = []
        logger.info(f"Created new FAISS index with dimension {self._dimension}")

    def ingest(self, id: str, text: str, metadata: dict[str, Any] | None = None) -> bool:
        if self.degraded_mode or self.index is None:
            return False

        try:
            vector = self.router.embed_query(text, mode="fast")
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, id))

            # Normalize vector for cosine similarity
            import numpy as np

            vector_np = np.array(vector, dtype=np.float32)
            faiss.normalize_L2(vector_np)

            # Add to index
            self.index.add(vector_np.reshape(1, -1))
            self.ids.append(point_id)
            self.metadata.append(
                {
                    "original_id": id,
                    "content": text,
                    **(metadata or {}),
                }
            )

            # Persist to disk
            self._save()
            return True
        except Exception as e:
            logger.exception(f"Vector ingest failed: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Search with fallback."""
        if self.degraded_mode or self.index is None or self.index.ntotal == 0:
            return []

        try:
            import numpy as np

            vector = self.router.embed_query(query, mode="fast")
            query_np = np.array(vector, dtype=np.float32).reshape(1, -1)
            faiss.normalize_L2(query_np)

            # Search
            scores, indices = self.index.search(query_np, min(limit, self.index.ntotal))

            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0], strict=False):
                if idx >= 0 and idx < len(self.metadata) and score >= threshold:
                    results.append(
                        {
                            "id": self.metadata[idx].get("original_id", self.ids[idx]),
                            "score": float(score),
                            "payload": self.metadata[idx],
                        }
                    )

            return results
        except Exception as e:
            logger.exception(f"Vector search failed: {e}")
            return []

    def _save(self) -> None:
        """Save index and metadata to disk."""
        try:
            import pickle

            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))

            # Save metadata
            metadata_path = self.index_path.with_suffix(".pkl")
            with open(metadata_path, "wb") as f:
                pickle.dump(
                    {
                        "ids": self.ids,
                        "metadata": self.metadata,
                        "dimension": self._dimension,
                    },
                    f,
                )
        except Exception as e:
            logger.warning(f"Failed to save FAISS index: {e}")

    def close(self) -> None:
        """Save and close."""
        if self.index is not None:
            self._save()
