#!/usr/bin/env python3
"""
SessionEnd Reminder for /gto skill

Shows session summary and cleanup state files at session end.

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


def load_session_state(terminal_id: str) -> dict | None:
    """Load session state from file."""
    state_file = _STATE_DIR / f"gto_session_{terminal_id}.json"

    if not state_file.exists():
        return None

    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


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


def cleanup_state_files(terminal_id: str) -> None:
    """Clean up state files after session."""
    session_file = _STATE_DIR / f"gto_session_{terminal_id}.json"
    checklist_file = _STATE_DIR / f"gto_checklist_{terminal_id}.json"

    # Remove session state file
    if session_file.exists():
        try:
            session_file.unlink()
        except OSError:
            pass

    # Keep checklist file for next session (it tracks pending items)


def main() -> tuple[bool, str]:
    """
    Main hook entry point.

    Returns:
        Tuple of (should_block, message)
    """
    terminal_id = get_terminal_id()
    session_state = load_session_state(terminal_id)

    if not session_state:
        # No /gto invocation this session
        return False, ""

    # Build session summary
    msg = "📋 **GTO SESSION SUMMARY**\n\n"
    msg += "✅ /gto was invoked this session\n\n"

    # Load checklist state
    checklist_state = load_checklist_state(terminal_id)

    if checklist_state:
        items = checklist_state.get("items", [])
        addressed = checklist_state.get("addressed", [])
        pending = [item for item in items if item not in addressed]

        if pending:
            msg += "⚠️ **Pending checklist items:**\n"
            for item in pending:
                if "Documentation updates" in item:
                    msg += (
                        "  • 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)\n"
                    )
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
        else:
            msg += "✅ All checklist items addressed\n"
    else:
        msg += "ℹ️ No checklist items tracked\n"

    msg += "\nRun /gto to check session status anytime."

    # Clean up session state file
    cleanup_state_files(terminal_id)

    # Don't block, just inform
    return False, msg


if __name__ == "__main__":
    # Test
    should_block, message = main()
    print(f"Block: {should_block}")
    print(f"Message: {message}")
