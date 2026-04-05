"""
Sequential thinking state management.

Provides CRUD operations for sequential thinking sessions with multi-terminal
safety via terminal_id isolation.

State file schema:
{
  "session_id": "uuid",
  "trigger_phrase": "string",
  "current_iteration": 0,
  "max_iterations": 2,
  "mode": "initial|critique|improvement",
  "intermediate_answers": [],
  "final_answer": null,
  "active": true,
  "terminal_id": "identifier"
}
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

# State directory location
STATE_DIR = Path("P:/").resolve() / ".claude" / "state" / "sequential-thinking"

# Ensure state directory exists
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _get_state_path(session_id: uuid.UUID, terminal_id: str = "") -> Path:
    """Get the state file path for a session.

    For multi-terminal isolation, state files include terminal_id in the filename.

    Args:
        session_id: Unique session identifier
        terminal_id: Terminal identifier for multi-terminal isolation

    Returns:
        Path to state file
    """
    if terminal_id:
        return STATE_DIR / f"{session_id}_{terminal_id}.json"
    return STATE_DIR / f"{session_id}.json"


def create_state(session_id: uuid.UUID, trigger_phrase: str, terminal_id: str) -> dict:
    """Create a new sequential thinking state file.

    Args:
        session_id: Unique session identifier
        trigger_phrase: The trigger phrase that started sequential thinking
        terminal_id: Terminal identifier for multi-terminal isolation

    Returns:
        Created state dict
    """
    state = {
        "session_id": str(session_id),
        "trigger_phrase": trigger_phrase,
        "current_iteration": 0,
        "max_iterations": 2,
        "mode": "initial",
        "intermediate_answers": [],
        "final_answer": None,
        "active": True,
        "terminal_id": terminal_id,
    }

    state_path = _get_state_path(session_id, terminal_id)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    return state


def load_state(session_id: uuid.UUID, terminal_id: str = "") -> dict | None:
    """Load a sequential thinking state file.

    Args:
        session_id: Unique session identifier
        terminal_id: Terminal identifier for multi-terminal isolation

    Returns:
        State dict if found, None otherwise
    """
    state_path = _get_state_path(session_id, terminal_id)

    if not state_path.exists():
        return None

    return json.loads(state_path.read_text(encoding="utf-8"))


def update_state(session_id: uuid.UUID, updates: dict, terminal_id: str = "") -> None:
    """Update a sequential thinking state file.

    Args:
        session_id: Unique session identifier
        updates: Dict of fields to update
        terminal_id: Terminal identifier for multi-terminal isolation
    """
    state = load_state(session_id, terminal_id)
    if state is None:
        return

    state.update(updates)

    state_path = _get_state_path(session_id, terminal_id)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def delete_state(session_id: uuid.UUID, terminal_id: str = "") -> None:
    """Delete a sequential thinking state file.

    Args:
        session_id: Unique session identifier
        terminal_id: Terminal identifier for multi-terminal isolation
    """
    state_path = _get_state_path(session_id, terminal_id)
    if state_path.exists():
        state_path.unlink()


def add_intermediate_answer(session_id: uuid.UUID, answer: str, terminal_id: str = "") -> None:
    """Add an intermediate answer to the state.

    Args:
        session_id: Unique session identifier
        answer: The intermediate answer to add
        terminal_id: Terminal identifier for multi-terminal isolation
    """
    state = load_state(session_id, terminal_id)
    if state is None:
        return

    state["intermediate_answers"].append(answer)

    update_state(session_id, {"intermediate_answers": state["intermediate_answers"]}, terminal_id)


def set_final_answer(session_id: uuid.UUID, final_answer: str, terminal_id: str = "") -> None:
    """Set the final answer and delete the session state file.

    Args:
        session_id: Unique session identifier
        final_answer: The final improved answer
        terminal_id: Terminal identifier for multi-terminal isolation
    """
    update_state(
        session_id,
        {"final_answer": final_answer, "active": False},
        terminal_id,
    )
    delete_state(session_id, terminal_id)


def should_continue(session_id: uuid.UUID, terminal_id: str = "") -> bool:
    """Check if a sequential thinking session should continue.

    Args:
        session_id: Unique session identifier
        terminal_id: Terminal identifier for multi-terminal isolation

    Returns:
        True if session should continue, False otherwise
    """
    state = load_state(session_id, terminal_id)
    if state is None:
        return False

    # Check if session is active
    if not state.get("active", True):
        return False

    # Check if max iterations reached
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 2)

    return current_iteration < max_iterations
