"""
NBM-3: Circuit Breaker for Infinite Repair Turn Loop Prevention.

This module provides a circuit breaker pattern to prevent gates from
trapping the agent in infinite loops when stop_hook_active=true.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from __lib.file_lock import FileLock

# Default threshold before circuit breaker trips
DEFAULT_THRESHOLD = 3

# Lock timeout in seconds
_LOCK_TIMEOUT = 5.0

# Acceptance phrases that indicate user has accepted remediation
_ACCEPTANCE_PHRASES = [
    r"(?i)\bI(?:'ll|'d)?\s+(?:try|will\s+try)\b",
    r"(?i)\bthanks?\b",
    r"(?i)\bgot\s+it\b",
    r"(?i)\bwill\s+do\b",
    r"(?i)\bunderstood?\b",
    r"(?i)\backnowledged?\b",
    r"(?i)\bokay\s+thanks\b",
    r"(?i)\bOK\s+thanks\b",
    r"(?i)\bsounds?\s+good\b",
    r"(?i)\bthat(?:'s| is)\s+(?:a\s+)?good\s+idea\b",
    r"(?i)\blet(?:'s| me)?\s+try\s+that\b",
    r"(?i)\bI(?:'ll)?\s+give\s+it\s+a\s+try\b",
    r"(?i)\bperfect\b",
    r"(?i)\bgreat\b",
    r"(?i)\bawesome\b",
]

# Strip embedded (?i) flags since we compile with re.IGNORECASE
_normalized = [re.sub(r"^\(\?i\)", "", p) for p in _ACCEPTANCE_PHRASES]
_ACCEPTANCE_PATTERN = re.compile("|".join(_normalized), re.IGNORECASE)


class CircuitBreaker:
    """
    Circuit breaker to prevent infinite repair loops.
    """

    def __init__(
        self,
        session_id: str,
        threshold: int = DEFAULT_THRESHOLD,
    ) -> None:
        self.session_id = session_id
        self.threshold = threshold
        self.iteration_file = self._get_iteration_file()

    def _get_iteration_file(self) -> Path:
        """Get the temp file path for iteration tracking."""
        # Check environment for custom path
        env_file = os.environ.get("CIRCUIT_BREAKER_ITERATION_FILE")
        if env_file:
            base = Path(env_file).parent
            name = f"iteration_count_{self.session_id}.tmp"
            return base / name
        # Default: ~/.claude/hooks/iteration_count_{session_id}.tmp
        return Path.home() / ".claude" / "hooks" / f"iteration_count_{self.session_id}.tmp"

    def get_count(self) -> int:
        """Get current iteration count for this session."""
        if not self.iteration_file.exists():
            return 0
        try:
            return int(self.iteration_file.read_text().strip())
        except (ValueError, OSError):
            return 0

    def increment(self) -> None:
        """Increment iteration counter atomically using FileLock."""
        lock_path = self.iteration_file.with_suffix(".lock")
        lock = FileLock(lock_path, timeout=_LOCK_TIMEOUT)
        with lock:
            count = self.get_count() + 1
            self.iteration_file.parent.mkdir(parents=True, exist_ok=True)
            self.iteration_file.write_text(str(count), encoding="utf-8")

    def reset(self) -> None:
        """Reset iteration counter for this session."""
        if self.iteration_file.exists():
            self.iteration_file.unlink()

    def should_block(self) -> bool:
        """Return True if should still block, False if circuit breaker tripped."""
        return self.get_count() < self.threshold


def get_iteration_count(session_id: str) -> int:
    """
    Get current iteration count for a session.

    RED PHASE: Stub.
    """
    cb = CircuitBreaker(session_id)
    return cb.get_count()


def increment_iteration(session_id: str) -> None:
    """
    Increment iteration count for a session.

    RED PHASE: Stub.
    """
    cb = CircuitBreaker(session_id)
    cb.increment()


def reset_iteration(session_id: str) -> None:
    """
    Reset iteration count for a session.

    RED PHASE: Stub.
    """
    cb = CircuitBreaker(session_id)
    cb.reset()


def should_allow_continue(
    session_id: str,
    stop_hook_active: bool = False,
    threshold: int = DEFAULT_THRESHOLD,
) -> bool:
    """
    Determine if should allow continuation based on circuit breaker state.

    Args:
        session_id: The session identifier
        stop_hook_active: Whether stop_hook is active (circuit breaker only applies when True)
        threshold: Iteration count threshold

    Returns:
        True if should allow (circuit breaker tripped or stop_hook not active)
        False if should block (below threshold)

    RED PHASE: Stub.
    """
    if not stop_hook_active:
        # Circuit breaker doesn't apply when stop_hook not active
        return False

    cb = CircuitBreaker(session_id, threshold)
    if cb.get_count() >= threshold:
        # Circuit breaker tripped - allow continuation
        return True

    # Below threshold - should block
    return False


def check_and_reset_on_acceptance(session_id: str, user_message: str) -> bool:
    """
    Check if user message contains acceptance phrase and reset circuit breaker if so.

    Args:
        session_id: The session identifier
        user_message: The user's message to check for acceptance phrases

    Returns:
        True if acceptance phrase was detected and circuit breaker was reset,
        False otherwise.
    """
    if not user_message or not isinstance(user_message, str):
        return False

    if _ACCEPTANCE_PATTERN.search(user_message):
        cb = CircuitBreaker(session_id)
        cb.reset()
        return True

    return False
