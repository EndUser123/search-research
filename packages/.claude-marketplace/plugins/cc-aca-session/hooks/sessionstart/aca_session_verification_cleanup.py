#!/usr/bin/env python3
"""SessionStart_verification_cleanup.py - Automatic verification state cleanup

Removes old session-scoped state files on terminal session start.
Prevents accumulation of stale state data across sessions.

Lifecycle: SessionStart (cleanup on session initialization)

Configuration:
  VERIFICATION_STATE_MAX_AGE_HOURS=24  (default: 24 hours)
  VERIFICATION_CLEANUP_ENABLED=true   (default: true)
  PLAN_FILE_MAX_AGE_DAYS=30           (default: 30 days for plan files)

State Management:
  Uses session_id for session isolation
    State directories:
    - dependency_verification_{terminal_id}.json
    - file_existence_decision_{session_id}.json
    - observe_before_act/observe_gate_console_{console}_{session}.json
    - anti_sycophancy_injector/{session}_{terminal/env}_{id}.json

Plan File Cleanup:
  Removes stale plan files from ~/.claude/plans/ that exceed the age threshold.
  Plan mode guard (PreToolUse_plan_mode_guard.py) blocks Edit/Write when ANY
  plan file exists, so stale plans can cause unexpected blocking.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

# Plugin lib for shared state paths (works from source or cache)
_PLUGIN_LIB = Path(__file__).resolve().parent.parent.parent / "lib"
if str(_PLUGIN_LIB) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_LIB))

from state_paths import get_state_dir, get_evidence_dir, get_plan_dir, get_hooks_dir

# Resolve paths via state_paths (not hardcoded)
HOOK_DIR = get_hooks_dir()
STATE_DIR = get_state_dir()
PLAN_DIR = get_plan_dir()
EVIDENCE_DIR = get_evidence_dir()

# Legacy compat: hooks that import from global __lib/
sys.path.insert(0, str(HOOK_DIR))

SKILLS_CODE_UTILS = HOOK_DIR.parent / "skills" / "code" / "utils"
if SKILLS_CODE_UTILS.exists():
    sys.path.insert(0, str(SKILLS_CODE_UTILS))


# Logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Configuration
ENABLED = os.environ.get("VERIFICATION_CLEANUP_ENABLED", "true").lower() == "true"
MAX_AGE_HOURS = int(os.environ.get("VERIFICATION_STATE_MAX_AGE_HOURS", "24"))
PLAN_MAX_AGE_DAYS = int(
    os.environ.get("PLAN_FILE_MAX_AGE_DAYS", "30")
)  # Increased from 7 to 30 days (2026-03-19)
TDD_CONTRACT_RETENTION_DAYS = int(
    os.environ.get("TDD_CONTRACT_RETENTION_DAYS", "7")
)  # TDD evidence cleanup (ADR-20260324)

# STATE_DIR, PLAN_DIR, EVIDENCE_DIR resolved above via state_paths


def cleanup_old_file_existence_decisions(max_age_hours: int = 24) -> int:
    """Remove old file_existence_decision state files.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        Number of files removed
    """
    if not STATE_DIR.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in STATE_DIR.glob("file_existence_decision_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed old file_existence_decision state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_verification_states(max_age_hours: int = 1) -> int:
    """Remove old verification state files.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        Number of files removed
    """
    if not STATE_DIR.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in STATE_DIR.glob("dependency_verification_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed old verification state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_observe_before_act(max_age_hours: int = 24) -> int:
    """Remove old observe_before_act state files.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        Number of files removed
    """
    state_dir = STATE_DIR / "observe_before_act"
    if not state_dir.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in state_dir.glob("*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed old observe_before_act state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_anti_sycophancy_injector(max_age_hours: int = 24) -> int:
    """Remove old anti_sycophancy_injector state files.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        Number of files removed
    """
    state_dir = STATE_DIR / "anti_sycophancy_injector"
    if not state_dir.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in state_dir.glob("*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed old anti_sycophancy_injector state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_grounded_artifacts(max_age_hours: int = 24) -> int:
    """Remove old grounded_artifact state files.

    These are created by PreToolUse_investigation_gate.py and consumed within
    turns. Files that survive past max_age_hours are crash-recovery artifacts.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        Number of files removed
    """
    if not STATE_DIR.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in STATE_DIR.glob("grounded_artifact_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed old grounded_artifact state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_pretool_degraded(max_age_hours: int = 24) -> int:
    """Remove old pretool_degraded state files.

    These are created by PreToolUse.py and consumed within turns.
    Files that survive past max_age_hours are crash-recovery artifacts.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        Number of files removed
    """
    if not STATE_DIR.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in STATE_DIR.glob("pretool_degraded_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed old pretool_degraded state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_pending_obligations(max_age_minutes: int = 5) -> int:
    """Remove stale pending_obligation state files on session start.

    Obligations older than max_age_minutes are crash-recovery artifacts from
    sessions that terminated before the Stop hook could clear them.  The
    obligation TTL (OBLIGATION_TTL_SECONDS, default 600 s) is the authoritative
    expiry during a live session; this function removes files that survived
    longer than that because the process crashed before the Stop hook ran.

    Args:
        max_age_minutes: Maximum age in minutes before removing state file.
            Default 5 minutes — matches the in-session TTL so stale files
            are cleaned up promptly while legitimate in-session files are
            never touched (they are cleared by the Stop hook).

    Returns:
        Number of files removed
    """
    if not STATE_DIR.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_minutes * 60)

    for state_file in STATE_DIR.glob("pending_obligation_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_count += 1
                logger.info(f"Removed stale obligation state: {state_file.name}")
        except OSError:
            continue

    return removed_count


def cleanup_old_plan_files(max_age_days: int = 7, plan_dir: Path | None = None) -> int:
    """Remove stale plan files from ~/.claude/plans/.

    Plan mode guard blocks Edit/Write when ANY plan file exists.
    Stale plans from abandoned sessions can cause unexpected blocking.
    This cleanup removes plans older than max_age_days.

    Args:
        max_age_days: Maximum age in days before removing plan file
        plan_dir: Custom plan directory for testing (defaults to PLAN_DIR)

    Returns:
        Number of files removed
    """
    # Use provided plan_dir or default
    cleanup_dir = plan_dir if plan_dir is not None else PLAN_DIR

    if not cleanup_dir.exists():
        return 0

    removed_count = 0
    cutoff_time = time.time() - (max_age_days * 86400)  # 86400 seconds per day
    deleted_files = []

    # Only clean .md files in the root plans directory (not subdirectories)
    for plan_file in cleanup_dir.glob("*.md"):
        try:
            mtime = plan_file.stat().st_mtime
            if mtime < cutoff_time:
                plan_file.unlink()
                removed_count += 1
                deleted_files.append(plan_file.name)
                logger.info(f"Removed stale plan file: {plan_file.name}")
        except OSError:
            continue

    # Emit stdout notification when files are deleted (Item 4a)
    if removed_count > 0 and deleted_files:
        files_str = ", ".join(deleted_files[:3])  # Show max 3 files
        if len(deleted_files) > 3:
            files_str += f" and {len(deleted_files) - 3} others"
        print(f"🧹 Removed {removed_count} stale plan file(s): {files_str}")
        print("   Note: Automatic cleanup is supplemental - verify important plans manually")

    return removed_count


def cleanup_old_tdd_contracts(retention_days: int = 7) -> int:
    """Remove old TDD contract evidence directories.

    TDD Clean-Room Loop v2 (ADR-20260324) stores phase transition evidence
    in .claude/evidence/tdd95/{contract_id}/. Completed contracts older than
    retention_days are cleaned up automatically.

    Args:
        retention_days: Maximum age in days before removing contract evidence

    Returns:
        Number of contract directories removed
    """
    tdd_evidence_dir = EVIDENCE_DIR / "tdd95"
    if not tdd_evidence_dir.exists():
        return 0

    # Import the cleanup module (graceful degradation if unavailable)
    try:
        # Add tdd package to path
        tdd_dir = HOOK_DIR / "tdd"
        if str(tdd_dir) not in sys.path:
            sys.path.insert(0, str(tdd_dir))

        from contract_cleanup import cleanup_all_completed_contracts

        # Run cleanup with the configured retention period
        results = cleanup_all_completed_contracts(
            evidence_dir=tdd_evidence_dir,
            retention_days=retention_days,
            dry_run=False,
        )

        removed_count = len(results)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old TDD contract(s)")
            # Print notification for user visibility
            contract_ids = [r.contract_id for r in results[:3]]
            print(f"🧹 Removed {removed_count} old TDD contract(s): {', '.join(contract_ids)}")

        return removed_count

    except ImportError as e:
        logger.debug(f"TDD cleanup module not available: {e}")
        return 0
    except Exception as e:
        logger.warning(f"TDD cleanup failed: {e}")
        return 0


def inject_tdd_resume_context() -> None:
    """Inject TDD resume context if active TDD sessions exist.

    This is called after cleanup operations to restore TDD context
    that may have been lost during a compact event or session resume.

    Reads state files from:
    - .claude/state/tdd/{terminal_id}/tdd.*.json (TDD state files)
    - .claude/evidence/tdd95/{contract_id}/ (Phase 3 evidence)
    """
    try:
        from tdd_resume import generate_tdd_resume_context

        context = generate_tdd_resume_context()
        if context:
            # Print to stdout for SessionStart hook injection
            print("\n" + "=" * 60)
            print("📋 TDD SESSION RESUME CONTEXT DETECTED")
            print("=" * 60)
            print(context)
            print("=" * 60 + "\n")
            logger.info("Injected TDD resume context for active sessions")
    except ImportError as e:
        logger.debug(f"TDD resume module not available: {e}")
    except Exception as e:
        logger.warning(f"TDD resume context injection failed: {e}")


def main() -> None:
    """SessionStart hook for verification state cleanup."""
    # Check if enabled
    if not ENABLED:
        sys.exit(0)

    # Clean up old state files from all sources
    verification_removed = cleanup_old_verification_states(MAX_AGE_HOURS)
    existence_removed = cleanup_old_file_existence_decisions(MAX_AGE_HOURS)
    observe_removed = cleanup_old_observe_before_act(MAX_AGE_HOURS)
    anti_sycophancy_removed = cleanup_old_anti_sycophancy_injector(MAX_AGE_HOURS)
    obligations_removed = cleanup_old_pending_obligations(max_age_minutes=5)
    grounded_artifacts_removed = cleanup_old_grounded_artifacts(MAX_AGE_HOURS)
    pretool_degraded_removed = cleanup_old_pretool_degraded(MAX_AGE_HOURS)
    plan_files_removed = cleanup_old_plan_files(PLAN_MAX_AGE_DAYS)
    tdd_contracts_removed = cleanup_old_tdd_contracts(TDD_CONTRACT_RETENTION_DAYS)

    total_removed = (
        verification_removed
        + existence_removed
        + observe_removed
        + anti_sycophancy_removed
        + obligations_removed
        + grounded_artifacts_removed
        + pretool_degraded_removed
        + plan_files_removed
        + tdd_contracts_removed
    )

    if total_removed > 0:
        logger.info(
            f"Cleaned up {total_removed} old state file(s) "
            f"(verification: {verification_removed}, existence: {existence_removed}, "
            f"observe: {observe_removed}, anti_sycophancy: {anti_sycophancy_removed}, "
            f"obligations: {obligations_removed}, grounded_artifacts: {grounded_artifacts_removed}, "
            f"pretool_degraded: {pretool_degraded_removed}, "
            f"plan_files: {plan_files_removed}, tdd_contracts: {tdd_contracts_removed})"
        )

    # Inject TDD resume context if active sessions exist (after compact/session resume)
    inject_tdd_resume_context()

    sys.exit(0)


if __name__ == "__main__":
    main()
