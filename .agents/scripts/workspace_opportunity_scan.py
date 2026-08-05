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
    """Check for unread harvest suggestions in pending/.

    harvest removed — handoffs are now the tracking system.
    """
    return []


def scan_capability_gaps():
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


def scan_open_handoffs():
    """Scan P:/docs/handoffs/ for OPEN handoffs with acceptance criteria.

    Used by /tp opportunity scan gate: if a track already has an open handoff
    with direction + acceptance criteria, it is EXECUTE_OR_DEFER, not RESEARCH.
    """
    handoffs_dir = Path("P:/docs/handoffs")
    if not handoffs_dir.exists():
        return []

    results = []
    for hf in handoffs_dir.rglob("HANDOFF.md"):
        try:
            text = hf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Parse frontmatter status
        status = "unknown"
        if text.startswith("---"):
            fm_end = text.find("---", 3)
            if fm_end > 0:
                fm = text[3:fm_end]
                for line in fm.splitlines():
                    if line.strip().startswith("status:"):
                        status = line.split(":", 1)[1].strip().strip('"').strip("'")
                        break

        if status != "open":
            continue

        # Check for acceptance criteria section
        has_criteria = any(
            kw in text.lower()
            for kw in ("## acceptance criteria", "## acceptance", "acceptance criteria")
        )

        # Extract title from first heading
        title = hf.parent.name
        for line in text.splitlines():
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break

        results.append({
            "path": str(hf.relative_to(Path("P:/"))),
            "title": title[:120],
            "has_acceptance_criteria": has_criteria,
            "disposition_hint": "EXECUTE_OR_DEFER" if has_criteria else "RESEARCH",
        })

    return results


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
        "open_handoffs": scan_open_handoffs(),
        "capability_gaps": scan_capability_gaps(),
        "recent_skill_changes": scan_untested_additions(),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("=== WORKSPACE OPPORTUNITY SCAN ===\n")

    if report["open_handoffs"]:
        execute_ready = [h for h in report["open_handoffs"] if h["has_acceptance_criteria"]]
        research_needed = [h for h in report["open_handoffs"] if not h["has_acceptance_criteria"]]
        if execute_ready:
            print(f"Execution-ready handoffs ({len(execute_ready)}) — EXECUTE_OR_DEFER, not RESEARCH:")
            for h in execute_ready[:15]:
                print(f"  [{h['disposition_hint']}] {h['title']}")
                print(f"    → {h['path']}")
            print()
        if research_needed:
            print(f"Open handoffs without acceptance criteria ({len(research_needed)}) — may need RESEARCH:")
            for h in research_needed[:10]:
                print(f"  [{h['disposition_hint']}] {h['title']}")
                print(f"    → {h['path']}")
            print()

    gaps = report["capability_gaps"]
    if gaps and gaps != "none detected" and isinstance(gaps, list):
        print(f"Capability gaps ({len(gaps)}):")
        for g in gaps[:10]:
            print(f"  {g}")
        print()

    if report["recent_skill_changes"]:
        print("Recent SKILL.md changes (untested):")
        for c in report["recent_skill_changes"][:5]:
            print(f"  {c}")
        print()

    if not any(v for k, v in report.items() if k != "capability_gaps"):
        print("No opportunities detected. Workspace is clean.")


if __name__ == "__main__":
    main()
