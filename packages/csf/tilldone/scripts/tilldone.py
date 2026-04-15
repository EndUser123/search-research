#!/usr/bin/env python3
"""
tilldone — Batch Convergence Runner

Run a command on each package in a target directory until phase states stop
changing (till-done) or for a fixed count.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def parse_phase_states(changelog_path: Path) -> dict[str, str]:
    """Parse phase states from references/changelog.md."""
    states = {}
    if not changelog_path.exists():
        return states
    content = changelog_path.read_text()
    for line in content.splitlines():
        match = re.match(r"- (PHASE \S+.*?) -- (\w+)", line)
        if match:
            phase_name = match.group(1).strip()
            status = match.group(2).strip()
            states[phase_name] = status
    return states


def run_command_for_target(target_dir: Path, command: str, extra_flags: list[str]) -> bool:
    """Run the command for a single target. Returns True on success."""
    cmd_str = f"{command} {target_dir}"
    if extra_flags:
        cmd_str += " " + " ".join(extra_flags)
    result = subprocess.run(
        ["claude", "-p", cmd_str],
        capture_output=False,
    )
    return result.returncode == 0


def tilldone(target: Path, command: str, extra_flags: list[str], max_iter: int = 20) -> dict:
    """Run till-done convergence loop for one package."""
    changelog = target / "references" / "changelog.md"

    for iteration in range(1, max_iter + 1):
        prev_states = parse_phase_states(changelog)

        success = run_command_for_target(target, command, extra_flags)
        if not success:
            return {"status": "error", "iterations": iteration, "reason": "command failed"}

        curr_states = parse_phase_states(changelog)

        if curr_states == prev_states:
            return {"status": "stable", "iterations": iteration}

    return {"status": "unstable", "iterations": max_iter}


def count_mode(target: Path, command: str, extra_flags: list[str], count: int) -> dict:
    """Run exactly N passes, no convergence check."""
    for i in range(1, count + 1):
        success = run_command_for_target(target, command, extra_flags)
        if not success:
            return {"status": "error", "iterations": i, "reason": "command failed"}
    return {"status": "done", "iterations": count}


def discover_targets(target_dir: Path) -> list[Path]:
    """Find all directories in target_dir that have a .git subdirectory."""
    targets = []
    if not target_dir.exists():
        print(f"ERROR: target directory does not exist: {target_dir}")
        return []

    for entry in sorted(target_dir.iterdir()):
        if entry.name.startswith("."):
            continue
        if not entry.is_dir():
            continue
        if (entry / ".git").is_dir():
            targets.append(entry)

    return targets


def dry_run(target: Path, command: str, extra_flags: list[str]):
    """Preview targets and iteration plan."""
    targets = discover_targets(target)
    print(f"Target directory: {target}")
    print(f"Command: {command}")
    if extra_flags:
        print(f"Extra flags: {' '.join(extra_flags)}")
    print(f"Discovered {len(targets)} packages:")
    for t in targets:
        print(f"  - {t.name}")
    print("\nRun without --dry-run to execute.")


def main():
    parser = argparse.ArgumentParser(description="Batch convergence runner")
    parser.add_argument("target", type=Path, help="Directory containing packages")
    parser.add_argument("-c", "--command", required=True, help="Command to run per package")
    parser.add_argument("--count", type=int, default=None, help="Run exactly N passes (overrides till-done)")
    parser.add_argument("--dry-run", action="store_true", help="Preview targets only")
    parser.add_argument(
        "--",
        dest="extra_flags", nargs="*", default=[],
        help="Flags passed through to the command",
    )

    args = parser.parse_args()

    if args.dry_run:
        dry_run(args.target, args.command, args.extra_flags)
        return

    targets = discover_targets(args.target)
    if not targets:
        print("No packages found.")
        sys.exit(1)

    results = []
    for target in targets:
        print(f"\n{'='*60}")
        print(f"Processing: {target.name}")

        if args.count is not None:
            result = count_mode(target, args.command, args.extra_flags, args.count)
        else:
            result = tilldone(target, args.command, args.extra_flags)

        print(f"Result: {result['status']} ({result['iterations']} iteration(s)")
        results.append((target.name, result))

    # Final summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    stable = sum(1 for _, r in results if r["status"] == "stable")
    done = sum(1 for _, r in results if r["status"] == "done")
    errors = sum(1 for _, r in results if r["status"] == "error")
    unstable = sum(1 for _, r in results if r["status"] == "unstable")

    for name, result in results:
        print(f"  {name}: {result['status']} ({result['iterations']} iters)")

    print(f"\nTotal: {stable + done} stable/done, {errors} errors, {unstable} unstable")

    if errors > 0 or unstable > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()