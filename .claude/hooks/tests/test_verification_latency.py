#!/usr/bin/env python3
"""Latency benchmark for Stop gate overhead.

TASK-016b: Benchmark test that measures wall-clock time for Stop_hypothesis_as_fact_gate.run()
over 100 synthetic turns with varying response lengths and tool event store sizes.

Acceptance: p95 ≤ 20ms for all combinations (response length × tool event count).
"""

import os
import sys
import time
from pathlib import Path
from typing import Any

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Disable gate for imports
os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = "false"

import pytest


def _generate_synthetic_response(length_chars: int) -> str:
    """Generate synthetic response text of specified length.

    Args:
        length_chars: Target length in characters

    Returns:
        Synthetic response text with claim pattern
    """
    # Base claim pattern
    claim = "The package has no skill/ directory. This means the project structure is incomplete."

    if length_chars <= len(claim):
        return claim[:length_chars]

    # Extend with repetitive text to reach target length
    repeat_count = (length_chars - len(claim)) // 50
    extension = " Additional context about the project structure and dependencies. " * repeat_count
    return (claim + extension)[:length_chars]


def _generate_synthetic_tool_events(count: int) -> list[dict[str, Any]]:
    """Generate synthetic tool events.

    Args:
        count: Number of tool events to generate

    Returns:
        List of synthetic tool event dictionaries
    """
    events = []
    for i in range(count):
        events.append({
            "id": i + 1,
            "name": "Read" if i % 2 == 0 else "Glob",
            "command": f"package/{i}/file.md",
            "cwd": "/project",
            "output_excerpt": f"Content of file {i}",
            "success": True,
        })
    return events


def _benchmark_run(
    response_length: int,
    event_count: int,
    iterations: int = 100,
) -> list[float]:
    """Benchmark gate execution time.

    Args:
        response_length: Length of response text in characters
        event_count: Number of tool events in evidence store
        iterations: Number of iterations to run

    Returns:
        List of execution times in milliseconds
    """
    from unittest.mock import patch

    import Stop_hypothesis_as_fact_gate

    # Generate synthetic data
    response_text = _generate_synthetic_response(response_length)
    tool_events = _generate_synthetic_tool_events(event_count)

    # Create mock evidence store
    def mock_load_events(*args, **kwargs):
        return tool_events

    # Hook data
    hook_data = {
        "session_id": "benchmark-session",
        "terminal_id": "benchmark-terminal",
        "response_text": response_text,
    }

    # Benchmark iterations
    times = []
    for _ in range(iterations):
        start = time.perf_counter()

        with patch('evidence_store.load_tool_events_for_context', mock_load_events):
            result = Stop_hypothesis_as_fact_gate.run(hook_data)

        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return times


@pytest.mark.benchmark
@pytest.mark.parametrize("response_length", [500, 2000, 8000])
@pytest.mark.parametrize("event_count", [5, 20, 50])
def test_gate_latency(response_length: int, event_count: int) -> None:
    """Benchmark gate latency across different response lengths and event counts.

    Asserts p95 ≤ 20ms for all combinations.
    """
    # Run benchmark
    times = _benchmark_run(response_length, event_count, iterations=100)

    # Calculate statistics
    times_sorted = sorted(times)
    p50 = times_sorted[49]  # Median (50th percentile)
    p95 = times_sorted[94]  # 95th percentile
    p99 = times_sorted[98]  # 99th percentile
    avg = sum(times) / len(times)

    # Print results
    print(f"\nBenchmark: {response_length} chars × {event_count} events")
    print(f"  Avg: {avg:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")

    # Assert p95 ≤ 20ms
    assert p95 <= 20.0, f"P95 latency {p95:.2f}ms exceeds 20ms threshold for {response_length} chars × {event_count} events"


@pytest.mark.benchmark
def test_latency_summary() -> None:
    """Generate tabular summary of all benchmark combinations.

    Output format: chars × events × p95ms
    """
    print("\n" + "=" * 60)
    print("LATENCY BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"{'Chars':<10} {'Events':<10} {'P50 (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12}")
    print("-" * 60)

    response_lengths = [500, 2000, 8000]
    event_counts = [5, 20, 50]

    for response_length in response_lengths:
        for event_count in event_counts:
            times = _benchmark_run(response_length, event_count, iterations=100)
            times_sorted = sorted(times)
            p50 = times_sorted[49]
            p95 = times_sorted[94]
            p99 = times_sorted[98]

            print(f"{response_length:<10} {event_count:<10} {p50:<12.2f} {p95:<12.2f} {p99:<12.2f}")

    print("=" * 60)
