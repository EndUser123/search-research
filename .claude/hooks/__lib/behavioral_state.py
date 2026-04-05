#!/usr/bin/env python3
"""Behavioral State Management for Truth & Evidence Hooks Modernization.

Provides session-scoped state storage for goal anchoring, confidence tracking,
and evidence tier metadata. Integrates with existing StateManager abstraction.

Per plan Phase 1:
- GoalAnchor dataclass (text, scope, confidence, action_type, target)
- UserGoal dataclass
- load_behavioral_state() function
- save_behavioral_state() function
- Session-based state storage with TTL
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from state_manager import StateManager

# Default TTL for behavioral state (2 hours in seconds)
DEFAULT_TTL_SECONDS = 7200

# State directory
STATE_DIR = Path("P:/.claude/state")


class GoalScope(Enum):
    """Goal scope categories from goal extraction patterns."""
    MODIFICATION = "modification"
    CREATION = "creation"
    ANALYSIS = "analysis"


@dataclass(frozen=True)
class GoalAnchor:
    """Structured representation of an extracted goal.

    Attributes:
        text: Full goal text (e.g., "fix authentication bug")
        action_type: Action verb (e.g., "fix", "create", "analyze")
        target: Target object (e.g., "authentication bug", "API endpoint")
        scope: Goal category (modification, creation, analysis)
        confidence: How likely this is the PRIMARY goal (0.1-1.0)
        position_in_prompt: Character position where goal was found
        timestamp: Unix timestamp when goal was extracted
    """
    text: str
    action_type: str
    target: str
    scope: GoalScope
    confidence: float
    position_in_prompt: int
    timestamp: float

    def __post_init__(self) -> None:
        """Validate confidence is between 0 and 1."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

    def is_stale(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
        """Check if this goal anchor is stale (older than TTL).

        Args:
            ttl_seconds: Time-to-live in seconds (default: 2 hours)

        Returns:
            True if goal anchor is stale
        """
        age = time.time() - self.timestamp
        return age > ttl_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "action_type": self.action_type,
            "target": self.target,
            "scope": self.scope.value,
            "confidence": self.confidence,
            "position_in_prompt": self.position_in_prompt,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GoalAnchor:
        """Create GoalAnchor from dictionary.

        Args:
            data: Dictionary with goal anchor fields

        Returns:
            GoalAnchor instance
        """
        return cls(
            text=data["text"],
            action_type=data["action_type"],
            target=data["target"],
            scope=GoalScope(data["scope"]),
            confidence=data["confidence"],
            position_in_prompt=data["position_in_prompt"],
            timestamp=data["timestamp"],
        )


@dataclass(frozen=True)
class UserGoal:
    """User's goal for the current session.

    Combines goal anchor with session metadata for downstream hooks.
    """
    anchor: GoalAnchor
    session_id: str
    terminal_id: str
    created_at: float

    def is_stale(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
        """Check if this user goal is stale."""
        age = time.time() - self.created_at
        return age > ttl_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "anchor": self.anchor.to_dict(),
            "session_id": self.session_id,
            "terminal_id": self.terminal_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UserGoal:
        """Create UserGoal from dictionary."""
        return cls(
            anchor=GoalAnchor.from_dict(data["anchor"]),
            session_id=data["session_id"],
            terminal_id=data["terminal_id"],
            created_at=data["created_at"],
        )


def get_session_id() -> str:
    """Get consistent session ID for behavioral state.

    Uses parent PID (Claude Code's process) for consistency across
    hook invocations within the same session.

    Returns:
        Session ID string
    """
    # Try environment variable first
    if env_id := os.environ.get("CLAUDE_SESSION_ID"):
        return env_id

    # Use parent process ID
    try:
        return str(os.getppid())
    except (AttributeError, OSError):
        # Fallback to current PID (less reliable)
        return str(os.getpid())


def get_terminal_id() -> str:
    """Get terminal ID for session isolation.

    Returns:
        Terminal ID string
    """
    # Try terminal detection module
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from __lib.terminal_detection import detect_terminal_id
        return detect_terminal_id()
    except Exception:
        # Fallback to session ID
        return get_session_id()


def load_behavioral_state(
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> UserGoal | None:
    """Load behavioral state from storage.

    Args:
        session_id: Session ID (uses current if None)
        terminal_id: Terminal ID (uses current if None)

    Returns:
        UserGoal if found and not stale, None otherwise
    """
    sid = session_id or get_session_id()
    tid = terminal_id or get_terminal_id()

    state_key = f"behavioral_goal_{sid}_{tid}"

    try:
        manager = StateManager(STATE_DIR)
        state = manager.read_state(state_key)

        if not state:
            return None

        user_goal = UserGoal.from_dict(state)

        # Check if stale
        if user_goal.is_stale():
            # Clean up stale state
            try:
                state_file = manager._state_path(state_key)
                state_file.unlink(missing_ok=True)
            except Exception:
                pass
            return None

        return user_goal

    except Exception:
        return None


def save_behavioral_state(
    goal: GoalAnchor,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> UserGoal:
    """Save behavioral state to storage.

    Args:
        goal: GoalAnchor to persist
        session_id: Session ID (uses current if None)
        terminal_id: Terminal ID (uses current if None)

    Returns:
        UserGoal with session metadata
    """
    sid = session_id or get_session_id()
    tid = terminal_id or get_terminal_id()

    user_goal = UserGoal(
        anchor=goal,
        session_id=sid,
        terminal_id=tid,
        created_at=time.time(),
    )

    state_key = f"behavioral_goal_{sid}_{tid}"

    try:
        manager = StateManager(STATE_DIR)
        manager.write_state(state_key, user_goal.to_dict())
    except Exception:
        # Fail silently - state is advisory
        pass

    return user_goal


def clear_behavioral_state(
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> bool:
    """Clear behavioral state from storage.

    Args:
        session_id: Session ID (uses current if None)
        terminal_id: Terminal ID (uses current if None)

    Returns:
        True if state was cleared, False otherwise
    """
    sid = session_id or get_session_id()
    tid = terminal_id or get_terminal_id()

    state_key = f"behavioral_goal_{sid}_{tid}"

    try:
        manager = StateManager(STATE_DIR)
        state_file = manager._state_path(state_key)

        if state_file.exists():
            state_file.unlink()
            return True

        return False

    except Exception:
        return False


def cleanup_stale_behavioral_state(ttl_seconds: int = DEFAULT_TTL_SECONDS) -> int:
    """Clean up stale behavioral state files.

    Args:
        ttl_seconds: TTL in seconds (default: 2 hours)

    Returns:
        Number of state files cleaned up
    """
    cleaned = 0

    try:
        manager = StateManager(STATE_DIR)
        current_time = time.time()

        # Find all behavioral_goal_* state files
        for state_file in STATE_DIR.glob("behavioral_goal_*.json"):
            try:
                # Check file age
                file_age = current_time - state_file.stat().st_mtime
                if file_age > ttl_seconds:
                    state_file.unlink(missing_ok=True)
                    cleaned += 1
            except Exception:
                pass

    except Exception:
        pass

    return cleaned


def get_current_goal(
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> GoalAnchor | None:
    """Get the current goal anchor (convenience function).

    Args:
        session_id: Session ID (uses current if None)
        terminal_id: Terminal ID (uses current if None)

    Returns:
        GoalAnchor if found, None otherwise
    """
    user_goal = load_behavioral_state(session_id, terminal_id)
    return user_goal.anchor if user_goal else None


def set_current_goal(
    text: str,
    action_type: str,
    target: str,
    scope: GoalScope,
    confidence: float,
    position_in_prompt: int = 0,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> GoalAnchor:
    """Create and save a goal anchor (convenience function).

    Args:
        text: Goal text
        action_type: Action verb
        target: Target object
        scope: Goal scope
        confidence: Confidence score
        position_in_prompt: Position in prompt
        session_id: Session ID (uses current if None)
        terminal_id: Terminal ID (uses current if None)

    Returns:
        Created GoalAnchor
    """
    goal = GoalAnchor(
        text=text,
        action_type=action_type,
        target=target,
        scope=scope,
        confidence=confidence,
        position_in_prompt=position_in_prompt,
        timestamp=time.time(),
    )

    save_behavioral_state(goal, session_id, terminal_id)
    return goal
