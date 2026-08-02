---
thread_id: close-check-remediation-performance-019fb937
parent_handoff_path: P:/docs/handoffs/close-check-lifecycle-019fb937-20260802/HANDOFF.md
current_session_id: 019fb937-b03e-7f80-a4b0-68afdb7da38d
parent_session: 019fb937-b03e-7f80-a4b0-68afdb7da38d
current_terminal_id: 311cd4b1-2bf4-47ec-8abd-7530e971493c
produced_at: 2026-08-02T05:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 448e0b38806f4bbcdc568696a45d638fdd3eb616
---

# Handoff: Close-check remediation performance optimization

## Objective

Reduce close-check Phase 3 remediation time from 12+ minutes to <3 minutes by moving mechanical scanning inline and only spawning subagents for write-capable skills.

## Status

OPEN — design identified, implementation deferred to fresh session.

## Producing context

- Session: `019fb937-b03e-7f80-a4b0-68afdb7da38d` (2026-07-31 → 2026-08-02)
- Terminal: 311cd4b1-2bf4-47ec-8abd-7530e971493c
- Host: grok (Grok Build)

## Read-first list

1. `P:/docs/handoffs/close-check-lifecycle-019fb937-20260802/HANDOFF.md` — close-check lifecycle for this session
2. `P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md` — close-check auto-chain design
3. `P:/docs/handoffs/claude-skill-decomposition-close-check-20260801/HANDOFF.md` — Claude skill decomposition
4. `C:/Users/brsth/.grok/workflows/close-check.rhai` — the workflow script (Phase 3 Remediate)

## Verified facts

- [FACT] Close-check Phase 3 takes 12+ minutes (source: hook-timeout-root-cause handoff, TP-04)
- [FACT] Each remediation skill runs as a full subagent spawn (read SKILL.md → scan transcript → check existing → write → commit) (source: TP-04 task packet)
- [FACT] 5 subagent lifecycles = 12+ minutes (source: TP-04 task packet)
- [FACT] Phase 1 sweep agents already scan the transcript for correction signals and friction patterns (source: close-check-lifecycle-auto-chain handoff)
- [FACT] The close-check workflow Rhai script only runs scan commands, not skill invocations (source: close-check-lifecycle-auto-chain handoff)

## Proposed approach

1. Move mechanical scanning (grep transcript for correction signals, count friction patterns) inline to the workflow script
2. Have Phase 1 sweep agents ALSO collect the remediation data (they already scan the transcript)
3. Phase 3 writes artifacts based on data already gathered, not by spawning new subagents
4. Only spawn subagents for write-capable skills that need LLM judgment to decide what to write

## Task packets

### T1: Instrument close-check Phase 3 timing

- **id:** CCP-01
- **goal:** Measure current Phase 3 timing to establish baseline
- **in scope:** close-check.rhai Phase 3 Remediate
- **acceptance:** Baseline timing recorded (expected: 12+ minutes)
- **falsifier:** Phase 3 completes in <3 minutes (already optimized)
- **verification level required:** LIVE_BEHAVIOR

### T2: Move mechanical scanning inline

- **id:** CCP-02
- **goal:** Replace subagent spawns for mechanical scanning with inline Rhai script logic
- **in scope:** close-check.rhai Phase 3
- **acceptance:** Mechanical scanning (grep, count, classify) runs inline without subagent spawn
- **falsifier:** Phase 3 still takes >5 minutes after optimization
- **verification level required:** LIVE_BEHAVIOR

### T3: Collect remediation data from Phase 1 sweep agents

- **id:** CCP-03
- **goal:** Have Phase 1 sweep agents pass remediation data to Phase 3 instead of Phase 3 re-scanning
- **in scope:** close-check.rhai Phase 1 and Phase 3
- **acceptance:** Phase 3 receives pre-collected remediation data from Phase 1
- **falsifier:** Phase 3 still spawns subagents for data collection
- **verification level required:** LIVE_BEHAVIOR

## Hard constraints

- Must not break existing close-check behavior
- Must not modify Phase 1 Sweep or Phase 4 Finalize (out of scope)
- All changes must have falsifiers

## Cross-reference couplings

- `P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md` → this handoff is a sub-task of the auto-chain design
- `P:/docs/handoffs/claude-skill-decomposition-close-check-20260801/HANDOFF.md` → the decomposition table identifies which components to port
- `C:/Users/brsth/.grok/workflows/close-check.rhai` → the workflow script to modify

## Resumption protocol

1. Read this handoff and the close-check-lifecycle-auto-chain handoff
2. Instrument Phase 3 timing (T1)
3. Move mechanical scanning inline (T2)
4. Collect remediation data from Phase 1 (T3)

## Suggested next invocation

```
/go CCP-01 — instrument close-check Phase 3 timing
```

## Last user message (verbatim)

> "Please use the handoff skill"

## Epistemic labels per claim

- All [FACT] entries above are sourced from the hook-timeout-root-cause handoff (TP-04) and close-check-lifecycle-auto-chain handoff
- The proposed approach is [INFERENCE] — based on the architecture described in TP-04

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:00 | 019fb937... | created |
