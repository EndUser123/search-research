#!/usr/bin/env python3
"""Git worktree sync: Pull from main, push to main, auto-resolve conflicts."""

import subprocess
import sys
from pathlib import Path

# Constants
_MAIN_BRANCH_NAME = "main"
_MAIN_ROOT_PATH = "P:/"
_COMMIT_MESSAGE_PREFIX = "wip: auto-commit"
_NO_EXT_KEY = "no_ext"

# Git commands
_GIT_CMD_SHOW_CURRENT = "git branch --show-current"
_GIT_CMD_STATUS_SHORT = "git status --short"
_GIT_CMD_ADD_ALL = "git add -A"
_GIT_CMD_DIFF_CACHED_NAME_ONLY = "git diff --cached --name-only"
_GIT_CMD_DIFF_CACHED_NUMSTAT = "git diff --cached --numstat"
_GIT_CMD_REV_LIST_AHEAD = "git rev-list --count HEAD..@{u}"
_GIT_CMD_PUSH_ORIGIN_MAIN = "git push origin main"
_GIT_CMD_REBASE_TEMPLATE = "git rebase {}"
_GIT_CMD_MERGE_TEMPLATE = "git merge {} --no-edit"

def run(cmd, cwd=None, check: bool = True, silent: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    """Run shell command and return result.

    Args:
        cmd: Command string to execute, or list of arguments
        cwd: Working directory for command execution
        check: If True, exit on non-zero return code
        silent: If True, suppress stderr output on error
        shell: If True, use shell=True (for complex commands with spaces/quotes)

    Returns:
        CompletedProcess with stdout/stderr

    Raises:
        SystemExit: If check=True and command returns non-zero exit code
    """
    kwargs = {"cwd": cwd, "capture_output": True, "text": True, "shell": shell}
    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        print(f"✗ Sync failed: {cmd}")
        if not silent:
            print(result.stderr)
        sys.exit(1)
    return result

def _generate_contextual_message(cwd=None) -> str:
    """Generate contextual commit message based on staged changes.

    Analyzes staged files to create a descriptive commit message including:
    - Total file count
    - File type breakdown (e.g., "3 py, 2 md")
    - Line change summary (e.g., "[+15/-3]")

    Args:
        cwd: Working directory for git commands (optional)

    Returns:
        Formatted commit message string
    """
    # Get list of staged files
    result = run(_GIT_CMD_DIFF_CACHED_NAME_ONLY, cwd=cwd)
    changed_files = [f for f in result.stdout.strip().split('\n') if f]
    file_count = len(changed_files)

    # Count files by type
    file_types = {}
    for file in changed_files:
        path = Path(file)
        ext = path.suffix[1:] if path.suffix else _NO_EXT_KEY
        file_types[ext] = file_types.get(ext, 0) + 1

    # Build type breakdown string
    type_parts = [f"{count} {ext}" for ext, count in file_types.items()]
    type_breakdown = ", ".join(type_parts)

    # Get line changes summary
    additions, deletions = _parse_line_changes(run(_GIT_CMD_DIFF_CACHED_NUMSTAT, cwd=cwd))

    # Build the commit message
    message = f"{_COMMIT_MESSAGE_PREFIX} {file_count} files ({type_breakdown}) before sync"

    # Add line changes if any
    if additions > 0 or deletions > 0:
        message += f" [+{additions}/-{deletions}]"

    return message


def _parse_line_changes(diff_result: subprocess.CompletedProcess) -> tuple[int, int]:
    """Parse git numstat output to extract addition and deletion counts.

    Args:
        diff_result: CompletedProcess from 'git diff --cached --numstat'

    Returns:
        Tuple of (additions, deletions) as integers
    """
    additions = 0
    deletions = 0
    for line in diff_result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 2:
                try:
                    additions += int(parts[0]) if parts[0] != '-' else 0
                    deletions += int(parts[1]) if parts[1] != '-' else 0
                except ValueError:
                    pass
    return additions, deletions


def extract_added_lines(diff_output: str) -> dict[str, list[str]]:
    """Parse git diff output to extract added lines by file.

    Args:
        diff_output: Raw git diff output string

    Returns:
        Dictionary mapping file paths to lists of added line contents
    """
    added = {}
    current_file = None

    for line in diff_output.split('\n'):
        if line.startswith('+++'):
            # Extract file path from +++ b/path/to/file
            parts = line.split()
            if len(parts) >= 2:
                # Remove leading 'b/' if present
                file_path = parts[1][2:] if parts[1].startswith('b/') else parts[1]
                current_file = file_path
                added[current_file] = []
        elif line.startswith('+') and not line.startswith('+++'):
            # This is an added line (not the file header)
            if current_file is not None:
                added[current_file].append(line[1:])

    return added


def verify_merge_propagated(worktree: Path, main_root: Path, verbose: bool = False) -> bool:
    """Verify that worktree changes actually exist in main repo after merge.

    This prevents the issue where commits merge successfully but semantic
    changes don't appear in main due to code structure differences.

    Args:
        worktree: Path to worktree directory
        main_root: Path to main repo root directory
        verbose: If True, print detailed verification info

    Returns:
        True if all changes found in main, False otherwise
    """
    # Get what changed in worktree (last commit)
    result = run(["git", "diff", "HEAD~1", "HEAD"], cwd=worktree, check=False)
    if result.returncode != 0:
        if verbose:
            print("No changes to verify (worktree has no new commits)")
        return True

    worktree_diff = result.stdout
    added_lines = extract_added_lines(worktree_diff)

    if not added_lines:
        if verbose:
            print("No added lines to verify")
        return True

    if verbose:
        print(f"Verifying {len(added_lines)} changed files propagated to main...")

    # Check if those lines exist in main repo
    for file_path, lines in added_lines.items():
        if not lines:
            continue  # Skip files with no actual additions

        # Resolve file path relative to main root
        main_file = main_root / file_path

        if not main_file.exists():
            print(f"⚠️  File not in main: {file_path}")
            return False

        content = main_file.read_text()
        for line in lines:
            if line not in content:
                print(f"⚠️  Change not found in {file_path}:")
                print(f"   Expected: {line.strip()}")
                return False

    if verbose:
        print("✓ All changes verified in main repo")
    return True

def git_sync(verbose: bool = False, verify: bool = True) -> None:
    """Sync worktree with main branch.

    Workflow:
    1. Auto-commit any uncommitted changes with contextual message
    2. If on main branch: push to origin if ahead, otherwise skip sync
    3. If on worktree branch: rebase onto main, then merge to main
    4. Verify changes propagated to main (unless --no-verify)

    Args:
        verbose: If True, print detailed command output
        verify: If True, verify merge propagated to main after sync
    """
    worktree = Path.cwd()
    main_root = Path(_MAIN_ROOT_PATH)
    silent_arg = not verbose

    # Get current branch
    current = run(_GIT_CMD_SHOW_CURRENT, cwd=worktree).stdout.strip()

    # 1. Auto-commit if needed (check first to avoid exit code 1)
    status = run(_GIT_CMD_STATUS_SHORT, cwd=worktree, silent=silent_arg).stdout.strip()

    if status:
        run(_GIT_CMD_ADD_ALL, cwd=worktree, silent=silent_arg)
        message = _generate_contextual_message(worktree)
        # Use list-based command to avoid shell=True with cwd issue on Windows
        run(["git", "commit", "-m", message], cwd=worktree, silent=silent_arg)

    # 2. Skip sync operations if already on main branch, but push if ahead
    if current == _MAIN_BRANCH_NAME:
        # Check if ahead of origin
        ahead_result = run(_GIT_CMD_REV_LIST_AHEAD, cwd=worktree, silent=silent_arg)
        ahead_count = int(ahead_result.stdout.strip())
        if ahead_count > 0:
            run(_GIT_CMD_PUSH_ORIGIN_MAIN, cwd=worktree, silent=silent_arg)
            print("Pushed to origin")
        else:
            print("Already up to date")
        return

    # 3. Rebase onto main
    run(_GIT_CMD_REBASE_TEMPLATE.format(_MAIN_BRANCH_NAME), cwd=worktree, silent=silent_arg)

    # 4. Merge to main
    run(_GIT_CMD_MERGE_TEMPLATE.format(current), cwd=main_root, silent=silent_arg)

    # 5. Verify changes propagated to main
    if verify:
        if not verify_merge_propagated(worktree, main_root, verbose=verbose):
            print("❌ Verification failed - changes may not have propagated to main")
            print("   Run with --verbose to see details, or --no-verify to skip")
            sys.exit(1)

    print("✓ Sync complete")

if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    verify = "--no-verify" not in sys.argv
    git_sync(verbose=verbose, verify=verify)
