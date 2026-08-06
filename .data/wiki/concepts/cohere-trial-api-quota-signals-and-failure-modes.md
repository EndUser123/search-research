---
title: "Cohere trial API: quota signals and failure modes"
created: 2026-08-06
source: session-20260806
tags: [cohere, api, quota, trial-key, rate-limit, provider-config]
sources:
  - https://docs.cohere.com/docs/rate-limits (Cohere, 2026)
  - https://docs.cohere.com/reference/errors (Cohere, 2026)
summary: >
  Cohere trial keys are limited to 1000 API calls/month. The monthly limit
  is NOT in response headers — it's only in the 429 body text. The {"id":"..."}
  JSON response that looks like a UUID is actually a rate-limit error body
  containing "message": "You are using a Trial key, limited to 1000 API calls
  / month." PI sends role='developer' which Mistral rejects but Cohere accepts.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/provider-rate-limits-and-benchmarking-strategies.md
    type: extends
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
  - target: wiki/concepts/dedicated-quota-first-dispatch-routing.md
    type: related
---

# Cohere trial API: quota signals and failure modes

## Decision context

Benchmarking Cohere models failed with `{"id":"..."}` responses at ~400ms
latency. Initial diagnosis assumed rate limiting, but the response format
(a UUID in JSON) was unusual — most providers return a structured error.
Investigation revealed the full body contains the actual error message.

## Key findings

### 1. Trial key monthly limit (1000 calls/month)

Confirmed via direct API test (2026-08-06):
- Cohere returns HTTP 429 with body: `{"id":"...", "message":"You are using a
  Trial key, which is limited to 1000 API calls / month."}`
- The `{"id":"..."}` is a request trace ID, not the error itself
- The actual error is in the `message` field
- The benchmark truncated error previews at 30 chars, cutting off the message

### 2. Response headers don't contain monthly remaining

Headers on 429 responses:
- `x-trial-endpoint-call-limit: 20` (per-minute RPM, not monthly)
- `x-trial-endpoint-call-remaining: 19` (per-minute remaining)
- No `x-endpoint-monthly-call-limit` or `x-monthly-call-remaining` header

The monthly limit is ONLY in the response body text. To detect monthly
exhaustion, you must parse the 429 body for "1000 API calls / month."

### 3. Per-minute vs monthly are separate limits

- Per-minute: 20 RPM (self-heals in 60 seconds)
- Monthly: 1000 calls/month (resets monthly, does NOT self-heal)
- A request can succeed on per-minute but fail on monthly (and vice versa)

### 4. Cohere trial key is shared across all Cohere models

`command-a-plus`, `command-a-reasoning`, and `north-mini-code` all share the
same 1000/month trial bucket. Exhausting calls on one model exhausts all.

This contrasts with providers that have per-model rate limits (see
[[model-fleet-provider-pools]] for the full provider inventory).

## What this means for our workspace

- `fleet_quota.py` `check_cohere()` parses the 429 body for "1000 API calls /
  month" to detect exhaustion. When not exhausted, telemetry undercount provides
  an approximate remaining count.
- The spawn gate (`PreToolUse_spawn_model_gate.py`) needs Cohere in its
  `write_quota_cache` provider map — currently missing (REV-004 from /review).
- The benchmark error preview should show more of the body (currently truncated
  at 30 chars, hiding the actual error message).
- Related: [[tool-fallbacks]] documents Cohere transport failure modes.
  [[dedicated-quota-first-dispatch-routing]] covers the dispatch path strategy.

## Receipts

- `~/.grok/skills/model-quota/scripts/fleet_quota.py:499-569` — `check_cohere()`
  implementation, verified 2026-08-06
- `~/.grok/skills/model-quota/scripts/fleet_quota.py:743-762` —
  `_count_cohere_calls_this_month()` telemetry counter
- Direct API probe (2026-08-06): `POST https://api.cohere.ai/compatibility/v1/
  chat/completions` → HTTP 429 with body containing monthly limit message

## Falsifier

If Cohere adds a `x-monthly-call-remaining` header in a future API update,
body-text parsing becomes unnecessary. Re-check headers after Cohere API
updates. If Cohere changes the trial cap from 1000, the hardcoded constant
in fleet_quota.py will report wrong percentages.

## Sources

- Direct API test (2026-08-06): verified 429 response headers + body
- [Cohere rate limits docs](https://docs.cohere.com/docs/rate-limits)
- [Cohere errors reference](https://docs.cohere.com/reference/errors)

## Auto-related

- [[cohere-api-integration-rate-limit-tracking]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[model-quota-contention-coordination-fleet-rate-limiting]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[proactive-reactive-pair-pattern-for-predictable-failure-prevention]]

