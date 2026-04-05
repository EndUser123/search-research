#!/usr/bin/env python3
"""CSF Metrics Tracker.

Provides metrics tracking for Cognitive Steering Framework hooks.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections import Counter
from pathlib import Path

STATE_DIR = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
LOG_DIR = Path(os.environ.get("CSF_LOG_DIR", "P:/.claude/logs"))

# Metrics storage
_metrics: Counter = Counter()
_metrics_lock = threading.Lock()

# Metrics file path
METRICS_FILE = STATE_DIR / "csf_metrics.json"


def increment(metric_name: str, value: int = 1) -> None:
    """Increment a metric by value.

    Args:
        metric_name: Name of the metric to increment
        value: Amount to increment (default: 1)
    """
    with _metrics_lock:
        _metrics[metric_name] += value


def get(metric_name: str, default: int = 0) -> int:
    """Get current value of a metric.

    Args:
        metric_name: Name of the metric
        default: Default value if metric doesn't exist

    Returns:
        Current metric value
    """
    with _metrics_lock:
        return _metrics.get(metric_name, default)


def get_all() -> dict[str, int]:
    """Get all metrics as a dictionary.

    Returns:
        Dictionary of all metric names and values
    """
    with _metrics_lock:
        return dict(_metrics)


def reset(metric_name: str | None = None) -> None:
    """Reset a metric or all metrics.

    Args:
        metric_name: Name of metric to reset, or None to reset all
    """
    with _metrics_lock:
        if metric_name:
            _metrics[metric_name] = 0
        else:
            _metrics.clear()


def save_metrics() -> bool:
    """Save metrics to disk.

    Returns:
        True if successful, False otherwise
    """
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with _metrics_lock:
            data = {
                "timestamp": time.time(),
                "metrics": dict(_metrics),
            }
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def load_metrics() -> bool:
    """Load metrics from disk.

    Returns:
        True if successful, False otherwise
    """
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            with _metrics_lock:
                _metrics.clear()
                _metrics.update(data.get("metrics", {}))
        return True
    except (OSError, json.JSONDecodeError):
        return False


# === FrameGuard Metrics ===


# Convenience functions for FrameGuard metrics
def frameguard_triggers_inc() -> None:
    """Increment FrameGuard trigger count."""
    increment("frameguard_triggers_total")


def frameguard_blocked_inc() -> None:
    """Increment FrameGuard block count."""
    increment("frameguard_blocked_total")


def frameguard_unhandled_inc() -> None:
    """Increment FrameGuard unhandled count."""
    increment("frameguard_unhandled_total")


def frameguard_false_positive_inc() -> None:
    """Increment FrameGuard false positive count."""
    increment("frameguard_false_positive_flagged")


def get_frameguard_metrics() -> dict[str, int]:
    """Get all FrameGuard metrics.

    Returns:
        Dictionary with FrameGuard metric names and values
    """
    return {
        "frameguard_triggers_total": get("frameguard_triggers_total"),
        "frameguard_blocked_total": get("frameguard_blocked_total"),
        "frameguard_unhandled_total": get("frameguard_unhandled_total"),
        "frameguard_false_positive_flagged": get("frameguard_false_positive_flagged"),
    }


if __name__ == "__main__":
    """CLI for metrics management."""
    import argparse

    parser = argparse.ArgumentParser(description="CSF Metrics Tracker")
    parser.add_argument("command", choices=["get", "reset", "save", "load"], help="Command to run")
    parser.add_argument("--metric", help="Metric name (for reset/get)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "get":
        if args.metric:
            value = get(args.metric)
            if args.json:
                print(json.dumps({args.metric: value}))
            else:
                print(f"{args.metric}: {value}")
        else:
            data = get_all()
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                for name, value in sorted(data.items()):
                    print(f"{name}: {value}")

    elif args.command == "reset":
        if args.metric:
            reset(args.metric)
            print(f"Reset {args.metric}")
        else:
            reset()
            print("Reset all metrics")

    elif args.command == "save":
        if save_metrics():
            print(f"Saved metrics to {METRICS_FILE}")
        else:
            print("Failed to save metrics")
            sys.exit(1)

    elif args.command == "load":
        if load_metrics():
            print(f"Loaded metrics from {METRICS_FILE}")
        else:
            print("Failed to load metrics")
            sys.exit(1)
