#!/usr/bin/env python3
"""
PreToolUse Hook: Breadcrumb Trail Verifier

Verifies breadcrumb trail completion before tool execution.
Checks workflow steps for skills with active breadcrumb trails.

Configuration:
    BREADCRUMB_VERIFIER_ENABLED=true to enable (default)
    BREADCRUMB_VERIFIER_MODE=warn to warn (default) or block
    BREADCRUMB_VERIFIER_DEBUG=true for verbose output
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add skill-guard to path
from __lib.skill_guard_path import ensure_skill_guard_in_syspath
ensure_skill_guard_in_syspath()

# Configuration
ENABLED = os.environ.get("BREADCRUMB_VERIFIER_ENABLED", "true").lower() in ("1", "true", "yes")
MODE = os.environ.get("BREADCRUMB_VERIFIER_MODE", "warn").lower()  # "warn" or "block"
DEBUG = os.environ.get("BREADCRUMB_VERIFIER_DEBUG", "false").lower() in ("1", "true", "yes")

# Tools that might indicate skill completion or important transitions
COMPLETION_TOOLS = {
    "Skill",  # Skill completion often involves Skill tool calls
    "Bash",   # Test runs, verification commands
}


def main() -> int:
    """Main entry point."""
    if not ENABLED:
        print(json.dumps({"continue": True}))
        return 0

    try:
        input_text = sys.stdin.read().strip()
        if not input_text:
            print(json.dumps({"continue": True}))
            return 0

        data = json.loads(input_text)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    tool_name = data.get("tool_name", "")

    # Only check on specific tools (not every tool execution)
    if tool_name not in COMPLETION_TOOLS:
        print(json.dumps({"continue": True}))
        return 0

    try:
        from skill_guard.breadcrumb.tracker import (
            get_active_breadcrumb_trails,
            verify_breadcrumb_trail,
        )

        # Get all active breadcrumb trails for this terminal
        trails = get_active_breadcrumb_trails()

        if not trails:
            # No active breadcrumb trails
            print(json.dumps({"continue": True}))
            return 0

        # Check each active trail
        incomplete_trails = []
        for trail in trails:
            skill_name = trail.get("skill", "unknown")
            is_complete, message = verify_breadcrumb_trail(skill_name)

            if not is_complete:
                incomplete_trails.append((skill_name, message))

                if DEBUG:
                    print(f"[BREADCRUMB DEBUG] {skill_name}: {message}", file=sys.stdout)

        if not incomplete_trails:
            # All trails complete
            print(json.dumps({"continue": True}))
            return 0

        # Some trails are incomplete
        warnings = []
        for skill_name, message in incomplete_trails:
            warnings.append(f"⚠️ {skill_name}: {message}")

        if MODE == "block":
            # Block tool execution
            block_message = (
                "**Incomplete Breadcrumb Trails Detected**\n\n"
                + "\n".join(warnings)
                + "\n\nComplete all workflow steps before proceeding.\n"
                "To bypass: export BREADCRUMB_VERIFIER_MODE=warn"
            )
            print(json.dumps({
                "continue": False,
                "reason": block_message,
            }))
            return 2
        else:
            # Warn but allow
            warn_message = (
                "**Breadcrumb Trail Warnings**\n\n"
                + "\n".join(warnings)
                + "\n\nProceeding with caution. To block: export BREADCRUMB_VERIFIER_MODE=block"
            )
            print(json.dumps({
                "continue": True,
                "warning": warn_message,
            }))
            return 0

    except ImportError:
        # skill_guard not available, skip verification
        if DEBUG:
            print("[BREADCRUMB DEBUG] skill_guard not available", file=sys.stdout)
        print(json.dumps({"continue": True}))
        return 0
    except Exception as e:
        # Fail open on unexpected errors
        if DEBUG:
            print(f"[BREADCRUMB DEBUG] Error: {e}", file=sys.stdout)
        print(json.dumps({"continue": True}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
