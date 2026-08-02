---
title: "Close-check should invoke capture"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [close-check, capture, session-lifecycle, improvement-opportunity]
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - ~/.grok/skills/capture/SKILL.md (capture is invoked by /close, not /close-check)
  - P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
  - Session transcript lines 209-232 (close sequence)
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: extends
  - target: wiki/concepts/proactive-improvement-opportunity-scanner.md
    type: related
---

# Close-check should invoke capture

## The gap

`/capture` is invoked by `/close` as a mandatory step (Step 3 in the close pipeline). But `/close-check` replaces `/close` as the session readiness gate — and `/close-check` does not invoke `/capture`.

The `/capture` skill scans the session transcript for 7 categories of improvement opportunity and routes findings to the right output type (wiki concepts, AGENTS.md rules, handoffs, tasks). When `/close-check` is used instead of `/close`, this scanning step is skipped entirely.

## What was missed in this session

The close-check scanner at the end of session 019f902a-621d-7711-9436-7c6003c57793 identified three gates needing attention but did not systematically scan the full session for improvement opportunities. Findings that `/capture` would have caught:

1. **Stale path references** — 9 references across 5 files (captured in-session but not as a reusable pattern)
2. **/www lifecycle script reference staleness** — `/www` SKILL.md referenced plugin-internal scripts at wrong path (captured in-session but not persisted as a concept)
3. **Skill consolidation candidates** — deprecated skills flagged for removal but without distinguishing safe vs unsafe removals

## The fix

`/close-check` should invoke `/capture` (or equivalent) as part of its pipeline. The `/capture` skill is designed to be invoked standalone or as part of `/close`. `/close-check` needs the same improvement-opportunity scan before declaring the session ready.

## Falsifier

If `/close-check` already invokes `/capture` or an equivalent scan, this gap is closed. If `/close-check` is used but `/capture` is not invoked, the gap persists.

## Receipts

- `~/.grok/skills/capture/SKILL.md` — capture is invoked by `/close`, not `/close-check`
- `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — close-check replaces close
- Session transcript lines 209-232 — close sequence without `/capture` invocation
