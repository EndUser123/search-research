#!/usr/bin/env python3
"""
Worktree Helper Library

Utilities for detecting and managing git worktrees in Claude Code workflows.

This module provides functions to:
- Detect the current worktree path
- Parse git worktree list output
- Validate worktree boundaries
- Check for cross-worktree file access

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional


def get_current_worktree(cwd: Optional[Path] = None) -> Path:
    """Get the current worktree path for the given directory.

    Determines which worktree the current working directory belongs to by:
    1. Checking if we're in the main repo (no .git file)
    2. Checking if we're in a worktree (has .git file with gitdir reference)
    3. Parsing the worktree path from git worktree list

    Args:
        cwd: Current working directory. Defaults to Path.cwd().

    Returns:
        Path to the current worktree root directory.

    Raises:
        ValueError: If not in a git repository
        RuntimeError: If worktree cannot be determined

    Examples:
        >>> get_current_worktree()
        Path('P:/')
        >>> get_current_worktree(Path('P:/.claude/worktrees/ai-task-1'))
        Path('P:/.claude/worktrees/ai-task-1')
    """
    if cwd is None:
        cwd = Path.cwd()

    # Check if we're in a git repository
    if not (cwd / ".git").exists():
        # Try traversing up to find repo root
        for parent in [cwd, *cwd.parents]:
            if (parent / ".git").exists():
                cwd = parent
                break
        else:
            raise ValueError(f"Not in a git repository: {cwd}")

    # Check if we're in main repo (has .git directory, not .git file)
    git_dir = cwd / ".git"
    if git_dir.is_dir():
        # We're in the main repository (has .git directory, not .git file)
        # Traverse up to find the repo root (in case we're in a subdirectory)
        repo_root = cwd
        while repo_root != repo_root.parent and (repo_root.parent / ".git").exists():
            repo_root = repo_root.parent

        return repo_root

    # Check if we're in a worktree (has .git file)
    if git_dir.is_file():
        try:
            # .git file contains: "gitdir: <path>"
            content = git_dir.read_text().strip()
            if content.startswith("gitdir:"):
                # Note: gitdir path extracted but not used - we traverse up instead
                # This preserves the gitdir parsing logic for potential future use

                # The gitdir is relative to .git file location
                # Worktree root is the parent of the .git file
                worktree_root = cwd

                # Traverse up until we find .git file (which marks worktree root)
                while worktree_root != worktree_root.parent:
                    if (worktree_root / ".git").is_file():
                        return worktree_root
                    worktree_root = worktree_root.parent

                # Fallback: use git worktree list
                return _get_worktree_from_git_list(cwd)

        except OSError as e:
            raise RuntimeError(f"Failed to read .git file: {e}")

    # Fallback: use git worktree list
    return _get_worktree_from_git_list(cwd)


def _get_worktree_from_git_list(cwd: Path) -> Path:
    """Get worktree path by parsing 'git worktree list' output.

    Args:
        cwd: Current working directory.

    Returns:
        Path to the worktree containing cwd.

    Raises:
        RuntimeError: If worktree cannot be determined.
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )

        if result.returncode != 0:
            raise RuntimeError(f"git worktree list failed: {result.stderr}")

        # Parse porcelain output
        # Format: "worktree /path/to/worktree\nHEAD <commit>\nbranch refs/heads/branch\n..."
        current_worktree = None
        worktree_path = None

        for line in result.stdout.split("\n"):
            if not line:
                continue

            if line.startswith("worktree "):
                # New worktree entry
                worktree_path = Path(line.split(" ", 1)[1].strip())

                # Check if cwd is within this worktree
                try:
                    cwd.resolve().relative_to(worktree_path.resolve())
                    current_worktree = worktree_path
                except ValueError:
                    # cwd is not within this worktree
                    pass

        if current_worktree:
            return current_worktree

        # Default: return git root (main repo)
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )

        if result.returncode == 0:
            return Path(result.stdout.strip())

        raise RuntimeError("Cannot determine worktree path")

    except subprocess.TimeoutExpired:
        raise RuntimeError("git worktree list timed out")
    except OSError as e:
        raise RuntimeError(f"Failed to run git worktree list: {e}")


def list_all_worktrees(repo_root: Optional[Path] = None) -> list[dict[str, str]]:
    """List all worktrees in the repository.

    Args:
        repo_root: Path to git repository root. If None, detects from cwd.

    Returns:
        List of worktree info dicts with keys:
        - 'path': Worktree path
        - 'branch': Branch name (if detached, HEAD commit)
        - 'is_bare': True if bare worktree
        - 'is_detached': True if HEAD is detached

    Examples:
        >>> list_all_worktrees()
        [
            {'path': 'P:/', 'branch': 'refs/heads/main', 'is_bare': False, 'is_detached': False},
            {'path': 'P:/.claude/worktrees/ai-task-1', 'branch': 'refs/heads/ai/fix-bug', 'is_bare': False, 'is_detached': False}
        ]
    """
    if repo_root is None:
        repo_root = Path.cwd()

    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=repo_root
        )

        if result.returncode != 0:
            return []

        worktrees = []
        current_worktree = {}

        for line in result.stdout.split("\n"):
            if not line:
                continue

            parts = line.split(" ", 1)
            if len(parts) != 2:
                continue

            key, value = parts

            if key == "worktree":
                # Save previous worktree if exists
                if current_worktree:
                    worktrees.append(current_worktree)

                # Start new worktree
                current_worktree = {"path": value}

            elif key == "HEAD":
                current_worktree["head"] = value

            elif key == "branch":
                current_worktree["branch"] = value

            elif key == "bare":
                current_worktree["is_bare"] = True

            elif key == "detached":
                current_worktree["is_detached"] = True

        # Add last worktree
        if current_worktree:
            worktrees.append(current_worktree)

        return worktrees

    except (subprocess.TimeoutExpired, OSError):
        return []


