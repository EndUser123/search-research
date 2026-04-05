#!/usr/bin/env python3
"""
SessionStart Memory Monitor
============================

Checks MEMORY.md line count at session start and warns if approaching limit.

This is a SessionStart hook that runs early in the setup sequence to provide
feedback about memory file size before the session continues.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add __lib to path for imports
HOOKS_DIR = Path(__file__).resolve().parent
LIB_DIR = HOOKS_DIR / "__lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

try:
    from memory_monitor import check_memory_limit
except ImportError:
    # Memory monitor not available - skip silently
    def check_memory_limit(path):  # type: ignore[misc]
        return None


def main():
    """SessionStart hook entry point."""
    try:
        # Read stdin for session data
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        try:
            raw_input = raw_input.lstrip('\ufeff')
            data = json.loads(raw_input)
        except json.JSONDecodeError:
            sys.exit(0)

        # Determine memory path from project root
        # Try to get project root from environment or current directory
        project_root = Path.cwd()

        # Check if we're in a git repo to find project root
        git_dir = project_root / ".git"
        if not git_dir.exists():
            # Try parent directories
            for parent in project_root.parents:
                if (parent / ".git").exists():
                    project_root = parent
                    break

        # Expected memory location
        memory_path = project_root / ".claude" / "projects" / project_root.name / "memory" / "MEMORY.md"

        # Fallback to common locations
        if not memory_path.exists():
            alt_paths = [
                project_root / "memory" / "MEMORY.md",
                Path.home() / ".claude" / "projects" / project_root.name / "memory" / "MEMORY.md",
            ]
            for alt_path in alt_paths:
                if alt_path.exists():
                    memory_path = alt_path
                    break

        # Check memory limit
        warning = check_memory_limit(memory_path)

        if warning:
            # Return warning as additional context
            print(
                json.dumps(
                    {
                        "additionalContext": warning,
                    }
                )
            )
        else:
            # No warning, return empty
            print("{}")

        sys.exit(0)

    except Exception:
        # Fail silently - memory monitoring is advisory
        print("{}")
        sys.exit(0)


if __name__ == "__main__":
    main()
