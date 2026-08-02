---
title: "Structural fix for Rhai workflow launch-time snapshot staleness"
current_session_id: 019fbf26-08f9-7f12-ace1-15ce7541c140
produced_at: 2026-08-02
status: OPEN
handoff_type: implementation
source_session: 019fbf26
accurate_as_of_head: unknown (capture-time artifact)
tags: [rhai, workflow, launch-time, snapshot, structural-fix, close-check, dispatch]
related_concepts:
  - P:/.data/wiki/concepts/rhai-workflow-launch-time-snapshot-staleness.md
  - P:/.data/wiki/concepts/rhai-workflow-smoke-check-misses-function-call-bugs.md
  - P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
---

# Structural fix for Rhai workflow launch-time snapshot staleness

## Objective

Eliminate the launch-time snapshot staleness failure mode by changing the Rhai workflow dispatcher to re-read the canonical `.rhai` file at every launch, instead of snapshotting it at dispatch time. This makes the recovery pattern (relaunch with `-N` suffix) unnecessary in the common case.

## Problem statement

When a Rhai workflow crashes on a runtime error (e.g., `Function not found: substr`), fixing the canonical `~/.grok/workflows/<name>.rhai` file is necessary but not sufficient. The launch-time snapshot — the script content captured when the workflow is dispatched — can still contain the broken version. The operator must currently relaunch with a `-N` suffix to force a fresh snapshot.

Empirical receipt: session 019fbf26, close-check workflow crashed at sweep+synthesis completion (~20m49s) on `substr()` at line 403:62. Canonical file was already fixed. Relaunch as `close-check-2` succeeded in 21m54s. Source: `P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md` line 24-25. Background concept: `P:/.data/wiki/concepts/rhai-workflow-launch-time-snapshot-staleness.md`.

## Why the current snapshot behavior exists (inference)

The snapshot is likely there to support:
1. **Reproducibility** — if the canonical file changes mid-workflow, the in-flight run should not see the new code
2. **Crash diagnostics** — the journal contains the exact script that ran
3. **Atomicity** — the workflow run gets a stable view of the script for its lifetime

These are legitimate concerns. The fix needs to preserve them while letting the NEXT launch pick up the canonical file.

## Proposed fix

**Change the dispatcher to re-read the canonical file at every launch**, but keep the in-flight snapshot for the duration of the workflow run. This separates two concerns:
- **At-launch-time**: the file on disk is the source of truth for what runs
- **During-run**: the snapshot is immutable for journal/diagnostic purposes

Implementation sketch:

```python
# Old behavior: snapshot at dispatch
workflow_state = {
    "name": name,
    "script_snapshot": read_canonical_file(name),  # frozen at dispatch
    ...
}

# New behavior: snapshot at dispatch, but re-read canonical if name has -N suffix
workflow_state = {
    "name": name,
    "script_snapshot": read_canonical_file(name),  # re-read on every launch
    "snapshot_at": datetime.now(),  # for journal diagnostics
    ...
}
```

If the snapshot is reread at every launch, the `-N` suffix becomes unnecessary — the next launch of `close-check` (no suffix) would pick up the fixed canonical file. The suffix becomes a debugging affordance (force a fresh run state) rather than a recovery pattern.

## Acceptance criteria

1. **Test: fix canonical file, relaunch with same name.** Workflow should pick up the fixed file on relaunch. Verify by introducing a known-good edit (e.g., a comment line) and confirming the journal reflects the new edit.

2. **Test: in-flight run keeps its snapshot.** Start a workflow, edit the canonical file mid-run, verify the in-flight journal still references the old snapshot. The journal must not show the in-flight edit.

3. **Test: failed workflow's snapshot persists for postmortem.** A failed launch should leave the broken snapshot in the workflow's journal directory so the operator can inspect what actually ran.

4. **No regression in smoke-check behavior.** `validate_only: true` should still validate the canonical file at validation time, not the launch-time snapshot.

## Out of scope

- Changing the smoke-check semantics (covered by `rhai-workflow-smoke-check-misses-function-call-bugs`)
- Fixing the `close_runner.py` JSON-arg parsing bug (covered by `close-runner-json-arg-parsing-bug` — distinct bug class, same failure signature)
- Removing the `-N` suffix convention (keep it as a debugging affordance)

## Files to investigate (priority order)

1. `~/.grok/workflows/` — where the workflow dispatcher and canonical files live
2. `~/.grok/skills/` — likely contains the workflow skill that handles dispatch
3. Any `dispatcher.py`, `workflow_runner.py`, or `rhai_runner.py` script in `~/.grok/`

## Estimate

- **Investigation**: 30 min (locate the dispatch path, confirm the snapshot behavior)
- **Fix**: 1-2 hours (change snapshot read time, add a test)
- **Validation**: 30 min (run the acceptance tests above)

Total: 2-3 hours. Low risk if the snapshot is only used for journal/diagnostic purposes; higher risk if other code depends on the snapshot being immutable across launches.

## Owner

Whoever runs the next workflow dispatch investigation (operator or grok). This handoff flags it for explicit assignment rather than leaving it to drift.

## Read-first list

1. `P:/.data/wiki/concepts/rhai-workflow-launch-time-snapshot-staleness.md` — the failure mode (with empirical receipts)
2. `P:/.data/wiki/concepts/rhai-workflow-smoke-check-misses-function-call-bugs.md` — adjacent failure mode (parse vs behavior, NOT snapshot staleness)
3. `P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md` line 24-25 — the empirical observation

## Status

OPEN. Not started. Investigation required before implementation (location of the dispatcher is not currently known to the agent that produced this handoff).
