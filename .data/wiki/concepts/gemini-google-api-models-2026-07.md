---
title: "Gemini / Google API models (catalog snapshot 2026-07)"
created: 2026-07-21
source: session-2026-07-21
tags: [gemini, google, models, api, fleet, picker, multimodal, grok-build]
summary: >
  As of 2026-07-21 the Gemini Developer API is Gemini 3.x-first (stable Flash
  3.6/3.5/3.1-lite, Pro 3.1 preview, image/audio/video specialists). Gemini 2.5
  remains usable; 2.0 is documented as shut down. Grok OpenAI-compat works against
  generativelanguage.googleapis.com/v1beta/openai. Free-tier Pro quotas often hit zero.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
source_url: https://ai.google.dev/gemini-api/docs/models
relations:
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: related
  - target: wiki/concepts/llm-council-and-model-fusion
    type: related
---

# Gemini / Google API models (catalog snapshot 2026-07)

## Why this page exists

A 2026-07-21 fleet edit added only `gemini-2.5-flash`, `2.5-flash-lite`, `2.5-pro`,
and `gemini-3-flash-preview`. Official docs and a live `ListModels` call the same
day show a much larger **Gemini 3** catalog already stable or preview. This page is
the durable correction so the next session does not re-anchor on 2.5-only.

