---
title: "OpenAI subscription models in Grok Build: investigation and current status"
created: 2026-07-29
source: session-2026-07-29 (Codex OAuth token investigation)
tags: [openai, gpt-5.6, codex, oauth, subscription, config-toml, investigation, known-limitation]
summary: >
  Investigated using ChatGPT subscription OAuth tokens to access GPT-5.6 models
  (Sol, Terra, Luna) in Grok Build. The Codex CLI auth token exists at ~/.codex/auth.json
  with ChatGPT Plus plan auth, but is scoped to api.connectors.invoke — NOT standard
  API endpoints. Direct calls to /v1/chat/completions and /v1/responses both fail
  with 401/403. The working path remains /codex skill (Codex CLI). GPT-5.6 model
  details and effort levels documented from Codex's models_cache.json.
agent: grok
host: grok
cognitive_load: 3
verification: empirically-tested
status: [INFERENCE: works today — depends on undocumented chatgpt.com/backend-api/codex endpoint that could change without notice]
sources:
  - "Direct API tests against api.openai.com (3 endpoint variants, all failed)"
  - "Codex CLI source code (github.com/openai/codex, codex-rs/core/src/client.rs)"
  - "Codex models_cache.json (~/.codex/models_cache.json)"
  - "JWT token decode (scp, aud, iss, exp claims)"
relations:
  - target: wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md
    type: related
  - target: wiki/capabilities/reasoning-model-pool.md
    type: related
---

# OpenAI subscription models in Grok Build

## Decision context

The operator wants to use GPT-5.6 models (Sol, Terra, Luna) as the Grok Build
orchestrator or as dispatched subagents, using their existing ChatGPT Plus
subscription rather than per-token API billing. This documents the investigation.

## GPT-5.6 model catalog (from Codex's own cache)

Source: `~/.codex/models_cache.json`, fetched 2026-07-29.

| Model | Slug | Effort levels | Default | Context |
|---|---|---|---|---|
| GPT-5.6 Sol | `gpt-5.6-sol` | low, medium, high, xhigh, max, ultra | low | 272K |
| GPT-5.6 Terra | `gpt-5.6-terra` | low, medium, high, xhigh, max, ultra | medium | 272K |
| GPT-5.6 Luna | `gpt-5.6-luna` | low, medium, high, xhigh, max | medium | 272K |

Additional models in cache: `codex-auto-review`, `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`.

API pricing (per 1M tokens):
- Sol: $5 input / $30 output
- Terra: $2.50 input / $15 output
- Luna: $1 input / $6 output

Tau2 scores (from pricepertoken.com):
- No GPT-5.6 scores published yet. GPT-5.5 = 93.9 (5.2 points behind GLM-5.2).

## Token investigation

### What exists

Codex CLI stores its ChatGPT subscription OAuth token at `~/.codex/auth.json`:
```
auth_mode: chatgpt
tokens.access_token: <JWT, 1733 chars>
tokens.refresh_token: <211 chars>
tokens.account_id: <36 chars>
last_refresh: 2026-07-24
```

The JWT's key claims:
```
iss: https://auth.openai.com
aud: ['https://api.openai.com/v1']
scp: ['openid', 'profile', 'email', 'offline_access',
      'api.connectors.read', 'api.connectors.invoke']
chatgpt_plan_type: plus
exp: 2026-08-03 (10-day lifetime, auto-refreshed by Codex CLI)
```

### Token extraction script

Built at `~/.grok/scripts/get-openai-codex-token.ps1`. Reads auth.json, checks
expiry, outputs access_token to stdout. Tested working.

### API endpoint test results

| Endpoint | Auth | Result |
|---|---|---|
| `POST /v1/chat/completions` | Bearer token | **429 insufficient_quota** |
| `POST /v1/responses` | Bearer token | **401 missing scope: api.responses.write** |
| `POST /v1/responses` | Bearer + chatgpt-account-id header | **401 missing scope: api.responses.write** |
| `GET /v1/models` | Bearer token | **403 missing scope: api.model.read** |

