#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from collections import Counter
from datetime import datetime
import logging as _li
_logger = _li.getLogger(__name__)

from pathlib import Path

# Setup path for local imports BEFORE importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

# GitHelper enabled for auto-commit - GitPython works when cwd is repo root
# auto_commit_all() uses Path.cwd().parent.parent to get repo root
# Previously disabled due to subdirectory issues, but that's resolved
try:
    from __lib.git_helper import GitHelper, HAS_GITPYTHON
    HAS_GIT_HELPER = HAS_GITPYTHON
except ImportError:
    HAS_GIT_HELPER = False

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Import session manager for session ID retrieval
try:
    from __lib.session_manager import get_current_session_id

    HAS_SESSION_MANAGER = True
except ImportError:
    HAS_SESSION_MANAGER = False


def get_session_id_for_commit() -> str:
    """Get session ID for commit message tagging.

    Reads from the Claude Code session file at .claude/hooks/current_session.json.
    Falls back to 'unknown' if session detection fails.
    """
    if HAS_SESSION_MANAGER:
        try:
            session_id = get_current_session_id()
            if session_id and session_id != "default":
                return session_id
        except Exception:
            pass

    return "unknown"


# Import notification queue for DUF reminder
try:
    from notification_queue import add_notification

    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False

# Import change analyzer for meaningful commit messages
try:
    from change_analyzer import (
        analyze_changes,
        changelog_already_changed,
        update_changelog,
    )

    HAS_CHANGE_ANALYZER = True
except ImportError:
    HAS_CHANGE_ANALYZER = False

# Import commit message parser for semantic commit messages
try:
    from commit_message_parser import generate_semantic_commit_message

    HAS_COMMIT_MESSAGE_PARSER = True
except ImportError:
    HAS_COMMIT_MESSAGE_PARSER = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = Path(__file__).resolve().parent

# Constants
DEFAULT_COMMIT_MESSAGE = "auto-commit: session end"
MERGE_COMMIT_MESSAGE = "auto-commit: merge resolution"
SESSION_LINK_COMMIT_MESSAGE = "auto-commit: [{session_id}] {message}"
OPPORTUNITIES_FILE = HOOKS_DIR / "logs/opportunities.md"
MIN_FILES_FOR_REFACTOR_SUGGESTION = 3

"""
Auto-commit and push on session exit.

Automatically commits and pushes uncommitted changes when a Claude
Code session ends. Prevents work loss from forgetting to commit.

Features:
- Multi-repo support: Commits to main P repo and package repos independently
- Checks for uncommitted changes (git status --porcelain)
- Runs git add -A, commit with auto message, and push
- Exits silently if no changes or not in a git repo
- Handles push failures gracefully (local commit still happens)
- Package repos committed before main repo (hooks finalized last)
- Each repo commit is independent (failure in one doesn't block others)
- Analyzes changes for opportunities/optimizations
- Uses GitPython for in-process git operations (2-5x faster, no lockups)
"""


