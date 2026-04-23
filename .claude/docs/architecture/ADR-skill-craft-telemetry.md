# ADR-{timestamp}: Production Telemetry for skill-craft Post-Run Validation

## Status
Proposed

## Context

skill-craft runs a 5-phase pipeline (DIAGNOSING → PLANNING → EXECUTING → EVALUATING → GATING) against target skills. After each run, it produces:

- `av_findings.json` — correctness findings
- `hook_findings.json`, `agent_findings.json`, `mcp_findings.json`, `runtime_findings.json` — review findings
- `cert_gate` — pass/fail outcome

**Problem:** None of this data is tracked across runs. A skill can "pass" skill-craft's gates but remain functionally degraded. No baseline exists to answer:

- Which eval cases now pass that previously failed?
- Which findings were closed vs deferred vs newly introduced?
- Did the skill's actual content semantically change (diff-based)?

## Decision

Add a telemetry layer to skill-craft that captures run history, computes delta vs baseline, and signals regression/improvement after each run.

### Architecture: Artifact-scoped JSON logs

Telemetry lives in `.claude/.artifacts/{terminal_id}/skill-craft/telemetry/{target_skill}/`:

```
run-{timestamp}.json   # Full run record (append-only history)
latest.json            # Most recent baseline (overwritten after each run)
delta.json             # Diff vs baseline (produced post-gating)
index.jsonl            # Run history index (one line per run)
```

### Baseline: Most recent successful run

On each run:
1. Before DIAGNOSING, check for `latest.json` for this target skill
2. If exists → compare current outputs against it
3. After GATING → overwrite `latest.json` with current run as new baseline

No baseline = first run = delta = full content (always "improved").

### Comparison thresholds

| Metric | Regression trigger | Improvement trigger |
|--------|-------------------|---------------------|
| Blockers | Any increase (0→1) | Any decrease |
| Highs | >2 increase | ≥2 decrease |
| Mediums | >5 increase | ≥3 decrease |
| Evals | Any newly failing | Any newly passing |

### Verdict logic

```
if blockers_delta > 0:                    → regression
elif blockers_delta < 0 or highs_delta < -1: → improved
else:                                         stable
```

## Key Design Decisions

### Decision 1: Artifact-scoped, not centralized

Artifact-scoped logs (per terminal_id + per target_skill) are isolated and survive session end. No external DB. Future aggregation script can combine if needed.

Rationale: Solo-dev environment. A full centralized store is over-engineering for the current scale.

### Decision 2: Baseline lives at target-skill level

`latest.json` is per target skill, not global. Running skill-craft on "av" vs "skill-craft" maintains separate baselines.

### Decision 3: Rollback exclusion

If EXECUTING triggers rollback, `latest.json` is NOT updated. The baseline stays as pre-execution state. User decides whether to re-run.

### Decision 4: Regression → immediate notification

If verdict = regression, send PushNotification to user summarizing the regression before exiting.

## Schema: Run Record (`run-{timestamp}.json`)

```json
{
  "run_id": "run-20260423T165052",
  "target_skill": "av",
  "target_path": "P:/.claude/skills/av",
  "started_at": "2026-04-23T16:50:52Z",
  "completed_at": "2026-04-23T16:55:12Z",
  "phase_sequence": ["diagnosing", "planning", "executing "evaluating", "gating"],
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
  "new_findings": ["av-021", "av-022"],
  "rollback_triggered": false
}
```

## Schema: Delta Record (`delta.json`)

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

## Schema: Index Entry (`index.jsonl`)

```json
{"run_id": "run-20260423T165052", "ts": "2026-04-23T16:55:12Z", "verdict": "improved", "target_skill": "av", "passed": true}
```

## Implementation: craft_telemetry_collector hook

```yaml
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

**Trigger condition:** skill-craft output contains "craft-done" OR phase=gating in CraftState.

**Flow:**
1. Read CraftState from state.json
2. Check for baseline (latest.json) for this target_skill
3. Compute delta using verdict logic above
4. Write run file + delta file + append to index
5. If verdict = regression → PushNotification(summary)
6. If rollback_triggered = false → overwrite latest.json

## Consequences

- **Positive:** Enables time-series analysis of skill health; catches regressions before they compound; builds institutional memory across sessions
- **Negative:** Adds write overhead (~50ms per run); requires sufficient disk for retention
- **Risk:** First-run baseline may be low-quality (skill was already broken before skill-craft ran) — mitigated by keeping first-run verdict as "baseline_only" not "improved"

## Retention Policy

Keep last 10 run files per target skill. Prune oldest on each run. latest.json and index.jsonl are not pruned.

## Verification

1. Run skill-craft on av (first run) → `verdict: "first_run"`, baseline written
2. Run skill-craft on av (second run) → `verdict: "stable|improved|regression"` computed, delta.json produced
3. Regression scenario: manually introduce blockers → run → PushNotification received

## Alternatives Considered

- **Centralized DB (CDS)**: Rejected — adds external dependency, schema migration, not solo-dev appropriate
- **Git-based telemetry**: Rejected — git history is not the right model for per-run JSON metrics
- **No delta tracking**: Rejected — without baseline comparison, "passes gates" is the only signal and it is insufficient
- **Separate Phase 6**: Rejected — telemetry is post-processing, not a pipeline phase. Runs after GATING, doesn't gate on regression (informational only)