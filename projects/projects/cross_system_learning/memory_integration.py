"""
Memory Integration System - Unified memory system that combines conversation memory,
enhancement patterns, domain-specific libraries, and quality gate data.

This system provides:
1. Unified memory architecture across all components
2. Cross-reference linking between different memory types
3. Memory consolidation and knowledge retention
4. Intelligent memory retrieval and pattern matching
5. Learning from integrated memory analysis
"""

import hashlib
import json
import logging
import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .core.base_patterns import DomainType
from .core.memory_structures import (
    MemoryManager,
)


class MemoryType(Enum):
    """Types of memory entries."""

    CONVERSATION = "conversation"
    PATTERN = "pattern"
    QUALITY_METRICS = "quality_metrics"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_PERFORMANCE = "system_performance"
    LEARNING_INSIGHT = "learning_insight"


class MemoryLinkType(Enum):
    """Types of links between memory entries."""

    CAUSES = "causes"  # A causes B
    ENHANCES = "enhances"  # A enhances B
    REPLACES = "replaces"  # A replaces B
    COMPLEMENTS = "complements"  # A complements B
    CONFLICTS = "conflicts"  # A conflicts with B
    PRECEDES = "precedes"  # A precedes B in sequence
    RELATES_TO = "relates_to"  # General relationship


@dataclass
class MemoryLink:
    """Link between two memory entries."""

    link_id: str
    source_memory_id: str
    target_memory_id: str
    link_type: MemoryLinkType
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_validated: datetime | None = None
    validation_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegratedMemoryEntry:
    """Unified memory entry that combines information from multiple sources."""

    memory_id: str
    memory_type: MemoryType
    primary_data: dict[str, Any]
    related_entries: list[str] = field(default_factory=list)
    links: list[MemoryLink] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    domain: DomainType | None = None
    quality_score: float = 0.0
    importance_score: float = 0.0
    access_frequency: int = 0
    last_accessed: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    expiry: datetime | None = None

    def add_link(
        self,
        target_id: str,
        link_type: MemoryLinkType,
        strength: float = 0.5,
        confidence: float = 0.5,
    ) -> MemoryLink:
        """Add a link to another memory entry."""
        link = MemoryLink(
            link_id=str(uuid.uuid4()),
            source_memory_id=self.memory_id,
            target_memory_id=target_id,
            link_type=link_type,
            strength=strength,
            confidence=confidence,
        )
        self.links.append(link)
        return link

    def access(self) -> None:
        """Record access to this memory entry."""
        self.access_frequency += 1
        self.last_accessed = datetime.now()

    def is_expired(self) -> bool:
        """Check if this memory entry has expired."""
        if self.expiry is None:
            return False
        return datetime.now() > self.expiry

    def calculate_composite_score(self) -> float:
        """Calculate composite importance score."""
        return (
            self.quality_score * 0.4
            + self.importance_score * 0.4
            + min(1.0, self.access_frequency / 100.0) * 0.2
        )


