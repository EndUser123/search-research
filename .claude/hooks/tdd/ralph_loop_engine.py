"""
RalphLoopEngine - State-machine driven autonomous TDD iteration.

Implements TASK-002 from ADR-20260324-clean-room-tdd-loop.md:
- MAX_ITERATIONS=10 guard to prevent infinite loops
- Crash recovery protocol with state persistence
- Director approval checkpoint after each iteration (COMP-001)
- FileLock context manager for all state operations (FM-2401)
- Atomic write pattern for state files (FM-2408)

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .tdd_phase_state import TDDPhaseState

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


# Maximum iterations to prevent infinite loops (TASK-002)
MAX_ITERATIONS = 10

# FileLock timeout (fail-closed per FM-2401)
LOCK_TIMEOUT_SECONDS = 5.0


@dataclass
class ContractState:
    """State for a single TDD contract."""

    impl_path: str
    test_path: str
    spec_path: str
    phase: TDDPhaseState = TDDPhaseState.NONE
    iteration: int = 0
    done: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "impl_path": self.impl_path,
            "test_path": self.test_path,
            "spec_path": self.spec_path,
            "phase": self.phase.value,
            "iteration": self.iteration,
            "done": self.done,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ContractState:
        """Deserialize from dictionary."""
        return cls(
            impl_path=data.get("impl_path", ""),
            test_path=data.get("test_path", ""),
            spec_path=data.get("spec_path", ""),
            phase=TDDPhaseState.from_string(data.get("phase", "none")),
            iteration=data.get("iteration", 0),
            done=data.get("done", False),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class RalphLoopStateData:
    """Complete state data for Ralph Loop engine."""

    session_id: str
    terminal_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    contracts: dict[str, ContractState] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "terminal_id": self.terminal_id,
            "created_at": self.created_at,
            "contracts": {k: v.to_dict() for k, v in self.contracts.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> RalphLoopStateData:
        """Deserialize from dictionary."""
        return cls(
            session_id=data.get("session_id", "unknown"),
            terminal_id=data.get("terminal_id", "unknown"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            contracts={k: ContractState.from_dict(v) for k, v in data.get("contracts", {}).items()},
        )


class RalphLoopEngine:
    """State-machine driven autonomous TDD iteration engine.

    Key features:
    - MAX_ITERATIONS=10 guard prevents infinite loops (TASK-002)
    - Crash recovery from disk state (TASK-002)
    - Director approval checkpoint per iteration (COMP-001)
    - FileLock for all file operations (FM-2401)
    - Atomic write pattern (FM-2408)

    Usage:
        engine = RalphLoopEngine(
            session_id="abc123",
            terminal_id="terminal_456"
        )
        engine.register_contract("impl.py", "test_impl.py", "spec.md")
        engine.set_phase("impl.py", "red")
        result = engine.run_iteration("impl.py", approval="approved")
    """

    # Default state directory
    DEFAULT_STATE_DIR = Path("P:/.claude/state/tdd95")

    def __init__(
        self,
        session_id: str | None = None,
        terminal_id: str | None = None,
        state_dir: Path | None = None,
    ):
        """Initialize the Ralph Loop engine.

        Args:
            session_id: Unique session identifier (defaults to env var or "default")
            terminal_id: Unique terminal identifier (defaults to env var or "default")
            state_dir: Directory for state files (defaults to P:/.claude/state/tdd95)
        """
        self.session_id = session_id or os.environ.get("CLAUDE_SESSION_ID", "default")
        self.terminal_id = terminal_id or os.environ.get("CLAUDE_TERMINAL_ID", "default")
        self.state_dir = state_dir or self.DEFAULT_STATE_DIR

        # In-memory cache (populated on first access or from disk)
        self._cache: RalphLoopStateData | None = None

    @property
    def state_file_path(self) -> Path:
        """Get the state file path with session and terminal isolation (FM-2406)."""
        safe_session = self._sanitize_id(self.session_id)
        safe_terminal = self._sanitize_id(self.terminal_id)
        return self.state_dir / "ralph" / f"{safe_session}_{safe_terminal}.json"

    @property
    def lock_file_path(self) -> Path:
        """Get the lock file path for this state file."""
        return Path(str(self.state_file_path) + ".lock")

    @staticmethod
    def _sanitize_id(id_str: str) -> str:
        """Sanitize ID to prevent path traversal and invalid characters."""
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in id_str)
        return safe[:64]

    def _acquire_lock(self) -> FileLock:
        """Acquire FileLock for state file operations (FM-2401)."""
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        return FileLock(self.lock_file_path, timeout=LOCK_TIMEOUT_SECONDS)

    def _load_state(self) -> RalphLoopStateData:
        """Load state from disk with FileLock protection (crash recovery)."""
        with self._acquire_lock():
            if not self.state_file_path.exists():
                return RalphLoopStateData(
                    session_id=self.session_id,
                    terminal_id=self.terminal_id,
                )

            try:
                with open(self.state_file_path, encoding="utf-8") as f:
                    data = json.load(f)
                return RalphLoopStateData.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Corrupted state file, starting fresh: {e}")
                return RalphLoopStateData(
                    session_id=self.session_id,
                    terminal_id=self.terminal_id,
                )

    def _save_state(self, state: RalphLoopStateData) -> None:
        """Save state to disk with atomic write pattern (FM-2408)."""
        with self._acquire_lock():
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write pattern: write to temp file, then rename
            temp_path = self.state_file_path.with_suffix(".tmp")

            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(state.to_dict(), f, indent=2)

                # Atomic rename
                temp_path.replace(self.state_file_path)

            except Exception:
                if temp_path.exists():
                    temp_path.unlink()
                raise

    def _get_or_load_cache(self) -> RalphLoopStateData:
        """Get cached state or load from disk (crash recovery)."""
        if self._cache is None:
            self._cache = self._load_state()
        return self._cache

    def register_contract(self, impl_path: str, test_path: str, spec_path: str) -> None:
        """Register a new TDD contract.

        Args:
            impl_path: Path to implementation file
            test_path: Path to test file
            spec_path: Path to specification file
        """
        state = self._get_or_load_cache()

        contract = ContractState(
            impl_path=impl_path,
            test_path=test_path,
            spec_path=spec_path,
            phase=TDDPhaseState.NONE,
        )

        state.contracts[impl_path] = contract
        self._save_state(state)
        self._cache = state

    def set_phase(self, impl_path: str, phase: str | TDDPhaseState) -> None:
        """Set the phase for a contract.

        Args:
            impl_path: Path to implementation file
            phase: Phase value (string or TDDPhaseState)
        """
        if isinstance(phase, str):
            new_phase = TDDPhaseState.from_string(phase)
        else:
            new_phase = phase

        state = self._get_or_load_cache()
        contract = state.contracts.get(impl_path)

        if contract:
            contract.phase = new_phase
            contract.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_state(state)
            self._cache = state

    def get_state(self, impl_path: str) -> dict | None:
        """Get the state for a contract.

        Args:
            impl_path: Path to implementation file

        Returns:
            Dictionary with contract state or None if not found
        """
        state = self._get_or_load_cache()
        contract = state.contracts.get(impl_path)

        if contract:
            return {
                "phase": contract.phase.value,
                "iteration": contract.iteration,
                "done": contract.done,
                "impl_path": contract.impl_path,
                "test_path": contract.test_path,
                "spec_path": contract.spec_path,
            }
        return None

    def transition_phase(self, impl_path: str, target_phase: str | TDDPhaseState) -> dict:
        """Transition to a new phase with validation.

        Args:
            impl_path: Path to implementation file
            target_phase: Target phase value (string or TDDPhaseState)

        Returns:
            Dictionary with success status and reason
        """
        if isinstance(target_phase, str):
            new_phase = TDDPhaseState.from_string(target_phase)
        else:
            new_phase = target_phase

        state = self._get_or_load_cache()
        contract = state.contracts.get(impl_path)

        if not contract:
            return {"success": False, "reason": f"Contract not found: {impl_path}"}

        # Validate transition
        if not contract.phase.can_transition_to(new_phase):
            return {
                "success": False,
                "reason": f"Invalid transition: {contract.phase.value} → {new_phase.value}",
            }

        # Increment iteration on GREEN → REFACTOR → GREEN loop
        if new_phase == TDDPhaseState.GREEN and contract.phase == TDDPhaseState.REFACTOR:
            contract.iteration += 1

        # Mark done on COMPLETE
        if new_phase == TDDPhaseState.COMPLETE:
            contract.done = True

        contract.phase = new_phase
        contract.updated_at = datetime.now(timezone.utc).isoformat()

        self._save_state(state)
        self._cache = state

        return {"success": True, "phase": new_phase.value}

    def run_iteration(
        self,
        impl_path: str,
        approval: str | None = None,
    ) -> dict:
        """Run one iteration of the Ralph Loop.

        Args:
            impl_path: Path to implementation file
            approval: Director approval token (COMP-001)

        Returns:
            Dictionary with iteration result:
            - status: "continue" | "complete" | "blocked" | "max_iterations"
            - reason: Human-readable explanation
            - iteration: Current iteration count
        """
        state = self._get_or_load_cache()
        contract = state.contracts.get(impl_path)

        if not contract:
            return {"status": "blocked", "reason": f"Contract not found: {impl_path}"}

        # Check MAX_ITERATIONS guard
        if contract.iteration >= MAX_ITERATIONS:
            return {
                "status": "max_iterations",
                "reason": f"Maximum iterations ({MAX_ITERATIONS}) reached",
                "iteration": contract.iteration,
            }

        # Check director approval checkpoint (COMP-001)
        if approval is None:
            return {
                "status": "blocked",
                "reason": "Director approval required for each iteration",
                "iteration": contract.iteration,
            }

        # Check if already complete
        if contract.done:
            return {
                "status": "complete",
                "reason": "Contract already marked as complete",
                "iteration": contract.iteration,
            }

        # Increment iteration for this run
        contract.iteration += 1
        contract.updated_at = datetime.now(timezone.utc).isoformat()

        self._save_state(state)
        self._cache = state

        return {
            "status": "continue",
            "reason": f"Iteration {contract.iteration} approved",
            "iteration": contract.iteration,
        }
