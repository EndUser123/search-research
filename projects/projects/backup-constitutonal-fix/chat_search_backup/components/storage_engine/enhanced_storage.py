from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""Enhanced Storage Engine for CHS
Advanced storage system with temporal indexing, semantic caching, and performance optimization.
"""



# Add CSF NIP paths

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)


class TemporalIndex:
    """Multi-scale temporal indexing for efficient time-based queries."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database for temporal indexing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS temporal_index (
                    entry_id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    date_bucket TEXT NOT NULL,
                    hour_bucket TEXT NOT NULL,
                    week_bucket TEXT NOT NULL,
                    month_bucket TEXT NOT NULL,
                    intensity_score REAL DEFAULT 0.0,
                    topic_vector TEXT,
                    metadata TEXT
                )
            """
            )

            # Create indexes for efficient temporal queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON temporal_index(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_date_bucket ON temporal_index(date_bucket)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hour_bucket ON temporal_index(hour_bucket)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_week_bucket ON temporal_index(week_bucket)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_month_bucket ON temporal_index(month_bucket)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_intensity ON temporal_index(intensity_score)"
            )

            conn.commit()

    def add_entry(
        self,
        entry_id: str,
        timestamp: int,
        intensity_score: float = 0.0,
        topic_vector: list[float] | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Add an entry to temporal index."""
        with self._lock:
            dt = datetime.fromtimestamp(timestamp / 1000)

            date_bucket = dt.strftime("%Y-%m-%d")
            hour_bucket = dt.strftime("%Y-%m-%d %H:00")
            week_bucket = dt.strftime("%Y-W%U")
            month_bucket = dt.strftime("%Y-%m")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO temporal_index
                    (entry_id, timestamp, date_bucket, hour_bucket, week_bucket, month_bucket,
                     intensity_score, topic_vector, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry_id,
                        timestamp,
                        date_bucket,
                        hour_bucket,
                        week_bucket,
                        month_bucket,
                        intensity_score,
                        json.dumps(topic_vector) if topic_vector else None,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()

    def get_temporal_range(self, start_time: int, end_time: int) -> list[str]:
        """Get entry IDs within time range."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT entry_id FROM temporal_index WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
                (start_time, end_time),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_conversation_intensity(
        self, bucket: str, scale: str = "date"
    ) -> dict[str, float]:
        """Get conversation intensity metrics for a time bucket."""
        bucket_column = f"{scale}_bucket"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT {bucket_column}, COUNT(*) as count, AVG(intensity_score) as avg_intensity
                FROM temporal_index
                WHERE {bucket_column} LIKE ?
                GROUP BY {bucket_column}
                ORDER BY {bucket_column}
            """,
                (f"{bucket}%",),
            )

            results = {}
            for row in cursor.fetchall():
                results[row[0]] = {
                    "count": row[1],
                    "avg_intensity": row[2] or 0.0,
                }

            return results

    def get_trending_topics(
        self, time_period: str = "week", limit: int = 10
    ) -> list[dict]:
        """Get trending topics for a time period."""
        bucket_column = f"{time_period}_bucket"
        recent_bucket = datetime.now().strftime(
            (
                f"%Y-{time_period[0].upper()}%W"
                if time_period == "week"
                else "%Y-%m" if time_period == "month" else "%Y-%m-%d"
            ),
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT topic_vector, COUNT(*) as frequency
                FROM temporal_index
                WHERE {bucket_column} = ? AND topic_vector IS NOT NULL
                GROUP BY topic_vector
                ORDER BY frequency DESC
                LIMIT ?
            """,
                (recent_bucket, limit),
            )

            topics = []
            for row in cursor.fetchall():
                if row[0]:  # topic_vector is not None
                    topic_vector = json.loads(row[0])
                    topics.append(
                        {
                            "vector": topic_vector,
                            "frequency": row[1],
                        },
                    )

            return topics


class SemanticCache:
    """LRU cache for semantic search results with TTL."""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.cache: dict[str, tuple[Any, float]] = {}
        self.access_order: list[str] = []
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry has expired."""
        return time.time() - timestamp > self.ttl_seconds

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, ts) in self.cache.items()
            if current_time - ts > self.ttl_seconds
        ]

        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

    def _evict_lru(self) -> None:
        """Remove least recently used entries."""
        while len(self.cache) >= self.max_size and self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if self._is_expired(timestamp):
                    del self.cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
                    return None

                # Move to end (most recently used)
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)

                return value
            return None

    def put(self, key: str, value: Any) -> None:
        """Put value into cache."""
        with self._lock:
            current_time = time.time()

            # Remove expired entries
            self._evict_expired()

            # Evict LRU entries if over capacity
            self._evict_lru()

            # Add new entry
            self.cache[key] = (value, current_time)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            time.time()
            expired_count = sum(
                1 for _, ts in self.cache.values() if self._is_expired(ts)
            )

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "expired_entries": expired_count,
                "hit_ratio": getattr(self, "_hit_count", 0)
                / max(getattr(self, "_total_requests", 1), 1),
            }


