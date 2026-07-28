---
title: "Grok Build web_search is xAI server-side search — cannot be repointed at cheaper models"
created: 2026-07-28
source: session-2026-07-28
tags: [web-search, grok-build, xai-responses-api, supports-backend-search, model-config, quota, search-architecture]
summary: >
  Grok Build's built-in web_search tool is a server-side tool executed by
  xAI's Responses API during model inference. The `[models] web_search =
  "<model>"` config selects which model's endpoint runs the search, and
  `supports_backend_search = true` declares that the endpoint implements
  xAI's server-side search protocol. Pointing web_search at a non-xAI
  model (GLM, DeepSeek, etc.) does NOT work — the flag is a capability
  declaration, not an enabler. The built-in web_search must stay on Grok
  quota because it IS Grok's tool.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://docs.x.ai/developers/tools/web-search (xAI, 2026-07-28)
  - https://docs.x.ai/build/settings/reference (xAI, 2026-07-28)
  - https://docs.x.ai/developers/tools/advanced-usage (xAI, 2026-07-28)
  - https://openrouter.ai/docs/guides/features/plugins/web-search (OpenRouter, 2026-07-28)
  - https://developers.openai.com/api/docs/guides/tools-web-search (OpenAI, 2026-07-28)
  - https://docs.perplexity.ai/docs/sonar/quickstart (Perplexity, 2026-07-28)
relations:
  - target: wiki/concepts/web-search-tool-routing.md
    type: complements
  - target: wiki/concepts/optimal-multi-backend-search-strategy.md
    type: related
---

# Grok Build web_search is xAI server-side search

## Decision context

**Why this research was needed:** we disabled web-search-prime MCP (uses GLM
quota) and wanted to know if the built-in `web_search` tool could be
repointed at a cheaper/free model via `[models] web_search = "<model>"`.
If yes, built-in search would stop consuming Grok quota entirely.

**What the research changed:** the idea is abandoned. `web_search` is xAI's
server-side tool — it cannot run on non-xAI endpoints. The existing search
stack (DDG → firecrawl → mmx → built-in web_search as last resort) is
confirmed as the correct architecture.

## How web_search works (verified)

Grok Build's built-in `web_search` tool is implemented as a **server-side
tool** on xAI's Responses API:

1. The `web_search` tool fires
2. Grok Build sends `POST /v1/responses` to the configured model's endpoint
   with `tools: [{"type": "web_search"}]`
3. **xAI's server executes the search**, browses pages, and returns grounded
   citations during inference
4. The result comes back as model output with search-grounded content

Source: [xAI Web Search docs](https://docs.x.ai/developers/tools/web-search) —
"server-side tools are executed automatically by xAI" (verified 2026-07-28).

## The two config knobs

| Config | What it does | Source |
|--------|-------------|--------|
| `[models] web_search = "grok-4.5"` | Selects which model's endpoint runs the search | `05-configuration.md:31` |
| `[model.<id>] supports_backend_search = true` | Declares that the endpoint implements xAI's server-side search protocol | `11-custom-models.md:327` |

**`supports_backend_search` is a capability declaration, not an enabler.**
Setting it on a model whose endpoint lacks the feature does not make the
feature appear. A generic OpenAI-compatible endpoint (GLM, DeepSeek, Ollama)
does not implement the xAI server-side `web_search` tool — it would reject
the unknown tool type or ignore it, returning no grounded results.

## Cross-provider map (from OpenRouter docs)

Which providers offer native server-side search through their API:

| Provider | Native server-side search? | Notes |
|----------|---------------------------|-------|
| **xAI** | ✅ | `web_search` + `x_search` via Responses API |
| **OpenAI** | ✅ | `web_search` tool on Responses API; or `gpt-4o-search-preview` model |
| **Anthropic** | ✅ | Server-side web search tool on Claude API |
| **Google** | ✅ | Gemini grounding |
| **Perplexity** | ✅ | Sonar — search is intrinsic to the model |
| **GLM/Z.ai** | ❌ | Not native; uses function-calling for browsing |
| **DeepSeek** | ❌ | Not native |
| **Qwen** | ❌ | Not native |
| **MiniMax** | ❌ | Not native |

Source: [OpenRouter web search plugin docs](https://openrouter.ai/docs/guides/features/plugins/web-search) —
GLM/DeepSeek/Qwen fall back to Exa ($0.005/req) when routed through OpenRouter.

## Why our search stack is correct

| Tier | Tool | Cost | Why |
|------|------|------|-----|
| 1 | DDG (Python `ddgs`) | Free | No key, no quota, no rate limit |
| 2 | firecrawl MCP | Freemium (1000 credits/mo) | Separate pool |
| 3 | mmx search query (CLI) | Free (MiniMax plan) | Separate pool |
| 4 | web-search-prime MCP | GLM plan — **DISABLED** | Shared with glm-5-2 model |
| 5 | built-in web_search | Grok quota | xAI server-side tool — must be xAI model |

Built-in `web_search` must stay as last resort because it IS xAI's tool —
there's no way to make it free without an xAI free tier (which doesn't exist
for production search).

## Falsifier

If a future xAI API or Grok Build update allows `supports_backend_search =
true` to work on non-xAI endpoints (via proxying or protocol translation),
this finding becomes obsolete. Check the xAI API changelog.

Alternatively, if a third-party proxy implements the xAI Responses API
protocol (including `web_search` tool) and forwards to a cheaper backend,
pointing `web_search` at that proxy could work. No such proxy is known as
of 2026-07-28.

## Receipts

- `~/.grok/docs/user-guide/05-configuration.md:31` — `web_search = "grok-4.5" # model used by the web_search tool`
- `~/.grok/docs/user-guide/11-custom-models.md:314-335` — "The web_search tool uses a separate model" + `supports_backend_search` flag docs
- `https://docs.x.ai/developers/tools/web-search` — server-side tool execution by xAI
- `https://docs.x.ai/build/settings/reference` — `supports_backend_search` field description: "Whether the endpoint supports Grok-hosted server-side search tools"
