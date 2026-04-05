"""Tests for dreaming_writer module (T-007).

Tests verify:
1. JSON file is valid and parseable
2. Markdown file generated if configured
3. Writes are atomic (no partial writes)

Run with: pytest P:/.claude/hooks/tests/test_dreaming_writer.py -v
"""
import json

# Import module under test
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from dreaming_insights import DreamingInsights, Pattern, PrincipleStats
from dreaming_writer import write_insights


class TestDreamingWriterBasicFunctionality:
    """Tests for basic write_insights functionality."""

    @pytest.fixture
    def sample_insights(self):
        """Create sample insights for testing."""
        return DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[
                PrincipleStats(
                    principle="context_awareness",
                    count=10,
                    first_seen="2025-03-01T00:00:00",
                    last_seen="2025-03-07T12:00:00"
                )
            ],
            patterns=[
                Pattern(
                    pattern_type="vague_directive",
                    description="User provided unclear requirements",
                    examples=["Add optimization", "Improve performance"]
                )
            ],
            recommendations=[
                "Add more specific requirements",
                "Use concrete metrics"
            ]
        )

    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            yield state_dir

    def test_write_insights_creates_json_file(self, sample_insights, temp_state_dir):
        """Test that write_insights creates a valid JSON file."""
        # Arrange
        config = {
            "json_output_path": str(temp_state_dir / "dreaming-insights.json"),
            "enable_markdown": False
        }

        # Act
        write_insights(sample_insights, config)

        # Assert
        json_path = temp_state_dir / "dreaming-insights.json"
        assert json_path.exists(), "JSON file should be created"

        # Verify JSON is valid
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["generated_at"] == "2025-03-07T12:00:00"
        assert data["total_events"] == 100
        assert len(data["principle_stats"]) == 1

    def test_write_insights_creates_markdown_when_enabled(self, sample_insights, temp_state_dir):
        """Test that write_insights creates markdown file when enable_markdown=True."""
        # Arrange
        config = {
            "json_output_path": str(temp_state_dir / "dreaming-insights.json"),
            "markdown_output_path": str(temp_state_dir / "dreaming-insights.md"),
            "enable_markdown": True
        }

        # Act
        write_insights(sample_insights, config)

        # Assert
        md_path = temp_state_dir / "dreaming-insights.md"
        assert md_path.exists(), "Markdown file should be created when enabled"

        # Verify markdown content
        content = md_path.read_text(encoding="utf-8")
        assert "# Dreaming Insights" in content
        assert "## Principle Statistics" in content
        assert "## Detected Patterns" in content
        assert "## Recommendations" in content

    def test_write_insights_skips_markdown_when_disabled(self, sample_insights, temp_state_dir):
        """Test that markdown file is NOT created when enable_markdown=False."""
        # Arrange
        config = {
            "json_output_path": str(temp_state_dir / "dreaming-insights.json"),
            "markdown_output_path": str(temp_state_dir / "dreaming-insights.md"),
            "enable_markdown": False
        }

        # Act
        write_insights(sample_insights, config)

        # Assert
        md_path = temp_state_dir / "dreaming-insights.md"
        assert not md_path.exists(), "Markdown file should NOT be created when disabled"

    def test_write_insights_uses_atomic_writes(self, sample_insights, temp_state_dir):
        """Test that write_insights uses atomic write pattern (tmp + replace)."""
        # Arrange
        config = {
            "json_output_path": str(temp_state_dir / "dreaming-insights.json"),
            "enable_markdown": False
        }

        # Track file operations to verify atomic pattern
        write_calls = []
        original_write_text = Path.write_text

        def mock_write_text(self, content, encoding=None):
            write_calls.append({
                "path": str(self),
                "content": content[:100]  # Just log first 100 chars
            })
            return original_write_text(self, content, encoding=encoding or "utf-8")

        replace_calls = []
        original_replace = Path.replace

        def mock_replace(self, target):
            replace_calls.append({
                "source": str(self),
                "target": str(target)
            })
            return original_replace(self, target)

        # Act
        with patch.object(Path, "write_text", mock_write_text):
            with patch.object(Path, "replace", mock_replace):
                write_insights(sample_insights, config)

        # Assert - Verify atomic pattern: write to .tmp, then replace
        assert len(write_calls) >= 1, "Should write to temp file"

        # Check that temp file was used
        temp_writes = [c for c in write_calls if c["path"].endswith(".tmp")]
        assert len(temp_writes) >= 1, "Should write to .tmp file first"

        # Check that replace was called
        assert len(replace_calls) >= 1, "Should call replace() for atomic update"

        # Verify final file exists and is valid
        json_path = temp_state_dir / "dreaming-insights.json"
        assert json_path.exists(), "Final file should exist"
        with open(json_path, encoding="utf-8") as f:
            json.load(f)  # Should not raise

    def test_write_insights_handles_missing_config_gracefully(self, sample_insights, temp_state_dir):
        """Test that write_insights uses defaults when config keys are missing."""
        # Arrange - Config with missing optional keys
        config = {
            "json_output_path": str(temp_state_dir / "custom-insights.json"),
            # Missing: enable_markdown, markdown_output_path
        }

        # Act
        write_insights(sample_insights, config)

        # Assert - Should use custom path for JSON
        json_path = temp_state_dir / "custom-insights.json"
        assert json_path.exists(), "Should use custom JSON path from config"

        # Should NOT create markdown (disabled by default)
        md_path = temp_state_dir / "dreaming-insights.md"
        assert not md_path.exists(), "Should not create markdown when not configured"

    def test_write_insights_json_content_matches_insights(self, sample_insights, temp_state_dir):
        """Test that JSON file content exactly matches the insights data."""
        # Arrange
        config = {
            "json_output_path": str(temp_state_dir / "dreaming-insights.json"),
            "enable_markdown": False
        }

        # Act
        write_insights(sample_insights, config)

        # Assert
        json_path = temp_state_dir / "dreaming-insights.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Verify all fields match
        assert data["generated_at"] == sample_insights.generated_at
        assert data["total_events"] == sample_insights.total_events
        assert len(data["principle_stats"]) == len(sample_insights.principle_stats)
        assert len(data["patterns"]) == len(sample_insights.patterns)
        assert len(data["recommendations"]) == len(sample_insights.recommendations)

        # Verify nested objects
        assert data["principle_stats"][0]["principle"] == "context_awareness"
        assert data["patterns"][0]["pattern_type"] == "vague_directive"
        assert data["patterns"][0]["examples"] == ["Add optimization", "Improve performance"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
