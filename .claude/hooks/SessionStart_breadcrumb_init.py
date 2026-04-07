#!/usr/bin/env python3
"""
SessionStart hook for /tdd skill - Initialize breadcrumb tracking

Initializes breadcrumb trail when /tdd skill is invoked.
This enables workflow step tracking across the RED → GREEN → REFACTOR cycle.

Usage: This hook is automatically called when /tdd skill session starts
Input: JSON via stdin with session details
Output: JSON via stdout with continue decision
"""

import json
import sys
from pathlib import Path

# Add skill-guard to path
skill_guard_path = Path("P:/packages/skill-guard")
if str(skill_guard_path) not in sys.path:
    sys.path.insert(0, str(skill_guard_path))

from skill_guard.breadcrumb.tracker import initialize_breadcrumb_trail


def main():
    """Initialize breadcrumb trail for /tdd skill."""
    try:
        # Initialize breadcrumb trail for 'tdd' skill
        # This reads workflow_steps from /tdd SKILL.md frontmatter
        # and creates breadcrumb_tdd.json with those steps
        initialize_breadcrumb_trail("tdd")

        # Allow session to continue
        print(json.dumps({"continue": True}))
        sys.exit(0)

    except Exception as e:
        # Log error but don't block session start
        # Breadcrumb tracking is optional for now
        print(json.dumps({"continue": True}), file=sys.stderr)
        print(f"Breadcrumb initialization failed: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
