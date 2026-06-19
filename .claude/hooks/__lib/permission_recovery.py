"""
Permission recovery library for settings.json modifications.

Provides:
- Pattern matching for Read→Write permission detection
- Atomic settings.json modification with rollback
- Permission validation (dangerous pattern rejection)
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


class PermissionCandidate(NamedTuple):
    """Candidate for Read→Write permission pair recovery."""
    existing_read: str
    missing_write: str
    path: str


def find_matching_read_permission(write_path: str, settings: dict) -> str | None:
    """Check if a Write path has a corresponding Read permission.

    Args:
        write_path: The path being written to
        settings: Loaded settings.json dictionary

    Returns:
        The matching Read permission string, or None if no match
    """
    allowlist = settings.get("allowlist", [])
    write_normalized = _normalize_path(write_path)

    for perm in allowlist:
        if not perm.startswith("Read("):
            continue

        # Extract path from Read(path) pattern
        read_pattern = perm[5:-1]  # Strip "Read(" and ")"

        if _path_matches_pattern(write_normalized, read_pattern):
            return perm

    return None


def _normalize_path(path: str) -> str:
    """Normalize path for consistent matching."""
    return Path(path).resolve().as_posix()


def _path_matches_pattern(path: str, pattern: str) -> bool:
    """Check if path matches permission pattern."""
    # Handle wildcards
    if "*" in pattern:
        regex_pattern = pattern.replace("*", ".*").replace("/", r"\/*")
        return bool(re.fullmatch(regex_pattern, path))
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def generate_permission_diff(missing_write: str, settings: dict) -> dict:
    """Generate minimal diff for adding missing Write permission.

    Args:
        missing_write: The Write permission string to add
        settings: Loaded settings.json dictionary

    Returns:
        Dict with insertion location and content
    """
    allowlist = settings.get("allowlist", [])
    insert_index = _find_read_write_boundary(allowlist)

    return {
        "file": str(SETTINGS_PATH),
        "insert_index": insert_index,
        "content": f'    "{missing_write}",\n',
    }


def generate_write_pattern(read_permission: str) -> str:
    """Generate Write permission pattern from Read permission.

    Args:
        read_permission: Read permission string (e.g., "Read(P:/.claude/.staging/**)")

    Returns:
        Write permission string (e.g., "Write(P:/.claude/.staging/**)")
    """
    # Strip Read() and wrap in Write()
    path_pattern = read_permission[5:-1]
    return f"Write({path_pattern})"


def _find_read_write_boundary(allowlist: list) -> int:
    """Find index where Write permissions should be inserted (after Read, before Denylist)."""
    # Find last Read permission
    last_read_index = -1
    for i, perm in enumerate(allowlist):
        if perm.startswith("Read("):
            last_read_index = i

    # Insert after last Read, or at end if no Read permissions
    return last_read_index + 1 if last_read_index >= 0 else 0


def validate_proposed_permission(write_perm: str) -> tuple[bool, str]:
    """Reject dangerous permission expansions.

    Args:
        write_perm: The Write permission string to validate

    Returns:
        (is_valid, message): Tuple of validity and explanation
    """
    # Direct string checks for dangerous patterns - simple and reliable
    if "../**" in write_perm:
        return False, "DANGEROUS: Parent directory wildcard"

    # Reject root-level double wildcards only (Write(**) not Write(P:/.../**))
    if write_perm == "Write(**)" or write_perm == "Write(**)":
        return False, "DANGEROUS: Root-level double wildcard"

    if "write(c:/*)" in write_perm.lower():
        return False, "DANGEROUS: Root drive wildcard"

    if "write(~/*)" in write_perm.lower():
        return False, "DANGEROUS: User root wildcard"

    if "write(/*)" in write_perm.lower():
        return False, "DANGEROUS: Unix root wildcard"

    # Allow safe patterns like Write(P:/.claude/.staging/**)
    if write_perm.startswith("Write(P:/") or write_perm.startswith("Write(~/"):
        return True, "Permission safe"

    return False, "Unknown pattern - manual review required"


def add_permission_atomically(new_perm: str) -> tuple[bool, str]:
    """Add permission to settings.json with backup and JSON validation.

    Args:
        new_perm: The Write permission string to add (e.g., "Write(P:/.claude/.staging/**)")

    Returns:
        (success, message): Tuple of success status and message
    """
    # Validate before proceeding
    is_safe, reason = validate_proposed_permission(new_perm)
    if not is_safe:
        return False, f"Permission rejected: {reason}"

    # Create backup
    backup_success, backup_msg = _create_backup()
    if not backup_success:
        return False, backup_msg

    try:
        # Read and parse
        with open(SETTINGS_PATH, 'r+', encoding='utf-8') as f:
            settings = json.load(f)
            f.seek(0)
            f.truncate()

            # Insert permission at correct location
            allowlist = settings.get("allowlist", [])
            insert_index = _find_read_write_boundary(allowlist)
            allowlist.insert(insert_index, new_perm)

            # Atomic write
            json.dump(settings, f, indent=2, ensure_ascii=False)

        # Verify JSON validity
        try:
            with open(SETTINGS_PATH, encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            _restore_backup()
            return False, f"JSON corruption detected, restored backup: {e}"

        return True, f"Permission added: {new_perm}"

    except Exception as e:
        _restore_backup()
        return False, f"Failed to add permission: {type(e).__name__}: {e}"


def _create_backup() -> tuple[bool, str]:
    """Create timestamped backup of settings.json."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = SETTINGS_PATH.parent / f"settings.backup_{timestamp}.json"
        shutil.copy2(SETTINGS_PATH, backup_path)

        if not backup_path.exists():
            return False, f"Backup file not created: {backup_path}"

        with open(backup_path, encoding='utf-8') as f:
            json.load(f)  # Verify backup validity

        return True, f"Backup created: {backup_path.name}"

    except Exception as e:
        return False, f"Backup failed: {type(e).__name__}: {e}"


def _restore_backup() -> None:
    """Restore latest backup if modification failed."""
    backups = sorted(SETTINGS_PATH.parent.glob("settings.backup_*.json"), reverse=True)
    if backups:
        shutil.copy2(backups[0], SETTINGS_PATH)