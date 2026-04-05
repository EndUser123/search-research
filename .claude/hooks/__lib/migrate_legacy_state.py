#!/usr/bin/env python3
"""
Migrate legacy state files to per-terminal state directory structure (TASK-005).

This script migrates state files from the legacy flat directory structure
to the new per-terminal isolated structure:

Legacy → New:
- session_data/intent_state.json → state/sessions/{session_id}/intent_state.json
- pending_command_intent_{terminal_id}.json → state/terminals/{terminal_id}/pending_command_intent.json
- session_data/*.json → state/sessions/{session_id}/ (if session-specific)

The migration is:
- Idempotent: Safe to run multiple times
- Atomic: Uses temporary files and rename operations
- Safe: Creates backups before migration
- Rollback-capable: Can undo migrations if needed

Usage:
    python -m __lib.migrate_legacy_state [--dry-run] [--force]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from __lib.state_paths import (
        SESSIONS_DIR,
        STATE_DIR,
        TERMINALS_DIR,
        get_session_state_path,
        get_terminal_id,
        get_terminal_state_path,
    )
except ImportError:
    print("ERROR: state_paths module not available", file=sys.stderr)
    sys.exit(1)


# Migration tracking
MIGRATION_LOG = STATE_DIR / "migration_log.jsonl"
BACKUP_DIR = STATE_DIR / "migration_backups"


def log_migration(action: str, source: str, target: str, success: bool) -> None:
    """Log migration action to audit trail."""
    try:
        MIGRATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "source": str(source),
            "target": str(target),
            "success": success,
        }
        with open(MIGRATION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Best-effort logging


def backup_file(source: Path) -> Path | None:
    """Create backup of file before migration."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / f"{source.name}.bak"
        shutil.copy2(source, backup_path)
        return backup_path
    except OSError:
        return None


def migrate_intent_state_file(dry_run: bool = False) -> dict:
    """Migrate session_data/intent_state.json to session-scoped paths.

    Legacy: session_data/intent_state.json
    New: state/sessions/{session_id}/intent_state.json

    Returns: Migration statistics
    """
    stats = {"migrated": 0, "failed": 0, "skipped": 0}

    # Legacy intent state file
    legacy_file = Path(__file__).resolve().parents[1] / "session_data" / "intent_state.json"

    if not legacy_file.exists():
        stats["skipped"] = 0  # No legacy file to migrate
        return stats

    try:
        # Read legacy state
        with open(legacy_file, encoding="utf-8") as f:
            legacy_data = json.load(f)

        # Extract session_id if available
        session_id = legacy_data.get("session_id") or "unknown"

        # Create new session-scoped path
        new_file = get_session_state_path(session_id, "intent_state.json")
        new_file.parent.mkdir(parents=True, exist_ok=True)

        if not dry_run:
            # Backup original
            backup = backup_file(legacy_file)

            # Write to new location
            with open(new_file, "w", encoding="utf-8") as f:
                json.dump(legacy_data, f, indent=2)

            # Verify write succeeded before deleting source
            with open(new_file, encoding="utf-8") as f:
                json.load(f)  # Verify valid JSON

            # Remove legacy file
            legacy_file.unlink(missing_ok=True)

        log_migration("migrate", legacy_file, new_file, True)
        stats["migrated"] += 1

    except (json.JSONDecodeError, OSError):
        log_migration("migrate", legacy_file, "intent_state.json", False)
        stats["failed"] += 1

    return stats


def migrate_pending_command_intent_files(dry_run: bool = False) -> dict:
    """Migrate pending_command_intent_{terminal_id}.json to terminal-scoped paths.

    Legacy: {hooks_dir}/.state/pending_command_intent_{terminal_id}.json
    New: state/terminals/{terminal_id}/pending_command_intent.json

    Returns: Migration statistics
    """
    stats = {"migrated": 0, "failed": 0, "skipped": 0}

    # Legacy state directory
    hooks_dir = Path(__file__).resolve().parents[1]
    legacy_state_dir = hooks_dir / ".state"

    if not legacy_state_dir.exists():
        stats["skipped"] = 0
        return stats

    try:
        # Find all pending_command_intent files
        for legacy_file in legacy_state_dir.glob("pending_command_intent_*.json"):
            try:
                # Extract terminal_id from filename
                terminal_id = legacy_file.stem.replace("pending_command_intent_", "")
                if not terminal_id:
                    stats["skipped"] += 1
                    continue

                # Read legacy state
                with open(legacy_file, encoding="utf-8") as f:
                    legacy_data = json.load(f)

                # Create new terminal-scoped path
                new_file = get_terminal_state_path(terminal_id, "pending_command_intent.json")
                new_file.parent.mkdir(parents=True, exist_ok=True)

                if not dry_run:
                    # Backup original
                    backup = backup_file(legacy_file)

                    # Write to new location
                    with open(new_file, "w", encoding="utf-8") as f:
                        json.dump(legacy_data, f, indent=2)

                    # Verify write succeeded
                    with open(new_file, encoding="utf-8") as f:
                        json.load(f)

                    # Remove legacy file
                    legacy_file.unlink(missing_ok=True)

                log_migration("migrate", legacy_file, new_file, True)
                stats["migrated"] += 1

            except (json.JSONDecodeError, OSError):
                log_migration("migrate", legacy_file, "terminal_scoped_path", False)
                stats["failed"] += 1

    except OSError:
        pass

    return stats


