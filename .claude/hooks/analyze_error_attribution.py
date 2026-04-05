#!/usr/bin/env python3
"""
Analyze error attribution injection frequency and patterns.

Usage:
    python analyze_error_attribution.py [--days N]

Note: This tracks INJECTION events. Compliance checking (whether LLM 
actually referenced the source) requires manual transcript review or
implementation of Phase 2 Stop gate enforcement.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path("P:/.claude/logs/error_attribution.jsonl")

# Threshold for recommending Phase 2 escalation
# Based on manual review of transcripts
ESCALATION_THRESHOLD = 0.30


def analyze(days: int = 7):
    if not LOG_FILE.exists():
        print("No error attribution log found.")
        print(f"Expected location: {LOG_FILE}")
        return

    cutoff = datetime.now() - timedelta(days=days)

    entries = []
    by_source = defaultdict(int)
    by_source_type = defaultdict(int)
    by_tool = defaultdict(int)

    with open(LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromtimestamp(entry.get("timestamp", 0))
                if ts < cutoff:
                    continue

                entries.append(entry)
                by_source[entry.get("source", "unknown")] += 1
                by_source_type[entry.get("source_type", "unknown")] += 1
                by_tool[entry.get("tool_name", "unknown")] += 1
            except (json.JSONDecodeError, KeyError):
                continue

    print(f"=== Error Attribution Report (last {days} days) ===\n")
    print(f"Total error attributions injected: {len(entries)}")

    if not entries:
        print("\nNo error attributions logged in this period.")
        return

    # By source type
    print("\nBy Source Type:")
    for source_type, count in sorted(by_source_type.items(), key=lambda x: -x[1]):
        print(f"  {source_type}: {count}")

    # By tool that triggered error
    print("\nBy Tool:")
    for tool, count in sorted(by_tool.items(), key=lambda x: -x[1]):
        print(f"  {tool}: {count}")

    # Top error sources
    print("\nTop Error Sources:")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1])[:10]:
        print(f"  {source}: {count}")

    # Recent entries
    print("\n--- Recent Error Attributions ---")
    for entry in entries[-5:]:
        ts = datetime.fromtimestamp(entry.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")
        source = entry.get("source", "?")
        tool = entry.get("tool_name", "?")
        print(f"  [{ts}] {tool} -> {source}")

    # Escalation guidance
    print("\n=== Escalation Status ===")
    print("Phase 1 (Advisory Injection): ACTIVE")
    print("Phase 2 (Stop Gate):          NOT IMPLEMENTED")
    print("\nTo evaluate escalation need:")
    print("  1. Review recent transcripts manually")
    print("  2. Check if LLM responses reference injected sources")
    print("  3. If >30% ignore source, implement error_attribution_gate.py")
    print("\nManual review command:")
    print("  # Check last 5 transcripts for source mentions")
    print("  grep -l 'skill_enforcement\\|tdd_gate' P:/.claude/logs/transcripts/*.json")


if __name__ == "__main__":
    days = 7
    if len(sys.argv) > 2 and sys.argv[1] == "--days":
        days = int(sys.argv[2])
    analyze(days)
