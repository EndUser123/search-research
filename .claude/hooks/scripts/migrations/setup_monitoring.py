#!/usr/bin/env python3
"""
Monitoring Infrastructure Setup (TASK-014)

Creates the monitoring database and configuration for tracking
LLM thinking quality improvements over time.
"""

import json
import sqlite3
import sys
from pathlib import Path


def create_monitoring_database():
    """Create SQLite database for metrics storage."""
    db_file = Path("P:/.claude/state/monitoring.db")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            phase TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            baseline_value REAL NOT NULL,
            improvement_pct REAL,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phase ON metrics(phase)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric ON metrics(metric_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)")

    conn.commit()
    conn.close()

    print(f"Created monitoring database at {db_file}")


def create_monitoring_config():
    """Create monitoring configuration file."""
    config = {
        "alerts": {
            "error_rate_threshold": 15.0,
            "token_reduction_target": 50.0,
            "verification_rate_target": 0.90,
        },
        "phases": {
            "baseline": {
                "name": "Baseline Measurement",
                "target_metrics": {
                    "average_tokens_per_response": 850.0,
                    "claim_verification_rate": 0.65,
                    "error_rate_per_100_responses": 24.2,
                },
            },
            "phase1": {
                "name": "Self-Reflection Loops",
                "target_metrics": {
                    "average_tokens_per_response": 680.0,  # 20% reduction
                    "claim_verification_rate": 0.85,  # 20% improvement
                    "error_rate_per_100_responses": 12.0,  # 50% reduction
                },
            },
            "phase2": {
                "name": "Tree-of-Thoughts",
                "target_metrics": {
                    "average_tokens_per_response": 600.0,
                    "claim_verification_rate": 0.90,
                    "error_rate_per_100_responses": 8.0,
                },
            },
            "phase3": {
                "name": "Chain-of-Draft",
                "target_metrics": {
                    "average_tokens_per_response": 450.0,  # 50% reduction from baseline
                    "claim_verification_rate": 0.92,
                    "error_rate_per_100_responses": 4.0,  # 85% reduction
                },
            },
        },
        "dashboard": {"refresh_interval_seconds": 300, "retention_days": 90},
    }

    config_file = Path("P:/.claude/state/monitoring_config.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Created monitoring config at {config_file}")


def main():
    """Main entry point."""
    print("Setting up monitoring infrastructure...")

    create_monitoring_database()
    create_monitoring_config()

    print("Monitoring infrastructure setup complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
