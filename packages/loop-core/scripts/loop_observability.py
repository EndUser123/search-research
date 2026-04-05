"""
loop_observability: Best-effort logging and metrics for Ralph loops.

This module provides observability functions that follow the best-effort principle:
logging failures never break loop correctness. All functions gracefully handle
disk full, permission errors, and other I/O failures.

Key functions:
- log_decision(terminal_id, event, payload): Append JSON lines to decision.log
- update_metrics(terminal_id, metrics_delta): Merge into loop_metrics.json
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from scripts.state_paths import get_terminal_log_dir, get_terminal_state_dir


# Configure logging for observability failures
logger = logging.getLogger(__name__)


class LoopObservabilityError(Exception):
    """Base exception for loop observability errors."""

    pass


def log_decision(terminal_id: str, event: str, payload: dict[str, Any]) -> None:
    """
    Append a JSON line entry to the terminal's decision.log.

    This function follows the best-effort principle: any logging failures
    (disk full, permission errors, etc.) are caught and logged but never
    re-raised to avoid breaking loop execution.

    Args:
        terminal_id: Terminal identifier for log isolation
        event: Event name (e.g., "task_started", "iteration_complete")
        payload: Event data dictionary

    Returns:
        None

    Example:
        >>> log_decision("term_001", "task_started", {"task_id": "TASK-001"})
    """
    try:
        # Get log directory for this terminal
        log_dir = get_terminal_log_dir(terminal_id)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Build log entry
        log_entry = {
            "terminal_id": terminal_id,
            "event": event,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }

        # Serialize to JSON line
        json_line = json.dumps(log_entry) + "\n"

        # Append to decision.log
        log_file = log_dir / "decision.log"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json_line)

    except (OSError, IOError, PermissionError) as e:
        # Best-effort: log failure but don't raise
        logger.warning(f"Failed to log decision for terminal {terminal_id}: {e}")
    except (TypeError, ValueError) as e:
        # JSON serialization errors - don't break loop
        logger.warning(
            f"Failed to serialize log entry for terminal {terminal_id}: {e}"
        )
    except Exception as e:
        # Catch-all for unexpected errors
        logger.warning(f"Unexpected error logging decision for terminal {terminal_id}: {e}")


def update_metrics(terminal_id: str, metrics_delta: dict[str, Any]) -> None:
    """
    Merge metrics delta into the terminal's loop_metrics.json.

    This function follows the best-effort principle: any I/O failures
    are caught and logged but never re-raised to avoid breaking loop execution.

    The function performs an atomic write using the temp file + rename pattern
    to prevent corruption from crashes or concurrent access.

    Args:
        terminal_id: Terminal identifier for metrics isolation
        metrics_delta: Dictionary of metric updates (merged with existing)

    Returns:
        None

    Example:
        >>> update_metrics("term_001", {"tasks_completed": 1, "iterations": 1})
    """
    try:
        # Get state directory for this terminal
        state_dir = get_terminal_state_dir(terminal_id)
        state_dir.mkdir(parents=True, exist_ok=True)

        metrics_file = state_dir / "loop_metrics.json"

        # Read existing metrics or start fresh
        existing_metrics: dict[str, Any] = {}
        if metrics_file.exists():
            try:
                with metrics_file.open("r", encoding="utf-8") as f:
                    existing_metrics = json.load(f)
            except (json.JSONDecodeError, OSError):
                # Corrupted file - start fresh
                existing_metrics = {}

        # Merge metrics delta
        updated_metrics = _merge_metrics(existing_metrics, metrics_delta)

        # Add last update timestamp
        updated_metrics["last_update"] = datetime.now().isoformat()

        # Atomic write: temp file + rename
        temp_file = state_dir / f"loop_metrics.{id(object())}.tmp"
        try:
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(updated_metrics, f, indent=2)

            # Atomic rename
            temp_file.replace(metrics_file)

        finally:
            # Clean up temp file if it still exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    except (OSError, IOError, PermissionError) as e:
        # Best-effort: log failure but don't raise
        logger.warning(f"Failed to update metrics for terminal {terminal_id}: {e}")
    except Exception as e:
        # Catch-all for unexpected errors
        logger.warning(f"Unexpected error updating metrics for terminal {terminal_id}: {e}")


def _merge_metrics(
    existing: dict[str, Any], delta: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge metrics delta into existing metrics.

    Numeric values are summed, other values are overwritten.

    Args:
        existing: Current metrics dictionary
        delta: Updates to apply

    Returns:
        Merged metrics dictionary
    """
    merged = existing.copy()

    for key, value in delta.items():
        if key in merged:
            # Try to sum numeric values
            try:
                merged[key] = merged[key] + value  # type: ignore[operator]
            except TypeError:
                # Non-numeric - just overwrite
                merged[key] = value
        else:
            # New field - add as-is
            merged[key] = value

    return merged


# Future enhancements (REFACTOR phase)

# TODO: TASK-006-B - Implement log rotation
# def rotate_log(log_file: Path, max_size_mb: int = 10) -> None:
#     """Rotate log file when it exceeds max_size_mb."""
#     pass

# TODO: TASK-006-C - Implement buffered metrics writes
# class MetricsBuffer:
#     """Buffer metrics updates for batch writes."""
#
#     def __init__(self, terminal_id: str, buffer_size: int = 100):
#         self.terminal_id = terminal_id
#         self.buffer_size = buffer_size
#         self.buffer: dict[str, Any] = {}
#
#     def add(self, metrics_delta: dict[str, Any]) -> None:
#         """Add metrics to buffer."""
#         pass
#
#     def flush(self) -> None:
#         """Flush buffered metrics to disk."""
#         pass
