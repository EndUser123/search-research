#!/usr/bin/env python3
"""PreToolUse hook: Detect blocked Write operations with matching Read permissions and offer recovery."""

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

from permission_recovery import (
    find_matching_read_permission,
    generate_permission_diff,
    generate_write_pattern,
    validate_proposed_permission,
)


def load_settings_json() -> dict:
    """Load and parse settings.json."""
    settings_path = Path.home() / ".claude" / "settings.json"
    with open(settings_path, encoding='utf-8') as f:
        return json.load(f)


def get_write_path(data: dict) -> str:
    """Extract file path from Write or Edit tool input."""
    tool_input = data.get("tool_input", {})
    return tool_input.get("file_path", tool_input.get("path", ""))


def run(data: dict) -> dict | None:
    """Hook entry point - detect Read/Write permission gaps.

    Returns:
        None to allow, dict with permissionDecision to handle recovery
    """
    tool_name = data.get("tool_name", "")

    # Only process Write and Edit operations
    if tool_name not in ("Write", "Edit"):
        return None

    write_path = get_write_path(data)
    if not write_path:
        return None

    # Load settings and check for matching Read permission
    settings = load_settings_json()
    matching_read = find_matching_read_permission(write_path, settings)

    if not matching_read:
        # No matching Read - let other hooks handle blocking
        return None

    # Found Read permission, generate Write candidate
    missing_write = generate_write_pattern(matching_read)

    # Validate proposed Write permission
    is_safe, reason = validate_proposed_permission(missing_write)
    if not is_safe:
        # Dangerous pattern - block and explain why
        return {
            "decision": "block",
            "reason": (
                f"⛔ DANGEROUS PERMISSION PROPOSAL REJECTED\n\n"
                f"Write permission rejected: {reason}\n\n"
                f"Path: {write_path}\n"
                f"Proposed: {missing_write}\n\n"
                f"This pattern could enable privilege escalation. "
                f"Manual intervention required."
            ),
            "blocking_hook": "PreToolUse_permission_pair_validator.py"
        }

    # Safe permission candidate - emit recovery metadata
    return {
        "permissionDecision": "approve_if_user_confirmed",
        "permissionDecisionReason": (
            f"🔍 PERMISSION GAP DETECTED\n\n"
            f"Write operation blocked, but Read permission exists:\n"
            f"  Read:  {matching_read}\n"
            f"  Write: {missing_write} (missing)\n"
            f"  Path:  {write_path}\n\n"
            f"Auto-recovery available. Type 'y' to add Write permission, "
            f"'n' to block and see manual edit instructions."
        ),
        "blocking_hook": "PreToolUse_permission_pair_validator.py",
        "recovery_metadata": {
            "existing_read": matching_read,
            "missing_write": missing_write,
            "write_path": write_path
        }
    }


if __name__ == "__main__":
    data = json.load(sys.stdin)
    result = run(data)

    if result:
        print(json.dumps(result, indent=2))
        sys.exit(2 if result.get("decision") == "block" else 0)

    sys.exit(0)