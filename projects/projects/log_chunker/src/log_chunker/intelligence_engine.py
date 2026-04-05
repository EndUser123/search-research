from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# Based on usage in chunking_engine.py and plugins
class ChunkInfo(BaseModel):
    """Metadata for individual chunks."""

    chunk_id: int
    start_line: int
    end_line: int
    estimated_tokens: int
    method_used: str = "unknown"
    quality_score: float = 0.0
    plugin_scores: dict[str, float] = Field(default_factory=dict)
    boundary_type: str | None = None  # from boundary_detection.py


# Based on usage in preprocessor.py
class LogEntry(BaseModel):
    """Represents a parsed log entry with metadata."""

    line_number: int | None = None  # Set later
    timestamp: str | None = None  # Preprocessor creates strings
    level: str | None = None
    message: str
    original_line: str
    logger: str | None = None
    pattern: str
    detected_patterns: list[str] = Field(default_factory=list)
    language: str


# Based on usage in intelligence_engine.py
class ErrorPattern(BaseModel):
    pattern_id: str
    template: str
    occurrences: int
    severity: str
    confidence: float
    first_occurrence_line: int
    last_occurrence_line: int
    related_chunks: list[int]


class CorrelationGroup(BaseModel):
    group_id: str
    error_pattern_ids: list[str]
    frequency: int
    time_window_minutes: int
    confidence: float
    description: str


class Anomaly(BaseModel):
    anomaly_id: str
    anomaly_type: str
    description: str
    confidence: float
    start_line: int
    end_line: int
    related_chunks: list[int]


class TimelineEvent(BaseModel):
    event_id: int
    timestamp: datetime | None
    event_type: str
    description: str
    line_number: int
    related_chunk_id: int
    causality_links: list[int] = Field(default_factory=list)


class SemanticCluster(BaseModel):
    """Represents a cluster of semantically similar chunks."""

    cluster_id: int
    label: str
    chunk_ids: list[int]
    coherence_score: float
    keywords: list[str]


class IntelligenceReport(BaseModel):
    report_version: str
    log_source: str
    total_lines_processed: int
    error_patterns: list[ErrorPattern] = Field(default_factory=list)
    correlations: list[CorrelationGroup] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    semantic_clusters: list[SemanticCluster] = Field(default_factory=list)
    plugin_analysis_results: dict[str, Any] = Field(default_factory=dict)


# Based on usage in log_chunker.py
class ChunkingResult(BaseModel):
    chunks: list[tuple[str, ChunkInfo]]
    intelligence_report: IntelligenceReport
    total_processing_time: float
    config_used: Any  # Should be ChunkingConfig, but avoid circular import
    preprocessing_stats: dict[str, Any]
    quality_metrics: dict[str, float]
    plugin_stats: dict[str, Any] = Field(default_factory=dict)


# Based on usage in adaptive_config.py
class ContentAnalysis(BaseModel):
    """Data model for content analysis results."""

    content_length: int
    avg_line_length: float
    detected_patterns: list[str]
    recommended_config: dict[str, Any]


# Intelligence engine class moved to data_models.py to avoid circular imports
