#!/usr/bin/env python3
"""
weekly_verification_analysis.py - Weekly verification gate metrics analysis

TASK-010: Monitoring & Iteration

Generates weekly reports on blocked claims patterns, tunes detection
patterns based on metrics, and provides recommendations for verification tiers.

Usage:
    python weekly_verification_analysis.py [--days 7] [--output report.json]

Example:
    python weekly_verification_analysis.py --days 7 --output weekly_report.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(HOOKS_DIR))

from telemetry.verification_metrics import get_metrics_summary


def generate_weekly_report(
    metrics_file: str | Path | None = None,
    days: int = 7
) -> dict[str, Any]:
    """Generate weekly verification analysis report.

    Args:
        metrics_file: Path to metrics JSONL file
        days: Number of days to analyze (default: 7)

    Returns:
        Dictionary with weekly analysis:
        {
            "period_days": int,
            "total_events": int,
            "block_rate": float,
            "by_tier": {...},
            "recommendations": [...]
        }

    Example:
        >>> report = generate_weekly_report(days=7)
        >>> print(f"Block rate: {report['block_rate']:.1%}")
    """
    summary = get_metrics_summary(metrics_file)

    # Calculate false positive indicators
    # High block count + low confidence = likely false positives
    high_blocks_low_conf = _analyze_false_positives(summary)

    # Generate recommendations
    recommendations = _generate_recommendations(summary, high_blocks_low_conf)

    return {
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
        "total_events": summary["total_events"],
        "blocked_count": summary["blocked_count"],
        "allowed_count": summary["allowed_count"],
        "block_rate": summary["block_rate"],
        "by_tier": summary["by_tier"],
        "confidence_distribution": summary["confidence_distribution"],
        "false_positive_indicators": high_blocks_low_conf,
        "recommendations": recommendations
    }


def _analyze_false_positives(summary: dict[str, Any]) -> dict[str, Any]:
    """Analyze metrics for false positive indicators.

    Args:
        summary: Metrics summary from get_metrics_summary()

    Returns:
        Dictionary with false positive analysis
    """
    low_conf_blocks = summary["confidence_distribution"]["low"]
    total = summary["total_events"]

    # Indicators of potential false positives:
    # 1. High block rate (>50%)
    # 2. Many low-confidence blocks (>20% of events)
    # 3. Block rate increasing over time (would need time-series data)

    return {
        "high_block_rate": summary["block_rate"] > 0.5,
        "high_block_rate_value": summary["block_rate"],
        "low_confidence_blocks": low_conf_blocks,
        "low_confidence_ratio": low_conf_blocks / total if total > 0 else 0.0,
        "potential_false_positive_rate": (
            low_conf_blocks / total if total > 0 else 0.0
        )
    }


def _generate_recommendations(
    summary: dict[str, Any],
    fp_indicators: dict[str, Any]
) -> list[str]:
    """Generate tuning recommendations based on metrics.

    Args:
        summary: Metrics summary
        fp_indicators: False positive indicators

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Check for high false positive rate
    if fp_indicators["potential_false_positive_rate"] > 0.1:
        recommendations.append(
            f"⚠️ High false positive rate detected ({fp_indicators['potential_false_positive_rate']:.1%}). "
            "Consider lowering detection thresholds or adding more exclusion patterns."
        )

    # Check for high block rate
    if summary["block_rate"] > 0.5:
        recommendations.append(
            f"⚠️ High block rate ({summary['block_rate']:.1%}). "
            "Review blocked claims to identify patterns that should be allowed."
        )

    # Check tier distribution
    tier_counts = summary.get("by_tier", {})
    if tier_counts:
        # Identify most active tier
        max_tier = max(tier_counts.items(), key=lambda x: x[1]["count"])
        recommendations.append(
            f"ℹ️ Most active verification tier: {max_tier[0]} "
            f"({max_tier[1]['count']} events, {max_tier[1]['blocked']} blocked)"
        )

    # Check confidence distribution
    conf_dist = summary["confidence_distribution"]
    total = summary["total_events"]
    if total > 0:
        high_conf_ratio = conf_dist["high"] / total
        if high_conf_ratio < 0.5:
            recommendations.append(
                f"⚠️ Low high-confidence ratio ({high_conf_ratio:.1%}). "
                "Detection patterns may need tuning for better precision."
            )

    # Default recommendation if everything looks good
    if not recommendations:
        recommendations.append(
            "✅ Verification gate performing well. "
            "Continue monitoring metrics weekly."
        )

    return recommendations


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Weekly verification gate metrics analysis"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--metrics-file",
        type=str,
        help="Path to metrics JSONL file (default: state/logs/verification_gate_metrics.jsonl)"
    )

    args = parser.parse_args()

    # Generate report
    report = generate_weekly_report(
        metrics_file=args.metrics_file,
        days=args.days
    )

    # Format output
    output = json.dumps(report, indent=2)

    # Write to file or stdout
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        print(f"Weekly report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
