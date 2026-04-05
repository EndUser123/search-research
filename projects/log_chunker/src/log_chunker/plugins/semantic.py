"""Semantic similarity-based chunking plugin."""

import logging
from typing import Any

import numpy as np

try:
    import torch
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logging.warning(
        "Sentence-transformers, scikit-learn, or torch not found. SemanticChunkingPlugin will be disabled."
    )

from ..data_models import ChunkInfo, LogEntry
from .base import BaseChunkingPlugin

logger = logging.getLogger(__name__)


class SemanticChunkingPlugin(BaseChunkingPlugin):
    """Semantic similarity-based chunking"""

    name = "semantic"
    version = "1.0.0"
    dependencies = ["sentence-transformers", "sklearn", "torch"]  # For documentation

    def __init__(self):
        super().__init__()
        self.model: SentenceTransformer | None = None
        self.device = "cpu"  # Default device
        # Cache for embeddings is not strictly needed here as we process a continuous stream of sentences
        # The model's internal caching or batching should be sufficient for performance.

    def initialize(self, config, console) -> bool:
        """Initialize semantic plugin and load model."""
        if not HAS_ML_LIBS:
            self.console.log(
                "[yellow]SemanticChunkingPlugin disabled: Missing sentence-transformers, sklearn, or torch.[/yellow]"
            )
            return False

        try:
            self.device = (
                "cuda" if config.use_gpu and torch.cuda.is_available() else "cpu"
            )
            self.model = SentenceTransformer(config.semantic_model, device=self.device)
            logger.info(
                f"Loaded semantic model {config.semantic_model} on {self.device}"
            )
            return super().initialize(config, console)
        except (ImportError, OSError) as ie:  # OSError for e.g. model not found
            self.console.log(
                f"[red]Failed to load semantic model {config.semantic_model}: {ie}[/red]"
            )
            logger.error(f"Failed to initialize semantic chunker: {ie}")
            self.model = None  # Ensure model is None if loading fails
            return False
        except Exception as e:
            self.console.log(
                f"[red]An unexpected error occurred initializing semantic chunker: {e}[/red]"
            )
            logger.error(f"Failed to initialize semantic chunker: {e}", exc_info=True)
            self.model = None
            return False

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        if not self.model or not log_entries:
            return []

        # Extract messages for embedding. Use original_line for better context if message is too short.
        sentences = [
            entry.message if entry.message else entry.original_line
            for entry in log_entries
        ]

        if not sentences:
            return []

        # Generate embeddings in batches for efficiency
        embeddings = []
        for i in range(0, len(sentences), self.config.batch_size):
            batch = sentences[i : i + self.config.batch_size]
            try:
                batch_embeddings = self.model.encode(
                    batch, convert_to_numpy=True, show_progress_bar=False
                )
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(
                    f"Error encoding batch for semantic chunking: {e}", exc_info=True
                )
                # If an error occurs, we can't generate embeddings for this batch.
                # This will likely lead to incorrect boundaries, but allows processing to continue.
                # For now, we'll append dummy embeddings (e.g., zeros) or skip.
                # Appending zeros might cause issues with cosine similarity, so skipping is safer.
                # For simplicity, let's just return empty boundaries if any encoding fails.
                return []  # Or handle more gracefully if partial results are acceptable

        if len(embeddings) < 2:
            return []

        # Calculate cosine similarities between consecutive sentence embeddings
        similarities = []
        for i in range(len(embeddings) - 1):
            # Reshape for cosine_similarity: (1, -1) for single vector
            sim = cosine_similarity(
                embeddings[i].reshape(1, -1), embeddings[i + 1].reshape(1, -1)
            )[0][0]
            similarities.append(sim)

        # Identify boundaries where similarity drops below threshold
        boundaries = []
        for i, sim in enumerate(similarities):
            if sim < self.config.semantic_threshold:
                # Boundary is at the line *after* the similarity drop
                boundaries.append(i + 1)

        return boundaries

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score semantic coherence of a chunk."""
        if not self.model or not chunk.strip():
            return 0.0

        sentences = [s.strip() for s in chunk.split("\n") if s.strip()]
        if len(sentences) < 2:
            return 1.0  # A single sentence chunk is perfectly coherent

        try:
            # Encode all sentences in the chunk
            embeddings = self.model.encode(
                sentences, convert_to_numpy=True, show_progress_bar=False
            )

            # Calculate average pairwise cosine similarity within the chunk
            # This is a measure of internal coherence
            pairwise_similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = cosine_similarity(
                        embeddings[i].reshape(1, -1), embeddings[j].reshape(1, -1)
                    )[0][0]
                    pairwise_similarities.append(sim)

            if pairwise_similarities:
                # Normalize to 0-1 range if needed, but cosine similarity is already in -1 to 1
                # We want higher scores for more coherent chunks, so average is good.
                return float(np.mean(pairwise_similarities))
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Error scoring semantic chunk: {e}", exc_info=True)
            return 0.0

    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """Perform semantic analysis on chunks."""
        if not self.model or not chunks:
            return {}

        try:
            # Extract chunk texts for analysis
            chunk_texts = [chunk_text for chunk_text, _ in chunks]

            # Generate embeddings for all chunks
            chunk_embeddings = self.model.encode(
                chunk_texts, convert_to_numpy=True, show_progress_bar=False
            )

            # Calculate semantic diversity metrics
            from sklearn.metrics.pairwise import cosine_similarity

            similarity_matrix = cosine_similarity(chunk_embeddings)

            # Calculate average inter-chunk similarity
            n_chunks = len(chunks)
            total_similarity = 0
            pair_count = 0

            for i in range(n_chunks):
                for j in range(i + 1, n_chunks):
                    total_similarity += similarity_matrix[i][j]
                    pair_count += 1

            avg_similarity = total_similarity / pair_count if pair_count > 0 else 0

            # Find most and least similar chunk pairs
            max_similarity = 0
            min_similarity = 1
            most_similar_pair = None
            least_similar_pair = None

            for i in range(n_chunks):
                for j in range(i + 1, n_chunks):
                    sim = similarity_matrix[i][j]
                    if sim > max_similarity:
                        max_similarity = sim
                        most_similar_pair = (i, j)
                    if sim < min_similarity:
                        min_similarity = sim
                        least_similar_pair = (i, j)

            # Calculate semantic coherence for each chunk
            chunk_coherence = []
            for i, (chunk_text, chunk_info) in enumerate(chunks):
                sentences = [s.strip() for s in chunk_text.split("\n") if s.strip()]
                if len(sentences) > 1:
                    sentence_embeddings = self.model.encode(
                        sentences, convert_to_numpy=True, show_progress_bar=False
                    )
                    sentence_similarities = cosine_similarity(sentence_embeddings)

                    # Calculate average intra-chunk similarity
                    intra_similarity = 0
                    intra_pairs = 0
                    for si in range(len(sentences)):
                        for sj in range(si + 1, len(sentences)):
                            intra_similarity += sentence_similarities[si][sj]
                            intra_pairs += 1

                    coherence = intra_similarity / intra_pairs if intra_pairs > 0 else 0
                else:
                    coherence = 1.0  # Single sentence is perfectly coherent

                chunk_coherence.append(
                    {
                        "chunk_id": chunk_info.chunk_id,
                        "coherence_score": float(coherence),
                        "sentence_count": len(sentences),
                    }
                )

            return {
                "semantic_diversity": {
                    "average_inter_chunk_similarity": float(avg_similarity),
                    "max_similarity": float(max_similarity),
                    "min_similarity": float(min_similarity),
                    "most_similar_chunks": most_similar_pair,
                    "least_similar_chunks": least_similar_pair,
                },
                "chunk_coherence": chunk_coherence,
                "semantic_summary": {
                    "total_chunks_analyzed": len(chunks),
                    "average_coherence": float(
                        np.mean([c["coherence_score"] for c in chunk_coherence])
                    ),
                    "coherence_std": float(
                        np.std([c["coherence_score"] for c in chunk_coherence])
                    ),
                    "highly_coherent_chunks": len(
                        [c for c in chunk_coherence if c["coherence_score"] > 0.8]
                    ),
                    "low_coherence_chunks": len(
                        [c for c in chunk_coherence if c["coherence_score"] < 0.3]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}", exc_info=True)
            return {"error": str(e)}

    def cleanup(self) -> None:
        """Clean up resources, especially GPU memory."""
        if self.model and self.device == "cuda":
            try:
                import torch

                del self.model
                torch.cuda.empty_cache()
                logger.info("Cleaned up semantic model and CUDA cache.")
            except Exception as e:
                logger.error(
                    f"Error during semantic plugin cleanup: {e}", exc_info=True
                )
