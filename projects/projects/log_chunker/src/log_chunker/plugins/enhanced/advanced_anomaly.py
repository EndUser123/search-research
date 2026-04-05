"""
Advanced Anomaly Detection Plugin using Isolation Forest

Dependencies: scikit-learn
Fallback: Uses existing frequency-based anomaly detection
Configuration: advanced_anomaly section in config
"""

import logging
from typing import Any

# Standard optional dependency pattern
try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer

    HAS_SKLEARN_DEPS = True
except ImportError:
    HAS_SKLEARN_DEPS = False
    IsolationForest = None
    TfidfVectorizer = None
    np = None

from ...config import ChunkingConfig
from ...data_models import ChunkInfo, LogEntry
from ..base import BaseChunkingPlugin

logger = logging.getLogger(__name__)


class AdvancedAnomalyPlugin(BaseChunkingPlugin):
    """Advanced anomaly detection using Isolation Forest"""

    name = "advanced_anomaly"
    version = "1.0.0"
    dependencies = ["scikit-learn"]

    def __init__(self):
        super().__init__()
        self.use_fallback = False
        self.isolation_forest = None
        self.vectorizer = None

    def initialize(self, config: ChunkingConfig, console) -> bool:
        """Initialize the advanced anomaly detection plugin"""
        super().initialize(config, console)

        if not HAS_SKLEARN_DEPS:
            logger.warning(
                f"{self.name}: Scikit-learn dependencies unavailable, using fallback"
            )
            self.console.print(
                "[yellow]Advanced anomaly detection dependencies not found, using fallback"
            )
            self.use_fallback = True
            return True

        self.use_fallback = False

        # Initialize isolation forest
        try:
            self.isolation_forest = IsolationForest(
                contamination=config.advanced_anomaly.contamination,
                n_estimators=config.advanced_anomaly.n_estimators,
                max_samples=config.advanced_anomaly.max_samples,
                random_state=config.advanced_anomaly.random_state,
                n_jobs=1,  # Keep single threaded for consistency
            )
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words="english",
                ngram_range=(1, 2),
                max_df=0.95,
                min_df=2,
            )
            self.console.print(
                f"[green]✅ Advanced anomaly detection initialized with contamination={config.advanced_anomaly.contamination}"
            )
            return True
        except Exception as e:
            logger.error(
                f"{self.name}: Failed to initialize anomaly detection components: {e}"
            )
            self.console.print(
                f"[red]Failed to initialize advanced anomaly detection: {e}"
            )
            self.use_fallback = True
            return True

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Find anomaly-based boundaries"""
        if self.use_fallback:
            return self._fallback_boundaries(text, log_entries)

        try:
            return self._isolation_forest_boundaries(text, log_entries)
        except Exception as e:
            logger.error(
                f"{self.name}: Isolation forest analysis failed: {e}, using fallback"
            )
            self.console.print(f"[yellow]Anomaly analysis failed, using fallback: {e}")
            return self._fallback_boundaries(text, log_entries)

    def _isolation_forest_boundaries(
        self, text: str, log_entries: list[LogEntry]
    ) -> list[int]:
        """Implementation using Isolation Forest"""
        if (
            len(log_entries) < 10
        ):  # Need sufficient data for meaningful anomaly detection
            return []

        # Extract messages for feature extraction
        messages = [entry.message for entry in log_entries]

        # Generate TF-IDF features
        self.console.print("[cyan]Generating TF-IDF features for anomaly detection...")
        try:
            tfidf_features = self.vectorizer.fit_transform(messages)
        except ValueError as e:
            logger.warning(f"{self.name}: TF-IDF vectorization failed: {e}")
            return self._fallback_boundaries(text, log_entries)

        # Perform anomaly detection
        self.console.print("[cyan]Performing Isolation Forest anomaly detection...")
        anomaly_labels = self.isolation_forest.fit_predict(tfidf_features)
        anomaly_scores = self.isolation_forest.decision_function(tfidf_features)

        # Find boundaries based on anomalous entries
        boundaries = []

        # Look for transitions from normal to anomalous or vice versa
        prev_label = anomaly_labels[0]

        for i, (label, score) in enumerate(
            zip(anomaly_labels[1:], anomaly_scores[1:], strict=False), 1
        ):
            # Create boundary if there's a transition
            if label != prev_label:
                if log_entries[i].line_number is not None:
                    boundaries.append(log_entries[i].line_number)

            # Also create boundaries for highly anomalous entries
            elif label == -1 and score < -0.5:  # Very anomalous
                if i > 0 and log_entries[i].line_number is not None:
                    boundaries.append(log_entries[i].line_number)

            prev_label = label

        # Remove duplicate boundaries and sort
        boundaries = sorted(list(set(boundaries)))

        self.console.print(f"[green]Found {len(boundaries)} anomaly-based boundaries")
        return boundaries

    def _fallback_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Fallback using frequency-based anomaly detection"""
        boundaries = []

        if len(log_entries) < 5:
            return boundaries

        # Simple frequency-based anomaly detection fallback
        # Count message patterns
        pattern_counts = {}
        for entry in log_entries:
            # Create a simple pattern by keeping only letters and common log keywords
            pattern = " ".join(
                word.lower()
                for word in entry.message.split()
                if word.isalpha() and len(word) > 2
            )
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Calculate frequency threshold (messages that appear very rarely)
        total_entries = len(log_entries)
        rare_threshold = max(1, total_entries * 0.05)  # 5% threshold

        # Find entries with rare patterns
        for i, entry in enumerate(log_entries):
            pattern = " ".join(
                word.lower()
                for word in entry.message.split()
                if word.isalpha() and len(word) > 2
            )

            if pattern_counts.get(pattern, 0) <= rare_threshold:
                if entry.line_number is not None:
                    boundaries.append(entry.line_number)

        return sorted(list(set(boundaries)))

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score based on anomaly likelihood"""
        if self.use_fallback:
            return 0.5  # Neutral score for fallback

        try:
            # Simple anomaly scoring
            lines = chunk.strip().split("\n")
            if len(lines) < 2:
                return 0.7

            # Get TF-IDF features for chunk lines
            try:
                tfidf_features = self.vectorizer.transform(lines)
            except:
                return 0.5  # Fallback if vectorizer not fitted

            # Get anomaly scores
            anomaly_scores = self.isolation_forest.decision_function(tfidf_features)

            # Convert to 0-1 score (higher = more normal, lower = more anomalous)
            avg_score = float(np.mean(anomaly_scores))

            # Normalize to 0-1 range where 1 is good quality (normal)
            # Anomaly scores are typically in range [-1, 1] with negative being anomalous
            normalized_score = (avg_score + 1) / 2
            return max(0.0, min(1.0, normalized_score))

        except Exception as e:
            logger.error(f"{self.name}: Scoring failed: {e}")
            return 0.5

    def analyze_chunks(self, chunks: list[tuple]) -> dict[str, Any]:
        """Perform anomaly analysis on chunks"""
        if self.use_fallback:
            return {
                "advanced_anomaly": {
                    "fallback_mode": True,
                    "total_chunks": len(chunks),
                    "analysis": "Frequency-based anomaly analysis",
                }
            }

        try:
            # Extract chunk content
            chunk_contents = [chunk[0] for chunk in chunks]

            if len(chunk_contents) < 2:
                return {
                    "advanced_anomaly": {
                        "total_chunks": len(chunks),
                        "anomalies_detected": 0,
                        "insufficient_data": True,
                    }
                }

            # Generate TF-IDF features for all chunks
            tfidf_features = self.vectorizer.fit_transform(chunk_contents)

            # Perform anomaly detection on chunks
            anomaly_labels = self.isolation_forest.fit_predict(tfidf_features)
            anomaly_scores = self.isolation_forest.decision_function(tfidf_features)

            # Analyze results
            anomalous_chunks = [
                i for i, label in enumerate(anomaly_labels) if label == -1
            ]
            normal_chunks = [i for i, label in enumerate(anomaly_labels) if label == 1]

            # Calculate statistics
            anomaly_rate = len(anomalous_chunks) / len(chunks) if chunks else 0
            avg_anomaly_score = float(np.mean(anomaly_scores))
            min_anomaly_score = float(np.min(anomaly_scores))
            max_anomaly_score = float(np.max(anomaly_scores))

            # Identify most anomalous chunks
            most_anomalous_indices = np.argsort(anomaly_scores)[
                : min(5, len(anomaly_scores))
            ]
            most_anomalous = [
                {
                    "chunk_id": int(idx),
                    "anomaly_score": float(anomaly_scores[idx]),
                    "preview": chunk_contents[idx][:100] + "..."
                    if len(chunk_contents[idx]) > 100
                    else chunk_contents[idx],
                }
                for idx in most_anomalous_indices
            ]

            return {
                "advanced_anomaly": {
                    "total_chunks": len(chunks),
                    "anomalous_chunks": len(anomalous_chunks),
                    "normal_chunks": len(normal_chunks),
                    "anomaly_rate": anomaly_rate,
                    "avg_anomaly_score": avg_anomaly_score,
                    "min_anomaly_score": min_anomaly_score,
                    "max_anomaly_score": max_anomaly_score,
                    "most_anomalous": most_anomalous,
                    "anomalous_chunk_ids": anomalous_chunks,
                    "model_params": {
                        "contamination": self.config.advanced_anomaly.contamination,
                        "n_estimators": self.config.advanced_anomaly.n_estimators,
                    },
                }
            }

        except Exception as e:
            logger.error(f"{self.name}: Analysis failed: {e}")
            return {
                "advanced_anomaly": {
                    "error": str(e),
                    "fallback_mode": True,
                    "total_chunks": len(chunks),
                }
            }
