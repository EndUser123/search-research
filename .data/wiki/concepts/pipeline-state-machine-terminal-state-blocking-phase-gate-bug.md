---
title: "Pipeline state-machine terminal-state blocking: a phase-gate bug class"
created: 2026-08-09
source: session-019fe403 (merge-unreachable bug in ship-py verdict phase)
tags: [failure-pattern, pipeline, state-machine, terminal-state, phase-gate, ship-py, bug-class]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/rag-apr-evidence-retrieval-augmented-generation-improves-llm-bug-repair.md
    type: supports — this concept fills a gap in the wiki's failure-pattern coverage for /why-in-fix
summary: >
  When a pipeline state machine uses a "complete" state as a terminal marker,
  any phase that sets state to "complete" before all downstream phases have
  run will block those phases permanently. The gate treats "complete" as
  terminal and rejects all re-entry — including valid downstream phases.
  Fix: use a non-terminal intermediate state (e.g., "merge-ready") between
  the phase that derives a verdict and the phase that acts on it.
---

# Pipeline state-machine terminal-state blocking

## The pattern

```
Phase A (verdict) sets state = "complete"
  ↓
Phase B (merge) tries to run
  ↓
Gate checks: state == "complete" → BLOCK ("already complete, cannot re-enter")
  ↓
Phase B can NEVER run after Phase A produces a terminal result
```

## Evidence

**ship-py verdict→merge bug (session 019fe403):** The verdict phase set
`state["phase"] = "complete"` when verdict was SHIP DONE. The phase gate
(`_check_phase_gate`) treats "complete" as terminal — it blocks ALL phases
after it. So when run_all tried to advance from verdict to merge (the next
phase in PHASE_ORDER), the gate blocked it with "Pipeline already COMPLETE."

**Impact:** SHIP DONE via run_all could never reach merge. Every successful
verdict immediately closed the door on the merge phase.

## How to detect this bug class

- **Symptom:** a phase that should run after a "success" phase never executes
- **Diagnostic:** check whether the success phase sets a terminal state that
  the gate treats as blocking
- **Code pattern:** look for `state["phase"] = "complete"` (or "done", "final")
  followed by phases that need to run after it

## Structural fix

Use intermediate states that are non-terminal:
- `"merge-ready"` — SHIP DONE reached, merge + publish still allowed
- `"complete"` — ONLY when the ENTIRE pipeline is finished (after publish/babysit)
- The gate should only block re-entry on truly terminal states, not intermediate ones

## Why /why-in-fix would benefit from this concept

When the fix agent encounters "phase B can't run after phase A succeeds,"
querying the wiki for "terminal state blocking" would surface this pattern
and the structural fix (intermediate non-terminal state) instead of the
agent re-deriving the root cause from scratch.
