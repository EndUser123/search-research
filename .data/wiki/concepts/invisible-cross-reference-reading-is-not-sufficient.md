---
title: "Invisible cross-reference: reading data is not sufficient; cross-referencing must produce visible output"
created: 2026-07-31
source: session-019fb177 (/handoff compaction cross-reference fix)
tags: [transferable-pattern, cross-reference, compaction, handoff, verification, invisible-work, receipt-principle]
summary: >
  When recovering work from a compaction summary (or any structured data source),
  reading the data is necessary but not sufficient. The missing step is
  cross-referencing each item against the agent's output coverage — and the
  cross-reference must produce a visible artifact (table, list) to be verifiable.
  An invisible mental cross-reference has the same failure mode as no
  cross-reference: items fall through the cracks and the operator can't tell.
  First observed in /handoff auto-update mode: the compaction summary listed
  OPP-05 as a pending task, the agent read the summary, but never checked whether
  any handoff covered it. Fix: require a cross-reference table in the report.
agent: grok
host: grok
cognitive_load: 1
verification: observed
sources:
  - "Session 019fb177: /handoff auto-update missed OPP-05 despite reading compaction summary"
relations:
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
  - target: wiki/concepts/check-receipt-lifecycle-manifest-and-mechanical-derivation.md
    type: related
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: related
---

# Invisible cross-reference: reading data is not sufficient

## Decision context

**Why this was needed:** during `/handoff` auto-update, the agent read the compaction summary (which contained a "Pending Tasks" section listing OPP-05), wrote handoffs for the post-compaction work streams, and reported done. But OPP-05 — a pending task from the pre-compaction session — was missing from all handoffs. The operator asked "did you start at the first session?" The agent then read the compaction summary again and found OPP-05 was there the whole time.

**Root cause:** the agent treated reading the summary as sufficient. It processed the narrative but didn't systematically check: "for each item in the summary's pending-tasks list, is there a handoff that covers it?" The cross-reference happened implicitly (the agent "knew" about the tasks) but never produced a visible check. The result: one task dropped, undetected until the operator caught it.

## The pattern

This is the same structural failure as [[mechanical-enforcement-over-behavioral-reminder]]: an instruction that depends on the agent remembering to do something has ~12% compliance under cognitive load. "Read the summary and make sure you cover everything" is a behavioral instruction. "Produce a cross-reference table showing each pending task and its handoff coverage" is a mechanical output requirement.

**The principle:** if a cross-reference doesn't produce output, it didn't happen. This is the same principle behind receipts ([[causal-mechanism-claims-require-source-receipts-before-durable-write]]) and manifests ([[check-receipt-lifecycle-manifest-and-mechanical-derivation]]): invisible work is unverifiable work.

## Where this pattern applies

| Context | Data source read | Cross-reference needed | Visible output |
|---------|-----------------|----------------------|----------------|
| `/handoff` auto-update after compaction | Compaction summary "Pending Tasks" | Each task → covered by which handoff? | Cross-reference table in report |
| `/close` git_state gate | git log/status | Each commit → attributed to which session? | Gate state (already mechanical) |
| `/review` findings → fix-loop | FINDINGS.md | Each finding → addressed by which fix? | Fix-loop receipt |
| Plan execution | Plan task list | Each task → completed? (checkbox) | Execution Status table |
| Removal protocol | Grep results | Each reference → removed? | Zero-references verification grep |

In all cases, reading the data is the input. The cross-reference is the processing step. The visible output is the proof.

## Falsifier

This pattern is wrong if:
- The cross-reference table adds ceremony without catching anything — meaning the implicit cross-reference was already sufficient. But this session's OPP-05 incident disproves that for the handoff case.
- The data source is small enough (<3 items) that a mental cross-reference is reliable. True for trivial cases; the rule should scale with item count.

## What this means for our workspace

The `/handoff` auto-update mode now requires a cross-reference table in the report (commit `bc499c4`). The general pattern — "cross-reference must produce visible output" — applies wherever an agent reads structured data and needs to verify complete coverage. Future skill edits should look for invisible cross-references and make them visible.

This connects to the meta-checkpoint Q2 ("did I audit my own output?"): an invisible cross-reference is unaudited output.

## Receipts

- `/handoff` SKILL.md Step 7: cross-reference table requirement (commit `bc499c4`)
- `/handoff` SKILL.md Step 2: cross-reference instruction (commit `a5b0d60`)
- Reference incident: OPP-05 missed despite being in compaction summary (session 019fb177)
