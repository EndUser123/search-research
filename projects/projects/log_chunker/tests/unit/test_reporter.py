"""Unit tests for reporter module - CORRECTED VERSION."""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from rich.console import Console
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import (
    Anomaly,
    ChunkInfo,
    ChunkingResult,
    CorrelationGroup,
    ErrorPattern,
    IntelligenceReport,
    SemanticCluster,
    TimelineEvent,
)
from src.log_chunker.reporter import Reporter


class TestReporter:
    """Test cases for Reporter class."""

    @pytest.fixture
    def sample_intelligence_report(self):
        """Create a sample intelligence report for testing."""
        return IntelligenceReport(
            report_version="1.0",
            log_source="test.log",
            total_lines_processed=100,
            error_patterns=[
                ErrorPattern(
                    pattern_id="error_001",
                    template="Database connection failed",
                    occurrences=5,
                    severity="critical",
                    confidence=0.95,
                    first_occurrence_line=10,
                    last_occurrence_line=50,
                )
            ],
            correlations=[
                CorrelationGroup(
                    group_id="corr_001",
                    error_pattern_ids=["error_001"],
                    frequency=3,
                    time_window_minutes=5,
                    confidence=0.8,
                    description="Database errors during peak hours",
                )
            ],
            anomalies=[
                Anomaly(
                    anomaly_id="anom_001",
                    anomaly_type="frequency_burst",
                    description="Unusual spike in error frequency",
                    confidence=0.85,
                    start_line=45,
                    end_line=55,
                )
            ],
            timeline=[
                TimelineEvent(
                    event_id=1,
                    timestamp=None,
                    event_type="error",
                    description="First database error",
                    line_number=10,
                    related_chunk_id=0,
                )
            ],
            semantic_clusters=[
                SemanticCluster(
                    cluster_id=0,
                    label="Database Operations",
                    chunk_ids=[0, 1],
                    coherence_score=0.85,
                    keywords=["database", "connection", "query"],
                )
            ],
            plugin_analysis_results={
                "security_analysis": {"security_events": 2, "risk_level": "medium"}
            },
        )

    @pytest.fixture
    def sample_config(self):
        """Create sample config."""
        return ChunkingConfig(target_tokens=1000, enabled_plugins=["semantic"])

    @pytest.fixture
    def sample_chunking_result(self, sample_intelligence_report, sample_config):
        """Create sample chunking result."""
        chunks = [
            ("First chunk content", ChunkInfo(0, 0, 10, 50, quality_score=0.8)),
            ("Second chunk content", ChunkInfo(1, 11, 20, 45, quality_score=0.7)),
        ]

        return ChunkingResult(
            chunks=chunks,
            intelligence_report=sample_intelligence_report,
            total_processing_time=1.5,
            config_used=sample_config,
            preprocessing_stats={
                "original_lines": 100,
                "processed_lines": 95,
                "unique_patterns": 10,
                "unique_loggers": 5,
                "processing_time": 1.23,
            },
            quality_metrics={"avg_chunk_size": 47.5},
            plugin_stats={
                "semantic": {
                    "status": "success",
                    "boundaries_found": 10,
                    "avg_chunk_score": 0.75,
                }
            },
        )

    def test_init_default_console(self):
        """Test Reporter initialization with default console."""
        reporter = Reporter()
        assert reporter.console is not None
        assert isinstance(reporter.console, Console)

    def test_init_custom_console(self):
        """Test Reporter initialization with custom console."""
        mock_console = Mock(spec=Console)
        reporter = Reporter(mock_console)
        assert reporter.console == mock_console

    def test_generate_yaml_frontmatter(self, sample_intelligence_report, sample_config):
        """Test YAML frontmatter generation."""
        reporter = Reporter()
        frontmatter = reporter._generate_yaml_frontmatter(
            sample_intelligence_report, sample_config, "test_report"
        )

        assert "---" in frontmatter
        assert "report_type: test_report" in frontmatter
        assert "report_version: '1.0'" in frontmatter
        assert "log_source: test.log" in frontmatter
        assert "total_lines: 100" in frontmatter

    def test_generate_markdown_report(self, sample_chunking_result):
        """Test Markdown report generation."""
        reporter = Reporter()
        markdown_content = reporter._generate_markdown_report(
            sample_chunking_result, "test_base"
        )

        assert "# Chunking Report: test_base" in markdown_content
        assert "Total Chunks" in markdown_content
        assert "Processing Time" in markdown_content
        assert "Plugin Performance" in markdown_content

    @patch("builtins.open", new_callable=mock_open)
    def test_create_summary_report(
        self, mock_file, sample_intelligence_report, sample_config
    ):
        """Test summary report creation."""
        reporter = Reporter()
        chunks = [("Test chunk content", ChunkInfo(0, 0, 10, 50, quality_score=0.8))]

        output_dir = Path("test_output")

        result_path = reporter._create_summary_report(
            sample_intelligence_report,
            chunks,
            output_dir,
            "test_base",
            1000,
            sample_config,
        )

        assert result_path.name == "test_base_llm_summary.md"
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_create_error_only_report(
        self, mock_file, sample_intelligence_report, sample_config
    ):
        """Test error-only report creation."""
        reporter = Reporter()
        chunks = [("Error chunk content", ChunkInfo(0, 0, 10, 50, quality_score=0.8))]

        # Add chunk ID to error pattern so it gets selected
        sample_intelligence_report.error_patterns[0].related_chunks = [0]

        output_dir = Path("test_output")

        result_path = reporter._create_error_only_report(
            sample_intelligence_report,
            chunks,
            output_dir,
            "test_base",
            1000,
            sample_config,
        )

        assert result_path.name == "test_base_llm_errors_only.md"
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_create_ultra_compact_report(
        self, mock_file, sample_intelligence_report, sample_config
    ):
        """Test ultra-compact report creation."""
        reporter = Reporter()
        chunks = [("Compact chunk content", ChunkInfo(0, 0, 10, 50, quality_score=0.8))]

        # Add chunk ID to error pattern so it gets selected
        sample_intelligence_report.error_patterns[0].related_chunks = [0]

        output_dir = Path("test_output")

        result_path = reporter._create_ultra_compact_report(
            sample_intelligence_report,
            chunks,
            output_dir,
            "test_base",
            1000,
            sample_config,
        )

        assert result_path.name == "test_base_llm_ultra.md"
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_create_standard_report(
        self, mock_file, sample_intelligence_report, sample_config
    ):
        """Test standard report creation."""
        reporter = Reporter()
        chunks = [
            ("Standard chunk content", ChunkInfo(0, 0, 10, 50, quality_score=0.8))
        ]

        output_dir = Path("test_output")

        result_path = reporter._create_standard_report(
            sample_intelligence_report,
            chunks,
            output_dir,
            "test_base",
            1000,
            sample_config,
        )

        assert result_path.name == "test_base_llm_optimized.md"
        mock_file.assert_called()

    def test_display_chunking_results(self, sample_chunking_result):
        """Test chunking results display."""
        mock_console = Mock(spec=Console)
        reporter = Reporter(mock_console)

        # Should not raise exception
        reporter.display_chunking_results(sample_chunking_result)

        # Verify console was used for output
        assert mock_console.print.called

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_save_detailed_report(self, mock_mkdir, mock_file, sample_chunking_result):
        """Test detailed report saving."""
        mock_console = Mock(spec=Console)
        reporter = Reporter(mock_console)

        chunks_dir = Path("chunks")
        reports_dir = Path("reports")

        # Should not raise exception
        reporter.save_detailed_report(
            sample_chunking_result, chunks_dir, reports_dir, "test_base"
        )

        # Verify files were written
        assert mock_file.called
        # Verify console output
        assert mock_console.print.called

    def test_empty_report_handling(self, sample_config):
        """Test handling of empty intelligence report."""
        empty_report = IntelligenceReport()
        reporter = Reporter()

        # Should not raise exceptions
        frontmatter = reporter._generate_yaml_frontmatter(
            empty_report, sample_config, "test"
        )
        assert "---" in frontmatter

        # Test with empty chunks
        chunks = []
        output_dir = Path("test_output")

        with patch("builtins.open", mock_open()):
            result_path = reporter._create_summary_report(
                empty_report, chunks, output_dir, "test_base", 1000, sample_config
            )
            assert result_path.name == "test_base_llm_summary.md"
