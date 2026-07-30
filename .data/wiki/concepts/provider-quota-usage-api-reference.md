---
title: "Provider quota and usage API reference"
created: 2026-07-30
source: session-2026-07-29/30 (provider quota API probing)
tags: [quota, usage, billing, providers, openrouter, glm, minimax, nvidia, opencode, api-reference]
summary: >
  Which API calls return quota/usage/balance information for each model
  provider in the fleet. Most providers don't expose API-based quota
  checking — you must use their web dashboard. OpenRouter is the exception
  with working API endpoints.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-tested
sources:
  - "Direct API probing 2026-07-30 (all endpoints tested live)"
relations:
  - target: wiki/concepts/opencode-go-zen-quota-and-pricing.md
    type: related
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: related
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: related
---

# Provider quota and usage API reference

## Decision context

The operator needs to know how to check quota/usage/balance for each model
provider to make routing decisions (when to conserve, when to spend freely).
This page documents which API calls work, which don't, and where to check
for providers without API-based quota checking.

## Summary table

| Provider | API quota check? | Working call | Web dashboard |
|----------|-----------------|-------------|---------------|
| **OpenRouter** | ✅ YES | `GET /api/v1/credits` + `GET /api/v1/key` | openrouter.ai/credits |
| **Z.ai (GLM)** | ❌ NO | No billing API found (4404 on all tested endpoints) | bigmodel.cn console |
| **MiniMax** | ❌ NO | 403 on account endpoints | platform.minimaxi.com |
| **Mistral** | ❌ NO | 404 on all tested endpoints | console.mistral.ai |
| **NVIDIA NIM** | ❌ NO | 404 on all tested endpoints | build.nvidia.com (no quota shown) |
| **OpenCode Zen/Go** | ❌ NO | 403 on all tested endpoints | opencode.ai/settings |
| **Google Gemini** | ❌ NO | 404 on usage endpoint | aistudio.google.com |
| **xAI/Grok** | ❌ NO (built-in) | Use `/quota` command in Grok TUI | grok.com |
| **Codex/OpenAI** | ❌ NO (subscription) | ChatGPT subscription, check Codex UI | chatgpt.com/codex |

## OpenRouter (the one that works)

OpenRouter is the only provider with a working API-based quota check.

### Check credits remaining

```bash
curl -s https://openrouter.ai/api/v1/credits \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq .
```

Response:
```json
{
  "data": {
    "total_credits": 65,
    "total_usage": 41.43
  }
}
```

### Check key usage (daily/weekly/monthly)

```bash
curl -s https://openrouter.ai/api/v1/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq .
```

Response includes: `usage`, `usage_daily`, `usage_weekly`, `usage_monthly`,
`is_free_tier`, rate limit info.

**Current status (2026-07-30):** $65 total credits, $41.43 used, $23.57
remaining. Monthly usage: $0.69. Plenty of headroom.

## Providers without API quota checking

For these providers, quota must be checked manually via web dashboards:

| Provider | Where to check | What you see |
|----------|---------------|-------------|
| **Z.ai (GLM)** | bigmodel.cn console | Token usage, subscription plan, remaining prompts |
| **MiniMax** | platform.minimaxi.com | API calls used, plan tier, remaining calls |
| **Mistral** | console.mistral.ai | Token usage, billing, rate limits |
| **NVIDIA NIM** | build.nvidia.com | No quota shown — free tier, rate-limited per model |
| **OpenCode Zen/Go** | opencode.ai/settings | Balance, auto-reload status, Go subscription status |
| **Google Gemini** | aistudio.google.com | Per-model daily quota usage |
| **xAI/Grok** | `/quota` in Grok TUI | Token plan usage, reset time |
| **Codex/OpenAI** | chatgpt.com/codex | Codex usage page, rate limit banner |

## What we know from config.toml (static)

From `opencode-go-zen-quota-and-pricing.md`:

| Provider | Quota model | Ceiling |
|----------|------------|---------|
| GLM Max-Yearly | 1,600 prompts/5h | ~288K/month |
| MiniMax Plus | 4,500 calls/5h | ~648K/month |
| OpenCode Go | $60/month shared | ~30K requests (DeepSeek V4 Flash) |
| OpenCode Zen free | $0, no published limit | Unknown — likely generous |
| NVIDIA | 40 RPM per model | ~2,400/hour per model |
| Groq | 6,000-8,000 TPM | Excluded (TPM blocks spawn) |
| Google Flash | ~20 RPD | Very limited |

## What this means for routing

- **GLM-5.2 quota (1,600/5h):** check the Z.ai dashboard if experiencing
  rate limits. No API check available.
- **OpenCode Go ($60/month):** check opencode.ai/settings for remaining
  balance. All Go models share this budget.
- **OpenRouter ($23.57 remaining):** API checkable. Run the curl command
  above to verify before heavy usage.
- **NVIDIA (free, 40 RPM):** effectively unlimited for our usage pattern
  (actual load is 7% of ceiling per `model-fleet-provider-pools.md`).
- **Zen free models:** no API check, no published limits. Assume generous
  but monitor for 429s.

## Falsifier

This reference is wrong if:
- A provider adds a billing/usage API endpoint (check their docs)
- OpenRouter changes their API format
- A provider removes their web dashboard quota display
