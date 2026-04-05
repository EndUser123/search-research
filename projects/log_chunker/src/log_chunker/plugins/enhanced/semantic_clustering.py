"""
Semantic Clustering Plugin using sentence-transformers and HDBSCAN

Dependencies: sentence-transformers, hdbscan
Fallback: Uses simple keyword clustering if dependencies unavailable
Configuration: semantic_clustering section in config
"""

import logging
from typing import Any

# Standard optional dependency pattern
try:
    import hdbscan
    import numpy as np
    from sentence_transformers import SentenceTransformer

    HAS_SEMANTIC_DEPS = True
except ImportError:
    HAS_SEMANTIC_DEPS = False
    SentenceTransformer = None
    hdbscan = None
    np = None

from ...config import ChunkingConfig
from ...data_models import ChunkInfo, LogEntry
from ..base import BaseChunkingPlugin

logger = logging.getLogger(__name__)


class SemanticClusteringPlugin(BaseChunkingPlugin):
    """Enhanced semantic clustering using transformer embeddings and HDBSCAN"""

    name = "semantic_clustering"
    version = "1.0.0"
    dependencies = ["sentence-transformers", "hdbscan", "scikit-learn"]

    def __init__(self):
        super().__init__()
        self.use_fallback = False
        self.model = None
        self.clusterer = None

    def initialize(self, config: ChunkingConfig, console) -> bool:
        """Initialize the semantic clustering plugin"""
        super().initialize(config, console)

        if not HAS_SEMANTIC_DEPS:
            logger.warning(
                f"{self.name}: Semantic dependencies unavailable, using fallback"
            )
            self.console.print(
                "[yellow]Semantic clustering dependencies not found, using fallback"
            )
            self.use_fallback = True
            return True

        self.use_fallback = False

        # Initialize semantic model
        try:
            self.model = SentenceTransformer(config.semantic_clustering.model_name)
            self.clusterer = hdbscan.HDBSCAN(
                min_cluster_size=config.semantic_clustering.min_cluster_size,
                min_samples=config.semantic_clustering.min_samples,
                metric="euclidean",
            )
            self.console.print(
                f"[green]✅ Semantic clustering initialized with {config.semantic_clustering.model_name}"
            )
            return True
        except Exception as e:
            logger.error(f"{self.name}: Failed to initialize semantic components: {e}")
            self.console.print(f"[red]Failed to initialize semantic clustering: {e}")
            self.use_fallback = True
            return True

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Find boundaries using semantic similarity"""
        if self.use_fallback:
            return self._fallback_boundaries(text, log_entries)

        try:
            return self._semantic_boundaries(text, log_entries)
        except Exception as e:
            logger.error(
                f"{self.name}: Semantic clustering failed: {e}, using fallback"
            )
            self.console.print(f"[yellow]Semantic analysis failed, using fallback: {e}")
            return self._fallback_boundaries(text, log_entries)

    def _semantic_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Implementation using semantic embeddings and HDBSCAN"""
        if len(log_entries) < 2:
            return []

        # Extract messages for embedding
        messages = [entry.message for entry in log_entries]

        # Generate embeddings
        self.console.print("[cyan]Generating semantic embeddings...")
        embeddings = self.model.encode(messages, show_progress_bar=False)

        # Perform clustering
        self.console.print("[cyan]Performing HDBSCAN clustering...")
        cluster_labels = self.clusterer.fit_predict(embeddings)

        # Find cluster boundaries
        boundaries = []
        if len(cluster_labels) > 0:
            current_cluster = cluster_labels[0]

            for i, label in enumerate(cluster_labels[1:], 1):
                if label != current_cluster:
                    if log_entries[i].line_number is not None:
                        boundaries.append(log_entries[i].line_number)
                    current_cluster = label

        self.console.print(f"[green]Found {len(boundaries)} semantic boundaries")
        return boundaries

    def _fallback_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Fallback using simple keyword similarity"""
        boundaries = []

        if len(log_entries) < 2:
            return boundaries

        # Simple keyword-based clustering fallback
        prev_keywords = set()

        for i, entry in enumerate(log_entries):
            # Extract simple keywords
            words = entry.message.lower().split()
            keywords = set(word for word in words if len(word) > 3)

            if i > 0:
                # Calculate Jaccard similarity
                intersection = prev_keywords.intersection(keywords)
                union = prev_keywords.union(keywords)
                similarity = len(intersection) / len(union) if union else 0

                # If similarity is low, create boundary
                if similarity < 0.3 and entry.line_number is not None:
                    boundaries.append(entry.line_number)

            prev_keywords = keywords

        return boundaries

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score based on semantic coherence"""
        if self.use_fallback:
            return 0.5  # Neutral score for fallback

        try:
            # Simple coherence scoring
            lines = chunk.strip().split("\n")
            if len(lines) < 2:
                return 0.7

            # Get embeddings for all lines
            embeddings = self.model.encode(lines, show_progress_bar=False)

            # Calculate average pairwise similarity
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    similarities.append(sim)

            return float(np.mean(similarities)) if similarities else 0.5

        except Exception as e:
            logger.error(f"{self.name}: Scoring failed: {e}")
            return 0.5

    def analyze_chunks(self, chunks: list[tuple]) -> dict[str, Any]:
        """Perform semantic analysis on chunks"""
        if self.use_fallback:
            return {
                "semantic_clustering": {
                    "fallback_mode": True,
                    "total_chunks": len(chunks),
                    "analysis": "Keyword-based similarity analysis",
                }
            }

        try:
            # Extract chunk content
            chunk_contents = [chunk[0] for chunk in chunks]

            # Generate embeddings for all chunks
            embeddings = self.model.encode(chunk_contents, show_progress_bar=False)

            # Perform clustering on chunks
            cluster_labels = self.clusterer.fit_predict(embeddings)

            # Calculate cluster statistics
            unique_clusters = len(set(cluster_labels)) - (
                1 if -1 in cluster_labels else 0
            )
            noise_points = sum(1 for label in cluster_labels if label == -1)

            # Calculate average intra-cluster similarity
            cluster_similarities = {}
            for cluster_id in set(cluster_labels):
                if cluster_id == -1:  # Skip noise
                    continue
                cluster_indices = [
                    i for i, label in enumerate(cluster_labels) if label == cluster_id
                ]
                if len(cluster_indices) > 1:
                    cluster_embeddings = embeddings[cluster_indices]
                    similarities = []
                    for i in range(len(cluster_embeddings)):
                        for j in range(i + 1, len(cluster_embeddings)):
                            sim = np.dot(
                                cluster_embeddings[i], cluster_embeddings[j]
                            ) / (
                                np.linalg.norm(cluster_embeddings[i])
                                * np.linalg.norm(cluster_embeddings[j])
                            )
                            similarities.append(sim)
                    cluster_similarities[cluster_id] = (
                        float(np.mean(similarities)) if similarities else 0.0
                    )

            return {
                "semantic_clustering": {
                    "total_chunks": len(chunks),
                    "clusters_found": unique_clusters,
                    "noise_points": noise_points,
                    "cluster_similarities": cluster_similarities,
                    "avg_cluster_similarity": float(
                        np.mean(list(cluster_similarities.values()))
                    )
                    if cluster_similarities
                    else 0.0,
                    "model_used": self.config.semantic_clustering.model_name,
                }
            }

        except Exception as e:
            logger.error(f"{self.name}: Analysis failed: {e}")
            return {
                "semantic_clustering": {
                    "error": str(e),
                    "fallback_mode": True,
                    "total_chunks": len(chunks),
                }
            }
