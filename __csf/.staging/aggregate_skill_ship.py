#!/usr/bin/env python3
"""Aggregate skill-ship iteration-1 results manually."""

import json
from pathlib import Path
from datetime import datetime, timezone

workspace = Path(r"P:\.claude\skills\skill-ship-workspace\iteration-1")

results = {}

for eval_dir in sorted(workspace.glob("eval-*")):
    eval_name = eval_dir.name  # e.g. "eval-0"
    eval_id = int(eval_name.split("-")[1])

    for config_dir in sorted(eval_dir.iterdir()):
        if not config_dir.is_dir():
            continue
        config = config_dir.name  # "skill-ship" or "baseline"
        if config not in results:
            results[config] = []

        grading_file = config_dir / "grading.json"
        timing_file = config_dir / "timing.json"

        if grading_file.exists():
            with open(grading_file) as f:
                grading = json.load(f)
        else:
            grading = {"summary": {}, "expectations": [], "timing": {}}

        timing_data = {}
        if timing_file.exists():
            with open(timing_file) as f:
                timing_data = json.load(f)

        summary = grading.get("summary", {})
        timing = grading.get("timing", {})

        # Extract pass_rate - handle numeric, string, and fraction formats
        pass_rate = summary.get("pass_rate", 0.0)
        if isinstance(pass_rate, str):
            if "/" in pass_rate:
                parts = pass_rate.split("/")
                pass_rate = int(parts[0]) / int(parts[1]) if parts[1] != "0" else 0.0
            else:
                try:
                    pass_rate = float(pass_rate)
                except ValueError:
                    pass_rate = 0.0

        result = {
            "eval_id": eval_id,
            "run_number": 1,
            "pass_rate": pass_rate,
            "passed": summary.get("passed_count", summary.get("passed", 0)),
            "failed": summary.get("total_count", summary.get("failed", 0)),
            "total": summary.get("total_count", summary.get("total", 0)),
            "time_seconds": timing.get(
                "total_duration_seconds", timing_data.get("total_duration_seconds", 0.0)
            ),
            "tokens": timing.get("total_tokens", timing_data.get("total_tokens", 0)),
            "expectations": grading.get("expectations", []),
            "notes": [],
        }
        results[config].append(result)

# Build runs array
runs = []
for config in ["skill-ship", "baseline"]:
    for r in results.get(config, []):
        runs.append(
            {
                "eval_id": r["eval_id"],
                "configuration": config,
                "run_number": r["run_number"],
                "result": {
                    "pass_rate": r["pass_rate"],
                    "passed": r["passed"],
                    "failed": r["failed"],
                    "total": r["total"],
                    "time_seconds": r["time_seconds"],
                    "tokens": r["tokens"],
                    "tool_calls": 0,
                    "errors": 0,
                },
                "expectations": r["expectations"],
                "notes": r["notes"],
            }
        )


# Compute summary stats
def calc_stats(values):
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    stddev = (sum((x - mean) ** 2 for x in values) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


run_summary = {}
for config in ["skill-ship", "baseline"]:
    runs_config = results.get(config, [])
    if not runs_config:
        run_summary[config] = {
            "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
            "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
            "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
        }
    else:
        prs = [r["pass_rate"] for r in runs_config]
        times = [r["time_seconds"] for r in runs_config]
        tokens = [r["tokens"] for r in runs_config]
        run_summary[config] = {
            "pass_rate": calc_stats(prs),
            "time_seconds": calc_stats(times),
            "tokens": calc_stats(tokens),
        }

# Delta
delta_pr = (
    run_summary["skill-ship"]["pass_rate"]["mean"]
    - run_summary["baseline"]["pass_rate"]["mean"]
)
delta_time = (
    run_summary["skill-ship"]["time_seconds"]["mean"]
    - run_summary["baseline"]["time_seconds"]["mean"]
)
delta_tokens = (
    run_summary["skill-ship"]["tokens"]["mean"]
    - run_summary["baseline"]["tokens"]["mean"]
)
run_summary["delta"] = {
    "pass_rate": f"{delta_pr:+.2f}",
    "time_seconds": f"{delta_time:+.1f}",
    "tokens": f"{delta_tokens:+.0f}",
}

benchmark = {
    "metadata": {
        "skill_name": "skill-ship",
        "skill_path": "P:\\.claude\\skills\\skill-ship",
        "executor_model": "claude-opus-4-6",
        "analyzer_model": "claude-opus-4-6",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evals_run": [0, 1, 2, 3, 4, 5],
        "runs_per_configuration": 1,
    },
    "runs": runs,
    "run_summary": run_summary,
    "notes": [],
}

output = workspace / "benchmark.json"
with open(output, "w") as f:
    json.dump(benchmark, f, indent=2)
print(f"Generated: {output}")

# Print summary
for config in ["skill-ship", "baseline"]:
    pr = run_summary[config]["pass_rate"]["mean"]
    t = run_summary[config]["time_seconds"]["mean"]
    tk = run_summary[config]["tokens"]["mean"]
    label = config.replace("_", " ").title()
    print(f"  {label}: pass_rate={pr:.2f}, time={t:.1f}s, tokens={tk:.0f}")
print(
    f"  Delta pass_rate: {delta_pr:+.2f}, time: {delta_time:+.1f}s, tokens: {delta_tokens:+.0f}"
)
