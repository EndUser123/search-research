import pytest
from config import ChunkingConfig
from data_models import (
    Anomaly,
    ChunkInfo,
    ChunkingResult,
    CorrelationGroup,
    ErrorPattern,
    IntelligenceReport,
    LogEntry,
    SemanticCluster,
    TimelineEvent,
)


def test_can_instantiate_data_models():
    """Smoke test to ensure all data models can be instantiated."""
    try:
        LogEntry(
            timestamp=None,
            level="INFO",
            message="test",
            original_line="test",
            line_number=1,
        )
        ChunkInfo(chunk_id=1, start_line=1, end_line=1, estimated_tokens=1)
        ErrorPattern(
            pattern_id="1",
            template="test",
            occurrences=1,
            severity="high",
            confidence=1.0,
            first_occurrence_line=1,
            last_occurrence_line=1,
        )
        CorrelationGroup(
            group_id="1",
            error_pattern_ids=["1"],
            frequency=1,
            time_window_minutes=1,
            confidence=1.0,
            description="test",
        )
        Anomaly(
            anomaly_id="1",
            anomaly_type="test",
            description="test",
            confidence=1.0,
            start_line=1,
            end_line=1,
        )
        TimelineEvent(
            event_id=1,
            timestamp=None,
            event_type="test",
            description="test",
            line_number=1,
            related_chunk_id=1,
        )
        SemanticCluster(cluster_id=1, label="test", chunk_ids=[1], coherence_score=1.0)
        intelligence_report = IntelligenceReport()
        chunking_config = ChunkingConfig()
        ChunkingResult(
            chunks=[],
            intelligence_report=intelligence_report,
            total_processing_time=1.0,
            config_used=chunking_config,
        )
    except Exception as e:
        pytest.fail(f"Failed to instantiate data models: {e}")
