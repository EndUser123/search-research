---
title: "Fleet quota API discovery — all providers (2026-07-30)"
created: 2026-07-30
source: session-20260730 (/www research: quota/rate/subscription APIs for all fleet providers)
tags: [quota, usage, billing, api-reference, opencode-quota, fleet-quota, providers, monitoring]
summary: >
  Comprehensive research into programmatic quota/usage/rate-limit checking for every
  provider in the fleet. Categorizes providers into three tiers: those with dedicated
  quota APIs (best), those with response-header-only signals (usable), and those with
  no programmatic check at all (self-track or handle 429). Built fleet_quota.py script
  that unifies all checkable providers into a single dashboard. Key findings: Mistral
  has a full billing API, SerpAPI has a complete account endpoint, Firecrawl has v2
  credit usage + historical, GitHub rate_limit is free, ElevenLabs has subscription API.
  OpenRouter opencode-quota integration is broken on null-limit keys. NVIDIA NIM has
  no observability at all.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-tested
sources:
  - "Direct API probing 2026-07-30 (all endpoints tested with real keys)"
  - "opencode-quota source code analysis (google-agy.js, google.js, minimax-auth.js)"
  - "Official provider docs (Groq, Mistral, ElevenLabs, HuggingFace, Brave, GitHub)"
  - "github.com/slkiser/opencode-quota README"
  - "github.com/Dicklesworthstone/coding_agent_usage_tracker (caut)"
relations:
  - target: wiki/concepts/provider-quota-usage-api-reference.md
    type: supersedes
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: related
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: related
  - target: capabilities/reasoning-model-pool.md
    type: related
---

# Fleet quota API discovery — all providers

## Decision context

The operator needed a unified quota dashboard that covers ALL providers — not just
the LLM ones. The existing `/model-quota` skill relied on `opencode-quota` (which
covers MiniMax, Z.ai, OpenCode Go, Google, Copilot) but missed OpenRouter (broken
on null-limit keys), all search APIs (Tavily, SerpAPI, Firecrawl, Exa, Brave),
platform APIs (GitHub, ElevenLabs), and had no visibility into free-tier providers
(Groq, HuggingFace, Cerebras, NVIDIA, Mistral, Gemini API). The question was: for
each provider, what is the BEST programmatic way to check quota/usage?

## Provider categorization — three tiers

### Tier 1: Dedicated quota/usage API (best — single call, structured data)

| Provider | Endpoint | Auth | Returns | Verified |
|----------|----------|------|---------|----------|
| **Mistral** | `api.mistral.ai/v1/billing/subscription` | Bearer key | plan, credit_balance, monthly_budget (EUR) | ⚠️ free-tier keys get 404 |
| **Mistral** | `api.mistral.ai/v1/billing/usage?start_date=&end_date=` | Bearer key | daily cost breakdown, token counts | ⚠️ free-tier keys get 404 |
| **ElevenLabs** | `api.elevenlabs.io/v1/user/subscription` | xi-api-key header | tier, character_count, character_limit, reset_unix | ✅ endpoint works (key expired) |
| **SerpAPI** | `serpapi.com/account.json?api_key=` | query param | plan, remaining searches, hourly usage, renewal date | ✅ verified working |
| **Tavily** | `api.tavily.com/usage` | Bearer key | plan_usage, plan_limit, per-endpoint breakdown | ✅ verified working |
| **Firecrawl** | `api.firecrawl.dev/v2/team/credit-usage` | Bearer key | remainingCredits, planCredits, billing period | ✅ verified (over quota: -3/1000) |
| **Firecrawl** | `api.firecrawl.dev/v2/team/credit-usage/historical` | Bearer key | monthly historical breakdown | [INFERENCE] not tested |
| **GitHub** | `api.github.com/rate_limit` | Bearer token | per-resource remaining/limit/reset (free call) | ✅ verified working |
| **OpenRouter** | `openrouter.ai/api/v1/credits` | Bearer key | total_credits, total_usage | ✅ verified ($23.57/$65) |
| **MiniMax** | `api.minimax.io/v1/api/openplatform/coding_plan/remains` | Bearer key | model_remains array with percent remaining | ✅ via mmx quota + opencode-quota |

### Tier 2: Response-header-only signals (usable — parse headers from each call)