def is_cross_worktree_access(
    current_cwd: Path,
    target_file: str,
    current_worktree_path: Optional[Path] = None
) -> bool:
    """Check if accessing target_file would cross worktree boundaries.

    Args:
        current_cwd: Current working directory.
        target_file: Target file path (can be relative or absolute).
        current_worktree_path: Current worktree path. If None, detects automatically.

    Returns:
        True if target_file is in a different worktree, False otherwise.

    Examples:
        >>> is_cross_worktree_access(Path('P:/.claude/worktrees/ai-1'), '../main-repo/file.py')
        True
        >>> is_cross_worktree_access(Path('P:/.claude/worktrees/ai-1'), './local_file.py')
        False
    """
    if current_worktree_path is None:
        current_worktree_path = get_current_worktree(current_cwd)

    # Resolve target file to absolute path
    target_abs = (current_cwd / target_file).resolve()

    # Check if target is within current worktree
    try:
        target_abs.relative_to(current_worktree_path.resolve())
        return False  # Within current worktree
    except ValueError:
        return True  # Outside current worktree


def validate_git_command_for_worktree(command: str, cwd: Optional[Path] = None) -> dict[str, any]:
    """Validate a git command for worktree boundary violations.

    Parses git commands that operate on files (restore, checkout, diff, etc.)
    and checks if the target files are within the current worktree.

    Args:
        command: Git command string to validate.
        cwd: Current working directory. Defaults to Path.cwd().

    Returns:
        Dict with validation result:
        - 'valid': True if command is safe, False if cross-worktree access detected
        - 'reason': Explanation of why command is invalid (if valid=False)
        - 'current_worktree': Current worktree path
        - 'target_files': List of target file paths
        - 'violations': List of files outside current worktree

    Examples:
        >>> validate_git_command_for_worktree('git restore ../main/file.py')
        {
            'valid': False,
            'reason': 'Target file is in different worktree',
            'current_worktree': Path('P:/.claude/worktrees/ai-1'),
            'target_files': [Path('../main/file.py')],
            'violations': [Path('P:/main/file.py')]
        }
    """
    if cwd is None:
        cwd = Path.cwd()

    # Get current worktree
    try:
        current_worktree = get_current_worktree(cwd)
    except (ValueError, RuntimeError) as e:
        # Can't determine worktree - allow command (fail open)
        return {
            "valid": True,
            "reason": f"Cannot determine worktree: {e}",
            "current_worktree": None,
            "target_files": [],
            "violations": []
        }

    # Parse target files from command
    # Patterns to match:
    # - git restore <file> [<file>...]
    # - git checkout -- <file> [<file>...]
    # - git checkout <commit> -- <file> [<file>...]
    # - git diff <file> [<file>...]
    target_files = []

    # Match: git restore file1 file2 ...
    match = re.match(r'git\s+restore\s+(.+)$', command)
    if match:
        files_part = match.group(1).strip()
        # Split on whitespace, but respect quotes
        # Simple version: split on whitespace
        target_files = files_part.split()

    # Match: git checkout -- file1 file2 ...
    match = re.match(r'git\s+checkout\s+.*?--\s+(.+)$', command)
    if match:
        files_part = match.group(1).strip()
        target_files = files_part.split()

    # Match: git checkout <commit> -- file1 file2 ...
    match = re.match(r'git\s+checkout\s+\S+\s+--\s+(.+)$', command)
    if match:
        files_part = match.group(1).strip()
        target_files = files_part.split()

    if not target_files:
        # No target files found - command is safe
        return {
            "valid": True,
            "reason": "No target files in command",
            "current_worktree": current_worktree,
            "target_files": [],
            "violations": []
        }

    # Check each target file
    violations = []
    for target_file in target_files:
        if is_cross_worktree_access(cwd, target_file, current_worktree):
            # Resolve to absolute path for reporting
            target_abs = (cwd / target_file).resolve()
            violations.append(target_abs)

    if violations:
        return {
            "valid": False,
            "reason": f"Cross-worktree access: {len(violations)} file(s) outside current worktree",
            "current_worktree": current_worktree,
            "target_files": target_files,
            "violations": violations
        }

    return {
        "valid": True,
        "reason": "All target files within current worktree",
        "current_worktree": current_worktree,
        "target_files": target_files,
        "violations": []
    }


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "get_current_worktree",
    "list_all_worktrees",
    "is_cross_worktree_access",
    "validate_git_command_for_worktree",
]
