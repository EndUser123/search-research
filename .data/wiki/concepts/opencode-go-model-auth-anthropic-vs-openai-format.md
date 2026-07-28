---
title: "OpenCode Go models: dual auth format — Anthropic Messages vs OpenAI Chat Completions"
created: 2026-07-28
source: session-2026-07-28
tags: [models, auth, opencode-go, anthropic, config, grok-build, spawn_subagent]
summary: >
  OpenCode Go serves models through two different API formats: OpenAI
  Chat Completions (`/chat/completions`) and Anthropic Messages
  (`/messages`). Grok Build's `api_backend = "messages"` does NOT send
  the `api_key` field as auth — it requires `x-api-key` via
  `extra_headers`. Models affected: Qwen3.7 Max/Plus, Qwen3.6 Plus,
  MiniMax M3/M2.7. Config fix documented with receipts.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - https://opencode.ai/docs/go/ (OpenCode, 2026-07-28)
  - https://docs.x.ai/build/overview (xAI, 2026-07-06)
relations:
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: extends
  - target: wiki/concepts/model-tool-calling-capability-matrix.md
    type: complements
  - target: wiki/concepts/spawn-subagent-slug-session-snapshot.md
    type: related
---

# OpenCode Go models: dual auth format

## Decision context

**Why this research was needed:** Session 2026-07-28 attempted to use
`go-qwen3-7-max` via `spawn_subagent` for a `/review` specialist. Every
spawn returned `401 Unauthorized: AuthError: Missing API key`. The key was
valid (confirmed via direct HTTP and CLI), but Grok Build's spawn path was
sending the wrong auth header. Seven attempts failed before the root cause
was found in the OpenCode Go documentation.

**The problem:** Grok Build's `api_backend = "messages"` (Anthropic format)
does not send the `api_key` config field as an authentication header. It
expects `x-api-key` to be provided explicitly via `extra_headers`. Without
this, the OpenCode Go `/messages` endpoint rejects all requests with 401.

This relates to [[spawn-subagent-slug-session-snapshot]] — Grok Build caches
model config at startup, so config changes need a restart. It also affects
which models are available for the [[model-pool-selection-policy-speed-quota-diversity]]
routing policy, since broken models were excluded from pools.

## The dual-format split

