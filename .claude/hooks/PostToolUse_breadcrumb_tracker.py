#!/usr/bin/env python3
"""
Breadcrumb Tracking Hook for PostToolUse
=========================================

This is a redirect to the actual implementation in the skill-guard package.

The implementation lives at:
P:/packages/skill-guard/src/skill_guard/breadcrumb/hooks/PostToolUse_breadcrumb_tracker.py

This redirect pattern is used because Windows symlinks require admin privileges.
"""

import sys
from pathlib import Path

# Add skill-guard to path
SKILL_GUARD = Path("P:/packages/skill-guard/src")
if SKILL_GUARD.exists():
    sys.path.insert(0, str(SKILL_GUARD))

# Import and run the actual hook implementation
from skill_guard.breadcrumb.hooks.PostToolUse_breadcrumb_tracker import run

if __name__ == "__main__":
    # Hook entry point
    import json
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)

    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({}))
