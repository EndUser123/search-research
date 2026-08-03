---
title: "Cohere API integration: compatibility endpoint, response-header quota tracking, and fleet rate-limit management"
created: 2026-08-03
source: session-2026-08-03 (Cohere key setup + fleet wiring)
tags: [cohere, api, rate-limits, quota-tracking, model-fleet, response-headers, spawn-gate]
summary: >
  Cohere exposes an OpenAI-compatible endpoint at api.cohere.ai/compatibility/v1
  that works with Grok's chat_completions backend including tool calling. The
  rate-limits documentation page does NOT mention it, but every API response
  includes live quota headers (x-trial-endpoint-call-remaining for per-minute,
  x-endpoint-monthly-call-limit for monthly cap). No dedicated usage API exists
  and no monthly-remaining header exists — monthly consumption must be tracked
  locally via telemetry. Per-minute rate limits (20 req/min trial) require
  different fleet management than monthly/5h limits: the spawn gate must NOT
  block on 429 (the 1-hour TTL is wrong for a 60-second rate window).
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - https://docs.cohere.com/docs/compatibility-api (Cohere, 2026) — OpenAI-compatible endpoint
  - https://docs.cohere.com/docs/rate-limits (Cohere, 2026) — rate limit tiers
  - https://github.com/cohere-ai/cohere-developer-experience/blob/main/fern/pages/going-to-production/rate-limits.mdx (Cohere GitHub, 2026) — source of rate-limits doc
relations:
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: complements
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: related
---

# Cohere API integration: compatibility endpoint, response-header quota tracking, and fleet rate-limit management

## Decision context

**Why this research was needed:** the operator obtained a Cohere API key and asked
how to use it in Grok Build and which models are interesting. This required: (1)
confirming Cohere has an OpenAI-compatible endpoint that Grok's `[model.*]` config
can target, (2) understanding the rate-limit structure, and (3) wiring Cohere into
the fleet's quota management infrastructure (spawn gate, error hook, quota dashboard,
benchmark, fleet-models registry).

A critical sub-question emerged: does Cohere expose a programmatic usage/quota API?
The initial investigation probed 9 candidate endpoints — all returned 404 — and
concluded "no quota API exists." The operator pushed back, asking whether response
headers or community approaches had been checked. That pushback uncovered live
quota-tracking headers that the rate-limits documentation page never mentions.

## Key findings

### 1. OpenAI-compatible endpoint confirmed and working

Cohere's Compatibility API at `https://api.cohere.ai/compatibility/v1` speaks
the OpenAI Chat Completions protocol. Grok's `chat_completions` backend works
with no special headers — standard `Authorization: Bearer` auth, no `x-api-key`
needed (unlike Anthropic).

**Verified capabilities** (test-fired 2026-08-03 with `command-a-plus-05-2026`):
- Plain chat completions: HTTP 200, correct responses
- Tool calling (`tools` parameter): HTTP 200, valid `tool_calls` array returned
- Streaming (`stream: true`): supported per docs
- Structured outputs (`response_format`): supported per docs
- Embeddings: supported via `/embeddings` endpoint (`embed-v4.0`)

### 2. The `reasoning_effort` gotcha

The Compatibility API accepts `reasoning_effort` but only supports `"none"` and
`"high"`. Passing `"medium"` or `"low"` returns HTTP 422:

```json
{"message":"unprocessable entity: reasoning_effort 'medium' and 'low' are not supported. Use 'high' instead"}
```

**Fleet impact:** the global `default_reasoning_effort = "medium"` in config.toml
inherited by all models will cause Command A Reasoning to fail unless overridden.

**Fix (verified 2026-08-03):** set `reasoning_effort = "none"` in the CAR model
block in config.toml. This tells Grok to send "none" (which Cohere accepts),
disabling thinking in the compat API. Cohere's native `thinking` parameter
controls reasoning independently — the model still reasons internally when
the compat API receives `reasoning_effort = "none"`, but Grok doesn't send a
conflicting default. Additionally, set `supportsReasoningEffort: False` in
PI's models.json for the Cohere provider so PI doesn't send the parameter
either.

**Spawn limitation (verified 2026-08-03):** CAR via `spawn_subagent` fails on
instruction-following tasks with `empty response from model (reasoning_only)`
after 357-382s. Root cause: the reasoning model spends its entire output budget
thinking about Grok's heavy agent context (~35K tokens of AGENTS.md + skills +
system prompt) and produces no content response. CAR via spawn works for
reasoning tasks (probe 10s, reasoning 7.5s, code-gen 25.6s) but fails on
instruction-following precision tasks. Workaround: use PI or OC (lighter
context) for structured-output dispatch. Documented in [[tool-fallbacks]].

### 3. Response headers contain live quota data — undocumented

This is the finding that the operator's pushback uncovered. Every Cohere API
response includes these headers (verified via empirical probe, 2026-08-03):

