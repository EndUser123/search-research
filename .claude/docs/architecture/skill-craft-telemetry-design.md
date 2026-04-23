# Design: Production Telemetry for skill-craft Post-Run Validation

## Problem Statement

skill-craft cannot currently measure whether a target skill actually improved after running. It only verifies that its own fidelity gates passed. This creates a gap:

- A skill can "pass" skill-craft's gates but remain functionally degraded
- No baseline exists to compare before vs. after health metrics
- Eval cases pass/fail are tracked per run but not as a time series
- Findings closed vs. deferred is not captured in a durable way

## What We Want to Measure

| Metric | Description | Source |
|--------|-------------|--------|
| Eval case delta | Which cases now pass that previously failed | `eval_sets/default.json` results per run |
| Findings closure rate | Blockers/highs/mediums resolved vs. left open | Findings JSON per phase |
| Semantic delta | Did the skill's actual content change? (diff-based) | Git diff of target skill |
| Phase duration | How long each phase takes (performance signal) | CraftState timestamps |
| Gate outcome | Passed/failed per phase and overall | cert_gate output |

## Architectural Decisions

### Decision 1: Where does telemetry live?

**Option A: Centralized Data Store (CDS)**
- Pros: Unified query, cross-run analysis, trend detection
- Cons: Adds external dependency, schema migration complexity

**Option B: Artifact-scoped JSON logs in `.claude/.artifacts/{terminal_id}/skill-craft/telemetry/`
- Pros: Isolated per run, no external dependency, survives session end
- Cons: Harder to query across runs, no aggregation built-in

**Decision: Option B (artifact-scoped) with optional central index**

Rationale: Solo-dev environment, no external DB. Artifact-scoped logs are sufficient for per-run validation and can be manually reviewed or aggregated via a future script. A lightweight index file (`telemetry_index.jsonl`) in the artifacts dir can track run history without a full DB.

### Decision 2: How is baseline established?

**Baseline = most recent successful run of skill-craft on the same target skill.**

On each run:
1. Before DIAGNOSING, check for existing `.claude/.artifacts/{terminal_id}/skill-craft/telemetry/{target_skill_name}/latest.json`
2. If exists, treat as baseline. Compare current run outputs against baseline.
3. After GATING, write new baseline (overwrite latest.json)

**No baseline = first run. First run is always "improved" (delta = full content).**

### Decision 3: What is the comparison threshold?

Three levels of delta:

| Level | Trigger | Signal |
|-------|---------|--------|
| **Regression** | Blockers increased, or critical finding count increased | Immediate user signal |
| **Stable** | No meaningful change in findings count/severity | Normal state |
| **Improved** | Blockers decreased OR mediums decreased OR new good evals | Celebrated but not gated |

**Threshold for "meaningful change":**
- Blockers: any change (0 → 1 is a regression)
- Highs: ≥2 change
- Mediums: ≥3 change
- Evals: any newly passing case counts as improvement

## Proposed Telemetry Artifact Structure

```
.claude/.artifacts/{terminal_id}/skill-craft/telemetry/
{target_skill_name}/
  latest.json          # Current baseline (overwritten after each run)
  run-{timestamp}.json  # This run's full results (append-only history)
  delta.json           # Diff vs baseline (produced after GATING)
  index.jsonl          # Run history index (one line per run, timestamp + outcome)
```

### `run-{timestamp}.json` schema:

```json
{
  "run_id": "run-20260423T165052",
  "target_skill": "av",
  "target_path": "P:/.claude/skills/av",
  "started_at": "2026-04-23T16:50:52Z",
  "completed_at": "2026-04-23T16:55:12Z",
  "phase_sequence": ["diagnosing", "planning", "executing", "evaluating", "gating"],
  "phase_durations_ms": {
    "diagnosing": 45230,
    "planning": 12340,
    "executing": 234560,
    "evaluating": 8900,
    "gating": 3400
  },
  "eval_results": {
    "total": 21,
    "passed": 18,
    "failed": 3,
    "newly_passing": ["eval_04", "eval_11"],
    "newly_failing": []
  },
  "findings_summary": {
    "blockers": { "before": 3, "after": 1 },
    "highs": { "before": 5, "after": 2 },
    "mediums": { "before": 8, "after": 4 },
    "minors": { "before": 12, "after": 9 }
  },
  "cert_gate": {
    "passed": true,
    "artifact_check": { "passed": true, "missing": [] },
    "diff_check": { "passed": true, "warnings": [], "delta_lines": 847 }
  },
  "closed_findings": ["av-001", "av-004", "av-012"],
  "deferred_findings": ["av-002", "av-009"],
  "new_findings": ["av-021", "av-022"]
}
```

### `delta.json` schema:

```json
{
  "run_id": "run-20260423T165052",
  "baseline_run_id": "run-20260420T093412",
  "delta_age_hours": 72.4,
  "eval_delta": {
    "gained": ["eval_04", "eval_11"],
    "lost": [],
    "unchanged": 19
  },
  "findings_delta": {
    "blockers": -2,
    "highs": -3,
    "mediums": -4,
    "minors": -3
  },
  "verdict": "improved",
  "regression_signal": null
}
```

## Implementation: Post-Run Hook

Add a `craft_telemetry_collector` PostToolUse hook:

```python
hooks:
  - id: craft_telemetry_collector
    type: PostToolUse
    matcher: "skill-craft.*gating"
    description: >
      After Phase 5 GATING completes, collects run metrics,
      computes delta vs baseline, writes telemetry artifacts.
    artifacts:
      telemetry_dir: ".claude/.artifacts/{terminal_id}/skill-craft/telemetry/{target_skill}/"
      run_file: "run-{timestamp}.json"
      delta_file: "delta.json"
      baseline_file: "latest.json"
      index_file: "index.jsonl"
```

**Behavior:**
1. On match (skill-craft output contains "craft-done" or phase=gating complete):
2. Read CraftState from state.json
3. Compute delta vs baseline (if exists)
4. Write run file + delta file + update index
5. Overwrite latest.json with current run as new baseline

## Comparison Logic

```python
def compute_delta(current: RunRecord, baseline: RunRecord | None) -> Delta:
    if baseline is None:
        return Delta(verdict="first_run", regression_signal=None)

    blockers_delta = current.findings_summary.blockers.after - baseline.findings_summary.blockers.after
    highs_delta = current.findings_summary.highs.after - baseline.findings_summary.highs.after

    regression = blockers_delta > 0 or (highs_delta > 2)

    if blockers_delta < 0 or (highs_delta < 0 and blockers_delta == 0):
        verdict = "improved"
    elif regression:
        verdict = "regression"
    else:
        verdict = "stable"

    return Delta(
        blockers_delta=blockers_delta,
        highs_delta=highs_delta,
        verdict=verdict,
        regression_signal="blockers_increased" if blockers_delta > 0 else None
    )
```

## Rollback Integration

If EXECUTING phase triggers rollback (due to regression signal), the telemetry collector should:
1. Note the rollback in the run record
2. NOT update latest.json (baseline stays as pre-execution state)
3. Write run file with `rollback_triggered: true`
4. User can then decide whether to re-run or accept the baseline

## Open Questions

1. **Retention policy**: How many historical run files to keep? Suggest: last 10 runs per target skill, prune oldest.
2. **Cross-terminal aggregation**: Should runs from different terminal_ids be comparable? Currently no — baseline is per-terminal.
3. **Alerting**: Should regression trigger a user-visible notification? Yes — PushNotification with summary.