#!/usr/bin/env python3
"""
Audit finding-to-skill coverage: which finding types have skills that detect
them, which don't, and which skills have finding-detection capabilities that
/tp session never invokes.

This script answers two questions:
1. "If we have skills for findings that don't exist, are we checking for
   those findings?" — i.e., capabilities that exist but aren't invoked.
2. "Are there findings with no skill coverage?" — i.e., gaps where a
   detection mechanism is missing entirely.

Usage:
    python audit_finding_coverage.py              # summary report
    python audit_finding_coverage.py --json        # JSON output
    python audit_finding_coverage.py --gaps-only    # only uncovered findings
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from capabilities import CapabilityRegistry

# ─── Finding types and their detection skills ───────────────────────────────
# Maps each finding type to the skills that SHOULD detect it.
# "Detection mechanism" describes how the skill finds the finding.

FINDING_TYPES: dict[str, dict] = {
    "FRICTION": {
        "description": "Recurring operational failure (>=2 instances)",
        "detecting_skills": {
            "/tp session": "transcript scan (Step 0b)",
            "/debrief": "5-lens retrospective scan",
        },
        "invoked_by_tp_session": True,
    },
    "OBLIGATION": {
        "description": "Incomplete work, blockers, verification gaps",
        "detecting_skills": {
            "/tp session": "NOW pass",
            "/close": "gate resolution scan",
            "/harvest": "unrealized obligation tracking",
        },
        "invoked_by_tp_session": True,
    },
    "LEARNED": {
        "description": "Durable knowledge worth remembering",
        "detecting_skills": {
            "/wiki": "knowledge distillation",
            "/tp session": "LEARNED findings in NOTED table",
        },
        "invoked_by_tp_session": True,
    },
    "SURPRISE": {
        "description": "Unexpected events, wrong assumptions",
        "detecting_skills": {
            "/why": "root cause analysis from surprising observation",
            "/tp session": "SURPRISE type (but no /why invocation)",
        },
        "invoked_by_tp_session": False,  # not routed to /why
    },
    "OPPORTUNITY": {
        "description": "Improvements possible, architectural enhancements",
        "detecting_skills": {
            "/tp explore": "system decomposition + opportunity surfacing",
            "/aar": "opportunity landscape",
            "/tp session": "OPPORTUNITY type (but no /tp explore invocation)",
        },
        "invoked_by_tp_session": False,  # not routed to /tp explore
    },
    "CONTINUE": {
        "description": "What went well, reusable approaches",
        "detecting_skills": {
            "/debrief": "what worked lens scan",
            "/wiki": "pattern capture",
            "/tp session": "CONTINUE type in NOTED table",
        },
        "invoked_by_tp_session": False,  # not routed to /debrief
    },
    "STOP": {
        "description": "Anti-patterns to retire, dead workflows",
        "detecting_skills": {
            "/debrief": "what didn't work lens scan",
            "/tp session": "STOP type (but not routed to /debrief)",
        },
        "invoked_by_tp_session": False,  # not routed to /debrief
    },
}

# ─── Skills with detection capabilities not invoked by /tp session ──────────

UNDERUTILIZED_SKILLS: dict[str, str] = {
    "/notice": "Mid-conversation observation surfacing — detects patterns during conversation that recall misses",
    "/harvest": "Output tracking with unrealized obligation — tracks work that consumed effort but wasn't claimed",
    "/dream": "Offline memory consolidation — detects chronic patterns spanning 90 days",
    "/skill-dev": "Skill measurement — measures whether skills used this session added value",
}

# ─── Findings with no detection skill at all (gaps) ─────────────────────────

FINDING_GAPS: dict[str, dict] = {
    "behavioral-drift": {
        "description": "Agent stopped following a rule (gradual shift)",
        "proposed_detection": "CUSUM drift detection across sessions",
        "data_sources": ["/tp critique log", "/aar artifacts", "transcript scans"],
        "skill_exists": False,
    },
    "coverage-gap": {
        "description": "Capabilities claimed but never exercised",
        "proposed_detection": "Skill graph audit (this script)",
        "data_sources": ["capability registry", "skill frontmatter", "transcripts"],
        "skill_exists": False,
    },
    "calibration-tracking": {
        "description": "Expressed confidence vs actual accuracy",
        "proposed_detection": "Calibration curve per session",
        "data_sources": ["reasoning traces", "outcome quality"],
        "skill_exists": False,
    },
    "constitutional-compliance": {
        "description": "AGENTS.md rules checked mechanically against behavior",
        "proposed_detection": "Rule-compliance scanner",
        "data_sources": ["AGENTS.md", "session transcripts"],
        "skill_exists": False,
    },
    "cross-session-friction-aggregation": {
        "description": "Same friction pattern in N of last M sessions",
        "proposed_detection": "Per-pattern frequency from critique log",
        "data_sources": ["/tp critique log", "/aar artifacts"],
        "skill_exists": "PARTIAL — /dream does 90-day synthesis but not per-pattern frequency",
    },
}


def audit_coverage(reg: CapabilityRegistry) -> dict:
    """Run the coverage audit and return structured results."""
    results = {
        "finding_types": {},
        "underutilized_skills": {},
        "finding_gaps": {},
        "registry_bugs": [],
    }

    # 1. Check each finding type for coverage
    for ftype, info in FINDING_TYPES.items():
        coverage = "COVERED" if info["invoked_by_tp_session"] else "PARTIAL"
        results["finding_types"][ftype] = {
            "description": info["description"],
            "detecting_skills": list(info["detecting_skills"].keys()),
            "invoked_by_tp_session": info["invoked_by_tp_session"],
            "coverage": coverage,
            "gap": (
                "Not routed to specialized skill in /tp session"
                if not info["invoked_by_tp_session"]
                else None
            ),
        }

    # 2. Check for skills that exist but aren't invoked
    for skill, description in UNDERUTILIZED_SKILLS.items():
        results["underutilized_skills"][skill] = description

    # 3. Check for finding patterns with no skill
    for gap_name, gap_info in FINDING_GAPS.items():
        results["finding_gaps"][gap_name] = gap_info

    # 4. Check for registry bugs (capabilities with no provider)
    for cap_name in reg.list_capabilities():
        providers = reg.get_by_capability(cap_name)
        if not providers:
            results["registry_bugs"].append({
                "capability": cap_name,
                "issue": "No providing skill — capability contract exists but no skill declares it in provides:",
            })

    return results


def print_report(results: dict):
    """Print a human-readable coverage report."""
    print("=" * 70)
    print("FINDING-TO-SKILL COVERAGE AUDIT")
    print("=" * 70)

    print("\n## Finding Type Coverage\n")
    print(f"{'Finding Type':<12} {'Coverage':<10} {'Invoked?':<10} {'Detecting Skills'}")
    print("-" * 70)
    for ftype, info in sorted(results["finding_types"].items()):
        invoked = "YES" if info["invoked_by_tp_session"] else "NO"
        skills = ", ".join(info["detecting_skills"])
        print(f"{ftype:<12} {info['coverage']:<10} {invoked:<10} {skills}")

    print("\n## Underutilized Skills (exist but not invoked by /tp session)\n")
    for skill, desc in results["underutilized_skills"].items():
        print(f"  {skill:<15} {desc}")

    print("\n## Finding Gaps (no detection skill exists)\n")
    for gap_name, gap_info in results["finding_gaps"].items():
        exists = gap_info.get("skill_exists", False)
        status = "PARTIAL" if exists else "NO SKILL"
        print(f"  {gap_name:<35} [{status}]")
        print(f"    {gap_info['description']}")
        print(f"    Detection: {gap_info['proposed_detection']}")

    if results["registry_bugs"]:
        print("\n## Registry Bugs\n")
        for bug in results["registry_bugs"]:
            print(f"  {bug['capability']:<30} {bug['issue']}")

    # Summary
    total_types = len(results["finding_types"])
    covered = sum(1 for t in results["finding_types"].values() if t["coverage"] == "COVERED")
    partial = total_types - covered
    gaps = len(results["finding_gaps"])
    underutilized = len(results["underutilized_skills"])
    bugs = len(results["registry_bugs"])

    print("\n## Summary")
    print(f"  Finding types: {total_types} ({covered} covered, {partial} partial)")
    print(f"  Underutilized skills: {underutilized}")
    print(f"  Finding gaps (no skill): {gaps}")
    print(f"  Registry bugs: {bugs}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audit finding-to-skill coverage")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--gaps-only", action="store_true", help="Only show gaps")
    args = parser.parse_args()

    reg = CapabilityRegistry()
    results = audit_coverage(reg)

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.gaps_only:
        print("\n## Finding Gaps (no detection skill exists)\n")
        for gap_name, gap_info in results["finding_gaps"].items():
            exists = gap_info.get("skill_exists", False)
            status = "PARTIAL" if exists else "NO SKILL"
            print(f"  {gap_name:<35} [{status}]")
            print(f"    {gap_info['description']}")
    else:
        print_report(results)