| Header | Value | Documented? | Changes per call? |
|---|---|---|---|
| `x-endpoint-monthly-call-limit` | `1000` | ❌ Not in rate-limits doc | No (static cap) |
| `x-trial-endpoint-call-limit` | `20` | ❌ Not in rate-limits doc | No (static cap) |
| `x-trial-endpoint-call-remaining` | `19` → `18` → `17`... | ❌ Not in rate-limits doc | **Yes — decrements per call, resets in 60s** |

**Neither the rate-limits documentation page nor the GitHub source** (`cohere-ai/cohere-developer-experience/fern/pages/going-to-production/rate-limits.mdx`) mention these headers. They were discovered by inspecting raw response headers during a probe call.

**What is NOT available:** there is no `x-endpoint-monthly-call-remaining` header.
The API tells you the monthly ceiling (1000) and the per-minute remaining (19/20),
but never how many monthly calls have been consumed. Monthly tracking requires
local telemetry counting.

### 4. No dedicated usage/billing API

Nine candidate endpoints were probed — all returned 404:

```
api.cohere.com/v1/usage         → 404
api.cohere.com/v2/usage         → 404
api.cohere.com/v1/billing       → 404
api.cohere.com/v1/me            → 404
api.cohere.com/v1/account       → 404
api.cohere.com/v1/limits        → 404
api.cohere.com/v1/quota         → 404
api.cohere.com/compatibility/v1/usage → 404
api.cohere.com/v1/dashboard     → 404
```

The response-header probe is the only programmatic quota signal. Usage is
otherwise dashboard-only at `dashboard.cohere.com`.

## Fleet rate-limit management decision

### The problem: per-minute limits need different gate behavior than monthly limits

The existing fleet infrastructure has two layers for rate-limit management,
documented in [[model-fleet-provider-pools]] and governed by the selection
policy in [[model-pool-selection-policy-speed-quota-diversity]]:

1. **PreToolUse_spawn_model_gate.py** — reads quota cache, blocks spawns to
   providers below 10% quota
2. **PostToolUseFailure_spawn_quota.py** — on 429, marks provider as `pct=0`
   in cache with a 1-hour TTL (`ERROR_HOOK_EXPIRY_SEC = 3600`)

This 1-hour block is correct for providers with monthly/5h quota windows
(OpenCode Go, GLM, MiniMax). **It is wrong for Cohere** because Cohere's rate
limit resets in 60 seconds — blocking for an hour after a single 429 would
effectively disable Cohere for the rest of the session.

### Decision: track 429s but never block

Cohere goes into `FREE_PROVIDERS` in the spawn gate — recognized but never
blocked. The error hook still maps `cohere-` to the `cohere` provider ID and
logs 429s to `spawn-blocks.jsonl` and the escalation tracker, but the gate
won't deny spawns based on those 429s.

**Steelman (the rejected alternative):** block Cohere on 429 with a short TTL
(60-90 seconds matching the rate window). This would protect against burst
failures during the rate window. Rejected because: (1) the spawn gate's TTL
mechanism is per-provider, not per-model, so a 60s block would also block
Command A+ when North Mini Code triggered the 429; (2) the 429 self-heals
in 60s without intervention — the cost of a failed spawn (8-38s wasted) is
lower than the cost of a false block that prevents a valid call; (3) Cohere
is `parallel_safe_count: 1` (serial dispatch), so burst collisions are
structural, not a race condition.

**Falsifier:** if Cohere 429 rates exceed 20% of spawn attempts (i.e., more
than 1 in 5 spawns fails), the never-block policy is costing more time than
it saves and a short-TTL block should be implemented. Track via
`spawn-blocks.jsonl` error rates.

### Monthly tracking via local telemetry

Since the API provides no monthly-remaining signal, `check_cohere()` in
`fleet_quota.py` counts calls from `P:/.artifacts/model-telemetry/usage.jsonl`
for the current month. This undercounts because Grok's native model dispatch
(Rust HTTP client talking to Cohere directly via config.toml `[model.*]`)
bypasses Python instrumentation entirely. The monthly number shown in the
dashboard is a floor, not exact. This is the same class of blind spot
documented in [[inference-in-code-blind-spot]] — values that look authoritative
but have an unverified gap between what's measured and what's real.

## Workspace wiring (what was changed)

| Component | Change | File |
|---|---|---|
| `config.toml` | 4 Cohere model blocks (A+, A Reasoning, A, North Mini Code) | `~/.grok/config.toml` |
| `.env` | `COHERE_API_KEY` + `CO_API_KEY` alias | `P:/.env` |
| Spawn gate | `cohere-` in `PREFIX_TO_PROVIDER` + `cohere` in `FREE_PROVIDERS` | `~/.grok/hooks/PreToolUse_spawn_model_gate.py` |
| Error hook | `cohere-` in `PREFIX_TO_PROVIDER` (429 tracking) | `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` |
| Quota dashboard | `check_cohere()` — response-header probe + telemetry monthly count | `~/.grok/skills/model-quota/scripts/fleet_quota.py` |
| Fleet registry | Cohere in `provider_prefixes`, `provider_quota_info`, coding lane tier1, reasoning lane tier2 | `~/.grok/skills/model-quota/scripts/fleet-models.json` |
| Benchmark | Cohere pricing (`$2.50/$10.00`), provider detection, label | `~/.grok/skills/model-benchmark/scripts/benchmark.py` |