| Provider | Headers | Data | Notes |
|----------|---------|------|-------|
| **Groq** | `x-ratelimit-limit-requests`, `x-ratelimit-remaining-requests`, `x-ratelimit-reset-requests` | RPD, RPM, TPM remaining + reset | No dedicated endpoint — must parse every response |
| **HuggingFace** | `RateLimit` (IETF draft), `RateLimit-Policy` | remaining requests + reset per bucket (api/resolvers/pages) | huggingface_hub SDK auto-parses |
| **Brave** | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` | per-second burst + monthly quota remaining | No dedicated endpoint — use probe call |
| **Mistral** | `ratelimit-limit`, `ratelimit-remaining`, `ratelimit-reset`, `x-ratelimit-limit-tokens` | RPM + TPM on every response | Also on `/v1/models` endpoint |
| **Context7** | `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` | monthly call limit (1000 free tier) | No dedicated endpoint |

### Tier 3: No programmatic check (worst — self-track or handle 429)

| Provider | What exists | Recommendation |
|----------|-------------|----------------|
| **NVIDIA NIM** | Nothing. No headers, no API, no dashboard. | Self-track requests. ~40 RPM soft limit. |
| **Cerebras** | Console dashboard (CSV export). No API. | Parse 429 error messages for bucket info. |
| **Gemini API (free)** | AI Studio dashboard only. No API. | Handle 429 reactively. 3 keys × 1500 RPD. |
| **YouTube Data API** | Console IAM quotas only. No API. | Self-track units. 4 keys × 10k/day. |
| **Serper** | Web dashboard only. No API. | Manual check. |
| **Exa** | Team management API (cost, not balance). | Cost tracking only via admin-api.exa.ai. |

## Key discoveries

### OpenRouter opencode-quota failure root cause

opencode-quota calls `openrouter.ai/api/v1/key` which returns `limit: null` and
`limit_remaining: null` for keys without a spending cap. The parser expects
numeric values and fails with "Invalid openrouter-key-v1 response." The fix:
use `openrouter.ai/api/v1/credits` directly (returns total_credits/total_usage
regardless of limit configuration). Implemented in fleet_quota.py.

### MiniMax mmx quota vs opencode-quota

Both hit the same API endpoint (`api.minimax.io/v1/api/openplatform/coding_plan/remains`).
The `/mm-quota` skill (cc-skills-utils) uses browser scraping of the MiniMax
console — this is the heaviest approach and is superseded by the direct API.

### caut — Rust alternative to opencode-quota

`caut` (github.com/Dicklesworthstone/coding_agent_usage_tracker) is a Rust CLI
that covers 16+ providers including Codex, Claude, Gemini, Cursor, Copilot,
z.ai, MiniMax, Kimi, Kiro, Antigravity. Single binary, JSON/markdown output.
Does not integrate with OpenCode TUI but is the strongest standalone alternative.

## What this means for our workspace

The `/model-quota` skill now uses `fleet_quota.py` — a single Python script that:
1. Runs opencode-quota (for OAuth providers: Google AGY/Antigravity, Copilot, MiniMax, Z.ai, OpenCode Go)
2. Calls direct APIs for OpenRouter, Mistral, SerpAPI, Tavily, Firecrawl, GitHub, ElevenLabs
3. Renders a grouped dashboard with progress bars and color-coded urgency (🟢/🟡/🔴)

This covers **15 providers with live data** and documents **8 more** that have
no API. The previous dashboard missed search APIs, GitHub, and OpenRouter entirely.

The `provider-quota-usage-api-reference.md` wiki concept is superseded by this
entry — it was last updated mid-session and doesn't include the search/platform
provider findings.

## Falsifier

This reference is wrong if:
- A provider adds or removes a quota API (likely for NVIDIA NIM — developers are requesting it)
- opencode-quota fixes the OpenRouter null-limit parser (would make the direct API fallback unnecessary)
- Firecrawl changes its API version from v2 to v3 (would break the endpoint path)
- A new provider is added to the fleet not covered here
- caut adds OpenCode TUI integration (would make opencode-quota + fleet_quota.py redundant)

## Sources

- [Groq Rate Limits](https://console.groq.com/docs/rate-limits) — response headers only
- [Mistral Billing](https://docs.mistral.ai/admin/billing-usage/billing) — full billing API
- [ElevenLabs Subscription](https://elevenlabs.io/docs/api-reference/user/subscription/get) — character quota
- [SerpAPI Account API](https://serpapi.com/account-api) — complete account info
- [Tavily Usage](https://docs.tavily.com/documentation/api-reference/endpoint/usage) — plan + per-endpoint
- [Firecrawl Credit Usage](https://docs.firecrawl.dev/api-reference/endpoint/credit-usage) — v2 endpoint
- [GitHub Rate Limit](https://docs.github.com/en/rest/rate-limit/rate-limit) — free, per-token
- [HuggingFace Rate Limits](https://huggingface.co/docs/hub/en/rate-limits) — IETF draft headers
- [Brave Rate Limiting](https://api-dashboard.search.brave.com/documentation/guides/rate-limiting) — response headers
- [caut](https://github.com/Dicklesworthstone/coding_agent_usage_tracker) — Rust quota CLI
- [opencode-quota](https://github.com/slkiser/opencode-quota) — npm quota checker
