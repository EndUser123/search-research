#!/usr/bin/env python3
"""
Analyze Assumption Audit Logs
==============================

Understand what's being blocked and why.

Key metrics:
- Block rate: % of responses blocked
- False positive rate: Blocks on general knowledge
- Pattern coverage: Which exemptions are used most
- Tool usage: Which tools prevent blocks

Usage:
  python analyze_assumption_audit.py [hours] [--terminal]
  
Options:
  hours       Hours to analyze (default: 24)
  --terminal  Filter to current terminal only (default: all terminals)
  --all       Show all terminals separately
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path("P:/.claude/hooks/logs/assumption_audit_v2.jsonl")

# Add hooks directory for imports
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))


def get_current_terminal_id() -> str:
    """Get current terminal ID for filtering."""
    try:
        from __lib.terminal_detection import detect_terminal_id
        return detect_terminal_id()
    except ImportError:
        return None


def matches_terminal(event_tid: str, target_tid: str) -> bool:
    """
    Check if event's terminal_id matches target terminal.
    
    Handles both old (raw) and new (normalized) formats.
    """
    if event_tid == target_tid:
        return True

    # Extract raw ID from normalized format for comparison
    def extract_raw(tid: str) -> str:
        if "_" in tid:
            parts = tid.split("_", 1)
            if len(parts) == 2 and parts[0] in ("env", "tempfile", "console", "fallback"):
                return parts[1]
        return tid

    return extract_raw(event_tid) == extract_raw(target_tid)


def analyze_logs(hours: int = 24, terminal_filter: str = None, show_all_terminals: bool = False):
    """Analyze recent audit decisions."""

    if not LOG_FILE.exists():
        print("No logs found yet")
        return

    cutoff = datetime.now() - timedelta(hours=hours)

    events = []
    for line in LOG_FILE.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            event = json.loads(line)
            timestamp = datetime.fromisoformat(event["timestamp"])
            if timestamp >= cutoff:
                # Apply terminal filter if specified
                if terminal_filter:
                    event_tid = event.get("terminal_id", "unknown")
                    if not matches_terminal(event_tid, terminal_filter):
                        continue
                events.append(event)
        except Exception:
            continue

    if not events:
        filter_msg = f" for terminal {terminal_filter[:20]}..." if terminal_filter else ""
        print(f"No events in last {hours} hours{filter_msg}")
        return

    # Show per-terminal breakdown if requested
    if show_all_terminals:
        terminals = defaultdict(list)
        for e in events:
            tid = e.get("terminal_id", "unknown")
            # Normalize for grouping
            raw = tid.split("_", 1)[-1] if "_" in tid else tid
            terminals[raw[:16]].append(e)

        print(f"\n=== Assumption Audit by Terminal (last {hours}h) ===\n")
        for tid, tevents in sorted(terminals.items(), key=lambda x: -len(x[1])):
            triggers = sum(1 for e in tevents if e["event"] == "trigger")
            safe = sum(1 for e in tevents if e["event"] == "safe_response")
            checks = sum(1 for e in tevents if e["event"] == "check")
            total = triggers + safe
            rate = (triggers / total * 100) if total > 0 else 0
            print(f"  {tid}...: {triggers} blocks, {safe} safe, {checks} checks ({rate:.0f}% block rate)")
        print()
        return

    # Count event types (v2 format: "block", "allow")
    event_types = Counter(e["event"] for e in events)

    filter_label = f" (terminal: {terminal_filter[:16]}...)" if terminal_filter else " (all terminals)"
    print(f"\n=== Assumption Audit Analysis (last {hours}h){filter_label} ===\n")
    print(f"Total events: {len(events)}\n")

    # Block rate (v2: block vs allow)
    blocks = event_types.get("block", 0)
    allows = event_types.get("allow", 0)
    total_responses = blocks + allows

    if total_responses > 0:
        block_rate = (blocks / total_responses) * 100
        print(f"Block rate: {blocks}/{total_responses} ({block_rate:.1f}%)")
        print(f"Allowed responses: {allows} ({(allows/total_responses)*100:.1f}%)")
        print()

    # Tools used in allowed responses (prevented blocks)
    tools_used = []
    for e in events:
        if e["event"] == "allow" and e.get("tools_used"):
            tools_used.extend(e.get("tools_used", []))

    if tools_used:
        print("Tools in allowed responses:")
        for tool, count in Counter(tools_used).most_common(5):
            print(f"  {tool}: {count}x")
        print()

    # Sample blocked responses
    blocked = [e for e in events if e["event"] == "block"]
    if blocked:
        print(f"Sample blocked responses ({len(blocked)} total):")
        for e in blocked[:3]:
            snippet = e.get("response_snippet", "")
            if snippet:
                print(f"  - {snippet[:80]}...")
        print()

    # V2 removed: oscillation, compliance tracking (simpler model)
    # V2 removed: safe response patterns (use "allow" events instead)


if __name__ == "__main__":
    hours = 24
    terminal_filter = None
    show_all = False

    for arg in sys.argv[1:]:
        if arg == "--terminal":
            terminal_filter = get_current_terminal_id()
            if not terminal_filter:
                print("Warning: Could not detect terminal ID, showing all")
        elif arg == "--all":
            show_all = True
        elif arg.isdigit():
            hours = int(arg)

    analyze_logs(hours, terminal_filter, show_all)
