---
title: "/trace skill execution gap — critical code shipped without trace-through"
created: 2026-08-01
source: session-019fa8f8-7e86-77f0-8e81-a7609f3c8b14
tags: [trace, lifecycle-skills, execution-gap, critical-code, coverage-gap, observation-vs-invocation]
agent: grok
host: grok
cognitive_load: 3
verification: observed
summary: >
  /trace is referenced, mentioned in workflow docs, and listed as a
  lifecycle skill in close-check Phase 3, but it does NOT reliably fire
  on critical code. Two consecutive sessions (wf_019fbf03 on 2026-07-31,
  session 019fa8f8 on 2026-08-01) shipped critical files with no trace
  artifact. /aar evidence is strong (preprocessor packet + report file);
  /behave evidence is thin (loaded but no behavior incident packet
  traced); /trace evidence is absent despite the skill being invoked
  conceptually 9+ times across the transcript. The pattern is not
  "agent forgot" — it is structural: /trace is invoked by the model's
  reasoning under behavioral rules with no visible-output contract.
relations:
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: extends
  - target: wiki/concepts/close-check-invokes-capture.md
    type: related
  - target: wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
    type: extends
  - target: wiki/concepts/code-verification-pipeline-gaps.md
    type: related
---

# /trace execution gap — critical code shipped without trace-through

## Decision context

**The problem:** close-check Phase 3 (Remediate) lists `/trace` as one of
five lifecycle skills to invoke (alongside `/capture`, `/friction`,
`/handoff`, `/wiki`). The skill exists at `~/.grok/skills/trace/SKILL.md`
with 100+ checklist items and state-table methodology. The trace skill is
also referenced conceptually in many places across the workspace:
`close-check-invokes-capture.md` says it runs "unconditionally alongside
`/friction`, `/handoff`, `/trace`, and `/wiki`." But on critical code
shipped in the 019fa8f8 sweep (PreToolUse_spawn_model_gate.py edited 9x
across events 679-695, the file that gates every spawn_subagent call on
the host), **no `/trace` was actually run and no TRACE REPORT was
produced.**

This is the same failure class as the `/capture` gap that
`close-check-invokes-capture.md` documents — a lifecycle skill that exists
and is referenced but does not reliably fire on the work it is supposed
to catch. The difference is that `/capture` had a clean fix (add to
Phase 3 Remediate, commit `6d460e1`); `/trace` does not, because the gap
is between invocation and observable output, not between absence and
presence in a workflow.

## Evidence

**Instance 1 (session 019fa8f8, 2026-08-01):**

Pre-close report from `wf_019fbf03` (cutoff 2026-07-31 06:14:21Z) flagged
critical-code-trace as `[fail]` with these measurements:

- `agentFilesTouched=228` (massive code footprint)
- `agentLinesAdded=64723` (substantial code volume)
- `humanLinesAdded=688` (human edits present)
- "Critical code likely written but not traced"
- "No /trace artifact or TRACE REPORT evidence in session"

