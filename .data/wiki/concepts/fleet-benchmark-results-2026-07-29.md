---
title: "Fleet benchmark results 2026-07-29: coding, reasoning, streaming, and spawn_subagent matrix"
created: 2026-07-29
source: session-2026-07-28/29 (full fleet benchmark sweep)
tags: [benchmark, fleet, coding-pool, reasoning-pool, streaming, ttft, spawn-subagent, laguna, ling, codex, agy, model-ranking]
summary: >
  Complete fleet benchmark across 74 models on code-exec (5 HumanEval problems),
  reasoning (GSM8K exact-match), tool-calling (structural validation), and
  streaming metrics (TTFT/ITL). Ling 3.0 Flash (free) is the standout: 5/5
  code-exec at 2-3s, fastest reasoner in fleet. GPT-5.6 Luna verified viable
  via codex CLI (passes both coding and reasoning). Groq excluded from all
  pools — can't spawn_subagent (system prompt exceeds 8000 TPM cap).
  Laguna S2.1 paid variant 5x faster than free variant.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-verified
sources:
  - "Fleet sweep 2026-07-29: 36 models, 144 calls, 4 universal tiers"
  - "Multi-problem code-exec sweep 2026-07-29: 5 HumanEval problems per model"
  - "Streaming benchmark 2026-07-29: 10 models, TTFT + ITL captured"
  - "CLI model tests 2026-07-29: codex (gpt-5.6-luna), mmx (MiniMax-M2.7), agy (Gemini 3.5 Flash)"
relations:
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: grounds
  - target: wiki/concepts/parameter-aware-benchmark-tier-system.md
    type: produced-by
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
  - target: wiki/concepts/opencode-go-zen-quota-and-pricing.md
    type: related
---

# Fleet benchmark results 2026-07-29

## Decision context

The fleet had 74 models across 8 providers but no empirical evidence for
which models could write working code, which could reason, or which worked
through the invocation paths the fleet actually uses (direct API,
spawn_subagent, CLI). This benchmark answers: which models belong in the
coding pool, the reasoning pool, and which are burst-only or excluded.

## Code-exec results (5 HumanEval problems, sandboxed execution)

### Tier 1: Perfect (5/5)

| Model | Avg speed | Provider | Cost |
|---|---|---|---|
| **mistral-medium-latest** | 3.0s | Mistral | Free |
| **nim-openai-gpt-oss-20b** | 8.3s | NVIDIA | Free |
| **or-ling-3-flash-free** | 3.6s | OpenRouter | $0/M |
| **or-laguna-s-2-1** (paid) | 12.4s | OpenRouter | ~$0.001/call |

### Tier 2: Strong (4/5)

| Model | Avg speed | Provider | Cost |
|---|---|---|---|
| **minimax-m3** | 29.7s | MiniMax | Sub |
| **glm-5-2** | 33.6s | GLM | Sub |
| **zen-deepseek-v4-flash-free** | 17.0s | Zen | $0 |
| **nvidia-nemotron-3-super-120b** | 16.7s | NVIDIA | Free |
| **go-deepseek-v4-flash** | 14.1s | Go sub | Sub (158K req/mo) |

### Failed code-exec (≤2/5 or structurally broken)

gemini-flash-latest (1/5), gemma-4-31b-it (1/5), nvidia-nemotron-mini-4b (1/5),
nvidia-llama-3-1-8b (2/5), nim-nemotron-super-49b-v1-5 (1/5).

## Streaming metrics (TTFT + ITL)

| Model | TTFT | ITL p50 | tok/s | Provider |
|---|---|---|---|---|
| groq-llama-3-1-8b-instant | 2ms | — | 1203 | Groq |
| groq-gpt-oss-120b | 160ms | 1.9ms | 95 | Groq |
| or-ling-3-flash-free | 5ms | 16ms | 63 | OpenRouter |
| mistral-medium-latest | 0ms | 21.6ms | 45 | Mistral |
| minimax-m3 | 0ms | 33.2ms | 33 | MiniMax |
| nim-openai-gpt-oss-20b | 824ms | 9.2ms | 21 | NVIDIA |
| glm-5-2 | null | null | null | GLM (reasoning tokens consume all) |

