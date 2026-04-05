#!/usr/bin/env python3
"""
Table Output Verification Script for yt-fts Refactoring

This script captures the CURRENT table output from CLI commands and saves it
to a baseline file. After refactoring, run this script again and compare to
verify the table output format hasn't changed.

Usage:
    # Save baseline output (before refactoring)
    python scripts/verify_table_output.py --save-baseline

    # Compare current output to baseline (after refactoring)
    python scripts/verify_table_output.py --compare

    # Show current output only
    python scripts/verify_table_output.py --show

    # Full verification with comparison
    python scripts/verify_table_output.py --save-baseline --compare

Commands Captured:
    - yt-fts health
    - yt-fts stats
    - yt-fts list --library
    - yt-fts list --channel <channel_id>

Exit Codes:
    0: Verification passed (outputs match baseline)
    1: Verification failed (outputs differ from baseline)
    2: Error (missing baseline, database issues, etc.)

File Structure:
    scripts/baselines/
        table_output_health.txt
        table_output_stats.txt
        table_output_list_library.txt
        table_output_list_channel.txt
        metadata.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from click.testing import CliRunner
from yt_fts.core.cli import cli
from yt_fts.core.database import get_channels


# Configuration
BASELINE_DIR = Path(__file__).parent.parent / "scripts" / "baselines"
METADATA_FILE = BASELINE_DIR / "metadata.json"


def get_baseline_files() -> dict[str, Path]:
    """Get mapping of command names to baseline file paths."""
    return {
        "health": BASELINE_DIR / "table_output_health.txt",
        "stats": BASELINE_DIR / "table_output_stats.txt",
        "list_library": BASELINE_DIR / "table_output_list_library.txt",
        "list_channel": BASELINE_DIR / "table_output_list_channel.txt",
    }


def ensure_baseline_dir() -> None:
    """Ensure baseline directory exists."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)


