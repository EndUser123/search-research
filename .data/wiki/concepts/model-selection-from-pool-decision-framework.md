---
title: "Model selection from the pool: the decision framework"
created: 2026-07-22
source: session-2026-07-22-www
sources:
  - https://www.mindstudio.ai/blog/ai-model-routing-frontier-vs-cheap-models-agent-stack
  - https://www.truefoundry.com/blog/llm-routing-cost-quality-aware-model-selection
  - https://arxiv.org/html/2603.04445v2
  - https://arxiv.org/html/2601.19793v1
  - http://minlanyu.seas.harvard.edu/writeup/sllm25-score.pdf
  - https://arxiv.org/html/2502.00409v2
  - P:/.data/wiki/concepts/model-pool-not-chain.md
  - P:/.data/wiki/concepts/model-lanes-vs-roles.md
tags: [models, routing, selection, decision-framework, cost, latency, quality, quota, pool, subscription, free-tier, cascade, failover]
summary: >
  How to pick ONE model from the pool for a given task. The pool-not-chain
  concept established that pool members are peers (not ranked); this concept
  answers the follow-up: given peers, what determines the pick? Six elements
  (task-novelty, quality-floor, latency-sensitivity, context-fit, cost-regime,
  quota-strategy) collapse into a decision order. The subscription+quota model
  is a strategic reserve for novel/high-stakes/load-bearing work and for
  reliability when free tiers rate-limit — NOT the default for mechanical work
  that a free-fast-good model clears the floor on.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/model-pool-not-chain
    type: extends
  - target: wiki/concepts/model-fleet-provider-pools
    type: complement
  - target: wiki/concepts/model-lanes-vs-roles
    type: extends
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: related
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass
    type: related
---

# Model selection from the pool: the decision framework

## Step 0 — identify the elements first 

Before any decision rule, name what you are trading. Six elements, grouped:

### Task-side (what the work demands)

| Element | Question | Why it matters |
|---------|----------|----------------|
| **1. Task novelty** | Is this a task the model has "seen a thousand times," or one it must "imagine"? | mindstudio: frontier models win on novel/ambiguous; cheap models win on well-defined repeated tasks. This is the single highest-leverage discriminator. |
| **2. Quality floor** | What is the minimum acceptable output quality for THIS output's downstream use? | A verification gate, a human reader, a throwaway scratch — different floors. Below-floor output is waste regardless of cost. |
| **3. Latency sensitivity** | Is the user blocked waiting, or is this background work? | Interactive turns value sub-second response; batch jobs tolerate minutes. |

### Model-side (what the candidate offers)

| Element | Question | Why it matters |
|---------|----------|----------------|
| **4. Context fit** | Does the input + expected output fit the model's *effective* budget (~40-50% of rated)? | SCORE: a model that drops context produces below-floor quality regardless of its rated window. |
| **5. Cost regime** | Free, free-with-limits, subscription-marginal, or per-token-paid? | "Free" vs "paid" is too coarse — see cost regimes below. |
| **6. Quota strategy** | Is this model's quota a resource I must preserve for later? | Subscription quota is finite and cyclical; free-tier quota is shared and unpredictable. Burning either on the wrong task creates a later shortage. |

**Why enumerate elements before the rule:** a decision rule that doesn't name what it's trading (e.g., "always pick free first") silently encodes weights on elements 1-6. Surfacing the elements makes the weights inspectable and overridable.

## Cost regimes (element 5, expanded — "free vs paid" is too coarse)

The real cost landscape has four regimes, and they behave differently:

| Regime | Examples on this host | Marginal cost | Quota character | Failure mode |
|--------|----------------------|---------------|-----------------|--------------|
| **Free, local** | `ccr-ornith` | Zero | Unlimited (your hardware) | Offline; limited ctx |
| **Free, hosted** | `nvidia-*`, `zen-*-free`, `or-*-free`, `gemini-*-flash-lite` | Zero | Shared/pooled, rate-limited, can 429 | Unpredictable 429 under load (this session hit it on minimax-search) |
| **Subscription, flat-rate** | Grok Token Plan, parent-inherited | Near-zero per call (you pay the sub regardless) | Finite per cycle, then hard-stop | "Token Plan usage limit reached" mid-task (this session hit it on subagents) |
| **Per-token paid** | (not in current config, but `go-*` routes through paid OpenRouter) | Linear in tokens | Effectively unlimited if funded | Bill shock at scale |

**Insight from truefoundry:** "cheapest" must mean **total expected request cost**, not the nominal input-token rate. Adjust for: expected output tokens (often 3-5x input), cache-hit rate, retry/hedge probability, cascade-escalation probability, tokenizer differences across families (Anthropic notes Opus emits ~35% more tokens for the same text). Estimate from real traces, not rate cards.

