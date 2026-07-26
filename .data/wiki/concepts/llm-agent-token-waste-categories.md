---
title: "LLM agent token waste: 3 categories, 59% in verification, and what to detect"
created: 2026-07-22
source: session-019f8507 (/www research on token efficiency detection)
sources:
  - https://arxiv.org/abs/2509.23586 (AgentDiet, Xiao et al., PACMSE 2026)
  - https://arxiv.org/abs/2601.14470 (Tokenomics, Salim et al., 2026)
  - https://arxiv.org/abs/2604.22750 (Stanford, Bai et al., 2026)
tags: [token-efficiency, waste-detection, trajectory-reduction, AgentDiet, Tokenomics, amplification, LLM-agent]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  LLM agent trajectories contain widespread waste in three categories
  (useless, redundant, expired). 59.4% of tokens go to iterative
  verification (Code Review), not code generation. Input tokens
  dominate (53.9%). Agentic tasks consume 1000x more tokens than code
  chat. Detection should use behavioral pattern proxies, not exact
  token counting (which is unreliable at the application level).
  Context amplification compounds: a 15KB read persists for all
  remaining turns, with KV-cache discounting making subsequent
  reads ~10x cheaper than the first.
---

# LLM agent token waste: 3 categories, 59% in verification, and what to detect

## The three waste categories (AgentDiet taxonomy)

Source: Xiao et al. (2025), arXiv:2509.23586, published in PACMSE.
Studied 100 trajectories from SWE-bench Verified (Claude 4 Sonnet).

| Category | Definition | Example | Detector proxy |
|---|---|---|---|
| **Useless** | Irrelevant to the task; can be safely removed | Cache files (`__pycache__`), verbose build output (`make[2]: Entering directory`), files irrelevant to the fix | `detect_oversized_read` (result > 10KB when limit was available) |
| **Redundant** | Same information appears multiple times; extra copies removable | File read 3x; validator run 4x; same error output in context | `detect_context_rederivation` (file read ≥3x), `detect_redundant_verification` (validator ≥3x without edits) |
| **Expired** | Was relevant, no longer is — superseded by later reads or actions | Early exploration of a file later replaced by a targeted grep; intermediate states superseded by final state | `detect_expired_context` (file read in first 1/3 of session, never referenced again after a related read) |

AgentDiet removes **39.9-59.7% of input tokens** by identifying and
reducing these categories — without hurting agent performance.

## Where tokens go (Tokenomics)

Source: Salim et al. (2026), arXiv:2601.14470. Analyzed 30 ChatDev
tasks with GPT-5 reasoning model.

| Stage | % of total tokens | Notes |
|---|---|---|
| **Code Review** (iterative verification) | **59.4%** | The dominant cost; not code generation |
| Coding | ~15% | Initial generation is cheap |
| Design | ~8% | |
| Testing | ~10% | |
| Documentation | ~5% | |
| Code Completion | ~3% | |

**Input tokens = 53.9% of total.** The primary cost driver is reading
context, not generating output.

## How expensive is agentic vs non-agentic

Source: Bai et al. (2026), Stanford Digital Economy Lab, arXiv:2604.22750.

| Task type | Token consumption |
|---|---|
| Code reasoning (single turn) | ~500-1,000 tokens |
| Code chat (single exchange) | ~1,000-3,000 tokens |
| **Agentic coding task** | **~1,000,000+ tokens** (1000x more) |

Key findings:
- Token usage is highly stochastic: same task can differ by **30x** between runs
- Higher token usage does NOT improve accuracy; accuracy peaks at intermediate cost and **saturates**
- Models vary by 1.5M+ tokens on the same tasks (Kimi-K2 vs GPT-5)
- Frontier models can't predict their own token usage (correlation ≤0.39)

## Context amplification model

A read at turn 5 of a 40-turn session doesn't cost just `file_size`. It
stays in the trajectory and is included in every subsequent turn's input.

**Naive model:** `total_cost = file_size × remaining_turns`
- 15KB read at turn 5 in 40-turn session = 15KB × 35 = 525KB

**With KV cache:** subsequent reads are ~10x cheaper than the first.
```
total_cost = file_size + (file_size × cache_discount_factor) × remaining_turns
           = file_size + (file_size × 0.1) × remaining_turns
           = 15KB + 1.5KB × 35 = 15KB + 52.5KB = 67.5KB
```

The naive model overestimates by ~8x. Use the cached model for cost
proxies in detectors. Source: derived from KV cache mechanism
described in AgentDiet (Xiao et al., 2025, §2.1).

## What to detect (behavioral proxies, not token counting)

Token counting is unreliable at the application level (reasoning models
don't expose token counts; provider invoices don't match app-level
counts per multiple vendor sources). Use behavioral pattern proxies:

| Proxy | What it detects | Threshold | Maps to AgentDiet category |
|---|---|---|---|
| Same file read ≥3x | Redundant reads | 3+ | Redundant |
| Same validator run ≥3x without edits | Redundant verification | 3+, 0 edits between | Redundant |
| Same tool + similar args in ≥4 consecutive calls | Retry loop | 4+ calls | Useless |
| read_file result > 10KB without limit param | Oversized read | > 10KB | Useless |
| File read early, never referenced again | Expired context | 1+ with no later ref | Expired |

These are deterministic, fast, and produce mechanically-cited signals.
They don't measure tokens — they measure **behaviors associated with
waste**.

## Related

- [[plan-skill-completeness]] — plan quality affects token efficiency (better plans = fewer correction loops)
- [[git-mv-search-replace-capture-bug]] — specific instance of wasted effort (re-editing after capture bug)

## Auto-related

<!-- Auto-generated by wiki_after_write.py - do not edit manually -->