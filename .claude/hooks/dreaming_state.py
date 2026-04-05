"""
State management for dreaming-daemon (T-003).

Provides persistent state storage for the dreaming daemon process.
Uses atomic write guarantees, backup rotation, and validation for corrupted state.
"""

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from backup_manager import BackupManager

logger = logging.getLogger(__name__)


@dataclass
class DreamingState:
    """State data for dreaming daemon process.

    Note: No file locking used. Daemon runs as singleton process.
    Concurrent access protection not needed.
    """

    version: int = 1  # Schema version for migration support
    offset: int = 0
    heartbeat: str = ""
    current_file: str = ""
    shutdown: bool = False
    canonical_pid: int = 0  # Canonical daemon PID (preserved on first acquisition)
    checksum: str = ""  # Content checksum for corruption detection (T-002)


def _validate_state(state: DreamingState) -> bool:
    """
    Validate DreamingState fields for corruption.

    Args:
        state: DreamingState instance to validate.

    Returns:
        True if state is valid, False otherwise.
    """
    # Check offset is non-negative
    if state.offset < 0:
        logger.warning(f"Invalid offset in state: {state.offset} < 0")
        return False

    # Check heartbeat format if present
    if state.heartbeat:
        try:
            datetime.fromisoformat(state.heartbeat)
        except ValueError:
            logger.warning(f"Invalid heartbeat format: {state.heartbeat}")
            return False

    # Check shutdown flag is boolean
    if not isinstance(state.shutdown, bool):
        logger.warning(f"Invalid shutdown flag type: {type(state.shutdown)}")
        return False

    return True


def _preserve_corrupted_file(path: Path) -> None:
    """
    Preserve corrupted file by renaming with timestamp suffix (T-005).

    Args:
        path: Path to corrupted file.

    Behavior:
        - Renames file to .corrupted.<timestamp>
        - Logs the preservation action

    Note:
        Timestamp format uses underscores instead of colons for Windows compatibility.
    """
    try:
        # Use timestamp format safe for Windows filenames (replace colons with underscores)
        timestamp = datetime.now(UTC).isoformat(timespec="seconds").replace(":", "_")
        corrupted_path = path.with_suffix(f"{path.suffix}.corrupted.{timestamp}")
        os.replace(path, corrupted_path)
        logger.info(f"Preserved corrupted file: {path.name} -> {corrupted_path.name}")
    except OSError as e:
        logger.error(f"Failed to preserve corrupted file {path.name}: {e}")


# Default state file path
STATE_FILE = Path("P:/.claude/state/dreaming-daemon-state.json")

# Number of backup state files to keep (P2 improvement)
# Reduced to 1 backup - sufficient for 60s heartbeat interval (T-007)
BACKUP_COUNT = 1


def load_state(state_path: Path | None = None) -> DreamingState:
    """
    Load dreaming daemon state from file with validation and backup fallback (P2 improvement).

    Args:
        state_path: Path to state file. Defaults to STATE_FILE.

    Returns:
        DreamingState with loaded data or defaults if file missing/corrupted.

    Behavior:
        - Try primary state file
        - If validation fails, preserve corrupted file with timestamp suffix
        - Find and restore from latest backup
        - Return default state if all files fail
    """
    path = state_path or STATE_FILE

    # Return default state if file doesn't exist
    if not path.exists():
        return DreamingState()

    # Try loading primary state file
    state = _load_state_file(path)
    if state and _validate_state(state):
        return state

    # Primary file failed validation - preserve corrupted file (T-005)
    logger.warning("Primary state file failed validation, initiating safe rollback...")
    _preserve_corrupted_file(path)

    # Find latest backup using BackupManager
    backup_mgr = BackupManager(path, BACKUP_COUNT)
    latest_backup = backup_mgr.find_latest_backup()

    if latest_backup:
        logger.info(f"Found latest backup: {latest_backup.name}")
        state = _load_state_file(latest_backup)

        if state and _validate_state(state):
            # Restore backup to primary location
            backup_mgr.restore_from_backup(latest_backup)

            # Log backup age for observability
            backup_mtime = datetime.fromtimestamp(latest_backup.stat().st_mtime, tz=UTC)
            backup_age = (datetime.now(UTC) - backup_mtime).total_seconds()
            logger.info(
                f"Successfully recovered from backup: {latest_backup.name} "
                f"(age: {backup_age:.0f}s, modified: {backup_mtime.isoformat()})"
            )
            return state
        else:
            logger.warning(f"Backup file {latest_backup.name} is also corrupted")
    else:
        logger.warning("No backup files found for recovery")

    # All files failed, return default state
    logger.warning("All state files (primary + backups) failed validation, using default state")
    return DreamingState()