## The decision order (when to pick which)

This is the core strategy. It is an **ordered filter**, not a scoring function — each stage narrows the pool before the next applies.

### Stage 1 — Task novelty gates the lane (element 1)

```
Is the task NOVEL (imagine) or REPEATED (execute)?
  ├─ Repeated/mechanical (extract, classify, summarize-known, batch-read, format)
  │     → Code lane pool (free-first)
  └─ Novel/ambiguous (plan, reason, design, synthesize-unknown, critique)
        → Reasoning lane pool
```
**Why first:** putting a mechanical task in the Reasoning lane wastes 50-200x cost for zero quality gain (mindstudio: cost gap is 50-200x per token, not 2-3x). Putting a novel task in the Code lane produces below-floor output. Lane choice is the largest single lever.

### Stage 2 — Quality floor filters within the lane (element 2)

Within the chosen lane, drop any model that cannot meet the output's quality floor for this task.
- Throwaway scratch / internal note → any pool member
- Verification gate downstream (tests, lint, review) → models with observed reliability on this task type
- Human-facing / load-bearing / hard-to-reverse → models with the highest observed quality, cost be damned

### Stage 3 — Context fit hard-gates (element 4)

Drop models whose **effective** budget (~40-50% rated) cannot hold input + expected output. A 65K-rated model is wrong for a 50K-token breadth dump regardless of its other merits.

### Stage 4 — Cost regime + quota strategy resolve the survivors (elements 5 + 6)

Among models still qualified (right lane, above floor, context fits), pick by cost regime — **but with quota strategy layered in**:

- **Default:** free-first. Prefer `{free-local, free-hosted}` over subscription, over per-token.
- **Quota-strategy override:** if the task is **load-bearing** (production, hard-to-reverse, blocks other agents) AND free-tier quota is observed-flaky, prefer the **subscription model** even though free is available — you are paying for guaranteed capacity, not for quality. This is the reliability hedge.
- **Subscription-preservation override:** if the task is mechanical AND you are running many of them, do NOT burn subscription quota on them — you will need it for the next novel task. Free-first here is quota-preservation, not just cost-saving.

## The specific question: subscription-with-quota vs free-fast-good

The trigger for using the **subscription** model (not the free-fast-good one) is ONE of:

| Trigger | Why subscription wins | Source |
|---------|----------------------|--------|
| **Task is novel/reasoning** and no free model clears the quality floor | Free-fast-good is not actually "good" here — it's below floor | mindstudio, SCORE |
| **Task is load-bearing / irreversible** and free-tier quota is flaky | You're buying guaranteed capacity, not quality | truefoundry (routing ≠ failover) |
| **Free tier is currently rate-limiting** (429 observed) | Free is not available; subscription is the failover tier | This session (minimax-search 429 → fell back to firecrawl) |
| **Task needs subscription-only capability** (tool the free model lacks, specific instruction-following reliability, multimodal) | Capability filter, not cost | truefoundry §1 |

**The trigger for free-fast-good** (the default for mechanical work) is ALL of:
- Task is repeated/mechanical (not novel)
- A free model clears the quality floor for it
- Free-tier quota is not currently exhausted
- No subscription-only capability is required

The defaults are asymmetric on purpose: **free is the default for mechanical work; subscription is the exception that must justify itself.** This is the inverse of "burn the subscription because it has quota" — quota is a reserve, not a budget to spend down.

## Anti-pattern: the silent cascade-escalation drain

From truefoundry's "Northwind" incident: a cascade verifier drifted, silently escalated ~90% of traffic to the most expensive model, bill tripled, nothing alerted. **Lesson for this host:** if you build a "try free, fall back to subscription" cascade, the **escalation rate is a live cost variable you must monitor.** A drifting verifier (or a flaky free endpoint) turns "free-first" into "subscription-always" without any error.

Mitigation: track escalation rate per task type. If it climbs above ~20%, the free tier is no longer carrying its weight for that task — either fix the verifier/endpoint or reclassify the task as subscription-appropriate.

## Anti-pattern: fail-then-retry cascades (CASTER)

CASTER (arxiv 2601.19793): "one-shot routing for hard tasks eliminates redundant weak calls — intelligent discrimination is economically superior to reactive cascading." The cascade pattern (cheap tries first, escalates on failure) **double-bills** when the cheap model fails: you pay for the failed cheap call AND the escalation. For tasks you can predict are hard, route directly to the capable model.

**Applied:** don't run DGemma → ccr-ornith → parent as a try-each-in-order cascade. Predict task difficulty upfront (Stage 1) and route directly. Reserve the cascade for genuinely uncertain tasks, and cap retries.

