"""
State migration script for evidence validation system.

Migrates existing empirical_observation_cache.json to the new hash cache format.
Preserves backward compatibility with existing state files.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Import after path setup
try:
    from shared_utils import log_hook_event
except ImportError:
    def log_hook_event(event_type: str, **kwargs):
        print(f"[{event_type}] {kwargs}")


def load_old_cache(cache_file: Path) -> dict[str, Any]:
    """Load old empirical observation cache file."""
    if not cache_file.exists():
        return {}

    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {cache_file}: {e}")
        return {}


def migrate_hash_cache(
    old_cache: dict[str, Any],
    new_cache_dir: Path,
    dry_run: bool = False
) -> dict[str, int]:
    """
    Migrate hash cache entries from old format to new per-terminal files.

    Old format:
    {
        "file_hashes": {
            "terminal_key": {
                "path/to/file.py": {"hash": "abc123", "updated_at": 1234567890.0},
                ...
            },
            ...
        },
        ...
    }

    New format (per-terminal):
    hash_cache_{terminal_key}.json:
    {
        "path/to/file.py": {"hash": "abc123", "updated_at": 1234567890.0},
        ...
    }
    """
    stats = {"migrated": 0, "skipped": 0, "errors": 0}

    file_hashes = old_cache.get("file_hashes", {})
    if not isinstance(file_hashes, dict):
        print("No file_hashes found in old cache")
        return stats

    # Create new cache directory
    new_cache_dir.mkdir(parents=True, exist_ok=True)

    for terminal_key, terminal_entries in file_hashes.items():
        if not isinstance(terminal_entries, dict):
            stats["skipped"] += 1
            continue

        # New cache file path
        new_cache_file = new_cache_dir / f"hash_cache_{terminal_key}.json"

        # Check if new cache already exists
        if new_cache_file.exists():
            try:
                existing = json.loads(new_cache_file.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    # Merge existing entries with migrated entries
                    for path, entry in terminal_entries.items():
                        if isinstance(entry, dict) and "hash" in entry:
                            existing[path] = entry
                            stats["migrated"] += 1
                    terminal_entries = existing
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Could not merge existing cache {new_cache_file}: {e}")
                stats["errors"] += 1

        if dry_run:
            print(f"[DRY RUN] Would write: {new_cache_file}")
            print(f"  Entries: {len(terminal_entries)}")
            stats["migrated"] += len(terminal_entries)
        else:
            try:
                new_cache_file.write_text(
                    json.dumps(terminal_entries, indent=2),
                    encoding="utf-8"
                )
                stats["migrated"] += len(terminal_entries)
                print(f"Migrated: {new_cache_file} ({len(terminal_entries)} entries)")
            except OSError as e:
                print(f"Error: Could not write {new_cache_file}: {e}")
                stats["errors"] += 1

    return stats


def backup_old_state(cache_file: Path) -> Path | None:
    """Create backup of old state file."""
    if not cache_file.exists():
        return None

    backup_path = cache_file.with_suffix(f"{cache_file.suffix}.bak")

    try:
        shutil.copy2(cache_file, backup_path)
        print(f"Backup created: {backup_path}")
        return backup_path
    except OSError as e:
        print(f"Warning: Could not create backup: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Migrate evidence validation state to new format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of old state files"
    )
    parser.add_argument(
        "--old-cache",
        type=str,
        default=None,
        help="Path to old empirical_observation_cache.json (default: session_data/empirical_observation_cache.json)"
    )
    parser.add_argument(
        "--new-cache-dir",
        type=str,
        default=None,
        help="Path to new hash cache directory (default: session_data/evidence/)"
    )

    args = parser.parse_args()

    # Resolve paths
    if args.old_cache:
        old_cache_file = Path(args.old_cache)
    else:
        old_cache_file = HOOKS_DIR / "session_data" / "empirical_observation_cache.json"

    if args.new_cache_dir:
        new_cache_dir = Path(args.new_cache_dir)
    else:
        new_cache_dir = HOOKS_DIR / "session_data" / "evidence"

    print(f"Old cache file: {old_cache_file}")
    print(f"New cache directory: {new_cache_dir}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Load old cache
    old_cache = load_old_cache(old_cache_file)
    if not old_cache:
        print("No old cache data found. Nothing to migrate.")
        return 0

    print(f"Loaded old cache with {len(old_cache)} top-level keys")

    # Create backup unless skipped
    if not args.dry_run and not args.no_backup:
        backup_old_state(old_cache_file)

    # Migrate hash cache
    print("\nMigrating hash cache...")
    stats = migrate_hash_cache(old_cache, new_cache_dir, dry_run=args.dry_run)

    print("\nMigration complete:")
    print(f"  Migrated: {stats['migrated']} entries")
    print(f"  Skipped: {stats['skipped']} terminals")
    print(f"  Errors: {stats['errors']}")

    if args.dry_run:
        print("\n[DRY RUN] No files were modified.")
        print("Run without --dry-run to perform the migration.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
