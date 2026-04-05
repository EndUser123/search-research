#!/usr/bin/env python3
r"""
Repository Visibility Guard Hook
================================
Prevents accidental repository visibility changes that could expose sensitive data.

Blocks:
- GitHub CLI: gh repo edit --visibility public (for P:\ drive repos)
- GitHub API: curl/wget/Invoke-WebRequest calls that change visibility

Allows:
- packages/ folder repos to be made public
- All repos to be made private (safe operation)
- Bypass with --allow-visibility-change flag
"""

import json
import os
import re
import sys
from pathlib import Path

# Hook directory for imports
HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Configuration
PROTECTED_PATHS = [
    "P:/",  # P: drive (case-insensitive)
]

ALLOWED_PUBLIC_PATHS = [
    "P:/packages/",  # packages folder (case-insensitive)
]

# Regex patterns for detecting visibility change commands
# GitHub CLI
_GH_REPO_EDIT_PATTERN = re.compile(
    r"gh\s+repo\s+edit\s+.*?--visibility\s+(public|private)", re.IGNORECASE
)

# GitHub API via curl
_CURL_API_PATTERN = re.compile(
    r"curl\s+.*?api\.github\.com/repos/[\w-]+/[\w-]+.*?(visibility|public|private)", re.IGNORECASE
)

# GitHub API via wget
_WGET_API_PATTERN = re.compile(
    r"wget\s+.*?api\.github\.com/repos/[\w-]+/[\w-]+.*?(visibility|public|private)", re.IGNORECASE
)

# GitHub API via PowerShell
_INVOKE_WEBREQUEST_PATTERN = re.compile(
    r"Invoke-WebRequest\s+.*?api\.github\.com/repos/[\w-]+/[\w-]+.*?(visibility|public|private)",
    re.IGNORECASE,
)

# Combined pattern list
VISIBILITY_PATTERNS = [
    _GH_REPO_EDIT_PATTERN,
    _CURL_API_PATTERN,
    _WGET_API_PATTERN,
    _INVOKE_WEBREQUEST_PATTERN,
]


def is_protected_path(repo_path: str) -> bool:
    r"""Check if repo path is in protected list (P:\ drive)."""
    normalized = repo_path.replace("\\", "/").lower()
    return any(normalized.startswith(protected.lower()) for protected in PROTECTED_PATHS)


def is_allowed_public_path(repo_path: str) -> bool:
    """Check if repo path is explicitly allowed to be public (packages/)."""
    normalized = repo_path.replace("\\", "/").lower()
    return any(normalized.startswith(allowed.lower()) for allowed in ALLOWED_PUBLIC_PATHS)


def detect_visibility_change(command: str) -> tuple[bool, str | None]:
    """Detect if command attempts to change repository visibility.

    Returns:
        (is_visibility_change, visibility_type|None)
        visibility_type is "public" or "private" or None

    NOTE: Uses only specific regex patterns — NOT broad keyword matching.
    Broad keyword matching ("public" in command) causes false positives when
    "public" appears in heredoc bodies, Python string literals, or comments
    inside multi-line bash commands.
    """
    # Check regex patterns for actual visibility change commands.
    # These patterns are specific enough to match only real gh/curl/wget/PS calls.
    for pattern in VISIBILITY_PATTERNS:
        match = pattern.search(command)
        if match:
            # Try to extract visibility from regex groups
            if match.groups():
                visibility = match.group(1).lower()
                if visibility in ("public", "private"):
                    return True, visibility
            # Pattern matched but no visibility extracted - generic match
            return True, None

    return False, None


def get_current_repo_path() -> str | None:
    """Get current git repository path.

    Returns:
        Repository path or None if not in a git repo.
    """
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return None


def run(data: dict) -> dict | None:
    """Hook entry point - block dangerous visibility changes.

    Returns:
        None to allow, {"decision": "block"} to block
    """
    # Check if hook is enabled
    enabled = os.environ.get("REPO_VISIBILITY_GUARD_ENABLED", "true")
    if enabled.lower() != "true":
        return None

    tool_name = data.get("tool_name", "")

    # Only process Bash commands
    if tool_name != "Bash":
        return None

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return None

    # Check for bypass flag
    if "--allow-visibility-change" in command:
        return None

    # Detect visibility change attempt
    is_visibility_change, visibility_type = detect_visibility_change(command)

    if not is_visibility_change:
        return None

    # Get current repo path
    repo_path = get_current_repo_path()

    if not repo_path:
        # Can't determine repo path - warn but allow
        # (This handles cases like gh repo edit owner/repo where we're not in a repo)
        return None

    # Check if this is a protected path
    if not is_protected_path(repo_path):
        # Not a protected path (e.g., C:/, D:/) - allow
        return None

    # Check if this is an allowed public path (packages/)
    if is_allowed_public_path(repo_path):
        # packages/ folder - allow public changes
        return None

    # Protected path (P:\ drive) attempting to go public
    if visibility_type == "public":
        return {
            "decision": "block",
            "reason": (
                "⛔ REPOSITORY VISIBILITY CHANGE BLOCKED\n\n"
                f"Repository: {repo_path}\n"
                "Command: gh repo edit --visibility public\n\n"
                "This repository is on the P: drive, which is protected from "
                "being made public to prevent accidental exposure of API keys "
                "and sensitive data.\n\n"
                "Exceptions:\n"
                "• Repositories under P:/packages/ are allowed to be public\n"
                "• All repositories can be made private (safe operation)\n\n"
                "To bypass this check (use with caution):\n"
                "  Add --allow-visibility-change to your command\n\n"
                "To disable this hook:\n"
                "  export REPO_VISIBILITY_GUARD_ENABLED=false"
            ),
            "blocking_hook": "PreToolUse_repo_visibility_guard.py",
        }

    # Private visibility change is always safe
    return None


@hook_main
def main() -> None:
    """Entry point for hook execution."""
    try:
        data = json.load(sys.stdin)
        res = run(data)

        if res and res.get("decision") == "block":
            print(json.dumps(res))
            sys.exit(2)

        sys.exit(0)
    except Exception:
        # Fail open - don't break the hook system on errors
        sys.exit(0)


if __name__ == "__main__":
    main()
