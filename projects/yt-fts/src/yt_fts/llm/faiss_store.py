"""
FAISS Vector Store for yt-fts

Provides efficient vector similarity search using FAISS (Facebook AI Similarity Search).
Stores embeddings in SQLite and builds FAISS indices for fast semantic search.
"""
from __future__ import annotations

import json
import os
import pickle
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from yt_fts.utils.config import get_config_path, get_db_path


class FaissVectorStore:
    """
    FAISS-based vector store for semantic search.

    Manages embeddings storage in SQLite and FAISS indices for fast similarity search.
    """

    # Default embedding dimension for all-MiniLM-L6-v2
    DEFAULT_DIM = 384
    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        db_path: str | None = None,
        model_name: str = DEFAULT_MODEL,
        dim: int = DEFAULT_DIM,
        use_scalar_quantization: bool | None = None,
    ):
        """
        Initialize the FAISS vector store.

        Args:
            db_path: Path to SQLite database (uses default if None)
            model_name: Name of the embedding model
            dim: Embedding dimension
            use_scalar_quantization: Use scalar quantization (75% memory reduction).
                Reads from YT_FTS_USE_SQ env var if None (default: enabled).
        """
        self.db_path = db_path or get_db_path()
        self.model_name = model_name
        self.dim = dim

        # Scalar quantization: enabled by default for 75% memory reduction
        if use_scalar_quantization is None:
            use_scalar_quantization = os.getenv("YT_FTS_USE_SQ", "true").lower() != "false"
        self.use_scalar_quantization = use_scalar_quantization
        config_path = get_config_path()
        if config_path is None:
            msg = "get_config_path() returned None"
            raise ValueError(msg)
        self.index_dir = Path(config_path) / "faiss_indices"
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def get_index_path(self, channel_id: str) -> Path:
        """Get the file path for a channel's FAISS index."""
        return self.index_dir / f"{channel_id}.faiss"

    def get_metadata_path(self, channel_id: str) -> Path:
        """Get the file path for a channel's index metadata."""
        return self.index_dir / f"{channel_id}.meta.json"

    def index_exists(self, channel_id: str) -> bool:
        """Check if FAISS index exists for a channel."""
        return self.get_index_path(channel_id).exists()

    def build_index(
        self,
        channel_id: str,
        force_rebuild: bool = False,
    ) -> bool:
        """
        Build FAISS index for a channel from database embeddings.

        Args:
            channel_id: YouTube channel ID
            force_rebuild: Rebuild even if index exists

        Returns:
            True if successful, False otherwise
        """
        if not force_rebuild and self.index_exists(channel_id):
            return True

        try:
            # Load embeddings from database
            embeddings, metadata = self._load_embeddings_from_db(channel_id)

            if len(embeddings) == 0:
                return False

            # Create FAISS index (Inner Product for cosine similarity)
            # Normalize embeddings for cosine similarity
            normalized_embeddings = self._normalize_embeddings(embeddings)

            # Create index
            if self.use_scalar_quantization:
                # Use scalar quantization for 75% memory reduction
                # QT_8bit provides good balance of compression and accuracy
                index = faiss.IndexScalarQuantizer(
                    self.dim,
                    faiss.ScalarQuantizer.QT_8bit,
                    faiss.METRIC_INNER_PRODUCT
                )
                # Train the quantizer on the data
                if not index.is_trained:
                    index.train(normalized_embeddings)
            else:
                index = faiss.IndexFlatIP(self.dim)
            index.add(normalized_embeddings)

            # Save index
            self._save_index(channel_id, index, metadata)

            return True

        except Exception as e:
            print(f"Error building FAISS index for channel {channel_id}: {e}")
            return False

    def search(
        self,
        query_embedding: np.ndarray,
        channel_id: str,
        k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search for similar subtitles using FAISS.

        Args:
            query_embedding: Query embedding vector
            channel_id: Channel to search
            k: Number of results to return

        Returns:
            List of search results with metadata
        """
        if not self.index_exists(channel_id) and not self.build_index(channel_id):
            # Build index if it doesn't exist
                return []

        try:
            # Load index
            index, metadata = self._load_index(channel_id)

            # Normalize query embedding for cosine similarity
            query_embedding = query_embedding.reshape(1, -1)
            normalized_query = self._normalize_embeddings(query_embedding)

            # Search
            distances, indices = index.search(normalized_query, k)

            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0], strict=False):
                if idx < len(metadata):
                    result = metadata[idx].copy()
                    result["similarity"] = float(dist)
                    results.append(result)

            return results

        except Exception as e:
            print(f"Error searching FAISS index: {e}")
            return []

    def _load_embeddings_from_db(
        self, channel_id: str
    ) -> tuple[np.ndarray, list[dict[str, Any]]]:
        """
        Load embeddings for a channel from the database.

        Returns:
            Tuple of (embeddings array, metadata list)
        """
        query = """
            SELECT
                s.subtitle_id, s.video_id, e.embedding, s.start_time, s.text,
                v.video_title, c.channel_name
            FROM embeddings e
            JOIN Subtitles s ON e.subtitle_id = s.subtitle_id
            JOIN Videos v ON s.video_id = v.video_id
            JOIN Channels c ON v.channel_id = c.channel_id
            WHERE e.channel_id = ?
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (channel_id,))
            rows = cursor.fetchall()

        if not rows:
            return np.array([]), []

        embeddings = []
        metadata = []

        for row in rows:
            subtitle_id, video_id, embedding_blob, start_time, text, video_title, channel_name = row

            # Deserialize embedding
            embedding = pickle.loads(embedding_blob)
            embeddings.append(embedding)

            metadata.append({
                "subtitle_id": subtitle_id,
                "video_id": video_id,
                "start_time": start_time,
                "text": text,
                "video_title": video_title,
                "channel_name": channel_name,
                "channel_id": channel_id,
            })

        return np.array(embeddings, dtype=np.float32), metadata

    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Normalize embeddings for cosine similarity using FAISS Inner Product.

        Args:
            embeddings: Input embeddings

        Returns:
            L2-normalized embeddings
        """
        # L2 normalize for cosine similarity with Inner Product
        faiss.normalize_L2(embeddings)
        return embeddings

    def _save_index(
        self,
        channel_id: str,
        index: faiss.Index,
        metadata: list[dict[str, Any]],
    ) -> None:
        """Save FAISS index and metadata to disk."""
        index_path = self.get_index_path(channel_id)
        meta_path = self.get_metadata_path(channel_id)

        # Save FAISS index
        faiss.write_index(index, str(index_path))

        # Save metadata
        metadata_dict = {
            "channel_id": channel_id,
            "model_name": self.model_name,
            "dim": self.dim,
            "num_vectors": len(metadata),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scalar_quantization": self.use_scalar_quantization,
            "metadata": metadata,
        }

        with open(meta_path, "w") as f:
            json.dump(metadata_dict, f)

    def _load_index(
        self, channel_id: str
    ) -> tuple[faiss.Index, list[dict[str, Any]]]:
        """Load FAISS index and metadata from disk."""
        index_path = self.get_index_path(channel_id)
        meta_path = self.get_metadata_path(channel_id)

        # Load FAISS index
        index = faiss.read_index(str(index_path))

        # Load metadata
        with open(meta_path) as f:
            metadata_dict = json.load(f)

        return index, metadata_dict["metadata"]

    def delete_index(self, channel_id: str) -> bool:
        """
        Delete FAISS index for a channel.

        Args:
            channel_id: Channel ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            index_path = self.get_index_path(channel_id)
            meta_path = self.get_metadata_path(channel_id)

            if index_path.exists():
                index_path.unlink()
            if meta_path.exists():
                meta_path.unlink()

            return True
        except (ImportError, ValueError, RuntimeError, OSError):
            return False

    def get_index_info(self, channel_id: str) -> dict[str, Any] | None:
        """
        Get information about a channel's index.

        Args:
            channel_id: Channel ID

        Returns:
            Dictionary with index info or None if not found
        """
        meta_path = self.get_metadata_path(channel_id)

        if not meta_path.exists():
            return None

        with open(meta_path) as f:
            metadata_dict = json.load(f)

        return {
            "channel_id": metadata_dict["channel_id"],
            "model_name": metadata_dict["model_name"],
            "num_vectors": metadata_dict["num_vectors"],
            "created_at": metadata_dict["created_at"],
        }

    def count_embeddings(self, channel_id: str) -> int:
        """
        Count embeddings for a channel in the database.

        Args:
            channel_id: Channel ID

        Returns:
            Number of embeddings
        """
        query = "SELECT COUNT(*) FROM embeddings WHERE channel_id = ?"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (channel_id,))
            result = cursor.fetchone()
            return result[0] if result else 0



def get_embedding_dim(model_name: str = "all-MiniLM-L6-v2") -> int:
    """
    Get the embedding dimension for a model.

    Args:
        model_name: Name of the sentence-transformers model

    Returns:
        Embedding dimension
    """
    # Known dimensions for common models
    dimensions = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "paraphrase-MiniLM-L6-v2": 384,
        "paraphrase-mpnet-base-v2": 768,
    }
    return dimensions.get(model_name, 384)  # Default to 384
