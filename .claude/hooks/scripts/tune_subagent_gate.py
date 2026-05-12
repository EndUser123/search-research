#!/usr/bin/env python3
"""tune_subagent_gate.py - Analyze delegation telemetry and recommend threshold tuning."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
_LOG_DIR = HOOKS_DIR / "logs" / "diagnostics"
_HISTORY_DIR = Path.home() / ".claude"
DEFAULT_DAYS = 7
DEFAULT_THRESHOLD = 3

def load_telemetry(log_file, days=DEFAULT_DAYS):
    if not log_file.exists():
        return []
    events = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = entry.get("ts", "")
                    if ts >= cutoff_str:
                        events.append(entry)
                except json.JSONDecodeError:
                    continue
    except (IOError, OSError):
        return []
    return events

def analyze_prospector(events):
    stats = {"total_prompts": 0, "opportunities_detected": 0, "by_pattern": Counter()}
    for event in events:
        stats["total_prompts"] += 1
        if event.get("event") == "delegation_opportunity_detected":
            stats["opportunities_detected"] += 1
            pattern = event.get("matched_pattern", "unknown")
            stats["by_pattern"][pattern] += 1
    return stats

def analyze_opportunity(events):
    stats = {"total_turns": 0, "below_threshold": 0, "opportunities_detected": 0, "agent_used": 0}
    for event in events:
        stats["total_turns"] += 1
        event_type = event.get("event", "")
        if event_type == "below_threshold":
            stats["below_threshold"] += 1
        elif event_type == "opportunity_detected":
            stats["opportunities_detected"] += 1
        elif event_type == "agent_used":
            stats["agent_used"] += 1
    return stats

def get_agent_usage(days=DEFAULT_DAYS):
    history_file = _HISTORY_DIR / "history.jsonl"
    if not history_file.exists():
        return {"total": 0, "agent_uses": 0}
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    total_prompts = 0
    agent_uses = 0
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", "")
                    if ts:
                        try:
                            event_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if event_time < cutoff:
                                continue
                        except ValueError:
                            continue
                    total_prompts += 1
                    prompt = entry.get("prompt", "") or entry.get("text", "")
                    if "Agent(" in prompt or '"subagent_type"' in prompt:
                        agent_uses += 1
                except json.JSONDecodeError:
                    continue
    except (IOError, OSError):
        pass
    return {"total": total_prompts, "agent_uses": agent_uses}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    prospector_log = _LOG_DIR / "delegation_prospector.jsonl"
    opportunity_log = _LOG_DIR / "subagent_opportunity.jsonl"
    prospector_events = load_telemetry(prospector_log, args.days)
    opportunity_events = load_telemetry(opportunity_log, args.days)
    prospector_stats = analyze_prospector(prospector_events)
    opportunity_stats = analyze_opportunity(opportunity_events)
    agent_stats = get_agent_usage(args.days)
    print("=" * 60)
    print("SUBAGENT DELEGATION ANALYSIS")
    print("=" * 60)
    print()
    print(f"PROSPECTOR: {prospector_stats['total_prompts']} prompts, {prospector_stats['opportunities_detected']} opportunities")
    print(f"OPPORTUNITY: {opportunity_stats['total_turns']} turns, {opportunity_stats['opportunities_detected']} surfaced, {opportunity_stats['agent_used']} Agent used")
    print(f"HISTORY: {agent_stats['total']} prompts, {agent_stats['agent_uses']} Agent uses")
    print()
    if prospector_stats['opportunities_detected'] > 0:
        rate = prospector_stats['opportunities_detected'] / prospector_stats['total_prompts'] * 100
        print(f"Detection rate: {rate:.1f}%")
    if opportunity_stats['opportunities_detected'] > 0:
        rate = opportunity_stats['agent_used'] / opportunity_stats['opportunities_detected'] * 100
        print(f"Delegation rate: {rate:.1f}%")
    print()
    print(f"Current threshold: {DEFAULT_THRESHOLD}")
    print("To tune: Edit _OPPORTUNITY_THRESHOLD in Stop_subagent_opportunity.py")

if __name__ == "__main__":
    main()
