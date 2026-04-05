"""Artifact Grounder for Grounded Artifact Validation (GAV).

This module extracts canonical artifact structs from hook data for deterministic
grounding of blocked tool commands. It prevents LLMs from writing explanations
about the wrong artifact by capturing exact tool input data.

Pattern: Ground (deterministic) -> Echo (LLM, constrained) -> Validate (deterministic) -> Narrate (LLM, free)
"""


import re
import time

from shared_utils import resolve_session_id as _resolve_session_id_from_utils


def _safe_id(value: str) -> str:
    """Sanitize a string for use in filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _resolve_session_id(data: dict) -> str:
    """Delegates to shared_utils.resolve_session_id()."""
    return _resolve_session_id_from_utils(data)

def extract_command_tokens(command: str, max_tokens: int = 10) -> list[str]:
    """Extract significant tokens from a shell command.

    Strips quotes, paths, and common shell syntax to get meaningful words.
    Used for drift detection (if the RCA talks about concepts not in these tokens,
    it's suspicious).

    Args:
        command: Shell command string
        max_tokens: Maximum number of tokens to return

    Returns:
        List of unique, meaningful tokens (lowercased, stopwords removed)
    """
    # Remove Windows paths (P:\\..., C:\\..., etc.)
    cleaned = re.sub(r'[A-Z]:\\[^\s"]*\\', '', command)
    # Remove Unix paths (/home/..., /usr/..., etc.)
    cleaned = re.sub(r'/[^\s"]*/', '', cleaned)

    # Remove quotes and common shell syntax
    cleaned = re.sub(r'["\']', '', cleaned)
    cleaned = re.sub(r'[|&;><]', ' ', cleaned)

    # Split and filter stopwords
    words = cleaned.split()
    stopwords = {'cd', 'echo', '&&', '||', '--', '-c', '-e', '-f'}

    tokens = [
        w.lower() for w in words
        if len(w) > 1 and w.lower() not in stopwords
    ]

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:max_tokens]


def ground_blocked_command(data: dict, blocking_hook: str, reason: str) -> dict:
    """Build a grounded artifact struct for a blocked tool command.

    Args:
        data: The hook stdin data (contains tool_name, tool_input, session)
        blocking_hook: Name of the hook that blocked
        reason: The block reason string

    Returns:
        A canonical artifact struct dict with schema "blocked_command"
    """
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = _resolve_session_id(data)

    # Extract command tokens for drift detection
    command_tokens = []
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    if command:
        command_tokens = extract_command_tokens(command)

    return {
        "schema": "blocked_command",
        "version": 1,
        "timestamp": time.time(),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "blocking_hook": blocking_hook,
        "raw_reason": reason,
        "command_tokens": command_tokens
    }


def ground_git_safety_block(data: dict, blocking_hook: str, reason: str) -> dict:
    """Build a grounded artifact struct for a git safety block.

    Similar to ground_blocked_command but includes git_subcommand field
    extracted from the git command.

    Args:
        data: The hook stdin data (contains tool_name, tool_input, session)
        blocking_hook: Name of the hook that blocked
        reason: The block reason string

    Returns:
        A canonical artifact struct dict with schema "git_safety_block"
    """
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = _resolve_session_id(data)

    # Extract git subcommand
    git_subcommand = ""
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    if command:
        # Parse git command to extract subcommand (status, diff, commit, etc.)
        # Pattern: git [options] <subcommand> [args]
        parts = command.split()
        if len(parts) >= 2 and parts[0] == "git":
            # Find the first word after "git" that's not an option (starts with -)
            for part in parts[1:]:
                if not part.startswith("-"):
                    git_subcommand = part
                    break

    # Extract command tokens for drift detection
    command_tokens = []
    if command:
        command_tokens = extract_command_tokens(command)

    return {
        "schema": "git_safety_block",
        "version": 1,
        "timestamp": time.time(),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "blocking_hook": blocking_hook,
        "git_subcommand": git_subcommand,
        "raw_reason": reason,
        "command_tokens": command_tokens
    }
