#!/usr/bin/env python3
"""
State manager for /verify skill multi-terminal safety.

Provides per-terminal state isolation and session validation to ensure
concurrent verification operations don't share or corrupt state.

Includes circuit breaker pattern for false positive cascade protection.
"""

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Circuit breaker configuration
VERIFY_CIRCUIT_BREAKER_THRESHOLD = int(os.environ.get("VERIFY_CIRCUIT_BREAKER_THRESHOLD", "3"))
VERIFY_CIRCUIT_BREAKER_COOLDOWN = int(
    os.environ.get("VERIFY_CIRCUIT_BREAKER_COOLDOWN", "3600")
)  # 1 hour


class VerifyStateManager:
    """
    Manage verification state with per-terminal isolation.

    State isolation strategy:
    - Each terminal gets its own state directory: .claude/state/verify_{terminal_id}/
    - Session validation prevents cross-terminal interference
    - Verification artifacts stored per-terminal
    - Circuit breaker for false positive cascade protection
    """

    def __init__(self, terminal_id: str | None = None, session_id: str | None = None):
        """
        Initialize state manager for a terminal.

        Args:
            terminal_id: Terminal identifier (auto-generated if None)
            session_id: Session identifier for validation
        """
        # Resolve terminal_id
        if not terminal_id:
            terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", f"term_{uuid.uuid4().hex[:8]}")

        self.terminal_id = terminal_id

        # Resolve session_id
        if not session_id:
            session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown-session")

        self.session_id = session_id

        # Create state directory for this terminal
        self.state_dir = Path(f".claude/state/verify_{self.terminal_id}")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # State file paths
        self.session_file = self.state_dir / "session.json"
        self.verifications_file = self.state_dir / "verifications.json"
        self.circuit_breaker_file = self.state_dir / "circuit_breaker.json"

        # Initialize session state
        self._ensure_session_state()

    def _ensure_session_state(self):
        """Create or validate session state file."""
        if not self.session_file.exists():
            # Create new session state
            self._write_session_state(
                {
                    "version": "1.0",
                    "terminal_id": self.terminal_id,
                    "session_id": self.session_id,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "verifications_count": 0,
                }
            )
        else:
            # Validate existing session matches
            existing_state = self._read_session_state()
            if existing_state.get("session_id") != self.session_id:
                # Session mismatch - this is a new session, reset state
                self._reset_session()

    def _read_session_state(self) -> dict[str, Any]:
        """Read session state from disk."""
        if not self.session_file.exists():
            return {}
        return json.loads(self.session_file.read_text())

    def _write_session_state(self, state: dict[str, Any]):
        """Write session state to disk."""
        state["last_updated"] = datetime.now().isoformat()
        self.session_file.write_text(json.dumps(state, indent=2))

    def _reset_session(self):
        """Reset state for new session."""
        # Archive old session state
        if self.session_file.exists():
            old_state = json.loads(self.session_file.read_text())
            archive_file = (
                self.state_dir / f"session_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            archive_file.write_text(json.dumps(old_state, indent=2))

        # Create new session state
        self._write_session_state(
            {
                "version": "1.0",
                "terminal_id": self.terminal_id,
                "session_id": self.session_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "verifications_count": 0,
            }
        )

    def validate_session(self, expected_session_id: str | None = None) -> bool:
        """
        Validate that current session matches expected session.

        Args:
            expected_session_id: Session ID to validate against (defaults to self.session_id)

        Returns:
            True if session is valid, False otherwise
        """
        session_to_check = expected_session_id or self.session_id
        existing_state = self._read_session_state()

        if not existing_state:
            # No existing state - valid
            return True

        return existing_state.get("session_id") == session_to_check

    def get_verification_state(self, verification_id: str) -> dict[str, Any] | None:
        """
        Get state for a specific verification.

        Args:
            verification_id: Verification UUID

        Returns:
            Verification state dict or None if not found
        """
        if not self.verifications_file.exists():
            return None

        verifications = json.loads(self.verifications_file.read_text())
        return verifications.get(verification_id)

    def save_verification_state(self, verification_id: str, state: dict[str, Any]):
        """
        Save state for a verification.

        Args:
            verification_id: Verification UUID
            state: Verification state dict to save
        """
        # Load existing verifications
        if self.verifications_file.exists():
            verifications = json.loads(self.verifications_file.read_text())
        else:
            verifications = {}

        # Update with new state
        state["saved_at"] = datetime.now().isoformat()
        verifications[verification_id] = state

        # Write back
        self.verifications_file.write_text(json.dumps(verifications, indent=2))

        # Update session counter
        session_state = self._read_session_state()
        session_state["verifications_count"] = len(verifications)
        session_state["last_updated"] = datetime.now().isoformat()
        self._write_session_state(session_state)

    def get_state_dir(self) -> Path:
        """Get the state directory path for this terminal."""
        return self.state_dir

    def get_evidence_ledger_path(self) -> Path:
        """
        Get the evidence ledger path for this terminal.

        Returns:
            Path to evidence ledger file for this terminal
        """
        return self.state_dir / "evidence_ledger.json"

    def cleanup_old_states(self, keep_count: int = 10):
        """
        Clean up old verification states, keeping only the most recent.

        Args:
            keep_count: Number of recent verifications to keep
        """
        if not self.verifications_file.exists():
            return

        verifications = json.loads(self.verifications_file.read_text())

        # Sort by saved_at timestamp and keep only the most recent
        sorted_verifications = sorted(
            verifications.items(), key=lambda x: x[1].get("saved_at", ""), reverse=True
        )

        kept_verifications = dict(sorted_verifications[:keep_count])

        # Write back
        self.verifications_file.write_text(json.dumps(kept_verifications, indent=2))

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about this terminal's state."""
        session_state = self._read_session_state()

        stats = {
            "terminal_id": self.terminal_id,
            "session_id": self.session_id,
            "state_dir": str(self.state_dir),
            "verifications_count": session_state.get("verifications_count", 0),
            "session_created_at": session_state.get("created_at"),
            "session_last_updated": session_state.get("last_updated"),
        }

        # Add circuit breaker status
        circuit_breaker = self._read_circuit_breaker_state()
        stats["circuit_breaker"] = {
            "active_gates": list(circuit_breaker.get("gates", {}).keys()),
            "threshold": VERIFY_CIRCUIT_BREAKER_THRESHOLD,
            "cooldown_seconds": VERIFY_CIRCUIT_BREAKER_COOLDOWN,
        }

        return stats

    # ========== Circuit Breaker Pattern ==========

    def _read_circuit_breaker_state(self) -> dict[str, Any]:
        """Read circuit breaker state from disk."""
        if not self.circuit_breaker_file.exists():
            return {"version": "1.0", "gates": {}}
        try:
            return json.loads(self.circuit_breaker_file.read_text())
        except (json.JSONDecodeError, OSError):
            return {"version": "1.0", "gates": {}}

    def _write_circuit_breaker_state(self, state: dict[str, Any]):
        """Write circuit breaker state to disk."""
        state["last_updated"] = datetime.now().isoformat()
        self.circuit_breaker_file.write_text(json.dumps(state, indent=2))

    def record_false_positive(
        self, gate_name: str, details: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Record a false positive for a gate and check if circuit breaker should trip.

        Args:
            gate_name: Name of the gate that had a false positive
            details: Optional details about the false positive

        Returns:
            Dict with circuit breaker status:
            - "tripped": True if circuit breaker just tripped
            - "consecutive_count": Current consecutive false positive count
            - "message": User-facing message if tripped
        """
        state = self._read_circuit_breaker_state()
        gates = state.get("gates", {})

        # Get or initialize gate state
        gate_state = gates.get(
            gate_name,
            {
                "consecutive_false_positives": 0,
                "total_false_positives": 0,
                "tripped_at": None,
                "suppressed_until": None,
            },
        )

        # Increment counters
        gate_state["consecutive_false_positives"] += 1
        gate_state["total_false_positives"] += 1
        gate_state["last_false_positive_at"] = datetime.now().isoformat()
        if details:
            gate_state["last_details"] = details

        result = {
            "tripped": False,
            "consecutive_count": gate_state["consecutive_false_positives"],
            "message": None,
        }

        # Check if threshold reached
        if gate_state["consecutive_false_positives"] >= VERIFY_CIRCUIT_BREAKER_THRESHOLD:
            gate_state["tripped_at"] = datetime.now().isoformat()
            gate_state["suppressed_until"] = time.time() + VERIFY_CIRCUIT_BREAKER_COOLDOWN
            result["tripped"] = True
            result["message"] = (
                f"⚠️ CIRCUIT BREAKER TRIPPED: {gate_name}\n"
                f"After {gate_state['consecutive_false_positives']} consecutive false positives, "
                f"this gate is temporarily disabled.\n"
                f"It will re-enable after {VERIFY_CIRCUIT_BREAKER_COOLDOWN // 60} minutes.\n"
                f"This alert is shown once."
            )

        # Save state
        gates[gate_name] = gate_state
        state["gates"] = gates
        self._write_circuit_breaker_state(state)

        return result

    def reset_false_positive_count(self, gate_name: str):
        """
        Reset consecutive false positive count for a gate (after a true positive).

        Args:
            gate_name: Name of the gate to reset
        """
        state = self._read_circuit_breaker_state()
        gates = state.get("gates", {})

        if gate_name in gates:
            gates[gate_name]["consecutive_false_positives"] = 0
            gates[gate_name]["reset_at"] = datetime.now().isoformat()
            state["gates"] = gates
            self._write_circuit_breaker_state(state)

    def is_gate_suppressed(self, gate_name: str) -> tuple[bool, str | None]:
        """
        Check if a gate is currently suppressed by circuit breaker.

        Args:
            gate_name: Name of the gate to check

        Returns:
            Tuple of (is_suppressed, message):
            - is_suppressed: True if gate should be bypassed
            - message: None or re-enable message if cooldown expired
        """
        state = self._read_circuit_breaker_state()
        gates = state.get("gates", {})

        if gate_name not in gates:
            return False, None

        gate_state = gates[gate_name]
        suppressed_until = gate_state.get("suppressed_until")

        if suppressed_until is None:
            return False, None

        current_time = time.time()

        if current_time < suppressed_until:
            # Still suppressed
            remaining = int(suppressed_until - current_time)
            return (
                True,
                f"Gate {gate_name} suppressed for {remaining // 60} more minutes (circuit breaker)",
            )

        # Cooldown expired - re-enable gate
        gate_state["suppressed_until"] = None
        gate_state["re_enabled_at"] = datetime.now().isoformat()
        gate_state["consecutive_false_positives"] = 0  # Reset on re-enable
        gates[gate_name] = gate_state
        state["gates"] = gates
        self._write_circuit_breaker_state(state)

        return False, f"✅ Gate {gate_name} re-enabled after cooldown period"
