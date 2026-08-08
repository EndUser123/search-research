---
title: "Pipeline phase-gate state machines must reset on re-entry"
created: 2026-08-08
source: dream-2026-08-08
tags: [pipeline, state-machine, ship-py, phase-gate, blocked-state, re-entry]
summary: >
  When a pipeline (ship-py) is re-run after a prior blocked attempt, the state
  file retains the blocked state. The inter-phase gate then blocks all phases
  even though the blocking condition may have been resolved. Fix: detect phase
  re-entry and reset the blocked state before checking the gate.
agent: grok
host: grok
cognitive_load: 2
verification: single-source-verified
relations:
  - target: wiki/concepts/pipeline-session-scoping-each-layer-independently.md
    type: related
---

# Pipeline phase-gate state machines must reset on re-entry

## The pattern

When a multi-phase pipeline (ship-py, close-check, or any state-machine-driven
orchestrator) blocks on a phase and the user fixes the blocking condition, re-running
the pipeline returns `GATE_BLOCKED` from the prior blocked state — not from the
current phase's actual state. The state file retains `phase: blocked` between runs,
and the inter-phase gate checks this stale value.

## Instances

1. **ship-py skill-dev block (2026-08-08):** skill-dev phase blocked on a foreign-session
   file. After the file was fixed, re-running skill-dev returned GATE_BLOCKED because
   the state file still said `phase: blocked`. Fix: re-run `detect --force` to reset state.

2. **ship-py doc-check block (2026-08-08):** same pattern — after fixing doc-check,
   re-running returned GATE_BLOCKED from prior blocked state. Required `--force` flag.

## Root cause

The inter-phase gate checks `state.get("phase") == "blocked"` before allowing any
phase to proceed. The blocked state is set when a phase fails, but never cleared
on re-entry. The `--force` flag exists as an escape hatch but is not the default
behavior — it should be automatic when re-entering after a block.

## Fix

Pipeline state machines should reset blocked state on re-entry:

```python
def _check_phase_gate(session_id, current_phase):
    state = load_state(session_id)
    # Reset blocked state when entering a new phase
    if state.get("phase") == "blocked":
        state["phase"] = current_phase
        save_state(session_id, state)
    # Now check the gate
    ...
```

The `--force` flag on `detect` is the current workaround. The structural fix is
making blocked-state reset automatic when the pipeline is re-invoked.

## Falsifier

This concept is wrong if:
- Pipelines always reset blocked state automatically (then the pattern doesn't exist)
- The `--force` flag is sufficient and no automatic reset is needed (then the fix is unnecessary)