def get_metadata() -> dict[str, Any]:
    """Load or create metadata dictionary."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {
        "created": None,
        "last_updated": None,
        "yt_fts_version": None,
        "python_version": sys.version,
        "commands": {}
    }


def save_metadata(data: dict[str, Any]) -> None:
    """Save metadata to file."""
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_first_channel_id() -> str | None:
    """Get the first channel ID from the database for testing list --channel."""
    try:
        channels = get_channels()
        if channels:
            return channels[0][1]  # channel_id is at index 1
    except Exception:
        pass
    return None


def capture_command_output(command_name: str, args: list[str] = None) -> tuple[int, str]:
    """
    Capture output from a CLI command.

    Args:
        command_name: Name of the command for logging
        args: List of CLI arguments to pass

    Returns:
        Tuple of (exit_code, output_string)
    """
    runner = CliRunner()
    result = runner.invoke(cli, args or [])

    return result.exit_code, result.output


def save_baseline(command_name: str, exit_code: int, output: str) -> Path:
    """
    Save command output to a baseline file.

    Args:
        command_name: Name of the command
        exit_code: Exit code from command execution
        output: Command output string

    Returns:
        Path to the saved baseline file
    """
    ensure_baseline_dir()

    baseline_files = get_baseline_files()
    filepath = baseline_files[command_name]

    # Write output with metadata header
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Baseline captured: {datetime.now().isoformat()}\n")
        f.write(f"# Command: yt-fts {' '.join(args_for_command(command_name))}\n")
        f.write(f"# Exit code: {exit_code}\n")
        f.write("#" + "=" * 76 + "\n")
        f.write(output)

    return filepath


def load_baseline(command_name: str) -> str | None:
    """
    Load baseline output from file.

    Args:
        command_name: Name of the command

    Returns:
        Baseline content string, or None if file doesn't exist
    """
    baseline_files = get_baseline_files()
    filepath = baseline_files[command_name]

    if not filepath.exists():
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        # Skip header lines
        lines = f.readlines()
        content_start = 0
        for i, line in enumerate(lines):
            if line.startswith("#" + "="):
                content_start = i + 1
                break
        return "".join(lines[content_start:])


def args_for_command(command_name: str, channel_id: str | None = None) -> list[str]:
    """Get CLI arguments for a command name."""
    if command_name == "health":
        return ["health"]
    elif command_name == "stats":
        return ["stats"]
    elif command_name == "list_library":
        return ["list", "--library"]
    elif command_name == "list_channel":
        if channel_id:
            return ["list", "--channel", channel_id]
        # Use a test channel ID
        return ["list", "--channel", "UCtest123"]
    return []


def compare_outputs(command_name: str, current_output: str) -> tuple[bool, str]:
    """
    Compare current output with saved baseline.

    Args:
        command_name: Name of the command
        current_output: Current command output

    Returns:
        Tuple of (matches, diff_string)
    """
    baseline = load_baseline(command_name)

    if baseline is None:
        return False, f"No baseline found for {command_name}"

    # Normalize outputs for comparison (ignore trailing whitespace differences)
    baseline_lines = [line.rstrip() for line in baseline.splitlines(keepends=True)]
    current_lines = [line.rstrip() for line in current_output.splitlines(keepends=True)]

    if baseline_lines == current_lines:
        return True, "Output matches baseline"

    # Generate diff
    diff = unified_diff(
        baseline_lines,
        current_lines,
        fromfile=f"baseline/{command_name}",
        tofile=f"current/{command_name}",
        lineterm=""
    )

    return False, "".join(diff)


def show_current_output(command_name: str) -> None:
    """Display current output for a command."""
    channel_id = get_first_channel_id()

    if command_name == "list_channel" and not channel_id:
        print("Warning: No channels found in database, using test channel ID")
        channel_id = "UCtest123"

    exit_code, output = capture_command_output(
        command_name,
        args_for_command(command_name, channel_id)
    )

    print(f"\n{'=' * 80}")
    print(f"Current output for: yt-fts {' '.join(args_for_command(command_name, channel_id))}")
    print(f"Exit code: {exit_code}")
    print(f"{'=' * 80}\n")
    print(output)


def save_all_baselines() -> dict[str, Any]:
    """
    Save baseline output for all commands.

    Returns:
        Dictionary with results for each command
    """
    results = {}
    channel_id = get_first_channel_id()

    commands_to_capture = [
        "health",
        "stats",
        "list_library",
    ]

    # Only capture list_channel if we have a channel
    if channel_id:
        commands_to_capture.append("list_channel")

    for cmd in commands_to_capture:
        print(f"\nCapturing baseline for: {cmd}")

        exit_code, output = capture_command_output(
            cmd,
            args_for_command(cmd, channel_id)
        )

        filepath = save_baseline(cmd, exit_code, output)
        results[cmd] = {
            "exit_code": exit_code,
            "output_length": len(output),
            "baseline_file": str(filepath)
        }

        print(f"  Saved to: {filepath}")
        print(f"  Exit code: {exit_code}")
        print(f"  Output length: {len(output)} characters")

    # Update metadata
    metadata = get_metadata()
    metadata["last_updated"] = datetime.now().isoformat()
    metadata["commands"] = results

    # Try to get version
    try:
        from yt_fts import __version__ as YT_FTS_VERSION
        metadata["yt_fts_version"] = YT_FTS_VERSION
    except Exception:
        metadata["yt_fts_version"] = "unknown"

    save_metadata(metadata)

    return results


def compare_all_baselines() -> dict[str, Any]:
    """
    Compare current output with all saved baselines.

    Returns:
        Dictionary with comparison results for each command
    """
    results = {}
    all_match = True
    channel_id = get_first_channel_id()

    commands_to_compare = [
        "health",
        "stats",
        "list_library",
    ]

    # Only compare list_channel if we have a baseline for it
    if (BASELINE_DIR / "table_output_list_channel.txt").exists():
        commands_to_compare.append("list_channel")

    for cmd in commands_to_compare:
        print(f"\n{'=' * 80}")
        print(f"Comparing: {cmd}")
        print(f"{'=' * 80}")

        exit_code, current_output = capture_command_output(
            cmd,
            args_for_command(cmd, channel_id)
        )

        matches, diff = compare_outputs(cmd, current_output)

        results[cmd] = {
            "matches": matches,
            "exit_code": exit_code,
            "current_length": len(current_output)
        }

        if matches:
            print(f"  Status: MATCHES baseline")
        else:
            print(f"  Status: DIFFERS from baseline")
            print(f"\nDiff:")
            print(diff)
            all_match = False

    return {
        "all_match": all_match,
        "commands": results
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify table output format for yt-fts refactoring"
    )
    parser.add_argument(
        "--save-baseline", "-s",
        action="store_true",
        help="Save current output as baseline"
    )
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="Compare current output to saved baseline"
    )
    parser.add_argument(
        "--show",
        action="store",
        metavar="COMMAND",
        nargs="?",
        const="all",
        help="Show current output for a command (or all commands)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Handle --show option
    if args.show is not None:
        if args.show == "all":
            for cmd in ["health", "stats", "list_library", "list_channel"]:
                show_current_output(cmd)
        else:
            show_current_output(args.show)
        return 0

    # Handle --save-baseline option
    if args.save_baseline:
        print("Saving baseline outputs...")
        print(f"Baseline directory: {BASELINE_DIR}")
        save_all_baselines()
        print(f"\nBaselines saved successfully!")
        print(f"Metadata saved to: {METADATA_FILE}")
        return 0

    # Handle --compare option
    if args.compare:
        if not METADATA_FILE.exists():
            print(f"Error: No baseline found. Run with --save-baseline first.")
            return 2

        print("Comparing current output to baseline...")
        results = compare_all_baselines()

        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")

        for cmd, result in results["commands"].items():
            status = "MATCH" if result["matches"] else "DIFFER"
            print(f"  {cmd}: {status}")

        if results["all_match"]:
            print(f"\nAll outputs match baseline! Refactoring preserved table format.")
            return 0
        else:
            print(f"\nSome outputs differ from baseline. Review the diff above.")
            return 1

    # No options specified - show help
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
