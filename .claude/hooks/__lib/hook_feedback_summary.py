"""Hook feedback summary module for user-friendly blocking messages.

This module provides functions to format blocking hook results into
user-friendly messages with actionable guidance.
"""

from typing import Dict


def format_blocking_summary(block_result: Dict) -> str:
    """Format a blocking hook result into a user-friendly summary.

    Args:
        block_result: Dictionary containing blocking information with keys:
            - blocking_hook: Name of the hook that blocked (optional)
            - reason: Explanation for the block (optional)
            - decision: 'deny' or similar (optional)

    Returns:
        Formatted string with hook name, reason, and actionable guidance.
    """
    hook_name = block_result.get("blocking_hook", "Unknown hook")
    reason = block_result.get("reason", "Action blocked by hook policy")

    # Extract guidance based on hook type
    guidance = _get_guidance_for_hook(hook_name)

    # Build summary
    lines = [
        "",
        "╌─────────────────────────────────────────────────────────────",
        f"⛔ BLOCKED: {hook_name}",
        "╞─────────────────────────────────────────────────────────────",
    ]

    # Add reason if provided
    if reason and reason.strip():
        lines.append(f"│ {reason}")

    # Add guidance
    if guidance:
        lines.append("│")
        lines.append(f"│ 💡 {guidance}")

    lines.append("╘─────────────────────────────────────────────────────────────")
    lines.append("")

    return "\n".join(lines)


def _get_guidance_for_hook(hook_name: str) -> str:
    """Get actionable guidance for a specific blocking hook.

    Args:
        hook_name: Name of the hook that blocked.

    Returns:
        Actionable guidance text, or empty string if no specific guidance.
    """
    guidance_map = {
        "authorization_gate": (
            "Destructive commands require explicit authorization. "
            "Use phrases like 'proceed', 'do it', or 'go ahead' to confirm."
        ),
        "planning_mode_gate": (
            "This action requires planning mode. "
            "Start with a plan or architecture design first."
        ),
        "tdd_gate": (
            "Code changes require tests first. "
            "Write failing tests (RED), implement to pass (GREEN), then refactor."
        ),
        "investigation_gate": (
            "Code modification requires investigation first. "
            "Use /debug or /rca to understand the issue before changing code."
        ),
        "directory_policy": (
            "Protected directory. "
            "Write to project directories or use .claude/ for generated content."
        ),
        "skill_pattern_gate": (
            "Skill execution validation failed. "
            "Check skill syntax and parameters, or use /help for guidance."
        ),
        "vague_directive_gate": (
            "Request is too vague. "
            "Provide specific requirements or use /arch for architecture analysis."
        ),
        "hook_edit_gate": (
            "Hook modifications require testing first. "
            "Write tests to verify hook behavior before editing."
        ),
        "git_safety": (
            "Git operation requires explicit confirmation. "
            "Use 'proceed' or 'do it' to confirm destructive git operations."
        ),
    }

    # Find matching guidance (support partial matches)
    for key, guidance in guidance_map.items():
        if key.lower() in hook_name.lower():
            return guidance

    # Default guidance for unknown hooks
    return "Review the hook requirements and modify your approach accordingly."


# Module export
__all__ = ["format_blocking_summary"]
