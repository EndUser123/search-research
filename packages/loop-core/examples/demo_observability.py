#!/usr/bin/env python
"""
Demo script for loop_observability module.

This demonstrates best-effort logging and metrics for Ralph loops.
"""

import json
from pathlib import Path

from scripts import log_decision, update_metrics


def demo_observability():
    """Demonstrate observability functions."""
    terminal_id = "demo_terminal"

    print("=" * 60)
    print("loop-observability Demo")
    print("=" * 60)

    # 1. Log some decisions
    print("\n1. Logging decisions...")
    log_decision(terminal_id, "loop_started", {"plan_path": "/path/to/plan.md"})
    log_decision(terminal_id, "task_started", {"task_id": "TASK-001", "title": "Implement feature"})
    log_decision(terminal_id, "task_complete", {"task_id": "TASK-001", "duration_seconds": 120})
    log_decision(terminal_id, "iteration_complete", {"iteration": 1, "tasks_completed": 1})
    print("   ✓ Logged 4 decisions")

    # 2. Update metrics
    print("\n2. Updating metrics...")
    update_metrics(terminal_id, {"iterations": 1, "tasks_completed": 1, "errors": 0})
    update_metrics(terminal_id, {"tasks_completed": 2, "total_duration": 300})
    print("   ✓ Updated metrics")

    # 3. Show log file
    print("\n3. Reading decision.log...")
    log_file = Path(".claude/state/terminals") / terminal_id / "logs" / "decision.log"
    if log_file.exists():
        print(f"   Log file: {log_file}")
        with log_file.open() as f:
            lines = f.readlines()
            print(f"   Entries: {len(lines)}")
            print("   Latest entry:")
            latest = json.loads(lines[-1])
            print(f"     Event: {latest['event']}")
            print(f"     Timestamp: {latest['timestamp']}")
    else:
        print(f"   ✗ Log file not found: {log_file}")

    # 4. Show metrics file
    print("\n4. Reading loop_metrics.json...")
    metrics_file = Path(".claude/state/terminals") / terminal_id / "loop_metrics.json"
    if metrics_file.exists():
        print(f"   Metrics file: {metrics_file}")
        with metrics_file.open() as f:
            metrics = json.load(f)
            print("   Current metrics:")
            for key, value in metrics.items():
                print(f"     {key}: {value}")
    else:
        print(f"   ✗ Metrics file not found: {metrics_file}")

    # 5. Demonstrate best-effort error handling
    print("\n5. Demonstrating best-effort error handling...")
    print("   Attempting to log with invalid payload...")

    class NotSerializable:
        pass

    # This won't crash, just logs a warning
    log_decision(terminal_id, "test", {
        "valid": "data",
        "invalid": NotSerializable()
    })
    print("   ✓ No crash - best-effort handling worked!")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("\nKey features demonstrated:")
    print("  • Per-terminal log isolation")
    print("  • JSON line format for decision.log")
    print("  • Metrics merging with atomic writes")
    print("  • Best-effort error handling (no crashes)")
    print("\nFile locations:")
    print(f"  • Log: {log_file}")
    print(f"  • Metrics: {metrics_file}")


if __name__ == "__main__":
    demo_observability()
