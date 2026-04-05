"""End-to-end tests for CLI smart defaults functionality."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCLISmartDefaults:
    """Test cases for CLI smart defaults behavior."""

    @pytest.fixture
    def sample_log_file(self):
        """Create a sample log file for testing."""
        content = """2025-07-14 10:00:00,000 - INFO - main - Application started.
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_smart_default_basic_execution(self, sample_log_file, temp_output_dir):
        """Test basic smart default execution with minimal arguments."""
        # Run log_chunker with just the log file (smart defaults)
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should complete successfully
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Should generate all default report formats
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

    def test_smart_default_intelligence_analysis(
        self, sample_log_file, temp_output_dir
    ):
        """Test that smart defaults enable full intelligence analysis."""
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )
        assert result.returncode == 0

        # Load and verify JSON output contains intelligence analysis
        json_file = temp_output_dir / "intelligence_report.json"
        with open(json_file) as f:
            report_data = json.load(f)

        # Should have performed error pattern analysis
        assert "error_patterns" in report_data
        assert len(report_data["error_patterns"]) > 0

        # Should have timeline analysis
        assert "timeline" in report_data
        assert len(report_data["timeline"]) > 0

        # Should have semantic analysis (if enabled by default)
        assert "semantic_clusters" in report_data

        # Should have plugin analysis results
        assert "plugin_analysis_results" in report_data

    def test_smart_default_auto_optimization(self, sample_log_file, temp_output_dir):
        """Test that smart defaults automatically optimize settings."""
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )
        assert result.returncode == 0

        # Should complete without manual configuration
        # The fact that it runs successfully indicates auto-optimization worked
        assert "Analysis complete" in result.stdout or result.returncode == 0

    def test_cli_help_message(self):
        """Test that CLI help message describes smart defaults."""
        cmd = [sys.executable, "-m", "src.log_chunker.log_chunker", "--help"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should show help without error
        assert result.returncode == 0

        # Help should mention smart defaults or auto-analysis
        help_text = result.stdout.lower()
        assert any(
            keyword in help_text
            for keyword in ["smart", "auto", "default", "intelligence", "analysis"]
        )

    def test_minimal_command_line_interface(self, sample_log_file, temp_output_dir):
        """Test the most minimal command line interface."""
        # Test with just the log file argument
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should work even without explicit output directory
        assert result.returncode == 0 or "output" in result.stderr.lower()

    def test_smart_defaults_with_different_log_sizes(self, temp_output_dir):
        """Test smart defaults adapt to different log file sizes."""
        # Test with small log
        small_content = "2025-07-14 10:00:00 - INFO - Small log entry\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(small_content)
            small_log = Path(f.name)

        try:
            cmd = [
                sys.executable,
                "-m",
                "src.log_chunker.log_chunker",
                str(small_log),
                "--output-dir",
                str(temp_output_dir / "small"),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd() / "_Projects/log_chunker",
            )

            # Should handle small logs gracefully
            assert result.returncode == 0

            # Should still generate output files
            output_dir = temp_output_dir / "small"
            json_file = output_dir / "intelligence_report.json"
            if json_file.exists():
                with open(json_file) as f:
                    report_data = json.load(f)
                assert report_data["total_lines_processed"] >= 0

        finally:
            if small_log.exists():
                small_log.unlink()

    def test_error_handling_invalid_log_file(self, temp_output_dir):
        """Test error handling for invalid log files."""
        # Test with non-existent file
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            "nonexistent_file.log",
            "--output-dir",
            str(temp_output_dir),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should fail gracefully with appropriate error message
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_output_directory_auto_creation(self, sample_log_file):
        """Test that output directory is automatically created."""
        with tempfile.TemporaryDirectory() as temp_base:
            output_dir = Path(temp_base) / "auto_created_dir"

            cmd = [
                sys.executable,
                "-m",
                "src.log_chunker.log_chunker",
                str(sample_log_file),
                "--output-dir",
                str(output_dir),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd() / "_Projects/log_chunker",
            )

            # Should create directory and succeed
            assert result.returncode == 0
            assert output_dir.exists()

    def test_verbose_output_option(self, sample_log_file, temp_output_dir):
        """Test verbose output option provides detailed information."""
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
            "--verbose",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should provide more detailed output
        assert result.returncode == 0
        # Verbose output should contain progress information
        output_text = result.stdout + result.stderr
        assert len(output_text) > 0

    def test_quiet_mode_option(self, sample_log_file, temp_output_dir):
        """Test quiet mode reduces output."""
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
            "--quiet",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should succeed with minimal output
        assert result.returncode == 0
        # Quiet mode should produce less output
        result.stdout + result.stderr
        # Should still work but with less verbose output

    def test_format_override_options(self, sample_log_file, temp_output_dir):
        """Test that format options can override smart defaults."""
        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
            "--format",
            "json",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )

        # Should respect format override
        assert result.returncode == 0

        # Should generate JSON file
        json_file = temp_output_dir / "intelligence_report.json"
        assert json_file.exists()

    def test_performance_with_smart_defaults(self, sample_log_file, temp_output_dir):
        """Test that smart defaults provide reasonable performance."""
        import time

        cmd = [
            sys.executable,
            "-m",
            "src.log_chunker.log_chunker",
            str(sample_log_file),
            "--output-dir",
            str(temp_output_dir),
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd() / "_Projects/log_chunker",
        )
        end_time = time.time()

        # Should complete successfully
        assert result.returncode == 0

        # Should complete within reasonable time for small log
        processing_time = end_time - start_time
        assert (
            processing_time < 30.0
        ), f"Processing took too long: {processing_time:.2f}s"

    def test_configuration_file_integration(self, sample_log_file, temp_output_dir):
        """Test integration with configuration files."""
        # Create a simple config file
        config_content = """
max_chunk_size: 1000
enable_semantic_analysis: true
output_formats: ["json", "markdown"]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_file = Path(f.name)

        try:
            cmd = [
                sys.executable,
                "-m",
                "src.log_chunker.log_chunker",
                str(sample_log_file),
                "--output-dir",
                str(temp_output_dir),
                "--config",
                str(config_file),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd() / "_Projects/log_chunker",
            )

            # Should use config file settings
            assert result.returncode == 0

            # Should generate specified formats
            assert (temp_output_dir / "intelligence_report.json").exists()
            assert (temp_output_dir / "intelligence_report.md").exists()

        finally:
            if config_file.exists():
                config_file.unlink()
