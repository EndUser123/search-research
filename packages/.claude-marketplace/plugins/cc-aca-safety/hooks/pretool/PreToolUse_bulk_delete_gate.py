#!/usr/bin/env python3
"""
Bulk Delete Gate v1.0
=====================

Prevents destructive bulk deletions by:
1. Detecting rm -rf / Remove-Item -Recurse on directories
2. Counting files that would be deleted
3. Auto-creating a git tag as a recovery point
4. Emitting a warning with the file inventory

This is the simple, structural fix for the fast-slow asymmetry problem:
destructive actions are fast and atomic, but verification is slow and
multi-step. This gate synchronizes them by forcing inventory before deletion.

Incident that motivated this:
  23 Python scripts + 7 test files deleted via rm -rf after only 2 of 23
  were migrated. The remaining 21 were permanently lost.

Design principles:
  - ~50 lines of core logic, not a framework
  - No state files, no tokens, no cross-terminal sync
  - Uses git tags for zero-cost recovery (no state management)
  - Only triggers on bulk operations (>FILE_THRESHOLD files)
  - In-process execution for speed (<100ms)
"""

from __future__ import annotations

# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import re
import subprocess
import sys
from datetime import UTC
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Only gate deletions affecting more than this many files
FILE_THRESHOLD = 5

# Patterns that indicate recursive/bulk deletion
BULK_DELETE_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|(-[a-zA-Z]*f[a-zA-Z]*r))\s+",  # rm -rf, rm -fr
    r"\brm\s+-r\s+",  # rm -r (without -f)
    r"\brmdir\s+/[sS]\s+",  # rmdir /s (Windows)
    r"\bRemove-Item\s+[^\|;]+?-Recurse",  # PowerShell
    r"\brd\s+/[sS]\s+",  # rd /s (Windows)
    r"\bdel\s+/[sS]\s+",  # del /s (Windows)
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BULK_DELETE_PATTERNS]

# Directories that are always safe to delete (build artifacts, caches)
SAFE_DELETE_PATTERNS = [
    r"__pycache__",
    r"node_modules",
    r"\.git/",
    r"\.pyc$",
    r"\bdist\b",
    r"\bbuild\b",
    r"\b\.tmp\b",
    r"\.backup\b",
    r"\bvenv\b",
    r"\benv\b",
    r"\b\.mypy_cache\b",
    r"\.pytest_cache",
    r"\.ruff_cache",
]

SAFE_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in SAFE_DELETE_PATTERNS]


# =============================================================================
# CORE LOGIC
# =============================================================================


def extract_delete_target(command: str) -> str | None:
    """Extract the directory path from a bulk delete command.

    Returns the target path or None if the command isn't a bulk delete.
    """
    # PowerShell: path comes between Remove-Item and -Recurse
    ps_match = re.search(r"\bRemove-Item\s+([^\s;|]+)", command, re.IGNORECASE)
    if ps_match and re.search(r"-Recurse", command, re.IGNORECASE):
        return ps_match.group(1).strip("\"'")

    for pattern in COMPILED_PATTERNS:
        match = pattern.search(command)
        if match:
            # Get everything after the matched pattern
            rest = command[match.end() :].strip()
            # Extract the path (first non-flag argument)
            # Skip any remaining flags like --no-preserve-root
            parts = rest.split()
            for part in parts:
                if not part.startswith("-") and part not in ("\\", "/"):
                    # Clean quotes
                    return part.strip("\"'")
    return None


def is_safe_target(target: str) -> bool:
    """Check if the deletion target is a known safe-to-delete directory."""
    for pattern in SAFE_PATTERNS_COMPILED:
        if pattern.search(target):
            return True
    return False


def count_files(target_path: Path) -> tuple[int, list[str]]:
    """Count files in directory and return (count, sample_files).

    Returns at most 20 filenames for the inventory display.
    """
    if not target_path.exists():
        return 0, []
    if not target_path.is_dir():
        return 1, [target_path.name]

    files = []
    try:
        for item in target_path.rglob("*"):
            if item.is_file():
                files.append(str(item.relative_to(target_path)))
    except (PermissionError, OSError):
        pass

    sample = files[:20]
    return len(files), sample


def create_git_tag(target_path: Path) -> str | None:
    """Create a git tag as a recovery point before deletion.

    Returns the tag name or None if git isn't available.
    """
    try:
        # Find the git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0:
            return None

        git_root = result.stdout.strip()

        # Check if there are any changes to stash
        # (target might have uncommitted changes)
        from datetime import datetime

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        tag_name = f"pre-delete-{target_path.name}-{timestamp}"

        # Create the tag at HEAD
        result = subprocess.run(
            ["git", "tag", tag_name, "-m", f"Recovery point before deleting {target_path}"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=git_root,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode == 0:
            return tag_name
    except Exception:
        pass
    return None


def run(data: dict) -> dict | None:
    """In-process execution entry point.

    Returns block dict with inventory info, or None to allow.
    """
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return None

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return None

    # Check bypass (parent env or inline in command)
    if os.environ.get("BULK_DELETE_BYPASS", "0") == "1":
        return None
    if re.search(r"\bBULK_DELETE_BYPASS\s*=\s*1\b", command):
        return None

    # Extract deletion target
    target = extract_delete_target(command)
    if not target:
        return None

    # Resolve the path
    target_path = Path(target).resolve()

    # Skip safe targets (build artifacts, caches)
    if is_safe_target(target):
        return None

    # Count files
    file_count, sample_files = count_files(target_path)

    # Below threshold — allow silently
    if file_count <= FILE_THRESHOLD:
        return None

    # GATE: Above threshold — create recovery tag and block with inventory
    tag_name = create_git_tag(target_path)

    # Build inventory message
    lines = [
        f"⚠️  BULK DELETE GATE: This will delete {file_count} files in {target_path.name}/",
        "",
    ]

    if tag_name:
        lines.append(f"📌 Recovery tag created: {tag_name}")
        lines.append(f"   Restore with: git checkout {tag_name} -- {target}")
        lines.append("")

    lines.append("📋 File inventory:")
    for f in sample_files:
        lines.append(f"   • {f}")
    if file_count > 20:
        lines.append(f"   ... and {file_count - 20} more files")

    lines.extend(
        [
            "",
            "To proceed, either:",
            "  1. Set BULK_DELETE_BYPASS=1 in environment",
            "  2. Delete files in smaller batches",
            "  3. Confirm you have verified migration/backup is complete",
        ]
    )

    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "PreToolUse_bulk_delete_gate.py",
    }


# =============================================================================
# SUBPROCESS ENTRY POINT (fallback)
# =============================================================================


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = run(data)
    if result:
        print(json.dumps(result))
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
