---
title: "State synchronization gap: two files that must stay in sync but are written independently"
created: 2026-08-09
source: session-019fe403 (orchestrator state.json vs hook ship-phase-py.json not synced)
tags: [failure-pattern, state-synchronization, dual-write, hook-sync, fail-open, ship-py, bug-class]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/rag-apr-evidence-retrieval-augmented-generation-improves-llm-bug-repair.md
    type: supports — fills gap in wiki failure-pattern coverage for /why-in-fix
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: applies — the hook state must match the orchestrator state
summary: >
  When two components read different state files that should contain the same
  information, but only one is written programmatically while the other depends
  on LLM-followed instructions, the LLM-dependent file is silently skipped
  under session pressure. The dependent component (hook) then fails OPEN
  because its state file is stale or missing. Fix: write both files from the
  same save_state() call atomically.
---

# State synchronization gap: dual-write fail-open

## The pattern

```
Component A (orchestrator) writes file1 (state.json) programmatically
  ↓
Component B (hook) reads file2 (ship-phase-py.json)
  ↓
file2 is supposed to be written by the LLM per SKILL.md instructions
  ↓
LLM forgets to write file2 (session pressure, context loss)
  ↓
Component B reads stale/missing file2 → fails OPEN (allows when it should block)
```

## Evidence

**ship-py hook state sync (session 019fe403):** The orchestrator wrote
`P:/.artifacts/ship-py/<sid>/state.json` via `save_state()`. The PreToolUse
hook read `~/.grok/state/<sid>/ship-phase-py.json` — a DIFFERENT file. The
SKILL.md told the agent to manually write the hook file at each pipeline
transition. But that's LLM-dependent enforcement: if the agent forgets,
the hook file is stale or missing, and the push gate is silently bypassed.

The fix: `save_state()` now writes BOTH files atomically (state.json +
ship-phase-py.json) using tmp+replace.

## How to detect this bug class

- **Symptom:** an enforcement gate (hook, check) silently allows something
  it should block
- **Diagnostic:** trace which file the gate reads, and check whether that
  file is written programmatically or depends on LLM instructions
- **Code pattern:** SKILL.md says "write this file at each transition" but
  no code actually writes it

## Structural fix

Never rely on LLM-followed instructions for state that an enforcement
component reads. Write the state from the code path that the component
depends on:

```python
def save_state(session_id, state):
    _atomic_write_json(state_path, state)        # orchestrator reads this
    _write_hook_state(session_id, state)          # hook reads this
    # both written from the same function call — LLM can't forget
```

## Why /why-in-fix would benefit from this concept

When the fix agent encounters "hook allows push when it should block,"
querying the wiki for "state synchronization gap" would surface this pattern
and the fix (write both files from the same save_state call).
