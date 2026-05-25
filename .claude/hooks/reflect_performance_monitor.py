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
import logging as _li

_REFL_DIR = Path(__file__).resolve().parent
_LOG_DIR = _REFL_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

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
            _logger.error("🚨 CRITICAL: Reflect signal extraction exceeded hook timeout!")
            _logger.error(f"Duration: {duration_ms}ms (timeout is 5000ms)")
            _logger.error("Action: Hook may have failed. Consider disabling semantic analysis.")
            _logger.error("Feature flags: Set FEATURE_FLAGS in extract_signals.py to disable categories.")
        elif duration_ms >= 4000:
            _logger.warning("Reflect signal extraction approaching timeout threshold")
            _logger.error(f"Duration: {duration_ms}ms (timeout is 5000ms)")
            _logger.warning("Consider: Disabling semantic analysis or reducing transcript size")
            _logger.error("Feature flags: Set FEATURE_FLAGS in extract_signals.py to disable categories.")
        elif duration_ms >= 3000:
            # Advisory: Performance degraded but not critical
            _logger.info(f"INFO: Reflect extraction took {duration_ms}ms (monitoring)")
            _logger.info("Performance is acceptable but worth monitoring.")


if __name__ == "__main__":
    # Read logs from stdin (piped from SessionEnd hook)
    logs = sys.stdin.read()

    # Check performance
    check_performance(logs)

    # Always pass (non-blocking)
    sys.exit(0)
