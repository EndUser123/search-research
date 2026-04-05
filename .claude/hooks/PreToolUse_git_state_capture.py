#!/usr/bin/env python3
"""
PreToolUse Hook: Git State Capture for Cross-Agent Isolation

Captures git status BEFORE Bash commands that could modify .py files.
This allows PostToolUse_bash_syntax_gate.py to compute only the files
actually modified by the current command (delta), preventing cross-agent
contamination where one agent's syntax errors block other agents' commands.

Run: PreToolUse (before Bash tool execution)
Timeout: 5 seconds
Exit Codes:
  - 0: Always allow (this hook only captures state, never blocks)

Author: Claude Code
Date: 2026-03-25
Related: plan-fix-bash-syntax-gate-cross-agent-contamination.md
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# Add hooks lib to path
hooks_dir = Path(__file__).resolve().parent
hooks_lib = hooks_dir / "__lib"
sys.path.insert(0, str(hooks_lib))

from shared_utils import load_state, save_state

# State file for pre-command git status
GIT_STATE_KEY = "bash_git_pre_state"


def _get_terminal_id() -> str:
    """Get terminal ID from environment or generate a hash of cwd."""
    # Try to get from environment
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")
    if terminal_id:
        return terminal_id

    # Fallback: hash of current working directory
    cwd = os.getcwd()
    return hashlib.md5(cwd.encode()).hexdigest()[:8]


def _get_session_id() -> str:
    """Get session ID from environment."""
    return os.environ.get("CLAUDE_SESSION_ID", "default")


def _could_modify_py_files(command: str) -> bool:
    """Check if command could modify .py files.

    Uses the same pattern matching as check_python_file_edits().
    """
    command_lower = command.lower()

    py_modifying_patterns = [
        '.py"',
        ".py'",
        ".py>",
        ".py|",
        ".py&",
        "*.py",
        ".py ",
        " .py",
        "write ",
        "echo ",
        "printf ",
        "cat ",
        "tee ",
        "sed ",
        "awk ",
        "perl ",
        ">file",
        ">>file",
        "python ",
        "python3 ",
        "touch ",
    ]

    heredoc_patterns = ["<<"]
    has_heredoc = any(pattern in command_lower for pattern in heredoc_patterns)

    return any(pattern in command_lower for pattern in py_modifying_patterns) or has_heredoc


def _capture_git_status(cwd: str) -> dict:
    """Capture git status --porcelain output.

    Returns:
        dict with keys:
            - files: set of file paths that are modified
            - raw: raw git status output
            - timestamp: ISO timestamp of capture
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5.0,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        files = set()
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                filename = " ".join(parts[1:])
                files.add(filename)

        return {
            "files": list(files),
            "raw": result.stdout,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        return {
            "files": [],
            "raw": "",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "error": str(e),
        }


def run(data: dict) -> dict | None:
    """Capture git status before Bash commands that could modify .py files.

    This hook NEVER blocks - it only captures state for PostToolUse.

    Args:
        data: Hook data dictionary from PreToolUse event

    Returns:
        None always (this hook never blocks)
    """
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return None

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return None

    # Only capture for commands that could modify .py files
    if not _could_modify_py_files(command):
        return None

    cwd = tool_input.get("cwd", "") or os.getcwd()

    # Capture git status
    git_state = _capture_git_status(cwd)

    # Store in session-scoped state file
    # Key includes terminal_id to support multi-terminal isolation
    terminal_id = _get_terminal_id()
    session_id = _get_session_id()

    state_key = f"{GIT_STATE_KEY}_{terminal_id}"

    # Load existing state or create new
    existing_state = load_state(state_key)
    if existing_state is None:
        existing_state = {}

    # Store pre-command state keyed by session_id
    # This allows the PostToolUse hook to retrieve the correct pre-state
    if "sessions" not in existing_state:
        existing_state["sessions"] = {}

    existing_state["sessions"][session_id] = {
        "cwd": cwd,
        "git_status": git_state,
    }
    existing_state["last_update"] = git_state["timestamp"]

    save_state(state_key, existing_state)

    return None


if __name__ == "__main__":
    # Read hook data from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    # Run the capture
    run(input_data)

    # Exit with success (this hook never blocks)
    sys.exit(0)
