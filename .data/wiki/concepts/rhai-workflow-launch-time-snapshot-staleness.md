---
title: "Rhai workflow launch-time snapshot can be stale even when the canonical file is fixed"
created: 2026-08-01
source: session-019fbf26-08f9-7f12-ace1-15ce7541c140
tags: [rhai, workflow, launch-time, snapshot, staleness, recovery, close-check, grok-build]
summary: >
  When a workflow crashes on a Rhai runtime error, fixing the canonical .rhai
  file is necessary but not sufficient. The launch-time snapshot can still
  contain the broken script, causing the same crash to recur on the next launch.
  The recovery is to relaunch with a `-2` (or `-N`) suffix; the canonical fix
  takes effect on the NEXT launch only. This is a distinct failure mode from
  the smoke-check parse-vs-behavior gap covered by [[rhai-workflow-smoke-check-misses-function-call-bugs]].
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - ~/.grok/workflows/close-check.rhai (canonical workflow)
  - C:/Users/brsth/.grok/sessions/P%3A%5C/019fbf26-08f9-7f12-ace1-15ce7541c140/workflows/wf_019fbf2811707d33a0da1153628f6012/state.json (failed launch)
  - C:/Users/brsth/.grok/sessions/P%3A%5C/019fbf26-08f9-7f12-ace1-15ce7541c140/workflows/wf_019fbf3c872070d3b0bba44facdfd293/state.json (recovered launch)
  - P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md (line 24-25)
relations:
  - target: wiki/concepts/rhai-workflow-smoke-check-misses-function-call-bugs.md
    type: parallel — smoke check covers parse-time gap, launch-time snapshot covers deploy-time gap
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related — close-check is the workflow that hit this in session 019fbf26
  - target: wiki/concepts/close-runner-json-arg-parsing-bug.md
    type: parallel — distinct bug class (boundary type confusion vs launch-time staleness) but same failure signature (close-gates gate failure with zero content)
---

# Rhai workflow launch-time snapshot can be stale even when the canonical file is fixed

## The failure mode

When a workflow launch fails with a Rhai runtime error such as `Function not found: substr (&str | ImmutableString | String, i64, i64) (line 403, position 62)`, the operator typically:

1. Inspects the canonical `.rhai` file
2. Confirms the bug is there (or has been fixed since the last launch)
3. Edits the canonical file to fix the bug
4. Relaunches the workflow

**Step 3 alone is not enough.** The launch-time snapshot — the script content captured at workflow dispatch time — can still contain the broken version. The fix to the canonical file does not propagate until the NEXT launch.

## Empirical observation (session 019fbf26)

In session `019fbf26-08f9-7f12-ace1-15ce7541c140`, the close-check workflow was launched with name `close-check`:

- **First launch** (wf_019fbf2811707d33a0da1153628f6012): crashed at sweep+synthesis completion (~20m49s) when the remediation phase hit `substr()` at line 403:62 of the launch-time snapshot. Workflow state: failed.
- **Canonical file fix:** the `~/.grok/workflows/close-check.rhai` was already fixed (the smoke-check gap had been closed in a prior session, concept `rhai-workflow-smoke-check-misses-function-call-bugs`).
- **Relaunch as `close-check-2`** (wf_019fbf3c872070d3b0bba44facdfd293): completed successfully in 21m54s.

The recovered launch worked because the `name` parameter (`close-check-2`) triggered a fresh dispatch with a fresh snapshot from the canonical file. The launch-time snapshot of the failed launch was discarded along with the failed workflow run.

## Recovery pattern

When a workflow crashes on a known Rhai runtime error:

1. **Confirm the canonical file is fixed.** If it isn't, fix it and DO NOT relaunch yet — wait for the next launch cycle.
2. **Relaunch with a `-N` suffix on the name.** This forces a new dispatch with a fresh launch-time snapshot. The failed workflow run and its snapshot are kept as a journal entry for postmortem; the new launch reads from the canonical file.
3. **Verify by checking the new workflow's journal.** The new launch should NOT reproduce the bug.

If the new launch reproduces the bug, the canonical file is not actually fixed — go back to step 1.

## Why this is distinct from the smoke-check gap

| Failure mode | When | What's wrong | Fix surface |
|---|---|---|---|
| Smoke check parse-vs-behavior (concept: `rhai-workflow-smoke-check-misses-function-call-bugs`) | Workflow author edits .rhai, runs `validate_only: true`, trusts it as behavioral validation | Smoke check passes but runtime fails | Add stricter smoke checks (function-call validation, inline-array rejection) |
| Launch-time snapshot staleness (this concept) | Operator fixes canonical file after a crash, expects relaunch to pick up the fix | Launch-time snapshot still has broken script; relaunch re-uses it | Relaunch with `-N` suffix to force fresh snapshot |

The two failures are often confused because they have similar symptoms (same runtime error on relaunch), but the fix surface is different.

## Open question (improvement stream)

The handoff `P:/docs/handoffs/workflow-launch-time-snapshot-staleness-20260802/HANDOFF.md` (if it exists, see /handoff output for session 019fbf26) proposes a structural fix: the workflow dispatcher should re-read the canonical file at every launch, not snapshot at the start of dispatch. Until that fix lands, the `-N` suffix pattern is the standard recovery.

## Falsifier

If relaunching with the same name (no suffix) ALSO picks up the canonical fix, then the launch-time snapshot is not actually cached — this concept describes the wrong failure mode. Verify by running the same workflow twice with a known-good canonical file; if the second run reads the file fresh, the snapshot staleness hypothesis is wrong.

## Receipts

- `P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md` line 24-25: "Launched close-check workflow — first run crashed on Rhai `substr()` bug at line 403 after 20m49s. Fixed: canonical workflow file was already fixed; the bug was in the launch-time snapshot. Relaunched as `close-check-2` — completed successfully in 21m54s"
- `C:/Users/brsth/.grok/sessions/P%3A%5C/019fbf26-08f9-7f12-ace1-15ce7541c140/workflows/wf_019fbf2811707d33a0da1153628f6012/state.json` — first launch, status: failed
- `C:/Users/brsth/.grok/sessions/P%3A%5C/019fbf26-08f9-7f12-ace1-15ce7541c140/workflows/wf_019fbf3c872070d3b0bba44facdfd293/state.json` — second launch with -2 suffix, status: complete
