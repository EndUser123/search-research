#!/usr/bin/env python3
"""
Analyze Debug Payload Logs

Quick script to summarize captured payload structures.
"""

import json
from collections import Counter
from pathlib import Path

LOG_DIR = Path("P:/.claude/state/logs/debug_payloads")


def analyze_jsonl(file_path: Path) -> dict:
    """Analyze a JSONL log file."""
    if not file_path.exists():
        return {"error": "File not found"}

    entries = []
    try:
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(json.loads(line))
    except Exception as e:
        return {"error": str(e)}

    if not entries:
        return {"error": "No entries"}

    # Analyze structure
    all_keys = Counter()
    session_ids = set()

    for entry in entries:
        if "top_level_keys" in entry:
            all_keys.update(entry["top_level_keys"])
        if "session_id" in entry:
            session_ids.add(entry["session_id"])

    # Get a sample entry
    sample = entries[0] if entries else {}

    return {
        "total_entries": len(entries),
        "unique_sessions": len(session_ids),
        "common_keys": dict(all_keys.most_common(20)),
        "sample_entry": sample,
    }


def main():
    """Main entry point."""
    print("=" * 80)
    print("DEBUG PAYLOAD ANALYSIS")
    print("=" * 80)
    print()

    # Analyze Stop payloads
    print("🔍 STOP HOOK PAYLOADS")
    print("-" * 80)
    stop_summary = analyze_jsonl(LOG_DIR / "Stop_payloads.jsonl")
    if "error" in stop_summary:
        print(f"❌ Error: {stop_summary['error']}")
        print("   (Run 5-10 responses first to generate data)")
    else:
        print(f"✅ Total captures: {stop_summary['total_entries']}")
        print(f"✅ Unique sessions: {stop_summary['unique_sessions']}")
        print("✅ Common keys:")
        for key, count in stop_summary['common_keys'].items():
            print(f"   - {key}: {count} times")

    print()

    # Analyze PreToolUse payloads
    print("🔍 PRETOOLUSE HOOK PAYLOADS")
    print("-" * 80)
    pretoul_summary = analyze_jsonl(LOG_DIR / "PreToolUse_payloads.jsonl")
    if "error" in pretoul_summary:
        print(f"❌ Error: {pretoul_summary['error']}")
        print("   (Run 5-10 tool calls first to generate data)")
    else:
        print(f"✅ Total captures: {pretoul_summary['total_entries']}")
        print(f"✅ Unique sessions: {pretoul_summary['unique_sessions']}")
        print("✅ Common keys:")
        for key, count in pretoul_summary['common_keys'].items():
            print(f"   - {key}: {count} times")

    print()
    print("=" * 80)
    print("📁 FULL PAYLOAD FILES")
    print("=" * 80)
    print(f"Stop full payloads:     {LOG_DIR / 'Stop_full.jsonl'}")
    print(f"PreToolUse full payloads: {LOG_DIR / 'PreToolUse_full.jsonl'}")
    print()
    print("View with:")
    print(f"  cat {LOG_DIR / 'Stop_full.jsonl'} | jq -s '.[0]'")
    print(f"  cat {LOG_DIR / 'PreToolUse_full.jsonl'} | jq -s '.[0]'")
    print()


if __name__ == "__main__":
    main()
