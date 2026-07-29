---
title: "Coding model pool: tier-1 and tier-2 selection with benchmark evidence"
created: 2026-07-29
source: session-2026-07-28/29 (fleet benchmark sweep + multi-problem code-exec)
tags: [models, coding, benchmark, tier-1, tier-2, model-pool, routing, go, skill-graph, capability-node]
summary: >
  Benchmark-derived coding model pool for fleet skills. Tier-1: mistral-medium-latest
  (5/5 HumanEval, 2s, no rate limits), nim-openai-gpt-oss-20b (4/5, 8s, NVIDIA-hosted,
  no rate limits), minimax-m3 (4/5, 6s, subscription). Tier-2: glm-5-2, nvidia-nemotron-3-super-120b,
  zen-deepseek-v4-flash-free. Groq models excluded from tier-1 due to rate limiting
  on sustained multi-call sequences. Pool selection based on 5-problem HumanEval
  code-exec pass rate, not single-shot tests.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-verified
relations:
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: refines
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
  - target: wiki/concepts/parameter-aware-benchmark-tier-system.md
    type: grounded-by
  - target: wiki/concepts/groq-free-tier-tpm-limit-6000.md
    type: related
  - target: wiki/concepts/capability-node-architecture.md
    type: implements
  - target: capabilities/coding-model-pool.md
    type: design-notes-for
---

# Coding model pool: tier-1 and tier-2

## Decision context

The fleet has 74 models across 8 providers. Not all can write working code.
The benchmark's code-exec tier (HumanEval-style problems with sandboxed
execution) provides empirical pass/fail data. Skills like `/go`, `/review`,
and `/check` need to know which models to spawn for coding tasks — using
a model that fails code-exec wastes a subagent slot and produces incorrect
output.

This pool is consumed by the `coding-model-pool` capability node
(`capabilities/coding-model-pool.md`), which skills reference via
frontmatter `consumes:` declarations.

## Tier-1: Primary coding pool

These models pass code-exec, sustain multi-call sequences, and scored
13/13 on deep-reasoning. Use these for agent loops, subagent dispatches,
and any task that generates or modifies code.

| Model | Provider | Code-exec | Reasoning | Speed | Quota | Why tier-1 |
|---|---|---|---|---|---|---|
| **or-ling-3-flash-free** | OpenRouter (free) | 5/5 | 13/13 | 2.2s | 20 RPM, 50-1000 RPD | Perfect quality, fastest, $0/M |
| **mistral-medium-latest** | Mistral (free) | 5/5 | 12/13 | 6.9s | No limits observed | Perfect code quality, reliable |
| **nim-openai-gpt-oss-20b** | NVIDIA (free) | 4/5 | 13/13 | 7.7s | No limits | GPT-OSS family, spawn verified |

**Selection priority within tier-1:**
1. or-ling-3-flash-free (fastest, perfect quality+reasoning, $0/M)
2. mistral-medium-latest (if Ling rate-limited or unavailable)
3. nim-openai-gpt-oss-20b (if both unavailable)

## Tier-2: Fallback coding pool

When all tier-1 models are unavailable (provider down, quota exhausted),
these pass code-exec and scored 12-13/13 on reasoning:

| Model | Provider | Code-exec | Reasoning | Limitation |
|---|---|---|---|---|
| **go-deepseek-v4-flash** | OpenCode Go (sub) | 5/5 | 13/13 | Subscription cost; OpenCode Go upstream reliability |
| **minimax-m3** | MiniMax (sub) | 4/5 | 13/13 | Subscription quota (4,500/5h); agentic #97/129 |
| **zen-deepseek-v4-flash-free** | Zen (free) | 4/5 | 13/13 | OpenCode Zen reliability varies |
| **glm-5-2** | GLM (sub) | 4/5 | 12/13 | Reasoning-token exhaustion; reserve for thought-partner role |

## Excluded from coding pool

| Model | Why excluded |
|---|---|
| **Groq models (all)** | TPM cap (6000-8000) blocks spawn_subagent entirely. 54K system prompt exceeds limit. |
| **gemma-4-31b-it** | 1/5 on code-exec. Strong reasoning but poor code generation |
| **nvidia-nemotron-mini-4b** | Context limit error; 4B params too small |
| **nvidia-llama-3-1-8b** | 2/5 code-exec. Inconsistent quality |
| **go-kimi-k2-7-code** | OpenCode Go upstream failure (all calls return "Error from provider") |
| **go-kimi-k3** | Operator exclusion directive |
| **Gemini Flash models** | Google free-tier RPD cap causes 429 under load (6/13 calls failed in sweep) |
| **or-morph-morph-v3-*** | Reject multi-turn API (no system message support) |
| **or-arcee-ai-virtuoso-large** | Provider endpoint down |

## How skills consume this pool

Skills that dispatch subagents for coding tasks should reference the
`coding-model-pool` capability node:

```yaml
# In SKILL.md frontmatter
consumes: [coding-model-pool]
```

At dispatch time, the skill reads the capability contract
(`capabilities/coding-model-pool.md`) for the current tier-1 list and
selects the first available model. If all tier-1 models fail, it falls
to tier-2.

For `/go` specifically: the H4 parallel wave dispatches coding subagents.
Each subagent should use a tier-1 model from this pool rather than
inheriting parent Grok. The model can be specified via:

```python
spawn_subagent(
    model="nim-openai-gpt-oss-20b",  # from coding-model-pool tier-1
    ...
)
```

## Evidence

- **5-problem HumanEval code-exec sweep** (session 2026-07-29): all data
  in this concept is from empirically verified benchmark runs
- **Parameter-aware benchmark tier system** ([[parameter-aware-benchmark-tier-system]]):
  the benchmark infrastructure that produced this data
- **Groq rate limiting** ([[groq-free-tier-tpm-limit-6000]]): documents
  why Groq is excluded from sustained coding tasks
- **Model pool selection policy** ([[model-pool-selection-policy-speed-quota-diversity]]):
  the general policy this refines for the coding-specific case

## Falsifier

This pool is wrong if:
- A tier-1 model fails code-exec on a subsequent run (transient failure
  vs structural failure — re-run to confirm)
- A tier-2 model consistently outperforms a tier-1 model on harder problems
  (would indicate the 5-problem test set is too easy to discriminate)
- Groq raises its rate limits to sustain multi-call sequences (would
  re-qualify Groq models for tier-1)
- A new model is added to the fleet that passes code-exec with better
  speed/quality than existing tier-1 (would enter tier-1)

## Maintenance

Re-run `python benchmark.py --tier code-exec --skip-paid` monthly to verify
tier-1 models still pass. Provider-side model updates can silently degrade
quality. The benchmark's telemetry tracks quality over time via
`analyze.py --trend`.
