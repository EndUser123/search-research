#!/usr/bin/env python3
"""
Verification Telemetry Analyzer
================================

Analyzes verification system telemetry for pattern tuning and monitoring.

Metrics:
- Blocked claims by type
- False positive rate
- Tier distribution
- Tool usage patterns

Usage:
    python analyze_verification_telemetry.py --week
    python analyze_verification_telemetry.py --false-positive-rate
    python analyze_verification_telemetry.py --tiers
    python analyze_verification_telemetry.py --format json --output metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = HOOKS_DIR / "state" / "logs"

# Log files
UNVERIFIED_STANCE_LOG = LOG_DIR / "unverified_stance.log"
E2E_EXECUTIONS_DIR = HOOKS_DIR / "state"
BYPASS_AUDIT_LOG = LOG_DIR / "verification_bypass.log"


def load_jsonl_logs(log_file: Path) -> list[dict]:
    """Load JSONL log file.

    Args:
        log_file: Path to JSONL log file

    Returns:
        List of log entry dictionaries
    """
    if not log_file.exists():
        return []

    entries = []
    try:
        with open(log_file, encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return []

    return entries


def filter_by_week(entries: list[dict], weeks: int = 1) -> list[dict]:
    """Filter log entries by time range.

    Args:
        entries: List of log entries
        weeks: Number of weeks to look back (default: 1)

    Returns:
        Filtered list of entries
    """
    cutoff = datetime.now() - timedelta(weeks=weeks)
    filtered = []

    for entry in entries:
        try:
            timestamp_str = entry.get("ts") or entry.get("timestamp")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if timestamp >= cutoff:
                    filtered.append(entry)
        except (ValueError, TypeError):
            continue

    return filtered


def analyze_blocked_claims(entries: list[dict]) -> dict:
    """Analyze blocked claims by type.

    Args:
        entries: Unverified stance log entries

    Returns:
        Dictionary with claim type statistics
    """
    claim_types = Counter()
    skills_mentioned = Counter()
    total_blocks = 0

    for entry in entries:
        if entry.get("status") == "blocked":
            total_blocks += 1

            # Count claim types
            claim_type = entry.get("claim_type", "unknown")
            claim_types[claim_type] += 1

            # Count skills mentioned
            skill = entry.get("skill_mentioned", "")
            if skill:
                skills_mentioned[skill] += 1

    return {
        "total_blocks": total_blocks,
        "claim_types": dict(claim_types.most_common(10)),
        "top_skills": dict(skills_mentioned.most_common(5))
    }


def calculate_false_positive_rate(entries: list[dict]) -> dict:
    """Calculate false positive rate.

    A false positive is a block that was later bypassed or corrected.

    Args:
        entries: Unverified stance log entries

    Returns:
        Dictionary with false positive statistics
    """
    total_blocks = sum(1 for e in entries if e.get("status") == "blocked")

    # Count blocks followed by bypass (proxy for false positive)
    false_positives = 0
    for i, entry in enumerate(entries):
        if entry.get("status") == "blocked":
            # Check if next entry is a bypass
            if i + 1 < len(entries):
                next_entry = entries[i + 1]
                if next_entry.get("status") == "bypassed":
                    false_positives += 1

    if total_blocks == 0:
        return {
            "total_blocks": 0,
            "false_positives": 0,
            "false_positive_rate": 0.0
        }

    return {
        "total_blocks": total_blocks,
        "false_positives": false_positives,
        "false_positive_rate": round(false_positives / total_blocks * 100, 2)
    }


def analyze_tier_distribution(entries: list[dict]) -> dict:
    """Analyze tier distribution of blocked claims.

    Args:
        entries: Unverified stance log entries

    Returns:
        Dictionary with tier statistics
    """
    tiers = Counter()

    for entry in entries:
        if entry.get("status") == "blocked":
            tier = entry.get("tier", "unknown")
            tiers[tier] += 1

    return {
        "tier_distribution": dict(tiers),
        "total_tiered": sum(tiers.values())
    }


def analyze_tool_usage(e2e_entries: list[dict]) -> dict:
    """Analyze tool usage patterns from E2E execution logs.

    Args:
        e2e_entries: E2E execution log entries

    Returns:
        Dictionary with tool usage statistics
    """
    tools = Counter()
    workflows = Counter()

    for entry in e2e_entries:
        # Count workflow types
        workflow_type = entry.get("workflow_type", "unknown")
        workflows[workflow_type] += 1

        # Count tools in stages
        for stage in entry.get("stages", []):
            tool_name = stage.get("stage", "unknown")
            tools[tool_name] += 1

    return {
        "tool_usage": dict(tools.most_common(10)),
        "workflow_types": dict(workflows)
    }


def analyze_bypass_patterns(bypass_entries: list[dict]) -> dict:
    """Analyze verification bypass patterns.

    Args:
        bypass_entries: Bypass audit log entries

    Returns:
        Dictionary with bypass statistics
    """
    reason_counts = Counter()
    impact_counts = Counter()
    total_bypasses = len(bypass_entries)

    for entry in bypass_entries:
        reason = entry.get("reason", "unknown")
        impact = entry.get("security_impact", "unknown")

        reason_counts[reason] += 1
        impact_counts[impact] += 1

    return {
        "total_bypasses": total_bypasses,
        "reason_counts": dict(reason_counts.most_common(5)),
        "impact_distribution": dict(impact_counts)
    }


def generate_pattern_recommendations(
    blocked_claims: dict,
    false_positive_rate: dict,
    tier_distribution: dict
) -> list[str]:
    """Generate pattern tuning recommendations.

    Args:
        blocked_claims: Blocked claims analysis
        false_positive_rate: False positive rate analysis
        tier_distribution: Tier distribution analysis

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Check false positive rate
    fpr = false_positive_rate.get("false_positive_rate", 0)
    if fpr > 10:
        recommendations.append(
            f"⚠️  HIGH FALSE POSITIVE RATE ({fpr}%): "
            "Consider adjusting detection patterns or adding exclusions."
        )
    elif fpr > 5:
        recommendations.append(
            f"⚠️  Moderate false positive rate ({fpr}%): "
            "Monitor for patterns causing false positives."
        )
    else:
        recommendations.append(
            f"✅ False positive rate acceptable ({fpr}%)"
        )

    # Check tier distribution
    tier_dist = tier_distribution.get("tier_distribution", {})
    if tier_dist.get("Tier 1", 0) > tier_dist.get("Tier 3", 0):
        recommendations.append(
            "⚠️  More Tier 1 blocks than Tier 3: "
            "Consider tuning sensitivity for critical claims."
        )

    # Check claim types
    claim_types = blocked_claims.get("claim_types", {})
    if claim_types.get("absence_claim", 0) > 10:
        recommendations.append(
            "💡 High absence_claim blocks: "
            "Consider adding verification guidance to hooks."
        )

    if not recommendations:
        recommendations.append("✅ No immediate recommendations")

    return recommendations


