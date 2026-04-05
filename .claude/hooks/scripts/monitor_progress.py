#!/usr/bin/env python3
"""
Monitoring Progress Script (TASK-014)

Records and reports on LLM thinking quality metrics over time.
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def record_metric(phase: str, metric_name: str, metric_value: float, baseline_value: float) -> None:
    """Record a metric to the monitoring database."""
    db_file = Path("P:/.claude/state/monitoring.db")

    # Calculate improvement percentage
    improvement_pct = None
    if baseline_value > 0:
        if metric_name in ["error_rate_per_100_responses", "average_tokens_per_response"]:
            # Lower is better
            improvement_pct = ((baseline_value - metric_value) / baseline_value) * 100
        else:
            # Higher is better
            improvement_pct = ((metric_value - baseline_value) / baseline_value) * 100

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO metrics (timestamp, phase, metric_name, metric_value, baseline_value, improvement_pct)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            datetime.now().isoformat(),
            phase,
            metric_name,
            metric_value,
            baseline_value,
            improvement_pct,
        ),
    )

    conn.commit()
    conn.close()


def generate_summary_report() -> dict[str, Any]:
    """Generate a summary report of all metrics."""
    db_file = Path("P:/.claude/state/monitoring.db")

    if not db_file.exists():
        return {"error": "Monitoring database not found"}

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get latest metrics by phase
    cursor.execute("""
        SELECT phase, metric_name, metric_value, baseline_value, improvement_pct
        FROM metrics
        WHERE (phase, metric_name, timestamp) IN (
            SELECT phase, metric_name, MAX(timestamp)
            FROM metrics
            GROUP BY phase, metric_name
        )
        ORDER BY phase, metric_name
    """)

    metrics = cursor.fetchall()
    conn.close()

    # Group by phase
    summary = {"phases": {}, "generated_at": datetime.now().isoformat()}

    for metric in metrics:
        phase = metric["phase"]
        if phase not in summary["phases"]:
            summary["phases"][phase] = {}

        summary["phases"][phase][metric["metric_name"]] = {
            "value": metric["metric_value"],
            "baseline": metric["baseline_value"],
            "improvement_pct": metric["improvement_pct"],
        }

    return summary


def main():
    """Main entry point."""
    # Load baseline metrics
    baseline_file = Path("P:/.claude/state/baseline_metrics.json")
    if not baseline_file.exists():
        print("Baseline metrics not found. Run measure_baseline.py first.")
        return 1

    with open(baseline_file) as f:
        baseline = json.load(f)

    # Record baseline metrics to monitoring database
    print("Recording baseline metrics...")
    record_metric(
        "baseline",
        "average_tokens_per_response",
        baseline["average_tokens_per_response"],
        baseline["average_tokens_per_response"],
    )
    record_metric(
        "baseline",
        "claim_verification_rate",
        baseline["claim_verification_rate"],
        baseline["claim_verification_rate"],
    )
    record_metric(
        "baseline",
        "error_rate_per_100_responses",
        baseline["error_rate_per_100_responses"],
        baseline["error_rate_per_100_responses"],
    )
    record_metric(
        "baseline",
        "stop_hook_latency_p50",
        baseline["stop_hook_latency_ms"]["p50"],
        baseline["stop_hook_latency_ms"]["p50"],
    )

    # Generate summary report
    summary = generate_summary_report()

    summary_file = Path("P:/.claude/state/monitoring_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary report written to {summary_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
