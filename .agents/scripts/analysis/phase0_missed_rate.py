#!/usr/bin/env python3
"""
Phase 0 analysis script: compute the missed-observation rate.

Joins the tool log (observation-tool-log/*.jsonl) with the text log
(observation-text-log/*.jsonl) by session_id+turn, then counts turns where:
  - lastAssistantMessage contains ZERO observation lines (no Note:/Maybe:/INFO:)
  - AND ≥2 distinct observation-producing tools fired in the joined window

Output: a single summary with the missed-observation rate per session and overall.

Usage:
    python phase0_missed_rate.py                    # summary report
    python phase0_missed_rate.py --per-session      # per-session breakdown
    python phase0_missed_rate.py --json             # JSON output for scripting

This is the gate to Phase 1: if the missed-observation rate is < 0.5/session,
the judge hook is not worth building (design doc §12.1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STATE_DIR = Path.home() / ".grok" / "state"
TOOL_LOG_DIR = STATE_DIR / "observation-tool-log"
TEXT_LOG_DIR = STATE_DIR / "observation-text-log"

# Observation-producing tools (must match PostToolUse_tool_log.py)
OBSERVATION_TOOLS = {
    "read_file", "Read",
    "grep", "Grep",
    "list_dir", "ListDir", "Glob",
    "web_search", "WebSearch",
    "web_fetch", "WebFetch",
}

# Observation line patterns (Note:/Maybe:/INFO:)
SURFACE_LINE_RE = re.compile(
    r"(?:^|\n)"          # line start
    r"(?:Note:|Maybe:|INFO:)"  # the three observation prefixes
    r"\s+",              # whitespace after prefix
    re.MULTILINE
)

# Phase 0 → Phase 1 threshold (design doc §12.1, §12.4 — adjustable)
THRESHOLD_MISSED_PER_SESSION = 0.5


# ---------------------------------------------------------------------------
# Load logs
# ---------------------------------------------------------------------------

def load_tool_logs() -> dict[str, list[dict]]:
    """Load all tool-log JSONL files. Returns {safe_session_id: [entries]}."""
    sessions: dict[str, list[dict]] = defaultdict(list)
    if not TOOL_LOG_DIR.exists():
        return sessions
    for log_file in sorted(TOOL_LOG_DIR.glob("*.jsonl")):
        for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                sessions[entry["session_id"]].append(entry)
            except (json.JSONDecodeError, KeyError):
                continue
    return sessions


def load_text_logs() -> dict[str, list[dict]]:
    """Load all text-log JSONL files. Returns {session_id: [entries]}."""
    sessions: dict[str, list[dict]] = defaultdict(list)
    if not TEXT_LOG_DIR.exists():
        return sessions
    for log_file in sorted(TEXT_LOG_DIR.glob("*.jsonl")):
        for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                sessions[entry["session_id"]].append(entry)
            except (json.JSONDecodeError, KeyError):
                continue
    return sessions


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def has_observation_line(text: str) -> bool:
    """Check if the agent's output contains a Note:/Maybe:/INFO: line."""
    return bool(SURFACE_LINE_RE.search(text))


def count_distinct_obs_tools(entries: list[dict]) -> int:
    """Count distinct observation-producing tools in the tool log entries."""
    tools = {e["tool"] for e in entries if e.get("is_observation_tool")}
    return len(tools)


