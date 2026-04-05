"""Plan parsing utilities for extracting tasks from markdown files."""

from pathlib import Path
from typing import Any

from scripts.patterns.task_patterns import (
    DEPENDENCY_PATTERN,
    TAG_PATTERN,
    TASK_PATTERN,
)


class PlanParseError(Exception):
    """Exception raised when plan file parsing fails."""


def parse_plan_tasks(plan_path: str | Path) -> list[dict[str, Any]]:
    """Extract tasks from plan.md markdown file.

    Args:
        plan_path: Path to plan markdown file

    Returns:
        List of task dictionaries with keys:
        - id: Task identifier (TASK-XXX format or auto-generated)
        - text: Task description text
        - complete: Boolean indicating completion status
        - tags: List of tags from [tag:name] syntax
        - dependencies: List of task IDs from after:TASK-ID syntax
        - raw_line: Original markdown line

    Raises:
        PlanParseError: If plan file doesn't exist or can't be read
    """
    plan_file = Path(plan_path)

    if not plan_file.exists():
        raise PlanParseError(f"Plan file not found: {plan_path}")

    try:
        content = plan_file.read_text()
    except OSError as e:
        raise PlanParseError(f"Failed to read plan file {plan_path}: {e}") from e

    tasks = []
    task_counter = 0

    for match in TASK_PATTERN.finditer(content):
        checkbox, task_text, comment = match.groups()
        is_complete = checkbox.lower() == "x"

        # Extract metadata
        tags = TAG_PATTERN.findall(task_text)
        dependencies = DEPENDENCY_PATTERN.findall(task_text)

        # Clean task text (remove task ID prefix, tags, and dependencies)
        clean_text = task_text
        # Remove task ID prefix if present at the beginning (e.g., "TASK-001 ")
        import re
        id_prefix_match = re.match(r'^(TASK-[0-9]+\s+)(.*)', clean_text)
        if id_prefix_match:
            clean_text = id_prefix_match.group(2)
        # Remove tags and dependencies
        clean_text = TAG_PATTERN.sub("", clean_text).strip()
        clean_text = DEPENDENCY_PATTERN.sub("", clean_text).strip()

        # Generate task ID
        task_counter += 1
        task_id = f"TASK-{task_counter:03d}"

        tasks.append({
            "id": task_id,
            "text": clean_text,
            "complete": is_complete,
            "tags": tags,
            "dependencies": dependencies,
            "raw_line": match.group(0),
        })

    return tasks


def extract_task_metadata(task_text: str) -> dict[str, Any]:
    """Parse task title, tags, and dependencies from markdown text.

    Args:
        task_text: Raw task text from markdown

    Returns:
        Dictionary with keys:
        - title: Task title (first line or first 50 chars)
        - tags: List of [tag:name] tags found
        - dependencies: List of after:TASK-ID dependencies found
    """
    tags = TAG_PATTERN.findall(task_text)
    dependencies = DEPENDENCY_PATTERN.findall(task_text)

    # Clean task text for title
    clean_text = task_text
    clean_text = TAG_PATTERN.sub("", clean_text).strip()
    clean_text = DEPENDENCY_PATTERN.sub("", clean_text).strip()

    # Extract title (first line, truncated to 50 chars)
    lines = clean_text.split("\n")
    title = lines[0] if lines else clean_text
    # Truncate to 50 characters if longer
    if len(title) > 50:
        title = title[:50]

    return {
        "title": title,
        "tags": tags,
        "dependencies": dependencies,
    }


def detect_incomplete_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter tasks that are not yet marked complete.

    Args:
        tasks: List of task dictionaries from parse_plan_tasks()

    Returns:
        Filtered list of incomplete tasks
    """
    return [task for task in tasks if not task.get("complete", False)]
