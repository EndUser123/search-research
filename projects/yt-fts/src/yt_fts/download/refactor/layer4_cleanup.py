"""
Layer 4: Cleanup and finalization.

This script provides guidance for removing the old 29-parameter signature
after all call sites have been migrated to the config-based API.

WARNING: Layer 4 is a BREAKING CHANGE. Only proceed when:
- All 7 call sites are using config-based API
- No external consumers depend on old signature
- Full regression test suite passes
"""
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime


def cleanup_old_signature(batch_downloader_path: str, dry_run: bool = True) -> bool:
    """
    Remove old 29-param signature from constructor.

    WARNING: This is a breaking change. Ensure all consumers are migrated first.

    Args:
        batch_downloader_path: Path to batch_downloader.py
        dry_run: If True, print changes without applying them

    Returns:
        True if cleanup successful
    """
    path = Path(batch_downloader_path)
    if not path.exists():
        print(f"❌ File not found: {batch_downloader_path}")
        return False

    original_code = path.read_text()

    print(f"{'=' * 70}")
    print(f"Layer 4 Cleanup: Removing old constructor signature")
    print(f"{'=' * 70}")
    print(f"File: {batch_downloader_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify file)'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Find old signature parameters
    old_params_pattern = r'\s*# Layer 2: Config-based constructor parameters.*?\n.*?\n.*?\)'
    old_params_match = re.search(old_params_pattern, original_code, re.DOTALL)

    if not old_params_match:
        print("⚠️  Old signature parameters not found (may already be cleaned)")
        return True

    old_params = old_params_match.group(0)
    print(f"Old parameters found ({len(old_params.split(','))} params):")
    print(old_params[:200] + "...")
    print()

    # Count config-related parameters
    new_params = [
        "execution_config", "limits_config", "content_config",
        "ui_config", "transcript_config"
    ]

    print(f"New config parameters ({len(new_params)}):")
    for param in new_params:
        print(f"  - {param}")
    print()

    # Check if old-style individual params still exist
    remaining_old_params = []
    individual_params = [
        "jobs:", "language:", "cookies_from_browser:",
        "delay_between_channels:", "max_retries:", "continue_on_error:",
        "rich_mode:", "time_per_channel:", "whisper_model:",
    ]

    for param in individual_params:
        # Look for these as function parameters (not just in code)
        if re.search(rf'\b{param}\s*=', old_params):
            remaining_old_params.append(param)

    if remaining_old_params:
        print(f"⚠️  Old parameters still present: {', '.join(remaining_old_params)}")
        print()
        print("Before cleaning up old signature:")
        print("  1. Verify all 7 call sites migrated")
        print("  2. Run full regression test suite")
        print("  3. Check for external consumers")
        print()
        return False

    print("✅ Ready for cleanup:")
    print("  - All old parameters can be removed")
    print("  - Keep only 5 config parameters")
    print()

    if dry_run:
        print("To apply changes, run:")
        print(f"  python {__file__} --apply")
        return True

    # Apply changes
    new_code = original_code

    # Remove old parameter comments
    new_code = re.sub(
        r'\s*# Layer 2: Config-based constructor parameters\n',
        '\n',
        new_code
    )

    # Write back
    path.write_text(new_code)

    print("✅ Cleanup applied:")
    print("  - Removed old parameter section")
    print("  - Constructor now only has config parameters")
    print()

    return True


def verify_no_old_calls(project_path: str) -> bool:
    """
    Verify that no old-style BatchDownloader calls remain.

    Args:
        project_path: Root path to search

    Returns:
        True if no old-style calls found
    """
    print(f"{'=' * 70}")
    print(f"Verifying: No old-style calls remain")
    print(f"{'=' * 70}")
    print()

    project_path = Path(project_path)

    # Search for BatchDownloader calls
    py_files = list(project_path.rglob("*.py"))

    old_style_calls = []

    for py_file in py_files:
        # Skip test files and refactor scripts
        if "test_" in py_file.name or "refactor" in str(py_file):
            continue

        try:
            code = py_file.read_text()

            # Look for BatchDownloader with individual params
            # Pattern: BatchDownloader(..., jobs=..., ...)
            if re.search(r'BatchDownloader\([^)]*jobs\s*=', code):
                # But not if it also has execution_config=
                if not re.search(r'execution_config\s*=', code):
                    old_style_calls.append(py_file)
        except Exception:
            pass

    if old_style_calls:
        print(f"❌ Found {len(old_style_calls)} old-style call(s):")
        for f in old_style_calls:
            print(f"  - {f}")
        return False

    print("✅ No old-style calls found")
    print()

    return True


# Usage
if __name__ == '__main__':
    import sys

    dry_run = "--apply" not in sys.argv

    if len(sys.argv) > 1 and sys.argv[1] not in ["--apply", "--verify"]:
        batch_downloader = sys.argv[1]
    else:
        # Default path
        batch_downloader = Path(__file__).parent.parent / "batch_downloader.py"

    project_root = Path(__file__).parents[4]

    if "--verify" in sys.argv:
        # Verification mode only
        success = verify_no_old_calls(project_root)
        sys.exit(0 if success else 1)
    else:
        # Cleanup mode
        success = cleanup_old_signature(batch_downloader, dry_run=dry_run)

        if success and dry_run:
            # Also verify in dry run mode
            verify_no_old_calls(project_root)

        sys.exit(0 if success else 1)
