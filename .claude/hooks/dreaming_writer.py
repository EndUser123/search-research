"""Dreaming insights writer module (T-007).

Writes dreaming daemon insights to JSON and optionally markdown files.
Uses atomic write pattern (tmp + replace) to prevent partial writes.

Usage:
    from dreaming_writer import write_insights
    from dreaming_insights import DreamingInsights

    insights = DreamingInsights(...)
    config = {
        "json_output_path": "P:/.claude/state/dreaming-insights.json",
        "markdown_output_path": "P:/.claude/state/dreaming-insights.md",
        "enable_markdown": True
    }
    write_insights(insights, config)
"""
import json
from dataclasses import asdict
from pathlib import Path


def write_insights(insights, config: dict) -> None:
    """Write dreaming insights to JSON and optionally markdown files.

    Args:
        insights: DreamingInsights dataclass instance to write
        config: Configuration dict with keys:
            - json_output_path (str): Path for JSON output (required)
            - markdown_output_path (str): Path for markdown output (optional)
            - enable_markdown (bool): Whether to write markdown file (default: False)

    Behavior:
        - Always writes JSON file using atomic write pattern
        - Writes markdown file only if enable_markdown=True
        - Creates parent directories if they don't exist
        - Uses atomic writes (write to .tmp, then replace) to prevent corruption

    Raises:
        OSError: If file write fails (parent directory creation, permissions, etc.)
        TypeError: If insights is not a DreamingInsights instance
    """
    # Extract config values with defaults
    json_path_str = config.get("json_output_path", "P:/.claude/state/dreaming-insights.json")
    markdown_path_str = config.get("markdown_output_path", "P:/.claude/state/dreaming-insights.md")
    enable_markdown = config.get("enable_markdown", False)

    json_path = Path(json_path_str)
    markdown_path = Path(markdown_path_str) if markdown_path_str else None

    # Write JSON (always)
    _write_json_atomic(insights, json_path)

    # Write markdown (if enabled)
    if enable_markdown and markdown_path:
        _write_markdown_atomic(insights, markdown_path)


def _write_json_atomic(insights, output_path: Path) -> None:
    """Write insights as JSON using atomic write pattern.

    Args:
        insights: DreamingInsights dataclass instance
        output_path: Path where JSON file should be written
    """
    # Convert dataclass to dict for JSON serialization
    insights_dict = asdict(insights)

    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then replace
    temp_path = output_path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(insights_dict, indent=2),
        encoding="utf-8"
    )
    temp_path.replace(output_path)


def _write_markdown_atomic(insights, output_path: Path) -> None:
    """Write insights as markdown using atomic write pattern.

    Args:
        insights: DreamingInsights dataclass instance
        output_path: Path where markdown file should be written
    """
    # Get markdown content from insights
    markdown_content = insights.to_markdown()

    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then replace
    temp_path = output_path.with_suffix(".tmp")
    temp_path.write_text(markdown_content, encoding="utf-8")
    temp_path.replace(output_path)
