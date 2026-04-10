#!/usr/bin/env python3
"""
PreToolUse - Breadcrumb Step Gate
==================================

Verifies that the current tool is a valid progression from the last completed step.

This gate implements per-step breadcrumb verification:
1. Get current tool being called
2. Get current skill context from breadcrumb state
3. Determine the next expected step from workflow_steps
4. Check if current tool is valid for that step
5. Block if invalid progression (before wasted work)

This is superior to Stop-hook verification because it blocks BEFORE
tokens are spent generating a response, not after.

Configuration:
- BREADCRUMB_GATE_ENABLED (default: true)
- BREADCRUMB_GATE_MODE (default: advisory) - advisory or block
- BREADCRUMB_GATE_ADVISORY_ONLY_LIST - comma-separated skills to always advisory

Author: ADR-20260327-breadcrumb-per-step-verification
Date: 2026-03-27
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add skill-guard to path
from __lib.skill_guard_path import ensure_skill_guard_in_syspath
ensure_skill_guard_in_syspath()

# Configuration
ENABLED = os.environ.get("BREADCRUMB_GATE_ENABLED", "true").lower() in ("1", "true", "yes")
MODE = os.environ.get("BREADCRUMB_GATE_MODE", "advisory").lower()  # "advisory" or "block"

# Skills that should always use advisory mode (not blocking)
ADVISORY_ONLY = set(
    s.strip().lower()
    for s in os.environ.get("BREADCRUMB_GATE_ADVISORY_ONLY_LIST", "").split(",")
    if s.strip()
)

# Tool to step kind mappings (from inference.py)
TOOL_TO_STEP_KIND: dict[str, str] = {
    # Research tools
    "WebSearch": "research",
    "mcp__tavily-mcp__tavily_search": "research",
    "mcp__tavily-mcp__tavily_research": "research",
    "mcp__perplexity__perplexity_search": "research",
    "mcp__perplexity__perplexity_ask": "research",
    "mcp__perplexity__perplexity_research": "research",
    "mcp__exa__get_code_context_exa": "research",
    # Requirements tools
    "Read": "requirements",
    "Glob": "requirements",
    "Grep": "requirements",
    "LSP": "requirements",
    # TDD/Implementation tools
    "Edit": "tdd",
    "Write": "tdd",
    "NotebookEdit": "tdd",
    # Verification tools
    "Bash": "verification",
    "Skill": "verification",
    # Planning tools
    "AskUserQuestion": "planning",
    "EnterPlanMode": "planning",
    "ExitPlanMode": "planning",
    # Agent tools
    "Agent": "agent_coordination",
}


def _get_step_kind_from_tool(tool_name: str) -> str | None:
    """Infer step kind from tool name.

    Args:
        tool_name: Name of the tool being used

    Returns:
        Step kind (e.g., "research", "tdd") or None if not mappable
    """
    # Check exact match
    if tool_name in TOOL_TO_STEP_KIND:
        return TOOL_TO_STEP_KIND[tool_name]

    # Check prefix match
    for mapped_tool, step_kind in TOOL_TO_STEP_KIND.items():
        if tool_name.startswith(mapped_tool):
            return step_kind

    # Pattern-based inference
    tool_lower = tool_name.lower()
    if "search" in tool_lower:
        return "research"
    if "read" in tool_lower or "get" in tool_lower:
        return "requirements"
    if "edit" in tool_lower or "write" in tool_lower:
        return "tdd"
    if "bash" in tool_lower or "run" in tool_lower:
        return "verification"
    if "agent" in tool_lower:
        return "agent_coordination"

    return None


def _get_expected_next_step(trail: dict) -> dict | None:
    """Get the next expected step from workflow_steps.

    Args:
        trail: Breadcrumb trail dict with workflow_steps and completed_steps

    Returns:
        Next step dict or None if all complete
    """
    workflow_steps = trail.get("workflow_steps", [])
    completed = set(trail.get("completed_steps", []))

    for step in workflow_steps:
        step_id = step.get("id") if isinstance(step, dict) else step
        if step_id not in completed:
            # Check if step has a kind
            step_kind = step.get("kind", "execution") if isinstance(step, dict) else "execution"
            # Skip optional verification steps
            if (
                isinstance(step, dict)
                and step.get("optional", False)
                and step_kind == "verification"
            ):
                continue
            return {"id": step_id, "kind": step_kind}

    return None


def _is_valid_progression(tool_name: str, expected_step: dict) -> bool:
    """Check if tool is valid for the expected step.

    Args:
        tool_name: Current tool being called
        expected_step: Next expected step dict with id and kind

    Returns:
        True if tool is valid progression
    """
    tool_kind = _get_step_kind_from_tool(tool_name)
    if tool_kind is None:
        # Unknown tool - allow
        return True

    expected_kind = expected_step.get("kind", "execution")

    # Same kind is always valid
    if tool_kind == expected_kind:
        return True

    # Allow transitions within execution phases
    # research -> requirements -> tdd -> verification is the normal flow
    # But allow going back (e.g., research after tdd) for investigation
    STEP_ORDER = [
        "research",
        "requirements",
        "tdd",
        "verification",
        "agent_coordination",
        "planning",
    ]

    try:
        tool_idx = STEP_ORDER.index(tool_kind)
        expected_idx = STEP_ORDER.index(expected_kind)
        # Allow if we're before or at the expected step
        # (can do earlier steps but not skip ahead)
        return tool_idx <= expected_idx
    except ValueError:
        # Unknown kind - allow
        return True


def _get_skill_from_context(data: dict) -> str | None:
    """Get skill name from breadcrumb trail context.

    Args:
        data: PreToolUse hook input data

    Returns:
        Skill name or None if not in skill context
    """
    try:
        from skill_guard.breadcrumb.tracker import get_active_breadcrumb_trails

        trails = get_active_breadcrumb_trails()
        if not trails:
            return None

        # Return the first active trail's skill
        # (typically there should only be one active skill at a time)
        return trails[0].get("skill")

    except ImportError:
        return None
    except Exception:
        return None


def run(data: dict) -> dict:
    """PreToolUse hook entry point.

    Args:
        data: Hook input with tool_name, tool_input, etc.

    Returns:
        {"continue": bool, "reason": str} dict
    """
    # Always allow if disabled
    if not ENABLED:
        return {"continue": True}

    tool_name = data.get("tool_name", "")

    # Always allow Skill tool (workflow initiation)
    if tool_name == "Skill":
        return {"continue": True}

    # Get current skill context
    skill_name = _get_skill_from_context(data)
    if not skill_name:
        # No active breadcrumb trail
        return {"continue": True}

    # Check advisory only list
    is_advisory = MODE == "advisory" or skill_name.lower() in ADVISORY_ONLY

    try:
        from skill_guard.breadcrumb.tracker import get_breadcrumb_trail

        trail = get_breadcrumb_trail(skill_name)
        if not trail:
            return {"continue": True}

        completed = trail.get("completed_steps", [])
        if not completed:
            # Just started - allow first tool
            return {"continue": True}

        # Get expected next step
        next_step = _get_expected_next_step(trail)
        if not next_step:
            # All steps complete
            return {"continue": True}

        # Check if current tool is valid for next step
        if _is_valid_progression(tool_name, next_step):
            return {"continue": True}

        # Invalid progression - block or warn
        step_id = next_step.get("id", "unknown")
        step_kind = next_step.get("kind", "execution")
        tool_kind = _get_step_kind_from_tool(tool_name) or "unknown"

        message = (
            f"Invalid step progression for skill '{skill_name}':\n"
            f"  Next expected: {step_id} ({step_kind})\n"
            f"  Current tool: {tool_name} ({tool_kind})\n"
            f"\n"
            f"Complete '{step_id}' before using {tool_name}.\n"
            f"Hint: The next step should be: {step_id}"
        )

        if is_advisory:
            return {"continue": True, "warning": message}
        else:
            return {"continue": False, "reason": message}

    except ImportError:
        # skill_guard not available - fail open
        return {"continue": True}
    except Exception:
        # Unexpected error - fail open
        return {"continue": True}


if __name__ == "__main__":
    import json

    input_text = sys.stdin.read().strip()
    if not input_text:
        data = {}
    else:
        try:
            data = json.loads(input_text)
        except json.JSONDecodeError:
            data = {}

    result = run(data)
    print(json.dumps(result))
