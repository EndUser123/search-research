"""
Protected path definitions and broken-file state for critical-file recovery mode.

Provides:
- PROTECTED_PATH_PATTERNS: list of (path_pattern, description) tuples
- broken_protected_files: module-level dict tracking which protected files are syntactically invalid
  Key: normalized absolute path -> {"broken_since": timestamp, "reason": str}
- is_protected_path(path): returns True if path matches any protected pattern
- set_file_broken(path): mark a protected file as syntactically invalid
- is_file_broken(path): check if a protected file is currently broken
- clear_file_broken(path): clear broken state after restore
"""

from __future__ import annotations

import fnmatch
import os
import time
from pathlib import Path
from typing import NamedTuple

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_CLAUDE_HOOKS = str(_HOOKS_DIR).replace("\\", "/")
_CLAUDE_SETTINGS = str(Path.home() / ".claude" / "settings.json").replace("\\", "/")


class BrokenEntry(NamedTuple):
    broken_since: float
    reason: str


# Protected path patterns — files whose corruption would break hook enforcement.
# Order matters: most specific first.
PROTECTED_PATH_PATTERNS: list[tuple[str, str]] = [
    # Hook system core
    (_CLAUDE_HOOKS + "/Stop.py", "Stop hook (primary enforcement"),
    (_CLAUDE_HOOKS + "/Stop_router.py", "Stop hook router"),
    (_CLAUDE_HOOKS + "/PreToolUse.py", "PreToolUse dispatcher"),
    (_CLAUDE_HOOKS + "/PostToolUse.py", "PostToolUse dispatcher"),
    (_CLAUDE_HOOKS + "/UserPromptSubmit.py", "UserPromptSubmit dispatcher"),
    # Hook state and config
    (_CLAUDE_HOOKS + "/state/", "hook state directory"),
    # Anti-sycophancy validators
    (_CLAUDE_HOOKS + "/anti_sycophancy/", "anti-sycophancy validators"),
    (_CLAUDE_HOOKS + "/validators/", "validator modules"),
    # Settings and policy
    str(Path.home() / ".claude" / "settings.json"), "Claude settings",
    # Hooks subdirectories (all .py files under hooks/)
    (_CLAUDE_HOOKS + "/PreToolUse_*.py", "PreToolUse hook modules (glob)"),
    (_CLAUDE_HOOKS + "/PostToolUse_*.py", "PostToolUse hook modules (glob)"),
    (_CLAUDE_HOOKS + "/UserPromptSubmit_*.py", "UserPromptSubmit hook modules (glob)"),
    (_CLAUDE_HOOKS + "/Stop_*.py", "Stop hook modules (glob)"),
    # Individual critical modules
    (_CLAUDE_HOOKS + "/__lib/turn_mode.py", "turn mode classifier"),
    (_CLAUDE_HOOKS + "/__lib/path_validator.py", "path validator"),
    (_CLAUDE_HOOKS + "/__lib/pre_tool_use_logic.py", "PreToolUse logic"),
    # Global CLAUDE.md
    (".claude/CLAUDE.md", "project CLAUDE.md"),
]

# Module-level broken-file state (session-scoped)
broken_protected_files: dict[str, BrokenEntry] = {}


def _normalize(p: str) -> str:
    """Normalize path for consistent dict keys."""
    return os.path.normpath(os.path.expanduser(p)).replace("\\", "/").lower()


def _glob_match(path: str, pattern: str) -> bool:
    """Match using simple glob (* wildcard) on path components or basename."""
    path_norm = _normalize(path)
    pat = pattern.replace("\\", "/")
    if "*" not in pat:
        return path_norm == _normalize(pat) or path_norm.startswith(_normalize(pat) + "/")
    # Glob pattern
    basename = os.path.basename(path_norm)
    return fnmatch.fnmatch(basename, pat) or fnmatch.fnmatch(path_norm, pat)


def is_protected_path(path: str) -> bool:
    """Return True if path matches any protected path pattern."""
    if not path:
        return False
    for pattern, _ in PROTECTED_PATH_PATTERNS:
        if _glob_match(path, pattern):
            return True
    return False


def set_file_broken(path: str, reason: str = "syntax error") -> None:
    """Mark a protected file as syntactically broken."""
    broken_protected_files[_normalize(path)] = BrokenEntry(
        broken_since=time.time(),
        reason=reason,
    )


def is_file_broken(path: str) -> bool:
    """Return True if protected file is currently marked as broken."""
    return _normalize(path) in broken_protected_files


def clear_file_broken(path: str) -> None:
    """Clear broken state after successful restore."""
    broken_protected_files.pop(_normalize(path), None)


def get_broken_reason(path: str) -> str | None:
    """Get the reason a file was marked broken."""
    entry = broken_protected_files.get(_normalize(path))
    return entry.reason if entry else None
