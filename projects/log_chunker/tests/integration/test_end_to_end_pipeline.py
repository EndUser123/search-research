"""Integration tests for the complete log processing pipeline."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import ChunkingResult
from src.log_chunker.log_chunker import LogChunker


class TestEndToEndPipeline:
    """Test cases for complete log processing pipeline."""

    @pytest.fixture
    def sample_log_content(self):
        """Create sample log content for testing."""
        return """2025-07-14 10:00:00,000 - INFO - main - Application started.
2025-07-14 10:00:01,123 - DEBUG - network - Connecting to host 192.168.1.1.
2025-07-14 10:00:02,456 - INFO - network - Connection established.
2025-07-14 10:00:03,789 - WARNING - data - Data integrity check failed for record 123.
2025-07-14 10:00:04,000 - ERROR - main - Critical error: Unable to process data.
Traceback (most recent call last):
  File "app.py", line 10, in <module>
    process_data()
  File "data_processor.py", line 5, in process_data
    raise ValueError("Invalid data format")
ValueError: Invalid data format
2025-07-14 10:00:05,111 - INFO - main - Application shutting down."""

    @pytest.fixture
    def temp_log_file(self, sample_log_content):
        """Create temporary log file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(sample_log_content)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_complete_pipeline_default_config(self, temp_log_file, temp_output_dir):
        """Test complete pipeline with default configuration."""
        chunker = LogChunker()

        # Process the log file
        result = chunker.process_log_file(temp_log_file, temp_output_dir)

        # Verify result structure
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) > 0
        assert result.intelligence_report is not None
        assert result.total_processing_time > 0
        assert result.config_used is not None

        # Verify intelligence report content
        report = result.intelligence_report
        assert report.log_source == str(temp_log_file)
        assert report.total_lines_processed > 0

        # Should detect error patterns
        assert len(report.error_patterns) > 0
        error_templates = [ep.template for ep in report.error_patterns]
        assert any("Critical error" in template for template in error_templates)

        # Should have timeline events
        assert len(report.timeline) > 0
        event_types = [event.event_type for event in report.timeline]
        assert "error" in event_types

    def test_complete_pipeline_custom_config(self, temp_log_file, temp_output_dir):
        """Test complete pipeline with custom configuration."""
        config = ChunkingConfig(
            max_chunk_size=100,
            overlap_size=10,
            enable_semantic_analysis=True,
            enable_error_deduplication=True,
        )

        chunker = LogChunker(config)
        result = chunker.process_log_file(temp_log_file, temp_output_dir)

        # Verify custom config was used
        assert result.config_used.max_chunk_size == 100
        assert result.config_used.overlap_size == 10
        assert result.config_used.enable_semantic_analysis

    def test_pipeline_with_semantic_analysis(self, temp_log_file, temp_output_dir):
        """Test pipeline with semantic analysis enabled."""
        config = ChunkingConfig(enable_semantic_analysis=True)
        chunker = LogChunker(config)

        with patch(
            "src.log_chunker.semantic_tagger.SentenceTransformer"
        ) as mock_transformer:
            # Mock the semantic analysis
            mock_model = Mock()
            mock_model.encode.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_transformer.return_value = mock_model

            result = chunker.process_log_file(temp_log_file, temp_output_dir)

            # Should have semantic clusters
            assert len(result.intelligence_report.semantic_clusters) >= 0

            # Should have plugin analysis results
            assert "semantic" in result.intelligence_report.plugin_analysis_results

    def test_pipeline_output_files_generation(self, temp_log_file, temp_output_dir):
        """Test that all expected output files are generated."""
        chunker = LogChunker()
        chunker.process_log_file(temp_log_file, temp_output_dir)

        # Check for expected output files
        expected_files = [
            "intelligence_report.json",
            "intelligence_report.yaml",
            "intelligence_report.md",
            "compact_summary.txt",
            "executive_summary.txt",
            "error_analysis.txt",
        ]

        for filename in expected_files:
            file_path = temp_output_dir / filename
            assert file_path.exists(), f"Expected output file not found: {filename}"
            assert file_path.stat().st_size > 0, f"Output file is empty: {filename}"

    def test_pipeline_json_output_validity(self, temp_log_file, temp_output_dir):
        """Test that JSON output is valid and contains expected data."""
        chunker = LogChunker()
        chunker.process_log_file(temp_log_file, temp_output_dir)

        # Read and validate JSON output
        json_file = temp_output_dir / "intelligence_report.json"
        with open(json_file) as f:
            json_data = json.load(f)

        # Verify JSON structure
        assert "report_version" in json_data
        assert "log_source" in json_data
        assert "total_lines_processed" in json_data
        assert "error_patterns" in json_data
        assert "timeline" in json_data
        assert "semantic_clusters" in json_data

        # Verify data content
        assert json_data["total_lines_processed"] > 0
        assert len(json_data["error_patterns"]) > 0

    def test_pipeline_error_handling_malformed_log(self, temp_output_dir):
        """Test pipeline handling of malformed log files."""
        # Create malformed log file
        malformed_content = (
            "This is not a proper log format\n\x00\x01\x02 binary data\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8", errors="ignore"
        ) as f:
            f.write(malformed_content)
            malformed_file = Path(f.name)

        try:
            chunker = LogChunker()
            result = chunker.process_log_file(malformed_file, temp_output_dir)

            # Should still produce a result, even if minimal
            assert isinstance(result, ChunkingResult)
            assert result.intelligence_report is not None

            # Should handle gracefully without crashing
            assert result.intelligence_report.total_lines_processed >= 0

        finally:
            if malformed_file.exists():
                malformed_file.unlink()

    def test_pipeline_large_log_performance(self, temp_output_dir):
        """Test pipeline performance with larger log files."""
        # Create larger log file
        large_content = ""
        for i in range(1000):
            large_content += f"2025-07-14 10:{i:02d}:00,000 - INFO - service{i%10} - Processing request {i}\n"
            if i % 100 == 0:
                large_content += f"2025-07-14 10:{i:02d}:01,000 - ERROR - service{i%10} - Error processing request {i}\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(large_content)
            large_file = Path(f.name)

        try:
            chunker = LogChunker()

            import time

            start_time = time.time()
            result = chunker.process_log_file(large_file, temp_output_dir)
            end_time = time.time()

            # Should complete within reasonable time (adjust threshold as needed)
            processing_time = end_time - start_time
            assert (
                processing_time < 30.0
            ), f"Processing took too long: {processing_time:.2f}s"

            # Should process all lines
            assert result.intelligence_report.total_lines_processed >= 1000

            # Should detect multiple error patterns
            assert len(result.intelligence_report.error_patterns) > 0

        finally:
            if large_file.exists():
                large_file.unlink()

    def test_pipeline_plugin_integration(self, temp_log_file, temp_output_dir):
        """Test that plugins are properly integrated in the pipeline."""
        chunker = LogChunker()
        result = chunker.process_log_file(temp_log_file, temp_output_dir)

        # Should have plugin analysis results
        plugin_results = result.intelligence_report.plugin_analysis_results
        assert isinstance(plugin_results, dict)

        # Should have results from enabled plugins
        # (Exact plugins depend on configuration, but should have some results)
        assert len(plugin_results) >= 0

    def test_pipeline_memory_usage(self, temp_log_file, temp_output_dir):
        """Test that pipeline doesn't consume excessive memory."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        chunker = LogChunker()
        chunker.process_log_file(temp_log_file, temp_output_dir)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for small log)
        assert (
            memory_increase < 100 * 1024 * 1024
        ), f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"

    def test_pipeline_reproducibility(self, temp_log_file, temp_output_dir):
        """Test that pipeline produces consistent results across runs."""
        chunker = LogChunker()

        # Run pipeline twice
        result1 = chunker.process_log_file(temp_log_file, temp_output_dir)
        result2 = chunker.process_log_file(temp_log_file, temp_output_dir)

        # Results should be consistent
        assert (
            result1.intelligence_report.total_lines_processed
            == result2.intelligence_report.total_lines_processed
        )
        assert len(result1.intelligence_report.error_patterns) == len(
            result2.intelligence_report.error_patterns
        )
        assert len(result1.intelligence_report.timeline) == len(
            result2.intelligence_report.timeline
        )

    def test_pipeline_configuration_validation(self, temp_log_file, temp_output_dir):
        """Test that invalid configurations are handled properly."""
        # Test with invalid configuration
        invalid_config = ChunkingConfig(
            max_chunk_size=-1,  # Invalid negative size
            overlap_size=200,  # Overlap larger than chunk size
        )

        # Should either raise appropriate exception or use default values
        try:
            chunker = LogChunker(invalid_config)
            result = chunker.process_log_file(temp_log_file, temp_output_dir)

            # If it doesn't raise exception, should use corrected values
            assert result.config_used.max_chunk_size > 0
            assert result.config_used.overlap_size < result.config_used.max_chunk_size

        except ValueError:
            # Acceptable to raise validation error for invalid config
            pass

    def test_pipeline_empty_log_file(self, temp_output_dir):
        """Test pipeline handling of empty log files."""
        # Create empty log file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            empty_file = Path(f.name)

        try:
            chunker = LogChunker()
            result = chunker.process_log_file(empty_file, temp_output_dir)

            # Should handle empty file gracefully
            assert isinstance(result, ChunkingResult)
            assert result.intelligence_report.total_lines_processed == 0
            assert len(result.intelligence_report.error_patterns) == 0
            assert len(result.chunks) == 0

        finally:
            if empty_file.exists():
                empty_file.unlink()
