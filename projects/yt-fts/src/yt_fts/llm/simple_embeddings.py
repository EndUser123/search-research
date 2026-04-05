"""
Semantic Embeddings Handler for yt-fts

Provides real semantic embeddings using sentence-transformers.
"""
from __future__ import annotations

import logging
import pickle
import sqlite3
from datetime import datetime, timezone
from typing import Any

import numpy as np
from rich.progress import track
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SemanticEmbeddingsHandler:
    """Semantic embeddings handler using sentence-transformers."""

    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    BATCH_SIZE = 32

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def get_embedding(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def get_embeddings_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        return self.model.encode(texts, batch_size=self.BATCH_SIZE, convert_to_numpy=True, show_progress_bar=False)

    def similarity_search(self, query_embedding: np.ndarray, document_embeddings: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        similarities = self._cosine_similarity_batch(query_embedding, document_embeddings)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [{"index": int(idx), "similarity": float(similarities[idx]), "embedding": document_embeddings[idx]} for idx in top_indices]

    def search_similar(self, query: str, texts: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        query_embedding = self.get_embedding(query)
        document_embeddings = self.get_embeddings_batch(texts)
        similarities = self._cosine_similarity_batch(query_embedding, document_embeddings)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [{"text": texts[idx], "index": int(idx), "similarity": float(similarities[idx]), "embedding": document_embeddings[idx]} for idx in top_indices]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        vec1, vec2 = vec1.reshape(-1), vec2.reshape(-1)
        norm_prod = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return np.dot(vec1, vec2) / norm_prod if norm_prod != 0 else 0.0

    def _cosine_similarity_batch(self, query: np.ndarray, documents: np.ndarray) -> np.ndarray:
        query, documents = query.reshape(-1), documents.reshape(-1) if documents.ndim == 1 else documents
        dot_products = np.dot(documents, query)
        query_norm, doc_norms = np.linalg.norm(query), np.linalg.norm(documents, axis=1)
        if query_norm == 0:
            return np.zeros(len(documents))
        return np.divide(dot_products, doc_norms * query_norm, out=np.zeros_like(dot_products), where=(doc_norms * query_norm) != 0)

    def get_model_info(self) -> dict[str, Any]:
        return {"model_name": self.model_name, "embedding_size": self.EMBEDDING_DIM, "type": "sentence_transformers", "description": f"Sentence-transformers: {self.model_name}"}

    def generate_and_store_embeddings(self, channel_id: str, db_path: str | None = None, show_progress: bool = True) -> int:
        from yt_fts.utils.config import get_db_path as get_db
        db_path = db_path or get_db()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Query for subtitles in this channel
            cursor.execute(
                "SELECT s.subtitle_id, s.video_id, s.text FROM Subtitles s "
                "JOIN Videos v ON s.video_id = v.video_id "
                "WHERE v.channel_id = ?",
                (channel_id,)
            )
            rows = cursor.fetchall()

            if not rows:
                return 0

            existing_ids = set()
            cursor.execute("SELECT subtitle_id FROM embeddings WHERE channel_id = ? AND model_name = ?", (channel_id, self.model_name))
            for row in cursor.fetchall():
                existing_ids.add(row[0])
            to_generate = [(r[0], r[1], r[2]) for r in rows if r[0] not in existing_ids]
            if not to_generate:
                return len(rows)
            texts = [r[2] for r in to_generate]
            embeddings = self.get_embeddings_batch(texts)
            timestamp = datetime.now(timezone.utc).isoformat()
            count = 0
            iterator = track(list(zip(to_generate, embeddings, strict=False)), description="Generating embeddings") if show_progress else zip(to_generate, embeddings, strict=False)
            for (subtitle_id, video_id, _), embedding in iterator:
                embedding_blob = pickle.dumps(embedding)
                try:
                    cursor.execute("INSERT INTO embeddings (subtitle_id, channel_id, video_id, embedding, model_name, created_at) VALUES (?, ?, ?, ?, ?, ?)", (subtitle_id, channel_id, video_id, embedding_blob, self.model_name, timestamp))
                    count += 1
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
            return count

    def get_embedding_status(self, channel_id: str, db_path: str | None = None) -> dict[str, Any]:
        from yt_fts.utils.config import get_db_path as get_db
        db_path = db_path or get_db()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Count total subtitles for this channel
            cursor.execute(
                "SELECT COUNT(*) FROM Subtitles s "
                "JOIN Videos v ON s.video_id = v.video_id "
                "WHERE v.channel_id = ?",
                (channel_id,)
            )
            total_subtitles = cursor.fetchone()[0]

            # Count existing embeddings
            cursor.execute(
                "SELECT COUNT(DISTINCT s.subtitle_id) FROM embeddings e "
                "JOIN Subtitles s ON e.subtitle_id = s.subtitle_id "
                "WHERE e.channel_id = ? AND e.model_name = ?",
                (channel_id, self.model_name)
            )
            total_embeddings = cursor.fetchone()[0]

        return {"channel_id": channel_id, "model_name": self.model_name, "total_subtitles": total_subtitles, "total_embeddings": total_embeddings, "missing_embeddings": total_subtitles - total_embeddings, "complete": total_embeddings >= total_subtitles}


SimpleEmbeddingsHandler = SemanticEmbeddingsHandler
