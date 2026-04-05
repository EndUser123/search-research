"""
Git Context Analyzer for /gto

Multi-terminal-safe git state reader (no caching, fresh reads).
Git repo is shared source of truth — safe for multi-terminal isolation.
"""

from __future__ import annotations

from typing import Any


def get_git_context(working_directory: str = ".") -> dict[str, Any] | None:
    """
    Analyze Git repository context for gap analysis.

    Multi-terminal safe: No caching, always fresh reads from git repo.
    Git repository is shared source of truth across all terminals.

    Returns:
        None if git not available or not in git repo
        Dict with:
            - repository_path: str
            - current_branch: str
            - is_clean: bool
            - has_uncommitted_changes: bool
            - current_commit: str | None
            - recent_commits: list[dict] (last 10)
            - modified_files: list[str]
            - development_activity: str (HIGH/MEDIUM/LOW)
            - recent_patterns: list[str]
    """
    try:
        import git
    except ImportError:
        return None

    try:
        repo = git.Repo(working_directory)
    except Exception:
        return None

    try:
        context = {
            "repository_path": working_directory,
            "current_branch": repo.active_branch.name,
            "is_clean": not repo.is_dirty(),
            "has_uncommitted_changes": repo.is_dirty(),
            "current_commit": None,
            "recent_commits": [],
            "modified_files": [],
            "development_activity": "LOW",
            "recent_patterns": [],
        }

        # Get current commit
        try:
            context["current_commit"] = repo.head.commit.hexsha[:8]
        except Exception:
            pass

        # Get recent commits (last 10)
        context["recent_commits"] = _get_recent_commits(repo, limit=10)

        # Get modified files
        context["modified_files"] = _get_modified_files(repo)

        # Analyze development activity
        context["development_activity"] = _analyze_activity(context)

        # Detect patterns
        context["recent_patterns"] = _detect_patterns(context["recent_commits"])

        return context

    except Exception:
        return None


def _get_recent_commits(repo, limit: int = 10) -> list[dict]:
    """Get recent commits with classification."""
    commits = []
    try:
        for commit in repo.iter_commits(max_count=limit):
            commit_dict = {
                "commit_hash": commit.hexsha[:8],
                "author": str(commit.author),
                "timestamp": commit.committed_date,
                "message": commit.message.strip(),
                "files_changed": len(commit.stats.files),
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"],
                "commit_type": _classify_commit_type(commit.message),
            }
            commits.append(commit_dict)
    except Exception:
        pass
    return commits


def _get_modified_files(repo) -> list[str]:
    """Get list of modified files (staged + unstaged + untracked)."""
    try:
        staged_files = [item.a_path for item in repo.index.diff(None)]
        unstaged_files = [item.a_path for item in repo.index.diff(repo.head.commit)]
        untracked_files = repo.untracked_files
        return list(set(staged_files + unstaged_files + untracked_files))
    except Exception:
        return []


def _classify_commit_type(message: str) -> str:
    """Classify commit type based on message keywords."""
    message_lower = message.lower()

    if any(keyword in message_lower for keyword in ["fix", "bug", "error"]):
        return "BUGFIX"
    if any(keyword in message_lower for keyword in ["feat", "feature", "add"]):
        return "FEATURE"
    if any(keyword in message_lower for keyword in ["refactor", "clean", "improve"]):
        return "REFACTOR"
    if any(keyword in message_lower for keyword in ["test", "spec"]):
        return "TEST"
    if any(keyword in message_lower for keyword in ["doc", "readme"]):
        return "DOCUMENTATION"
    if any(keyword in message_lower for keyword in ["merge", "merge"]):
        return "MERGE"
    return "OTHER"


def _analyze_activity(git_context: dict) -> str:
    """Analyze development activity level based on recent commits."""
    if not git_context["recent_commits"]:
        return "LOW"

    recent_commits = len(git_context["recent_commits"])
    if recent_commits >= 10:
        return "HIGH"
    if recent_commits >= 5:
        return "MEDIUM"
    return "LOW"


def _detect_patterns(commits: list[dict]) -> list[str]:
    """Detect patterns in recent commits."""
    patterns = []

    if not commits:
        return patterns

    # Count commit types
    commit_types = [commit["commit_type"] for commit in commits]
    type_counts = {
        commit_type: commit_types.count(commit_type)
        for commit_type in set(commit_types)
    }

    # Identify dominant patterns
    if type_counts.get("FEATURE", 0) > type_counts.get("BUGFIX", 0):
        patterns.append("Feature development focus")
    elif type_counts.get("BUGFIX", 0) > type_counts.get("FEATURE", 0):
        patterns.append("Bug fixing focus")

    if type_counts.get("REFACTOR", 0) > 2:
        patterns.append("Active refactoring")

    if type_counts.get("TEST", 0) > 0:
        patterns.append("Test development activity")

    return patterns
