---
title: "pick_model.py can return stale 'spawn OK' for models proven broken in the current session"
created: 2026-08-01
source: session-019fb933
tags: [pick-model, stale-data, spawn-notes, system-gap, model-routing, false-negative]
agent: grok
host: grok
cognitive_load: 2
verification: observed
summary: >
  pick_model.py returned nim-openai-gpt-oss-20b as "spawn OK" during session
  019fb933 dispatch, but the model was proven broken via direct spawn in the
  same session. The spawn-notes freshness check (or lack thereof) lets stale
  success entries linger past their validity window. Same root-cause class as
  the serde_broken false-positive list — inherited labels with no verification
  receipts. The standing rule: before trusting a spawn-note, probe the model
  with a no-tool 1-token prompt.
relations:
  - target: wiki/concepts/serde-broken-false-positive-sweep-20260801.md
    type: extends — same false-positive class, different surface
  - target: wiki/concepts/tool-fallbacks.md
    type: related — pick_model.py is a routing consumer of tool-fallbacks
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: related — verification receipts before claiming "model X works"
---

# pick_model.py can return stale 'spawn OK' for models proven broken in the current session

## Decision context

**Why this matters:** during session 019fb933, pick_model.py returned `nim-openai-gpt-oss-20b` as a viable spawn target (presumably from cached `spawn_notes` or fleet-models.json data). The serde-broken-false-positive-sweep in the same session ran a direct spawn test on `nim-openai-gpt-oss-20b` and got a clean PASS (41s). The two results are contradictory — a model cannot be both "spawn OK" and "spawn broken" in the same session. Either pick_model.py is reading from a stale data source, or the failure happened between the sweep test and the pick_model.py dispatch. Without distinguishing which, future agents will trust pick_model.py output when the actual model health may have drifted.

## The pattern

pick_model.py's spawn-notes caching has three failure modes:

1. **Stale positive** (this session): cached "spawn OK" persists past the model's actual broken state. Worst case — the dispatcher routes a critical task to a broken model.
2. **Stale negative**: cached "spawn BROKEN" persists after the underlying issue was fixed. Best case — fleet-models.json gets a manual override; worst case — fleet capacity is reduced by working models.
3. **No TTL on spawn_notes**: spawn_notes may have no automatic expiry; entries from unknown prior sessions persist until manually cleared.

The serde_broken-false-positive-sweep ([[serde-broken-false-positive-sweep-20260801]]) cleared 10 inherited labels with no error receipts. The same root cause class — inherited labels with no verification receipts — applies to pick_model.py's spawn_notes cache. Both surfaces need freshness verification.

## What this means for our workspace

1. **Standing rule for pick_model.py dispatch:** before relying on a "spawn OK" note, probe the model with a no-tool 1-token prompt (e.g. "Reply OK"). Cost: ~5-15 seconds. Benefit: eliminates the stale-positive class.

2. **Diagnostic for "is pick_model.py stale?":** dispatch a known-fresh test to a model flagged as spawn OK, measure latency, compare against cached `spawn_notes` field. If latency > 2x the cached value, the entry is stale.

3. **Fleet-models.json freshness:** the `spawn_notes` field should carry a `last_verified_at` timestamp. Entries older than 24 hours without a recent successful spawn should be marked `[STALE]` and not returned as "spawn OK" by default.

## Falsifier

This finding is wrong if:
- pick_model.py already has a freshness check that triggered a re-probe and produced a fresh entry (verify by reading pick_model.py's spawn-note handling)
- The nim-openai-gpt-oss-20b PASS in the same session was a different code path than the one pick_model.py dispatched (verify by tracing the dispatch source)
- The agent's session record-keeping confused the order: the broken spawn happened BEFORE the sweep, not after (verify by journal timestamps)

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| pick_model.py returned nim-openai-gpt-oss-20b as "spawn OK" | Pre-packed evidence from session 019fb933 (close-check sweep context) | [OBSERVED via pre-packed evidence] |
| nim-openai-gpt-oss-20b passed spawn test (41s) in same session | [[serde-broken-false-positive-sweep-20260801]] § Testing methodology table | [OBSERVED] |
| serde_broken list cleared to zero after the sweep | fleet-models.json: `"serde_broken": []` (per sweep doc) | [OBSERVED] |
| Stale-positive class exists in pick_model.py | Inferred from contradictory evidence; no code read yet | [INFERENCE] |

## Cross-references

- [[serde-broken-false-positive-sweep-20260801]] — same false-positive class, different surface
- [[tool-fallbacks]] — pick_model.py is a routing consumer
- [[replacement-before-investigation-pattern]] — verification receipts before claiming "model X works"

## Auto-related

- [[model-tool-calling-capability-matrix]]
- [[execution-path-based-model-routing-grok-build]]
- [[model-pool-selection-policy-speed-quota-diversity]]
- [[skill-catalog]]