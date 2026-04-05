import numpy as np
import torch
from adaptive_config import print_log_message
from rich.console import Console
from rich.progress import Progress
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN

from log_chunker.data_models import ChunkInfo, SemanticCluster

from .config import ChunkingConfig


class SemanticTagger:
    """A class to perform semantic clustering on log chunks."""

    def __init__(self, config: ChunkingConfig, console: Console):
        """Initializes the SemanticTagger."""
        self.config = config
        self.console = console
        self.model = SentenceTransformer(config.semantic_model)
        if torch.cuda.is_available():
            print_log_message(
                self.console,
                "[green]Using GPU for semantic analysis.[/green]",
                "semantic_tagger.py:22",
            )
        else:
            print_log_message(
                self.console,
                "[yellow]GPU not available, using CPU for semantic analysis.[/yellow]",
                "semantic_tagger.py:24",
            )

    def cluster_chunks(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> list[SemanticCluster]:
        """Clusters log chunks based on their semantic similarity."""
        if not chunks:
            return []

        with Progress(console=self.console) as progress:
            task = progress.add_task("[cyan]Clustering chunks...[/cyan]", total=3)

            # 1. Generate embeddings
            corpus = [chunk[0] for chunk in chunks]
            embeddings = self.model.encode(corpus, show_progress_bar=False)
            progress.update(
                task, advance=1, description="[cyan]Embeddings generated.[/cyan]"
            )

            # 2. Perform clustering
            clusterer = HDBSCAN(
                min_cluster_size=self.config.min_cluster_size,
                min_samples=self.config.min_samples,
                metric="euclidean",
            )
            cluster_labels = clusterer.fit_predict(embeddings)
            progress.update(
                task, advance=1, description="[cyan]Clustering complete.[/cyan]"
            )

            # 3. Label and format clusters
            clusters = self._label_clusters(cluster_labels, chunks)
            progress.update(
                task, advance=1, description="[cyan]Clusters labeled.[/cyan]"
            )

        return clusters

    def _label_clusters(
        self, cluster_labels: np.ndarray, chunks: list[tuple[str, ChunkInfo]]
    ) -> list[SemanticCluster]:
        """Labels the clusters found by HDBSCAN."""
        labeled_clusters = []
        unique_labels = set(cluster_labels)

        for label in unique_labels:
            if label == -1:
                continue  # Skip noise points

            cluster_indices = [i for i, l in enumerate(cluster_labels) if l == label]
            cluster_chunks = [chunks[i] for i in cluster_indices]

            # Simple labeling strategy: use the most common words from the first chunk
            first_chunk_text = cluster_chunks[0][0]
            keywords = [word for word in first_chunk_text.split() if len(word) > 4]
            label_text = " ".join(keywords[:5])

            labeled_clusters.append(
                SemanticCluster(
                    cluster_id=int(label),
                    label=label_text,
                    chunk_ids=[chunk[1].chunk_id for chunk in cluster_chunks],
                    coherence_score=0.0,  # Placeholder
                    keywords=keywords[:10],
                )
            )

        return labeled_clusters
