#!/usr/bin/env python3
"""
SessionEnd TDD Cleanup - Terminal-isolated state cleanup

Deletes state files older than 24 hours from current terminal's state directory.

Pattern based on /v skill's SessionEnd_v_cleanup.py but with terminal isolation.
"""

import json
import sys
import time
from pathlib import Path

# Plugin lib for shared state paths (works from source or cache)
_PLUGIN_LIB = Path(__file__).resolve().parent.parent.parent / "lib"
if str(_PLUGIN_LIB) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_LIB))

from state_paths import get_hooks_dir

# Add global hooks directory to path for __lib imports
hooks_dir = get_hooks_dir()
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

# Import terminal detection for isolation
# Guard the import — when run as subprocess from skills/tdd/hooks/, __lib is not resolvable
try:
    from __lib.terminal_detection import detect_terminal_id
except ImportError:
    # Stub for when __lib is not on path (subprocess execution from skill hooks dir)
    def detect_terminal_id() -> str:
        import os
        return os.environ.get("CLAUDE_TERMINAL_ID", "unknown")


def cleanup_expired_tdd_states(max_age_hours: int = 24) -> dict:
    """Clean up expired TDD state files from current terminal's state directory.

    Args:
        max_age_hours: Maximum age in hours for state files to keep (default 24)

    Returns:
        dict: Cleanup statistics
    """
    # Get terminal-isolated state directory
    terminal_id = detect_terminal_id()
    state_dir = Path.home() / ".claude" / ".state" / "tdd" / terminal_id

    if not state_dir.exists():
        return {"terminal_id": terminal_id, "cleaned": 0, "skipped": 0, "errors": 0}

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    cleaned = 0
    skipped = 0
    errors = 0

    # Include both legacy pattern files (tdd.*.json) and workflow state files
    # such as tdd_workflow.json used by continuation hooks.
    for state_file in state_dir.glob("*.json"):
        try:
            # Check file age
            file_mtime = state_file.stat().st_mtime
            file_age = current_time - file_mtime

            if file_age > max_age_seconds:
                # Check if state is expired (TTL check)
                with open(state_file, encoding="utf-8") as f:
                    state = json.load(f)

                created_str = state.get("created_at", "")
                if created_str:
                    try:
                        from datetime import datetime

                        created = datetime.fromisoformat(created_str)
                        if datetime.now() - created > __import__("datetime").timedelta(hours=24):
                            state_file.unlink()
                            cleaned += 1
                            continue
                    except (ValueError, TypeError):
                        pass

                # Safe to delete if file is old
                state_file.unlink()
                cleaned += 1
            else:
                skipped += 1

        except (OSError, json.JSONDecodeError):
            errors += 1

    return {
        "terminal_id": terminal_id,
        "cleaned": cleaned,
        "skipped": skipped,
        "errors": errors,
    }


def main():
    """SessionEnd hook entry point."""
    result = cleanup_expired_tdd_states()
    # Silent cleanup - no output unless errors
    if result["errors"] > 0:
        print(json.dumps(result), file=sys.stderr)


if __name__ == "__main__":
    main()