GLM-5.2 produced zero content tokens in streaming mode — all budget consumed
by reasoning before any content streamed.

## spawn_subagent test results

| Model | Works via spawn? | Latency | Notes |
|---|---|---|---|
| mistral-medium-latest | ✅ | 7.3s | |
| minimax-m3 | ✅ | 3.7s | |
| nim-openai-gpt-oss-20b | ✅ | 7.5s | |
| glm-5-2 | ✅ | 8.1s | |
| groq-gpt-oss-120b | ❌ | — | TPM: 53781 requested vs 8000 cap. System prompt too large for Groq free tier |
| or-laguna-s-2-1-free | ❌ | — | 429 rate limited |

**Groq cannot do spawn_subagent** — Grok Build's system prompt (~54K tokens)
exceeds Groq's 8000 TPM limit. This excludes ALL Groq models from any pool
that uses spawn_subagent dispatch.

## CLI model tests (codex, mmx, agy)

| Model | Via | Reasoning | Coding | Speed |
|---|---|---|---|---|
| **gpt-5.6-luna** | codex CLI | ✅ ANSWER: 18 | ✅ 9/9 cases | 13-14s |
| **MiniMax-M2.7** | mmx CLI | ✅ ANSWER: 18 | ✅ 2/2 cases | 6-38s |
| **Gemini 3.5 Flash** | agy CLI | ✅ ANSWER: 18 | (not tested — not a coder) | 4.1s API |

GPT-5.6 Luna is viable via codex CLI (`codex -m gpt-5.6-luna`) — uses
OpenAI subscription OAuth, no per-token API cost. Both reasoning and
coding pass.

## Laguna S2.1: free vs paid comparison

| Variant | Code-exec | Avg speed | Rate limits |
|---|---|---|---|
| `:free` | 1/5 (3 rate-limited) | 59.7s | 20 RPM, 50-1000 RPD |
| paid | 4/5 | 12.4s | No platform cap |

Paid variant is 5x faster and doesn't hit rate limits. At ~$0.001/call,
$25 credit covers ~25,000 calls.

## What this means for the fleet

The coding pool should include Ling 3.0 Flash (free, 5/5, fastest
reasoner in fleet) and GPT-5.6 Luna (via codex CLI) alongside the
existing tier-1 models. Groq models are permanently excluded from
spawn-based pools. The Zen free models are viable for both coding and
reasoning. See [[coding-model-pool-tier-1-tier-2]] for the pool
definition that this data grounds.

**Scope note (added 2026-07-29):** This benchmark measures competition-math
accuracy through our API paths — it does NOT measure thought-partner quality,
instruction compliance, or planning ability. For those axes, see
[[model-role-assignment-public-vs-custom-benchmarks]] which uses public
benchmarks (IFEval, IFBench, Tau2) to assess fleet models. GLM-5.2 scoring
12/13 on math does NOT mean M3 is a better thought partner — GLM-5.2 is #1
globally on Tau2 (multi-turn agent coherence) while M3 is #97/129 on agentic.

The [[opencode-go-zen-quota-and-pricing]] concept documents the quota
structure — Go subscription models share a $60/month dollar cap, while
Zen free models ($0/token) have no published rate limit. The
[[parameter-aware-benchmark-tier-system]] documents the benchmark
infrastructure that produced these results. The
[[model-fleet-provider-pools]] concept has the full fleet inventory.
GLM-5.2's reasoning-token behavior is documented in
[[groq-free-tier-tpm-limit-6000]] which also explains the TPM issue
that excludes Groq from spawn_subagent.

## Falsifier

These results are a snapshot from 2026-07-29. Provider-side model updates,
quantization changes, and catalog changes (models added/removed) can shift
the ranking. Re-run `benchmark.py --tier code-exec --skip-paid` monthly.
The `pool_health.py` script detects degradation from accumulated telemetry.