## Decision checklist (paste into the turn)

```
[ ] Lane: novel→Reasoning, repeated→Code
[ ] Floor: what quality does the downstream use demand?
[ ] Context: does input+output fit effective budget (~40-50% rated)?
[ ] Cost regime: free-local > free-hosted > subscription > per-token (default)
[ ] Quota override: is this load-bearing + free-tier-flaky? → subscription for reliability
[ ] Quota override: is this mechanical + high-volume? → free, preserve subscription
[ ] Novelty override: is this novel + no free model clears floor? → subscription for quality
[ ] Avoid: fail-then-retry cascade on predictable-hard tasks (route directly)
[ ] Monitor: if you built a cascade, track escalation rate
```

## Do's and don'ts

### Do
- Identify the 6 elements BEFORE picking
- Default free-first for mechanical work; make subscription justify itself
- Treat subscription quota as a **reserve** for novel/load-bearing/flaky-free-tier situations
- Route novel tasks directly to the capable model; don't cascade
- Measure escalation rate if you cascade; a drifting cascade silently moves you to the expensive tier
- Estimate total request cost (output tokens, retries, escalation prob), not nominal rate

### Don't
- Don't pick a model without naming which element you're optimizing (silent weighting)
- Don't burn subscription quota on mechanical work just because "it has quota"
- Don't assume free = fast (SCORE: cheaper ≠ faster; load and architecture matter)
- Don't conflate routing (optimization) with failover (availability) — truefoundry
- Don't treat the pool as ranked (see [[model-pool-not-chain]])

## Mapping to this host's pools

| Trigger | Pick from | Examples |
|---------|-----------|----------|
| Mechanical breadth read, ctx < 65K | Code pool, free-first | `ccr-ornith` |
| Mechanical breadth read, large ctx | Code pool, free-large-ctx | `nvidia-diffusiongemma-26b`, `gemini-2.5-flash-lite` |
| Mechanical, free tier 429'd | Code pool, subscription | `minimax-m3` (subscription), or wait for reset |
| Novel reasoning, free clears floor | Reasoning pool, free-first | `nvidia-nemotron-3-ultra`, `zen-nemotron-3-ultra-free` |
| Novel reasoning, free misses floor | Reasoning pool, subscription | `glm-5-2` |
| Load-bearing + free flaky | Subscription for reliability | parent-inherited, `minimax-m3` |
| Synthesis / judgment (Tier 3) | Parent | parent-inherited (Grok) |

## Relationship to existing concepts

- **Extends** [[model-pool-not-chain]] — that concept says pool members are peers; this says how to pick among peers
- **Extends** [[model-lanes-vs-roles]] — that concept defines the two lanes; this defines selection within a lane
- **Related** [[model-picker-as-failover-not-router]] — the picker implements this selection interactively per-failure
- **Related** [[compensating-for-weaker-models-ensemble-multi-pass]] — ensemble techniques can raise a free model above the floor, deferring subscription escalation

## Falsifier

This framework is wrong if:
- A fixed ordering (chain) consistently produces better outcomes than element-based selection — then the elements are fiction and the pool is actually ranked
- Subscription-quota-as-reserve is wrong — if spending subscription quota freely never causes a later shortage, the "reserve" framing is unnecessary
- The 6 elements are not independent — if 2-3 collapse into one, the enumeration is over-specified

Re-evaluate if any pattern appears within 3 months.

## Sources (scored CREDIBLE-lite)

| Source | Auth | Rec | Evid | Bias | Total | Role |
|--------|------|-----|------|------|-------|------|
| mindstudio blog | 2 | 3 | 3 | 2 (vendor) | 10 | frontier-vs-cheap decision rules; 50-200x cost gap |
| truefoundry blog | 2 | 3 | 3 | 2 (vendor) | 10 | routing≠failover; total-cost; cascade escalation drain |
| arxiv 2603.04445 (routing survey) | 3 | 3 | 3 | 3 | 12 | routing vs cascading taxonomy |
| arxiv 2601.19793 (CASTER) | 3 | 3 | 3 | 3 | 12 | one-shot routing > reactive cascade; 72.4% cost reduction |
| Harvard SCORE (ICLR 2025) | 3 | 3 | 3 | 3 | 12 | constrained optimization: quality s.t. cost+latency; cheaper≠faster |
| arxiv 2502.00409 (Doing More with Less) | 3 | 3 | 3 | 3 | 12 | §2 elements to optimize for routing |

Phase 2 synthesis: parent-inherited model (subagent spawns rate-limited this session).

## Auto-related

- [[multi-agent-correlated-errors]]
- [[skill-catalog]]

