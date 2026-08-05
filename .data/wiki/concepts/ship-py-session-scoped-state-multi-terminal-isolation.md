---
title: "ship-py session-scoped state: multi-terminal isolation and inter-phase gates"
created: 2026-08-05
source: session-2026-08-05 (ship-py improvements after pipeline bypass)
sources:
  - internal: P:/.data/wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation.md
  - internal: P:/.data/wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
  - internal: ~/.grok/skills/ship-py/__lib/ship_orchestrator.py
tags: [ship-py, multi-terminal-isolation, session-scoped-state, inter-phase-gate, stale-data-immunity, artifacts-directory, phase-enforcement]
agent: grok
host: grok
cognitive_load: 2
verification: source-verified
summary: >
  ship-py state moved from P:/tmp/ship-py-state.json (global, collision-prone)
  to P:/.artifacts/ship-py/<session-id>/state.json (session-scoped, multi-terminal
  safe). Inter-phase gates added: each phase checks that prior phases completed
  via state["completed_phases"] list before executing. A phase cannot be run
  out of order — the orchestrator returns GATE_BLOCKED with exit code 2.
  Design decision: state path uses .artifacts/ (not tmp/) because it must
  survive crashes for resume and must not be cleaned by generic temp sweepers.
relations:
  - target: wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation.md
    type: fixes — inter-phase gates address the fragmentation problem
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: instance-of — session-scoped state implements this pattern
---

# ship-py session-scoped state: multi-terminal isolation and inter-phase gates

## Decision

**State path:** `P:/.artifacts/ship-py/<session-id>/state.json`

The old path (`P:/tmp/ship-py-state.json`) was a single global file — two
terminals running `/ship-py` concurrently would collide, overwriting each
other's state. The new path uses `.artifacts/` with a session-id subdirectory,
matching the workspace's standard isolation pattern.

**Why `.artifacts/` not `tmp/`:** state must survive crashes for resume. The
`tmp/` directory is swept by cleanup scripts. `.artifacts/` is durable and
session-scoped by convention.

**Inter-phase gates:** each phase (`review`, `verify`, `verdict`) calls
`_check_phase_gate()` which reads `state["completed_phases"]` and verifies the
required prior phase is in the list. If not, it returns GATE_BLOCKED with
exit code 2. The LLM cannot skip phases because the Python script refuses to
execute them out of order.

## What changed

| Before | After |
|--------|-------|
| `STATE_PATH = Path("P:/tmp/ship-py-state.json")` | `_state_path(session_id)` → `P:/.artifacts/ship-py/<sid>/state.json` |
| `load_state()` / `save_state(state)` (no session arg) | `load_state(session_id)` / `save_state(session_id, state)` |
| No phase-completion tracking | `state["completed_phases"]` list, appended after each phase finishes |
| No inter-phase gate | `_check_phase_gate(session_id, phase)` checks completed_phases before each cmd |
| Findings path: `P:/tmp/ship-py-review-findings.json` | `_findings_path(session_id)` → session-scoped |
| Phase log: `P:/tmp/ship-py-phase-log.txt` | `_phase_log_path(session_id)` → session-scoped |

## Falsifier

This design is wrong if:
- The session-scoped directory creates orphan state files that accumulate
  without cleanup (mitigated: SessionEnd hook cleans `.artifacts/` state)
- The inter-phase gate prevents legitimate resume from crash (mitigated:
  completed_phases list allows partial resume — skip already-completed phases)
- Two concurrent runs in the same session collide (should not happen —
  one session = one pipeline run)

## Related

- [[ship-py-phase-fragmentation-llm-controlled-continuation]]@fixes — the gates address the fragmentation problem
- [[multi-terminal-isolation-stale-data-immunity]]@instance-of — session-scoped state implements this pattern