@dataclass
class MemoryCluster:
    """Cluster of related memory entries."""

    cluster_id: str
    name: str
    description: str
    memory_ids: set[str] = field(default_factory=set)
    centroid_vector: list[float] = field(default_factory=list)
    coherence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class MemoryIntegrationSystem:
    """Unified memory integration system."""

    def __init__(self, memory_manager: MemoryManager | None = None):
        self.memory_manager = memory_manager or MemoryManager()
        self.logger = logging.getLogger(__name__)

        # Core memory storage
        self.integrated_memories: dict[str, IntegratedMemoryEntry] = {}
        self.memory_clusters: dict[str, MemoryCluster] = {}
        self.memory_links: dict[str, MemoryLink] = {}

        # Domain-specific knowledge bases
        self.domain_knowledge: dict[DomainType, dict[str, Any]] = defaultdict(dict)

        # Memory management
        self.max_memories = 50000
        self.max_clusters = 1000
        self.consolidation_interval = timedelta(hours=24)
        self.default_ttl = timedelta(days=90)

        # Learning parameters
        self.learning_rate = 0.1
        self.forget_rate = 0.01
        self.importance_decay_rate = 0.05

        # Vector space for semantic similarity
        self.memory_vectors: dict[str, list[float]] = {}
        self.vector_dimensions = 512

        # Performance tracking
        self.integration_stats = {
            "total_memories": 0,
            "total_links": 0,
            "total_clusters": 0,
            "memory_type_distribution": defaultdict(int),
            "domain_distribution": defaultdict(int),
        }

        # Threading
        self.lock = threading.RLock()
        self._shutdown = False
        self._background_threads: list[threading.Thread] = []

        # Initialize background tasks
        self._start_background_tasks()

    def integrate_memory(
        self,
        memory_type: MemoryType,
        data: dict[str, Any],
        source_system: str = "",
        ttl_hours: int | None = None,
    ) -> str:
        """Integrate a new memory entry into the unified system."""
        with self.lock:
            memory_id = str(uuid.uuid4())

            # Create integrated memory entry
            expiry = None
            if ttl_hours:
                expiry = datetime.now() + timedelta(hours=ttl_hours)

            integrated_entry = IntegratedMemoryEntry(
                memory_id=memory_id,
                memory_type=memory_type,
                primary_data=data,
                expiry=expiry,
            )

            # Extract and enrich information based on memory type
            self._enrich_memory_entry(integrated_entry, memory_type, data)

            # Generate memory vector for semantic similarity
            vector = self._generate_memory_vector(integrated_entry)
            if vector:
                self.memory_vectors[memory_id] = vector

            # Find related memories and create links
            related_memories = self._find_related_memories(integrated_entry)
            for related_id, similarity_score in related_memories:
                if similarity_score > 0.3:  # Threshold for creating links
                    link_type = self._determine_link_type(
                        integrated_entry, self.integrated_memories.get(related_id)
                    )
                    integrated_entry.add_link(
                        related_id, link_type, similarity_score, similarity_score
                    )

            # Add to storage
            self.integrated_memories[memory_id] = integrated_entry

            # Update statistics
            self.integration_stats["total_memories"] += 1
            self.integration_stats["memory_type_distribution"][memory_type.value] += 1
            if integrated_entry.domain:
                self.integration_stats["domain_distribution"][
                    integrated_entry.domain.value
                ] += 1

            # Cluster if appropriate
            self._cluster_memory_if_needed(integrated_entry)

            self.logger.info(f"Integrated {memory_type.value} memory: {memory_id}")
            return memory_id

    def _enrich_memory_entry(
        self,
        entry: IntegratedMemoryEntry,
        memory_type: MemoryType,
        data: dict[str, Any],
    ) -> None:
        """Enrich memory entry with additional information based on its type."""
        if memory_type == MemoryType.CONVERSATION:
            entry.domain = DomainType(data.get("domain", "software_development"))
            entry.importance_score = self._calculate_conversation_importance(data)
            entry.tags.update(data.get("tags", []))
            entry.tags.add("conversation")

        elif memory_type == MemoryType.PATTERN:
            pattern_data = data.get("pattern", {})
            if isinstance(pattern_data, dict):
                entry.domain = DomainType(
                    pattern_data.get("domain", "software_development")
                )
                entry.quality_score = pattern_data.get("quality_score", 0.0)
                entry.importance_score = pattern_data.get("importance_score", 0.5)
            entry.tags.add("pattern")

        elif memory_type == MemoryType.QUALITY_METRICS:
            metrics_data = data.get("metrics", {})
            if isinstance(metrics_data, dict):
                entry.domain = DomainType(
                    metrics_data.get("domain", "software_development")
                )
                entry.quality_score = (
                    metrics_data.get("improvement_percentage", 0.0) / 100.0
                )
                entry.importance_score = min(
                    1.0, metrics_data.get("processing_time", 1.0) / 10.0
                )
            entry.tags.add("quality")

        elif memory_type == MemoryType.DOMAIN_KNOWLEDGE:
            entry.domain = DomainType(data.get("domain", "software_development"))
            entry.importance_score = data.get("importance", 0.5)
            entry.tags.update(data.get("tags", []))
            entry.tags.add("domain_knowledge")

        elif memory_type == MemoryType.USER_FEEDBACK:
            feedback_data = data.get("feedback", {})
            if isinstance(feedback_data, dict):
                entry.quality_score = feedback_data.get("satisfaction_score", 0.0) / 5.0
                entry.importance_score = (
                    0.7 if feedback_data.get("is_critical", False) else 0.3
                )
            entry.tags.add("feedback")

        elif memory_type == MemoryType.SYSTEM_PERFORMANCE:
            perf_data = data.get("performance", {})
            if isinstance(perf_data, dict):
                entry.quality_score = 1.0 - min(1.0, perf_data.get("error_rate", 0.0))
                entry.importance_score = min(
                    1.0, perf_data.get("response_time", 1.0) / 5.0
                )
            entry.tags.add("performance")

        elif memory_type == MemoryType.LEARNING_INSIGHT:
            insight_data = data.get("insight", {})
            if isinstance(insight_data, dict):
                entry.quality_score = insight_data.get("confidence", 0.5)
                entry.importance_score = insight_data.get("impact", 0.5)
                entry.domain = DomainType(
                    insight_data.get("domain", "software_development")
                )
            entry.tags.add("insight")

    def _calculate_conversation_importance(
        self, conversation_data: dict[str, Any]
    ) -> float:
        """Calculate importance score for conversation memory."""
        importance = 0.0

        # Length factor
        message_count = len(conversation_data.get("messages", []))
        importance += min(0.3, message_count / 20.0)

        # Resolution factor
        if conversation_data.get("resolved", False):
            importance += 0.2

        # Complexity factor
        complexity = conversation_data.get("complexity", 0.5)
        importance += complexity * 0.3

        # User engagement factor
        engagement = conversation_data.get("user_engagement", 0.5)
        importance += engagement * 0.2

        return min(1.0, importance)

    def _generate_memory_vector(
        self, entry: IntegratedMemoryEntry
    ) -> list[float] | None:
        """Generate vector representation of memory for semantic similarity."""
        try:
            # Simple vector generation based on text content and features
            vector = [0.0] * self.vector_dimensions

            # Use hash-based encoding for text content
            text_content = json.dumps(entry.primary_data, sort_keys=True)
            text_hash = hashlib.md5(text_content.encode()).hexdigest()

            # Fill vector with hash-derived features
            for i, char in enumerate(text_hash[: self.vector_dimensions]):
                if char.isdigit():
                    vector[i] = int(char) / 10.0
                elif char.isalpha():
                    vector[i] = (ord(char.lower()) - ord("a")) / 26.0

            # Add type encoding
            type_encoding = hash(entry.memory_type.value) % 100
            vector[0] = type_encoding / 100.0

            # Add domain encoding
            if entry.domain:
                domain_encoding = hash(entry.domain.value) % 100
                vector[1] = domain_encoding / 100.0

            # Add quality and importance scores
            if self.vector_dimensions > 10:
                vector[10] = entry.quality_score
                vector[11] = entry.importance_score

            return vector

        except Exception as e:
            self.logger.error(f"Error generating memory vector: {str(e)}")
            return None

    def _find_related_memories(
        self, entry: IntegratedMemoryEntry, limit: int = 10
    ) -> list[tuple[str, float]]:
        """Find related memories using vector similarity."""
        if not self.memory_vectors or entry.memory_id not in self.memory_vectors:
            return []

        entry_vector = self.memory_vectors[entry.memory_id]
        similarities = []

        for memory_id, vector in self.memory_vectors.items():
            if memory_id == entry.memory_id:
                continue

            # Calculate cosine similarity
            similarity = self._cosine_similarity(entry_vector, vector)
            if similarity > 0.1:  # Minimum similarity threshold
                similarities.append((memory_id, similarity))

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
        magnitude_a = sum(a * a for a in vec_a) ** 0.5
        magnitude_b = sum(b * b for b in vec_b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _determine_link_type(
        self,
        source_entry: IntegratedMemoryEntry | None,
        target_entry: IntegratedMemoryEntry | None,
    ) -> MemoryLinkType:
        """Determine the type of link between two memory entries."""
        if not source_entry or not target_entry:
            return MemoryLinkType.RELATES_TO

        # Pattern-based link type determination
        if (
            source_entry.memory_type == MemoryType.PATTERN
            and target_entry.memory_type == MemoryType.CONVERSATION
        ):
            return MemoryLinkType.ENHANCES

        elif (
            source_entry.memory_type == MemoryType.CONVERSATION
            and target_entry.memory_type == MemoryType.PATTERN
        ):
            return MemoryLinkType.PRECEDES

        elif (
            source_entry.memory_type == MemoryType.QUALITY_METRICS
            and target_entry.memory_type == MemoryType.PATTERN
        ):
            return MemoryLinkType.CAUSES

        elif source_entry.domain == target_entry.domain:
            if source_entry.memory_type == target_entry.memory_type:
                return MemoryLinkType.COMPLEMENTS
            else:
                return MemoryLinkType.RELATES_TO

        elif (
            source_entry.memory_type == MemoryType.USER_FEEDBACK
            and target_entry.memory_type
            in [MemoryType.PATTERN, MemoryType.CONVERSATION]
        ):
            return MemoryLinkType.ENHANCES

        return MemoryLinkType.RELATES_TO

    def _cluster_memory_if_needed(self, entry: IntegratedMemoryEntry) -> None:
        """Cluster memory entry if appropriate."""
        # Find existing clusters
        best_cluster = None
        best_similarity = 0.0

        for cluster in self.memory_clusters.values():
            if entry.memory_id in cluster.memory_ids:
                return  # Already in this cluster

            if cluster.centroid_vector:
                similarity = self._cosine_similarity(
                    self.memory_vectors.get(entry.memory_id, []),
                    cluster.centroid_vector,
                )
                if similarity > best_similarity and similarity > 0.5:
                    best_similarity = similarity
                    best_cluster = cluster

        if best_cluster:
            # Add to existing cluster
            best_cluster.memory_ids.add(entry.memory_id)
            best_cluster.last_updated = datetime.now()
            self._update_cluster_centroid(best_cluster)
        else:
            # Create new cluster
            if len(self.memory_clusters) < self.max_clusters:
                cluster_id = str(uuid.uuid4())
                new_cluster = MemoryCluster(
                    cluster_id=cluster_id,
                    name=f"Cluster_{entry.memory_type.value}_{len(self.memory_clusters)}",
                    description=f"Cluster for {entry.memory_type.value} memories",
                    memory_ids={entry.memory_id},
                    centroid_vector=self.memory_vectors.get(entry.memory_id, []).copy(),
                )
                self.memory_clusters[cluster_id] = new_cluster
                self.integration_stats["total_clusters"] += 1

    def _update_cluster_centroid(self, cluster: MemoryCluster) -> None:
        """Update the centroid vector for a cluster."""
        if not cluster.memory_ids:
            return

        # Collect all vectors in the cluster
        cluster_vectors = []
        for memory_id in cluster.memory_ids:
            if memory_id in self.memory_vectors:
                cluster_vectors.append(self.memory_vectors[memory_id])

        if not cluster_vectors:
            return

        # Calculate centroid (mean of all vectors)
        if cluster_vectors:
            vector_length = len(cluster_vectors[0])
            centroid = [0.0] * vector_length

            for vector in cluster_vectors:
                for i, value in enumerate(vector):
                    centroid[i] += value

            # Normalize by number of vectors
            for i in range(vector_length):
                centroid[i] /= len(cluster_vectors)

            cluster.centroid_vector = centroid

    def retrieve_memories(
        self, query: dict[str, Any], limit: int = 20
    ) -> list[IntegratedMemoryEntry]:
        """Retrieve memories based on query criteria."""
        with self.lock:
            results = []

            for memory in self.integrated_memories.values():
                if memory.is_expired():
                    continue

                # Check if memory matches query
                if self._memory_matches_query(memory, query):
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(memory, query)
                    results.append((memory, relevance_score))

            # Sort by relevance score
            results.sort(key=lambda x: x[1], reverse=True)

            # Access memories (updates access statistics)
            retrieved_memories = []
            for memory, _ in results[:limit]:
                memory.access()
                retrieved_memories.append(memory)

            return retrieved_memories

    def _memory_matches_query(
        self, memory: IntegratedMemoryEntry, query: dict[str, Any]
    ) -> bool:
        """Check if a memory matches the query criteria."""
        # Memory type filter
        if "memory_type" in query:
            if isinstance(query["memory_type"], str):
                query_type = MemoryType(query["memory_type"])
                if memory.memory_type != query_type:
                    return False
            elif isinstance(query["memory_type"], list):
                query_types = [MemoryType(t) for t in query["memory_type"]]
                if memory.memory_type not in query_types:
                    return False

        # Domain filter
        if "domain" in query:
            if isinstance(query["domain"], str):
                query_domain = DomainType(query["domain"])
                if memory.domain != query_domain:
                    return False
            elif isinstance(query["domain"], list):
                query_domains = [DomainType(d) for d in query["domain"]]
                if memory.domain not in query_domains:
                    return False

        # Tags filter
        if "tags" in query:
            query_tags = set(query["tags"])
            if not query_tags.intersection(memory.tags):
                return False

        # Quality score filter
        if "min_quality" in query:
            if memory.quality_score < query["min_quality"]:
                return False

        # Importance score filter
        if "min_importance" in query:
            if memory.importance_score < query["min_importance"]:
                return False

        # Text search filter
        if "text_search" in query:
            search_terms = query["text_search"].lower().split()
            text_content = json.dumps(memory.primary_data).lower()
            if not all(term in text_content for term in search_terms):
                return False

        # Time range filter
        if "time_range" in query:
            time_range = query["time_range"]
            start_time = time_range.get("start")
            end_time = time_range.get("end")

            if start_time and memory.created_at < start_time:
                return False
            if end_time and memory.created_at > end_time:
                return False

        return True

    def _calculate_relevance_score(
        self, memory: IntegratedMemoryEntry, query: dict[str, Any]
    ) -> float:
        """Calculate relevance score for memory relative to query."""
        score = 0.0

        # Base composite score
        score += memory.calculate_composite_score() * 0.3

        # Recency bonus
        days_old = (datetime.now() - memory.created_at).days
        recency_bonus = max(0.0, 1.0 - days_old / 365.0)  # Decay over a year
        score += recency_bonus * 0.2

        # Access frequency bonus
        access_bonus = min(1.0, memory.access_frequency / 50.0)
        score += access_bonus * 0.1

        # Query-specific bonuses
        if "tags" in query:
            query_tags = set(query["tags"])
            tag_overlap = len(query_tags.intersection(memory.tags))
            if query_tags:
                score += (tag_overlap / len(query_tags)) * 0.2

        if "domain" in query and memory.domain:
            if (
                isinstance(query["domain"], str)
                and memory.domain.value == query["domain"]
            ):
                score += 0.1
            elif (
                isinstance(query["domain"], list)
                and memory.domain.value in query["domain"]
            ):
                score += 0.1

        return min(1.0, score)

    def get_memory_connections(self, memory_id: str, depth: int = 2) -> dict[str, Any]:
        """Get connected memories with specified depth."""
        with self.lock:
            if memory_id not in self.integrated_memories:
                return {}

            visited = set()
            connections = {memory_id: self.integrated_memories[memory_id]}
            queue = [(memory_id, 0)]

            while queue:
                current_id, current_depth = queue.pop(0)

                if current_id in visited or current_depth >= depth:
                    continue

                visited.add(current_id)
                current_memory = self.integrated_memories.get(current_id)

                if not current_memory:
                    continue

                # Add linked memories
                for link in current_memory.links:
                    if (
                        link.target_memory_id not in connections
                        and link.target_memory_id in self.integrated_memories
                    ):
                        connections[link.target_memory_id] = self.integrated_memories[
                            link.target_memory_id
                        ]
                        queue.append((link.target_memory_id, current_depth + 1))

            return {
                "root_memory_id": memory_id,
                "total_connections": len(connections) - 1,
                "connections": {
                    mem_id: memory.to_dict()
                    if hasattr(memory, "to_dict")
                    else {
                        "memory_id": memory.memory_id,
                        "memory_type": memory.memory_type.value,
                        "quality_score": memory.quality_score,
                        "importance_score": memory.importance_score,
                        "tags": list(memory.tags),
                    }
                    for mem_id, memory in connections.items()
                },
            }

    def consolidate_memory(self) -> dict[str, int]:
        """Consolidate and optimize memory storage."""
        consolidation_results = {
            "expired_removed": 0,
            "duplicates_merged": 0,
            "clusters_merged": 0,
            "low_importance_removed": 0,
        }

        with self.lock:
            # Remove expired memories
            expired_ids = [
                mem_id
                for mem_id, memory in self.integrated_memories.items()
                if memory.is_expired()
            ]

            for mem_id in expired_ids:
                del self.integrated_memories[mem_id]
                if mem_id in self.memory_vectors:
                    del self.memory_vectors[mem_id]
                consolidation_results["expired_removed"] += 1

            # Remove and update empty clusters
            empty_cluster_ids = [
                cluster_id
                for cluster_id, cluster in self.memory_clusters.items()
                if not cluster.memory_ids
            ]

            for cluster_id in empty_cluster_ids:
                del self.memory_clusters[cluster_id]
                consolidation_results["clusters_merged"] += 1

            # Remove low-importance memories if over limit
            if len(self.integrated_memories) > self.max_memories:
                memories_by_importance = sorted(
                    self.integrated_memories.items(),
                    key=lambda x: x[1].calculate_composite_score(),
                )

                excess_count = len(self.integrated_memories) - self.max_memories
                for mem_id, _ in memories_by_importance[:excess_count]:
                    if self.integrated_memories[mem_id].importance_score < 0.2:
                        del self.integrated_memories[mem_id]
                        if mem_id in self.memory_vectors:
                            del self.memory_vectors[mem_id]
                        consolidation_results["low_importance_removed"] += 1

            # Merge similar clusters
            self._merge_similar_clusters(consolidation_results)

        self.logger.info(f"Memory consolidation completed: {consolidation_results}")
        return consolidation_results

    def _merge_similar_clusters(self, consolidation_results: dict[str, int]) -> None:
        """Merge similar clusters to optimize storage."""
        cluster_list = list(self.memory_clusters.values())
        merged_clusters = set()

        for i, cluster_a in enumerate(cluster_list):
            if cluster_a.cluster_id in merged_clusters:
                continue

            for cluster_b in cluster_list[i + 1 :]:
                if cluster_b.cluster_id in merged_clusters:
                    continue

                # Calculate cluster similarity
                similarity = self._calculate_cluster_similarity(cluster_a, cluster_b)

                if similarity > 0.8:  # High similarity threshold
                    # Merge cluster_b into cluster_a
                    cluster_a.memory_ids.update(cluster_b.memory_ids)
                    self._update_cluster_centroid(cluster_a)

                    # Remove cluster_b
                    del self.memory_clusters[cluster_b.cluster_id]
                    merged_clusters.add(cluster_b.cluster_id)
                    consolidation_results["clusters_merged"] += 1

    def _calculate_cluster_similarity(
        self, cluster_a: MemoryCluster, cluster_b: MemoryCluster
    ) -> float:
        """Calculate similarity between two clusters."""
        if not cluster_a.centroid_vector or not cluster_b.centroid_vector:
            return 0.0

        return self._cosine_similarity(
            cluster_a.centroid_vector, cluster_b.centroid_vector
        )

    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        # Memory consolidation thread
        consolidation_thread = threading.Thread(
            target=self._background_consolidation, daemon=True
        )
        consolidation_thread.start()
        self._background_threads.append(consolidation_thread)

        # Importance decay thread
        decay_thread = threading.Thread(
            target=self._background_importance_decay, daemon=True
        )
        decay_thread.start()
        self._background_threads.append(decay_thread)

        # Cluster optimization thread
        cluster_thread = threading.Thread(
            target=self._background_cluster_optimization, daemon=True
        )
        cluster_thread.start()
        self._background_threads.append(cluster_thread)

    def _background_consolidation(self) -> None:
        """Background thread for memory consolidation."""
        while not self._shutdown:
            try:
                self.consolidate_memory()
                threading.Event().wait(
                    timeout=self.consolidation_interval.total_seconds()
                )

            except Exception as e:
                self.logger.error(f"Error in background consolidation: {str(e)}")
                threading.Event().wait(timeout=300)  # 5 minutes on error

    def _background_importance_decay(self) -> None:
        """Background thread for importance score decay."""
        while not self._shutdown:
            try:
                with self.lock:
                    for memory in self.integrated_memories.values():
                        # Decay importance scores
                        memory.importance_score *= 1.0 - self.importance_decay_rate
                        memory.quality_score *= 1.0 - self.forget_rate

                        # Update composite score automatically
                        memory.calculate_composite_score()

                threading.Event().wait(timeout=3600)  # 1 hour

            except Exception as e:
                self.logger.error(f"Error in importance decay: {str(e)}")
                threading.Event().wait(timeout=300)

    def _background_cluster_optimization(self) -> None:
        """Background thread for cluster optimization."""
        while not self._shutdown:
            try:
                with self.lock:
                    # Update cluster centroids
                    for cluster in self.memory_clusters.values():
                        self._update_cluster_centroid(cluster)

                    # Recluster if needed
                    self._recluster_memories_if_needed()

                threading.Event().wait(timeout=1800)  # 30 minutes

            except Exception as e:
                self.logger.error(f"Error in cluster optimization: {str(e)}")
                threading.Event().wait(timeout=300)

    def _recluster_memories_if_needed(self) -> None:
        """Recluster memories if clusters are not optimal."""
        # Check if any memory is not in an appropriate cluster
        for memory_id, memory in self.integrated_memories.items():
            current_cluster = None
            for cluster in self.memory_clusters.values():
                if memory_id in cluster.memory_ids:
                    current_cluster = cluster
                    break

            if current_cluster and memory_id in self.memory_vectors:
                # Check if memory fits well in current cluster
                similarity = self._cosine_similarity(
                    self.memory_vectors[memory_id], current_cluster.centroid_vector
                )

                # If similarity is low, consider moving or creating new cluster
                if similarity < 0.3:
                    # Find better cluster or create new one
                    best_cluster = None
                    best_similarity = 0.0

                    for cluster in self.memory_clusters.values():
                        if cluster.cluster_id != current_cluster.cluster_id:
                            sim = self._cosine_similarity(
                                self.memory_vectors[memory_id], cluster.centroid_vector
                            )
                            if sim > best_similarity and sim > 0.5:
                                best_similarity = sim
                                best_cluster = cluster

                    if best_cluster:
                        # Move to better cluster
                        current_cluster.memory_ids.remove(memory_id)
                        best_cluster.memory_ids.add(memory_id)
                        self._update_cluster_centroid(current_cluster)
                        self._update_cluster_centroid(best_cluster)

    def get_integration_statistics(self) -> dict[str, Any]:
        """Get comprehensive integration statistics."""
        with self.lock:
            stats = self.integration_stats.copy()

            # Current counts
            stats["current_memories"] = len(self.integrated_memories)
            stats["current_clusters"] = len(self.memory_clusters)
            stats["current_links"] = sum(
                len(memory.links) for memory in self.integrated_memories.values()
            )

            # Memory type distribution
            stats["current_memory_type_distribution"] = defaultdict(int)
            stats["current_domain_distribution"] = defaultdict(int)

            for memory in self.integrated_memories.values():
                stats["current_memory_type_distribution"][memory.memory_type.value] += 1
                if memory.domain:
                    stats["current_domain_distribution"][memory.domain.value] += 1

            # Quality and importance statistics
            if self.integrated_memories:
                qualities = [m.quality_score for m in self.integrated_memories.values()]
                importances = [
                    m.importance_score for m in self.integrated_memories.values()
                ]
                composites = [
                    m.calculate_composite_score()
                    for m in self.integrated_memories.values()
                ]

                stats["average_quality_score"] = sum(qualities) / len(qualities)
                stats["average_importance_score"] = sum(importances) / len(importances)
                stats["average_composite_score"] = sum(composites) / len(composites)

            # Convert defaultdicts to regular dicts
            stats["memory_type_distribution"] = dict(stats["memory_type_distribution"])
            stats["domain_distribution"] = dict(stats["domain_distribution"])
            stats["current_memory_type_distribution"] = dict(
                stats["current_memory_type_distribution"]
            )
            stats["current_domain_distribution"] = dict(
                stats["current_domain_distribution"]
            )

            return stats

    def shutdown(self) -> None:
        """Shutdown the memory integration system gracefully."""
        self._shutdown = True

        # Wait for background threads to finish
        for thread in self._background_threads:
            if thread.is_alive():
                thread.join(timeout=10)

        # Final consolidation
        self.consolidate_memory()

        # Save to disk
        self.memory_manager.save_to_disk()

        self.logger.info("Memory Integration System shutdown complete")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except:
            pass