def analyze_session(session_id: str, tool_entries: list[dict], text_entries: list[dict]) -> dict:
    """Analyze a single session and return metrics.

    For each text entry (turn), check if:
    - The text has zero observation lines
    - ≥2 distinct observation-producing tools were used in nearby tool calls

    Since we don't have exact turn-to-tool-call mapping in Phase 0, we approximate:
    if the session has ≥2 distinct observation tools overall AND a specific turn's
    text has no observation line, that turn counts as a "missed observation opportunity."
    """
    # Group text entries by turn (they're already in order)
    total_turns = len(text_entries)

    if total_turns == 0:
        return {
            "session_id": session_id,
            "total_turns": 0,
            "missed_opportunities": 0,
            "missed_rate": 0.0,
            "distinct_obs_tools": 0,
        }

    # Count distinct observation tools in the whole session
    distinct_obs = count_distinct_obs_tools(tool_entries)

    # For each turn, check if text has an observation line
    turns_without_obs = 0
    for te in text_entries:
        text = te.get("text", "")
        if not has_observation_line(text):
            turns_without_obs += 1

    # Missed opportunities = turns without observation lines (when ≥2 obs tools used)
    # Only count as "missed" if the session used ≥2 distinct observation tools
    missed = turns_without_obs if distinct_obs >= 2 else 0

    return {
        "session_id": session_id[:16] + "..." if len(session_id) > 16 else session_id,
        "total_turns": total_turns,
        "missed_opportunities": missed,
        "missed_rate": missed / total_turns if total_turns > 0 else 0.0,
        "distinct_obs_tools": distinct_obs,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0 missed-observation rate analyzer")
    parser.add_argument("--per-session", action="store_true", help="Show per-session breakdown")
    parser.add_argument("--json", action="store_true", help="JSON output for scripting")
    args = parser.parse_args()

    tool_logs = load_tool_logs()
    text_logs = load_text_logs()

    all_sessions = set(tool_logs.keys()) | set(text_logs.keys())

    if not all_sessions:
        msg = "No Phase 0 data found. Run with the hooks active for at least 7 days."
        if args.json:
            print(json.dumps({"error": msg, "sessions": 0}))
        else:
            print(msg)
        sys.exit(0)

    results = []
    for session_id in sorted(all_sessions):
        results.append(analyze_session(
            session_id,
            tool_logs.get(session_id, []),
            text_logs.get(session_id, []),
        ))

    total_sessions = len(results)
    total_missed = sum(r["missed_opportunities"] for r in results)
    avg_missed_per_session = total_missed / total_sessions if total_sessions > 0 else 0.0
    total_turns = sum(r["total_turns"] for r in results)

    # Gate decision
    gate_passed = avg_missed_per_session >= THRESHOLD_MISSED_PER_SESSION

    if args.json:
        print(json.dumps({
            "sessions": total_sessions,
            "total_turns": total_turns,
            "total_missed_opportunities": total_missed,
            "avg_missed_per_session": round(avg_missed_per_session, 2),
            "threshold": THRESHOLD_MISSED_PER_SESSION,
            "gate_passed": gate_passed,
            "per_session": results if args.per_session else None,
        }, indent=2))
    else:
        print("=" * 60)
        print("Phase 0 Missed-Observation Rate Report")
        print("=" * 60)
        print(f"Sessions analyzed:     {total_sessions}")
        print(f"Total turns:           {total_turns}")
        print(f"Total missed opps:     {total_missed}")
        print(f"Avg missed/session:    {avg_missed_per_session:.2f}")
        print(f"Threshold (§12.1):     {THRESHOLD_MISSED_PER_SESSION}")
        print(f"Gate decision:         {'PROCEED to Phase 1' if gate_passed else 'RETIRE — rate too low'}")
        print()

        if args.per_session:
            print("-" * 60)
            print(f"{'Session':<20} {'Turns':>6} {'Missed':>7} {'Rate':>6} {'ObsTools':>9}")
            print("-" * 60)
            for r in results:
                print(f"{r['session_id']:<20} {r['total_turns']:>6} {r['missed_opportunities']:>7} "
                      f"{r['missed_rate']:>5.1%} {r['distinct_obs_tools']:>9}")

        print()
        print("Gate: if avg missed/session ≥ 0.5, proceed to Phase 1 (build judge).")
        print("      if < 0.5, the missed-observation rate doesn't justify the judge.")


if __name__ == "__main__":
    main()