def _load_state_file(path: Path) -> DreamingState | None:
    """
    Load state from a specific file without validation.

    Args:
        path: Path to state file.

    Returns:
        DreamingState if loaded successfully, None on error.

    Note:
        Checksum mismatch returns None to trigger rollback (T-005).
        JSON decode error returns None to trigger rollback (T-005).
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Verify checksum if present (T-004)
        if data.get("checksum"):
            # Calculate checksum of loaded content (without checksum field, sorted for consistency)
            data_dict_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
            json_str = json.dumps(data_dict_without_checksum, indent=2, sort_keys=True)
            calculated = hashlib.sha256(json_str.encode()).hexdigest()

            # Compare with stored checksum
            if calculated != data["checksum"]:
                logger.warning(
                    f"Checksum mismatch in {path.name} - file corrupted, triggering rollback. "
                    f"Stored: {data['checksum'][:8]}..., Calculated: {calculated[:8]}..."
                )
                # Return None to trigger rollback (T-005)
                return None
        # If checksum missing: allow load (backward compatibility)

        return DreamingState(**data)
    except (OSError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error loading state file {path.name}: {e} - triggering rollback")
        return None


def save_state(state: DreamingState, state_path: Path | None = None) -> None:
    """
    Save dreaming daemon state to file using atomic write with backup rotation (P2 improvement).

    Args:
        state: DreamingState instance to save.
        state_path: Path to state file. Defaults to STATE_FILE.

    Behavior:
        - Rotate backups using BackupManager (T-006)
        - Write new state atomically to primary path
        - Retry on WinError 32 (ERROR_SHARING_VIOLATION) with exponential backoff (10ms → 20ms → 40ms, max 250ms)
    """
    path = state_path or STATE_FILE

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Rotate backups using BackupManager (T-006)
    backup_mgr = BackupManager(path, BACKUP_COUNT)
    backup_mgr.rotate_backups()

    # Calculate checksum before writing (T-003)
    # 1. Serialize state to dict (without checksum field)
    data_dict = asdict(state)
    data_dict_without_checksum = {k: v for k, v in data_dict.items() if k != "checksum"}

    # 2. Calculate SHA256 of JSON content (without checksum, sorted for consistency)
    json_str = json.dumps(data_dict_without_checksum, indent=2, sort_keys=True)
    checksum = hashlib.sha256(json_str.encode()).hexdigest()

    # 3. Set checksum in state object
    state.checksum = checksum

    # 4. Atomic write pattern: write to temp file, then rename
    temp_path = path.with_suffix(".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2)
            # Flush buffers and fsync for durability
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename (temp -> actual) with retry on WinError 32
        delay = 0.01  # 10ms initial delay
        for attempt in range(3):  # max 3 attempts (1 initial + 2 retries)
            try:
                temp_path.replace(path)
                break
            except PermissionError as e:
                if getattr(e, "winerror", None) == 32 and attempt < 2:
                    import time

                    time.sleep(delay)
                    delay = min(delay * 2, 0.25)  # cap at 250ms
                    continue
                raise
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")
        # Clean up temp file if write failed
        if temp_path.exists():
            temp_path.unlink()
