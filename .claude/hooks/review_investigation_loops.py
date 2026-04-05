#!/usr/bin/env python3
"""
Investigation Loop Evidence Review Script

Review investigation loop warnings after advisory period to determine
if blocking is warranted.

Usage:
    python review_investigation_loops.py [--days 7]
"""

import argparse
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


def analyze_warnings(log_file: Path, days: int = 7):
    """Analyze investigation loop warnings from log file."""

    if not log_file.exists():
        return {
            "status": "no_data",
            "message": f"No warnings log found at {log_file}",
            "recommendation": "Continue advisory mode. No evidence yet."
        }

    cutoff_date = datetime.now() - timedelta(days=days)
    warnings = []
    sessions = set()
    tools = Counter()
    consecutive_counts = []

    try:
        with open(log_file) as f:
            for line in f:
                try:
                    # Parse log format: timestamp | Session: {session_id} | Tool: {tool} | Consecutive count: {count} | Command: {command}
                    parts = line.split(' | ')
                    if len(parts) < 5:
                        continue

                    timestamp_str = parts[0].strip()
                    timestamp = datetime.fromisoformat(timestamp_str)

                    # Filter by date range
                    if timestamp < cutoff_date:
                        continue

                    warnings.append({
                        'timestamp': timestamp_str,
                        'raw': line.strip()
                    })

                    # Extract session ID
                    session_part = [p for p in parts if p.startswith('Session:')]
                    if session_part:
                        session_id = session_part[0].split(':')[1].strip()
                        sessions.add(session_id)

                    # Extract tool
                    tool_part = [p for p in parts if p.startswith('Tool:')]
                    if tool_part:
                        tool = tool_part[0].split(':')[1].strip()
                        tools[tool] += 1

                    # Extract consecutive count
                    count_part = [p for p in parts if p.startswith('Consecutive count:')]
                    if count_part:
                        count = int(count_part[0].split(':')[1].strip())
                        consecutive_counts.append(count)

                except (ValueError, IndexError):
                    continue

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading log file: {e}",
            "recommendation": "Check log file format and permissions."
        }

    # Analysis
    if not warnings:
        return {
            "status": "no_warnings",
            "period": f"Last {days} days",
            "total_warnings": 0,
            "recommendation": "No investigation loop warnings. Consider disabling the feature entirely."
        }

    # Calculate statistics
    avg_consecutive = sum(consecutive_counts) / len(consecutive_counts) if consecutive_counts else 0
    max_consecutive = max(consecutive_counts) if consecutive_counts else 0

    # Generate recommendation
    total_warnings = len(warnings)
    unique_sessions = len(sessions)

    if total_warnings == 0:
        recommendation = "No warnings in period. Feature may not be needed."
    elif total_warnings < 5:
        recommendation = f"Low frequency ({total_warnings} warnings). Advisory mode is sufficient."
    elif total_warnings < 20:
        recommendation = f"Moderate frequency ({total_warnings} warnings). Consider extending advisory period."
    else:
        recommendation = f"High frequency ({total_warnings} warnings). Blocking may be warranted."

    return {
        "status": "analyzed",
        "period": f"Last {days} days",
        "total_warnings": total_warnings,
        "unique_sessions": unique_sessions,
        "tool_distribution": dict(tools),
        "consecutive_stats": {
            "average": round(avg_consecutive, 1),
            "max": max_consecutive
        },
        "recommendation": recommendation,
        "warnings_sample": warnings[:5]  # First 5 warnings as sample
    }


def main():
    parser = argparse.ArgumentParser(
        description="Review investigation loop warnings to determine if blocking is warranted"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to analyze (default: 7)'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=Path(__file__).resolve().parent.parent / 'state' / 'logs' / 'investigation_loop_warnings.log',
        help='Path to investigation loop warnings log file'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("INVESTIGATION LOOP EVIDENCE REVIEW")
    print("=" * 70)
    print(f"Analysis period: Last {args.days} days")
    print(f"Log file: {args.log_file}")
    print()

    result = analyze_warnings(args.log_file, args.days)

    print(f"Status: {result['status'].upper()}")
    print()

    if result['status'] == 'analyzed':
        print(f"Total warnings: {result['total_warnings']}")
        print(f"Unique sessions: {result['unique_sessions']}")
        print()
        print("Tool distribution:")
        for tool, count in result['tool_distribution'].items():
            print(f"  • {tool}: {count} warnings")
        print()
        print("Consecutive operation stats:")
        print(f"  • Average: {result['consecutive_stats']['average']}")
        print(f"  • Maximum: {result['consecutive_stats']['max']}")
        print()
        print("-" * 70)
        print("RECOMMENDATION")
        print("-" * 70)
        print(result['recommendation'])
        print()
        print("Sample warnings (first 5):")
        for warning in result['warnings_sample']:
            print(f"  {warning['timestamp']}: {warning['raw'][:120]}...")
    else:
        print(result['message'])
        print()
        print(result['recommendation'])

    print()
    print("=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("Based on this analysis, you can:")
    print("1. Keep advisory mode (INVESTIGATION_LOOP_ADVISORY_MODE=true)")
    print("2. Enable blocking mode (INVESTIGATION_LOOP_ADVISORY_MODE=false)")
    print("3. Disable the feature entirely (remove from settings.json)")
    print()


if __name__ == '__main__':
    main()