**Live inventory artifact:** `P:/.data/www-ledger/gemini-api-models-live-2026-07-21.json`
(50 models returned by `GET …/v1beta/models` with this host's key).

## Authority sources

| Source | Role | Score (CREDIBLE-lite) |
|--------|------|------------------------|
| [Models catalog](https://ai.google.dev/gemini-api/docs/models) | Official list; last-updated stamp 2026-07-21 | 12 |
| [Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3) | Series IDs, thinking_level, pricing table | 12 |
| Live ListModels + OpenAI-compat chat probes on this host | What the key can actually call | 11 |

## Gemini 3 series (current)

Per official Models page (stable vs preview):

### Stable text / agentic

| Model ID | Positioning | Notes for this fleet |
|----------|-------------|----------------------|
| **`gemini-3.6-flash`** | Latest balance of speed + intelligence, agentic + multimodal | Preferred Flash default if quota allows |
| **`gemini-3.5-flash`** | Sustained frontier on agentic/coding | Strong code/agent lane |
| **`gemini-3.5-flash-lite`** | Fastest 3.5, high-throughput | Mechanical / high volume |
| **`gemini-3.1-flash-lite`** | Cost workhorse; frontier-class at low price | Good free-tier candidate |

### Preview text

| Model ID | Positioning |
|----------|-------------|
| **`gemini-3.1-pro-preview`** | Advanced reasoning, agentic + vibe coding |
| **`gemini-3-flash-preview`** | Flash-class preview (still listed; superseded in practice by 3.5/3.6 stable) |

### Aliases

| ID | Meaning |
|----|---------|
| `gemini-flash-latest` | Hot-swapped latest Flash variation (2-week notice on breaking swaps) |
| `gemini-pro-latest` | Latest Pro variation |
| `gemini-flash-lite-latest` | Latest Flash-Lite |

Prefer **stable pin** (`gemini-3.6-flash`) for production skill recipes; use `*-latest` only when intentional drift is acceptable.

### Image (Nano Banana family)

| ID / brand | Role |
|------------|------|
| `gemini-3.1-flash-image` (**Nano Banana 2**) | High-efficiency image gen/edit |
| `gemini-3.1-flash-lite-image` (**Nano Banana 2 Lite**) | Ultra-low latency image |
| `gemini-3-pro-image` / `…-preview` (**Nano Banana Pro**) | Studio-quality, complex layout, 4K-class |
| `gemini-2.5-flash-image` (**Nano Banana**) | Prior-gen native image |

### Video / music / live

| ID | Role |
|----|------|
| `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview` | Cinematic video (+ audio sync on full) |
| `gemini-omni-flash-preview` | Conversational video gen/edit |
| `lyria-3-pro-preview`, `lyria-3-clip-preview` | Music generation |
| `gemini-3.1-flash-live-preview` | Live A2A dialogue |
| `gemini-3.5-live-translate-preview` | Real-time speech translation (70+ langs) |
| `gemini-3.1-flash-tts-preview`, `gemini-2.5-*-tts` | TTS |

### Tool / agent specialists

| ID | Role |
|----|------|
| `gemini-2.5-computer-use-preview-10-2025` | Screen + UI actions |
| `deep-research-preview-04-2026`, `deep-research-max-preview-04-2026`, `deep-research-pro-preview-12-2025` | Multi-step research agents |
| `antigravity-preview-05-2026` | Managed agent in isolated Linux sandbox |

### Embeddings / robotics / open weights

| ID | Role |
|----|------|
| `gemini-embedding-2`, `gemini-embedding-2-preview`, `gemini-embedding-001` | Embeddings (2 is multimodal) |
| `gemini-robotics-er-1.5-preview`, `…-1.6-preview` | Embodied reasoning |
| `gemma-4-26b-a4b-it`, `gemma-4-31b-it` | Open Gemma 4 instruct (API-hosted) |

## Gemini 2.5 (still listed)

| ID | Role |
|----|------|
| `gemini-2.5-flash` | Price/performance reasoning workhorse |
| `gemini-2.5-flash-lite` | Cheapest 2.5 multimodal |
| `gemini-2.5-pro` | Deep reasoning / coding |
| TTS / Live / image variants | See audio/media sections above |

## Previous / shutdown (do not prefer)

Official "Previous models" section marks **shut down** (or equivalent):

- `gemini-2.0-flash`, `gemini-2.0-flash-lite`
- `gemini-3.1-flash-lite-preview` (preview string; stable is without `-preview`)
- `gemini-3-pro-preview` (superseded by `gemini-3.1-pro-preview`)

Live ListModels may still *list* 2.0 IDs; treat docs + deprecations page as policy, not the raw list alone.

## OpenAI compatibility (Grok picker)

Base URL for Chat Completions-style clients:

```text
https://generativelanguage.googleapis.com/v1beta/openai
```

Auth: `Authorization: Bearer $GEMINI_API_KEY` (same key as Generative Language API).

**This host probes (2026-07-21, OpenAI-compat chat):**

| ID | Result |
|----|--------|
| `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-flash-latest` | HTTP OK (sometimes empty content under free-tier pressure) |
| `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-2.5-flash` | OK with content |
| `gemini-3.1-pro-preview`, `gemini-pro-latest`, `gemini-2.5-pro` | **Quota exceeded** free-tier (limit 0 on generate_content for Pro-class) |
| `gemma-4-31b-it` | OK (reasoning trace-style output) |

Implication: put **Flash / Flash-Lite** in the default picker path; treat **Pro** as escalate-when-billed-or-quota-available.

## Gemini 3 API behavior notes (developer guide)

- Prefer **Interactions API** for latest features; OpenAI-compat still works for Grok `chat_completions`.
- `thinking_level`: `minimal` | `low` | `medium` | `high` (default high/dynamic on Pro/Flash).
- Keep **temperature at default 1.0** for Gemini 3; lowering can degrade reasoning.
- Thought signatures required for multi-turn reasoning continuity in some modes.
- Context tables on Gemini 3 guide: often **1M in / 64k out** for Flash/Pro class text models.

## Recommended Grok picker subset (quality–latency floor)

For `~/.grok/config.toml` (not every ListModels ID):

1. **`gemini-3.6-flash`** — current default Google text/agent  
2. **`gemini-3.5-flash-lite`** or **`gemini-3.1-flash-lite`** — mechanical / cheap  
3. **`gemini-2.5-flash`** — proven free-tier fallback  
4. **`gemini-3.1-pro-preview`** — reasoning when Pro quota exists  
5. Optional: **`gemini-flash-latest`** (alias), **`gemma-4-31b-it`** (open-family diversity), image IDs only if image workflows need native Gemini

Do **not** use 2.0 IDs as primaries.

## Relationship to existing concepts

- [[model-picker-as-failover-not-router]] — skills recommend; picker fails over; Gemini is another family for diversity.
- [[llm-council-and-model-fusion]] — OpenRouter Fusion panels often include Gemini 3 Flash as a **budget panel member**, not as sole frontier.
- [[multi-agent-correlated-errors]] — cross-family (Gemini vs GLM vs local) is the strong diversity lever.

## Sources

- https://ai.google.dev/gemini-api/docs/models (scraped 2026-07-21)
- https://ai.google.dev/gemini-api/docs/gemini-3 (scraped 2026-07-21)
- Live: `GET https://generativelanguage.googleapis.com/v1beta/models` → `P:/.data/www-ledger/gemini-api-models-live-2026-07-21.json`
- OpenAI-compat probes: same day, `…/v1beta/openai/chat/completions`

## Staleness

Re-list models if this page is **>30 days** old (Google ships stable/preview churn fast). Prefer re-running ListModels over trusting chat memory.

## Auto-related

- [[solo_operator_adr_best_practices]]