### North Mini Code positioning

The operator's directive: `cohere-north-mini-code` is **primary** in the coding
lane (tier1 position 1), not overflow. Rationale: it has a dedicated key with
its own rate-limit bucket, separate from the Zen/OpenCode shared pool. The same
model via Zen (`zen-north-mini-code-free`) and OpenRouter (`or-north-mini-code-free`)
serve as fallback quota buckets. Benchmark showed Q=1.0 across all tiers.

## What this means for our workspace

- **Cohere is now a fully integrated fleet provider** with live quota tracking,
  spawn-gate recognition, error-hook 429 logging, and benchmark cost tracking.
- **The per-minute rate limit is managed by serial dispatch** (`parallel_safe_count: 1`),
  not by gate blocking. One-at-a-time dispatch keeps Cohere under 20 req/min
  naturally for its primary use cases (cross-family diversity for `/tp` and
  `/review`, primary coding model for North Mini Code).
- **Monthly consumption is a floor count** — the dashboard shows calls logged
  through Python instrumentation. Native Grok dispatch (`/model cohere-*` in
  the TUI) is not counted. If the monthly count appears low, it may be
  undercounting rather than reflecting actual remaining quota.
- **The response-header finding generalizes**: any future provider integration
  should check response headers for rate-limit data before concluding "no quota
  API exists." This is the same lesson as [[replacement-before-investigation-pattern]]
  — don't conclude "doesn't exist" without checking the obvious inspection points
  first. For API integrations, response headers are the equivalent of "have you
  read the docs?"

## Falsifier

1. If Cohere adds a dedicated usage API endpoint (`/v1/usage` or similar) in
   the future, the response-header probe becomes unnecessary overhead (1 API
   call per `/model-quota` run) and should be replaced with a non-consuming
   API call.
2. If Cohere 429 rates exceed 20% of spawn attempts, the never-block policy
   should be revisited with a per-minute TTL block.
3. If Cohere changes the header names (undocumented APIs can change without
   notice), `check_cohere()` will silently report `0/0` — the function should
   be tested on first use after any Cohere API version bump.

## Receipts

- Response headers verified via `P:/tmp/cohere_headers.py` probe, 2026-08-03:
  `x-trial-endpoint-call-limit: 20`, `x-trial-endpoint-call-remaining: 19`,
  `x-endpoint-monthly-call-limit: 1000`
- `reasoning_effort` rejection verified via `P:/tmp/test_cohere.py`, 2026-08-03:
  HTTP 422 on `"medium"`, HTTP 200 on `"high"`
- Tool calling verified via same script: valid `tool_calls` response from
  `command-a-plus-05-2026`
- Benchmark results: 80 calls, 58 OK, 22 FAIL (rate-limit collisions), Q=0.98/1.0
  average when responding. Full output in session transcript.
- 404 endpoint probe: 9 endpoints tested, all returned 404
- Spawn gate implementation: `~/.grok/hooks/PreToolUse_spawn_model_gate.py`
  lines 27-43 (`PREFIX_TO_PROVIDER`, `FREE_PROVIDERS`)
- Error hook implementation: `~/.grok/hooks/PostToolUseFailure_spawn_quota.py`
  lines 25-31 (`PREFIX_TO_PROVIDER`)
- Quota checker implementation: `~/.grok/skills/model-quota/scripts/fleet_quota.py`
  `check_cohere()` function + `_count_cohere_calls_this_month()`

## Sources

- [Using Cohere models via the OpenAI SDK](https://docs.cohere.com/docs/compatibility-api) (Cohere, 2026) — compatibility endpoint base_url, auth, supported parameters
- [Cohere API Rate Limits](https://docs.cohere.com/docs/rate-limits) (Cohere, 2026) — trial/production rate tiers
- [Cohere rate-limits.mdx source](https://github.com/cohere-ai/cohere-developer-experience/blob/main/fern/pages/going-to-production/rate-limits.mdx) (Cohere GitHub, 2026) — confirms rate-limits doc does not mention response headers
- [Command A API Pricing](https://pricepertoken.com/pricing-page/model/cohere-command-a) (PricePerToken, 2026) — $2.50/$10.00 per 1M tokens

## Auto-related

- [[fleet-quota-api-discovery-2026]]
- [[openai-subscription-models-in-grok-build]]
- [[cdp-network-interception-and-sse-capture-for-llm-chat]]
- [[skill-catalog]]
- [[testing-methodology-both-outcomes-informative]]

