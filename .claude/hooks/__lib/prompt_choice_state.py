#!/usr/bin/env python3
"""
Prompt Choice State Manager

Manages state for prompt enhancement choice system.
When the prompt enhancement hook modifies a user's prompt,
this system stores both versions and presents a choice.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

STATE_DIR = Path("P:/.claude/state/prompt_choice")
CHOICE_TIMEOUT = 300  # 5 minutes


def _get_session_id(session_id: str | None = None, terminal_id: str | None = None) -> str:
    """Get stable session identifier.

    Priority: session_id > terminal_id > environment > PID (fallback)

    Args:
        session_id: Session ID from hook input
        terminal_id: Terminal ID from hook input

    Returns:
        Stable identifier string
    """
    if session_id:
        return f"session_{session_id}"
    if terminal_id:
        return f"terminal_{terminal_id}"
    # Try environment variable
    if env_id := os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_TERMINAL_ID"):
        return str(env_id)
    # Fallback to current PID (least stable)
    return f"pid_{os.getpid()}"


def _get_state_file(session_id: str | None = None, terminal_id: str | None = None) -> Path:
    """Get state file path for current terminal.

    Args:
        session_id: Session ID from hook input
        terminal_id: Terminal ID from hook input
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / f"{_get_session_id(session_id, terminal_id)}.json"


def save_prompt_choice(
    original: str,
    enhanced: str,
    injection: str,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> None:
    """Store both prompts and the injection.

    Args:
        original: The user's original prompt
        enhanced: The enhanced version after modification
        injection: The additionalContext that was injected
    """
    state = {
        "original_prompt": original,
        "enhanced_prompt": enhanced,
        "injection": injection,
        "waiting_for_choice": True,
        "created_at": time.monotonic()
    }

    state_file = _get_state_file(session_id, terminal_id)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_pending_choice(
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> dict | None:
    """Get pending prompt choice if exists.

    Returns:
        State dict if waiting for choice, None otherwise
    """
    state_file = _get_state_file(session_id, terminal_id)
    if not state_file.exists():
        return None

    try:
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)

        # Check if waiting for choice and not expired
        if not state.get("waiting_for_choice"):
            return None

        if time.monotonic() - state.get("created_at", 0) > CHOICE_TIMEOUT:
            # Expired - clean up
            state_file.unlink(missing_ok=True)
            return None

        return state
    except (json.JSONDecodeError, OSError):
        return None


def clear_prompt_choice(
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> None:
    """Clear the prompt choice state.

    Args:
        session_id: Session ID from hook input
        terminal_id: Terminal ID from hook input
    """
    state_file = _get_state_file(session_id, terminal_id)
    state_file.unlink(missing_ok=True)


def get_chosen_prompt() -> str | None:
    """Get the user's chosen prompt based on their response.

    This is called in the next turn to determine which prompt to use.

    Returns:
        The chosen prompt, or None if no choice was made
    """
    state = get_pending_choice()
    if not state:
        return None

    # Check user's response for choice indicators
    # This will be called with the user's latest message
    # For now, we'll check if there's a "[0]" or "[1]" pattern
    # The actual detection will happen in the hook
    return state.get("enhanced_prompt")  # Default to enhanced


def detect_choice_from_message(message: str) -> str | None:
    """Detect user's choice from their message.

    Args:
        message: The user's message text

    Returns:
        "original" if user chose original, "enhanced" if enhanced, None if no choice
    """
    message_stripped = message.strip()

    # Check for number patterns (priority - matches /p style)
    # Match "0", "0 -", "0 - Use", etc. at start of message
    if re.match(r"^0(\s*-|\s+|$)", message_stripped):
        return "enhanced"
    if re.match(r"^1(\s*-|\s+|$)", message_stripped):
        return "original"

    # Fallback to word patterns for clarity
    message_lower = message_stripped.lower()
    if any(pattern in message_lower for pattern in ["[0]", "zero", "enhanced"]):
        return "enhanced"
    if any(pattern in message_lower for pattern in ["[1]", "one", "original"]):
        return "original"

    return None


if __name__ == "__main__":
    # Test the state manager

    print("Testing prompt choice state manager...")

    # Save a test choice
    save_prompt_choice(
        original="fix this",
        enhanced="fix this by adding error handling",
        injection="**Clarification**: What should be fixed?"
    )
    print(f"Saved choice to {_get_state_file()}")

    # Retrieve it
    choice = get_pending_choice()
    if choice:
        print(f"Retrieved: {choice['original_prompt']}")
        print(f"Enhanced: {choice['enhanced_prompt']}")

    # Clean up
    clear_prompt_choice()
    print("State cleared")
