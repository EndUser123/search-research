#!/usr/bin/env python3
"""
PostToolUse Format Validator for /gto skill

Validates /gto output format after execution to ensure required sections
are present and properly formatted.

This is a skill-based hook - defined in GTO SKILL.md frontmatter.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# State directory for checklist tracking (skill-relative path)
_SCRIPT_DIR = Path(__file__).resolve().parent
_STATE_DIR = _SCRIPT_DIR.parent / ".state"

REQUIRED_SECTIONS = [
    (r"\*\*Status Details\*\*", "**Status Details**"),
    (r"\*\*Recommended Next Steps\*\*", "**Recommended Next Steps**"),
]

VALID_TERMINATOR = re.compile(r"^0\s*-\s*(Do ALL|Nothing left to do)", re.MULTILINE)

SNAPSHOT_PATTERN = re.compile(r"=== GTO SNAPSHOT ===", re.MULTILINE)

# Domain/action format: "1 - Description" or "1 (DOMAIN) - Description"
DOMAIN_HEADER = re.compile(r"^[1-9]\d*\s*(?:\([^)]+\))?\s*-\s+.+", re.MULTILINE)

# Action format: "- 1a: Action description"
ACTION_LINE = re.compile(r"^\s*-\s*\d+[a-z]:\s+.+", re.MULTILINE)


def get_terminal_id() -> str:
    """Get terminal ID from environment."""
    return os.environ.get("CLAUDE_TERMINAL_ID", "default") or "default"


def save_checklist_state(terminal_id: str, items: list[str]) -> None:
    """Save checklist items to state file for Stop hook."""
    state_file = _STATE_DIR / f"gto_checklist_{terminal_id}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "items": items,
        "timestamp": datetime.now().isoformat(),
        "addressed": [],
    }

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def save_session_state(terminal_id: str) -> None:
    """Save session state indicating /gto was invoked."""
    state_file = _STATE_DIR / f"gto_session_{terminal_id}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "gto_invoked": True,
        "timestamp": datetime.now().isoformat(),
    }

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def extract_checklist_items(output: str) -> list[str]:
    """Extract checklist items from /gto output."""
    items = []

    # Checklist patterns from /gto SKILL.md
    CHECKLIST_PATTERNS = [
        r"🟋\s*Documentation updates",
        r"🟋\s*Tests for new/modified code",
        r"🟋\s*Git commit for completed work",
        r"🟋\s*Configuration changes documented",
        r"🟋\s*Dependencies verified before use",
        r"🟋\s*Breaking changes noted",
        r"🟋\s*Performance/security implications considered",
    ]

    for pattern in CHECKLIST_PATTERNS:
        if re.search(pattern, output):
            items.append(pattern)

    return items


def validate_gto_output(output: str) -> tuple[bool, list[str]]:
    """
    Validate /gto output format.

    Args:
        output: The /gto skill output text

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not output or not output.strip():
        return True, []  # Empty output is valid (no findings)

    # Check required sections
    for pattern, name in REQUIRED_SECTIONS:
        if not re.search(pattern, output):
            errors.append(f"Missing required section: {name}")

    # Check terminator
    if "**Recommended Next Steps**" in output:
        if not VALID_TERMINATOR.search(output):
            errors.append(
                "Missing required terminator: '0 - Do ALL Recommended Next Steps' "
                "or '0 - Nothing left to do'"
            )

        # Check domain/action format if Recommended Next Steps exists
        if "Nothing left to do" not in output:
            # Check for at least one domain header
            if not DOMAIN_HEADER.search(output):
                errors.append(
                    "Missing domain header format: expected '1 - Description' or "
                    "'1 (DOMAIN) - Description'"
                )

            # Check for at least one action line (if domains exist)
            if DOMAIN_HEADER.search(output) and not ACTION_LINE.search(output):
                errors.append("Missing action format: expected '- 1a: Action description'")

    return len(errors) == 0, errors


def main(tool_name: str, tool_result: dict[str, Any]) -> tuple[bool, str]:
    """
    Main hook entry point.

    Args:
        tool_name: Name of the tool that was invoked
        tool_result: Result from the tool invocation

    Returns:
        Tuple of (should_block, message)
    """
    # Only validate /gto skill invocations
    if tool_name != "Skill":
        return False, ""

    # Extract skill name from input
    tool_input = tool_result.get("input", {})
    skill_name = tool_input.get("skill", "")

    if skill_name != "gto":
        return False, ""

    # Get output
    output = tool_result.get("output", "")
    if isinstance(output, dict):
        output = output.get("content", str(output))

    # Save session state (indicates /gto was invoked)
    terminal_id = get_terminal_id()
    save_session_state(terminal_id)

    # Extract and save checklist items for Stop hook
    checklist_items = extract_checklist_items(output)
    if checklist_items:
        save_checklist_state(terminal_id, checklist_items)

    # Validate
    is_valid, errors = validate_gto_output(output)

    if not is_valid:
        # Return warning (don't block)
        msg = "[GTO Format Validator] Output format issues:\n"
        for i, error in enumerate(errors, 1):
            msg += f"  {i}. {error}\n"
        return False, msg

    return False, ""


if __name__ == "__main__":
    # Test validation
    test_output = """
=== GTO SNAPSHOT ===
- Status: Test

**Status Details**
- Test item

**Recommended Next Steps**
1 - Test domain
- 1a: Test action

0 - Do ALL Recommended Next Steps
"""
    is_valid, errors = validate_gto_output(test_output)
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
