"""
Phase Transition Logger for Clean-Room TDD Loop v2.

Logs phase transitions with evidence binding for audit trail.
Each transition generates an evidence hash stored in:
.claude/evidence/tdd95/{contract_id}/

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseTransition:
    """Record of a phase transition event."""

    from_phase: str
    to_phase: str
    impl_path: str
    timestamp: str
    evidence_hash: str
    session_id: str = ""
    terminal_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def compute_evidence_hash(
    impl_path: str,
    test_output: str = "",
    impl_content: str = "",
) -> str:
    """Compute evidence hash for a phase transition.

    Args:
        impl_path: Path to implementation file
        test_output: Test output (failure or success)
        impl_content: Implementation file content

    Returns:
        SHA256 hash of combined evidence
    """
    hasher = hashlib.sha256()

    # Include impl path
    hasher.update(impl_path.encode("utf-8"))

    # Include test output if provided
    if test_output:
        hasher.update(test_output.encode("utf-8"))

    # Include impl content if provided
    if impl_content:
        hasher.update(impl_content.encode("utf-8"))

    return hasher.hexdigest()[:16]  # Short hash for readability


def log_phase_transition(
    from_phase: str | Any,
    to_phase: str | Any,
    impl_path: str,
    session_id: str = "",
    terminal_id: str = "",
    test_output: str = "",
    evidence_dir: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> PhaseTransition:
    """Log a phase transition with evidence binding.

    Args:
        from_phase: Source phase (string or enum)
        to_phase: Target phase (string or enum)
        impl_path: Path to implementation file
        session_id: Session identifier
        terminal_id: Terminal identifier
        test_output: Test output for evidence
        evidence_dir: Directory for evidence storage
        metadata: Additional metadata

    Returns:
        PhaseTransition record
    """
    # Normalize phases
    from_str = from_phase.value if hasattr(from_phase, "value") else str(from_phase)
    to_str = to_phase.value if hasattr(to_phase, "value") else str(to_phase)

    # Compute evidence hash
    impl_content = ""
    impl_file = Path(impl_path)
    if impl_file.exists():
        impl_content = impl_file.read_text(encoding="utf-8")

    evidence_hash = compute_evidence_hash(impl_path, test_output, impl_content)

    # Create transition record
    transition = PhaseTransition(
        from_phase=from_str.lower(),
        to_phase=to_str.lower(),
        impl_path=impl_path,
        timestamp=datetime.now(timezone.utc).isoformat(),
        evidence_hash=evidence_hash,
        session_id=session_id,
        terminal_id=terminal_id,
        metadata=metadata or {},
    )

    # Write evidence file
    if evidence_dir:
        _write_evidence_file(transition, evidence_dir, test_output, impl_content)

    logger.info(f"Phase transition: {from_str} → {to_str} (hash={evidence_hash}, impl={impl_path})")

    return transition


def _write_evidence_file(
    transition: PhaseTransition,
    evidence_dir: Path,
    test_output: str,
    impl_content: str,
) -> None:
    """Write evidence file for a transition.

    Args:
        transition: Phase transition record
        evidence_dir: Base directory for evidence
        test_output: Test output
        impl_content: Implementation content
    """
    # Create contract-specific directory
    contract_id = hashlib.md5(transition.impl_path.encode()).hexdigest()[:8]
    contract_dir = evidence_dir / "tdd95" / contract_id
    contract_dir.mkdir(parents=True, exist_ok=True)

    # Create evidence file
    timestamp_safe = transition.timestamp.replace(":", "-").replace(".", "-")
    evidence_file = contract_dir / f"{transition.to_phase}_{timestamp_safe}.json"

    evidence_data = {
        "transition": {
            "from_phase": transition.from_phase,
            "to_phase": transition.to_phase,
            "impl_path": transition.impl_path,
            "timestamp": transition.timestamp,
            "evidence_hash": transition.evidence_hash,
            "session_id": transition.session_id,
            "terminal_id": transition.terminal_id,
            "metadata": transition.metadata,
        },
        "test_output": test_output[:5000] if test_output else "",  # Truncate
        "impl_hash": hashlib.sha256(impl_content.encode()).hexdigest()[:16] if impl_content else "",
    }

    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, indent=2)


def get_transition_history(
    impl_path: str,
    evidence_dir: Path,
) -> list[PhaseTransition]:
    """Get transition history for an implementation.

    Args:
        impl_path: Path to implementation file
        evidence_dir: Base directory for evidence

    Returns:
        List of PhaseTransition records (newest first)
    """
    contract_id = hashlib.md5(impl_path.encode()).hexdigest()[:8]
    contract_dir = evidence_dir / "tdd95" / contract_id

    if not contract_dir.exists():
        return []

    # Collect all transitions with their timestamps
    transition_data = []
    for evidence_file in contract_dir.glob("*.json"):
        try:
            with open(evidence_file, encoding="utf-8") as f:
                data = json.load(f)

            trans_data = data.get("transition", {})
            timestamp = trans_data.get("timestamp", "")
            transition = PhaseTransition(
                from_phase=trans_data.get("from_phase", ""),
                to_phase=trans_data.get("to_phase", ""),
                impl_path=trans_data.get("impl_path", ""),
                timestamp=timestamp,
                evidence_hash=trans_data.get("evidence_hash", ""),
                session_id=trans_data.get("session_id", ""),
                terminal_id=trans_data.get("terminal_id", ""),
                metadata=trans_data.get("metadata", {}),
            )
            transition_data.append((timestamp, transition))
        except (json.JSONDecodeError, OSError):
            continue

    # Sort by timestamp (newest first)
    transition_data.sort(key=lambda x: x[0], reverse=True)

    return [t for _, t in transition_data]


def validate_transition_sequence(
    transitions: list[PhaseTransition],
) -> tuple[bool, str]:
    """Validate that transitions follow TDD sequence.

    Valid sequences:
    - NONE → RED → GREEN → REFACTOR → COMPLETE
    - RED → GREEN (loop back on failure)
    - GREEN → RED (failure)

    Args:
        transitions: List of transitions (oldest first)

    Returns:
        Tuple of (is_valid, reason)
    """
    if not transitions:
        return True, "No transitions to validate"

    valid_transitions = {
        ("none", "red"),
        ("red", "green"),
        ("green", "refactor"),
        ("green", "red"),  # Failure loop
        ("refactor", "complete"),
        ("red", "red"),  # Re-entry
        ("green", "green"),  # Re-entry
    }

    for i, trans in enumerate(transitions):
        pair = (trans.from_phase, trans.to_phase)
        if pair not in valid_transitions:
            return False, f"Invalid transition at step {i}: {pair}"

    return True, "All transitions valid"
