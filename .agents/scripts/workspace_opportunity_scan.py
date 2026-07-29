"""Workspace opportunity scan — combines multiple audit sources into one report.

Called by /tp explore as a pre-step and by /aar as input.
Surfaces: harvest obligations, capability gaps, untested additions,
unwired conventions, and skill-graph recommendations.

Usage:
    python workspace_opportunity_scan.py [--json]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def scan_harvest_pending():
    """Check for unread harvest suggestions in pending/."""
    pending_dir = Path("P:/.data/harvest/pending")
    if not pending_dir.exists():
        return []
    suggestions = []
    for f in pending_dir.glob("*.json"):
        try:
            items = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(items, list):
                for item in items:
                    item["source"] = f.name
                    suggestions.append(item)
        except (json.JSONDecodeError, OSError):
            continue
    return suggestions


def scan_capability_gaps():
    """Find capabilities consumed but not provided by any skill."""
    result = subprocess.run(
        [sys.executable, "P:/.data/wiki/scripts/capabilities.py", "--help-text"],
        capture_output=True, text=True, check=False, cwd="P:/"
    )
    if result.returncode != 0:
        return "capabilities.py unavailable"

    text = result.stdout
    # Look for capabilities with no "provided by"
    gaps = []
    for line in text.splitlines():
        if "-- provided by" not in line and "**" in line and "--" not in line:
            # Capability with no provider
            m = re.search(r'\*\*(.+?)\*\*', line)
            if m:
                gaps.append(m.group(1))
    return gaps if gaps else "none detected"


def scan_harvest_store():
    """Read harvest store for OPEN items."""
    harvest_script = Path.home() / ".grok/skills/harvest/scripts/harvest.py"
    if not harvest_script.exists():
        return []
    result = subprocess.run(
        [sys.executable, str(harvest_script), "show", "--top", "20"],
        capture_output=True, text=True, check=False,
        env={**os.environ, "HARVEST_HOME": "P:/.data/harvest"}
    )
    if result.returncode != 0:
        return []
    # Parse items from output
    items = []
    for line in result.stdout.splitlines():
        m = re.match(r'\d+\.\s+(.+)', line)
        if m:
            items.append(m.group(1))
    return items


def scan_untested_additions():
    """Check if recently-added SKILL.md features have been exercised."""
    # This is heuristic — check if recent git commits added SKILL.md text
    # that hasn't been validated via a real skill invocation
    result = subprocess.run(
        ["git", "log", "--oneline", "--since=2 days ago", "--", "*/SKILL.md"],
        capture_output=True, text=True, check=False, cwd=str(Path.home() / ".grok")
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []

    commits = result.stdout.strip().splitlines()
    untested = []
    for line in commits:
        if any(kw in line.lower() for kw in ["add", "fix", "wire", "checkpoint", "lens"]):
            untested.append(line.strip())
    return untested[:10]


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="output as JSON")
    args = parser.parse_args()

    report = {
        "harvest_pending": scan_harvest_pending(),
        "harvest_open_items": scan_harvest_store(),
        "capability_gaps": scan_capability_gaps(),
        "recent_skill_changes": scan_untested_additions(),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("=== WORKSPACE OPPORTUNITY SCAN ===\n")

    if report["harvest_pending"]:
        print(f"Harvest pending suggestions ({len(report['harvest_pending'])}):")
        for item in report["harvest_pending"]:
            print(f"  [{item.get('source', '?')}] {item.get('title', '?')[:80]}")
        print()

    if report["harvest_open_items"]:
        print(f"Harvest open items ({len(report['harvest_open_items'])}):")
        for item in report["harvest_open_items"][:10]:
            print(f"  {item}")
        print()

    gaps = report["capability_gaps"]
    if gaps and gaps != "none detected" and isinstance(gaps, list):
        print(f"Capability gaps ({len(gaps)}):")
        for g in gaps[:10]:
            print(f"  {g}")
        print()

    if report["recent_skill_changes"]:
        print(f"Recent SKILL.md changes (untested):")
        for c in report["recent_skill_changes"][:5]:
            print(f"  {c}")
        print()

    if not any(v for k, v in report.items() if k != "capability_gaps"):
        print("No opportunities detected. Workspace is clean.")


if __name__ == "__main__":
    main()