class EnhancedStorageEngine:
    """Enhanced storage engine with temporal indexing, semantic caching, and performance optimization."""

    def __init__(self, index_dir: Path) -> None:
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Initialize storage components
        self.db_path = self.index_dir / "enhanced_storage.db"
        self.temporal_index = TemporalIndex(self.db_path)
        self.semantic_cache = SemanticCache()

        # File paths for traditional storage
        self.index_file = self.index_dir / "chat_index.json"
        self.vocabulary_file = self.index_dir / "vocabulary.json"
        self.metadata_file = self.index_dir / "metadata.json"
        self.conversation_graph_file = self.index_dir / "conversation_graph.json"

        # In-memory caches
        self._index_cache: dict | None = None
        self._vocabulary_cache: dict | None = None
        self._metadata_cache: dict | None = None
        self._conversation_graph_cache: dict | None = None

        # Performance metrics
        self.performance_metrics = {
            "queries_served": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0,
        }

        self.logger.info("Enhanced storage engine initialized")

    def _generate_cache_key(self, query: str, filters: dict[str, Any]) -> str:
        """Generate cache key for search query."""
        cache_data = {
            "query": query,
            "filters": sorted(filters.items()),
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def load_index(self) -> dict[str, Any]:
        """Load chat index with caching."""
        if self._index_cache is None:
            try:
                if self.index_file.exists():
                    with open(self.index_file, encoding="utf-8") as f:
                        self._index_cache = json.load(f)
                else:
                    self._index_cache = {
                        "entries": {},
                        "word_index": {},
                        "date_index": {},
                        "project_index": {},
                    }
            except Exception as e:
                self.logger.exception(f"Failed to load index: {e}")
                self._index_cache = {
                    "entries": {},
                    "word_index": {},
                    "date_index": {},
                    "project_index": {},
                }
        return self._index_cache

    def save_index(self, index: dict[str, Any]) -> None:
        """Save chat index and update cache."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            self._index_cache = index
        except Exception as e:
            self.logger.exception(f"Failed to save index: {e}")

    def load_vocabulary(self) -> dict[str, Any]:
        """Load vocabulary with caching."""
        if self._vocabulary_cache is None:
            try:
                if self.vocabulary_file.exists():
                    with open(self.vocabulary_file, encoding="utf-8") as f:
                        self._vocabulary_cache = json.load(f)
                else:
                    self._vocabulary_cache = {}
            except Exception as e:
                self.logger.exception(f"Failed to load vocabulary: {e}")
                self._vocabulary_cache = {}
        return self._vocabulary_cache

    def save_vocabulary(self, vocabulary: dict[str, Any]) -> None:
        """Save vocabulary and update cache."""
        try:
            with open(self.vocabulary_file, "w", encoding="utf-8") as f:
                json.dump(vocabulary, f, indent=2, ensure_ascii=False)
            self._vocabulary_cache = vocabulary
        except Exception as e:
            self.logger.exception(f"Failed to save vocabulary: {e}")

    def load_metadata(self) -> dict[str, Any]:
        """Load metadata with caching."""
        if self._metadata_cache is None:
            try:
                if self.metadata_file.exists():
                    with open(self.metadata_file, encoding="utf-8") as f:
                        self._metadata_cache = json.load(f)
                else:
                    self._metadata_cache = {
                        "last_updated": None,
                        "total_entries": 0,
                        "index_version": "2.0",
                        "enhanced_features": True,
                    }
            except Exception as e:
                self.logger.exception(f"Failed to load metadata: {e}")
                self._metadata_cache = {
                    "last_updated": None,
                    "total_entries": 0,
                    "index_version": "2.0",
                    "enhanced_features": True,
                }
        return self._metadata_cache

    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata and update cache."""
        try:
            metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self._metadata_cache = metadata
        except Exception as e:
            self.logger.exception(f"Failed to save metadata: {e}")

    def load_conversation_graph(self) -> dict[str, Any]:
        """Load conversation knowledge graph with caching."""
        if self._conversation_graph_cache is None:
            try:
                if self.conversation_graph_file.exists():
                    with open(self.conversation_graph_file, encoding="utf-8") as f:
                        self._conversation_graph_cache = json.load(f)
                else:
                    self._conversation_graph_cache = {
                        "nodes": {},
                        "edges": [],
                        "topics": {},
                        "last_updated": None,
                    }
            except Exception as e:
                self.logger.exception(f"Failed to load conversation graph: {e}")
                self._conversation_graph_cache = {
                    "nodes": {},
                    "edges": [],
                    "topics": {},
                    "last_updated": None,
                }
        return self._conversation_graph_cache

    def save_conversation_graph(self, graph: dict[str, Any]) -> None:
        """Save conversation graph and update cache."""
        try:
            graph["last_updated"] = datetime.now().isoformat()
            with open(self.conversation_graph_file, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)
            self._conversation_graph_cache = graph
        except Exception as e:
            self.logger.exception(f"Failed to save conversation graph: {e}")

    def add_temporal_entry(
        self,
        entry_id: str,
        entry: dict[str, Any],
        intensity_score: float = 0.0,
        topic_vector: list[float] | None = None,
    ) -> None:
        """Add entry to temporal index."""
        timestamp = entry.get("timestamp", 0)
        if timestamp:
            self.temporal_index.add_entry(
                entry_id=entry_id,
                timestamp=timestamp,
                intensity_score=intensity_score,
                topic_vector=topic_vector,
                metadata=entry,
            )

    def get_cached_search_results(
        self, query: str, filters: dict[str, Any]
    ) -> list[dict] | None:
        """Get cached search results."""
        cache_key = self._generate_cache_key(query, filters)
        self.performance_metrics["queries_served"] += 1

        cached_result = self.semantic_cache.get(cache_key)
        if cached_result is not None:
            self.performance_metrics["cache_hits"] += 1
            return cached_result

        return None

    def cache_search_results(
        self, query: str, filters: dict[str, Any], results: list[dict]
    ) -> None:
        """Cache search results."""
        cache_key = self._generate_cache_key(query, filters)
        self.semantic_cache.put(cache_key, results)

    def get_temporal_patterns(self, time_period: str = "week") -> dict[str, Any]:
        """Get temporal conversation patterns."""
        return {
            "intensity_metrics": self.temporal_index.get_conversation_intensity(
                bucket=datetime.now().strftime("%Y-%m-%d"),
                scale="date",
            ),
            "trending_topics": self.temporal_index.get_trending_topics(
                time_period=time_period
            ),
            "analysis_period": time_period,
            "generated_at": datetime.now().isoformat(),
        }

    def update_performance_metrics(self, response_time: float) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_response_time"] += response_time
        self.performance_metrics["avg_response_time"] = (
            self.performance_metrics["total_response_time"]
            / self.performance_metrics["queries_served"]
        )

    def get_storage_stats(self) -> dict[str, Any]:
        """Get comprehensive storage statistics."""
        index = self.load_index()
        metadata = self.load_metadata()

        return {
            "storage_engine": "enhanced",
            "version": "2.0",
            "indexed_entries": len(index.get("entries", {})),
            "vocabulary_size": len(self.load_vocabulary()),
            "temporal_entries": self._get_temporal_entry_count(),
            "conversation_graph_nodes": len(
                self.load_conversation_graph().get("nodes", {})
            ),
            "cache_stats": self.semantic_cache.get_stats(),
            "performance_metrics": self.performance_metrics.copy(),
            "file_sizes": {
                "index": (
                    self.index_file.stat().st_size if self.index_file.exists() else 0
                ),
                "vocabulary": (
                    self.vocabulary_file.stat().st_size
                    if self.vocabulary_file.exists()
                    else 0
                ),
                "metadata": (
                    self.metadata_file.stat().st_size
                    if self.metadata_file.exists()
                    else 0
                ),
                "conversation_graph": (
                    self.conversation_graph_file.stat().st_size
                    if self.conversation_graph_file.exists()
                    else 0
                ),
                "database": self.db_path.stat().st_size if self.db_path.exists() else 0,
            },
            "last_updated": metadata.get("last_updated"),
            "enhanced_features_enabled": True,
        }

    def _get_temporal_entry_count(self) -> int:
        """Get count of entries in temporal index."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM temporal_index")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def optimize_storage(self) -> None:
        """Optimize storage performance."""
        self.logger.info("Optimizing storage engine...")

        # Clear expired cache entries
        self.semantic_cache._evict_expired()

        # Optimize database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
        except Exception as e:
            self.logger.exception(f"Database optimization failed: {e}")

        # Clear in-memory caches to free memory
        self._index_cache = None
        self._vocabulary_cache = None
        self._metadata_cache = None
        self._conversation_graph_cache = None

        self.logger.info("Storage optimization completed")
