#!/usr/bin/env python3
"""
Performance monitoring hook for reflect signal extraction.

Monitors extract_signals.py execution time and warns if approaching
the 5-second hook timeout threshold. This prevents silent performance
regression that could cause hook failures.

Trigger: SessionEnd hook
Checks: Signal extraction duration from stdout/stderr
Action: Warn user if extraction took >4 seconds
"""

import re
import sys


def check_performance(logs: str) -> None:
    """
    Check reflect signal extraction performance from logs.

    Args:
        logs: Combined stdout/stderr from SessionEnd hook

    Returns:
        None (writes warnings to stderr if performance issue detected)
    """
    # Pattern to match extraction duration warning from extract_signals.py
    # Example: "⚠️  WARNING: Signal extraction took 4200ms (approaching 5s hook timeout)"
    warning_pattern = r"WARNING: Signal extraction took (\d+)ms"

    matches = re.findall(warning_pattern, logs)

    if matches:
        # Get the most recent (last) duration
        duration_ms = int(matches[-1])

        # Severity levels based on duration
        if duration_ms >= 5000:
            print(
                "\n🚨 CRITICAL: Reflect signal extraction exceeded hook timeout!",
                file=sys.stderr
            )
            print(
                f"   Duration: {duration_ms}ms (timeout is 5000ms)",
                file=sys.stderr
            )
            print(
                "   Action: Hook may have failed. Consider disabling semantic analysis.",
                file=sys.stderr
            )
            print(
                "   Feature flags: Set FEATURE_FLAGS in extract_signals.py to disable categories.",
                file=sys.stderr
            )
        elif duration_ms >= 4000:
            print(
                "\n⚠️  WARNING: Reflect signal extraction approaching timeout threshold",
                file=sys.stderr
            )
            print(
                f"   Duration: {duration_ms}ms (timeout is 5000ms)",
                file=sys.stderr
            )
            print(
                "   Consider: Disabling semantic analysis or reducing transcript size",
                file=sys.stderr
            )
            print(
                "   Feature flags: Set FEATURE_FLAGS in extract_signals.py to disable categories.",
                file=sys.stderr
            )
        elif duration_ms >= 3000:
            # Advisory: Performance degraded but not critical
            print(
                f"\nℹ️  INFO: Reflect extraction took {duration_ms}ms (monitoring)",
                file=sys.stderr
            )
            print(
                "   Performance is acceptable but worth monitoring.",
                file=sys.stderr
            )


if __name__ == "__main__":
    # Read logs from stdin (piped from SessionEnd hook)
    logs = sys.stdin.read()

    # Check performance
    check_performance(logs)

    # Always pass (non-blocking)
    sys.exit(0)
