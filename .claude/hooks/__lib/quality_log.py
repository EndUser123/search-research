#!/usr/bin/env python3
"""Quality Log - Track code quality skill usage per project.

Records when quality skills (verify, uci, simplify, q, r, adversarial-review, etc.)
are run on a project. GTO reads this log to recommend quality skills that haven't
been run recently.

Log Format (JSONL):
    {"timestamp": "2026-03-19T02:30:00Z", "skill": "verify", "result": "passed", "tier": "4-tier"}
    {"timestamp": "2026-03-19T03:15:00Z", "skill": "uci", "result": "found 3 issues", "tier": "code-inspection"}

Location: {project_root}/.claude/quality_log.jsonl
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# Code quality skills that should be tracked
CODE_QUALITY_SKILLS = {
    "verify",
    "uci",
    "simplify",
    "q",
    "r",
    "refactor",
    "adversarial-review",
    "adversarial-performance",
    "adversarial-security",
    "adversarial-testing",
    "adversarial-quality",
    "tdd",
    "trace",
    "p",  # Code Maturation Pipeline with ToT enhancement
    "s",  # Exploratory strategy with multi-persona braiding
    "t",  # Context-aware adaptive testing with ToT enhancement
    "arch",  # Architecture advisor
}


def get_quality_log_path(project_root: str | Path | None = None) -> Path:
    """Get the quality log path for a project.

    Args:
        project_root: Project directory. Uses cwd if None.

    Returns:
        Path to .claude/quality_log.jsonl
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)

    # Check for .claue directory in project root
    # If not found, check for common project markers (package.json, pyproject.toml, etc.)
    claude_dir = project_root / ".claude"

    # If .claude doesn't exist at project root, check parent directories
    if not claude_dir.exists():
        for parent in [project_root.parent, project_root.parent.parent]:
            if (parent / ".claude").exists():
                claude_dir = parent / ".claude"
                break

    return claude_dir / "quality_log.jsonl"


def log_quality_skill(
    skill_name: str,
    result: str,
    tier: str = "unknown",
    project_root: str | Path | None = None,
) -> bool:
    """Log a quality skill execution to the project's quality log.

    Args:
        skill_name: Name of the skill (e.g., "verify", "uci")
        result: Result summary (e.g., "passed", "found 3 issues")
        tier: Skill tier/category (e.g., "4-tier", "code-inspection")
        project_root: Project directory. Uses cwd if None.

    Returns:
        True if log entry was written, False otherwise
    """
    # Only log code quality skills
    if skill_name not in CODE_QUALITY_SKILLS:
        return False

    log_path = get_quality_log_path(project_root)

    # Ensure .claude directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create log entry
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": skill_name,
        "result": result,
        "tier": tier,
    }

    # Append to log
    from file_lock import append_jsonl_safe
    return append_jsonl_safe(log_path, entry)


def read_quality_log(
    project_root: str | Path | None = None,
    skill_name: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Read quality log entries for a project.

    Args:
        project_root: Project directory. Uses cwd if None.
        skill_name: Filter to specific skill. If None, return all.
        limit: Maximum entries to return (most recent first).

    Returns:
        List of log entries, sorted by timestamp descending
    """
    log_path = get_quality_log_path(project_root)

    if not log_path.exists():
        return []

    try:
        with open(log_path, encoding="utf-8") as f:
            entries = []
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if skill_name is None or entry.get("skill") == skill_name:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

        # Sort by timestamp descending and limit
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return entries[:limit]
    except OSError:
        return []


def get_last_run(
    skill_name: str,
    project_root: str | Path | None = None,
) -> str | None:
    """Get the last run timestamp for a skill.

    Args:
        skill_name: Name of the skill
        project_root: Project directory. Uses cwd if None.

    Returns:
        ISO timestamp string or None if never run
    """
    entries = read_quality_log(project_root, skill_name, limit=1)
    if entries:
        return entries[0].get("timestamp")
    return None


def get_skills_not_run_recently(
    days: int = 7,
    project_root: str | Path | None = None,
) -> dict[str, str | None]:
    """Get skills that haven't been run recently.

    Args:
        days: Threshold in days. Skills not run within this period are returned.
        project_root: Project directory. Uses cwd if None.

    Returns:
        Dict mapping skill_name -> last_run_timestamp (None if never run)
    """
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    result = {}
    for skill in CODE_QUALITY_SKILLS:
        last_run = get_last_run(skill, project_root)
        if last_run is None or last_run < cutoff_iso:
            result[skill] = last_run

    return result
