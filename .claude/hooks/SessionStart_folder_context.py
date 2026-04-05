#!/usr/bin/env python3
"""
SessionStart Hook: Folder Context Generation

Auto-generates per-project context files with activity timelines.
Inspired by claude-mem: https://docs.claude-mem.ai/introduction

This hook creates .claude/context.md files in project directories with:
- Project name and path
- Last activity timestamp
- Recent files modified (from activity log)
- Recent search queries (from activity log)
- Recent git commits (last 7 days)

The context files are auto-generated and will be overwritten on each session start.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add CSF NIP src to path
_csf_root = Path(__file__).resolve().parent.parent.parent / "__csf"
if str(_csf_root / "src") not in sys.path:
    sys.path.insert(0, str(_csf_root / "src"))

# NOTE: Logging disabled for hooks - any stderr is treated as "hook error" by Claude Code
# The default logging.basicConfig() writes to stderr, which triggers false "hook error" messages
# Use NullHandler to silence all logging output
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Activity log location
ACTIVITY_LOG = Path(__file__).resolve().parent.parent / "projects" / "P--" / ".data" / "activity.jsonl"


def get_recent_activity(days: int = 7) -> list[dict]:
    """Get recent activity from the activity log.

    Args:
        days: Number of days to look back

    Returns:
        List of activity entries
    """
    if not ACTIVITY_LOG.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    recent_activity = []

    try:
        for line in ACTIVITY_LOG.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts_str = entry.get("timestamp", "")
                if isinstance(ts_str, str):
                    try:
                        # Try ISO format first
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        # Try Unix timestamp
                        ts = datetime.fromtimestamp(float(ts_str))
                elif isinstance(ts_str, (int, float)):
                    ts = datetime.fromtimestamp(ts_str)
                else:
                    continue

                if ts >= cutoff:
                    recent_activity.append(entry)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
    except OSError:
        return []

    return recent_activity


def extract_files_and_queries(activity: list[dict]) -> tuple[list[str], list[str]]:
    """Extract unique files and queries from activity log.

    Args:
        activity: List of activity entries

    Returns:
        Tuple of (files, queries)
    """
    files = []
    queries = []
    seen_files = set()
    seen_queries = set()

    for entry in activity:
        # Extract files from tool calls
        for call in entry.get("tool_calls", []):
            if call.get("name") == "Read":
                for inp in call.get("input", []):
                    if isinstance(inp, dict) and "file_path" in inp:
                        file_path = inp["file_path"]
                        # Shorten to relative path if possible
                        if ":\\" in file_path or "/" in file_path:
                            parts = file_path.replace("\\", "/").split("/")
                            file_path = "/".join(parts[-3:]) if len(parts) > 3 else file_path
                        if file_path not in seen_files:
                            seen_files.add(file_path)
                            files.append(file_path)

            if call.get("name") == "Grep" or call.get("name") == "Glob":
                for inp in call.get("input", []):
                    if isinstance(inp, dict) and "pattern" in inp:
                        # Treat patterns as pseudo-queries
                        pattern = inp["pattern"]
                        if pattern not in seen_queries:
                            seen_queries.add(pattern)
                            queries.append(pattern)

        # Extract queries from user messages
        user_msg = entry.get("user_message", "")
        if user_msg and len(user_msg) < 100:
            # Heuristic: short messages might be search queries
            if user_msg not in seen_queries:
                seen_queries.add(user_msg)
                queries.append(user_msg)

    return files[:10], queries[:10]


@hook_main
def main() -> None:
    """Main entry point for the folder context generation hook."""
    # Gracefully skip if FolderContextGenerator is not available
    try:
        from features.lib_folder_context import FolderContextGenerator
    except (ImportError, ModuleNotFoundError):
        # FolderContextGenerator module not found - skip this hook silently
        # This is expected if the feature hasn't been implemented yet
        return

    # Get current working directory as the project path
    project_path = Path.cwd()

    # Skip if not in a meaningful project directory
    if project_path.name == "" or str(project_path) == "/":
        logger.debug("Skipping folder context: not in a project directory")
        return

    # Get recent activity
    recent_activity = get_recent_activity(days=7)
    recent_files, recent_queries = extract_files_and_queries(recent_activity)

    # Generate context
    generator = FolderContextGenerator()

    # Write context file
    context_file = generator.write_context_file(
        project_path=project_path,
        recent_files=recent_files if recent_files else None,
        recent_queries=recent_queries if recent_queries else None,
    )

    logger.info(f"Folder context generated: {context_file}")

if __name__ == "__main__":
    main()

