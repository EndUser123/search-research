"""
Code Map Query Helper

Provides fast lookup of code map context without loading full documents.
Optimized for LLM token efficiency - reads only frontmatter YAML.

Usage:
    from yt_fts.utils.code_map import get_code_map_context, get_file_context

    # Get context for a specific file
    context = get_file_context("batch_downloader.py")

    # Get context for a specific concern
    context = get_code_map_context(concern="deadlock")
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
import logging

log = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    log.warning("PyYAML not installed - code map queries will return empty results")


def _find_code_map_path(start_dir: str | None = None) -> Path | None:
    """Find the nearest CODE_MAP.md file."""
    if start_dir is None:
        start_dir = Path.cwd()

    # Search upward for docs/ directory
    current = Path(start_dir)
    while current != current.parent:
        code_map = current / "docs" / "CODE_MAP.md"
        if code_map.exists():
            return code_map
        current = current.parent

    # Try project root relative
    project_root = Path(__file__).parent.parent.parent  # Back to project root
    code_map = project_root / "docs" / "CODE_MAP.md"
    if code_map.exists():
        return code_map

    return None


def _parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from CODE_MAP.md."""
    if not YAML_AVAILABLE:
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract YAML frontmatter (between --- markers)
        # Find content between first --- and second ---
        if not content.startswith('---'):
            return None
        
        # Find the end marker (second ---)
        end_marker = content.find(chr(10) + '---', 4)  # chr(10) = newline
        if end_marker == -1:
            return None
        
        # Extract YAML content (skip first '---' + newline)
        yaml_content = content[4:end_marker]
        return yaml.safe_load(yaml_content)
    except Exception as e:
        log.warning("Failed to parse CODE_MAP.md frontmatter: %s", e)
        return None

def get_code_map_context(concern: str | None = None) -> str:
    """
    Get code map context for a specific concern.

    Args:
        concern: The concern to look up (e.g., "deadlock", "high_cc", "types")

    Returns:
        Formatted context string with relevant information, or empty string if not found.

    Examples:
        >>> get_code_map_context(concern="deadlock")
        "Found in CODE_MAP.md: Section 4 - Risk Register / unified_discovery.py:98-107"

        >>> get_code_map_context(concern="not_found")
        ""
    """
    code_map = _find_code_map_path()
    if not code_map:
        return ""

    frontmatter = _parse_frontmatter(code_map)
    if not frontmatter:
        return ""

    # Check lookup_by_concern
    lookup = frontmatter.get("lookup_by_concern", {})
    if concern in lookup:
        log.debug('Code map query successful: concern=%s -> %s', concern, lookup[concern])
        return f"Found in CODE_MAP.md: {lookup[concern]}"

    log.debug('Code map query: concern=%s not found', concern)
    return ""


def get_file_context(file_name: str) -> str:
    """
    Get code map context for a specific file.

    Args:
        file_name: Name of the file (e.g., "batch_downloader.py")

    Returns:
        Formatted context string with relevant information.

    Examples:
        >>> get_file_context("batch_downloader.py")
        "File in CODE_MAP.md:
        - Severity: critical
        - CC max: 30
        - Risks: god_class, high_params, deadlock
        - Sections: 1_dependencies, 3_complexity, 4_risks, 5_types
        - Lines: 3649"

        >>> get_file_context("unknown_file.py")
        "File not found in CODE_MAP.md (low-risk indicator)"
    """
    code_map = _find_code_map_path()
    if not code_map:
        return "CODE_MAP.md not found"

    frontmatter = _parse_frontmatter(code_map)
    if not frontmatter:
        return "CODE_MAP.md frontmatter parsing failed"

    # Check quick_index
    quick_index = frontmatter.get("quick_index", {})
    if file_name in quick_index:
        info = quick_index[file_name]
        return f"""File in CODE_MAP.md:
- Severity: {info.get('severity', 'unknown')}
- CC max: {info.get('cc_max', 'N/A')}
- Risks: {', '.join(info.get('risks', []))}
- Sections: {', '.join(info.get('sections', []))}
- Lines: {info.get('lines', 'N/A')}"""

    return f"File not found in CODE_MAP.md (low-risk indicator)"


def list_critical_files() -> list[str]:
    """List all files marked as critical or high severity in CODE_MAP.md."""
    code_map = _find_code_map_path()
    if not code_map:
        return []

    frontmatter = _parse_frontmatter(code_map)
    if not frontmatter:
        return []

    quick_index = frontmatter.get("quick_index", {})
    critical = [
        file for file, info in quick_index.items()
        if info.get('severity') in ('critical', 'high')
    ]

    return critical


def get_summary() -> dict[str, Any] | None:
    """Get summary statistics from CODE_MAP.md."""
    code_map = _find_code_map_path()
    if not code_map:
        return None

    frontmatter = _parse_frontmatter(code_map)
    if not frontmatter:
        return None

    return frontmatter.get("summary", {})


def format_for_llm(concern: str, file_name: str | None = None) -> str:
    """
    Format code map context for LLM consumption.

    This is the main entry point for skills to query code maps.

    Args:
        concern: The concern being investigated (e.g., "deadlock", "high_cc")
        file_name: Optional file name to filter by

    Returns:
        Formatted string with relevant context.
    """
    parts = []

    if file_name:
        parts.append(f"# File: {file_name}")
        parts.append(get_file_context(file_name))
        parts.append("")

    if concern:
        parts.append(f"# Concern: {concern}")
        parts.append(get_code_map_context(concern))
        parts.append("")

    # Add summary if available
    summary = get_summary()
    if summary:
        parts.append("# Summary Statistics")
        parts.append(f"- Critical risks: {summary.get('critical_risks', 'N/A')}")
        parts.append(f"- High risks: {summary.get('high_risks', 'N/A')}")
        parts.append(f"- Complexity hotspots: {summary.get('complexity_hotspots', 'N/A')}")
        parts.append(f"- Type gaps: {summary.get('type_gaps', 'N/A')}")

    return "\n".join(parts)


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--concern":
            if len(sys.argv) > 2:
                print(format_for_llm(concern=sys.argv[2]))
            else:
                print("Usage: python code_map.py --concern <name>")
        elif sys.argv[1] == "--file":
            if len(sys.argv) > 2:
                print(format_for_llm(concern=None, file_name=sys.argv[2]))
            else:
                print("Usage: python code_map.py --file <name>")
        elif sys.argv[1] == "--summary":
            summary = get_summary()
            if summary:
                print("Code Map Summary:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
        elif sys.argv[1] == "--critical":
            critical = list_critical_files()
            print("Critical/High severity files:")
            for f in critical:
                print(f"  - {f}")
    else:
        print(__doc__)
