---
title: "Proactive-reactive pair pattern for predictable failure prevention"
created: 2026-08-06
source: session-019fc882 (design skill improvements — quota pre-check + context-size check)
tags: [pattern, architecture, proactive, reactive, failure-prevention, defense-in-depth, model-fleet, subagent-dispatch]
host: both
agent: grok
verification: observed
cognitive_load: 2
summary: >
  When a failure mode is predictable (you know the precondition that causes it),
  add a proactive check before the action that triggers it — but keep the reactive
  fallback as a safety net. The proactive layer eliminates the predictable failure
  path; the reactive layer catches the unpredictable edge cases the proactive
  check misses. This pair is defense-in-depth applied to LLM-agent infrastructure:
  the proactive check costs <10ms and runs before dispatch; the reactive hook/fallback
  costs a failed attempt but catches cases the proactive check can't predict.
relations:
  - target: wiki/concepts/model-quota-contention-coordination-fleet-rate-limiting.md
    type: extends
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md
    type: complements
  - target: wiki/concepts/multi-subagent-orchestration-workflow-failure-patterns.md
    type: related
---

# Proactive-reactive pair pattern for predictable failure prevention

## Decision context

**The problem:** the fleet had reactive-only failure prevention for subagent dispatch. The `PreToolUse_spawn_model_gate.py` hook blocked quota-exhausted and serde-broken models *after* the spawn was attempted. `/design` Step 5's "Resume failure recovery" waited for `max_tokens_truncation` *before* switching to a fresh reviewer. Both patterns guaranteed one failed attempt per predictable failure — costing 8-38 seconds per failed spawn and a wasted revision round per truncated review.

**The decision:** add proactive checks before the action, but keep the reactive mechanisms as safety nets. This is not replacing reactive with proactive — it's pairing them.

## The pattern

```
┌─────────────────────────────────────────────┐
│ PROACTIVE LAYER (primary path)              │
│ Check the precondition BEFORE the action    │
│ Cost: <10ms (local cache read)              │
│ Eliminates: the predictable failure path    │
├─────────────────────────────────────────────┤
│ ACTION (spawn / resume / dispatch)          │
├─────────────────────────────────────────────┤
│ REACTIVE LAYER (safety net)                 │
│ Catch the failure AFTER it occurs           │
│ Cost: one failed attempt (~8-38s)           │
│ Catches: edge cases the proactive miss      │
└─────────────────────────────────────────────┘
```

**Why both layers:** the proactive check reads a local cache (`pick_model.py` quota cache, line count of design doc). The cache can be stale — quota changes between check and dispatch, doc grows between check and resume, model context limit is smaller than expected. The reactive layer catches these. Without the proactive layer, the reactive layer fires every time the precondition holds (the common case). Without the reactive layer, the proactive layer misses edge cases with no recovery.

## Instances implemented (2026-08-06)

### Instance 1: Quota pre-check before subagent dispatch

| Layer | Mechanism | What it checks | When | Source |
|-------|-----------|----------------|------|--------|
| **Proactive** | `pick_model.py --list` in `/design` Step 0.9 + `~/.grok/AGENTS.md` convention | Provider quota from local cache | Before first spawn | Commit `f768c24` |
| **Reactive** | `PreToolUse_spawn_model_gate.py` hook | Live quota at spawn time | On each spawn attempt | Pre-existing |

**Failure it prevents:** 3+ failed spawn attempts on OpenCode-Go at 0% quota (observed 2026-08-03, 38 error-pattern hits in transcript).

### Instance 2: Context-size check before resume

| Layer | Mechanism | What it checks | When | Source |
|-------|-----------|----------------|------|--------|
| **Proactive** | `/design` Step 4/5 context-size check | Design doc line count >1500 OR resume count ≥2 | Before deciding resume vs fresh | Commit `4369371` |
| **Reactive** | `/design` Step 5 "Reactive fallback" | `max_tokens_truncation` error after resume attempt | After resume fails | Pre-existing (renamed from "Resume failure recovery") |

**Failure it prevents:** `max_tokens_truncation` at 175K input tokens on a 2000-line design doc (observed 2026-08-03 with MiniMax-M3).

## When to apply this pattern

The pattern applies when ALL of these hold:

