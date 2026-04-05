from __future__ import annotations

"""Pydantic/dataclass compatibility layer with proper type annotations"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TypeAlias

from rich.console import Console

# Pydantic/dataclass compatibility layer
try:
    from pydantic import BaseModel
    from pydantic.v1 import Field as PydanticField  # Use v1-compatible Field
    HAS_PYDANTIC = True

    # Type-safe Field wrapper with proper generics
    def Field(
        default: Any = None,
        *,
        default_factory: Any = None,
        **kwargs: Any
    ) -> Any:
        if default_factory:
            return PydanticField(default_factory=default_factory, **kwargs)
        return PydanticField(default, **kwargs)

    FieldType: TypeAlias = PydanticField  # type: ignore[misc]

except ImportError:
    HAS_PYDANTIC = False

    # Fallback dataclass implementation with type checking
    def dataclass_wrapper(cls):  # type: ignore
        return dataclass(eq=False, frozen=True)(cls)

    BaseModel = dataclass_wrapper  # type: ignore[assignment,misc]

    def Field(
        default: Any = None,
        *,
        default_factory: Any = None,
        **kwargs: Any
    ) -> Any:  # type: ignore[no-redef]
        if default_factory:
            return field(default_factory=default_factory, **kwargs)
        return field(default=default, **kwargs)

    FieldType: TypeAlias = Any  # type: ignore[misc]

# Model class definitions within compatibility context
if HAS_PYDANTIC:
    # Pydantic model implementations
    class ChunkInfo(BaseModel):
        """Metadata for individual chunks."""
        chunk_id: int
        start_line: int
        end_line: int
        estimated_tokens: int
        method_used: str = Field(default="unknown")
        quality_score: float = Field(default=0.0)
        plugin_scores: Dict[str, float] = Field(default_factory=dict)
        boundary_type: Optional[str] = Field(default=None)

    class LogEntry(BaseModel):
        """Represents a parsed log entry with metadata."""
        line_number: Optional[int] = Field(default=None)
        timestamp: Optional[str] = Field(default=None)
        level: Optional[str] = Field(default=None)
        message: str = Field(...)
        original_line: str = Field(...)
        logger: Optional[str] = Field(default=None)
        pattern: str = Field(...)
        detected_patterns: List[str] = Field(default_factory=list)
        language: str = Field(default="unknown")

else:
    # Dataclass implementations
    @dataclass
    class ChunkInfo:
        """Metadata for individual chunks."""
        chunk_id: int
        start_line: int
        end_line: int
        estimated_tokens: int
        method_used: str = "unknown"
        quality_score: float = 0.0
        plugin_scores: Dict[str, float] = field(default_factory=dict)
        boundary_type: Optional[str] = None

    @dataclass
    class LogEntry:
        """Represents a parsed log entry with metadata."""
        line_number: Optional[int] = None
        timestamp: Optional[str] = None
        level: Optional[str] = None
        message: str
        original_line: str
        logger: Optional[str] = None
        pattern: str
100|         detected_patterns: List[str] = field(default_factory=list)
101|         language: str = "unknown"

    # Pydantic model implementations
    class ErrorPattern(BaseModel):
        pattern_id: str
        template: str
        occurrences: int
        severity: str
        confidence: float
        first_occurrence_line: int
        last_occurrence_line: int
        related_chunks: List[int] = Field(default_factory=list)

    class CorrelationGroup(BaseModel):
        group_id: str
        error_pattern_ids: List[str] = Field(default_factory=list)
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
        related_chunks: List[int] = Field(default_factory=list)

    class TimelineEvent(BaseModel):
        event_id: int
        timestamp: Optional[datetime] = Field(default=None)
        event_type: str
        description: str
        line_number: int
        related_chunk_id: int
        causality_links: List[int] = Field(default_factory=list)

    class SemanticCluster(BaseModel):
        """Represents a cluster of semantically similar chunks."""
        cluster_id: int
        label: str
        chunk_ids: List[int] = Field(default_factory=list)
        coherence_score: float
        keywords: List[str] = Field(default_factory=list)

    class IntelligenceReport(BaseModel):
        report_version: str
        log_source: str
        total_lines_processed: int
        error_patterns: List[ErrorPattern] = Field(default_factory=list)
        correlations: List[CorrelationGroup] = Field(default_factory=list)
        anomalies: List[Anomaly] = Field(default_factory=list)
        timeline: List[TimelineEvent] = Field(default_factory=list)
        semantic_clusters: List[SemanticCluster] = Field(default_factory=list)
        plugin_analysis_results: Dict[str, Any] = Field(default_factory=dict)

    class ChunkingResult(BaseModel):
        chunks: List[Tuple[str, ChunkInfo]]
        intelligence_report: IntelligenceReport
        total_processing_time: float
        config_used: Any  # Should be ChunkingConfig, but avoid circular import
        preprocessing_stats: Dict[str, Any]
        quality_metrics: Dict[str, float]
        plugin_stats: Dict[str, Any] = Field(default_factory=dict)

    class ContentAnalysis(BaseModel):
        """Data model for content analysis results."""
        content_length: int
        avg_line_length: float
        detected_patterns: List[str] = Field(default_factory=list)
        recommended_config: Dict[str, Any]

else:
    # Dataclass implementations
    @dataclass
    class ErrorPattern:
        pattern_id: str
        template: str
        occurrences: int
        severity: str
        confidence: float
        first_occurrence_line: int
        last_occurrence_line: int
        related_chunks: List[int] = field(default_factory=list)

    @dataclass
    class CorrelationGroup:
        group_id: str
        error_pattern_ids: List[str] = field(default_factory=list)
        frequency: int
        time_window_minutes: int
        confidence: float
        description: str

    @dataclass
    class Anomaly:
        anomaly_id: str
        anomaly_type: str
        description: str
        confidence: float
        start_line: int
        end_line: int
        related_chunks: List[int] = field(default_factory=list)

    @dataclass
    class TimelineEvent:
        event_id: int
        event_type: str
        description: str
        line_number: int
        related_chunk_id: int
        timestamp: Optional[datetime] = None
        causality_links: List[int] = field(default_factory=list)

    @dataclass
    class SemanticCluster:
        """Represents a cluster of semantically similar chunks."""
        cluster_id: int
        label: str
        chunk_ids: List[int] = field(default_factory=list)
        coherence_score: float
        keywords: List[str] = field(default_factory=list)

    @dataclass
    class IntelligenceReport:
        report_version: str
        log_source: str
        total_lines_processed: int
        error_patterns: List[ErrorPattern] = field(default_factory=list)
        correlations: List[CorrelationGroup] = field(default_factory=list)
        anomalies: List[Anomaly] = field(default_factory=list)
        timeline: List[TimelineEvent] = field(default_factory=list)
        semantic_clusters: List[SemanticCluster] = field(default_factory=list)
        plugin_analysis_results: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class ChunkingResult:
        chunks: List[Tuple[str, ChunkInfo]]
        intelligence_report: IntelligenceReport
        total_processing_time: float
        config_used: Any
        preprocessing_stats: Dict[str, Any]
        quality_metrics: Dict[str, float]
        plugin_stats: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class ContentAnalysis:
        """Data model for content analysis results."""
        content_length: int
        avg_line_length: float
        detected_patterns: List[str] = field(default_factory=list)
        recommended_config: Dict[str, Any]


class IntelligenceEngine:
    """Core analysis engine for processing log chunks and generating intelligence reports."""

    def __init__(self, config: ChunkingConfig, console: Console):
        """Initialize the intelligence engine."""
        self.config = config
        self.console = console
        self.plugin_analysis_results: Dict[str, Any] = {}

    def set_plugin_analysis(self, plugin_analysis_results: Dict[str, Any]) -> None:
        """Set plugin analysis results for use in intelligence analysis."""
        self.plugin_analysis_results = plugin_analysis_results or {}

    def analyze(self, chunks: List[Tuple[str, ChunkInfo]], preprocessing_stats: Dict[str, Any], input_file: str) -> IntelligenceReport:
        """Perform comprehensive analysis of log chunks and return intelligence report."""

        # Extract all text content from chunks
        all_text = "\n".join([chunk_text for chunk_text, _ in chunks])
        total_lines = len(all_text.split('\n'))

        # Initialize empty analysis results
        error_patterns = self._detect_error_patterns(all_text, chunks)
        correlations = self._detect_correlations(error_patterns)
        anomalies = self._detect_anomalies(all_text, chunks)
        timeline = self._build_timeline(all_text, chunks)
        semantic_clusters = self._cluster_semantically(chunks)

        # Create intelligence report
        report = IntelligenceReport(
            report_version="1.0",
            log_source=input_file,
            total_lines_processed=total_lines,
            error_patterns=error_patterns,
            correlations=correlations,
            anomalies=anomalies,
            timeline=timeline,
            semantic_clusters=semantic_clusters,
            plugin_analysis_results=self.plugin_analysis_results
        )

        return report

    def _detect_error_patterns(self, text: str, chunks: List[Tuple[str, ChunkInfo]]) -> List[ErrorPattern]:
        """Detect and classify error patterns in the log data."""
        patterns = []

        # Common error pattern regexes
        error_regexes = [
            (r'ERROR.*?([\w\.]+Exception[^:\n]*)', 'exception', 'high'),
            (r'FATAL.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'fatal', 'critical'),
            (r'WARNING.*?(timeout|failed|error)', 'warning', 'medium'),
            (r'(\d{4}-\d{2}-\d{2}.*?ERROR.*?)(?=\n|$)', 'timestamped_error', 'high'),
        ]

        for i, (pattern, error_type, severity) in enumerate(error_regexes):
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            if matches:
                # Find related chunks
                related_chunks = []
                for chunk_text, chunk_info in chunks:
                    if re.search(pattern, chunk_text, re.IGNORECASE):
                        related_chunks.append(chunk_info.chunk_id)

                # Get line numbers
                lines = text.split('\n')
                first_line = last_line = 0
                for match in matches:
                    line_num = text[:match.start()].count('\n') + 1
                    if first_line == 0:
                        first_line = line_num
                    last_line = max(last_line, line_num)

                patterns.append(ErrorPattern(
                    pattern_id=f"error_pattern_{i}_{error_type}",
                    template=pattern,
                    occurrences=len(matches),
                    severity=severity,
                    confidence=min(0.9, 0.5 + (len(matches) / 10)),
                    first_occurrence_line=first_line,
                    last_occurrence_line=last_line,
                    related_chunks=related_chunks
                ))

        return patterns

    def _detect_correlations(self, error_patterns: List[ErrorPattern]) -> List[CorrelationGroup]:
        """Detect correlations between error patterns."""
        correlations = []

        # Simple correlation: if patterns appear in same chunks
        for i, pattern1 in enumerate(error_patterns):
            for j, pattern2 in enumerate(error_patterns[i+1:], i+1):
                common_chunks = set(pattern1.related_chunks) & set(pattern2.related_chunks)
                if len(common_chunks) > 0:
                    correlations.append(CorrelationGroup(
                        group_id=f"correlation_{i}_{j}",
                        error_pattern_ids=[pattern1.pattern_id, pattern2.pattern_id],
                        frequency=len(common_chunks),
                        time_window_minutes=60,  # Default window
                        confidence=min(0.8, len(common_chunks) / max(len(pattern1.related_chunks), len(pattern2.related_chunks))),
                        description=f"Patterns {pattern1.pattern_id} and {pattern2.pattern_id} co-occur in {len(common_chunks)} chunks"
                    ))

        return correlations

    def _detect_anomalies(self, text: str, chunks: List[Tuple[str, ChunkInfo]]) -> List[Anomaly]:
        """Detect anomalous patterns in the log data."""
        anomalies = []

        # Detect unusual frequency of errors
        lines = text.split('\n')
        error_lines = [i for i, line in enumerate(lines) if re.search(r'error|exception|failed', line, re.IGNORECASE)]

        if len(error_lines) > len(lines) * 0.1:  # More than 10% error lines
            anomalies.append(Anomaly(
                anomaly_id="high_error_rate",
                anomaly_type="frequency",
                description=f"High error rate detected: {len(error_lines)}/{len(lines)} lines contain errors",
                confidence=0.8,
                start_line=min(error_lines) if error_lines else 0,
                end_line=max(error_lines) if error_lines else 0,
                related_chunks=[chunk_info.chunk_id for _, chunk_info in chunks]
            ))

        return anomalies

    def _build_timeline(self, text: str, chunks: List[Tuple[str, ChunkInfo]]) -> List[TimelineEvent]:
        """Build a timeline of events from the log data."""
        timeline = []

        # Extract timestamped events
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})'
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            timestamp_match = re.search(timestamp_pattern, line)
            if timestamp_match:
                try:
                    timestamp_str = timestamp_match.group(1)
                    # Try parsing common timestamp formats
                    timestamp = None
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            timestamp = datetime.strptime(timestamp_str, fmt)
                            break
                        except ValueError:
                            continue

                    # Determine event type
                    event_type = "info"
                    if re.search(r'error|exception|failed', line, re.IGNORECASE):
                        event_type = "error"
                    elif re.search(r'warning|warn', line, re.IGNORECASE):
                        event_type = "warning"
                    elif re.search(r'start|begin|init', line, re.IGNORECASE):
                        event_type = "start"
                    elif re.search(r'stop|end|finish', line, re.IGNORECASE):
                        event_type = "stop"

                    # Find related chunk
                    related_chunk_id = 0
                    for chunk_text, chunk_info in chunks:
                        if chunk_info.start_line <= line_num <= chunk_info.end_line:
                            related_chunk_id = chunk_info.chunk_id
                            break

                    timeline.append(TimelineEvent(
                        event_id=len(timeline),
                        timestamp=timestamp,
                        event_type=event_type,
                        description=line.strip()[:100],  # Truncate long lines
                        line_number=line_num + 1,
                        related_chunk_id=related_chunk_id
                    ))
                except Exception:
                    # Skip invalid timestamps
                    continue

        return sorted(timeline, key=lambda x: x.timestamp or datetime.min)

    def _cluster_semantically(self, chunks: List[Tuple[str, ChunkInfo]]) -> List[SemanticCluster]:
        """Cluster chunks based on semantic similarity."""
        clusters = []

        # Simple keyword-based clustering
        keywords_clusters = {}

        for chunk_text, chunk_info in chunks:
            # Extract important keywords
            words = re.findall(r'\b[a-zA-Z]{4,}\b', chunk_text.lower())
            important_words = [w for w in words if w not in ['this', 'that', 'with', 'from', 'they', 'have', 'will', 'been', 'were']]

            # Find most common words as cluster key
            word_counts = {}
            for word in important_words:
                word_counts[word] = word_counts.get(word, 0) + 1

            if word_counts:
                top_word = max(word_counts.items(), key=lambda x: x[1])[0]
                if top_word not in keywords_clusters:
                    keywords_clusters[top_word] = []
                keywords_clusters[top_word].append(chunk_info.chunk_id)

        # Convert to semantic clusters
        for i, (keyword, chunk_ids) in enumerate(keywords_clusters.items()):
            if len(chunk_ids) > 1:  # Only clusters with multiple chunks
                clusters.append(SemanticCluster(
                    cluster_id=i,
                    label=f"Cluster_{keyword}",
                    chunk_ids=chunk_ids,
                    coherence_score=min(0.9, len(chunk_ids) / len(chunks)),
                    keywords=[keyword]
                ))

        return clusters
