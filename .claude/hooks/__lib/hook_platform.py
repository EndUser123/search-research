#!/usr/bin/env python3
"""Platform detection utilities for skill-based hooks.

This module provides cross-platform hook execution for Claude Code skills.
It automatically detects the operating system and executes the appropriate
shell script (PowerShell on Windows, bash on Unix/Linux/macOS).

Exit Code Conventions:
    0: Pass - action allowed
    1: Advisory warning - action allowed, message shown
    2: Block - action denied, user must retry
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_platform_hook(
    script_dir: Path,
    script_name: str,
    env: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, str, str]:
    """Run appropriate script for current platform.

    Automatically detects the operating system and executes the appropriate
    shell script (.ps1 for Windows PowerShell, .sh for Unix/Linux/macOS bash).

    Args:
        script_dir: Directory containing hook scripts
        script_name: Base name of script (without extension)
        env: Environment variables to pass to script (defaults to os.environ)
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (exit_code, stdout, stderr)

    Raises:
        FileNotFoundError: If script file doesn't exist
        subprocess.TimeoutExpired: If script execution exceeds timeout
    """
    # Prepare environment
    script_env = os.environ.copy()
    if env:
        script_env.update(env)

    # Detect platform and select appropriate script
    if sys.platform == "win32":
        script_path = script_dir / f"{script_name}.ps1"
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ]
    else:
        script_path = script_dir / f"{script_name}.sh"
        cmd = ["bash", str(script_path)]

    # Verify script exists
    if not script_path.exists():
        raise FileNotFoundError(f"Hook script not found: {script_path}")

    # Execute script
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=script_env,
    )

    return result.returncode, result.stdout, result.stderr


def scope_guard_check(
    project_root: Path,
    state_dir_pattern: str,
    terminal_id: str | None = None,
) -> tuple[bool, str]:
    """Check if skill was actually used (state directory exists).

    This prevents running verification hooks when the skill was never invoked,
    reducing unnecessary overhead and false positives.

    Args:
        project_root: Project root directory
        state_dir_pattern: Pattern for state directory (use {terminal_id} placeholder)
        terminal_id: Terminal ID for multi-terminal isolation

    Returns:
        Tuple of (should_skip, reason)
        - should_skip=True: Hook should be skipped (skill not used)
        - should_skip=False: Hook should run (skill was used)

    Examples:
        >>> should_skip, reason = scope_guard_check(
        ...     Path("/project"),
        ...     "gto-state-{terminal_id}",
        ...     "term_123"
        ... )
        >>> if should_skip:
        ...     print(reason)  # "GTO was not used, skipping verification"
    """
    # Format state directory path
    if terminal_id:
        state_dir_name = state_dir_pattern.format(terminal_id=terminal_id)
    else:
        # Fallback: check for any matching state directory
        state_dir_name = state_dir_pattern.format(terminal_id="*")

    state_dir = project_root / ".evidence" / state_dir_name

    # If terminal_id was provided, check exact directory
    if terminal_id:
        if not state_dir.exists():
            return (
                True,
                f"Scope guard: State directory not found ({state_dir.name}), skill was not used",
            )
        return False, "Scope guard: State directory found, running verification"

    # If no terminal_id, check for any matching directory
    if state_dir.parent.exists():
        matching_dirs = list(state_dir.parent.glob(state_dir_name))
        if matching_dirs:
            return (
                False,
                f"Scope guard: Found {len(matching_dirs)} state directory(s), running verification",
            )
        return True, "Scope guard: No state directories found, skill was not used"

    return True, "Scope guard: .evidence directory not found, skill was not used"
