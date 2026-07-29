---
title: "OpenCode Go and Zen: quota, pricing, and model catalog"
created: 2026-07-29
source: session-2026-07-29 (verified via opencode.ai/docs/go + opencode.ai/docs/zen)
tags: [opencode, go, zen, pricing, quota, models, subscription, pay-as-you-go, stealth]
summary: >
  OpenCode has two tiers: Go ($10/month subscription, dollar-based usage caps
  of $12/5hr, $30/week, $60/month) and Zen (pay-as-you-go per 1M tokens).
  Zen has 7 free models (limited time) including stealth model "big-pickle."
  Go has 16 subscription models. Full quota tables per model documented.
agent: grok
host: grok
cognitive_load: 2
verification: directly-verified
sources:
  - https://opencode.ai/docs/go (OpenCode, 2026-07-29)
  - https://opencode.ai/docs/zen (OpenCode, 2026-07-29)
relations:
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: related
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: complements
---

# OpenCode Go and Zen: quota, pricing, and model catalog

## OpenCode Go ($10/month subscription)

**Price:** $5 first month, then $10/month.

**Limits are dollar-based, not request-based.** The $10 subscription gives
you $60/month of actual model usage (6x multiplier).

| Window | Usage cap |
|---|---|
| 5-hour rolling | **$12** |
| Weekly | **$30** |
| Monthly | **$60** |

When you hit the cap, you can either wait for the window to reset or
fall back to Zen balance (if "Use balance" is enabled).

### Go model request estimates (per 5hr / week / month)

These are derived from typical token-per-request patterns. Actual counts
vary with prompt size and cache hit rate.

| Model | req/5hr | req/week | req/month |
|---|---|---|---|
| Grok 4.5 | 120 | 300 | 600 |
| GLM-5.2 | 880 | 2,150 | 4,300 |
| GLM-5.1 | 880 | 2,150 | 4,300 |
| Kimi K3 (2x promo) | 220 | 500 | 980 |
| Kimi K2.7 Code | 1,350 | 3,380 | 6,750 |
| Kimi K2.6 | 1,150 | 2,880 | 5,750 |
| MiMo-V2.5 | 30,100 | 75,200 | 150,400 |
| MiMo-V2.5-Pro | 3,250 | 8,150 | 16,300 |
| MiniMax M3 | 3,200 | 8,000 | 16,000 |
| MiniMax M2.7 | 3,400 | 8,500 | 17,000 |
| Qwen3.7 Max | 950 | 2,390 | 4,770 |
| Qwen3.7 Plus | 4,300 | 10,800 | 21,600 |
| Qwen3.6 Plus | 3,300 | 8,200 | 16,300 |
| DeepSeek V4 Pro | 3,450 | 8,550 | 17,150 |
| DeepSeek V4 Flash | 31,650 | 79,050 | 158,150 |
| Hy3 | 4,300 | 10,750 | 21,500 |

### Endpoints
- OpenAI-compatible: `https://opencode.ai/zen/go/v1/chat/completions`
- Anthropic-compatible: `https://opencode.ai/zen/go/v1/messages`

---

## OpenCode Zen (pay-as-you-go)

Zen is **NOT free** — it's pay-as-you-go, priced per 1M tokens. Auto-reload
triggers when balance < $5, default top-up $20 (configurable). 4.4% + $0.30
credit card processing fee.

### Free models on Zen (7 models, limited time)

These are $0 for input, output, and cached read:

| Model | Notes |
|---|---|
| **big-pickle** | Stealth model — identity undisclosed. Free for limited time. |
| **deepseek-v4-flash-free** | DeepSeek V4 Flash. Free for limited time. |
| **mimo-v2.5-free** | MiMo V2.5. Free for limited time. |
| **laguna-s-2.1-free** | Poolside Laguna S 2.1. Free for limited time. |
| **ling-3.0-flash-free** | InclusionAI Ling 3.0 Flash. Free for limited time. |
| **north-mini-code-free** | Cohere North Mini Code. Data may be retained. |
| **nemotron-3-ultra-free** | NVIDIA Nemotron 3 Ultra. Trial use only; data logged. |

**Stealth models** are models where OpenCode doesn't disclose the underlying
model identity. "big-pickle" is the only current stealth model — it performs
well on code-exec (passes benchmark) but its actual model family is unknown.

**Privacy caveat:** free models may use your data for training during the
free period. Don't send sensitive data to free-tier Zen models.

### Zen rate limits

Not publicly documented. Only spend-based controls exposed (auto-reload
threshold, optional monthly caps). No RPM/TPM numbers published.

### Sample Zen paid pricing (per 1M tokens)

| Model | Input | Output | Cached Read |
|---|---|---|---|
| GPT 5 Nano | $0.05 | $0.40 | $0.005 |
| DeepSeek V4 Flash | $0.14 | $0.28 | $0.028 |
| Qwen3.5 Plus | $0.20 | $1.20 | $0.02 |
| MiniMax M3 | $0.30 | $1.20 | $0.06 |
| GLM 5.2 | $1.40 | $4.40 | $0.26 |
| Claude Opus 5 | $5.00 | $25.00 | $0.50 |
| GPT 5.5 Pro | $30.00 | $180.00 | $30.00 |

---

## Fleet config mapping

In our config.toml, Zen and Go models are configured at
`~/.grok/config.toml` with base_url `https://opencode.ai/zen/v1`. The
[[model-fleet-provider-pools]] concept documents the fleet inventory,
and the [[coding-model-pool-tier-1-tier-2]] concept references Zen
models as tier-2 fallback candidates. See also
[[model-pool-selection-policy-speed-quota-diversity]] for the general
selection policy this pricing data feeds into.

## Falsifier

This data is wrong if OpenCode changes their pricing, quota structure, or
model catalog. Re-verify by fetching opencode.ai/docs/go and
opencode.ai/docs/zen. The free model list may shrink as the "limited time"
promotions expire.