1. **The failure is predictable** — you know the precondition that causes it (quota at 0%, doc too large, model serde-broken)
2. **The precondition is checkable cheaply** — local cache read, line count, registry lookup (<10ms)
3. **The reactive mechanism already exists** — you're not building from scratch; you're adding the proactive layer on top
4. **The failure is expensive** — 8-38s per failed spawn, a wasted revision round, or a truncated review that produces zero output

## When NOT to apply

- **The failure is unpredictable** (random network errors, transient rate limits) — reactive-only is correct; a proactive check can't predict these
- **The precondition check is expensive** (>100ms adds latency to every dispatch) — the check cost may exceed the failure cost at low failure rates
- **No reactive mechanism exists** — build the reactive layer first (it's the safety net), then add proactive
- **The failure rate is negligible** — if it happens once per year, the proactive check's latency cost on every invocation exceeds the one failure it prevents

## What this means for our workspace

This pattern is now the standard for subagent dispatch infrastructure. When a new predictable failure mode is discovered:

1. **First:** ensure the reactive fallback exists (hook block, resume failure recovery, error handler)
2. **Then:** add the proactive check (cache read, precondition test, line count) before the action
3. **Document both layers** — the `tool-fallbacks.md` entry should note both the proactive check and the reactive fallback, not just one

The pattern extends beyond `/design` to any skill that dispatches subagents: `/review`, `/red-team`, `/tp`, `/go`. Each skill that spawns should check its known failure preconditions before the first dispatch.

## Falsifier

The proactive-reactive pair is wrong if:

1. **The proactive check's false-negative rate is high** — if the proactive check passes but the reactive fallback fires frequently anyway, the proactive check adds latency without reducing failures. Measure: if reactive fallback fires on >20% of dispatches despite the proactive check, the proactive check is not catching the right precondition.
2. **The proactive check's false-positive rate is high** — if it prevents dispatches that would have succeeded, it's over-blocking. Measure: if the proactive check blocks >5% of dispatches that would have succeeded, the precondition threshold needs tuning.
3. **A future change makes the failure unpredictable** — e.g., provider changes quota enforcement from "block at 0%" to "throttle near limit." The proactive check's precondition would no longer predict the failure.

## Receipts

- `/design` SKILL.md "Quota pre-check" subsection (lines ~230-255): proactive `pick_model.py --list` call before first spawn. Commit `f768c24`. [OBSERVED — edited this session]
- `/design` SKILL.md Step 4 "Context-size check" (lines ~830-846): proactive doc line count + resume count check. Commit `4369371`. [OBSERVED — edited this session]
- `~/.grok/AGENTS.md` "Quota pre-check before subagent dispatch" (lines ~1245-1260): global convention. Commit `f768c24`. [OBSERVED — edited this session]
- `PreToolUse_spawn_model_gate.py` lines 200-320: reactive quota-exhausted block with fallback chain. [OBSERVED — read this session]
- `/design` SKILL.md Step 5 "Reactive fallback (safety net)" (line ~1033): renamed from "Resume failure recovery" to clarify it's the reactive layer. Commit `4369371`. [OBSERVED — edited this session]
- `pick_model.py` lines 40-50: `load_quota_cache()` reads `~/.cache/opencode/fleet-quota-cache.json` (<10ms local read). [OBSERVED — read this session]

## Sources

- Commit `f768c24` — `/design` SKILL.md "Quota pre-check" subsection + AGENTS.md convention (session 019fc882)
- Commit `4369371` — `/design` SKILL.md Step 4/5 context-size check (session 019fc882)
- `PreToolUse_spawn_model_gate.py` — existing reactive quota/serde hook (pre-existing infrastructure)
- [[model-quota-contention-coordination-fleet-rate-limiting]] — documents the reactive system and the 2026-08-03 proactive addition
- [[tool-fallbacks]] — MiniMax-M3 entry documents both proactive and reactive layers
- [[multi-subagent-orchestration-workflow-failure-patterns]] — documents the reactive-only resume failure recovery that preceded the proactive check
- [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]] — the general principle: make the correct path the easiest one (proactive check makes "pick an available model" the default path instead of "try, fail, retry")

## Auto-related

- [[agent-reliability-patterns-and-production-validation]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[skill-graph]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]

