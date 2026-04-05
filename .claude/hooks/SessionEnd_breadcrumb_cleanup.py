#!/usr/bin/env python3
"""
Breadcrumb Trail Cleanup (SessionEnd Hook)
==========================================

Cleans up all breadcrumb trails for the current session when it ends.

This prevents stale breadcrumb trails from littering the filesystem.

Configuration:
- BREADCRUMB_CLEANUP_ENABLED (default: true)
"""

import json
import os
import sys
from pathlib import Path

# Import breadcrumb tracker from skill_guard package
sys.path.insert(0, str(Path("P:/packages/skill-guard/src")))
from skill_guard.breadcrumb import cleanup_session_breadcrumbs
from skill_guard.breadcrumb.log import cleanup_old_log_dirs

# =============================================================================
# CONFIGURATION
# =============================================================================

ENABLED = os.environ.get("BREADCRUMB_CLEANUP_ENABLED", "true").lower() == "true"


# =============================================================================
# MAIN HOOK LOGIC
# =============================================================================


def run(data: dict) -> dict:
    """Clean up breadcrumb trails for this session.

    Args:
        data: SessionEnd hook input dict

    Returns:
        {"cleaned": int} dict with count of trails cleaned
    """
    # Check if enabled
    if not ENABLED:
        return {"cleaned": 0, "reason": "Breadcrumb cleanup disabled"}

    # Clean up all breadcrumb trails for this session
    cleaned_count = cleanup_session_breadcrumbs()

    # Also clean up old log directories (opportunistic, runs on every session end)
    log_result = cleanup_old_log_dirs(age_days=7)
    removed_dirs = len(log_result["removed"])

    return {
        "cleaned": cleaned_count,
        "removed_dirs": removed_dirs,
        "reason": f"Cleaned {cleaned_count} trails, removed {removed_dirs} old log dirs",
    }


# =============================================================================
# HOOK ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Read SessionEnd hook input from stdin
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)

    # Output result as JSON
    print(json.dumps(result, indent=2))
