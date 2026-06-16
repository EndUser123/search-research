#!/usr/bin/env python3
"""
SessionStart Task Registration Hook

Ensures task identity is established on session start.

Flow:
1. Try to recover task via TaskIdentityManager (5-source chain)
2. If no task found, infer from context:
   - Check TASK_NAME environment variable
   - Check git branch for task mapping
   - Use current directory name as fallback
3. Register task via TaskIdentityManager.set_current_task()

This ensures checkpoints have meaningful names instead of "checkpoint_test".
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add hooks dir for imports
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

# Import TaskIdentityManager from CKS location or local fallback
_resolved = False
for _path in [
    HOOKS_DIR.parent.parent / "packages/.claude-marketplace/plugins/quickstop/skills",
    HOOKS_DIR.parent.parent / "__csf" / "src",
]:
    if _path.exists():
        if str(_path) not in sys.path:
            sys.path.insert(0, str(_path))
        try:
            from knowledge.systems.cks.integration.adapters.project_context.task_identity_manager import (
                TaskIdentityManager,
            )
            _resolved = True
            break
        except ImportError:
            if str(_path) in sys.path:
                sys.path.remove(str(_path))

if not _resolved:
    from __lib.task_identity_manager import TaskIdentityManager
from __lib.terminal_detection import detect_terminal_id


def ensure_state_files(project_root: Path) -> None:
    """Ensure required state files exist (create empty if missing)."""
    state_dir = project_root / ".claude"
    state_files = [
        state_dir / "progress.txt",
        state_dir / "next-steps.txt",
    ]

    missing = [f for f in state_files if not f.exists()]

    if missing:
        state_dir.mkdir(parents=True, exist_ok=True)
        for f in missing:
            f.write_text("")  # Create empty file
        # NOTE: stderr output suppressed - any stderr is treated as "hook error" by Claude Code
        # missing_names = [f.name for f in missing]
        # print(f"[SessionStart] Created missing state files: {', '.join(missing_names)}", file=sys.stderr)


def _get_git_executable() -> str:
    """Get the real git.exe path, bypassing git.bat wrappers.

    On Windows, if PATH contains git.bat before git.exe, subprocess will find
    the batch file which spawns PowerShell, causing console flash.

    This function finds the actual git.exe to avoid that.
    """
    if sys.platform != "win32":
        return "git"

    # Try to find git.exe directly
    git_exe = shutil.which("git.exe")
    if git_exe:
        return git_exe

    # Fallback to common Git for Windows installation paths
    common_paths = [
        "C:/Program Files/Git/mingw64/bin/git.exe",
        "C:/Program Files/Git/cmd/git.exe",
        "C:/Program Files/Git/bin/git.exe",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path

    # Ultimate fallback - hope git in PATH works
    return "git"


def infer_task_from_context(project_root: Path) -> str | None:
    """Infer task name from project context."""
    # Method 1: Environment variable (already checked by get_current_task, but check again)
    task_name = os.getenv("TASK_NAME")
    if task_name:
        return task_name

    # Method 2: Git branch mapping
    try:
        git_exe = _get_git_executable()
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [git_exe, "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5,
            creationflags=creation_flags,
        )
        branch = result.stdout.strip()
        if branch:
            # Load task-worktree mapping
            mapping_file = project_root / ".claude" / "task-worktree-mapping.json"
            if mapping_file.exists():
                import json as json_mod
                mapping = json_mod.loads(mapping_file.read_text())
                if branch in mapping:
                    return mapping[branch]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Method 3: Current directory name (if not root)
    cwd = Path.cwd()
    if cwd != project_root and cwd.is_relative_to(project_root):
        # Use relative path as task name
        rel_path = cwd.relative_to(project_root)
        # Convert path to task name: "features/cks" -> "features-cks"
        return str(rel_path).replace("/", "-").replace("\\", "-")

    # Method 4: Use "adhoc" for unstructured work
    return "adhoc"


@hook_main
def main():
    """Register task on session start."""
    # Read hook input
    input_text = sys.stdin.read().strip()
    hook_input = {}
    if input_text:
        try:
            hook_input = json.loads(input_text)
        except json.JSONDecodeError:
            pass

    project_root = Path("P:/")
    terminal_id = detect_terminal_id()

    # Ensure state files exist (prevents file-not-found errors)
    ensure_state_files(project_root)

    # Initialize task manager
    task_mgr = TaskIdentityManager(project_root=project_root, terminal_id=terminal_id)

    # Try to recover existing task
    existing_task = task_mgr.get_current_task()

    if existing_task:
        # Task already exists, no registration needed
        # NOTE: stderr output suppressed - any stderr is treated as "hook error" by Claude Code
        # print(f'[SessionStart] Task already registered: {existing_task}', file=sys.stderr)
        print("{}")
        sys.exit(0)

    # No task found - infer from context
    inferred_task = infer_task_from_context(project_root)

    if not inferred_task:
        print("{}")
        sys.exit(0)

    # Register the inferred task
    success = task_mgr.set_current_task(inferred_task)

    if success:
        # NOTE: stderr output suppressed - any stderr is treated as "hook error" by Claude Code
        # print(f'[SessionStart] Registered task: {inferred_task}', file=sys.stderr)
        print("{}")
        sys.exit(0)
    else:
        # NOTE: stderr output suppressed - any stderr is treated as "hook error" by Claude Code
        # print('[SessionStart] Failed to register task', file=sys.stderr)
        print("{}")
        sys.exit(0)

if __name__ == "__main__":
    main()
