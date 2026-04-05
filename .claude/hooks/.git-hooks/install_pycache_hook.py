#!/usr/bin/env python3
"""
Install Git Pre-Commit Hook for PyCache Cleanup

Installs the pre-commit hook that automatically clears Python bytecode
caches before committing. This prevents stale .pyc files from being
committed and ensures hooks always run with fresh bytecode.

Usage:
    python install_pycache_hook.py [--uninstall]

Options:
    --uninstall  Remove the installed pre-commit hook

Integration:
    Run once after cloning repository
    Re-run after git pull if hook is overwritten
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    """Install or uninstall the pre-commit hook."""
    # Determine script location
    script_dir = Path(__file__).resolve().parent
    hook_source = script_dir / "pre-commit-clear-pycache"

    # Find .git directory
    # Start from script dir and search upward
    search_dir = script_dir
    git_dir = None

    for parent in [search_dir, *search_dir.parents]:
        if (parent / ".git").is_dir():
            git_dir = parent / ".git"
            break
        if (parent / "HEAD").is_file() and (parent / "refs").is_dir():
            # Bare repo or separate git dir
            git_dir = parent
            break

    if not git_dir:
        print("Error: Could not find .git directory", file=sys.stderr)
        return 1

    hooks_dir = git_dir / "hooks"
    hook_target = hooks_dir / "pre-commit"

    # Check for --uninstall flag
    if "--uninstall" in sys.argv:
        if hook_target.exists():
            # Check if it's our hook
            content = hook_target.read_text(encoding="utf-8")
            if "pre-commit-clear-pycache" in content:
                hook_target.unlink()
                print(f"Removed pre-commit hook from {hook_target}")
                return 0
            else:
                print(
                    "Warning: Existing pre-commit hook doesn't match ours",
                    file=sys.stderr,
                )
                print("Skipping uninstall to avoid breaking other hooks", file=sys.stderr)
                return 1
        else:
            print("No pre-commit hook installed")
            return 0

    # Install hook
    if not hook_source.exists():
        print(f"Error: Hook source not found at {hook_source}", file=sys.stderr)
        return 1

    # Check for existing hook
    if hook_target.exists():
        # Warn but don't overwrite
        print(
            f"Warning: pre-commit hook already exists at {hook_target}",
            file=sys.stderr,
        )
        print("Skipping installation to avoid overwriting existing hooks", file=sys.stderr)
        print("To replace manually: cp pre-commit-clear-pycache .git/hooks/pre-commit", file=sys.stderr)
        return 1

    # Copy hook
    hooks_dir.mkdir(exist_ok=True)
    shutil.copy(hook_source, hook_target)

    # Make executable
    hook_target.chmod(0o755)

    print(f"Installed pre-commit hook to {hook_target}")
    print("PyCache cleanup will run automatically before each commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
