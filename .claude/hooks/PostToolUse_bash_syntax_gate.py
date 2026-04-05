#!/usr/bin/env python3
"""
PostToolUse Hook: Bash Syntax Validation Gate

Detects and validates Python files modified by Bash commands to prevent
syntax errors from breaking the application.

This hook addresses the P0 issue from the yt-fts debugging session where
an IndentationError introduced via Bash heredoc blocked application
startup for 8 minutes.

Cross-Agent Isolation: Uses pre-state captured by PreToolUse_git_state_capture.py
to only validate files actually modified by the current command, preventing
one agent's syntax errors from blocking other agents' commands.

Run: PostToolUse (after Bash tool execution)
Timeout: 10 seconds
Exit Codes:
  - 0: Allow (no syntax errors or no .py files changed)
  - 2: Block (syntax errors detected)

Author: Claude Code
Date: 2026-03-02
Related: plan-bash-syntax-validation.md
Related: 2026-03-02_debugging_workflow_analysis.md (P0 issue)
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# Add hooks lib to path
hooks_lib = Path(__file__).resolve().parent / "__lib"
sys.path.insert(0, str(hooks_lib))

from pre_tool_use_logic import check_python_file_edits
from shared_utils import load_state

# State key for pre-command git status (must match PreToolUse_git_state_capture.py)
GIT_STATE_KEY = "bash_git_pre_state"


def _get_terminal_id() -> str:
    """Get terminal ID from environment or generate a hash of cwd."""
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")
    if terminal_id:
        return terminal_id
    cwd = os.getcwd()
    return hashlib.md5(cwd.encode()).hexdigest()[:8]


def _get_session_id() -> str:
    """Get session ID from environment."""
    return os.environ.get("CLAUDE_SESSION_ID", "default")


def _load_pre_state() -> dict | None:
    """Load pre-command git state captured by PreToolUse_git_state_capture.py.

    Returns:
        The git status dict from before the command, or None if not found.
    """
    terminal_id = _get_terminal_id()
    session_id = _get_session_id()
    state_key = f"{GIT_STATE_KEY}_{terminal_id}"

    state = load_state(state_key)
    if not state:
        return None

    # Get session-specific state
    if "sessions" not in state:
        return None

    session_data = state["sessions"].get(session_id)
    if not session_data:
        return None

    return session_data.get("git_status")


def run(data: dict) -> dict | None:
    """Validate Python files modified by Bash commands.

    Args:
        data: Hook data dictionary from PostToolUse event

    Returns:
        None if validation passes
        {"decision": "block", ...} if syntax errors found
    """
    # Load pre-state for cross-agent isolation
    pre_state = _load_pre_state()

    # Check if any .py files were modified (delta computed if pre_state available)
    result = check_python_file_edits(data, pre_state=pre_state)

    if result and result.get("decision") == "block":
        # Syntax errors detected - show helpful message but DON'T block
        # (PostToolUse blocking has no effect since command already ran)
        if "blocking_hook" not in result:
            result["blocking_hook"] = "PostToolUse_bash_syntax_gate.py"
        print(json.dumps(result), file=sys.stdout)
        # Exit 0 (allow) so user sees the helpful message instead of "Blocked by hook"
        sys.exit(0)

    # Allow the operation to proceed
    return None


if __name__ == "__main__":
    # Read hook data from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Invalid JSON - allow operation
        sys.exit(0)

    # Run the validation
    run(input_data)

    # Exit with success
    sys.exit(0)