def print_weekly_report(
    blocked_claims: dict,
    false_positive_rate: dict,
    tier_distribution: dict,
    tool_usage: dict,
    bypass_patterns: dict,
    recommendations: list[str]
) -> None:
    """Print formatted weekly report.

    Args:
        blocked_claims: Blocked claims analysis
        false_positive_rate: False positive rate analysis
        tier_distribution: Tier distribution analysis
        tool_usage: Tool usage analysis
        bypass_patterns: Bypass patterns analysis
        recommendations: List of recommendations
    """
    print("\n" + "=" * 60)
    print("VERIFICATION TELEMETRY WEEKLY REPORT")
    print("=" * 60)

    print("\n📊 BLOCKED CLAIMS")
    print(f"  Total blocks: {blocked_claims['total_blocks']}")
    print("  Top claim types:")
    for claim_type, count in list(blocked_claims['claim_types'].items())[:5]:
        print(f"    • {claim_type}: {count}")

    print("\n  Top skills mentioned:")
    for skill, count in list(blocked_claims['top_skills'].items())[:3]:
        print(f"    • {skill}: {count}")

    print("\n📈 FALSE POSITIVE RATE")
    fpr = false_positive_rate['false_positive_rate']
    print(f"  Total blocks: {false_positive_rate['total_blocks']}")
    print(f"  False positives: {false_positive_rate['false_positives']}")
    print(f"  Rate: {fpr}%")
    if fpr < 5:
        print("  Status: ✅ ACCEPTABLE")
    elif fpr < 10:
        print("  Status: ⚠️  MODERATE")
    else:
        print("  Status: ❌ HIGH")

    print("\n🎯 TIER DISTRIBUTION")
    print(f"  Total tiered blocks: {tier_distribution['total_tiered']}")
    for tier, count in tier_distribution['tier_distribution'].items():
        print(f"    • {tier}: {count}")

    print("\n🔧 TOOL USAGE")
    print("  Top tools:")
    for tool, count in list(tool_usage['tool_usage'].items())[:5]:
        print(f"    • {tool}: {count}")

    print("\n🔄 BYPASS PATTERNS")
    print(f"  Total bypasses: {bypass_patterns['total_bypasses']}")
    if bypass_patterns['reason_counts']:
        print("  Top reasons:")
        for reason, count in list(bypass_patterns['reason_counts'].items())[:3]:
            print(f"    • {reason}: {count}")

    print("\n💡 RECOMMENDATIONS")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    print("\n" + "=" * 60)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze verification system telemetry"
    )
    parser.add_argument(
        "--week",
        type=int,
        default=1,
        help="Number of weeks to analyze (default: 1)"
    )
    parser.add_argument(
        "--false-positive-rate",
        action="store_true",
        help="Show false positive rate only"
    )
    parser.add_argument(
        "--tiers",
        action="store_true",
        help="Show tier distribution only"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Load logs
    unverified_entries = load_jsonl_logs(UNVERIFIED_STANCE_LOG)
    unverified_entries = filter_by_week(unverified_entries, args.week)

    bypass_entries = load_jsonl_logs(BYPASS_AUDIT_LOG)
    bypass_entries = filter_by_week(bypass_entries, args.week)

    # Load E2E execution logs
    e2e_entries = []
    for log_file in E2E_EXECUTIONS_DIR.glob("e2e_executions_*.jsonl"):
        e2e_entries.extend(load_jsonl_logs(log_file))
    e2e_entries = filter_by_week(e2e_entries, args.week)

    # Run analyses
    blocked_claims = analyze_blocked_claims(unverified_entries)
    false_positive_rate = calculate_false_positive_rate(unverified_entries)
    tier_distribution = analyze_tier_distribution(unverified_entries)
    tool_usage = analyze_tool_usage(e2e_entries)
    bypass_patterns = analyze_bypass_patterns(bypass_entries)
    recommendations = generate_pattern_recommendations(
        blocked_claims,
        false_positive_rate,
        tier_distribution
    )

    # Prepare output
    if args.format == "json":
        output = {
            "blocked_claims": blocked_claims,
            "false_positive_rate": false_positive_rate,
            "tier_distribution": tier_distribution,
            "tool_usage": tool_usage,
            "bypass_patterns": bypass_patterns,
            "recommendations": recommendations
        }

        output_json = json.dumps(output, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"✅ Output written to {args.output}")
        else:
            print(output_json)

    elif args.false_positive_rate:
        print("\n📈 FALSE POSITIVE RATE")
        print(f"  Total blocks: {false_positive_rate['total_blocks']}")
        print(f"  False positives: {false_positive_rate['false_positives']}")
        print(f"  Rate: {false_positive_rate['false_positive_rate']}%")

    elif args.tiers:
        print("\n🎯 TIER DISTRIBUTION")
        print(f"  Total tiered blocks: {tier_distribution['total_tiered']}")
        for tier, count in tier_distribution['tier_distribution'].items():
            print(f"    • {tier}: {count}")

    else:
        # Full weekly report
        print_weekly_report(
            blocked_claims,
            false_positive_rate,
            tier_distribution,
            tool_usage,
            bypass_patterns,
            recommendations
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
