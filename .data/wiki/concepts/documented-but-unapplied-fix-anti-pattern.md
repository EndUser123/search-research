---
title: "Documented-but-unapplied fix anti-pattern: when verified solutions sit in handoffs instead of code"
created: 2026-08-12
source: session-2026-08-12 /tp improve analysis (chain-break fix documented for 2 compaction segments, never applied)
tags: [anti-pattern, handoff-degradation, fix-application-gap, specification-gaming-adjacent, chronic-pattern]
agent: grok
host: both
cognitive_load: 2
verification: session-observed
summary: >
  A fix that is verified, documented, and trivial (≤5 lines) but sits in a handoff
  or compaction segment for an entire session without being applied to code. The
  documentation creates a false sense of completion — "we solved this" — while the
  bug remains active. The fix is rediscovered on the next encounter, sometimes by
  a different session that doesn't know the handoff exists. This is the same failure
  class as the "unactioned recommendations" pattern but specific to code fixes that
  were fully specified and just never typed into the file.
---

# Documented-but-unapplied fix anti-pattern

## The pattern

1. A bug is found during a session (e.g., ship-py chain break on compacted sessions).
2. The root cause is traced and verified (e.g., detect loads stale state.json, old chain hashes contaminate current run).
3. The fix is specified in detail (e.g., "clear `_transition_chain` to `[]` at start of every detect invocation, 3 lines in detect.py").
4. The fix is written into a handoff, compaction summary, or improvement analysis instead of into the code.
5. The session ends or moves to other work.
6. The fix is never applied. The next session (or the next run) hits the same bug.

## Why this happens

- **Closure pressure:** documenting the fix *feels* like fixing it. The agent has produced a complete specification, which satisfies the narrative completion drive without the code change.
- **Batching bias:** the agent plans to "apply it later" as part of a batch of fixes, but the batch never materializes.
- **Scope separation:** the fix is discovered during analysis (e.g., `/tp improve`) but the analysis turn doesn't also implement code changes — the skill is in evaluation mode, not execution mode.
- **Compaction loss:** the fix is in the compaction summary, which the post-compaction context loses or de-prioritizes.

## Structural fixes

### 1. Immediate application for trivial fixes

If a fix is ≤5 lines, verified, and the file is known: apply it in the same turn it's discovered. Don't defer to a handoff. The [[no-deferred-persistence]] rule already covers this for writes — extend the principle to code fixes.

### 2. Close-py COMPLETENESS SCAN extension

The `/tp session` COMPLETENESS SCAN catches unactioned *recommendations*. But it scans for recommendation markers ("I recommend", "should", "fix"). It misses fixes that were specified in handoff *body text* or compaction segments, where the language is diagnostic ("root cause is X, correct fix is Y") rather than recommendation-shaped.

**Extension:** the scan should also flag handoff files with `## Fix` or `## Solution` sections that have no corresponding commit in git. If a handoff specifies a fix and no commit touches the referenced file after the handoff was written, the fix is documented-but-unapplied.

### 3. Detect-phase contamination check

For pipeline skills (ship-py, close-py): the detect phase should check whether prior-run state.json contains stale data that would contaminate the current run. This is the specific fix for the chain-break class, but the pattern generalizes: any pipeline that loads state from disk at start must either (a) clear stale fields or (b) validate that the state matches the current session.

## What this means for our workspace

1. **Apply trivial fixes immediately** — if a fix is ≤5 lines, verified, and the file is known, apply it in the same turn. Don't defer to a handoff.
2. **Extend the `/tp session` COMPLETENESS SCAN** — flag handoff files with `## Fix` or `## Solution` sections that have no corresponding commit touching the referenced file.
3. **Pipeline detect-phase contamination check** — any pipeline that loads state from disk at detect entry must clear stale fields or validate the state matches the current session.

## Reference incidents

- **Session 019fef5d (2026-08-12):** ship-py chain-break fix (3 lines in detect.py) was documented in the compaction summary and improvement analysis for 2+ compaction segments but never applied. The fix was only applied when `/tp improve` produced it as recommendation #1 and the operator said "0" (execute all).
- **Session 019fba58 (2026-08-02):** 5 ensemble findings (E-09, E-10, E-12, E-15, E-19) were surfaced during `/design` review but silently dropped. Related pattern — documented findings that were never actioned.

## Falsifier

This concept is wrong if applying trivial fixes immediately (rather than batching them) causes more problems than it solves — e.g., if the fixes are wrong as often as they're right, or if batching produces materially better results. Track: after implementing "immediate application for trivial fixes," does the documented-but-unapplied count drop to near-zero?

## Relationship to other concepts

- [[no-deferred-persistence]] — the parent principle. Documented-but-unapplied is the code-fix-specific instance.
- [[claims-require-receipts-worked-examples]] — documenting a fix is a "claim" of solving the problem; the receipt is the commit, not the handoff.
- [[specification-gaming-in-llm-agent-pipelines]] — adjacent: the agent satisfies the "we solved it" expectation by writing documentation instead of code.
