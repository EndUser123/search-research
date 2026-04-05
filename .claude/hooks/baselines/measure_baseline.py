#!/usr/bin/env python3
"""Performance baseline measurement for cognitive & reasoning systems.

This script instruments cognitive_enhancers, reasoning_mode_selector, and
think_trigger to measure actual latency before optimization.

Output: baselines/current_performance_baseline.json
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Sample prompts for measurement (representative of actual usage)
SAMPLE_PROMPTS = [
    # Implementation prompts
    "Implement a new feature to add user authentication",
    "Refactor the database layer to use async patterns",
    "Create a new endpoint for handling file uploads",

    # Diagnostic prompts
    "Debug why the test keeps failing intermittently",
    "Investigate the root cause of the memory leak",
    "Figure out why the API is returning 500 errors",

    # Architecture prompts
    "Design a system for handling real-time notifications",
    "Should we use Redis or Memcached for caching?",
    "Evaluate whether to split this into microservices",

    # Tradeoff prompts
    "What's the best approach for error handling here?",
    "Should we optimize for read or write performance?",
    "Tradeoff between consistency and availability for this feature",

    # Short prompts (edge cases)
    "fix the bug",
    "optimize this code",
    "/code refactor the auth module",
]


@dataclass(frozen=True)
class TimingResult:
    """Result from timing a single hook execution."""
    hook_name: str
    duration_ms: float
    prompt_length: int
    matched_frameworks: list[str] | None = None
    matched_modes: list[str] | None = None
    matched_profiles: list[str] | None = None


@dataclass(frozen=True)
class BaselineMetrics:
    """Aggregated baseline metrics."""
    hook_name: str
    total_runs: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    stdev_ms: float


def time_hook(hook_func: Callable, hook_name: str, prompt: str) -> TimingResult:
    """Time a single hook execution with result extraction.

    Args:
        hook_func: Hook function to call (accepts HookContext, returns HookResult)
        hook_name: Name of the hook for logging
        prompt: Prompt text to pass to hook

    Returns:
        TimingResult with duration and extracted results
    """
    # Create hook context
    from UserPromptSubmit_modules.base import HookContext

    context = HookContext(
        prompt=prompt,
        data={
            "prompt": prompt,
            "session_id": "baseline-measurement",
            "terminal_id": "baseline",
        },
    )

    # Time the execution
    start = time.perf_counter()
    result = hook_func(context)
    end = time.perf_counter()

    duration_ms = (end - start) * 1000

    # Extract results
    matched_frameworks = None
    matched_modes = None
    matched_profiles = None

    if result and result.context:
        if isinstance(result.context, dict):
            # Check for cognitive framework matches
            injection = result.context.get("systemContext") or result.context.get("additionalContext", "")
            if injection and "[COG]" in injection:
                # Extract framework names from injection
                matched_frameworks = []
                for framework in [
                    "assumption_surfacing", "outcome_anchoring", "inversion_prompting",
                    "chestertons_fence", "calibrated_confidence", "socratic_decomposition",
                    "cynefin_classification", "hanlons_razor", "devils_advocate"
                ]:
                    if framework.replace("_", " ").title() in injection:
                        matched_frameworks.append(framework)

            # Check for reasoning mode
            if "[SEQ]" in injection or "[MAS]" in injection or "[2ST]" in injection:
                matched_modes = []
                if "[SEQ]" in injection:
                    matched_modes.append("sequential")
                if "[MAS]" in injection:
                    matched_modes.append("multi_agent")
                if "[2ST]" in injection:
                    matched_modes.append("two_stage")

    return TimingResult(
        hook_name=hook_name,
        duration_ms=duration_ms,
        prompt_length=len(prompt),
        matched_frameworks=matched_frameworks,
        matched_modes=matched_modes,
        matched_profiles=matched_profiles,
    )


def calculate_metrics(timings: list[TimingResult]) -> BaselineMetrics:
    """Calculate aggregated metrics from timing results.

    Args:
        timings: List of timing results

    Returns:
        BaselineMetrics with p50, p95, p99, mean, median, min, max, stdev
    """
    hook_name = timings[0].hook_name
    durations = [t.duration_ms for t in timings]

    return BaselineMetrics(
        hook_name=hook_name,
        total_runs=len(timings),
        p50_ms=statistics.quantiles(durations, n=2)[0] if len(durations) > 1 else durations[0],
        p95_ms=statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
        p99_ms=statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
        mean_ms=statistics.mean(durations),
        median_ms=statistics.median(durations),
        min_ms=min(durations),
        max_ms=max(durations),
        stdev_ms=statistics.stdev(durations) if len(durations) > 1 else 0.0,
    )


def measure_cognitive_enhancers() -> list[TimingResult]:
    """Measure cognitive_enhancers.py performance."""
    from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers

    timings = []
    for prompt in SAMPLE_PROMPTS:
        result = time_hook(cognitive_enhancers, "cognitive_enhancers", prompt)
        timings.append(result)
        print(f"  cognitive_enhancers: {result.duration_ms:.2f}ms (prompt: {prompt[:50]}...)")

    return timings


def measure_reasoning_mode_selector() -> list[TimingResult]:
    """Measure reasoning_mode_selector.py performance."""
    from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector

    timings = []
    for prompt in SAMPLE_PROMPTS:
        result = time_hook(reasoning_mode_selector, "reasoning_mode_selector", prompt)
        timings.append(result)
        print(f"  reasoning_mode_selector: {result.duration_ms:.2f}ms (prompt: {prompt[:50]}...)")

    return timings


def measure_think_trigger() -> list[TimingResult]:
    """Measure think_trigger.py performance."""
    from UserPromptSubmit_modules.think_trigger import think_trigger

    timings = []
    for prompt in SAMPLE_PROMPTS:
        result = time_hook(think_trigger, "think_trigger", prompt)
        timings.append(result)
        print(f"  think_trigger: {result.duration_ms:.2f}ms (prompt: {prompt[:50]}...)")

    return timings


def main():
    """Run baseline measurement and save results."""
    print("Measuring cognitive & reasoning hook performance baseline...")
    print()

    # Measure each system
    print("1. Measuring cognitive_enhancers.py...")
    cognitive_timings = measure_cognitive_enhancers()
    cognitive_metrics = calculate_metrics(cognitive_timings)
    print()

    print("2. Measuring reasoning_mode_selector.py...")
    reasoning_timings = measure_reasoning_mode_selector()
    reasoning_metrics = calculate_metrics(reasoning_timings)
    print()

    print("3. Measuring think_trigger.py...")
    think_timings = measure_think_trigger()
    think_metrics = calculate_metrics(think_timings)
    print()

    # Calculate aggregate metrics
    all_timings = cognitive_timings + reasoning_timings + think_timings
    aggregate_durations = [t.duration_ms for t in all_timings]

    # Build baseline JSON
    baseline = {
        "measurement_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_prompts_count": len(SAMPLE_PROMPTS),
        "total_measurements": len(all_timings),
        "systems": {
            "cognitive_enhancers": asdict(cognitive_metrics),
            "reasoning_mode_selector": asdict(reasoning_metrics),
            "think_trigger": asdict(think_metrics),
        },
        "aggregate": {
            "total_runs": len(all_timings),
            "p50_ms": statistics.quantiles(aggregate_durations, n=2)[0] if len(aggregate_durations) > 1 else aggregate_durations[0],
            "p95_ms": statistics.quantiles(aggregate_durations, n=20)[18] if len(aggregate_durations) > 1 else aggregate_durations[0],
            "p99_ms": statistics.quantiles(aggregate_durations, n=100)[98] if len(aggregate_durations) > 1 else aggregate_durations[0],
            "mean_ms": statistics.mean(aggregate_durations),
            "median_ms": statistics.median(aggregate_durations),
            "min_ms": min(aggregate_durations),
            "max_ms": max(aggregate_durations),
            "stdev_ms": statistics.stdev(aggregate_durations) if len(aggregate_durations) > 1 else 0.0,
        },
        "duplicate_analysis": {
            "notes": "All three systems analyze the same prompt independently",
            "estimated_overhead": "Current implementation runs all 3 systems sequentially",
            "expected_savings": "Unified detection could eliminate ~30% duplicate work",
        },
        "regression_threshold": {
            "description": "Any optimization should not exceed baseline + 20%",
            "threshold_ms": statistics.mean(aggregate_durations) * 1.2,
        },
        "target_optimization": {
            "description": "Target unified detection performance",
            "target_ms": statistics.mean(aggregate_durations) * 0.6,  # 40% reduction
        },
    }

    # Save baseline JSON
    baseline_dir = Path(__file__).resolve().parent
    baseline_file = baseline_dir / "current_performance_baseline.json"
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    print("=" * 60)
    print("BASELINE MEASUREMENT COMPLETE")
    print("=" * 60)
    print()
    print("Cognitive Enhancers:")
    print(f"  Mean: {cognitive_metrics.mean_ms:.2f}ms")
    print(f"  P95: {cognitive_metrics.p95_ms:.2f}ms")
    print(f"  P99: {cognitive_metrics.p99_ms:.2f}ms")
    print()
    print("Reasoning Mode Selector:")
    print(f"  Mean: {reasoning_metrics.mean_ms:.2f}ms")
    print(f"  P95: {reasoning_metrics.p95_ms:.2f}ms")
    print(f"  P99: {reasoning_metrics.p99_ms:.2f}ms")
    print()
    print("Think Trigger:")
    print(f"  Mean: {think_metrics.mean_ms:.2f}ms")
    print(f"  P95: {think_metrics.p95_ms:.2f}ms")
    print(f"  P99: {think_metrics.p99_ms:.2f}ms")
    print()
    print("Aggregate (all systems):")
    print(f"  Mean: {baseline['aggregate']['mean_ms']:.2f}ms")
    print(f"  P95: {baseline['aggregate']['p95_ms']:.2f}ms")
    print(f"  P99: {baseline['aggregate']['p99_ms']:.2f}ms")
    print()
    print(f"Baseline saved to: {baseline_file}")
    print()
    print("Regression threshold (baseline + 20%):")
    print(f"  {baseline['regression_threshold']['threshold_ms']:.2f}ms")
    print()
    print("Target optimization (40% reduction):")
    print(f"  {baseline['target_optimization']['target_ms']:.2f}ms")


if __name__ == "__main__":
    main()
