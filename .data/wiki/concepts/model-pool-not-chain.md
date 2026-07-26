---
title: "Model pool, not model chain: qualified-pool routing vs linear fallback"
created: 2026-07-22
source: session-2026-07-21
tags: [models, routing, pool, chain, fallback, qualified, failover, fleet, grok-build, correction]
summary: >
  Models that clear the quality floor for a lane are a POOL of qualified
  candidates, not a linear fallback chain. Any pool member is acceptable;
  selection is by situational fit (context size, speed, availability),
  not by fixed ordering. The chain notation "A → B → C" in the /go spawn
  recipe and model-lanes-vs-roles implied a quality ranking that doesn't
  exist and a fallback discipline that's too rigid. This concept corrects
  both: the pool is the routing unit; the picker handles per-failure
  selection from within the pool; escalation beyond the pool (to
  subscription models) is the exception, not the default path.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
relations:
  - target: wiki/concepts/model-lanes-vs-roles
    type: corrects
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: refines
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass
    type: related
---

# Model pool, not model chain

## The correction

The `/go` spawn recipe and `model-lanes-vs-roles.md` use **chain notation**:
```
Code → ccr-ornith → diffusiongemma → m3
```

This notation implies:
1. ccr-ornith is "better" than diffusiongemma (it's first)
2. DiffusionGemma is a "fallback" (only used when ornith fails)
3. m3 is a last resort (only used when both fail)
4. Each transition is a failure event

**None of these implications are correct.** ccr-ornith, DiffusionGemma, and
MiniMax M3 all clear the quality floor for the Code lane. They are a **pool**
of qualified candidates. The operator's actual design intent (discussed
2026-07-21) was a pool, not a chain.

## Pool vs chain — what changes

| Aspect | Chain (what we wrote) | Pool (what we meant) |
|--------|----------------------|---------------------|
| Ordering | Strict: A > B > C | None: A, B, C are peers |
| Selection trigger | Failure of the prior | Situational fit (context size, speed, availability, multimodal need) |
| Switching semantics | Each switch = failure recovery | Switching = normal routing |
| Resilience | Less: if A is down, forced to B regardless of fit | More: any available pool member works |
| Quality implication | A is better than B | All clear the floor; differences are situational |
| Cost discipline | First free model wins by position | Free models preferred as a group; subscription is the escalation tier, not a position in the chain |

## The Code lane pool (qualified models)

These models have all been tested and clear the quality floor for Code-lane
work (implementation, discovery, tests, mechanical reads):

| Model | Context | Speed | Free? | Best situational fit |
|-------|---------|-------|-------|---------------------|
| `ccr-ornith` | 65K | Fast (small), slow (large reviews) | Free local | Small-medium context; when network unavailable; deep single-file analysis |
| `nvidia-diffusiongemma-26b` | 262K | 42x faster than ornith | Free NVIDIA | Large-context breadth reads; batch scanning; when ornith context too small |
| `minimax-m3` | 1M | Medium | Subscription | Large context; multimodal; when free models unavailable or quota exhausted |
| `gemini-3.6-flash` | 1M | Fast | Free (Google) | Multimodal; large context; fresh results |
| `gemini-3.5-flash-lite` | 1M | Fastest | Free (Google) | High-throughput mechanical work |

**Any of these is acceptable for Code-lane work.** The selection criteria are:
1. Context fit (does the input fit the effective budget?)
2. Availability (is the model responding?)
3. Cost preference (free > subscription, when quality is equal)
4. Special needs (multimodal, batch, specific model strengths)

**NOT a fixed ordering.**

## The Reasoning lane pool

| Model | Context | Free? | Best situational fit |
|-------|---------|-------|---------------------|
| `nvidia-nemotron-3-ultra` | 1M | Free NVIDIA | Deep reasoning; long-context analysis |
| `glm-5-2` | 1M | Subscription | When Nemotron misses the floor or quota exhausted |

**Subscription escalation** (`glm-5-2`, parent Grok) is the exception — used
when free pool members fail or are unavailable — not a position in a chain.

## What "escalation" actually means

Escalation is **leaving the pool**, not advancing within it:
- **Within-pool selection:** pick from {ornith, DiffusionGemma, m3, Gemini Flash} based on fit
- **Escalation to subscription:** only when ALL free pool members are unavailable or quality-insufficient
- **Parent model (Grok):** last resort for synthesis/judgment; not a Code-lane model at all

