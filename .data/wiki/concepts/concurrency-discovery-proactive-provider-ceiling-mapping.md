---
title: "Concurrency discovery — proactive provider ceiling mapping before going live"
created: 2026-08-11
source: session-019fdf47
tags: [concurrency, provider-limits, fleet-routing, capacity-gate, discovery, pool-test]
summary: >
  How to discover provider concurrency limits (how many simultaneous
  requests a provider allows) BEFORE going live, rather than learning them
  reactively from 429 errors. Three discovery modes: per-model, per-provider,
  and contention matrix. Results feed the fleet router's capacity gate.
agent: grok
host: grok
cognitive_load: 2
verification: observed
---

# Concurrency discovery — proactive ceiling mapping

## Decision context

The fleet needed to know how many parallel subagents could safely dispatch to each provider. Without this, dispatching 8 parallel subagents to MiniMax could cause 6 of them to 429 — wasting time and corrupting benchmark data. The question: do we discover these limits reactively (wait for 429s) or proactively (probe them)?

## The discovery method

Three discovery modes, implemented in `concurrency_probe.py`:

### 1. Per-model (binary search)

Fire 2, 4, 8, 16 simultaneous requests to the **same model**. Binary search for the ceiling where 429s start.

```
N=4: 4/4 OK → go higher
N=8: 8/8 OK → go higher  
N=16: 14/16 OK, 2× 429 → back off
→ Ceiling: 8 concurrent requests for this model
```

### 2. Per-provider (cross-model contention)

Fire 1 request each to **N different models** on the same provider simultaneously. If all succeed: no shared pool. If some 429: shared pool detected.

```
8 different MiniMax models simultaneously → 2/8 succeeded, 6× 429
→ Shared pool detected, ceiling ≈ 2
```

### 3. Contention matrix

Fire N requests to model-A + N to model-B simultaneously. Detects whether two specific models share a pool.

## Empirical results (4 providers, 2026-08-11)

| Provider | Per-model ceiling | Per-provider (cross-model) | Shared pool? |
|----------|------------------|---------------------------|-------------|
| **MiniMax** | 8+ (all models) | **2/8 succeeded** | Yes — strict cap |
| **NVIDIA** | 5-7 per model | 7/8 succeeded | Yes (1 timeout, not 429) |
| **ZAI** | 4-7 per model | 7/7 succeeded | No — full parallelism |
| **OpenRouter** | not tested per-model | 8/8 succeeded | No — best for parallel |

MiniMax is the critical finding: despite each model handling 8 concurrent requests alone, only ~2 can run across the provider simultaneously. This is the exact "provider allows 6 concurrent but only 1 per model" scenario the operator flagged.

## What this means for our workspace

**The fleet router's concurrency gate** (`concurrency_gate.py`) reads `concurrency-limits.json` and blocks dispatches exceeding provider ceilings. When dispatching parallel subagents:

- MiniMax: cap at 2 total concurrent (3rd blocked with fallback suggestion)
- NVIDIA/ZAI: cap at 7 concurrent
- OpenRouter: cap at 8 concurrent (free tier)

The in-flight tracker uses a shared state file with TTL cleanup (5 min) so crashed processes don't permanently hold slots.

**The concurrency gate is wired into both:**
1. `pick_model.py` gate_results() — 6th gate in the selection chain
2. `PreToolUse_spawn_model_gate.py` — acquire on spawn, `PostToolUse_spawn_release.py` — release on completion

## Falsifier

This approach is wrong if:
- Provider concurrency limits change frequently (the probe data goes stale). **Mitigation:** re-probe periodically or after observing unexpected 429 patterns.
- The probe itself causes rate-limiting that skews results. **Mitigation:** probes use minimal tokens (5 max_tokens) and inter-probe delays.
- The concurrency ceiling is token-based, not request-based (e.g., 100K tokens/min regardless of request count). **Not yet tested.** If providers enforce TPM limits, request-count ceilings are insufficient.

## Receipts

- Implementation: `~/.grok/skills/model-benchmark/scripts/concurrency_probe.py`
- Gate: `~/.grok/skills/model-quota/scripts/concurrency_gate.py`
- Data: `P:/.artifacts/model-telemetry/concurrency-limits.json`
- Spawn hook wiring: `~/.grok/hooks/PreToolUse_spawn_model_gate.py` (Check 3)
- Release hook: `~/.grok/hooks/PostToolUse_spawn_release.py`

Related: [[diagnostic-logging-by-default-in-fleet-tooling]], [[shared-dispatch-component-deep-module-pattern]], [[provider-wide-api-discovery-not-curated-registry]], [[model-pool-selection-policy-speed-quota-diversity]]

## Auto-related

- [[skill-graph]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[model-fleet-provider-pools]]
- [[proactive-reactive-pair-pattern-for-predictable-failure-prevention]]
- [[model-quota-contention-coordination-fleet-rate-limiting]]

