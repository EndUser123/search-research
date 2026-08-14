---
title: "I want to use my minimax token plan with bifrost and use the minimax model M2.7.   When I do model discovery I'm not see"
date: "2026-04-28"
mode: "CONCISE"
uuid: "30817541-d3ee-4da9-a7b0-75348c81101e"
entry_count: 6
---

## Human

I want to use my minimax token plan with bifrost and use the minimax model M2.7.   When I do model discovery I'm not seeing M2.7, I only see up to M2.5

## Assistant

MiniMax M2.7 exists as a recently released model (March-April 2026) available via MiniMax's official API and token plans, with strong agentic/coding performance, but Bifrost's model discovery likely omits it due to lacking integration or a version lag.[1][2][3]

## Model Status
M2.7 is live on MiniMax's platform for token plan users, supporting high-speed variants and complex tasks like software engineering (SWE-Pro 56.22%). Bifrost supports MiniMax (e.g., up to M2.5 or M2.1 via direct/custom configs), but docs/catalogs show no M2.7 listing as of latest checks (April 2026).[4][5][3][6][1]

## Discovery Issue
Bifrost fetches models dynamically from providers; if M2.7 isn't propagated (new release, config mismatch, or Bifrost version < latest), it won't appear—common for fresh models. Exact name may be "minimax-m2.7" or "MiniMax-M2.7"; Bifrost uses provider-specific prefixes like "minimax/" or OpenAI-compatible.[3][7][6]

## Next Steps
- Update Bifrost to newest version/release (check GitHub for Minimax patches).[8]
- Manually add as custom provider: Type "OpenAI", base URL `https://api.minimax.chat` (or your token plan endpoint), API key from MiniMax dashboard; force-refresh discovery.[7]
- Test direct API call to MiniMax (`model: "minimax-m2.7"`) outside Bifrost to confirm token plan access, then alias in Bifrost config (e.g., `minimax/minimax-m2.7`).[1][3]
- If stuck, query Bifrost Discord/GitHub issues for "minimax m2.7" or open one with your version/logs.[8]

Uncertainty: Bifrost support unconfirmed (no explicit doc hit); assume lag since M2.7 is <1mo old. Primary source: MiniMax docs > Bifrost secondary.[3][1]

## Human

look up what the token plan endpoint should be.

## Assistant

The Token Plan endpoint for MiniMax depends on whether you're using OpenAI-compatible or Anthropic-compatible protocol:[1]

## Token Plan API Endpoints

**OpenAI-Compatible Protocol**
- Base URL: `https://api.minimax.io/v1`
- API Key: Your Token Plan API Key (from Account/Token Plan page)
- Model ID: `MiniMax-M2.7` or `MiniMax-M2.7-highspeed`

**Anthropic-Compatible Protocol**
- Base URL: `https://api.minimax.io/anthropic`
- API Key: Your Token Plan API Key
- Model ID: `MiniMax-M2.7` or `MiniMax-M2.7-highspeed`

**MCP/General Use**
- API Host: `https://api.minimax.io`

[2][1]

## Key Differences from Pay-As-You-Go

Token Plan uses a **dedicated API key** separate from your standard MiniMax Open Platform key. The Token Plan key is exclusively for subscription plans (request-count billing), while the standard key uses pay-as-you-go token pricing ($0.30/M input, $1.20/M output for M2.7).[3][4][5]

## For Bifrost Setup

Use the **OpenAI-compatible** endpoint when configuring Bifrost:
- Provider type: `OpenAI` or `Custom OpenAI-compatible`
- Base URL: `https://api.minimax.io/v1`
- Model name: `MiniMax-M2.7` (case-sensitive)
- API Key: Token Plan key from platform.minimax.io → Account/Token Plan

[6][1]

The `/v1` suffix is critical for OpenAI-format requests; omitting it will cause 404/endpoint errors.[1]

## Human

Are you sure about the end point?

## Assistant

Yes, I'm certain—the official MiniMax Token Plan documentation confirms the endpoints:[1]

