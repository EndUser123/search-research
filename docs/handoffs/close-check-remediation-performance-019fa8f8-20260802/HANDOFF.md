---
thread_id: close-check-remediation-performance-019fa8f8
parent_handoff_path: P:/docs/handoffs/close-check-remediation-performance-019fb937-20260802/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: unknown
produced_at: 2026-08-02T00:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: efac5a42fb93d25224ca4bf0c9237c8afc23607
---

# Handoff: Close-check remediation performance — session 019fa8f8

## Objective

Reduce close-check Phase 3 remediation time from 12+ minutes to <3 minutes by moving mechanical scanning inline and only spawning subagents for write-capable skills.

## Status

OPEN — design identified from session 019fa8f8 sweep, implementation deferred.

## Producing context

- Session: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14 (started 2026-07-28T07:44:45)
- Sweep verdict: BLOCKED — close_runner terminal state = blocked (scanner returned CLOSE INCOMPLETE)
- Close gates: NOT ASSESSED, Evidence ledger: NOT GENERATED
- The close-check scanner was unavailable during this session, so remediation could not be executed

## Read-first list

1. `P:/docs/handoffs/close-check-remediation-performance-019fb937-20260802/HANDOFF.md` — sibling session's design (same problem, different session)
2. `P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md` — close-check auto-chain design
3. `P:/docs/handoffs/claude-skill-decomposition-close-check-20260801/HANDOFF.md` — Claude skill decomposition
4. `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — close-check workflow context

## Verified facts

- [FACT] Close-check Phase 3 takes 12+ minutes (source: close-check-remediation-performance handoff from session 019fb937, TP-04)
- [FACT] Each remediation skill runs as a full subagent spawn (read SKILL.md → scan transcript → check existing → write → commit) (source: TP-04 task packet)
- [FACT] 5 subagent lifecycles = 12+ minutes (source: TP-04 task packet)
- [FACT] Phase 1 sweep agents already scan the transcript for correction signals and friction patterns (source: close-check-lifecycle-auto-chain handoff)
- [FACT] The close-check workflow Rhai script only runs scan commands, not skill invocations (source: close-check-lifecycle-auto-chain handoff)
- [FACT] Session 019fa8f8 had close_runner terminal state = blocked — scanner was unavailable (source: sweep evidence, close-gates findings)
- [FACT] Evidence ledger was NOT GENERATED for this session (source: sweep evidence, close-gates findings)
- [FACT] Close gates were NOT ASSESSED for this session (source: sweep evidence, close-gates findings)

## Current state

- The close-check scanner crashed/returned CLOSE INCOMPLETE during session 019fa8f8
- The close-runner Windows-path JSON-stringification bug (OSError WinError 123) is the root cause — close_runner.py crashes when --session is a JSON dict
- The close-runner bug is documented in handoff close-runner-windows-path-bug-fix-20260802 but not yet fixed
- Until close-runner is fixed, close-check Phase 3 cannot produce gate evaluations or evidence ledgers

## Proposed approach (from sibling session 019fb937)

1. Move mechanical scanning (grep transcript for correction signals, count friction patterns) inline to the workflow script
2. Have Phase 1 sweep agents ALSO collect the remediation data (they already scan the transcript)
3. Phase 3 writes artifacts based on data already gathered, not by spawning new subagents
4. Only spawn subagents for write-capable skills that need LLM judgment to decide what to write

## Task packets

### T1: Fix close_runner.py Windows-path bug (prerequisite)

- **id:** CCR-01
- **goal:** Fix the JSON-stringified path crash in close_runner.py so close-check can run on Windows
- **in scope:** close_runner.py path construction (line ~137)
- **out of scope:** Other close-runner functionality
- **files / anchors:** locate close_runner.py, find path-building line
- **acceptance:** close-check produces non-zero gate evaluations on Windows with JSON-dict --session argument; WinError 123 no longer occurs
- **falsifier:** Same WinError 123 occurs after patch
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 1 hour (locate + patch + verify)

### T2: Instrument close-check Phase 3 timing

- **id:** CCR-02
- **goal:** Measure current Phase 3 timing to establish baseline after close-runner fix
- **in scope:** close-check.rhai Phase 3 Remediate
- **acceptance:** Baseline timing recorded (expected: 12+ minutes)
- **falsifier:** Phase 3 completes in <3 minutes (already optimized)
- **verification level required:** LIVE_BEHAVIOR

### T3: Move mechanical scanning inline

- **id:** CCR-03
- **goal:** Replace subagent spawns for mechanical scanning with inline Rhai script logic
- **in scope:** close-check.rhai Phase 3
- **acceptance:** Mechanical scanning (grep, count, classify) runs inline without subagent spawn
- **falsifier:** Phase 3 still takes >5 minutes after optimization
- **verification level required:** LIVE_BEHAVIOR

### T4: Collect remediation data from Phase 1 sweep agents

- **id:** CCR-04
- **goal:** Have Phase 1 sweep agents pass remediation data to Phase 3 instead of Phase 3 re-scanning
- **in scope:** close-check.rhai Phase 1 and Phase 3
- **acceptance:** Phase 3 receives pre-collected remediation data from Phase 1
- **falsifier:** Phase 3 still spawns subagents for data collection
- **verification level required:** LIVE_BEHAVIOR

## Open decisions

1. **Close-runner fix priority:** Should the close-runner Windows-path bug be fixed before or after the remediation performance optimization?
   - Option A: Fix close-runner first (T1) — unblocks all close-check runs
   - Option B: Do both in parallel — fix close-runner while designing inline scanning
   - **Selection criterion:** close-runner is a prerequisite for Phase 3 to work at all
   - **Leading option:** Option A — fix close-runner first, then optimize

## Hard constraints

- Must not break existing close-check behavior
- Must not modify Phase 1 Sweep or Phase 4 Finalize (out of scope)
- All changes must have falsifiers
- close_runner.py patch must not break POSIX behavior (Windows-safe is a subset of POSIX-safe)

## Cross-reference couplings

- `P:/docs/handoffs/close-runner-windows-path-bug-fix-20260802/HANDOFF.md` — close-runner bug handoff (prerequisite)
- `P:/docs/handoffs/close-check-remediation-performance-019fb937-20260802/HANDOFF.md` — sibling session design
- `P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md` — auto-chain design
- `P:/docs/handoffs/claude-skill-decomposition-close-check-20260801/HANDOFF.md` — decomposition table
- `P:/.data/wiki/concepts/close-runner-windows-path-json-stringification-bug.md` — wiki concept with RCA

## Resumption protocol

1. Fix close_runner.py Windows-path bug (T1) — prerequisite for all close-check work
2. Instrument Phase 3 timing (T2) to establish baseline
3. Move mechanical scanning inline (T3)
4. Collect remediation data from Phase 1 (T4)

## Suggested next invocation

```
/go CCR-01 — fix close_runner.py Windows-path JSON-stringification bug
```

## Last user message (verbatim)

> "Run the /handoff skill."

## Epistemic labels per claim

- "Close-check Phase 3 takes 12+ minutes" — [FACT] (source: close-check-remediation-performance handoff from session 019fb937, TP-04)
- "close_runner.py crashes with WinError 123" — [FACT] (source: close-runner-windows-path-bug-fix handoff)
- "The close-runner bug is the root cause of CLOSE INCOMPLETE" — [INFERENCE] (the sweep found scanner unavailable; the close-runner bug is the known cause of scanner crashes on Windows with JSON-dict --session)
- "Option A (fix close-runner first) is leading" — [INFERENCE] (close-runner is a prerequisite for Phase 3 to function)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02 | 019fa8f8 | created |
