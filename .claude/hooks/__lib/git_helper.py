"""
Git helper module using GitPython for in-process git operations.

Benefits over subprocess:
- No subprocess.spawn() overhead (2-5x faster)
- No process contention/lockups with multiple terminals
- Direct Python object access to git state
- Better error handling and return values

Usage:
    from git_helper import GitHelper

    git = GitHelper(cwd=Path.cwd())
    if git.has_uncommitted_changes():
        git.add(["-A"])
        git.commit("auto-commit: session end")
        git.push()
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import git as gitpython
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False


class GitHelper:
    """Helper class for git operations using GitPython (in-process)."""

    def __init__(self, cwd: Path):
        """Initialize git helper for a directory.

        Args:
            cwd: Working directory for git operations
        """
        self.cwd = Path(cwd)
        self._repo: gitpython.Repo | None = None

    @property
    def repo(self) -> gitpython.Repo:
        """Lazy-load git repository."""
        if self._repo is None:
            if not HAS_GITPYTHON:
                raise ImportError("GitPython is not installed. Run: pip install GitPython")
            self._repo = gitpython.Repo(self.cwd)
        return self._repo

    def is_git_repo(self) -> bool:
        """Check if the current directory is a git repository."""
        if not HAS_GITPYTHON:
            return False
        try:
            # Try to open the repo - will raise exception if not a git repo
            _ = self.repo
            return True
        except (gitpython.InvalidGitRepositoryError, gitpython.NoSuchPathError):
            return False

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes in the git repo."""
        if not HAS_GITPYTHON:
            # Fallback to subprocess if gitpython not available
            return self._subprocess_has_uncommitted_changes()

        try:
            return self.repo.is_dirty(untracked_files=True)
        except Exception:
            return False

    def is_worktree(self) -> bool:
        """Check if the current directory is a git worktree (not the main repo)."""
        if not HAS_GITPYTHON:
            # Fallback to subprocess if gitpython not available
            return self._subprocess_is_worktree()

        try:
            # Check if .git is a file (indicating a worktree)
            git_dir = self.cwd / ".git"
            if git_dir.is_file():
                return True

            # Compare git dir with toplevel
            toplevel = Path(self.repo.working_dir)
            return toplevel != self.cwd
        except Exception:
            return False

    def add(self, args: list[str]) -> bool:
        """Stage files for commit (git add).

        Args:
            args: Arguments to pass to git add (e.g., ["-A"] or ["file.txt"])

        Returns:
            True if successful, False otherwise
        """
        if not HAS_GITPYTHON:
            return self._subprocess_git_command(["add"] + args)

        try:
            # Handle special cases
            if "-A" in args or "--all" in args:
                # Stage all changes
                self.repo.git.add(A=True)
            elif "-u" in args or "--update" in args:
                # Stage tracked files only
                self.repo.index.update([])
            else:
                # Stage specific files
                self.repo.git.add(args)
            return True
        except Exception:
            return False

    def commit(self, message: str, allow_empty: bool = False) -> bool:
        """Create a commit (git commit).

        Args:
            message: Commit message
            allow_empty: Whether to allow empty commits

        Returns:
            True if successful, False otherwise
        """
        if not HAS_GITPYTHON:
            return self._subprocess_git_command(["commit", "-m", message])

        try:
            self.repo.index.commit(message, allow_empty=allow_empty)
            return True
        except Exception:
            return False

    def push(self, args: list[str] | None = None) -> bool:
        """Push commits to remote (git push).

        Args:
            args: Optional arguments to pass to git push

        Returns:
            True if successful, False otherwise
        """
        if not HAS_GITPYTHON:
            return self._subprocess_git_command(["push"] + (args or []))

        try:
            if args:
                self.repo.git.push(args)
            else:
                # Push to current branch's remote
                origin = self.repo.remote(name='origin')
                origin.push()
            return True
        except Exception:
            return False

    def status(self) -> str:
        """Get git status output.

        Returns:
            Git status output as string
        """
        if not HAS_GITPYTHON:
            result = self._subprocess_git_command(["status", "--porcelain"], capture_output=True)
            return result.stdout if result else ""

        try:
            # Use git command for compatibility with existing parsers
            return self.repo.git.status(porcelain=True)
        except Exception:
            return ""

    def rev_parse(self, args: list[str]) -> str:
        """Run git rev-parse.

        Args:
            args: Arguments to pass to git rev-parse

        Returns:
            Output from git rev-parse
        """
        if not HAS_GITPYTHON:
            result = self._subprocess_git_command(["rev-parse"] + args, capture_output=True)
            return result.stdout if result else ""

        try:
            return self.repo.git.rev_parse(args)
        except Exception:
            return ""

    # Fallback subprocess methods for when gitpython is not available

    def _subprocess_has_uncommitted_changes(self) -> bool:
        """Fallback: Check for uncommitted changes using subprocess."""
        result = self._subprocess_git_command(["status", "--porcelain"], capture_output=True)
        return bool(result.stdout.strip() if result else False)

    def _subprocess_is_worktree(self) -> bool:
        """Fallback: Check if worktree using subprocess."""
        git_dir = self.cwd / ".git"
        if git_dir.is_file():
            return True

        result = self._subprocess_git_command(["rev-parse", "--show-toplevel"], capture_output=True)
        if not result or result.returncode != 0:
            return False

        toplevel = Path(result.stdout.strip())
        return toplevel != self.cwd

    def _subprocess_git_command(
        self,
        args: list[str],
        capture_output: bool = False
    ) -> subprocess.CompletedProcess | None:
        """Fallback: Run git command using subprocess.

        Args:
            args: Git command arguments
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess result or None if failed
        """
        import subprocess

        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                ["git"] + args,
                capture_output=capture_output,
                text=True,
                cwd=str(self.cwd),
                creationflags=creation_flags
            )
            return result
        except Exception:
            return None


def create_git_helper(cwd: Path) -> GitHelper:
    """Factory function to create GitHelper instance.

    Args:
        cwd: Working directory for git operations

    Returns:
        GitHelper instance
    """
    return GitHelper(cwd)