## OpenAI-Compatible Protocol
- **Base URL**: `https://api.minimax.io/v1`
- **API Key**: Token Plan API Key (from [Account/Token Plan page](https://platform.minimax.io/user-center/payment/token-plan))
- **Model ID**: `MiniMax-M2.7` or `MiniMax-M2.7-highspeed`

## Anthropic-Compatible Protocol
- **Base URL**: `https://api.minimax.io/anthropic`
- **API Key**: Token Plan API Key
- **Model ID**: `MiniMax-M2.7` or `MiniMax-M2.7-highspeed`

[1]

## For Bifrost

Since Bifrost typically expects OpenAI-compatible providers, use:
- Provider: `OpenAI Compatible` or `Custom`
- Base URL: **`https://api.minimax.io/v1`**
- Model: `MiniMax-M2.7`

[1]

The `/v1` suffix is required for OpenAI-format requests; the `/anthropic` endpoint is only for Claude-style tools (e.g., Claude Code, Cline). Both protocols access the same Token Plan quota (rolling 5-hour request limits, not token-based).[2][1]

## Human

for z.ai on the coding plan, what endpoint should I use?

## Assistant

For Z.AI on the **Coding Plan**, use the dedicated Coding API endpoint:[1][2]

## Coding Plan Endpoint
**Base URL**: `https://api.z.ai/api/coding/paas/v4`

This endpoint is **subscription-based** with prompt-based pricing, separate from the standard pay-as-you-go endpoint (`https://api.z.ai/api/paas/v4`).[3][1]

## For Bifrost Setup
- Provider type: `OpenAI Compatible` or `Custom`
- Base URL: `https://api.z.ai/api/coding/paas/v4`
- API Key: Your Z.AI API Key (from [api.z.ai](https://api.z.ai) → API Keys page)
- Model: `glm-5.1`, `glm-5`, `glm-5-turbo`, `glm-4.7`, or `glm-4.5-air`

[2][4]

## Important Restrictions
The Coding Plan endpoint is **intended for supported tools only** (Claude Code, Cline, OpenCode, Cursor, etc.) and may have usage monitoring to prevent direct curl/API abuse. Z.AI updated policies in April 2026 to block accounts that bypass tool integration. For Bifrost use, ensure your setup mimics standard OpenAI-compatible client behavior (proper headers, user-agent) to avoid detection.[5][6]

## Alternative for General Use
If Bifrost doesn't qualify as a "supported tool" or you encounter blocks, fall back to the **general API endpoint** (`https://api.z.ai/api/paas/v4`) with pay-as-you-go token pricing instead.[1][5]

## Human

Is there any info on using Bifrost with z.ai coding plan?

## Assistant

Yes, there's confirmed usage of Z.AI Coding Plan with Bifrost. Users successfully configured it as a **custom provider** using the **Anthropic-compatible endpoint**.[1]

## Confirmed Working Configuration

**Provider Setup in Bifrost**:
- Provider type: `Anthropic` or `Custom Anthropic-compatible`
- Base URL: `https://api.z.ai/api/anthropic`
- API Key: Your Z.AI API Key
- Model: `glm-5.1`, `glm-5`, `glm-4.7`, etc.

[1]

## Endpoint Discussion

GitHub issue #1546 clarified two valid endpoints for Z.AI Coding Plan:[1]

1. **Anthropic-compatible** (`https://api.z.ai/api/anthropic`) — Confirmed working in Bifrost, officially documented for Claude Code/Cline tools[1]
2. **OpenAI-compatible** (`https://api.z.ai/api/coding/paas/v4`) — Also valid but discussion focused on Anthropic endpoint[1]

## Why Anthropic Endpoint Works

Z.AI's official docs recommend the Anthropic endpoint for coding tools (Claude Code, Cline, etc.). Since Bifrost supports custom Anthropic-compatible providers, this maps cleanly without additional configuration. The issue was marked as "solved" in March 2026 after users confirmed Anthropic endpoint functionality.[1]

## Recommendation

Use **`https://api.z.ai/api/anthropic`** as your base URL in Bifrost's custom provider configuration with Anthropic compatibility mode. This aligns with Z.AI's documented approach for coding plan integrations and has been validated by the community.[1]

## Human

but the models are not discovered.

## Assistant

Model discovery failing for custom providers (Z.AI, MiniMax) is a known limitation—Bifrost can't auto-fetch models from non-standard endpoints. You must **manually specify models** in the provider configuration.[1][2][3]

## Solution: Manual Model Configuration

When adding Z.AI or MiniMax as custom providers, explicitly declare models in the `allowed_models` field instead of relying on discovery:[3]

### For Z.AI Coding Plan
**Provider Config**:
- Type: `Anthropic` or `OpenAI Compatible`
- Base URL: `https://api.z.ai/api/anthropic` (Anthropic) or `https://api.z.ai/api/coding/paas/v4` (OpenAI)
- API Key: Your Z.AI key
- **Allowed Models**: Manually list models:
  ```
  ["glm-5.1", "glm-5", "glm-5-turbo", "glm-4.7", "glm-4.5-air"]
  ```

[4][3]

### For MiniMax Token Plan
**Provider Config**:
- Type: `OpenAI Compatible`
- Base URL: `https://api.minimax.io/v1`
- API Key: Token Plan key
- **Allowed Models**: 
  ```
  ["MiniMax-M2.7", "MiniMax-M2.7-highspeed", "MiniMax-M2.5", "MiniMax-M2.5-turbo"]
  ```

[3]

## Why Discovery Fails

Bifrost's model catalog auto-syncs via `/v1/models` endpoints for standard providers, but custom endpoints (especially proprietary auth schemes) don't expose model lists in OpenAI-compatible format. The warning `"failed to list models for provider"` is expected—Bifrost falls back to your explicit `allowed_models` list.[2][1][3]

## Configuration Methods

1. **Web UI**: Providers → Custom Provider → "Allowed Models" field → Add models manually[3]
2. **config.json**: Edit provider config with `"allowed_models": ["model-name"]`[3]
3. **API**: POST to provider config endpoint with `allowed_models` array[3]

Setting `allowed_models: ["*"]` won't work for custom providers since the catalog has no baseline; you must enumerate models explicitly.[3]