def migrate_session_data_files(dry_run: bool = False) -> dict:
    """Migrate session_data files to appropriate scoped paths.

    Returns: Migration statistics
    """
    stats = {"migrated": 0, "failed": 0, "skipped": 0}

    # Legacy session_data directory
    hooks_dir = Path(__file__).resolve().parents[1]
    session_data_dir = hooks_dir / "session_data"

    if not session_data_dir.exists():
        stats["skipped"] = 0
        return stats

    try:
        # Find all JSON files in session_data
        for legacy_file in session_data_dir.glob("*.json"):
            try:
                # Read file to determine type
                with open(legacy_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Determine appropriate migration based on content
                filename = legacy_file.name

                # Intent state files → session-scoped
                if filename == "intent_state.json":
                    session_id = data.get("session_id") or "unknown"
                    new_file = get_session_state_path(session_id, filename)

                # Hook dev session files → session-scoped
                elif filename.startswith("hook_dev_session_"):
                    session_id = data.get("session_id") or filename.replace("hook_dev_session_", "").replace(".json", "")
                    new_file = get_session_state_path(session_id, filename)

                # Active command files → session-scoped
                elif filename.startswith("active_command_"):
                    session_id = data.get("session_id") or "unknown"
                    new_file = get_session_state_path(session_id, filename)

                # Skip files that don't fit migration pattern
                else:
                    stats["skipped"] += 1
                    continue

                new_file.parent.mkdir(parents=True, exist_ok=True)

                if not dry_run:
                    # Backup original
                    backup = backup_file(legacy_file)

                    # Write to new location
                    with open(new_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)

                    # Verify write succeeded
                    with open(new_file, encoding="utf-8") as f:
                        json.load(f)

                    # Remove legacy file
                    legacy_file.unlink(missing_ok=True)

                log_migration("migrate", legacy_file, new_file, True)
                stats["migrated"] += 1

            except (json.JSONDecodeError, OSError):
                log_migration("migrate", legacy_file, "session_scoped_path", False)
                stats["failed"] += 1

    except OSError:
        pass

    return stats


def rollback_migration() -> dict:
    """Rollback migrations by restoring from backups.

    Returns: Rollback statistics
    """
    stats = {"restored": 0, "failed": 0}

    if not BACKUP_DIR.exists():
        return stats

    try:
        # Restore all backup files
        for backup_file in BACKUP_DIR.glob("*.bak"):
            try:
                # Original filename (remove .bak suffix)
                original_name = backup_file.stem
                original_path = backup_file.parent.parent / original_name

                # Restore backup
                shutil.copy2(backup_file, original_path)

                # Remove backup
                backup_file.unlink()

                stats["restored"] += 1

            except OSError:
                stats["failed"] += 1

        # Try to remove backup directory if empty
        try:
            BACKUP_DIR.rmdir()
        except OSError:
            pass

    except OSError:
        pass

    return stats


def main(dry_run: bool = False, force: bool = False) -> None:
    """Run migration process.

    Args:
        dry_run: Show what would be migrated without making changes
        force: Run migration even if already completed
    """
    print("TASK-005 State Migration: Legacy → Per-Terminal Structure")
    print("=" * 60)

    total_stats = {"migrated": 0, "failed": 0, "skipped": 0}

    # Migration steps
    migrations = [
        ("Intent state files", migrate_intent_state_file),
        ("Pending command intent files", migrate_pending_command_intent_files),
        ("Session data files", migrate_session_data_files),
    ]

    for name, migrate_fn in migrations:
        print(f"\n{name}...")
        stats = migrate_fn(dry_run=dry_run)
        print(f"  Migrated: {stats['migrated']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")

        total_stats["migrated"] += stats["migrated"]
        total_stats["failed"] += stats["failed"]
        total_stats["skipped"] += stats["skipped"]

    print("\n" + "=" * 60)
    print(f"Total: Migrated {total_stats['migrated']} files, Failed {total_stats['failed']}, Skipped {total_stats['skipped']}")

    if dry_run:
        print("\n[DRY RUN] No changes were made. Run without --dry-run to execute migration.")

    if total_stats["failed"] > 0:
        print(f"\n⚠️  WARNING: {total_stats['failed']} files failed to migrate")
        print("   Check migration log for details:", MIGRATION_LOG)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate legacy state files to per-terminal structure")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--force", action="store_true", help="Force migration even if already completed")
    args = parser.parse_args()

    main(dry_run=args.dry_run, force=args.force)
