---
title: "Coding model pool live test evidence: quality and latency across all provider combinations"
created: 2026-07-31
source: session-2026-07-31 (12 live model tests across 6 provider combinations)
tags: [models, coding, pool, testing, latency, quality, provider-diversity, go, spawn-subagent]
agent: grok
host: grok
verification: live-tested
---

# Coding model pool live test evidence

## What was tested

12 live `spawn_subagent` calls across 6 provider combinations, reviewing 2 code
snippets (a login function with 4 critical issues, and a Cache class with 2
critical issues + 6 medium issues). Each model reviewed both snippets. All 4
pool models were tested in all pairwise combinations.

## Quality results

Every model found every critical issue. Zero fabricated findings across all
12 tests.

| Model | Provider | Login findings | Cache findings | Fabricated? | Notes |
|---|---|---|---|---|---|
| or-ling-3-flash-free | OpenRouter | 10 | 8 | No | Most thorough. Fastest. |
| nim-openai-gpt-oss-20b | NVIDIA | 7-9 | 9 | No | Reliable, good fixes |
| minimax-m3 | MiniMax | 9 | 12 | No | Deepest analysis, slowest |
| zen-deepseek-v4-flash-free | Zen | 6 | 10 | No | Full corrected code, slow |

## Latency results

| Model | Nominal (single-shot) | Live (review task) |
|---|---|---|
| or-ling-3-flash-free | 2.2s | 7-8s |
| nim-openai-gpt-oss-20b | 7.7s | 9-13s |
| zen-deepseek-v4-flash-free | 7.4s | 28-50s |
| minimax-m3 | 7.3s | 30-60s |

**Key insight:** nominal single-shot latency underestimates real task latency
by 3-8×. Live task latency is what gates `parallel()` barriers. or-ling is
consistently fastest; minimax is consistently slowest.

## Decision rule derived from evidence

1. Default single subagent: or-ling (fastest + most thorough)
2. Parallel wave 2-4: round-robin or-ling/nim (two fastest, two providers)
3. Parallel wave 5-8: add zen, minimax for provider diversity
4. Reasoning tasks: glm-5-2 (rationed, reasoning lane only)
5. Multi-file architectural work: parent Grok (20B models untested on this)
6. 429 failover: swap provider, no retry on same

See `P:/.data/wiki/capabilities/coding-model-pool.md` for the canonical procedure.
