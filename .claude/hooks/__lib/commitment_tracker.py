"""
Commitment Tracker - Proactive commitment tracking via session boundary hooks.

Detects stated commitments (via TASK_INTENT_PATTERNS) and tracks completion status
(via COMPLETION_SIGNALS) across session boundaries.

Path C: Next-session surfacing - uncompleted commitments appear in next session.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

# File locking for atomic writes
import portalocker  # noqa: E402
from portalocker.exceptions import LockException  # noqa: E402

# ---------------------------------------------------------------------------
# Pattern imports from GTO library
# ---------------------------------------------------------------------------

try:
    import sys

    _GTO_PATH = Path(__file__).resolve().parents[3] / "skills" / "gto"
    if _GTO_PATH.exists():
        sys.path.insert(0, str(_GTO_PATH))
    from lib.session_outcome_detector import (
        COMPLETION_SIGNALS as _COMPLETION_SIGNALS,
    )
    from lib.session_outcome_detector import (
        TASK_INTENT_PATTERNS as _TASK_INTENT_PATTERNS,
    )

    # Re-export for convenience
    TASK_INTENT_PATTERNS = _TASK_INTENT_PATTERNS
    COMPLETION_SIGNALS = _COMPLETION_SIGNALS
except Exception:
    # Fallback patterns if GTO library unavailable
    TASK_INTENT_PATTERNS = [
        (r"I want to\s+([^\.]{10,80})", 0.8),
        (r"I need to\s+([^\.]{10,80})", 0.8),
        (r"I'd like to\s+([^\.]{10,80})", 0.8),
        (r"let's\s+([^\.]{10,80})", 0.7),
        (r"we should\s+([^\.]{10,80})", 0.7),
        (r"we need to\s+([^\.]{10,80})", 0.7),
    ]
    COMPLETION_SIGNALS = [
        r"(?:done|finished|completed|implemented|fixed|added|created)",
        r"(?:let's start|now let's|next let's)",
        r"(?:moving on|on to|turning to)",
    ]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TrackedCommitment:
    """A commitment stated during a session."""

    content: str  # The commitment text
    turn_number: int  # When stated (turn index)
    category: Literal["user_goal", "agent_promise", "deferred_item"]
    completed: bool = False
    completion_turn: int | None = None
    session_id: str = ""  # Which session this was stated in


# ---------------------------------------------------------------------------
# CommitmentTracker
# ---------------------------------------------------------------------------


class CommitmentTracker:
    """Tracks commitments across session boundaries."""

    # Patterns for detecting task intents (from SessionOutcomeDetector)
    TASK_INTENT_PATTERNS = TASK_INTENT_PATTERNS

    # Patterns that indicate completion (from SuspicionDetector)
    COMPLETION_SIGNALS = COMPLETION_SIGNALS

    def __init__(self, claude_home: Path | None = None) -> None:
        """Initialize tracker with Claude home directory."""
        self._home = claude_home or (Path.home() / ".claude")
        self._evidence_dir = self._home / ".evidence"
        self._checkpoint_dir = self._home / ".checkpoints"

    # ------------------------------------------------------------------
    # Path construction
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_terminal_id(terminal_id: str) -> str:
        """Validate and sanitize terminal ID.

        Raises:
            ValueError: If terminal_id contains invalid characters.
        """
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", terminal_id):
            raise ValueError(f"Invalid terminal_id: {terminal_id!r}. Must match ^[a-zA-Z0-9_-]+$")
        return terminal_id

    def _get_state_path(self, terminal_id: str) -> Path:
        """Get path for commitment state file."""
        tid = self._validate_terminal_id(terminal_id)
        return self._evidence_dir / f"gto-commitments-{tid}.json"

    def _get_checkpoint_path(self, terminal_id: str) -> Path:
        """Get path for commitment checkpoint file (PreCompact)."""
        tid = self._validate_terminal_id(terminal_id)
        return self._checkpoints_dir / f"gto-commitments-{tid}.json"

    @property
    def _checkpoints_dir(self) -> Path:
        """Get checkpoints directory, create if needed."""
        d = self._home / ".checkpoints"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def scan_transcript(
        self,
        transcript: list[dict],
        session_id: str = "",
    ) -> list[TrackedCommitment]:
        """Scan transcript for stated commitments.

        Args:
            transcript: List of message dicts with 'role' and 'content' keys.
            session_id: Optional session identifier.

        Returns:
            List of detected TrackedCommitments (not yet checked for completion).
        """
        commitments: list[TrackedCommitment] = []
        completion_re = re.compile("|".join(self.COMPLETION_SIGNALS), re.IGNORECASE)

        for turn_num, msg in enumerate(transcript, start=1):
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Only scan USER messages (per plan spec)
            if role != "user":
                continue

            # Skip if content has completion signals (already done)
            if completion_re.search(content):
                continue

            # Check for task intent patterns
            for pattern, _ in self.TASK_INTENT_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    task_content = match.group(1).strip()
                    if len(task_content) >= 10:
                        commitments.append(
                            TrackedCommitment(
                                content=task_content,
                                turn_number=turn_num,
                                category="user_goal",
                                session_id=session_id,
                            )
                        )
                        break  # One match per message

        return commitments

    def check_completion(
        self,
        commitment: TrackedCommitment,
        transcript: list[dict],
    ) -> TrackedCommitment:
        """Check if a commitment was completed in the transcript.

        Args:
            commitment: The commitment to check.
            transcript: Full transcript to search.

        Returns:
            Updated commitment with completed=True if completion detected.
        """
        completion_re = re.compile("|".join(self.COMPLETION_SIGNALS), re.IGNORECASE)
        normalized = commitment.content.lower()

        for turn_num, msg in enumerate(transcript, start=1):
            content = msg.get("content", "")
            # Skip turns before the commitment was stated
            if turn_num <= commitment.turn_number:
                continue

            # Check if completion signal present
            if completion_re.search(content):
                # Check if commitment content appears near completion signal
                # Simple heuristic: same message or next message mentions the task
                msg_lower = content.lower()
                # Look for task keywords in completion context
                task_words = normalized.split()[:3]  # First 3 words
                if any(word in msg_lower for word in task_words if len(word) > 4):
                    commitment.completed = True
                    commitment.completion_turn = turn_num
                    return commitment

        return commitment

    # ------------------------------------------------------------------
    # State persistence (atomic write with FileLock)
    # ------------------------------------------------------------------

    def save_state(
        self,
        commitments: list[TrackedCommitment],
        terminal_id: str,
    ) -> None:
        """Save commitments to terminal-scoped state file.

        Uses atomic write with FileLock. If lock cannot be acquired in 10 seconds,
        raises RuntimeError (must NOT proceed without lock).

        Args:
            commitments: List of TrackedCommitments to save.
            terminal_id: Terminal identifier for state file naming.

        Raises:
            RuntimeError: If FileLock cannot be acquired within 10 seconds.
        """
        state_path = self._get_state_path(terminal_id)

        # Ensure directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # Lock file for atomic write
        lock_path = state_path.with_suffix(".lock")
        try:
            lock = portalocker.Lock(
                str(lock_path),
                mode="a",
                timeout=10.0,
            )
            lock.acquire()
        except LockException as exc:
            raise RuntimeError(
                f"Could not acquire lock on {lock_path} within 10 seconds: {exc}"
            ) from exc

        try:
            # Atomic write: write to temp, then rename
            data = {
                "version": "1.0",
                "commitments": [asdict(c) for c in commitments],
            }
            tmp_path = state_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp_path.replace(state_path)
        finally:
            lock.release()

    def load_state(self, terminal_id: str) -> list[TrackedCommitment]:
        """Load commitments from terminal-scoped state file.

        Args:
            terminal_id: Terminal identifier.

        Returns:
            List of TrackedCommitments (empty if file missing).
        """
        state_path = self._get_state_path(terminal_id)

        if not state_path.exists():
            return []

        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            commitments = []
            for item in data.get("commitments", []):
                commitments.append(TrackedCommitment(**item))
            return commitments
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    # ------------------------------------------------------------------
    # Checkpoint persistence (for PreCompact/SessionStart flow)
    # ------------------------------------------------------------------

    def save_checkpoint(
        self,
        commitments: list[TrackedCommitment],
        terminal_id: str,
    ) -> None:
        """Save checkpoint before compaction.

        Args:
            commitments: List of TrackedCommitments to checkpoint.
            terminal_id: Terminal identifier.

        Raises:
            RuntimeError: If FileLock cannot be acquired within 10 seconds.
        """
        checkpoint_path = self._get_checkpoint_path(terminal_id)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        lock_path = checkpoint_path.with_suffix(".lock")
        try:
            lock = portalocker.Lock(
                str(lock_path),
                mode="a",
                timeout=10.0,
            )
            lock.acquire()
        except LockException as exc:
            raise RuntimeError(
                f"Could not acquire lock on {lock_path} within 10 seconds: {exc}"
            ) from exc

        try:
            data = {
                "version": "1.0",
                "saved_at": str(Path(__file__).stat().st_mtime if Path(__file__).exists() else ""),
                "commitments": [asdict(c) for c in commitments],
            }
            tmp_path = checkpoint_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp_path.replace(checkpoint_path)
        finally:
            lock.release()

    def load_checkpoint(self, terminal_id: str) -> list[TrackedCommitment]:
        """Load commitments from checkpoint file.

        Args:
            terminal_id: Terminal identifier.

        Returns:
            List of TrackedCommitments from checkpoint (empty if missing).
        """
        checkpoint_path = self._get_checkpoint_path(terminal_id)

        if not checkpoint_path.exists():
            return []

        try:
            data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            commitments = []
            for item in data.get("commitments", []):
                commitments.append(TrackedCommitment(**item))
            return commitments
        except (json.JSONDecodeError, TypeError, KeyError):
            return []
