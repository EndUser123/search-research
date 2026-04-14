#!/usr/bin/env python3
"""
Track phase completion in the target package's changelog.

Reads the target's references/changelog.md to determine which phases have
already completed, and appends phase completion markers after each run.

Format in changelog:
  ## v5.25.0 (2026-04-14)
  - PHASE 1: Diagnose and Prep -- COMPLETED
  - PHASE 1.5: Detect Package Type -- COMPLETED
"""

import argparse
import re
import sys
from pathlib import Path


def find_changelog(target_dir: Path) -> Path | None:
    """Find changelog.md in the target package.

    Preference order:
    1. references/changelog.md (gitready convention) -- if references/ exists, always use this path
    2. changelog.md (root level)
    3. CHANGELOG.md (root level, uppercase)
    """
    # If references/ exists, always use it as the canonical path (even if file doesn't exist yet)
    refs_dir = target_dir / "references"
    if refs_dir.exists() and refs_dir.is_dir():
        return refs_dir / "changelog.md"

    candidates = [
        target_dir / "changelog.md",
        target_dir / "CHANGELOG.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_completed_phases(changelog_path: Path) -> set[str]:
    """Parse the changelog and return set of completed phase names."""
    completed = set()
    if not changelog_path.exists():
        return completed

    content = changelog_path.read_text(encoding="utf-8")
    # Match lines like: "  - PHASE 1: Diagnose and Prep -- COMPLETED"
    pattern = re.compile(r"^\s*-\s*(PHASE\s+[\d.]+):\s*.*--\s*COMPLETED", re.IGNORECASE)
    for line in content.splitlines():
        if pattern.match(line):
            # Extract "PHASE 1" or "PHASE 1.5" etc.
            phase_match = re.search(r"(PHASE\s+[\d.]+)", line, re.IGNORECASE)
            if phase_match:
                completed.add(phase_match.group(1).upper())
    return completed


def append_phase_completion(changelog_path: Path, phase_name: str, phase_desc: str) -> None:
    """Append a phase completion marker to the changelog."""
    marker = f"- PHASE {phase_name}: {phase_desc} -- COMPLETED"

    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
    else:
        # Create minimal changelog if none exists
        content = "# Changelog\n\n"

    # Normalize line endings
    content = content.rstrip() + "\n"

    # If content doesn't end with newline, add one
    if content and not content.endswith("\n"):
        content += "\n"

    content += marker + "\n"
    changelog_path.write_text(content, encoding="utf-8")


PHASE_DEFINITIONS = {
    "1": "Diagnose and Prep",
    "1.5": "Detect Package Type",
    "1.6": "Brownfield Conversion",
    "1.6.5": "Intentional Exception Registry",
    "1.7": "Plugin Standards Validation",
    "1.8": "Stale Location Cleanup and Junction/Symlink Setup",
    "2": "Build Structure",
    "3": "Generate Templates",
    "4": "Validate",
    "4.5": "Code Review and Meta-Review",
    "4.6": "Quality Scanning",
    "4.7": "Media Generation",
    "4.8": "Interactive Course",
    "5": "Portfolio Polish",
    "6": "GitHub Publication",
    "7": "Repository Finalization",
    "8": "Cleanup",
    "9": "Git Ready",
    "10": "Recruiter Readiness Validation",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Track gitready phase completion in changelog")
    parser.add_argument("target_dir", help="Target package directory")
    parser.add_argument("--read", action="store_true", help="Read completed phases from changelog")
    parser.add_argument("--write", help="Write completed phase (e.g. '1' or '1.5')")
    parser.add_argument("--list", action="store_true", help="List all phase definitions")
    args = parser.parse_args()

    target = Path(args.target_dir)

    if args.list:
        for num, desc in PHASE_DEFINITIONS.items():
            print(f"PHASE {num}: {desc}")
        return

    changelog = find_changelog(target)
    if args.read:
        if changelog is None:
            print("No changelog found -- all phases pending", file=sys.stderr)
            print("ALL_PENDING")
            return
        completed = parse_completed_phases(changelog)
        if not completed:
            print("No phases completed yet", file=sys.stderr)
            print("ALL_PENDING")
            return
        print(f"COMPLETED: {','.join(sorted(completed))}")
        return

    if args.write:
        phase_num = args.write
        if phase_num not in PHASE_DEFINITIONS:
            print(f"Unknown phase: {phase_num}", file=sys.stderr)
            sys.exit(1)

        if changelog is None:
            changelog = target / "references" / "changelog.md"
            changelog.parent.mkdir(parents=True, exist_ok=True)

        append_phase_completion(changelog, phase_num, PHASE_DEFINITIONS[phase_num])
        print(f"Tracked: PHASE {phase_num} completed in {changelog}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