## How the picker fits

Per `model-picker-as-failover-not-router`: the picker handles per-failure
decisions interactively. With the pool model, the picker is choosing **which
pool member** to use, not advancing a chain. If ornith times out on a large
review, the picker doesn't "fall back to position 2" — it picks the pool
member that fits the situation (DiffusionGemma for large context, Gemini Flash
for speed, m3 for instruction-following).

## What needs to change in skills

The chain notation appears in several places and teaches the wrong mental
model. Every instance of `A → B → C` model notation should be reframed as
pool selection:

### 1. `/go` spawn recipe (`~/.grok/skills/go/SKILL.md`)

**Current (chain):**
```text
code  general + sdlc-code  medium  Code → ccr-ornith → diffusiongemma → m3
```

**Should be (pool):**
```text
code  general + sdlc-code  medium  Code pool: {ccr-ornith, diffusiongemma, gemini-flash} — pick by fit; escalate to m3 only if free pool exhausted
```

### 2. `model-lanes-vs-roles.md`

**Current:** "Primary (free)" / "Escalate" columns with DiffusionGemma labeled "Code lane fallback"

**Should be:** "Pool members" / "Escalation tier" — DiffusionGemma is not a fallback, it's a pool member with different strengths (large context, speed)

### 3. `/debrief` skill (`~/.grok/skills/debrief/SKILL.md`)

**Current:** "Each lens has a primary model and explicit fallbacks. The skill probes the first model, then falls back."

**Should be:** "Each lens has a pool of qualified models. The skill probes for availability, then picks from the pool by situational fit."

### 4. `tool-fallbacks.md`

**Current:** "Reflex pattern: built-in fails → check fallback table → run CLI equivalent"

**This is correct for TOOL fallbacks** (those ARE chains — if web_search fails, use mmx). But it should not be conflated with MODEL selection, which is pool-based.

## Why the chain notation crept in

The chain notation was inherited from the `tool-fallbacks.md` pattern (tool
fails → CLI equivalent). That pattern is correct for tools (they ARE
ordered: try the native first, fall back to CLI). It was incorrectly applied
to models, where the appropriate pattern is a pool. The two patterns are
structurally different:

| Pattern | Applies to | Logic |
|---------|-----------|-------|
| **Chain** | Tools (web_search → mmx → agy) | Try native; if fails, CLI equivalent. Ordered by integration depth. |
| **Pool** | Models within a lane | All qualified; pick by fit. Not ordered by quality. |

## Do's and don'ts

### Do
- Select from the pool by situational fit (context, speed, availability)
- Prefer free pool members as a group (cost discipline)
- Escalate to subscription only when free pool is exhausted or quality-insufficient
- Treat switching between pool members as normal routing, not failure recovery
- Use the picker for per-failure pool selection

### Don't
- Don't treat the pool as a ranked chain (A is not "better" than B)
- Don't write fallback logic that always tries A first then B — probe availability and pick by fit
- Don't label pool members as "fallback" — they're peers
- Don't escalate to subscription models just because the first free model tried failed — try another free pool member first
- Don't conflate tool-fallback chains with model-pool selection

## Relationship to existing concepts

- **Corrects** [[model-lanes-vs-roles]] — the chain notation and "fallback" labels are wrong; should be pool
- **Refines** [[model-picker-as-failover-not-router]] — the picker selects from within the pool, not from a chain
- **Related** [[compensating-for-weaker-models-ensemble-multi-pass]] — multi-pass techniques apply to pool members

## Sources

- Session 2026-07-21: operator discussion about qualified-pool model routing
- Session 2026-07-22: operator correction that the chain notation in skills led another LLM to propose a linear fallback chain (DGemma → ccr-ornith → parent), which is the wrong model
- `~/.grok/skills/go/SKILL.md` spawn recipe — the chain notation that needs correction
- `P:/.data/wiki/concepts/model-lanes-vs-roles.md` — the wiki concept that encodes the chain

## Falsifier

This concept is wrong if:
- The models in the "pool" actually DO have a consistent quality ordering (pool is fiction, chain is real)
- Situational-fit selection produces worse outcomes than fixed-ordering (the chain is actually optimal)
- The operator intended a chain all along (this concept misrepresents the design intent)

If any pattern appears within 3 months, revise or retire.

## Auto-related

- [[exemption-logic-as-conflict-signal]]
- [[handoff-pre-compact-problems]]
- [[multi-agent-correlated-errors]]

