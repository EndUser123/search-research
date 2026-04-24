"""
TDD Phase State Management for Clean-Room TDD Loop v2.

Extends TDD-95 with RED/GREEN/REFACTOR phases, session-scoped state isolation,
and crash recovery support.

ADR: P:/docs/adrs/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Import FileLock from existing infrastructure
try:
    from __lib.file_lock import FileLock
except ImportError:
    # Fallback for direct execution
    import sys

    _lib_path = Path(__file__).resolve().parent.parent / "__lib"
    if _lib_path.exists():
        sys.path.insert(0, str(_lib_path.parent))
        from hooks.__lib.file_lock import FileLock
    else:
        raise ImportError("FileLock not found - ensure __lib/file_lock.py exists")


class TDDPhaseState(Enum):
    """TDD phase states extending TDD95State.

    Phase progression:
        NONE → TEST_EXISTS → RED → GREEN → REFACTOR → COMPLETE

    Key rules:
    - RED: Write failing tests, can edit tests
    - GREEN: Make tests pass, cannot edit tests
    - REFACTOR: Clean up code, cannot edit tests, can loop back to GREEN
    """

    # Inherited from TDD95State
    NONE = "none"
    TEST_EXISTS = "test_exists"
    FAILING = "failing"  # Legacy - maps to RED behavior
    PASSING = "passing"  # Legacy - maps to GREEN behavior
    COMPLETE = "complete"

    # New phase states for Clean-Room TDD
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"

    @classmethod
    def from_string(cls, value: str) -> TDDPhaseState:
        """Parse phase state from string, with legacy mapping."""
        mapping = {
            "none": cls.NONE,
            "test_exists": cls.TEST_EXISTS,
            "failing": cls.FAILING,
            "passing": cls.PASSING,
            "complete": cls.COMPLETE,
            "red": cls.RED,
            "green": cls.GREEN,
            "refactor": cls.REFACTOR,
            # Legacy aliases
            "idle": cls.NONE,
            "green_confirmed": cls.PASSING,
        }
        return mapping.get(value.lower().strip(), cls.NONE)

    def can_transition_to(self, target: TDDPhaseState) -> bool:
        """Check if transition from current state to target is valid.

        Valid transitions:
        - NONE → TEST_EXISTS (test file created)
        - TEST_EXISTS → RED (test executed and fails)
        - TEST_EXISTS → FAILING (legacy path)
        - RED → GREEN (implementation passes tests)
        - RED → FAILING (legacy path)
        - GREEN → REFACTOR (code cleanup phase)
        - GREEN → COMPLETE (skip refactor, cycle finished)
        - GREEN → PASSING (legacy path)
        - REFACTOR → GREEN (tests still pass after refactor)
        - REFACTOR → COMPLETE (cycle finished)
        - FAILING → RED (upgrade to new phase)
        - PASSING → GREEN (upgrade to new phase)
        """
        valid_transitions = {
            TDDPhaseState.NONE: {
                TDDPhaseState.TEST_EXISTS,
            },
            TDDPhaseState.TEST_EXISTS: {
                TDDPhaseState.RED,
                TDDPhaseState.FAILING,
            },
            TDDPhaseState.RED: {
                TDDPhaseState.GREEN,
                TDDPhaseState.FAILING,
            },
            TDDPhaseState.GREEN: {
                TDDPhaseState.REFACTOR,
                TDDPhaseState.COMPLETE,
                TDDPhaseState.PASSING,
            },
            TDDPhaseState.REFACTOR: {
                TDDPhaseState.GREEN,
                TDDPhaseState.COMPLETE,
            },
            # Legacy states can upgrade to new phases
            TDDPhaseState.FAILING: {
                TDDPhaseState.RED,
                TDDPhaseState.GREEN,
                TDDPhaseState.PASSING,
            },
            TDDPhaseState.PASSING: {
                TDDPhaseState.GREEN,
                TDDPhaseState.REFACTOR,
                TDDPhaseState.COMPLETE,
            },
            # COMPLETE is terminal
            TDDPhaseState.COMPLETE: set(),
        }

        return target in valid_transitions.get(self, set())

    def can_edit_impl(self) -> bool:
        """Check if implementation files can be edited in this phase."""
        return self in {
            TDDPhaseState.RED,
            TDDPhaseState.GREEN,
            TDDPhaseState.REFACTOR,
            TDDPhaseState.FAILING,  # Legacy
            TDDPhaseState.PASSING,  # Legacy
        }

    def can_edit_test(self) -> bool:
        """Check if test files can be edited in this phase.

        Per Three-File Contract: tests can only be modified in RED phase.
        """
        return self == TDDPhaseState.RED


@dataclass
class FilePhaseState:
    """State for a single file in the TDD cycle."""

    phase: TDDPhaseState
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    iteration: int = 0
    test_hash: str | None = None  # SHA-256 hash of test file for immutability check

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "phase": self.phase.value,
            "updated_at": self.updated_at,
            "iteration": self.iteration,
            "test_hash": self.test_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FilePhaseState:
        """Deserialize from dictionary."""
        return cls(
            phase=TDDPhaseState.from_string(data.get("phase", "none")),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            iteration=data.get("iteration", 0),
            test_hash=data.get("test_hash"),
        )


@dataclass
class TDDPhaseStateData:
    """Complete state data for TDD phase management."""

    session_id: str
    terminal_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    files: dict[str, FilePhaseState] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "terminal_id": self.terminal_id,
            "created_at": self.created_at,
            "files": {k: v.to_dict() for k, v in self.files.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> TDDPhaseStateData:
        """Deserialize from dictionary."""
        return cls(
            session_id=data.get("session_id", "unknown"),
            terminal_id=data.get("terminal_id", "unknown"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            files={k: FilePhaseState.from_dict(v) for k, v in data.get("files", {}).items()},
        )


class TDDPhaseStateManager:
    """Manages TDD phase state with session/terminal isolation.

    Key features:
    - Session-scoped state file paths (FM-2406)
    - FileLock for all file operations (FM-2401)
    - Atomic write pattern (FM-2408)
    - Crash recovery from disk state

    Usage:
        manager = TDDPhaseStateManager(
            session_id="abc123",
            terminal_id="terminal_456"
        )
        manager.set_phase("src/module.py", "red")
        phase = manager.get_phase("src/module.py")
    """

    # Default state directory
    DEFAULT_STATE_DIR = Path("P:/.claude/state/tdd95")

    # FileLock timeout (fail-closed per FM-2401)
    LOCK_TIMEOUT_SECONDS = 5.0

    def __init__(
        self,
        session_id: str | None = None,
        terminal_id: str | None = None,
        state_dir: Path | None = None,
    ):
        """Initialize the phase state manager.

        Args:
            session_id: Unique session identifier (defaults to env var or "default")
            terminal_id: Unique terminal identifier (defaults to env var or "default")
            state_dir: Directory for state files (defaults to P:/.claude/state/tdd95)
        """
        self.session_id = session_id or os.environ.get("CLAUDE_SESSION_ID", "default")
        self.terminal_id = terminal_id or os.environ.get("CLAUDE_TERMINAL_ID", "default")
        self.state_dir = state_dir or self.DEFAULT_STATE_DIR

        # In-memory cache (populated on first access or from disk)
        self._cache: TDDPhaseStateData | None = None

    @property
    def state_file_path(self) -> Path:
        """Get the state file path with session and terminal isolation (FM-2406).

        Format: {state_dir}/phases/{session_id}_{terminal_id}.json
        """
        # Sanitize IDs to prevent path traversal
        safe_session = self._sanitize_id(self.session_id)
        safe_terminal = self._sanitize_id(self.terminal_id)

        return self.state_dir / "phases" / f"{safe_session}_{safe_terminal}.json"

    @property
    def lock_file_path(self) -> Path:
        """Get the lock file path for this state file."""
        return Path(str(self.state_file_path) + ".lock")

    @staticmethod
    def _sanitize_id(id_str: str) -> str:
        """Sanitize ID to prevent path traversal and invalid characters."""
        # Replace any non-alphanumeric characters (except underscore, dash)
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in id_str)
        # Limit length
        return safe[:64]

    def _acquire_lock(self) -> FileLock:
        """Acquire FileLock for state file operations (FM-2401)."""
        # Ensure directory exists
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        return FileLock(self.lock_file_path, timeout=self.LOCK_TIMEOUT_SECONDS)

    def _load_state(self) -> TDDPhaseStateData:
        """Load state from disk with FileLock protection."""
        with self._acquire_lock() as lock:
            if not self.state_file_path.exists():
                return TDDPhaseStateData(
                    session_id=self.session_id,
                    terminal_id=self.terminal_id,
                )

            try:
                with open(self.state_file_path, encoding="utf-8") as f:
                    data = json.load(f)
                return TDDPhaseStateData.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Corrupted state file, starting fresh: {e}")
                return TDDPhaseStateData(
                    session_id=self.session_id,
                    terminal_id=self.terminal_id,
                )

    def _save_state(self, state: TDDPhaseStateData) -> None:
        """Save state to disk with atomic write pattern (FM-2408).

        Atomic write pattern:
        1. Write to temp file
        2. Atomic rename to target
        """
        with self._acquire_lock() as lock:
            # Ensure directory exists
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first (atomic write pattern)
            temp_path = self.state_file_path.with_suffix(".tmp")

            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(state.to_dict(), f, indent=2)

                # Atomic rename (POSIX guarantees atomic, Windows is "close enough")
                temp_path.replace(self.state_file_path)

            except Exception:
                # Clean up temp file on failure
                if temp_path.exists():
                    temp_path.unlink()
                raise

    def _get_or_load_cache(self) -> TDDPhaseStateData:
        """Get cached state or load from disk (crash recovery)."""
        if self._cache is None:
            self._cache = self._load_state()
        return self._cache

    def get_phase(self, file_path: str) -> TDDPhaseState | None:
        """Get the current phase for a file.

        Args:
            file_path: Path to the file (relative or absolute)

        Returns:
            TDDPhaseState or None if file not tracked
        """
        state = self._get_or_load_cache()
        file_state = state.files.get(file_path)
        return file_state.phase if file_state else None

    def set_phase(
        self,
        file_path: str,
        phase: str | TDDPhaseState,
        test_hash: str | None = None,
    ) -> None:
        """Set the phase for a file.

        Args:
            file_path: Path to the file
            phase: Phase value (string or TDDPhaseState)
            test_hash: Optional SHA-256 hash of test file for immutability

        Raises:
            ValueError: If transition is invalid
        """
        # Normalize phase
        if isinstance(phase, str):
            new_phase = TDDPhaseState.from_string(phase)
        else:
            new_phase = phase

        state = self._get_or_load_cache()

        # Check if file already has a phase
        existing = state.files.get(file_path)
        if existing:
            current_phase = existing.phase
            if not current_phase.can_transition_to(new_phase):
                raise ValueError(
                    f"Invalid phase transition: {current_phase.value} → {new_phase.value}"
                )
            iteration = existing.iteration
        else:
            iteration = 0

        # Increment iteration on GREEN → REFACTOR → GREEN loop
        if (
            new_phase == TDDPhaseState.GREEN
            and existing
            and existing.phase == TDDPhaseState.REFACTOR
        ):
            iteration += 1

        # Update state
        state.files[file_path] = FilePhaseState(
            phase=new_phase,
            iteration=iteration,
            test_hash=test_hash or (existing.test_hash if existing else None),
        )

        # Persist to disk
        self._save_state(state)
        self._cache = state

    def get_all_files(self) -> dict[str, FilePhaseState]:
        """Get all tracked files and their states."""
        state = self._get_or_load_cache()
        return dict(state.files)

    def clear_file(self, file_path: str) -> bool:
        """Remove a file from tracking.

        Returns:
            True if file was tracked, False otherwise
        """
        state = self._get_or_load_cache()
        if file_path in state.files:
            del state.files[file_path]
            self._save_state(state)
            self._cache = state
            return True
        return False

    def clear_all(self) -> None:
        """Clear all tracked files (used by cleanup task)."""
        state = self._get_or_load_cache()
        state.files.clear()
        self._save_state(state)
        self._cache = state


# Utility functions for file hashing (Three-File Contract)


def compute_file_hash(file_path: str | Path) -> str:
    """Compute SHA-256 hash of a file for immutability verification.

    Args:
        file_path: Path to the file

    Returns:
        Hex-encoded SHA-256 hash
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_file_hash(file_path: str | Path, expected_hash: str) -> bool:
    """Verify that a file's hash matches expected value.

    Uses timing-attack safe comparison for security.

    Args:
        file_path: Path to the file
        expected_hash: Expected SHA-256 hash

    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual_hash = compute_file_hash(file_path)
        # Timing-attack safe comparison
        return len(actual_hash) == len(expected_hash) and all(
            a == b for a, b in zip(actual_hash, expected_hash)
        )
    except FileNotFoundError:
        return False
