#!/usr/bin/env python3
"""
Shared utilities for next-command suggestion hooks.

CONSOLIDATES duplicate code from:
- PostToolUse_next_command_suggester.py (function-based, active)
- posttooluse/next_command_suggester.py (class-based, orphaned)
- next_command_hint.py (utility module with zen patterns)

JUSTIFICATION for creating new functions:
- Searched __lib/ for existing implementations: none found
- task_identity_manager.py has _from_git_worktree() but is domain-specific (task inference)
- These are generic utilities used across multiple suggestion hooks
- Centralizing eliminates ~200 lines of duplicate code
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# =============================================================================
# Registry Loading
# =============================================================================

def load_commands_registry(registry_path: Path | None = None) -> dict[str, Any]:
    """Load the commands.toml registry.

    Args:
        registry_path: Optional path to commands.toml. If None, searches default locations.

    Returns:
        Dictionary with "commands" and "signals" keys.
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    if registry_path is None:
        # Try default locations
        possible_paths = [
            Path("P:/.claude/registry/commands.toml"),
            Path(__file__).resolve().parent.parent.parent / "registry/commands.toml",
        ]
    else:
        possible_paths = [registry_path]

    for path in possible_paths:
        if path.exists():
            try:
                with open(path, "rb") as f:
                    return tomllib.load(f)
            except Exception:
                pass

    return {"commands": {}, "signals": {}}


# =============================================================================
# Signal Extraction
# =============================================================================

# Standard signal patterns for workflow detection
SIGNAL_PATTERNS = {
    "SUPPORTED": r"\bSUPPORTED\b",
    "FALSE": r"\bFALSE\b",
    "INSUFFICIENT": r"\bINSUFFICIENT\b",
    "root_cause_found": r"root\s+cause",
    "fix_applied": r"fix.*applied",
    "plan_complete": r"plan.*complete",
    "tests_passing": r"tests.*pass",
    # Triggered by task unresolved output blocks/hints.
    "unresolved_items_detected": r"unresolved\s+from\s+chat\s+history|/task-unresolved",
}


def extract_output_signals(response: str) -> list[str]:
    """Extract workflow signals from LLM response.

    Args:
        response: The response text to analyze.

    Returns:
        List of detected signal names.
    """
    signals = []
    for signal, pattern in SIGNAL_PATTERNS.items():
        if re.search(pattern, response, re.IGNORECASE):
            signals.append(signal)
    return signals


# =============================================================================
# Git Context
# =============================================================================

def get_git_context(cwd: Path | None = None, timeout: int = 2) -> dict[str, Any]:
    """Get git repository status for context-aware suggestions.

    Args:
        cwd: Directory to check. If None, uses current working directory.
        timeout: Subprocess timeout in seconds.

    Returns:
        Dictionary with git status information:
        - has_changes: bool - True if any uncommitted changes
        - has_unstaged: bool - True if unstaged changes exist
        - has_unpushed: bool - True if unpushed commits exist
        - is_worktree: bool - True if in a git worktree
        - change_count: int - Number of changed files
        - summary: str - First few lines of git status output
    """
    if cwd is None:
        try:
            cwd = Path.cwd()
        except Exception:
            return _empty_git_context()

    # Find git root
    git_root = _find_git_root(cwd)
    if not git_root:
        return _empty_git_context()

    # Detect worktree vs main repo
    git_dir = git_root / ".git"
    is_worktree = git_dir.is_file()

    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        # Check for unstaged changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=git_root,
            creationflags=creation_flags
        )

        has_unstaged = False
        change_count = 0
        summary_lines = []

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            for line in lines:
                if line and line[0] not in "?!":
                    if len(line) > 1 and line[1] != " ":
                        has_unstaged = True
                    change_count += 1
                    if len(summary_lines) < 5:
                        summary_lines.append(line)

        # Check for unpushed commits (only in worktrees)
        has_unpushed = False
        if is_worktree:
            result2 = subprocess.run(
                ["git", "log", "origin/main..HEAD", "--oneline"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=git_root,
                creationflags=creation_flags
            )
            has_unpushed = result2.returncode == 0 and bool(result2.stdout.strip())

        return {
            "has_changes": has_unstaged or has_unpushed,
            "has_unstaged": has_unstaged,
            "has_unpushed": has_unpushed,
            "is_worktree": is_worktree,
            "change_count": change_count,
            "summary": "\n".join(summary_lines),
        }
    except Exception:
        return _empty_git_context()


def _find_git_root(start_dir: Path) -> Path | None:
    """Find the git repository root from a starting directory."""
    try:
        for parent in [start_dir] + list(start_dir.parents):
            if (parent / ".git").exists():
                return parent
    except Exception:
        pass
    return None


def _empty_git_context() -> dict[str, Any]:
    """Return empty git context when git is unavailable."""
    return {
        "has_changes": False,
        "has_unstaged": False,
        "has_unpushed": False,
        "is_worktree": False,
        "change_count": 0,
        "summary": "",
    }


# =============================================================================
# Command Description Lookup
# =============================================================================

def get_command_description(command: str, registry: dict[str, Any] | None = None) -> str:
    """Get description for a command from the registry.

    Args:
        command: Command name (with or without leading slash).
        registry: Optional registry dict. If None, loads default.

    Returns:
        Command description or empty string.
    """
    if registry is None:
        registry = load_commands_registry()

    commands = registry.get("commands", {})
    lookup_cmd = command.lstrip("/")

    for cmd_data in commands.values():
        aliases = cmd_data.get("aliases", [])
        if command in aliases or lookup_cmd in aliases:
            return cmd_data.get("description", "")
    return ""


# =============================================================================
# Suggestion Building
# =============================================================================

def build_suggestion_block(
    suggestions: list[str],
    max_suggestions: int = 3,
    context: str = ""
) -> str:
    """Build a formatted suggestion block for display.

    Args:
        suggestions: List of suggestions (may include "cmd - description" format).
        max_suggestions: Maximum number of suggestions to include.
        context: Optional context string to append.

    Returns:
        Formatted suggestion block as a string.
    """
    if not suggestions:
        return ""

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in suggestions:
        cmd = item.split()[0] if item else ""
        if cmd and cmd not in seen:
            seen.add(cmd)
            unique.append(item)

    # Limit to max_suggestions
    unique = unique[:max_suggestions]

    if not unique:
        return ""

    lines = ["", "---", "**Next Command Suggestions:**"]

    for item in unique:
        lines.append(f"  • {item}")

    if context:
        lines.append("")
        lines.append(f"Context: {context}")

    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Last Command Extraction
# =============================================================================

def get_last_command(prompt: str) -> str | None:
    """Extract the last slash command from a prompt string.

    Args:
        prompt: The prompt text to search.

    Returns:
        The extracted command (with leading slash) or None.
    """
    match = re.search(r'/([a-zA-Z][a-zA-Z0-9_-]*)', prompt)
    if match:
        return f"/{match.group(1)}"
    return None
