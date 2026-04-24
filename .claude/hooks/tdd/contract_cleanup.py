"""
Contract Cleanup for Clean-Room TDD Loop v2.

Cleans up evidence directories for completed TDD contracts.
Evidence is retained for a configurable period before cleanup.

ADR: P:/docs/adrs/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default retention period in days
DEFAULT_RETENTION_DAYS = 7


@dataclass(frozen=True)
class CleanupResult:
    """Result of a contract cleanup operation."""

    contract_id: str
    impl_path: str
    evidence_files_removed: int
    freed_bytes: int
    completed_at: str | None = None


def get_completed_contracts(
    evidence_dir: Path,
    state_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Find contracts that have reached COMPLETE phase.

    Args:
        evidence_dir: Base directory for evidence storage
        state_dir: Optional state directory for phase tracking

    Returns:
        List of dicts with contract_id, impl_path, completion_time
    """
    tdd95_dir = evidence_dir / "tdd95"
    if not tdd95_dir.exists():
        return []

    completed_contracts = []

    for contract_dir in tdd95_dir.iterdir():
        if not contract_dir.is_dir():
            continue

        # Check for COMPLETE phase evidence
        complete_files = list(contract_dir.glob("complete_*.json"))
        if not complete_files:
            continue

        # Get the most recent completion time
        latest_completion = None
        impl_path = None

        for evidence_file in complete_files:
            try:
                with open(evidence_file, encoding="utf-8") as f:
                    data = json.load(f)

                trans_data = data.get("transition", {})
                timestamp = trans_data.get("timestamp", "")
                if impl_path is None:
                    impl_path = trans_data.get("impl_path", "")

                if timestamp and (latest_completion is None or timestamp > latest_completion):
                    latest_completion = timestamp
            except (json.JSONDecodeError, OSError):
                continue

        if latest_completion and impl_path:
            completed_contracts.append(
                {
                    "contract_id": contract_dir.name,
                    "impl_path": impl_path,
                    "completion_time": latest_completion,
                    "evidence_dir": contract_dir,
                }
            )

    return completed_contracts


def cleanup_completed_contract(
    contract_id: str,
    evidence_dir: Path,
    retention_days: int = DEFAULT_RETENTION_DAYS,
) -> CleanupResult | None:
    """Clean up evidence for a completed contract.

    Args:
        contract_id: Contract identifier (MD5 hash prefix)
        evidence_dir: Base directory for evidence storage
        retention_days: Number of days to retain evidence after completion

    Returns:
        CleanupResult if cleanup performed, None if not eligible
    """
    contract_dir = evidence_dir / "tdd95" / contract_id
    if not contract_dir.exists():
        return None

    # Find completion time
    complete_files = list(contract_dir.glob("complete_*.json"))
    if not complete_files:
        return None

    # Get latest completion time
    latest_completion = None
    impl_path = ""

    for evidence_file in complete_files:
        try:
            with open(evidence_file, encoding="utf-8") as f:
                data = json.load(f)

            trans_data = data.get("transition", {})
            timestamp = trans_data.get("timestamp", "")
            if impl_path == "":
                impl_path = trans_data.get("impl_path", "")

            if timestamp and (latest_completion is None or timestamp > latest_completion):
                latest_completion = timestamp
        except (json.JSONDecodeError, OSError):
            continue

    if not latest_completion:
        return None

    # Check retention period
    try:
        completion_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        retention_cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        if completion_dt > retention_cutoff:
            # Still within retention period
            return None
    except (ValueError, TypeError):
        return None

    # Calculate size before cleanup
    evidence_files = list(contract_dir.glob("*.json"))
    freed_bytes = sum(f.stat().st_size for f in evidence_files if f.exists())

    # Remove contract directory
    try:
        shutil.rmtree(contract_dir)
        logger.info(f"Cleaned up contract {contract_id} (freed {freed_bytes} bytes)")
    except OSError as e:
        logger.error(f"Failed to cleanup contract {contract_id}: {e}")
        return None

    return CleanupResult(
        contract_id=contract_id,
        impl_path=impl_path,
        evidence_files_removed=len(evidence_files),
        freed_bytes=freed_bytes,
        completed_at=latest_completion,
    )


def cleanup_all_completed_contracts(
    evidence_dir: Path,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    dry_run: bool = False,
) -> list[CleanupResult]:
    """Clean up all completed contracts past retention period.

    Args:
        evidence_dir: Base directory for evidence storage
        retention_days: Number of days to retain evidence after completion
        dry_run: If True, report what would be cleaned without deleting

    Returns:
        List of CleanupResult for contracts cleaned up
    """
    completed = get_completed_contracts(evidence_dir)
    results = []

    for contract_info in completed:
        contract_id = contract_info["contract_id"]
        contract_dir = contract_info["evidence_dir"]

        # Check retention period
        try:
            completion_dt = datetime.fromisoformat(
                contract_info["completion_time"].replace("Z", "+00:00")
            )
            retention_cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

            if completion_dt > retention_cutoff:
                # Still within retention period
                continue
        except (ValueError, TypeError):
            continue

        if dry_run:
            # Report without deleting
            evidence_files = list(contract_dir.glob("*.json"))
            freed_bytes = sum(f.stat().st_size for f in evidence_files if f.exists())

            results.append(
                CleanupResult(
                    contract_id=contract_id,
                    impl_path=contract_info["impl_path"],
                    evidence_files_removed=len(evidence_files),
                    freed_bytes=freed_bytes,
                    completed_at=contract_info["completion_time"],
                )
            )
        else:
            result = cleanup_completed_contract(contract_id, evidence_dir, retention_days)
            if result:
                results.append(result)

    return results


def get_cleanup_stats(evidence_dir: Path) -> dict[str, Any]:
    """Get statistics about contracts eligible for cleanup.

    Args:
        evidence_dir: Base directory for evidence storage

    Returns:
        Dict with total_contracts, completed_contracts, eligible_for_cleanup,
        total_bytes_reclaimable
    """
    tdd95_dir = evidence_dir / "tdd95"
    if not tdd95_dir.exists():
        return {
            "total_contracts": 0,
            "completed_contracts": 0,
            "eligible_for_cleanup": 0,
            "total_bytes_reclaimable": 0,
        }

    total_contracts = 0
    completed_contracts = 0
    eligible_for_cleanup = 0
    total_bytes = 0

    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=DEFAULT_RETENTION_DAYS)

    for contract_dir in tdd95_dir.iterdir():
        if not contract_dir.is_dir():
            continue

        total_contracts += 1

        # Check for COMPLETE phase
        complete_files = list(contract_dir.glob("complete_*.json"))
        if not complete_files:
            continue

        completed_contracts += 1

        # Check if past retention
        for evidence_file in complete_files:
            try:
                with open(evidence_file, encoding="utf-8") as f:
                    data = json.load(f)

                timestamp = data.get("transition", {}).get("timestamp", "")
                if timestamp:
                    completion_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if completion_dt <= retention_cutoff:
                        eligible_for_cleanup += 1
                        evidence_files = list(contract_dir.glob("*.json"))
                        total_bytes += sum(f.stat().st_size for f in evidence_files if f.exists())
                        break
            except (json.JSONDecodeError, OSError, ValueError, TypeError):
                continue

    return {
        "total_contracts": total_contracts,
        "completed_contracts": completed_contracts,
        "eligible_for_cleanup": eligible_for_cleanup,
        "total_bytes_reclaimable": total_bytes,
    }
