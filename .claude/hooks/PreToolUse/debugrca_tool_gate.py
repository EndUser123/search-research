#!/usr/bin/env python3
"""
debugrca_tool_gate.py - PreToolUse Hook for Tool Availability Gate

This hook enforces tool availability requirements for the debugRCA skill.
It blocks debugRCA execution when required tools are not available,
with support for local-only mode via DEBUGRCA_LOCAL_ONLY environment variable.

Behavior:
- When debugRCA skill is active: Check that required tools are available
- When debugRCA skill is NOT active: Allow all tools (pass-through)
- In local-only mode: WebSearch is not required

Required Tools:
- Grep: Code searching
- Read: File reading
- Bash: Command execution
- WebSearch: Optional (local-only mode disables this requirement)

Priority: 5.0 (medium - runs after critical gates, before late checks)

Author: TDD Cycle for debugRCA Tier 1
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# =============================================================================
# Configuration
# =============================================================================

ENABLED = os.environ.get("DEBUGRCA_TOOL_GATE_ENABLED", "true").lower() == "true"

# Required tools for debugRCA
REQUIRED_TOOLS = {
    "Grep": True,      # Required - Code search
    "Read": True,      # Required - File reading
    "Bash": True,      # Required - Command execution
    "WebSearch": False,  # Optional - Remote search
}

# =============================================================================
# Tool Checker Import
# =============================================================================


def check_tool_availability() -> dict[str, Any]:
    """Check tool availability by importing tool_checker module.

    Returns:
        Dict with availability status or None if checker fails
    """
    try:
        # Add skills directory to path
        skills_dir = Path("P:/.claude/skills")
        if str(skills_dir) not in sys.path:
            sys.path.insert(0, str(skills_dir))

        # Try both debugRCA (actual module name) and debugrca (lowercase alias)
        try:
            from debugRCA.tool_checker import check_tool_availability as check
        except ImportError:
            from debugrca.tool_checker import check_tool_availability as check

        return check()
    except ImportError:
        # tool_checker not available, fail gracefully
        return None
    except Exception:
        # Tool checker crashed, fail open
        return None


# =============================================================================
# Main Handler
# =============================================================================


def handle_pre_tool_use(data: dict[str, Any]) -> dict[str, Any]:
    """Handle PreToolUse event for debugRCA tool gating.

    Args:
        data: Hook input with keys:
            - tool_name: str - Name of the tool being called
            - input: dict - Tool input parameters
            - skill: str | None - Current skill context

    Returns:
        Empty dict to allow, or {"block": True, "reason": "..."} to block
    """
    # Check if gate is enabled
    if not ENABLED:
        return {}

    # Extract tool information
    tool_name = data.get("tool_name", "")
    skill = data.get("skill", None)

    # Only check when debugRCA is the active skill
    if not skill or str(skill).lower() not in ("debugrca", "debugrca"):
        # Not using debugRCA, allow all tools
        return {}

    # Check tool availability
    availability = check_tool_availability()

    if availability is None:
        # Checker failed - fail open (allow) to avoid breaking everything
        # This is a safety measure: we'd rather debugRCA work with degraded
        # functionality than block it entirely due to a checker bug
        return {}

    # Check if required tools are available
    if not availability.get("available", False):
        missing = availability.get("missing", [])
        mode = availability.get("mode", "full")

        reason_parts = [
            "debugRCA requires the following tools that are not available:",
            f"  Missing: {', '.join(missing)}",
        ]

        if mode == "local":
            reason_parts.append(
                "\nNote: Running in local-only mode (DEBUGRCA_LOCAL_ONLY=1). "
                "Core tools (Grep, Read, Bash) are still required."
            )

        return {
            "block": True,
            "reason": "\n".join(reason_parts),
        }

    # All checks passed
    return {}


# =============================================================================
# Hook Entry Point
# =============================================================================


def main() -> None:
    """Hook entry point - handles JSON input from stdin."""
    try:
        # Read hook input
        payload = json.loads(sys.stdin.read())

        # Process the tool use
        result = handle_pre_tool_use(payload)

        if result and result.get("block"):
            # Block the tool use
            print(json.dumps(result))
            sys.exit(2)  # Exit code 2 = block
        else:
            # Allow the tool use
            print(json.dumps({}))
            sys.exit(0)

    except json.JSONDecodeError:
        # Bad stdin - fail open (allow tool to proceed)
        print(json.dumps({}))
        sys.exit(0)

    except Exception as e:
        # Unexpected error - log but fail open
        # Critical: PreToolUse exceptions block ALL tools
        import traceback
        sys.stderr.write(f"[debugrca_tool_gate] Error: {e}\n")
        sys.stderr.write(traceback.format_exc())
        print(json.dumps({}))  # Allow tool to proceed
        sys.exit(0)


# Allow running without decorator for direct execution
if __name__ == "__main__":
    main()
