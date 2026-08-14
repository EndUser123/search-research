"""Result Clustering & Topic Modeling for CHS v2.

Implements fast clustering algorithms for organizing search results
into thematic groups using FAISS IVF for approximate nearest neighbors.

Clustering Modes:
- topic: Semantic clustering using embeddings
- backend: Group by source backend
- temporal: Group by time (recent/older)
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import sqlite3
logger = logging.getLogger(__name__)
MIN_RESULTS_FOR_CLUSTERING = 10
DEFAULT_EMBEDDING_DIM = 384
TOPIC_SIMILARITY_THRESHOLD = 0.75
MIN_CLUSTER_SIZE = 2


def cluster_results(
    results: list[dict], mode: str = "topic", n_clusters: int | None = None
) -> dict:
    """Cluster search results by the specified mode.

    Args:
        results: List of search result dicts with 'id', 'content', etc.
        mode: Clustering mode ('topic', 'backend', 'temporal')
        n_clusters: Optional max number of clusters (auto-detect if None)

    Returns:
        Dict with clustering output:
        {
            "mode": str,
            "total_results": int,
            "clusters": [
                {
                    "id": str,
                    "label": str,
                    "count": int,
                    "result_ids": list[int],
                    "confidence": float,
                    "summary": str
                },
                ...
            ],
            "unclustered": int
        }
    """
    requested_mode = mode
    if not results or len(results) < MIN_RESULTS_FOR_CLUSTERING:
        return {
            "mode": requested_mode,
            "total_results": len(results),
            "clusters": [],
            "unclustered": len(results),
        }
    if mode == "topic":
        result = _cluster_by_topic(results, n_clusters)
    elif mode == "backend":
        result = _cluster_by_backend(results)
    elif mode == "temporal":
        result = _cluster_by_temporal(results)
    else:
        logger.warning(f"Unknown clustering mode: {mode}, falling back to backend")
        result = _cluster_by_backend(results)
    result["mode"] = requested_mode
    return result


def _cluster_by_topic(results: list[dict], n_clusters: int | None) -> dict:
    """Cluster results by semantic similarity using embeddings.

    Uses a simple greedy clustering approach that's O(n) instead of O(n^2).
    Results are assigned to the first cluster they're similar enough to,
    or start a new cluster if no match is found.

    Args:
        results: List of search result dicts
        n_clusters: Optional max number of clusters

    Returns:
        Clustering output dict
    """
    embeddings = []
    valid_results = []
    result_indices = []
    for i, result in enumerate(results):
        embedding = _extract_embedding(result)
        if embedding is not None:
            embeddings.append(embedding)
            valid_results.append(result)
            result_indices.append(i)
    if len(valid_results) < MIN_RESULTS_FOR_CLUSTERING:
        return {
            "mode": "topic",
            "total_results": len(results),
            "clusters": [],
            "unclustered": len(results),
        }
    embedding_matrix = np.array(embeddings, dtype=np.float32)
    norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized_embeddings = embedding_matrix / norms
    clusters = []
    for i, embedding in enumerate(normalized_embeddings):
        assigned = False
        for cluster_idx, (center_idx, members, center_vec) in enumerate(clusters):
            similarity = np.dot(embedding, center_vec)
            if similarity >= TOPIC_SIMILARITY_THRESHOLD:
                members.append(result_indices[i])
                n = len(members)
                clusters[cluster_idx] = (
                    center_idx,
                    members,
                    (center_vec * (n - 1) + embedding) / n,
                )
                assigned = True
                break
        if not assigned:
            if n_clusters is None or len(clusters) < n_clusters:
                clusters.append((i, [result_indices[i]], embedding))
    cluster_outputs = []
    clustered_ids = set()
    for cluster_idx, (_, members, _) in enumerate(clusters):
        if len(members) < MIN_CLUSTER_SIZE:
            continue
        cluster_results = [results[idx] for idx in members]
        label = _generate_cluster_label(cluster_results)
        cluster_embeddings = [
            normalized_embeddings[idx]
            for idx in range(len(normalized_embeddings))
            if result_indices[idx] in members
        ]
        confidence = _calculate_cluster_confidence(cluster_embeddings)
        cluster_outputs.append(
            {
                "id": f"c{cluster_idx + 1}",
                "label": label,
                "count": len(members),
                "result_ids": members,
                "confidence": confidence,
                "summary": _generate_cluster_summary(cluster_results, label),
            }
        )
        clustered_ids.update(members)
    cluster_outputs.sort(key=lambda c: c["count"], reverse=True)
    return {
        "mode": "topic",
        "total_results": len(results),
        "clusters": cluster_outputs,
        "unclustered": len(results) - len(clustered_ids),
    }


def _cluster_by_backend(results: list[dict]) -> dict:
    """Cluster results by their source backend.

    Args:
        results: List of search result dicts

    Returns:
        Clustering output dict
    """
    backend_groups = defaultdict(list)
    for i, result in enumerate(results):
        backend = result.get("backend", result.get("source", "unknown"))
        backend_groups[backend].append(i)
    cluster_outputs = []
    for cluster_idx, (backend, members) in enumerate(
        sorted(backend_groups.items(), key=lambda x: len(x[1]), reverse=True)
    ):
        if len(members) < MIN_CLUSTER_SIZE:
            continue
        cluster_outputs.append(
            {
                "id": f"c{cluster_idx + 1}",
                "label": f"{backend.title()} Results",
                "count": len(members),
                "result_ids": members,
                "confidence": 1.0,
                "summary": f"Results from {backend} backend",
            }
        )
    return {
        "mode": "backend",
        "total_results": len(results),
        "clusters": cluster_outputs,
        "unclustered": sum(
            1 for members in backend_groups.values() if len(members) < MIN_CLUSTER_SIZE
        ),
    }


def _cluster_by_temporal(results: list[dict]) -> dict:
    """Cluster results by time (recent vs older).

    Args:
        results: List of search result dicts

    Returns:
        Clustering output dict
    """
    now = datetime.now(UTC)
    time_groups = {"recent": [], "older": [], "archived": []}
    for i, result in enumerate(results):
        timestamp = _extract_timestamp(result)
        if timestamp is None:
            time_groups["older"].append(i)
            continue
        age_days = (now - timestamp).days
        if age_days < 7:
            time_groups["recent"].append(i)
        elif age_days < 30:
            time_groups["older"].append(i)
        else:
            time_groups["archived"].append(i)
    cluster_outputs = []
    for cluster_idx, (period, members) in enumerate(
        sorted(time_groups.items(), key=lambda x: len(x[1]), reverse=True)
    ):
        if len(members) < MIN_CLUSTER_SIZE:
            continue
        label_map = {
            "recent": "Recent (Last 7 days)",
            "older": "Previous (7-30 days)",
            "archived": "Archived (30+ days)",
        }
        cluster_outputs.append(
            {
                "id": f"c{cluster_idx + 1}",
                "label": label_map.get(period, period.title()),
                "count": len(members),
                "result_ids": members,
                "confidence": 1.0,
                "summary": f"Results from {period} time period",
            }
        )
    return {
        "mode": "temporal",
        "total_results": len(results),
        "clusters": cluster_outputs,
        "unclustered": sum(
            1 for members in time_groups.values() if len(members) < MIN_CLUSTER_SIZE
        ),
    }


def _extract_embedding(result: dict) -> np.ndarray | None:
    """Extract embedding vector from result.

    Args:
        result: Result dict

    Returns:
        Embedding as numpy array or None
    """
    embedding = result.get("embedding")
    if embedding is not None:
        if isinstance(embedding, bytes):
            try:
                return np.frombuffer(embedding, dtype=np.float32)
            except Exception:
                pass
        elif isinstance(embedding, np.ndarray):
            return embedding
        elif isinstance(embedding, list):
            return np.array(embedding, dtype=np.float32)
    vector = result.get("vector")
    if vector is not None:
        if isinstance(vector, bytes):
            try:
                return np.frombuffer(vector, dtype=np.float32)
            except Exception:
                pass
        elif isinstance(vector, np.ndarray):
            return vector
        elif isinstance(vector, list):
            return np.array(vector, dtype=np.float32)
    return None


def _extract_timestamp(result: dict) -> datetime | None:
    """Extract timestamp from result.

    Args:
        result: Result dict

    Returns:
        Datetime or None
    """
    timestamp_fields = ["timestamp", "created_at", "date", "time"]
    for field in timestamp_fields:
        value = result.get(field)
        if value:
            try:
                if isinstance(value, datetime):
                    return value
                elif isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value, tz=UTC)
                elif isinstance(value, str):
                    if "Z" in value:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    elif "+" in value or value.count("-") >= 2:
                        return datetime.fromisoformat(value)
            except Exception:
                continue
    return None


def _generate_cluster_label(results: list[dict]) -> str:
    """Generate a descriptive label for a cluster.

    Args:
        results: List of result dicts in the cluster

    Returns:
        Generated label string
    """
    all_text = []
    for result in results:
        content = result.get("content", "")
        title = result.get("title", "")
        all_text.append(f"{title} {content}")
    combined = " ".join(all_text).lower()
    words = re.findall("\\b[a-z]{2,}\\b", combined)
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "they",
        "them",
        "their",
        "there",
        "here",
        "what",
        "which",
        "who",
        "when",
        "where",
        "why",
        "how",
        "use",
        "using",
        "make",
        "get",
    }
    significant = [w for w in words if w not in stopwords]
    counter = Counter(significant)
    top_terms = [term for term, _ in counter.most_common(3)]
    if top_terms:
        label = " ".join(term.title() for term in top_terms[:2])
        if len(label) > 40:
            label = label[:37] + "..."
        return label
    return "General Topic"


def _calculate_cluster_confidence(embeddings: list[np.ndarray]) -> float:
    """Calculate cluster confidence based on pairwise similarity.

    Args:
        embeddings: List of embedding vectors in the cluster

    Returns:
        Confidence score (0-1)
    """
    if len(embeddings) < 2:
        return 1.0
    normalized = []
    for emb in embeddings:
        norm = np.linalg.norm(emb)
        if norm > 0:
            normalized.append(emb / norm)
        else:
            normalized.append(emb)
    similarities = []
    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            sim = np.dot(normalized[i], normalized[j])
            similarities.append(max(0, sim))
    if not similarities:
        return 0.5
    return float(np.mean(similarities))


def _generate_cluster_summary(results: list[dict], label: str) -> str:
    """Generate a brief summary for the cluster.

    Args:
        results: List of result dicts in the cluster
        label: Cluster label

    Returns:
        Summary string
    """
    for result in results:
        content = result.get("content", "")
        if content and len(content) > 20:
            if len(content) > 100:
                content = content[:97] + "..."
            return f"Focuses on {label.lower()}: {content[:50]}..."
    return f"Results related to {label.lower()}"


def filter_results_by_cluster(
    results: list[dict], clustering_output: dict, cluster_id: str
) -> list[dict]:
    """Filter results to only those in the specified cluster.

    Args:
        results: Original search results
        clustering_output: Output from cluster_results()
        cluster_id: ID of cluster to filter (e.g., "c1")

    Returns:
        Filtered list of results
    """
    for cluster in clustering_output.get("clusters", []):
        if cluster["id"] == cluster_id:
            result_indices = cluster["result_ids"]
            return [results[i] for i in result_indices if i < len(results)]
    return []


def interactive_cluster_selection(clustering_output: dict) -> str | None:
    """Display cluster menu and return user selection.

    This is a placeholder for interactive TTY input.
    In practice, this would be called from a CLI context.

    Args:
        clustering_output: Output from cluster_results()

    Returns:
        Selected cluster ID or None
    """
    clusters = clustering_output.get("clusters", [])
    if not clusters:
        return None
    return clusters[0]["id"] if clusters else None


class ClusteredSearchResults:
    """Wrapper for search results with clustering support."""

    def __init__(self, results: list[dict], clustering: dict | None = None):
        """Initialize clustered search results.

        Args:
            results: Original search results
            clustering: Optional clustering output
        """
        self.results = results
        self.clustering = clustering

    def get_clusters(self) -> list[dict]:
        """Get list of clusters."""
        return self.clustering.get("clusters", []) if self.clustering else []

    def filter_by_cluster(self, cluster_id: str) -> list[dict]:
        """Filter results to specific cluster."""
        if not self.clustering:
            return self.results
        return filter_results_by_cluster(self.results, self.clustering, cluster_id)

    def get_cluster_summary(self) -> str:
        """Get a human-readable summary of clustering."""
        if not self.clustering:
            return "No clustering applied"
        clusters = self.clustering.get("clusters", [])
        total = self.clustering.get("total_results", 0)
        unclustered = self.clustering.get("unclustered", 0)
        lines = [
            f"Clustering mode: {self.clustering.get('mode', 'unknown')}",
            f"Total results: {total}",
            f"Clusters found: {len(clusters)}",
        ]
        for cluster in clusters:
            lines.append(
                f"  - {cluster['id']}: {cluster['label']} ({cluster['count']} results, {cluster['confidence']:.2f} confidence)"
            )
        if unclustered > 0:
            lines.append(f"Unclustered: {unclustered}")
        return "\n".join(lines)


def extract_embeddings_from_results(
    results: list[dict], db: sqlite3.Connection | None = None
) -> list[np.ndarray | None]:
    """Extract or generate embeddings for results.

    First tries to extract existing embeddings from results.
    If not available and db is provided, looks up in turn_embeddings table.

    Args:
        results: List of search result dicts
        db: Optional database connection for embedding lookup

    Returns:
        List of embedding vectors (or None where unavailable)
    """
    embeddings = []
    for result in results:
        embedding = _extract_embedding(result)
        if embedding is not None:
            embeddings.append(embedding)
            continue
        if db is not None:
            result_id = result.get("id")
            if result_id:
                cursor = db.execute(
                    "SELECT embedding FROM turn_embeddings WHERE turn_id = ?", (result_id,)
                )
                row = cursor.fetchone()
                if row:
                    try:
                        embedding = np.frombuffer(row[0], dtype=np.float32)
                        embeddings.append(embedding)
                        continue
                    except Exception:
                        pass
        embeddings.append(None)
    return embeddings
