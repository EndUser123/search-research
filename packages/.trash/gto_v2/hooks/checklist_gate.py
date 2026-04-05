#!/usr/bin/env python3
"""
Stop Checklist Gate for /gto skill

Reminds about pending checklist items before session ends.

This is a skill-based hook - defined in GTO SKILL.md frontmatter.
"""

import json
import os
from pathlib import Path

# State directory for checklist tracking (skill-relative path)
_SCRIPT_DIR = Path(__file__).resolve().parent
_STATE_DIR = _SCRIPT_DIR.parent / ".state"


def get_terminal_id() -> str:
    """Get terminal ID from environment."""
    return os.environ.get("CLAUDE_TERMINAL_ID", "default") or "default"


def load_checklist_state(terminal_id: str) -> dict | None:
    """Load checklist state from file."""
    state_file = _STATE_DIR / f"gto_checklist_{terminal_id}.json"

    if not state_file.exists():
        return None

    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def main(prompt: str, bypass_flag: bool = False) -> tuple[bool, str]:
    """
    Main hook entry point.

    Args:
        prompt: The user's prompt message
        bypass_flag: Whether --skip-gto-checklist flag is present

    Returns:
        Tuple of (should_block, message)
    """
    # Check for bypass flag
    if bypass_flag or "--skip-gto-checklist" in prompt.lower():
        return False, ""

    terminal_id = get_terminal_id()
    state = load_checklist_state(terminal_id)

    if not state:
        return False, ""

    items = state.get("items", [])
    addressed = state.get("addressed", [])

    # Filter out addressed items
    pending = [item for item in items if item not in addressed]

    if not pending:
        return False, ""

    # Build reminder message
    msg = "📋 PENDING GTO CHECKLIST ITEMS\n\n"
    msg += "The following items from /gto have not been addressed:\n"

    for item in pending:
        # Convert pattern to readable description
        if "Documentation updates" in item:
            msg += "  • 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)\n"
        elif "Tests for new/modified code" in item:
            msg += "  • 🟋 Tests for new/modified code\n"
        elif "Git commit for completed work" in item:
            msg += "  • 🟋 Git commit for completed work\n"
        elif "Configuration changes documented" in item:
            msg += "  • 🟋 Configuration changes documented\n"
        elif "Dependencies verified before use" in item:
            msg += "  • 🟋 Dependencies verified before use\n"
        elif "Breaking changes noted" in item:
            msg += "  • 🟋 Breaking changes noted\n"
        elif "Performance/security implications considered" in item:
            msg += "  • 🟋 Performance/security implications considered\n"
        else:
            msg += f"  • {item}\n"

    msg += "\nTo skip this check: Add --skip-gto-checklist to your message"

    # Don't block, just warn
    return False, msg


if __name__ == "__main__":
    # Test
    should_block, message = main("test prompt", bypass_flag=False)
    print(f"Block: {should_block}")
    print(f"Message: {message}")
