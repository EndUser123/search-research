#!/usr/bin/env python3
"""
Unified Hook Analysis Tool
==========================

Consolidates analysis across all hook logging systems.

Usage:
    python analyze_hooks.py                    # Summary of all systems
    python analyze_hooks.py --system blocks    # Just constructional blocks
    python analyze_hooks.py --system audit     # Just assumption audit
    python analyze_hooks.py --system all       # Detailed all systems
    python analyze_hooks.py --days 30          # Last 30 days (default: 7)
    python analyze_hooks.py --verbose          # Show recent entries
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from collections.abc import Iterator

LOGS_DIR = Path("P:/.claude/hooks/logs")


# Terminal-scoped log files for multi-terminal isolation
def get_log_files(base_pattern: str) -> list[Path]:
    """Get all terminal-scoped log files matching the base pattern."""
    pattern = base_pattern.replace(".jsonl", "_*.jsonl")
    return sorted(LOGS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


# Log file registry - add new logs here
LOG_REGISTRY = {
    "blocks": {
        "pattern": "constructional_blocks.jsonl",
        "description": "General hook violations/blocks",
        "event_field": None,  # No event field, each line is a violation
        "count_field": "hook",  # Field to group by
    },
    "enforcement": {
        "pattern": "block_enforcement.jsonl",
        "description": "Hard blocks (exit 2)",
        "event_field": None,
        "count_field": "hook",
    },
    "audit": {
        "pattern": "test_assumption_audit.jsonl",
        "description": "Assumption audit triggers & compliance",
        "event_field": "event",
        "count_field": "event",
    },
    "absence": {
        "pattern": "absence_claim_gate.jsonl",
        "description": "Absence claim detections",
        "event_field": "event",
        "count_field": "event",
    },
    "subagent": {
        "pattern": "subagent_enforcer.jsonl",
        "description": "Subagent enforcement",
        "event_field": "event",
        "count_field": "event",
    },
}


def load_jsonl(path_pattern: str, days: int, terminal_filter: str = None) -> Iterator[dict]:
    """Load JSONL entries from last N days, optionally filtered by terminal."""
    log_files = get_log_files(path_pattern)

    cutoff = datetime.now() - timedelta(days=days)

    for log_path in log_files:
        try:
            with open(log_path) as f:
                for line in f:
                    try:
                        entry = json.loads(line)

                        # Terminal filter
                        if terminal_filter and entry.get("terminal_id") != terminal_filter:
                            continue

                        ts_str = entry.get("timestamp", "")
                        if ts_str:
                            # Handle various timestamp formats
                            ts_str = ts_str.replace("Z", "+00:00")
                            try:
                                ts = datetime.fromisoformat(ts_str)
                                if ts.replace(tzinfo=None) < cutoff:
                                    continue
                            except ValueError:
                                pass  # Include if can't parse timestamp
                        yield entry
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue  # Skip files that can't be read


def analyze_system(
    name: str, config: dict, days: int, verbose: bool, terminal_filter: str = None
) -> dict:
    """Analyze a single logging system."""
    pattern = config.get("pattern", config.get("file", ""))
    entries = list(load_jsonl(pattern, days, terminal_filter))

    if not entries:
        # Check if any matching files exist
        log_files = get_log_files(pattern)
        return {"count": 0, "file_exists": len(log_files) > 0}

    # Count by field
    counts = defaultdict(int)
    count_field = config["count_field"]
    for entry in entries:
        key = entry.get(count_field, "unknown")
        counts[key] += 1

    # Severity breakdown (if present)
    severity_counts = defaultdict(int)
    for entry in entries:
        sev = entry.get("severity", "unknown")
        severity_counts[sev] += 1

    # Special handling for audit compliance
    compliance = None
    if name == "audit":
        compliance_checks = [e for e in entries if e.get("event") == "compliance_check"]
        if compliance_checks:
            complied = sum(1 for c in compliance_checks if c.get("complied"))
            compliance = {
                "total_checks": len(compliance_checks),
                "complied": complied,
                "ignored": len(compliance_checks) - complied,
                "rate": (complied / len(compliance_checks)) * 100,
            }

    result = {
        "count": len(entries),
        "file_exists": True,
        "by_field": dict(counts),
        "by_severity": dict(severity_counts) if len(severity_counts) > 1 else None,
        "recent": entries[-5:] if verbose else None,
    }

    if compliance:
        result["compliance"] = compliance

    return result


def print_summary(results: dict, days: int):
    """Print summary across all systems."""
    print(f"\n{'=' * 60}")
    print(f"  HOOK ANALYSIS SUMMARY (last {days} days)")
    print(f"{'=' * 60}\n")

    total_events = 0
    for name, data in results.items():
        config = LOG_REGISTRY[name]
        status = "✓" if data["file_exists"] else "✗"
        count = data["count"]
        total_events += count

        print(f"{status} {name.upper():12} | {count:6} entries | {config['description']}")

        # Show top counts
        if data.get("by_field") and count > 0:
            top_items = sorted(data["by_field"].items(), key=lambda x: -x[1])[:3]
            for field, cnt in top_items:
                pct = (cnt / count) * 100
                print(f"  └─ {field}: {cnt} ({pct:.0f}%)")

        # Show severity breakdown if present
        if data.get("by_severity"):
            sev_str = ", ".join(f"{k}:{v}" for k, v in sorted(data["by_severity"].items()))
            print(f"  └─ severity: {sev_str}")

        # Show compliance for audit
        if data.get("compliance"):
            c = data["compliance"]
            print(f"  └─ COMPLIANCE: {c['rate']:.1f}% ({c['complied']}/{c['total_checks']})")

    print(f"\n{'─' * 60}")
    print(f"  Total events: {total_events}")
    print()


def print_detailed(name: str, data: dict, config: dict, days: int):
    """Print detailed analysis for one system."""
    print(f"\n{'=' * 60}")
    print(f"  {name.upper()}: {config['description']}")

    # Show file(s) - use pattern if available, otherwise use file
    if "pattern" in config:
        pattern = config["pattern"]
        log_files = get_log_files(pattern)
        print(f"  Files: {[str(f.name) for f in log_files]}")
    else:
        print(f"  File: {config['file']}")

    print(f"  Period: last {days} days")
    print(f"{'=' * 60}\n")

    # Check for matching files
    if "pattern" in config:
        log_files = get_log_files(config["pattern"])
        if not log_files:
            print("  [No matching log files found]\n")
            return
    elif not data.get("file_exists", False):
        print("  [File not found]\n")
        return

    if data["count"] == 0:
        print("  [No entries in period]\n")
        return

    print(f"Total entries: {data['count']}\n")

    # Breakdown
    if data.get("by_field"):
        print("Breakdown:")
        for field, cnt in sorted(data["by_field"].items(), key=lambda x: -x[1]):
            pct = (cnt / data["count"]) * 100
            bar = "█" * int(pct / 5)
            print(f"  {field:30} {cnt:5} ({pct:5.1f}%) {bar}")

    # Compliance
    if data.get("compliance"):
        c = data["compliance"]
        print("\nCompliance Tracking:")
        print(f"  Checks performed: {c['total_checks']}")
        print(f"  LLM complied:     {c['complied']} ({c['rate']:.1f}%)")
        print(f"  LLM ignored:      {c['ignored']}")

    # Recent entries
    if data.get("recent"):
        print("\nRecent entries:")
        for entry in data["recent"]:
            ts = entry.get("timestamp", "?")[:19]
            # Show relevant fields based on system
            if name == "audit":
                event = entry.get("event", "?")
                snippet = entry.get("response_snippet", entry.get("pending_snippet", ""))[:50]
                print(f"  {ts} | {event:20} | {snippet}...")
            elif name == "blocks":
                hook = entry.get("hook_name", "?")
                reason = entry.get("reason", "")[:40]
                print(f"  {ts} | {hook:25} | {reason}...")
            else:
                print(f"  {ts} | {json.dumps(entry)[:60]}...")

    print()


def main():
    days = 7
    system = "summary"
    verbose = False

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--system" and i + 1 < len(args):
            system = args[i + 1]
            i += 2
        elif args[i] == "--verbose":
            verbose = True
            i += 1
        else:
            i += 1

    # Analyze
    results = {}
    for name, config in LOG_REGISTRY.items():
        results[name] = analyze_system(name, config, days, verbose)

    # Output
    if system == "summary":
        print_summary(results, days)
    elif system == "all":
        for name, config in LOG_REGISTRY.items():
            print_detailed(name, results[name], config, days)
    elif system in LOG_REGISTRY:
        print_detailed(system, results[system], LOG_REGISTRY[system], days)
    else:
        print(f"Unknown system: {system}")
        print(f"Available: {', '.join(LOG_REGISTRY.keys())}, summary, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
