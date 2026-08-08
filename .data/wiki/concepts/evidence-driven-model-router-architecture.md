---
title: "Evidence-driven model router: flat-pool selection with lifecycle states"
created: 2026-08-07
source: session-2026-08-07
tags: [models, routing, pool, selection, evidence-driven, lifecycle, circuit-breaker, fleet, architecture, model-router]
host: grok
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/model-pool-not-chain
    type: implements
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity
    type: implements
  - target: wiki/concepts/model-fleet-provider-pools
    type: supersedes
  - target: wiki/concepts/model-tool-calling-capability-matrix
    type: consumes
---

# Evidence-driven model router: flat-pool selection with lifecycle states

## Summary

Replaced tier1/tier2 model selection with a flat-pool, evidence-driven router
that selects models based on measured quality, latency, and quota — not list
position. Three selection modes (deterministic, weighted_pool, diverse_panel)
serve different task types. Lifecycle states (active/candidate/quarantined/retired)
gate eligibility. Hierarchical circuit breakers prevent quarantine cascades.
The design converged across three independent lenses (Grok, Codex, ChatGPT)
through structured design dialogue.

## Design decisions (with rationale)

### No tiers

Tier1/tier2 was implicit list ordering: scan tier1, take first available.
This created several problems: tier1 wasn't demonstrably "better," quality
evidence was uneven across tiers, and adding weights created an undefined
tier-vs-weight conflict. Flat pool with evidence-derived ranking replaces
both concepts cleanly.

### Three selection modes

| Mode | When | Mechanism |
|------|------|-----------|
| `deterministic` | Mechanical, coding, routine work | Rank by evidence quality × speed × quota headroom; return top |
| `weighted_pool` | Reasoning pool | Weighted random from evidence-derived weights |
| `diverse_panel` | Critique, cross-family review | Constraint satisfaction maximizing provider diversity |

Weighted random is a MODE for the reasoning pool, not the universal algorithm.
Routine work stays deterministic — making it nondeterministic would solve no
problem and create unpredictability.

### 4-tuple evidence identity

Every evidence record is keyed by `provider + model + invocation_method +
orchestrator`. The same model via different transports under different
orchestrators produces separate evidence. A model that works under Grok's
spawn contract but fails under Codex's runner → Pi chain has distinct
evidence for each path.

### Policy gates before evidence weighting

Policy states (`use_freely`, `reasoning_pool`, `explicit_approval`, `excluded`)
are HARD GATES that filter candidates BEFORE weighting. `use_freely` means
"no quota-conservation or approval restriction," NOT "always select this
model." The order is:

```
safety/capability gates → approval/quota policy → task evidence floor → selection mode
```

### Bayesian freshness shrinkage (not decay)

Old evidence doesn't decay toward zero or toward the model's own average.
Instead, the posterior confidence interval widens (sample-size adjustment).
A proven model with old evidence has a wider posterior but the same mean —
lower confidence, not lower quality. A new model with zero evidence starts
neutral.

### Hierarchical circuit breakers

Three levels of quarantine prevent cascade failures:
1. **Transport-level**: if spawn fails, try PI/HTTP before giving up on the model
2. **Model-level**: all transports failed → quarantine the model
3. **Provider-level**: ≥N models from same provider fail in same window → quarantine the PROVIDER (prevents cascade)

Provider-level quarantine auto-clears after a configurable cooldown with
automatic reprobe.

### Bounded exploration per lane

Epsilon-greedy exploration prevents evidence self-reinforcement (models
selected more accumulate more evidence, reinforcing their position).
Exploration is per-lane and gated by task policy: disabled for writes,
configurable for reads/mechanical/reasoning.

### Shared schema, native selectors

One canonical registry (`fleet-models.json` v5) shared between Grok (Python)
and Codex (Node/JS). Each side implements its own native selector from the
same schema spec. Golden test vectors (25 self-contained cases) prove
conformance. CI runs golden vectors on every selector change.

## What this replaces

- `tier1`/`tier2` arrays in fleet-models.json → flat `candidates` array
- First-available selection (`pick()` scans tier1 then tier2) → evidence-weighted selection
- Static `quality_scores` → evidence accumulator computes from telemetry with Bayesian shrinkage
- Manual model health tracking → hierarchical circuit breaker with auto-quarantine + auto-reprobe

## Implementation

11 tasks across 4 parallel waves. 7 Python modules, ~10K lines, 390 tests.

| Module | Responsibility |
|--------|----------------|
| `registry_schema.py` | Schema definition + validation |
| `evidence_accumulator.py` | Reads telemetry, computes evidence with Bayesian shrinkage |
| `circuit_breaker.py` | Hierarchical health monitoring |
| `model_router.py` | Three selectors + gate chain + receipts |
| `benchmark_runner.py` | Codex→Pi benchmark promotion gate |
| `golden_vectors.py` | Grok/Codex conformance verifier |
| `snapshot_manager.py` | Versioned routing snapshots + rollback |
| `pick_model.py` | Migrated picker delegating to model_router |

## Selection receipt

Every selection produces an auditable receipt:

```json
{
  "selected": "model-slug",
  "selection_mode": "deterministic",
  "eligible_candidates": [...],
  "weights": {...},
  "gates": {"capability": true, "policy": true, "health": true},
  "gates_failed_by_others": {"slug": "policy=excluded"},
  "random_seed": 12345,
  "quota_snapshot": {...},
  "timestamp": "..."
}
```

## Remaining work

- Codex (JS) side: implement same gate chain + selectors from shared schema
- CI: golden vectors running on every selector change (both repos)
- Model promotion: benchmark the 12 candidate models through the full dispatch path
