"""
Layer 3: Track call site migration progress.

This script verifies which call sites have been migrated to the new
config-based API and provides guidance for any remaining migrations.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple
from datetime import datetime


class CallSite(NamedTuple):
    """A call site to migrate."""
    number: int
    file: str
    line: int
    week: int
    description: str


# All 7 known call sites for BatchDownloader
CALL_SITES = [
    CallSite(1, "batch_execution.py", 249, 3,
             "Main batch execution entry point"),
    CallSite(2, "download_cli.py", 1603, 4,
             "CLI download command"),
    CallSite(3, "parallel_processor.py", 415, 5,
             "Rich progress display (no display plugin)"),
    CallSite(4, "parallel_processor.py", 564, 6,
             "FZF-style output with display plugin"),
    CallSite(5, "parallel_processor.py", 719, 7,
             "FZF output variant"),
    CallSite(6, "parallel_processor.py", 868, 8,
             "JSON output with display plugin"),
    CallSite(7, "parallel_processor.py", 1072, 9,
             "Plugin output with quota display"),
]


def check_call_site_migrated(site: CallSite, project_root: Path) -> bool:
    """
    Check if a call site has been migrated to config-based API.

    Args:
        site: The call site to check
        project_root: Root of the project

    Returns:
        True if migrated (uses config parameters)
    """
    # Find the file - check multiple possible locations
    possible_paths = [
        project_root / "src/yt_fts/core" / site.file,
        project_root / "src/yt_fts/download" / site.file,
        project_root / site.file,
    ]

    file_path = None
    for path in possible_paths:
        if path.exists():
            file_path = path
            break

    if not file_path:
        return False

    code = file_path.read_text()

    # Check if this file has config imports (site-level check)
    # Config imports indicate the file has been migrated
    config_import_patterns = [
        r"from \.batch_config import",
        r"from yt_fts\.download\.batch_config import",
        r"ExecutionConfig\(",
    ]

    for pattern in config_import_patterns:
        if re.search(pattern, code):
            return True

    return False


def scan_migration_status(project_root: Path) -> dict:
    """
    Scan all call sites and return migration status.

    Args:
        project_root: Root of the project

    Returns:
        Dictionary with migration status for each site
    """
    results = {}

    for site in CALL_SITES:
        migrated = check_call_site_migrated(site, project_root)
        results[site] = migrated

    return results


def print_migration_report(results: dict):
    """Print a formatted migration status report."""
    print("\n" + "=" * 70)
    print("BatchDownloader Refactor - Migration Status")
    print("=" * 70)
    print()

    migrated_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for site, migrated in results.items():
        status = "✅ MIGRATED" if migrated else "❌ OLD API"
        print(f"Site {site.number}: {site.file}:{site.line}")
        print(f"           {site.description}")
        print(f"           Status: {status}")
        print()

    print("-" * 70)
    print(f"Progress: {migrated_count}/{total_count} sites migrated")
    print(f"({migrated_count * 100 // total_count}% complete)")
    print("=" * 70)
    print()

    if migrated_count == total_count:
        print("🎉 All call sites migrated! Ready for Layer 4 (cleanup).")
    else:
        remaining = total_count - migrated_count
        print(f"⚠️  {remaining} site(s) still using old API.")
        print()
        print("Next steps:")
        for site, migrated in results.items():
            if not migrated:
                print(f"  - Migrate Site {site.number}: {site.file}:{site.line}")


# Usage
if __name__ == '__main__':
    import sys

    # Default project root
    project_root = Path(__file__).parents[4]  # Go up to project root

    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])

    print(f"Scanning project: {project_root}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    results = scan_migration_status(project_root)
    print_migration_report(results)

    # Exit with error if any sites not migrated
    all_migrated = all(results.values())
    sys.exit(0 if all_migrated else 1)
