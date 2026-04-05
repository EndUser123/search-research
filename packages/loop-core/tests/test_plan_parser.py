"""Tests for plan parsing utilities."""


import pytest

from scripts.plan_parser import (
    PlanParseError,
    detect_incomplete_tasks,
    extract_task_metadata,
    parse_plan_tasks,
)


class TestParsePlanTasks:
    """Test suite for parse_plan_tasks function."""

    @pytest.fixture
    def sample_plan(self, tmp_path):
        """Create sample plan file with tasks."""
        plan_file = tmp_path / "plan.md"
        plan_content = """
# Implementation Plan

## Tasks

- [ ] TASK-001 First task [tag:important]
- [x] TASK-002 Completed task
- [ ] Third task after:TASK-001

## Additional Tasks

- [ ] Fourth task [tag:bug] after:TASK-002
- [x] TASK-005 Another completed task

## More Tasks

- [ ] Task with multiline
  description
"""
        plan_file.write_text(plan_content)
        return plan_file

    def test_parse_plan_tasks_extracts_all_tasks(self, sample_plan):
        """Test that all tasks are extracted from plan file."""
        tasks = parse_plan_tasks(sample_plan)
        assert len(tasks) == 6

    def test_parse_plan_tasks_task_ids(self, sample_plan):
        """Test that task IDs are auto-generated correctly."""
        tasks = parse_plan_tasks(sample_plan)
        task_ids = [task["id"] for task in tasks]
        assert task_ids == [
            "TASK-001",
            "TASK-002",
            "TASK-003",
            "TASK-004",
            "TASK-005",
            "TASK-006",
        ]

    def test_parse_plan_tasks_completion_status(self, sample_plan):
        """Test that completion status is detected correctly."""
        tasks = parse_plan_tasks(sample_plan)
        assert tasks[0]["complete"] is False  # - [ ]
        assert tasks[1]["complete"] is True  # - [x]
        assert tasks[2]["complete"] is False
        assert tasks[4]["complete"] is True  # - [x]

    def test_parse_plan_tasks_tag_extraction(self, sample_plan):
        """Test that [tag:name] tags are extracted."""
        tasks = parse_plan_tasks(sample_plan)
        assert tasks[0]["tags"] == ["important"]
        assert tasks[3]["tags"] == ["bug"]

    def test_parse_plan_tasks_dependency_extraction(self, sample_plan):
        """Test that after:TASK-ID dependencies are extracted."""
        tasks = parse_plan_tasks(sample_plan)
        assert tasks[2]["dependencies"] == ["TASK-001"]
        assert tasks[3]["dependencies"] == ["TASK-002"]

    def test_parse_plan_tasks_clean_text(self, sample_plan):
        """Test that task text has tags and dependencies removed."""
        tasks = parse_plan_tasks(sample_plan)
        assert tasks[0]["text"] == "First task"
        assert tasks[2]["text"] == "Third task"
        assert tasks[3]["text"] == "Fourth task"

    def test_parse_plan_tasks_raw_line_preserved(self, sample_plan):
        """Test that original markdown line is preserved."""
        tasks = parse_plan_tasks(sample_plan)
        assert "raw_line" in tasks[0]
        assert "- [ ]" in tasks[0]["raw_line"]

    def test_parse_plan_tasks_file_not_found(self, tmp_path):
        """Test PlanParseError raised when file doesn't exist."""
        with pytest.raises(PlanParseError, match="Plan file not found"):
            parse_plan_tasks(tmp_path / "nonexistent.md")

    def test_parse_plan_tasks_empty_file(self, tmp_path):
        """Test parsing empty plan file returns empty list."""
        plan_file = tmp_path / "empty.md"
        plan_file.write_text("")
        tasks = parse_plan_tasks(plan_file)
        assert len(tasks) == 0


class TestExtractTaskMetadata:
    """Test suite for extract_task_metadata function."""

    def test_extract_metadata_simple_task(self):
        """Test metadata extraction from simple task."""
        metadata = extract_task_metadata("Simple task description")
        assert metadata["title"] == "Simple task description"
        assert metadata["tags"] == []
        assert metadata["dependencies"] == []

    def test_extract_metadata_with_tags(self):
        """Test metadata extraction with tags."""
        metadata = extract_task_metadata("Task [tag:important] [tag:bug]")
        assert metadata["tags"] == ["important", "bug"]
        assert metadata["title"] == "Task"

    def test_extract_metadata_with_dependencies(self):
        """Test metadata extraction with dependencies."""
        metadata = extract_task_metadata("Task after:TASK-001 after:TASK-002")
        assert metadata["dependencies"] == ["TASK-001", "TASK-002"]
        assert metadata["title"] == "Task"

    def test_extract_metadata_mixed(self):
        """Test metadata extraction with tags and dependencies."""
        metadata = extract_task_metadata("Complex task [tag:test] after:TASK-001")
        assert metadata["title"] == "Complex task"
        assert metadata["tags"] == ["test"]
        assert metadata["dependencies"] == ["TASK-001"]

    def test_extract_metadata_multiline(self):
        """Test title extraction from multiline task."""
        metadata = extract_task_metadata("First line\nSecond line\nThird line")
        assert metadata["title"] == "First line"

    def test_extract_metadata_long_title(self):
        """Test title truncation for long tasks."""
        long_text = "A" * 100
        metadata = extract_task_metadata(long_text)
        assert len(metadata["title"]) == 50


class TestDetectIncompleteTasks:
    """Test suite for detect_incomplete_tasks function."""

    def test_detect_incomplete_filters_complete(self):
        """Test that complete tasks are filtered out."""
        tasks = [
            {"id": "TASK-001", "complete": False},
            {"id": "TASK-002", "complete": True},
            {"id": "TASK-003", "complete": False},
        ]
        incomplete = detect_incomplete_tasks(tasks)
        assert len(incomplete) == 2
        assert incomplete[0]["id"] == "TASK-001"
        assert incomplete[1]["id"] == "TASK-003"

    def test_detect_incomplete_all_complete(self):
        """Test when all tasks are complete."""
        tasks = [
            {"id": "TASK-001", "complete": True},
            {"id": "TASK-002", "complete": True},
        ]
        incomplete = detect_incomplete_tasks(tasks)
        assert len(incomplete) == 0

    def test_detect_incomplete_all_incomplete(self):
        """Test when all tasks are incomplete."""
        tasks = [
            {"id": "TASK-001", "complete": False},
            {"id": "TASK-002", "complete": False},
        ]
        incomplete = detect_incomplete_tasks(tasks)
        assert len(incomplete) == 2

    def test_detect_incomplete_missing_key(self):
        """Test handling tasks without 'complete' key."""
        tasks = [
            {"id": "TASK-001"},  # Missing 'complete' key
            {"id": "TASK-002", "complete": False},
        ]
        incomplete = detect_incomplete_tasks(tasks)
        assert len(incomplete) == 2  # Both treated as incomplete

    def test_detect_incomplete_empty_list(self):
        """Test handling empty task list."""
        incomplete = detect_incomplete_tasks([])
        assert len(incomplete) == 0
