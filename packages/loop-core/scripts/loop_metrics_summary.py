"""
loop_metrics_summary: Acceptance monitoring script for Ralph loops.

This module scans terminal state directories, parses decision.log and
loop_metrics.json files, and produces summary reports with aggregated
statistics and cross-terminal isolation validation.

Key functions:
- collect_terminal_data(): Scan and collect data from all terminals
- parse_decision_log(): Parse JSON lines from decision.log
- parse_loop_metrics(): Parse loop_metrics.json file
- aggregate_metrics(): Aggregate statistics across terminals
- validate_cross_terminal_isolation(): Check for isolation violations
- format_summary_report(): Generate formatted summary report
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from scripts.state_paths import get_terminals_dir

# Configure logging
logger = logging.getLogger(__name__)


def parse_decision_log(log_file: Path) -> list[dict[str, Any]]:
    """
    Parse decision.log file, extracting JSON line entries.

    Handles malformed JSON gracefully by skipping invalid lines.

    Args:
        log_file: Path to decision.log file

    Returns:
        List of parsed log entries (empty list if file doesn't exist)
    """
    if not log_file.exists():
        return []

    entries: list[dict[str, Any]] = []

    try:
        with log_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    # Skip malformed lines
                    logger.debug(f"Skipping malformed JSON line in {log_file}")
                    continue

    except (OSError, IOError) as e:
        logger.warning(f"Failed to read decision log {log_file}: {e}")

    return entries


def parse_loop_metrics(metrics_file: Path) -> dict[str, Any] | None:
    """
    Parse loop_metrics.json file.

    Args:
        metrics_file: Path to loop_metrics.json file

    Returns:
        Parsed metrics dictionary, or None if file doesn't exist or is corrupted
    """
    if not metrics_file.exists():
        return None

    try:
        with metrics_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, IOError) as e:
        logger.warning(f"Failed to parse metrics file {metrics_file}: {e}")
        return None


def collect_terminal_data(terminals_dir: Path) -> list[dict[str, Any]]:
    """
    Scan terminal state directories and collect all data.

    Args:
        terminals_dir: Path to terminals state directory

    Returns:
        List of terminal data dictionaries with keys:
        - terminal_id: Terminal identifier
        - metrics: Parsed loop_metrics.json (or None)
        - decision_log: Parsed decision.log entries
    """
    if not terminals_dir.exists():
        return []

    terminals_data: list[dict[str, Any]] = []

    # Iterate over terminal subdirectories
    for terminal_path in terminals_dir.iterdir():
        if not terminal_path.is_dir():
            continue

        terminal_id = terminal_path.name

        # Parse decision.log
        log_file = terminal_path / "decision.log"
        decision_log = parse_decision_log(log_file)

        # Parse loop_metrics.json
        metrics_file = terminal_path / "loop_metrics.json"
        metrics = parse_loop_metrics(metrics_file)

        terminals_data.append(
            {
                "terminal_id": terminal_id,
                "metrics": metrics,
                "decision_log": decision_log,
            }
        )

    return terminals_data


def aggregate_metrics(terminals_data: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate metrics across all terminals.

    Args:
        terminals_data: List of terminal data dictionaries

    Returns:
        Aggregated metrics dictionary with keys:
        - total_terminals: Total number of terminals
        - total_errors: Sum of error counts from metrics
        - total_iterations: Sum of iteration counts
        - total_tasks_completed: Sum of completed tasks
        - exit_reasons: Dict mapping exit reasons to counts
        - error_events: Dict mapping terminal IDs to error event counts
        - per_terminal: List of per-terminal summaries
    """
    aggregated: dict[str, Any] = {
        "total_terminals": len(terminals_data),
        "total_errors": 0,
        "total_iterations": 0,
        "total_tasks_completed": 0,
        "exit_reasons": {},
        "error_events": {},
        "per_terminal": [],
    }

    for terminal_data in terminals_data:
        terminal_id = terminal_data["terminal_id"]
        metrics = terminal_data["metrics"]
        decision_log = terminal_data["decision_log"]

        # Aggregate metrics if available
        if metrics:
            aggregated["total_errors"] += metrics.get("errors", 0)
            aggregated["total_iterations"] += metrics.get("iterations", 0)
            aggregated["total_tasks_completed"] += metrics.get("tasks_completed", 0)

        # Count error events from decision log
        error_count = sum(1 for entry in decision_log if entry.get("event") == "error")
        if error_count > 0:
            aggregated["error_events"][terminal_id] = error_count

        # Extract exit reasons
        for entry in decision_log:
            if entry.get("event") == "exit":
                reason = entry.get("payload", {}).get("reason", "unknown")
                aggregated["exit_reasons"][reason] = (
                    aggregated["exit_reasons"].get(reason, 0) + 1
                )

        # Build per-terminal summary
        per_terminal_summary: dict[str, Any] = {
            "terminal_id": terminal_id,
            "errors": metrics.get("errors", 0) if metrics else 0,
            "iterations": metrics.get("iterations", 0) if metrics else 0,
            "tasks_completed": metrics.get("tasks_completed", 0) if metrics else 0,
            "error_events": error_count,
        }

        # Find exit reason for this terminal
        for entry in reversed(decision_log):
            if entry.get("event") == "exit":
                per_terminal_summary["exit_reason"] = (
                    entry.get("payload", {}).get("reason", "unknown")
                )
                break

        aggregated["per_terminal"].append(per_terminal_summary)

    return aggregated


def validate_cross_terminal_isolation(
    terminals_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate that terminals are properly isolated (no cross-terminal modifications).

    Checks for:
    - State modification events targeting other terminals
    - File access patterns to other terminal directories

    Args:
        terminals_data: List of terminal data dictionaries

    Returns:
        Validation result dictionary with keys:
        - is_isolated: True if no violations detected
        - violations: List of violation dictionaries
    """
    violations: list[dict[str, Any]] = []

    for terminal_data in terminals_data:
        terminal_id = terminal_data["terminal_id"]
        decision_log = terminal_data["decision_log"]

        for entry in decision_log:
            payload = entry.get("payload", {})

            # Check for cross-terminal state modifications
            if "target_terminal" in payload:
                target_terminal = payload["target_terminal"]
                if target_terminal != terminal_id:
                    violations.append(
                        {
                            "type": "cross_terminal_modification",
                            "terminal": terminal_id,
                            "target_terminal": target_terminal,
                            "event": entry.get("event"),
                            "details": f"Terminal {terminal_id} modified state of {target_terminal}",
                        }
                    )

            # Check for foreign terminal file access
            if "path" in payload:
                path = payload["path"]
                if "../terminals/" in path or "/terminals/" in path:
                    # Extract potential target terminal from path
                    for other_terminal in [t["terminal_id"] for t in terminals_data]:
                        if other_terminal in path and other_terminal != terminal_id:
                            violations.append(
                                {
                                    "type": "foreign_terminal_access",
                                    "terminal": terminal_id,
                                    "target_terminal": other_terminal,
                                    "event": entry.get("event"),
                                    "path": path,
                                    "details": f"Terminal {terminal_id} accessed {other_terminal} directory",
                                }
                            )

    return {
        "is_isolated": len(violations) == 0,
        "violations": violations,
    }


def format_summary_report(
    aggregated: dict[str, Any], validation: dict[str, Any]
) -> str:
    """
    Generate formatted summary report.

    Args:
        aggregated: Aggregated metrics from aggregate_metrics()
        validation: Validation results from validate_cross_terminal_isolation()

    Returns:
        Formatted summary report string
    """
    lines: list[str] = []

    # Header
    lines.append("=" * 60)
    lines.append("RALPH LOOP ACCEPTANCE MONITORING REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Terminal Summary
    lines.append("Terminal Summary:")
    lines.append("-" * 60)

    if aggregated.get("total_terminals", 0) == 0:
        lines.append("No terminal data found")
    else:
        lines.append(f"Total terminals: {aggregated.get('total_terminals', 0)}")
        lines.append(f"Total errors: {aggregated.get('total_errors', 0)}")
        lines.append(f"Total iterations: {aggregated.get('total_iterations', 0)}")
        lines.append(f"Total tasks completed: {aggregated.get('total_tasks_completed', 0)}")
        lines.append("")

        # Per-terminal breakdown
        if "per_terminal" in aggregated and aggregated["per_terminal"]:
            lines.append("Per-Terminal Details:")
            for terminal_summary in aggregated["per_terminal"]:
                terminal_id = terminal_summary.get("terminal_id", "unknown")
                errors = terminal_summary.get("errors", 0)
                exit_reason = terminal_summary.get("exit_reason", "unknown")

                lines.append(f"  - {terminal_id}: {errors} errors, exit: {exit_reason}")

        # Error events breakdown
        if aggregated.get("error_events"):
            lines.append("")
            lines.append("Error Events by Terminal:")
            for terminal_id, count in aggregated["error_events"].items():
                lines.append(f"  - {terminal_id}: {count} error events")

        # Exit reasons breakdown
        if aggregated.get("exit_reasons"):
            lines.append("")
            lines.append("Exit Reasons:")
            for reason, count in aggregated["exit_reasons"].items():
                lines.append(f"  - {reason}: {count}")

    lines.append("")

    # Cross-Terminal Validation
    lines.append("Cross-Terminal Validation:")
    lines.append("-" * 60)

    if validation["is_isolated"]:
        lines.append("✓ No state modifications detected")
        lines.append("✓ All terminals isolated")
    else:
        lines.append("✗ VIOLATIONS DETECTED")
        lines.append("")

        for violation in validation["violations"]:
            lines.append(f"  Violation Type: {violation['type']}")
            lines.append(f"  Terminal: {violation['terminal']}")
            if "target_terminal" in violation:
                lines.append(f"  Target: {violation['target_terminal']}")
            if "path" in violation:
                lines.append(f"  Path: {violation['path']}")
            lines.append(f"  Details: {violation['details']}")
            lines.append("")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    """
    Main entry point for loop metrics summary script.

    Scans terminal state directories and prints summary report.
    """
    # Get terminals directory
    terminals_dir = get_terminals_dir()

    # Collect data
    terminals_data = collect_terminal_data(terminals_dir)

    # Aggregate metrics
    aggregated = aggregate_metrics(terminals_data)

    # Validate isolation
    validation = validate_cross_terminal_isolation(terminals_data)

    # Generate and print report
    report = format_summary_report(aggregated, validation)
    print(report)


if __name__ == "__main__":
    main()