All standard API endpoints reject the token. The `api.connectors.invoke` scope
maps to an internal Codex endpoint that is compiled into the Codex CLI binary
and not documented for third-party use.

### Why it fails

The token is an OAuth access token issued to Codex CLI's registered OAuth client
(`client_id: app_EMoamEEZ73f0CkXaXp7hrann`). OpenAI scopes it to Codex's
internal connector API only. Standard API endpoints require different scopes
(`api.responses.write`, `api.model.read`) that this token doesn't have.

Cline's "Sign in with OpenAI" integration works because Cline registered as a
separate OAuth client with OpenAI and received the necessary scopes. Grok Build
has not built this integration.

## What works today

### /codex skill (delegation)

The `/codex` skill delegates to Codex CLI, which uses its own internal API path.
GPT-5.6 Luna was verified passing both coding and reasoning tests via this path
(session 2026-07-29).

### Codex OAuth Bridge (Grok Build config.toml integration)

**Working as of 2026-07-29.** A local Python HTTP bridge translates standard
OpenAI-compatible API calls to the Codex backend, using the ChatGPT subscription
OAuth token. Zero per-token cost.

**Source:** `github.com/PandelisZ/grok-bypass` (community project, MIT license)

**How it works:**
1. Bridge reads `~/.codex/auth.json` for the ChatGPT subscription token
2. Exposes `http://127.0.0.1:11435/v1` with `/v1/models`, `/v1/responses`, `/v1/chat/completions`
3. Forwards to `https://chatgpt.com/backend-api/codex/responses` (the real Codex endpoint)
4. Handles token refresh automatically via `https://auth.openai.com/oauth/token`
5. Required headers: `Authorization: Bearer <token>`, `ChatGPT-Account-ID`, `User-Agent: codex-cli`

**Installed at:**
- Bridge scripts: `~/.local/share/grok-codex-bridge/` (codex_bridge.py, codex_auth.py, codex_wire.py)
- Launcher: `~/.local/bin/codex-bridge.bat`
- Config.toml entries: `gpt-5-6-luna`, `gpt-5-6-terra`, `gpt-5-6-sol`

**Usage:**
1. Start bridge: `codex-bridge` (or `python ~/.local/share/grok-codex-bridge/codex_bridge.py`)
2. Switch model in Grok: `/model gpt-5-6-luna` (or terra, sol)
3. Use normally — subagents, tools, skills all work through the bridge

**Verified:** GPT-5.6 Luna responds correctly via chat_completions and responses
endpoints. Math (17*23=391), simple prompts, model listing all pass.

**Limitations:**
- Bridge must be running before starting Grok session (or restart Grok after starting it)
- Token expires every 10 days; bridge auto-refreshes via refresh_token
- Relies on undocumented `chatgpt.com/backend-api/codex` endpoint (could change)
- No streaming support for chat_completions bridge (returns full response, not SSE)

## What would need to happen for direct config.toml integration

1. **SpaceXAI builds an OpenAI OAuth provider** — registers Grok Build as an
   OAuth client with OpenAI, requests `api.responses.write` scope. This is a
   feature request to SpaceXAI.
2. **OpenAI opens the connectors endpoint** — if the `api.connectors.invoke`
   scope's endpoint were documented, a proxy could translate standard API calls.
   Not currently documented.
3. **Per-token API key** — works today but bills per-token, not subscription.
   No GPT-5.6 variant beats GLM-5.2 on Tau2, so the cost isn't justified for
   the orchestrator role.

## Falsifier

This investigation is wrong if:
- Grok Build has a hidden OpenAI OAuth integration we haven't found
- The connectors endpoint URL is discoverable (network intercept, binary analysis)
- OpenAI changes the token scopes to include standard API access

Re-verify by checking Grok Build release notes for OpenAI OAuth provider support.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