OpenCode Go serves models through **two distinct API formats**, documented at
[opencode.ai/docs/go](https://opencode.ai/docs/go/) in the "Endpoints" table:

| Models | Endpoint | SDK package | Auth header |
|--------|----------|-------------|-------------|
| Grok 4.5, GLM-5.2/5.1, Kimi K3/K2.7/K2.6, DeepSeek V4 Pro/Flash, MiMo-V2.5/Pro, Hy3 | `/chat/completions` | `@ai-sdk/openai-compatible` | `Authorization: Bearer <key>` |
| **MiniMax M3/M2.7/M2.5, Qwen3.7 Max/Plus, Qwen3.6 Plus** | **`/messages`** | **`@ai-sdk/anthropic`** | **`x-api-key: <key>`** |

The split is not arbitrary — it reflects how each model was trained/served.
Models that natively use Anthropic's message format go through `/messages`;
everything else uses OpenAI's chat completions format.

## The Grok Build config fix

Grok Build's `11-custom-models.md` user guide (lines 200-210) documents the
rule explicitly:

> The `messages` backend uses the Anthropic Messages protocol. Anthropic
> authenticates with an `x-api-key` header rather than `Authorization: Bearer`,
> so pass your key through `extra_headers`, which Grok sends verbatim.

The correct config for Anthropic-format OpenCode Go models:

```toml
[model.go-qwen3-7-max]
model = "qwen3.7-max"
api_key = "sk-ZGBJ20..."
base_url = "https://opencode.ai/zen/go/v1"
api_backend = "messages"
context_window = 200000

[model.go-qwen3-7-max.extra_headers]
anthropic-version = "2023-06-01"
x-api-key = "sk-ZGBJ20..."
```

**Key points:**
- `api_backend = "messages"` is correct for Qwen/MiniMax models (NOT `chat_completions`)
- The `api_key` field alone is NOT sufficient — Grok Build's messages backend doesn't send it as `x-api-key`
- `x-api-key` must be duplicated in `extra_headers` (the `api_key` field is still needed for Grok's internal credential resolution)
- `anthropic-version = "2023-06-01"` is required by the Messages API

## Verification (post-restart, 2026-07-28)

All three Qwen models verified working via `spawn_subagent` after config
fix + Grok Build restart:

| Model | Latency | Quota (5h / month) |
|-------|---------|---------------------|
| `go-qwen3-7-max` | 5.9s | 950 / 4,770 |
| `go-qwen3-7-plus` | 5.1s | 4,300 / 21,600 |
| `go-qwen3-6-plus` | 3.9s | 3,300 / 16,300 |

Pre-restart, the same config produced 401 on every spawn. Grok Build caches
model config at session startup — config.toml changes require a restart.

## What this means for our workspace

1. **Qwen and MiniMax M3 models are now pool-eligible via spawn_subagent.**
   Previously documented as broken (tool-fallbacks.md, 2026-07-21). The
   failure was a config issue, not a platform limitation. This expands the
   [[model-pool-selection-policy-speed-quota-diversity]] pool with three
   new high-quota models.

2. **The `go-mimo-v2-5` and `go-deepseek-v4-flash` models already worked**
   because they use `chat_completions` backend, which sends `api_key` as
   `Authorization: Bearer` correctly. No config change needed for those.
   See [[model-tool-calling-capability-matrix]] for which models support
   tool use.

3. **When adding new OpenCode Go models, check the endpoints table first.**
   If the model uses `/messages` (Anthropic format), add `x-api-key` to
   `extra_headers`. If it uses `/chat/completions` (OpenAI format), the
   default `api_key` field works. This is the same credential resolution
   pattern documented in [[model-fleet-provider-pools]].

4. **MiniMax M3 via OpenCode Go (`go-minimax-m3`) would need the same fix**
   if added — it uses `/messages` per the endpoints table. The current
   `minimax-m3` config works because it uses a different provider (MiniMax
   direct, not OpenCode Go). See [[model-lanes-vs-roles]] for the routing
   framework.

## How to debug model auth failures in Grok Build

1. **Check the error for `Auth: Oidc` or `Missing API key`.** This means
   Grok Build's auth layer didn't send credentials the endpoint accepts.

2. **Determine the API format.** Check the provider's docs for whether the
   model uses OpenAI Chat Completions (`Authorization: Bearer`) or Anthropic
   Messages (`x-api-key`) format.

3. **Test the key via direct HTTP.** Use `Invoke-RestMethod` with the
   appropriate header to confirm the key works:
   - OpenAI format: `Authorization: Bearer <key>` to `/chat/completions`
   - Anthropic format: `x-api-key: <key>` to `/messages`

4. **Update config.toml with the right `api_backend` and `extra_headers`.**
   The `api_key` field alone is insufficient for Anthropic-format models.

5. **Restart Grok Build.** Config changes don't apply mid-session.

## Falsifier

This entry would be wrong if Grok Build updates to automatically send
`x-api-key` for the `messages` backend (making the `extra_headers` entry
unnecessary). Check the Grok Build changelog — if a future version adds
automatic `x-api-key` injection for messages-backend models, this config
entry becomes redundant but not harmful.

## Sources

- [OpenCode Go docs](https://opencode.ai/docs/go/) (OpenCode, 2026-07-28) — endpoints table showing which models use `/messages` vs `/chat/completions`
- [Grok Build overview](https://docs.x.ai/build/overview) (xAI, 2026-07-06) — custom model config.toml format
- Grok Build user guide `~/.grok/docs/user-guide/11-custom-models.md` lines 200-210 — messages backend auth rule

## Receipts

- `~/.grok/config.toml` lines 281-320 — the three Qwen model configs with `x-api-key` header
- `~/.grok/tool-fallbacks.md` — updated from "broken" to "resolved" with verification data
- Session 019f9f4f spawn tests: `go-qwen3-7-max` (5.9s), `go-qwen3-7-plus` (5.1s), `go-qwen3-6-plus` (3.9s)
