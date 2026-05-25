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

# Resolve skill-guard path (works from plugin source or cache)
_PLUGIN_LIB = Path(__file__).resolve().parent.parent.parent / "lib"
if str(_PLUGIN_LIB) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_LIB))
from state_paths import get_hooks_dir

_hooks_dir = get_hooks_dir()
sys.path.insert(0, str(_hooks_dir))

# Add skill-guard to path via __lib helper
try:
    from __lib.skill_guard_path import ensure_skill_guard_in_syspath
    ensure_skill_guard_in_syspath()
except ImportError:
    # Fallback: direct path resolution
    _skill_guard_src = _hooks_dir.parent.parent / "packages" / "skill-guard" / "src"
    if not _skill_guard_src.exists():
        _skill_guard_src = Path("P:/packages/skill-guard/src")
    sys.path.insert(0, str(_skill_guard_src))

from skill_guard.breadcrumb.tracker import initialize_breadcrumb_trail


def main():
    """Initialize breadcrumb trail for /tdd skill."""
    try:
        # Initialize breadcrumb trail for 'tdd' skill
        # This reads workflow_steps from /tdd SKILL.md frontmatter
        # and creates breadcrumb_tdd.json with those steps
        initialize_breadcrumb_trail("tdd")

        # Allow session to continue
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

    except Exception as e:
        # Log error but don't block session start
        # Breadcrumb tracking is optional for now
        print(json.dumps({"continue": True}), file=sys.stderr)
        print(f"Breadcrumb initialization failed: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
