---
title: "close-runner verdicts go stale when later phases run additional checks"
created: 2026-08-01
source: session-019f9a89 (close-check post-compaction sweep)
tags: [close-runner, close-check, phase-3-remediate, verdict-staleness, evidence-timestamp, post-compaction-invalidation, capture]
agent: grok
host: grok
cognitive_load: 3
verification: observed
summary: >
  close-check Phase 3 (Remediate) runs /capture, /friction, /handoff, /trace,
  and /wiki unconditionally. When Phase 1 or Phase 2 produces a verdict about
  one of those checks (e.g. "no /trace report" or "0 friction signals"), that
  verdict becomes stale the moment Phase 3 runs the check. A pre-close-report
  or pre-compaction close-run's verdicts are NOT trustworthy after a
  post-compaction sweep re-runs the same workflow. The structural fix is
  timestamping verdicts and re-running the close-check end-to-end before
  trusting any verdict about post-compaction work.
sources:
  - P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md
  - P:/.data/wiki/concepts/close-check-invokes-capture.md
  - P:/.data/wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md
  - P:/.data/wiki/concepts/compaction-inherited-diagnosis-unverified-propagation.md
relations:
  - target: wiki/concepts/close-check-invokes-capture.md
    type: extends — close-check Phase 3 invocation is the structural cause of verdict staleness
  - target: wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md
    type: extends — Phase 4 finalization is downstream of the staleness issue
  - target: wiki/concepts/compaction-inherited-diagnosis-unverified-propagation.md
    type: refines — that concept covers claims ARRIVING from compaction; this one covers verdicts MADE before compaction becoming invalid
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: related — both about scanner evidence boundaries becoming stale; this one is about phase boundaries
  - target: wiki/concepts/close-runner-windows-path-json-stringification-bug.md
    type: related — different close-runner failure mode (crash vs verdict staleness)
---

# close-runner verdicts go stale when later phases run additional checks

## Decision context

**Why this knowledge was needed:** session 019f9a89 ran close-check, which produced a `BLOCKED` verdict (scanner execution blocked, evidence ledger NOT GENERATED, close gates NOT ASSESSED). The session was then compacted. During the post-compaction sweep, close-check was re-invoked, and **Phase 3 (Remediate)** ran `/capture`, `/friction`, `/handoff`, `/trace`, and `/wiki` as auto-act subagents. The pre-compaction close-report's prior verdict that "no /trace report" was present became stale the moment `/trace` ran in Phase 3.

The operator's evidence-packet explicitly noted: "Pre-close-report's prior 'no /trace report' verdict is stale: /trace ran during the post-compaction sweep, not the prior pre-close-run."

This is a structurally new failure mode: **close-check is a multi-phase workflow where Phase 3 changes the evidence base that Phase 1/2 verdicts refer to**. Pre-Phase-3 verdicts about Phase-3 checks are not just stale — they are *guaranteed* stale by construction.

## The mechanism

### close-check's phase model (from `close-check-finalize-phase-make-blocking-unnecessary.md`)

```
Phase 1: Sweep        3 agents detect issues (git, harvest, gates, health, fmea, friction, coverage)
Phase 2: Synthesize   classify findings, produce verdict
Phase 3: Remediate    run /capture, /friction, /handoff, /trace, /wiki unconditionally
Phase 4: Finalize     commit artifacts, clean temp files, refresh index, emit operator-only report
```

### Why verdicts go stale

Phase 3 is **unconditional**. It runs `/trace` regardless of whether Phase 1 reported "no /trace report" — because Phase 3's job is to ensure those checks *did* happen, not to skip them based on prior phase reports.

This means: **a verdict about whether `/trace` ran is stale the instant Phase 3 runs.** Phase 1/2 verdicts about Phase-3-managed artifacts are by construction invalidated by Phase 3 itself.

### Three properties that produce this pattern

1. **Phase 3 is unconditional auto-act.** It runs even when Phase 2 has findings that "look complete."
2. **Phase 3 produces durable artifacts** (wiki concepts, handoffs, trace reports, friction reports, capture reports). The pre-Phase-3 absence of these artifacts is *evidence* that Phase 3 hasn't run yet — but the *next* invocation of close-check will produce them, invalidating the prior "absent" verdict.
3. **close-check verdicts are not timestamped in a way that surfaces this.** A reader of an old pre-close-report sees "no /trace report" and has no way to know whether the report was produced *after* the verdict (because close-check ran Phase 3) or *before* (because close-check never got to Phase 3).

## Worked example — session 019f9a89

| Phase | Pre-compaction close-run | Post-compaction sweep |
|-------|--------------------------|------------------------|
| Phase 1 | Sweep blocked: scanner crashed/returned blocked. Verdict: "no /trace report" | Sweep runs and reports 26+ handoff findings, 218 open handoffs |
| Phase 2 | Synthesize: BLOCKED (evidence ledger NOT GENERATED) | Synthesize: re-runs the same workflow with different output |
| Phase 3 | Did NOT run (Phase 2 returned BLOCKED) | Runs /capture, /friction, /handoff, /trace, /wiki as auto-act subagents |
| Phase 4 | Did NOT run | Finalizes: commits artifacts |

The pre-compaction "no /trace report" verdict was true at the time — but became false the instant the post-compaction sweep ran Phase 3. The receipt chain shows `/trace` was invoked (turn 163, `read_file of trace/SKILL.md`) AFTER the pre-compaction verdict was made. A future reader of the pre-compaction report cannot distinguish "verdict was accurate when made" from "verdict is wrong now."

## How to detect this pattern

**When reading a pre-close report:**

