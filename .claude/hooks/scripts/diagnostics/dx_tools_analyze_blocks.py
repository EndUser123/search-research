#!/usr/bin/env python3
"""
DX Tools Block Decision Analysis Script

Analyzes authorization gate block decisions to calculate false positive rate
and identify patterns that may need refinement.

Run weekly to review whitelist effectiveness and detect potential issues.

Usage:
    python scripts/dx_tools_analyze_blocks.py [--days N]

Example:
    python scripts/dx_tools_analyze_blocks.py --days 7  # Last 7 days
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze DX tools authorization gate block decisions"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to auth_blocks.jsonl (default: hooks/logs/auth_blocks.jsonl)"
    )
    parser.add_argument(
        "--alert-threshold",
        type=float,
        default=10.0,
        help="Block rate warning threshold as percentage (default: 10%%)"
    )

    return parser.parse_args()


def load_blocks(log_file: Path, days: int):
    """Load block decisions from JSONL log file.

    Args:
        log_file: Path to auth_blocks.jsonl
        days: Number of days to analyze

    Returns:
        List of block decision entries
    """
    if not log_file.exists():
        print(f"Error: Block log file not found: {log_file}")
        sys.exit(1)

    cutoff_time = datetime.utcnow() - timedelta(days=days)
    blocks = []

    try:
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(entry["timestamp"])

                    # Only include entries within the time window
                    if timestamp >= cutoff_time:
                        blocks.append(entry)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Skipping invalid log entry: {e}")
                    continue
    except Exception as e:
        print(f"Error reading block log: {e}")
        sys.exit(1)

    return blocks


def analyze_blocks(blocks):
    """Analyze block decisions and calculate metrics.

    Args:
        blocks: List of block decision entries

    Returns:
        Dictionary with analysis results
    """
    total_blocks = len(blocks)

    if total_blocks == 0:
        return {
            "total_blocks": 0,
            "block_rate_percentage": 0.0,
            "by_reason": {},
            "by_pattern": Counter(),
            "recent_blocks": []
        }

    # Count blocks by reason
    reason_counts = Counter(b.get("reason", "unknown") for b in blocks)

    # Count blocks by pattern (if available)
    pattern_counts = Counter(b.get("pattern", "") for b in blocks if b.get("pattern"))
    pattern_counts.pop("", None)  # Remove empty pattern

    # Get most recent blocks (last 10)
    recent_blocks = sorted(blocks, key=lambda b: b["timestamp"], reverse=True)[:10]

    return {
        "total_blocks": total_blocks,
        "block_rate_percentage": 0.0,  # Will be calculated by caller
        "by_reason": dict(reason_counts),
        "by_pattern": dict(pattern_counts.most_common(10)),
        "recent_blocks": recent_blocks
    }


def print_report(analysis, alert_threshold: float):
    """Print analysis report with warnings if threshold exceeded.

    Args:
        analysis: Analysis results dictionary
        alert_threshold: Block rate warning threshold
    """
    print("\n" + "="*60)
    print("DX TOOLS AUTHORIZATION GATE BLOCK ANALYSIS")
    print("="*60)

    print(f"\nTotal blocks: {analysis['total_blocks']}")

    if analysis['total_blocks'] > 0:
        print(f"Block rate: {analysis['block_rate_percentage']:.2f}%")

        # Check if block rate exceeds threshold
        if analysis['block_rate_percentage'] > alert_threshold:
            print(f"\n⚠️  WARNING: Block rate ({analysis['block_rate_percentage']:.1f}%) exceeds threshold ({alert_threshold}%)")
            print("   Consider reviewing whitelist patterns in PreToolUse_authorization_gate.py")
        else:
            print(f"\n✓ Block rate within acceptable range (< {alert_threshold}%)")

        # Breakdown by reason
        if analysis['by_reason']:
            print("\nBlocks by reason:")
            for reason, count in sorted(analysis['by_reason'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / analysis['total_blocks']) * 100
                print(f"  - {reason}: {count} ({percentage:.1f}%)")

        # Top blocked patterns
        if analysis['by_pattern']:
            print("\nTop blocked patterns:")
            for pattern, count in list(analysis['by_pattern'].items())[:5]:
                percentage = (count / analysis['total_blocks']) * 100
                print(f"  - {pattern[:60]}: {count} ({percentage:.1f}%)")

        # Recent blocks
        if analysis['recent_blocks']:
            print("\nRecent blocks (last 10):")
            for block in analysis['recent_blocks']:
                timestamp = block['timestamp'][:19]  # Remove microseconds
                command = block['command'][:50] + "..." if len(block['command']) > 50 else block['command']
                print(f"  [{timestamp}] {block.get('reason', 'unknown')}: {command}")

    print("\n" + "="*60)


def main():
    """Main entry point."""
    args = parse_arguments()

    # Determine log file path
    if args.log_file:
        log_file = Path(args.log_file)
    else:
        hooks_dir = Path(__file__).resolve().parent.parent
        log_file = hooks_dir / "logs" / "auth_blocks.jsonl"

    # Load and analyze blocks
    blocks = load_blocks(log_file, args.days)

    # Get metrics for total operations count (if available)
    try:
        # Try to get total auth decisions from metrics
        from __lib.dx_tools_observability import get_metrics

        metrics = get_metrics()
        auth_metrics = metrics.get_metrics("auth")

        total_operations = auth_metrics.get("auto_approved", 0) + auth_metrics.get("blocked", 0)
        blocked_count = auth_metrics.get("blocked", 0)

        if total_operations > 0:
            block_rate = (blocked_count / total_operations) * 100
        else:
            block_rate = 0.0
    except Exception:
        # Fallback: calculate from block log only (incomplete data)
        print("Warning: Could not load metrics, using block log only (total count unknown)")
        total_operations = None
        block_rate = 0.0

    # Analyze blocks
    analysis = analyze_blocks(blocks)
    analysis['block_rate_percentage'] = block_rate

    # Print report
    print_report(analysis, args.alert_threshold)

    # Exit with warning code if threshold exceeded
    if block_rate > args.alert_threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