A grep for "TRACE REPORT" or "trace report" in `chat_history.jsonl`
returned **9 lines, all conceptual references** (e.g., turn 902: "The
`/trace` skill — new skill for tracing through verification. Not the
right place"). No actual trace report output exists in the transcript.
The session claimed `postsession-20260801` handoff line 26 stated "6
lifecycle skills run (`/harvest`, `/capture`, `/friction`, `/slc`,
`/behave`, `/trace`)" — but `/trace` invocation is absent from the
direct transcript evidence.

**Instance 2 (preceding session wf_019fbf03, 2026-07-31):**

The pre-close report explicitly flagged critical-code-trace as failing.
The fix-forward path was unclear because `/trace` is a **manual**
skill — the model is supposed to read the code, follow the call graph,
build a state table, and write the trace report. None of those actions
produced a trace artifact for the critical file edits.

**Pattern across both instances:**

- `/trace` was referenced conceptually multiple times in the transcript
- `/trace` SKILL.md was loaded (mention of the skill body in turns)
- `/trace` was NOT actually run on the critical files
- The "trace report" was never written to disk
- `/close-check` Phase 3 listed `/trace` as unconditional but did not
  verify a trace report was produced before declaring success

This is the execution-gap analog of the workspace-internal coverage gap
that `close-scanner-false-positive-resolved-handoff-references.md` and
`hook-evidence-collection-cost-vs-timeout-tradeoff.md` describe: the
artifact that would prove the work happened is the work itself, and the
work does not produce an audit trail.

## Root cause analysis

**Structural, not behavioral.** The model did not "forget" to run
`/trace`. The structural properties:

1. **No interception point.** `/trace` is invoked by the model's
   reasoning under a behavioral instruction in `close-check.rhai`. There
   is no runtime hook that can detect "this skill step was skipped" the
   way a PreToolUse hook detects a disallowed command.

2. **No visible-output contract.** Unlike `/capture` which writes to
   `docs/handoffs/` and can be verified by file existence, `/trace`
   produces a written report. There is no canonical filename that the
   model MUST write to. A report named `trace-report.md` somewhere in
   `P:/tmp/` is structurally the same as no report at all — the
   workspace doesn't know where to look.

3. **Lazy correlation with `/aar`.** Sessions that successfully produce
   `/aar` reports (preprocessor packet + report file) often claim
   `/trace` was also run because the two are conceptually adjacent in
   close-check Phase 3. This is the "lifecycle-skill-list-the-skill-as-
   done" failure mode: the workflow says "run these 5 skills" and the
   model reports "ran these 5 skills" without verifying each one's
   artifact.

4. **No failure surface.** If `/capture` is skipped, handoffs are
   missing. If `/wiki` is skipped, no new concepts. If `/friction` is
   skipped, no friction report. If `/trace` is skipped, **nothing
   observable is missing.** The trace report is the only output, and
   its absence is invisible to downstream gates.

## What this means for our workspace

**The fix is a visible-output contract for `/trace`**, modeled on the
pattern documented in
`visible-output-contracts-for-behavioral-skill-steps.md`:

1. **Canonical artifact path.** `/trace` must write its report to a
   fixed path the workspace can grep for:
   `P:/.artifacts/grok-trace/<session-id>-trace-report.md`. If the file
   doesn't exist after a Phase 3 invocation, the trace step is skipped.

2. **Receipt in close-check output.** The close-check Phase 3 output
   must contain a row for `/trace` showing the artifact path + file size
   + line count, the same way `/capture` shows handoff counts. Missing
   row = skipped skill = blocked close.

3. **Coverage gate for critical files.** Pre-close-report already
   classifies files as critical (spawn gate, close runner, hook
   dispatchers, lifecycle scripts). The trace gate should be: **critical
   files edited in this session MUST have a TRACE REPORT row referencing
   the file path.** No row = no trace = `[fail] critical-code-trace`,
   blocking close.

4. **Distinguish "/trace loaded" from "/trace run".** The session
   transcript should distinguish between (a) the model reading the
   `/trace` SKILL.md and (b) the model producing a trace report. The
   postsession handoff in 019fa8f8 claimed `/trace` was run; the
   transcript evidence shows the SKILL.md was loaded but no report was
   written. These are not the same thing.

## Falsifier

This finding is wrong if:
- **A canonical trace-report path already exists** that the workspace
  greps for (verify by grep `P:/.artifacts/` and `P:/.data/` for
  existing trace reports — the evidence says no canonical path exists).
- **The `/trace` skill is invoked by a hook** rather than by the model's
  reasoning (verify by reading `~/.grok/workflows/close-check.rhai` — the
  evidence says it is invoked as a behavioral step).
- **`/aar` evidence covers the same ground** as `/trace` (verify by
  reading `P:/.artifacts/grok-aar/20260731-close/aar-report.md` — AAR
  reports document post-session retrospective, not pre-shipment trace
  analysis; the two are complementary, not redundant).
- **Critical code in this session was actually simpler than the
  agentFilesTouched count suggests** (verify by reading
  `PreToolUse_spawn_model_gate.py` — 9 edits in events 679-695 is not
  simple).

## Receipts

- Session 019fa8f8 sweep pre-close report (cutoff 2026-07-31
  06:14:21Z): `critical-code-trace [fail]` with
  `agentFilesTouched=228`, `agentLinesAdded=64723`,
  `humanLinesAdded=688`, "Critical code likely written but not traced"
- Transcript grep for "TRACE REPORT" in `chat_history.jsonl`: 9 hits,
  all conceptual references, no actual trace report output
- `PreToolUse_spawn_model_gate.py` edited 9x across events 679-695
  (signal.json event_indices)
- `~/.grok/skills/trace/SKILL.md` — exists, 100+ checklist items,
  state-table methodology
- `~/.grok/workflows/close-check.rhai` — Phase 3 Remediate lists
  `/trace` as unconditional; no verification of trace artifact
- Postsession handoff `postsession-20260801` line 26: "6 lifecycle
  skills run" — claim vs transcript evidence mismatch

## Related

- [[visible-output-contracts-for-behavioral-skill-steps]] — the
  pattern that produces the fix: behavioral steps must emit a receipt
  to be auditable
- [[close-check-invokes-capture]] — the lifecycle-skill-not-firing
  failure mode on a different skill (capture), and the clean fix
  (commit 6d460e1)
- [[lifecycle-skill-remediation-modes-auto-act-vs-surface-only]] —
  /trace is `surface-only` per the catalog, which is part of why
  the gap exists
- [[code-verification-pipeline-gaps]] — gap analysis for static
  verification tooling; does not address the trace execution gap
  specifically
- [[hook-evidence-collection-cost-vs-timeout-tradeoff]] — same failure
  class at a different layer (hooks silently dropping receipts)
- [[close-check-finalize-phase-make-blocking-unnecessary]] — the
  architectural argument that Phase 3 should run lifecycle skills
  unconditionally; this concept is the boundary case where
  unconditional invocation is not sufficient without verification

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[codebase-knowledge-graph-mapping]]
- [[claude-code-hooks]]

