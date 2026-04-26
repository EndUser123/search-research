#!/usr/bin/env python3
"""Analyze post-skill prose detection metrics from logs.

Queries skill_first_enforcement.jsonl for post-skill events and generates
a metrics report showing detection rate, block/allow ratio, and skill patterns.
"""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def parse_log_file(log_path: Path) -> list[dict]:
    """Parse JSONL log file and return list of entries.

    Args:
        log_path: Path to skill_first_enforcement.jsonl

    Returns:
        List of log entries (dicts)
    """
    entries = []
    try:
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")
        print("No post-skill prose events recorded yet.")
        return []

    return entries


def filter_post_skill_events(entries: list[dict]) -> list[dict]:
    """Filter entries to only post_skill_prose_response events.

    Args:
        entries: All log entries

    Returns:
        Filtered list of post-skill events
    """
    return [
        e for e in entries
        if e.get("event") == "post_skill_prose_response"
        and "skill_name" in e
    ]


def filter_by_time_window(entries: list[dict], since_hours: float | None) -> list[dict]:
    """Filter entries by time window.

    Args:
        entries: Log entries
        since_hours: Only include entries from last N hours (None = all time)

    Returns:
        Filtered entries
    """
    if since_hours is None:
        return entries

    cutoff_time = datetime.now().timestamp() - (since_hours * 3600)
    return [e for e in entries if e.get("timestamp", 0) >= cutoff_time]


def calculate_metrics(events: list[dict]) -> dict:
    """Calculate metrics from post-skill events.

    Args:
        events: Post-skill prose events

    Returns:
        Metrics dictionary with statistics
    """
    if not events:
        return {
            "total_events": 0,
            "block_count": 0,
            "allow_count": 0,
            "block_rate": 0.0,
            "allow_rate": 0.0,
        }

    block_count = sum(1 for e in events if e.get("decision") == "block")
    allow_count = sum(1 for e in events if e.get("decision") == "allow")
    total = len(events)

    # Count by skill type
    skill_types = Counter(e.get("skill_type", "unknown") for e in events)

    # Count by skill name
    skill_names = Counter(e.get("skill_name", "unknown") for e in events)

    # Count by reason
    reasons = Counter(e.get("reason", "unknown") for e in events)

    # Execution tools used
    execution_tools_used = Counter()
    for e in events:
        for tool in e.get("execution_tools_used", []):
            execution_tools_used[tool] += 1

    return {
        "total_events": total,
        "block_count": block_count,
        "allow_count": allow_count,
        "block_rate": block_count / total if total > 0 else 0.0,
        "allow_rate": allow_count / total if total > 0 else 0.0,
        "skill_types": dict(skill_types),
        "skill_names": dict(skill_names.most_common(10)),
        "reasons": dict(reasons),
        "execution_tools_used": dict(execution_tools_used),
    }


def format_report(metrics: dict, time_filter: str = "all time") -> str:
    """Format metrics as human-readable report.

    Args:
        metrics: Metrics dictionary
        time_filter: Description of time window

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 60,
        "Post-Skill Prose Detection Metrics",
        f"Time window: {time_filter}",
        "=" * 60,
        "",
        f"Total events: {metrics['total_events']}",
        f"  Blocks: {metrics['block_count']} ({metrics['block_rate']:.1%})",
        f"  Allows: {metrics['allow_count']} ({metrics['allow_rate']:.1%})",
        "",
        "Skill Types:",
    ]

    for skill_type, count in metrics.get("skill_types", {}).items():
        pct = count / metrics["total_events"] * 100 if metrics["total_events"] > 0 else 0
        lines.append(f"  {skill_type}: {count} ({pct:.1f}%)")

    if metrics.get("skill_names"):
        lines.extend([
            "",
            "Top Skills:",
        ])
        for skill_name, count in metrics["skill_names"].items():
            pct = count / metrics["total_events"] * 100 if metrics["total_events"] > 0 else 0
            lines.append(f"  /{skill_name}: {count} ({pct:.1f}%)")

    if metrics.get("reasons"):
        lines.extend([
            "",
            "Decision Reasons:",
        ])
        for reason, count in metrics["reasons"].items():
            pct = count / metrics["total_events"] * 100 if metrics["total_events"] > 0 else 0
            lines.append(f"  {reason}: {count} ({pct:.1f}%)")

    if metrics.get("execution_tools_used"):
        lines.extend([
            "",
            "Execution Tools Used:",
        ])
        for tool, count in metrics["execution_tools_used"].items():
            lines.append(f"  {tool}: {count}")

    lines.extend([
        "",
        "=" * 60,
    ])

    return "\n".join(lines)


def main():
    """Main entry point for metrics analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze post-skill prose detection metrics"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to skill_first_enforcement.jsonl (default: P:/.claude/hooks/skill_first_enforcement.jsonl)",
    )
    parser.add_argument(
        "--since",
        type=float,
        dest="since_hours",
        default=None,
        help="Only show events from last N hours (default: all time)",
    )
    parser.add_argument(
        "--last-n-events",
        type=int,
        dest="last_n",
        default=None,
        help="Only show last N events (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output metrics as JSON instead of human-readable report",
    )

    args = parser.parse_args()

    # Determine log file path
    if args.log_file:
        log_path = Path(args.log_file)
    else:
        log_path = Path(__file__).resolve().parent.parent / "skill_first_enforcement.jsonl"

    # Parse and filter logs
    all_entries = parse_log_file(log_path)
    post_skill_events = filter_post_skill_events(all_entries)

    # Apply time window filter
    if args.since_hours:
        post_skill_events = filter_by_time_window(post_skill_events, args.since_hours)
        time_filter = f"last {args.since_hours} hours"
    else:
        time_filter = "all time"

    # Apply last-n-events filter
    if args.last_n:
        post_skill_events = post_skill_events[-args.last_n :]
        time_filter = f"last {args.last_n} events"

    # Calculate metrics
    metrics = calculate_metrics(post_skill_events)

    # Output
    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print(format_report(metrics, time_filter))


if __name__ == "__main__":
    main()
