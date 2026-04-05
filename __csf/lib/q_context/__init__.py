"""
Q Context - Context sharing between /q and strategic skills

Provides structured context passing from /q analysis to strategic skills
with conversation proximity detection and staleness checking.

Also provides session activity tracking with semantic topic inference.
Also provides artifact audit integration for pending documentation checks.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

CONTEXT_FILE = Path("P:/__csf/.state/q_context.json")
MESSAGE_WINDOW = 10  # Number of messages to check for conversation continuity
SESSION_ACTIVITY_DIR = Path("P:/__csf/.state/session_activities")


def write_context(
    session_id: str,
    analysis: Mapping[str, object],
) -> None:
    """
    Write /q analysis context to file.

    Args:
        session_id: WT_SESSION value
        analysis: Analysis results from /q (issues, mode, files, etc.)
    """
    import json

    # Capture git state for staleness detection
    session_files = analysis.get("session_files", [])
    git_snapshot = _capture_git_state(session_files)

    context = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "git_snapshot": git_snapshot,
        "analysis": dict(analysis),
    }

    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_FILE.write_text(json.dumps(context, indent=2) + "\n")


def read_context(
    session_id: str,
    messages: list[Mapping[str, object]] | None = None,
    check_stale: bool = True,
) -> dict[str, object] | None:
    """
    Read /q context if valid for current session and conversation.

    Validity rules:
    - Session ID must match
    - /q output must be in recent messages (conversation proximity)

    Args:
        session_id: Current WT_SESSION value
        messages: Recent conversation messages (for proximity check)
        check_stale: If True, include staleness check results

    Returns:
        Context dict if valid, None otherwise. Includes 'stale' key if check_stale=True.
    """
    import json

    if not CONTEXT_FILE.exists():
        return None

    try:
        data = json.loads(CONTEXT_FILE.read_text())
    except json.JSONDecodeError:
        return None

    # Session must match
    if data.get("session_id") != session_id:
        return None

    # Conversation proximity: check if /q output is in recent messages
    if messages:
        if not _q_in_recent_messages(messages):
            return None

    analysis = data.get("analysis", {})

    # Add staleness check if requested
    if check_stale:
        git_snapshot = data.get("git_snapshot", {})
        session_files = analysis.get("session_files", [])
        staleness = _check_staleness(git_snapshot, session_files)
        analysis["stale"] = staleness

    return analysis


def _q_in_recent_messages(messages: list[Mapping[str, object]]) -> bool:
    """
    Check if /q output appears in recent message history.

    Args:
        messages: Recent conversation messages (last 10)

    Returns:
        True if /q output found in recent messages
    """
    # Look for /q markers in message content
    for msg in list(messages)[-MESSAGE_WINDOW:]:
        content = str(msg.get("content", ""))
        if any(marker in content for marker in ["## Quick Scan:", "## Strategic Priorities", "## INTEL:"]):
            return True
    return False


def _capture_git_state(session_files: list[str]) -> dict[str, str]:
    """
    Capture git state for staleness detection.

    Args:
        session_files: Files touched in this session

    Returns:
        Dict with HEAD commit hash and file modification times
    """
    state: dict[str, str] = {}

    # Get HEAD commit hash
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            state["head"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Get mtime for session files that exist
    mtimes: dict[str, str] = {}
    for file_path in session_files:
        path = Path(file_path)
        if path.exists():
            try:
                mtimes[file_path] = str(path.stat().st_mtime)
            except OSError:
                pass

    if mtimes:
        state["file_mtimes"] = mtimes

    return state


def _check_staleness(
    git_snapshot: dict[str, str],
    session_files: list[str],
) -> dict[str, object]:
    """
    Check if context is stale due to git or file changes.

    Args:
        git_snapshot: Git state captured when context was written
        session_files: Files that were in the session

    Returns:
        Dict with 'is_stale' bool and 'reason' str if stale
    """
    result: dict[str, object] = {"is_stale": False, "reason": None}

    # Check if HEAD changed
    old_head = git_snapshot.get("head")
    if old_head:
        try:
            new_head_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if new_head_result.returncode == 0:
                new_head = new_head_result.stdout.strip()
                if new_head != old_head:
                    result["is_stale"] = True
                    result["reason"] = "Git HEAD changed (new commits)"
                    return result
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check if any session files were modified
    old_mtimes = git_snapshot.get("file_mtimes", {})
    for file_path, old_mtime in old_mtimes.items():
        path = Path(file_path)
        if path.exists():
            try:
                new_mtime = str(path.stat().st_mtime)
                if new_mtime != old_mtime:
                    result["is_stale"] = True
                    result["reason"] = f"File modified: {file_path}"
                    return result
            except OSError:
                pass

    return result


def clear_context(session_id: str | None = None) -> None:
    """
    Clear stored /q context.

    Args:
        session_id: If provided, only clear if session matches
    """
    if not CONTEXT_FILE.exists():
        return

    if session_id:
        try:
            data = json.loads(CONTEXT_FILE.read_text())
            if data.get("session_id") != session_id:
                return
        except json.JSONDecodeError:
            pass

    CONTEXT_FILE.unlink(missing_ok=True)


# ============================================================================
# Session Activity Tracking with Semantic Inference
# ============================================================================

def get_session_activity(
    wt_session: str,
    minutes: int = 30,
    operations: tuple[str, ...] = ("write", "edit"),
) -> dict[str, object]:
    """
    Get session activity with semantic topic inference.

    Args:
        wt_session: WT_SESSION environment variable value
        minutes: Temporal window for recent activity (default 30)
        operations: Operation types to include (default: write, edit only)

    Returns:
        Dict with:
        - terminal: Session ID (truncated)
        - topic: Inferred semantic topic
        - files_worked: List of file paths
        - domains: Dict mapping domain -> set of files
    """
    # Extract session ID from UUID
    session_id = wt_session.split("-")[0] if "-" in wt_session else wt_session
    session_file = SESSION_ACTIVITY_DIR / f"wt_{session_id}.json"

    if not session_file.exists():
        return {
            "terminal": wt_session[:8] + "...",
            "topic": "No session activity found",
            "files_worked": [],
            "domains": {},
        }

    try:
        with open(session_file) as f:
            session_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            "terminal": wt_session[:8] + "...",
            "topic": "Error reading session activity",
            "files_worked": [],
            "domains": {},
        }

    activities = session_data.get("activities", [])

    # Filter by operation type
    filtered_activities = [
        a for a in activities
        if a.get("operation") in operations
    ]

    # Path + Temporal clustering
    domain_clusters = _cluster_session_activity(filtered_activities, minutes)

    # Infer semantic topic
    inferred_topic = _infer_topic_from_clusters(domain_clusters)

    # Flatten for display
    files_worked = []
    for files_set in domain_clusters.values():
        files_worked.extend(list(files_set)[:3])  # Max 3 per domain

    return {
        "terminal": wt_session[:8] + "...",
        "topic": inferred_topic,
        "files_worked": files_worked[:5],  # Max 5 total
        "domains": {k: list(v) for k, v in domain_clusters.items()},
    }


def _cluster_session_activity(
    activities: list[dict],
    minutes: int,
) -> defaultdict[str, set]:
    """
    Cluster session activities by domain pattern and temporal window.

    Args:
        activities: List of activity dicts from session file
        minutes: Temporal window in minutes

    Returns:
        defaultdict mapping domain -> set of file paths
    """
    domain_clusters = defaultdict(set)
    recent_cutoff = datetime.now() - timedelta(minutes=minutes)

    for activity in activities:
        file_path = activity.get("file_path")
        timestamp_str = activity.get("timestamp")

        if not file_path:
            continue

        # Parse timestamp for temporal filtering
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        # Only include recent activity (temporal clustering)
        if timestamp < recent_cutoff:
            continue

        domain = _extract_domain_pattern(file_path)
        domain_clusters[domain].add(file_path)

    return domain_clusters


def _extract_domain_pattern(file_path: str) -> str:
    """
    Extract domain pattern from file path for clustering.

    Args:
        file_path: File path string

    Returns:
        Domain pattern (e.g., 'skills/strat', 'src/modules', 'tests')
    """
    # Normalize path separators
    path_str = str(file_path).replace("\\", "/")

    # Key domain indicators (string matching for cross-platform)
    if "/.claude/skills/" in path_str:
        parts = path_str.split("/.claude/skills/")
        if len(parts) > 1:
            skill_name = parts[1].split("/")[0]
            return f"skills/{skill_name}" if skill_name != "SKILL.md" else "skills"
    elif "/__csf/src/modules/" in path_str:
        return "src/modules"
    elif "/__csf/tests/" in path_str or "/tests/" in path_str:
        return "tests"
    elif "/.claude/hooks/" in path_str:
        return "hooks"
    elif "/__csf/scripts/" in path_str or "/scripts/" in path_str:
        return "scripts"

    # Fallback: extract first meaningful directory
    parts = [p for p in path_str.split("/") if p and p not in ("P:", "__csf", ".claude")]
    return parts[0] if parts else "other"


def _infer_topic_from_clusters(clusters: dict[str, set]) -> str:
    """
    Infer semantic topic from clustered file patterns.

    Args:
        clusters: Dict mapping domain -> set of file paths

    Returns:
        Human-readable topic description
    """
    if not clusters:
        return "No clear topic detected"

    topic_map = {
        "skills": "Skill/Command development",
        "src/modules": "Module development",
        "tests": "Testing",
        "hooks": "Hook development",
        "scripts": "Script development",
    }

    # Detect consolidation patterns (multiple skills touched)
    skill_domains = [k for k in clusters.keys() if "skills" in k]
    if len(skill_domains) > 2:
        return f"Skills consolidation ({len(skill_domains)} skills)"

    # Single dominant domain
    if len(clusters) == 1:
        domain = list(clusters.keys())[0]
        return topic_map.get(domain, f"{domain.capitalize()} work")

    # Multiple domains - list them
    topics = [topic_map.get(k, k) for k in list(clusters.keys())[:3]]
    return " + ".join(topics)


# ============================================================================
# Git Status Filtering for Session Isolation
# ============================================================================

def get_git_status_for_session(
    wt_session: str,
    cwd: str | Path | None = None,
) -> dict[str, object]:
    """
    Get git status filtered by session files only.

    Prevents bleed-in from other terminals by only reporting files that
    were actually modified in the current session.

    Args:
        wt_session: WT_SESSION environment variable value
        cwd: Current working directory (optional, for CWD filtering)

    Returns:
        Dict with:
        - session_files: List of files worked in this session
        - all_modified: All files in git status (terminal-agnostic)
        - session_modified: Files in git status AND session (intersection)
        - is_clean: True if no session files are modified
        - has_unpushed: True if unpushed commits exist
    """
    import subprocess

    # Get session files
    session_activity = get_session_activity(wt_session, minutes=30)
    session_files = set(session_activity.get("files_worked", []))
    session_domains = session_activity.get("domains", {})

    # Get all git status (terminal-agnostic)
    all_modified = []
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            cwd=cwd,
        )
        if result.returncode == 0:
            # Parse git status output: "M file.py" or "MM file.py" etc.
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                # Format: "XY filename" where X=staging, Y=worktree
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    status, filepath = parts
                    # Normalize path
                    normalized = str(Path(filepath).absolute())
                    all_modified.append({
                        "path": normalized,
                        "status": status,
                    })
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Filter: only include files that were touched in THIS session
    session_modified = []
    for entry in all_modified:
        file_path = entry["path"]
        # Check if file was worked in this session
        if file_path in session_files:
            session_modified.append(entry)
        else:
            # Also check if any session file path is a prefix (directory matching)
            for session_file in session_files:
                try:
                    if Path(file_path).is_relative_to(Path(session_file)):
                        session_modified.append(entry)
                        break
                except ValueError:
                    # is_relative_to() raises ValueError on different drives on Windows
                    pass

    # Check for unpushed commits
    has_unpushed = False
    try:
        result = subprocess.run(
            ["git", "log", "origin/main..HEAD", "--oneline"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            cwd=cwd,
        )
        if result.returncode == 0 and result.stdout.strip():
            has_unpushed = True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return {
        "session_files": list(session_files),
        "all_modified": all_modified,
        "session_modified": session_modified,
        "is_clean": len(session_modified) == 0,
        "has_unpushed": has_unpushed,
        "domains": session_domains,
        "terminal": wt_session[:8] + "...",
    }


# ============================================================================
# Artifact Audit Integration for /q
# ============================================================================

def check_pending_artifacts(project_root: str | Path | None = None) -> dict[str, object]:
    """
    Check for pending artifact updates (PRD, ARD, CHANGELOG, README).

    Integrated into /q Stage 1 Quick Scan to detect documentation debt.

    Args:
        project_root: Project directory (defaults to auto-detect)

    Returns:
        Dict with:
        - has_pending: bool - True if any pending artifacts exist
        - count: int - Total number of pending items
        - by_severity: dict - Counts by severity (critical, standard, low)
        - items: list - Pending item summaries (item_id, summary, artifacts)
        - error: str | None - Error message if check failed
    """
    result: dict[str, object] = {
        "has_pending": False,
        "count": 0,
        "by_severity": {"critical": 0, "standard": 0, "low": 0},
        "items": [],
        "error": None,
    }

    try:
        # Import artifact_core (shared with artifact-audit skill)
        artifact_skill_dir = Path("P:/") / ".claude" / "skills" / "artifact" / "resources" / "scripts"
        import sys
        if str(artifact_skill_dir) not in sys.path:
            sys.path.insert(0, str(artifact_skill_dir))

        from artifact_core import get_pending_items, find_project_root
        from artifact_init import ensure_schema

        # Ensure schema exists
        ensure_schema()

        # Find project root
        root = Path(project_root) if project_root else find_project_root()
        if not root:
            result["error"] = "Could not find project root"
            return result

        # Get pending items
        items = get_pending_items(root)

        if not items:
            return result

        # Process results
        result["has_pending"] = True
        result["count"] = len(items)

        # Group by severity
        by_severity: dict[str, int] = {"critical": 0, "standard": 0, "low": 0}
        item_summaries = []

        for item in items:
            severity = item.get("severity", "low")
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # Extract pending artifacts (not done, not n/a)
            artifacts = item.get("artifacts", {})
            pending_artifacts = [
                k for k, v in artifacts.items()
                if v not in ("done", "n/a")
            ]

            item_summaries.append({
                "item_id": item.get("item_id"),
                "summary": item.get("summary"),
                "severity": severity,
                "artifacts": pending_artifacts,
            })

        result["by_severity"] = by_severity
        result["items"] = item_summaries

    except ImportError as e:
        result["error"] = f"Artifact module not available: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result
