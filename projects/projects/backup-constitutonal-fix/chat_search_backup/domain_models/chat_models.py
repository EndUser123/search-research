from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

#!/usr/bin/env python3
"""Domain Models for Enhanced CHS
Clean architecture domain models for chat analysis system.
"""




class MessageType(Enum):
    """Message type enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ConversationContext(Enum):
    """Conversation context types."""

    PROJECT = "project"
    GENERAL = "general"
    TECHNICAL = "technical"
    RESEARCH = "research"
    DEBUGGING = "debugging"
    PLANNING = "planning"


class SearchRanking(Enum):
    """Search ranking methods."""

    RELEVANCE = "relevance"
    RECENCY = "recency"
    FREQUENCY = "frequency"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"


class TemporalScale(Enum):
    """Temporal analysis scales."""

    HOURLY = "hour"
    DAILY = "day"
    WEEKLY = "week"
    MONTHLY = "month"
    QUARTERLY = "quarter"


@dataclass
class ChatMessage:
    """Core chat message domain model."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    timestamp: int = field(
        default_factory=lambda: int(datetime.now().timestamp() * 1000)
    )
    message_type: MessageType = MessageType.USER
    context: ConversationContext = ConversationContext.GENERAL
    project_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Enhanced fields for CHS
    intensity_score: float = 0.0
    topic_vector: list[float] | None = None
    semantic_tags: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_type": self.message_type.value,
            "context": self.context.value,
            "project_name": self.project_name,
            "metadata": self.metadata,
            "intensity_score": self.intensity_score,
            "topic_vector": self.topic_vector,
            "semantic_tags": self.semantic_tags,
            "related_entries": self.related_entries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        """Create from dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", int(datetime.now().timestamp() * 1000)),
            message_type=MessageType(data.get("message_type", "user")),
            context=ConversationContext(data.get("context", "general")),
            project_name=data.get("project_name"),
            metadata=data.get("metadata", {}),
            intensity_score=data.get("intensity_score", 0.0),
            topic_vector=data.get("topic_vector"),
            semantic_tags=data.get("semantic_tags", []),
            related_entries=data.get("related_entries", []),
        )

    @property
    def datetime(self) -> datetime:
        """Get datetime object from timestamp."""
        return datetime.fromtimestamp(self.timestamp / 1000)

    def add_tag(self, tag: str) -> None:
        """Add semantic tag."""
        if tag not in self.semantic_tags:
            self.semantic_tags.append(tag)

    def add_related_entry(self, entry_id: str) -> None:
        """Add related entry reference."""
        if entry_id not in self.related_entries:
            self.related_entries.append(entry_id)


@dataclass
class SearchResult:
    """Search result domain model."""

    message: ChatMessage
    relevance_score: float = 0.0
    matched_terms: list[str] = field(default_factory=list)
    highlighted_snippet: str | None = None
    ranking_method: SearchRanking = SearchRanking.RELEVANCE
    temporal_relevance: float = 0.0
    semantic_similarity: float = 0.0

    # Evidence tracking
    evidence_sources: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message.to_dict(),
            "relevance_score": self.relevance_score,
            "matched_terms": self.matched_terms,
            "highlighted_snippet": self.highlighted_snippet,
            "ranking_method": self.ranking_method.value,
            "temporal_relevance": self.temporal_relevance,
            "semantic_similarity": self.semantic_similarity,
            "evidence_sources": self.evidence_sources,
            "confidence_score": self.confidence_score,
            "processing_metadata": self.processing_metadata,
        }


@dataclass
class ConversationPattern:
    """Conversation pattern domain model."""

    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = ""
    description: str = ""
    frequency: int = 0
    confidence: float = 0.0
    time_span_days: int = 0
    context_distribution: dict[ConversationContext, int] = field(default_factory=dict)
    sample_messages: list[str] = field(default_factory=list)
    temporal_distribution: dict[str, int] = field(default_factory=dict)
    related_patterns: list[str] = field(default_factory=list)

    # Evidence fields
    evidence_entries: list[str] = field(default_factory=list)
    last_observed: datetime | None = None
    trend_direction: str = "stable"  # increasing, decreasing, stable

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "time_span_days": self.time_span_days,
            "context_distribution": {
                ctx.value: count for ctx, count in self.context_distribution.items()
            },
            "sample_messages": self.sample_messages,
            "temporal_distribution": self.temporal_distribution,
            "related_patterns": self.related_patterns,
            "evidence_entries": self.evidence_entries,
            "last_observed": (
                self.last_observed.isoformat() if self.last_observed else None
            ),
            "trend_direction": self.trend_direction,
        }


@dataclass
class TemporalMetrics:
    """Temporal analysis metrics domain model."""

    time_bucket: str
    scale: TemporalScale
    message_count: int = 0
    intensity_average: float = 0.0
    intensity_peak: float = 0.0
    topic_distribution: dict[str, float] = field(default_factory=dict)
    context_distribution: dict[ConversationContext, int] = field(default_factory=dict)
    unique_topics: int = 0
    engagement_score: float = 0.0

    # Trend analysis
    trend_slope: float = 0.0
    trend_significance: float = 0.0
    seasonality_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "time_bucket": self.time_bucket,
            "scale": self.scale.value,
            "message_count": self.message_count,
            "intensity_average": self.intensity_average,
            "intensity_peak": self.intensity_peak,
            "topic_distribution": self.topic_distribution,
            "context_distribution": {
                ctx.value: count for ctx, count in self.context_distribution.items()
            },
            "unique_topics": self.unique_topics,
            "engagement_score": self.engagement_score,
            "trend_slope": self.trend_slope,
            "trend_significance": self.trend_significance,
            "seasonality_detected": self.seasonality_detected,
        }


@dataclass
class KnowledgeGraph:
    """Knowledge graph domain model for conversations."""

    graph_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    topics: dict[str, dict[str, Any]] = field(default_factory=dict)
    clusters: dict[str, list[str]] = field(default_factory=dict)
    centrality_scores: dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    # Graph metrics
    node_count: int = 0
    edge_count: int = 0
    cluster_count: int = 0
    average_degree: float = 0.0
    modularity: float = 0.0

    def add_node(self, node_id: str, node_data: dict[str, Any]) -> None:
        """Add node to graph."""
        self.nodes[node_id] = node_data
        self.node_count = len(self.nodes)
        self._update_metrics()

    def add_edge(self, source: str, target: str, edge_data: dict[str, Any]) -> None:
        """Add edge to graph."""
        edge = {
            "source": source,
            "target": target,
            **edge_data,
        }
        self.edges.append(edge)
        self.edge_count = len(self.edges)
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Update graph metrics."""
        if self.nodes:
            total_degree = sum(
                len(
                    [
                        e
                        for e in self.edges
                        if e["source"] == node or e["target"] == node
                    ]
                )
                for node in self.nodes
            )
            self.average_degree = total_degree / len(self.nodes) if self.nodes else 0.0

        self.cluster_count = len(self.clusters)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "graph_id": self.graph_id,
            "nodes": self.nodes,
            "edges": self.edges,
            "topics": self.topics,
            "clusters": self.clusters,
            "centrality_scores": self.centrality_scores,
            "last_updated": self.last_updated.isoformat(),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "cluster_count": self.cluster_count,
            "average_degree": self.average_degree,
            "modularity": self.modularity,
        }