1. Find the verdict timestamp (if present). Compare to the timestamp of any Phase-3-managed artifact the report references (trace reports, friction reports, wiki concepts from `/wiki auto`).
2. If the artifact timestamp is newer than the verdict, the verdict is stale.
3. If no timestamp is present, assume the verdict is stale unless you can verify the artifact was NOT produced by a later close-check invocation.

**When writing a pre-close verdict:**

1. Always include the workflow phase that produced it (Phase 1 / Phase 2 / Phase 3 / Phase 4).
2. State explicitly which checks the verdict covers and which are deferred to later phases.
3. Note in the verdict text: "Phase 3 not yet run as of this verdict — re-run after Phase 3."

**When running close-check end-to-end:**

1. Run all four phases in one invocation. Do not stop after Phase 1/2.
2. Trust only verdicts from the most recent end-to-end run.

## The structural fix (proposed)

**Timestamped verdict receipts**: close-check Phase 2 should emit a verdict with `produced_at: <ISO timestamp>` and `covers_phases: [1, 2]` in its JSON output. Phase 4's finalize report should re-emit the verdict with `produced_at: <ISO timestamp>` and `covers_phases: [1, 2, 3, 4]`. A consumer reading an old verdict can compare `produced_at` against the latest close-check invocation's `produced_at` to detect staleness.

**Phase-aware verdict schema**: each verdict should declare which phases it depends on. A "no /trace report" verdict should carry `depends_on: [phase_3]`, and a stale-detector can refuse to trust it after Phase 3 has run.

**End-to-end re-run rule**: when close-check is invoked, do NOT trust any prior close-run's verdict about Phase-3-managed artifacts. Always re-run end-to-end.

These are structural fixes (require close-check schema changes). The behavioral fix (always re-run, never trust prior verdicts) works without schema changes but is not mechanical.

## What this is NOT

- **Not the same as `close-scanner-verification-gap-stale-read`**. That concept covers evidence invisibility (parent transcript vs child transcripts). This concept covers phase-evidence invalidation (Phase 3 changes the evidence Phase 1/2 refer to).
- **Not the same as `compaction-inherited-diagnosis-unverified-propagation`**. That concept covers claims ARRIVING from compaction without verification receipts. This concept covers verdicts MADE before compaction becoming stale because post-compaction work ran additional checks.
- **Not a bug in close-check.** The multi-phase design is intentional. The staleness is a property of the design, not a defect.

## How a cold-start LLM should read this

When a close-runner verdict says "no /trace report" or "no /capture" or "0 friction signals":

1. **Check whether Phase 3 has run** for that session. If yes, the verdict is stale.
2. **Read the most recent Phase 4 finalization report** (if present) for the actual state of Phase-3-managed artifacts.
3. **Do not propagate the verdict** as a current-state claim without verifying Phase 3 has NOT run.

```powershell
# Check whether Phase 3 has run by looking for Phase-3 artifacts
Get-ChildItem P:\.artifacts\<terminal>\gro-capture\ -Directory -ErrorAction SilentlyContinue
Get-ChildItem P:\.artifacts\<terminal>\gro-trace\ -Directory -ErrorAction SilentlyContinue
# If these exist, Phase 3 ran, and any pre-Phase-3 verdict about these is stale.
```

## Falsifier

This concept is wrong if:

- **Phase 3 is no longer unconditional** — if Phase 3 only runs when Phase 2 reports "needs more checks," then verdicts about Phase-3 artifacts are valid as long as Phase 2 didn't report "needs more checks."
- **Verdicts already carry phase-dependency metadata** that consumers can use to detect staleness — in that case the structural fix is already shipped and this concept is documentation-only.
- **The close-check workflow is redesigned as a single-phase pipeline** — then there are no phase boundaries and staleness cannot occur.
- **No session has ever re-run close-check after a prior close-check produced verdicts** — in that case the pattern is theoretical, not observed.

## Receipts

- Session 019f9a89 evidence packet (pre-packed): "Pre-close-report's prior 'no /trace report' verdict is stale: /trace ran during the post-compaction sweep, not the prior pre-close-run."
- Session 019f9a89 evidence packet (lifecycle-skill-coverage): "turn 163 read_file of trace/SKILL.md (operator-invoked '/trace' on skills + workflows)" — the timestamped evidence that /trace ran during the post-compaction sweep.
- P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md — the close-check Phase 4 build session that defined the four-phase model.
- P:/.data/wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md — the source of the four-phase definition (Phase 1 sweep, Phase 2 synthesize, Phase 3 remediate, Phase 4 finalize).
- P:/.data/wiki/concepts/close-check-invokes-capture.md — confirms Phase 3 runs `/capture`, `/friction`, `/handoff`, `/trace`, `/wiki` unconditionally.

## What this means for our workspace

1. **The close-check verdict schema should add `produced_at` and `covers_phases` fields.** This is a one-PR change to close-check Phase 2's JSON output and Phase 4's finalize report. Without these fields, every future session that reads a pre-Phase-3 verdict risks propagating stale information.

2. **The `/close-check` skill should refuse to consume pre-Phase-3 verdicts as current-state claims.** A simple rule in the SKILL.md: "If reading a verdict about /trace, /capture, /friction, /handoff, or /wiki, verify Phase 3 ran AFTER the verdict timestamp."

3. **End-to-end re-run is the safe default.** When in doubt, re-run close-check end-to-end. Phase 1+2+3+4 in a single invocation produces trustworthy verdicts.

4. **The `/wiki` concept for the close-check pipeline should link to this concept.** Any future close-check documentation should reference verdict staleness as a known design property.

## Auto-related

- [[skill-graph]]
- [[close-authority-state-machine-design]]
- [[intg2-resolved-gate-state-set-needs-llm-check]]
- [[close-check-finalize-phase-make-blocking-unnecessary]]
- [[close-scanner-verification-gap-stale-read]]

