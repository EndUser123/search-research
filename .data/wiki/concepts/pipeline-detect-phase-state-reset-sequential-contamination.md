---
title: "Pipeline detect-phase state reset: sequential run contamination from prior completed state"
created: 2026-08-12
source: session-2026-08-12 ship-py chain-break root cause (compaction segments 000-001 documented fix, applied this turn)
tags: [pipeline-architecture, state-management, tamper-evident-chain, sequential-contamination, ship-py, close-py, detect-phase]
agent: grok
host: both
cognitive_load: 2
verification: session-observed
summary: >
  Pipeline skills (ship-py, close-py) that load state.json at detect entry inherit
  stale state from the prior completed run. The tamper-evident transition chain —
  designed to prevent specification gaming — breaks because old chain hashes don't
  match the new run's state. The fix: always reset the transition chain at detect
  entry, not just on --force. This is sequential contamination, distinct from
  concurrent-session contamination (multi-terminal isolation).
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: related
  - target: wiki/concepts/specification-gaming-in-llm-agent-pipelines.md
    type: related
  - target: wiki/concepts/documented-but-unapplied-fix-anti-pattern.md
    type: related
  - target: wiki/concepts/python-orchestrated-skill-build-pattern-study-replicate-test.md
    type: refines
---

# Pipeline detect-phase state reset: sequential run contamination

## Decision context

Ship-py and close-py use a tamper-evident transition chain to prevent specification gaming: each phase hashes the prior state + current phase name, producing a chain that breaks if the agent writes state directly (bypassing the orchestrator). The chain is the anti-gaming backstop.

But on compacted sessions — or any session where the pipeline ran once before — detect loads `state.json` from the prior completed run. The prior run's chain entries hash state that doesn't match the new run. When `run-all` validates the chain, it sees `chain_broken_at_entry: expected prior_hash=genesis, got 5a105ab5eef05da1`.

The chain-break is not a gaming attempt — it's stale state contamination. But the result is the same: the pipeline blocks, and the operator has to use `--force` to clear it.

## Root cause

```
Session A: detect → ... → verdict → state.json written with chain entries
Session B (compacted): detect loads Session A's state.json
  → chain entries from Session A are still present
  → detect adds its own entry, but the prior_hash doesn't match
  → run-all validates: chain broken
```

The chain validation is correct — the chain IS broken because the state was loaded from a different run. The problem is that detect doesn't clear the chain at entry.

## The fix

**Always reset the transition chain at detect entry, not just on --force.**

```python
# detect.py — cmd_detect()
# Always reset the tamper-evident transition chain on detect entry.
# detect is the first phase — every new pipeline run starts a fresh chain.
state["_transition_chain"] = []
state["_chain_trimmed"] = False
```

This was originally inside the `--force` block only. But the failure happens on the FIRST detect call of a new run, before --force is used. Moving the reset outside the `--force` conditional fixes it for every run.

**Receipt:** `~/.grok/skills/ship-py/__lib/phases/detect.py` lines 88-99 (commit a612f27).

## Why this is distinct from multi-terminal isolation

| Property | Multi-terminal isolation | Sequential run contamination |
|----------|-------------------------|------------------------------|
| **Failure mode** | Two sessions write the same state file simultaneously | One session loads a prior session's completed state |
| **Root cause** | No per-session isolation (shared working tree) | No state reset at pipeline entry |
| **Fix location** | Session-scoped file paths, run-ID isolation | Detect-phase state clear |
| **Concept** | [[multi-terminal-isolation-stale-data-immunity]] | This concept |

Both produce stale-data failures, but the mechanisms are different. Multi-terminal isolation fixes concurrent access; detect-phase reset fixes sequential access. A pipeline needs both.

## What this means for our workspace

1. **Ship-py:** fix applied (2026-08-12, commit a612f27). Every detect entry clears the chain.

2. **Close-py:** needs the same fix. Close-py's detect phase (`~/.grok/skills/close-py/__lib/phases/detect.py`) loads state.json and should clear `_transition_chain` at entry. This is part of the close-py dispatch-only conversion handoff.

3. **Any future pipeline skill:** the detect-phase state-reset pattern should be in the shared `pipeline_chain` module (extracted in commit c911d02), not copied into each skill. The pattern: `save_state()` writes the chain; `cmd_detect()` clears it. This is the contract.

4. **The chain exists to prevent gaming — stale state defeats it indirectly.** A broken chain from stale state trains the operator to use `--force`, which is the same escape hatch the gaming prevention was designed to close. If `--force` becomes routine, the anti-gaming measure is defeated by habituation.

## Receipts

- `~/.grok/skills/ship-py/__lib/phases/detect.py` lines 88-99 — the chain-reset block moved outside `--force` conditional (commit a612f27, 2026-08-12). `state["_transition_chain"] = []` and `state["_chain_trimmed"] = False` at every detect entry.
- `~/.grok/skills/ship-py/__lib/phases/_shared.py` `save_state()` / `validate_transition_chain()` — the chain write and validation logic (the consumer of the reset).
- Compaction segment 001, line 72: `chain_broken_at_entry: expected prior_hash=genesis, got 5a105ab5eef05da1` — the observed failure that motivated the fix.
- `~/.grok/skills/close-py/__lib/phases/detect.py` — needs the same fix (not yet applied as of this write).

## Falsifier

This concept is wrong if moving the chain reset outside `--force` causes a different problem — e.g., if legitimate mid-pipeline restarts need the chain to persist across detect re-entries. Track: after the fix, do any pipeline runs need the chain to survive a detect re-entry? If yes, the reset should be conditional (new-session-only), not unconditional.

## Related

- [[multi-terminal-isolation-stale-data-immunity]] — concurrent contamination (distinct mechanism)
- [[specification-gaming-in-llm-agent-pipelines]] — the chain exists to prevent this; stale state defeats it indirectly
- [[documented-but-unapplied-fix-anti-pattern]] — this fix sat documented for 2 compaction segments before being applied
- [[python-orchestrated-skill-build-pattern-study-replicate-test]] — the build pattern study; this concept refines it with the state-reset contract

## Auto-related

- [[pipeline-orchestration-and-transport-reliability]]
- [[python-orchestrated-skill-build-pattern-study-replicate-test]]
- [[close-runner-verdict-staleness-across-phases]]
- [[skill-catalog]]
- [[wiki-lifecycle-state-file]]