@dataclass
class AnalysisSession:
    """Analysis session domain model."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    results: list[SearchResult] = field(default_factory=list)
    patterns: list[ConversationPattern] = field(default_factory=list)
    temporal_metrics: list[TemporalMetrics] = field(default_factory=list)
    knowledge_graph: KnowledgeGraph | None = None

    # Session metadata
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    processing_time_ms: int = 0
    cache_hit: bool = False
    user_feedback: str | None = None
    session_metadata: dict[str, Any] = field(default_factory=dict)

    # Evidence tracking
    evidence_collected: dict[str, list[str]] = field(default_factory=dict)
    confidence_score: float = 0.0
    validation_status: str = "pending"  # pending, validated, failed

    def add_result(self, result: SearchResult) -> None:
        """Add search result to session."""
        self.results.append(result)

    def add_pattern(self, pattern: ConversationPattern) -> None:
        """Add pattern to session."""
        self.patterns.append(pattern)

    def add_temporal_metric(self, metric: TemporalMetrics) -> None:
        """Add temporal metric to session."""
        self.temporal_metrics.append(metric)

    def complete_session(self, processing_time_ms: int) -> None:
        """Mark session as completed."""
        self.completed_at = datetime.now()
        self.processing_time_ms = processing_time_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "filters": self.filters,
            "results": [result.to_dict() for result in self.results],
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "temporal_metrics": [metric.to_dict() for metric in self.temporal_metrics],
            "knowledge_graph": (
                self.knowledge_graph.to_dict() if self.knowledge_graph else None
            ),
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "processing_time_ms": self.processing_time_ms,
            "cache_hit": self.cache_hit,
            "user_feedback": self.user_feedback,
            "session_metadata": self.session_metadata,
            "evidence_collected": self.evidence_collected,
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
        }


@dataclass
class ExportConfiguration:
    """Export configuration domain model."""

    export_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    format: str = "json"  # json, csv, markdown, xml
    include_analysis: bool = True
    include_patterns: bool = True
    include_temporal_data: bool = True
    include_knowledge_graph: bool = True
    include_evidence: bool = True
    max_results: int = 1000
    date_range: tuple | None = None
    context_filters: list[ConversationContext] = field(default_factory=list)
    output_path: str | None = None
    custom_template: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "export_id": self.export_id,
            "format": self.format,
            "include_analysis": self.include_analysis,
            "include_patterns": self.include_patterns,
            "include_temporal_data": self.include_temporal_data,
            "include_knowledge_graph": self.include_knowledge_graph,
            "include_evidence": self.include_evidence,
            "max_results": self.max_results,
            "date_range": self.date_range,
            "context_filters": [ctx.value for ctx in self.context_filters],
            "output_path": self.output_path,
            "custom_template": self.custom_template,
        }