def run_git_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Fallback: Run a git command using subprocess (only if GitHelper unavailable)."""
    # Add CREATE_NO_WINDOW on Windows to prevent console flash
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    return subprocess.run(
        ["git"] + args, capture_output=True, text=True, cwd=str(cwd), creationflags=creation_flags
    )


def has_uncommitted_changes(cwd: Path) -> bool:
    """Check if there are uncommitted changes in the git repo."""
    if HAS_GIT_HELPER:
        try:
            git = GitHelper(cwd)
            return git.has_uncommitted_changes()
        except Exception:
            pass  # Fall back to subprocess

    # Fallback to subprocess
    result = run_git_command(["status", "--porcelain"], cwd)
    return bool(result.stdout.strip())


def is_git_repo(cwd: Path) -> bool:
    """Check if the current directory is a git repository."""
    if HAS_GIT_HELPER:
        try:
            git = GitHelper(cwd)
            return git.is_git_repo()
        except Exception:
            pass  # Fall back to subprocess

    # Fallback to subprocess
    result = run_git_command(["rev-parse", "--git-dir"], cwd)
    return result.returncode == 0


def is_worktree(cwd: Path) -> bool:
    """Check if the current directory is a git worktree (not the main repo)."""
    if HAS_GIT_HELPER:
        try:
            git = GitHelper(cwd)
            return git.is_worktree()
        except Exception:
            pass  # Fall back to subprocess

    # Fallback to subprocess
    # In a worktree, .git is a file (not a directory) pointing to .git/worktrees/<name>
    git_dir = cwd / ".git"
    if git_dir.is_file():
        # Verify it's actually a worktree file (contains "gitdir:" pointing to worktrees)
        try:
            content = git_dir.read_text().strip()
            if content.startswith("gitdir:") and "worktrees" in content:
                return True
        except OSError:
            pass
    return False


def add_duf_notification() -> None:
    """
    Add DUF (Did You Forget?) notification after auto-commit.

    Notification persists across CC restarts via global session_id.
    User sees 🔔 in statusline, runs /duf to review.
    """
    if not HAS_NOTIFICATIONS:
        return

    try:
        # Use empty session_id so notification persists across CC restarts
        add_notification(
            notification_type="duf",
            message="🔔 Auto-committed. Run /duf: Did you forget anything?",
            source="auto_commit",
            priority=1,
            session_id="",  # Global - shows in all terminals
        )
    except Exception:
        pass


def verify_hook_event_timing() -> str:
    """Pre-flight check: Verify correct understanding of hook event timing.

    Returns:
        Event timing description for logging/verification
    """
    # Stop event = after every response completes, NOT session end
    # This is critical for performance and behavior expectations
    return "after_every_response"


def add_brainstorm_notification() -> None:
    """
    Add brainstorm notification after auto-commit.

    Prompts user to run /brainstorm for heavyweight opportunity analysis.
    User sees 💡 in statusline. Persists across CC restarts.
    """
    if not HAS_NOTIFICATIONS:
        return

    try:
        # Use empty session_id so notification persists across CC restarts
        add_notification(
            notification_type="brainstorm",
            message="💡 Session complete. Run /brainstorm for opportunity analysis",
            source="auto_commit",
            priority=0,  # Lower than DUF
            session_id="",  # Global - shows in all terminals
        )
    except Exception:
        pass


def analyze_opportunities(cwd: Path) -> None:
    """
    Analyze committed changes for opportunities and optimizations.

    Detects patterns in changes and appends suggestions to opportunities.md.
    Runs after commit succeeds, non-blocking.
    """

    try:
        # Get list of changed files from last commit
        if HAS_GIT_HELPER:
            try:
                git = GitHelper(cwd)
                diff_output = git.rev_parse(["HEAD~1", "--name-status"])
            except Exception:
                diff_output = ""
        else:
            result = run_git_command(["diff", "HEAD~1", "--name-status"], cwd)
            diff_output = result.stdout if result.returncode == 0 else ""

        if not diff_output.strip():
            return

        changes = []
        for line in diff_output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                status, filepath = parts
                changes.append((status, filepath))

        if not changes:
            return

        # Detect patterns and generate opportunities
        opportunities = []

        # Pattern: New files created
        new_files = [f for s, f in changes if s == "A"]
        for f in new_files:
            if f.endswith(".py") and not f.startswith("test_") and "/tests/" not in f:
                opportunities.append(f"- [ ] **{f}**: Consider adding tests")
            if f.endswith(".md") and "command" in f.lower():
                opportunities.append(f"- [ ] **{f}**: Add to command index if user-facing")
            if f.endswith("hook.py") or f.endswith("_hook.py"):
                opportunities.append(f"- [ ] **{f}**: Verify hook is registered in settings.json")

        # Pattern: Config/settings changed
        config_files = [
            f
            for s, f in changes
            if any(x in f.lower() for x in ["config", "settings", ".json", ".yaml", ".toml"])
        ]
        for f in config_files:
            opportunities.append(f"- [ ] **{f}**: Validate config, consider migration notes")

        # Pattern: Multiple files in same directory
        dirs = [str(Path(f).parent) for s, f in changes if s in ("A", "M")]
        dir_counts = Counter(dirs)
        for d, count in dir_counts.items():
            if count >= MIN_FILES_FOR_REFACTOR_SUGGESTION and d != ".":
                opportunities.append(
                    f"- [ ] **{d}/**: {count} files changed - consider shared module or refactor"
                )

        # Pattern: Deleted files
        deleted = [f for s, f in changes if s == "D"]
        for f in deleted:
            opportunities.append(f"- [ ] **{f}** (deleted): Verify no stale references remain")

        # Pattern: Hook files modified
        hook_changes = [f for s, f in changes if "hook" in f.lower() and s == "M"]
        for f in hook_changes:
            opportunities.append(f"- [ ] **{f}**: Test hook behavior after changes")

        if not opportunities:
            return

        # Append to opportunities file
        OPPORTUNITIES_FILE.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Get commit hash
        if HAS_GIT_HELPER:
            try:
                git = GitHelper(cwd)
                commit_hash = git.rev_parse(["--short", "HEAD"]).strip()
            except Exception:
                commit_hash = "unknown"
        else:
            result = run_git_command(["rev-parse", "--short", "HEAD"], cwd)
            commit_hash = result.stdout.strip() if result.returncode == 0 else "unknown"

        entry = f"\n## {timestamp} ({commit_hash})\n\n"
        entry += "\n".join(opportunities) + "\n"

        with OPPORTUNITIES_FILE.open("a") as f:
            f.write(entry)

    except Exception:
        pass  # Don't fail commit due to opportunity analysis


def find_repos_with_changes(root: Path) -> list[Path]:
    """Find all git repos under root that have uncommitted changes.

    Returns list of repo paths sorted by type (packages first, main last).
    """
    repos = []

    # Check main repo
    if has_uncommitted_changes(root):
        repos.append(root)

    # Check package repos
    packages_dir = root / "packages"
    if packages_dir.exists():
        for package_dir in packages_dir.iterdir():
            if package_dir.is_dir() and (package_dir / ".git").exists():
                if has_uncommitted_changes(package_dir):
                    repos.append(package_dir)

    # Sort: main repo last (so hooks are finalized last)
    repos.sort(key=lambda r: r == root)
    return repos


def auto_commit_all() -> bool:
    """Auto-commit to all repos with uncommitted changes.

    Returns True if any changes were committed.
    """
    root = Path.cwd().parent.parent  # From hooks/ to P:/

    repos_with_changes = find_repos_with_changes(root)

    if not repos_with_changes:
        return False

    committed = False
    for repo in repos_with_changes:
        try:
            if auto_commit(repo):
                rel_path = repo.relative_to(root)
                print(f"[auto-commit] Committed to {rel_path}")
                committed = True
        except Exception as e:
            # Continue with other repos even if one fails
            _logger.warning(f"[auto-commit] Failed to commit to {rel_path}: {e}")

    return committed


def auto_commit(cwd: Path, do_push: bool = False) -> bool:
    """
    Auto-commit and push uncommitted changes.

    Args:
        cwd: Path to the git repo.
        do_push: Whether to push after commit. Default False (Stop hook use case).

    Returns:
        True if changes were committed, False otherwise.
    """
    # Check if we're in a git repo
    if not is_git_repo(cwd):
        return False

    # Skip auto-commit in worktrees (scratchpads, isolated environments)
    if is_worktree(cwd):
        return False

    # Check for uncommitted changes
    if not has_uncommitted_changes(cwd):
        return False

    # Stage all changes FIRST - commit message generation needs staged diff
    if HAS_GIT_HELPER:
        try:
            git = GitHelper(cwd)
            git.add(["-A"])
        except Exception:
            # Fall back to subprocess
            run_git_command(["add", "-A"], cwd)
    else:
        run_git_command(["add", "-A"], cwd)

    # Re-check for changes after staging (git add may have been no-op if clean)
    if not has_uncommitted_changes(cwd):
        return False

    # Analyze changes for meaningful commit message
    commit_msg = DEFAULT_COMMIT_MESSAGE

    # First try semantic commit message parser
    if HAS_COMMIT_MESSAGE_PARSER:
        try:
            commit_msg = generate_semantic_commit_message(str(cwd))
        except Exception:
            # Parser failed - continue to fallback options
            pass

    # Fall back to change analyzer if available
    if commit_msg == DEFAULT_COMMIT_MESSAGE and HAS_CHANGE_ANALYZER:
        try:
            analysis = analyze_changes(cwd)
            # During merge: commit with merge message, skip CHANGELOG (via elif)
            if analysis.get("skip_reason") == "merge":
                commit_msg = MERGE_COMMIT_MESSAGE
            # Use generated message if notable (and update CHANGELOG BEFORE commit)
            elif analysis["notable"]:
                commit_msg = f"auto-commit: {analysis['commit_message']}"
                # Update CHANGELOG BEFORE commit so it's included in the same commit
                changelog_path = cwd / ".claude" / "hooks" / "CHANGELOG.md"
                if not changelog_already_changed(cwd):
                    update_changelog(cwd, analysis["changelog_entry"], changelog_path)
                    # Re-stage CHANGELOG after update so it's included in commit
                    if HAS_GIT_HELPER:
                        try:
                            git = GitHelper(cwd)
                            git.add([str(changelog_path)])
                        except Exception:
                            run_git_command(["add", str(changelog_path)], cwd)
                    else:
                        run_git_command(["add", str(changelog_path)], cwd)
        except Exception:
            # Analysis failed - fall back to default message
            pass

    # Session-linked commit: tag with session ID for traceability
    session_id = get_session_id_for_commit()
    if session_id != "unknown":
        commit_msg = f"[{session_id}] {commit_msg}"

    # Commit with generated message (CHANGELOG already staged if notable)
    if HAS_GIT_HELPER:
        try:
            git = GitHelper(cwd)
            commit_success = git.commit(commit_msg)
        except Exception:
            commit_success = False
    else:
        commit_result = run_git_command(["commit", "-m", commit_msg], cwd)
        commit_success = commit_result.returncode == 0

    # Only add notifications if commit actually succeeded
    if commit_success:
        # DUF/brainstorm notifications removed - now triggered by session_end
        # via notification_decoupling module, not auto_commit
        # See: P:\__csf\src\features\modules\notification\notification_decoupling.py
        # add_duf_notification()
        # add_brainstorm_notification()
        analyze_opportunities(cwd)  # Log opportunities from this commit

    # Auto-push is DISABLED by default for Stop hook use case.
    # Stop hook should only commit locally - user pushes explicitly via /git when ready.
    # Pass do_push=True only if you want push alongside commit (e.g., SessionEnd cleanup).
    if do_push and not is_worktree(cwd):
        if HAS_GIT_HELPER:
            try:
                git = GitHelper(cwd)
                push_success = git.push()
                if not push_success:
                    print("[auto-commit] Changes committed locally (push failed)", file=sys.stdout)
            except Exception:
                print("[auto-commit] Changes committed locally (push failed)", file=sys.stdout)
        else:
            push_result = run_git_command(["push"], cwd)
            if push_result.returncode != 0:
                print("[auto-commit] Changes committed locally (push failed)", file=sys.stdout)

    return True


def run(data: dict) -> dict | None:
    """
    Stop hook entry point (in-process, via Stop_router).

    Runs auto-commit for all repos with uncommitted changes.
    Designed to be fast when nothing needs committing.
    """
    auto_commit_all()
    return {"continue": True}


@hook_main
def main() -> int:
    """
    CLI entry point for standalone invocation.
    """
    if auto_commit_all():
        print("[auto-commit] All repos committed and pushed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
