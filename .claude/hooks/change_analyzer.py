#!/usr/bin/env python3
"""Analyze git changes for commit message generation and CHANGELOG updates."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def is_in_merge(cwd: Path) -> bool:
    """Check if we're in a merge or rebase state."""
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        # Get actual git directory (handles worktrees, non-standard locations)
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            cwd=str(cwd),
            timeout=5,
            text=True,
            creationflags=creation_flags
        )
        if result.returncode != 0:
            return False
        git_dir = Path(result.stdout.strip())

        # Check merge state (MERGE_HEAD exists)
        result = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
            capture_output=True,
            cwd=str(cwd),
            timeout=5,
            creationflags=creation_flags
        )
        if result.returncode == 0:
            return True

        # Check rebase state (rebase-merge or rebase-apply directories exist)
        rebase_merge = git_dir / "rebase-merge"
        rebase_apply = git_dir / "rebase-apply"
        return rebase_merge.exists() or rebase_apply.exists()
    except (subprocess.TimeoutExpired, OSError):
        return False


def get_cached_changes(cwd: Path) -> list[tuple[str, str]]:
    """Get staged changes as (status, filepath) tuples."""
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=10,
            creationflags=creation_flags
        )
        changes = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                changes.append((parts[0], parts[1]))
        return changes
    except (subprocess.TimeoutExpired, OSError):
        return []


def changelog_already_changed(cwd: Path) -> bool:
    """Check if CHANGELOG.md is already being changed manually."""
    changes = get_cached_changes(cwd)
    return any(f.endswith("CHANGELOG.md") for _, f in changes)


def detect_performance_change(cwd: Path, filepath: str) -> str | None:
    """Detect performance improvements in diff."""
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            ["git", "diff", "--cached", filepath],
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=5,
            creationflags=creation_flags
        )
        patterns = [
            r'(\d+\.?\d*[mu]?s)\s*→\s*(\d+\.?\d*[mu]?s)',
            r'(\d+%)\s+(faster|reduction|improvement)',
        ]
        for line in result.stdout.split('\n')[:100]:  # Limit scan
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(0)
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def analyze_changes(cwd: Path) -> dict:
    """Analyze changes and return commit message + changelog data."""
    if is_in_merge(cwd):
        return {"notable": False, "skip_reason": "merge"}

    changes = get_cached_changes(cwd)
    if not changes:
        return {"notable": False}

    added = []
    changed = []
    removed = []
    fixed = []
    commit_parts = []

    for status, filepath in changes:
        name = Path(filepath).name

        if status == "A":  # Added
            if "router" in filepath.lower():
                added.append(f"{filepath}: consolidated router")
                commit_parts.append("consolidate router")
            elif "hook" in filepath.lower():
                added.append(f"{filepath}: new hook")
                commit_parts.append("add hook")
            elif filepath.endswith("CHANGELOG.md"):
                commit_parts.append("update docs")
            elif "test_" in filepath or "_test." in filepath:
                added.append(f"{filepath}: tests")
                commit_parts.append("add tests")
            else:
                added.append(filepath)
                commit_parts.append(f"add {name}")

        elif status == "D":  # Deleted
            removed.append(filepath)
            if "router" in filepath.lower():
                commit_parts.append("remove old router")
            else:
                commit_parts.append(f"remove {name}")

        elif status in ("M", "R"):  # Modified/Renamed
            perf = detect_performance_change(cwd, filepath)
            if perf:
                changed.append(f"{filepath}: {perf}")
                commit_parts.append(f"performance: {perf}")
            elif "fix" in filepath.lower() or "bug" in filepath.lower():
                fixed.append(filepath)
                commit_parts.append(f"fix {name}")
            else:
                commit_parts.append(f"update {name}")

    # Build commit message
    if commit_parts:
        unique_parts = list(dict.fromkeys(commit_parts))
        if len(unique_parts) <= 3:
            commit_msg = ", ".join(unique_parts)
        else:
            commit_msg = f"{', '.join(unique_parts[:3])} (+{len(unique_parts)-3} more)"
    else:
        commit_msg = "session changes"

    # Notable if: multiple changes, deletions, performance improvements, or 2+ files touched
    # Single trivial file additions are NOT notable
    notable = bool(
        removed or  # Any deletion is notable
        changed or  # Performance improvements are notable
        len(added) > 1 or  # Multiple additions are notable
        (len(added) == 1 and any(x in added[0].lower() for x in ["router", "hook", "CHANGELOG.md"])) or  # Significant single additions
        len(commit_parts) >= 2  # 2+ files modified is notable
    )

    return {
        "notable": notable,
        "commit_message": commit_msg,
        "changelog_entry": {
            "Added": added,
            "Changed": changed,
            "Removed": removed,
            "Fixed": fixed,
        }
    }


def update_changelog(cwd: Path, entry: dict, changelog_path: Path) -> bool:
    """Append entry to CHANGELOG.md, preserving frontmatter and matching existing format."""
    if not any(entry.values()):
        return False

    try:
        content = changelog_path.read_text() if changelog_path.exists() else ""

        # Build new section matching existing CHANGELOG format
        # Format: ## [Unreleased] followed by ### Category\n\n- item\n- item\n\n
        new_section = "\n"
        for category, items in entry.items():
            if items:
                new_section += f"### {category}\n\n"
                for item in items:
                    new_section += f"- {item}\n"
                new_section += "\n"

        # Preserve frontmatter if present
        if content.startswith("---"):
            parts = content.split("\n---\n", 1)
            if len(parts) == 2:
                frontmatter, body = parts
                # Insert after frontmatter, before first section or after [Unreleased]
                if "## [Unreleased]" in body:
                    content = frontmatter + "\n---\n" + body.replace("## [Unreleased]", f"## [Unreleased]{new_section}")
                else:
                    content = frontmatter + "\n---\n" + new_section + body
            else:
                content = new_section + content
        elif "## [Unreleased]" in content:
            content = content.replace("## [Unreleased]", f"## [Unreleased]{new_section}")
        else:
            content = new_section + content

        changelog_path.write_text(content)
        return True
    except Exception:
        return False
