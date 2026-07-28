---
title: "Groq free tier TPM limit: 6000 tokens per minute blocks large max_tokens"
created: 2026-07-28
source: session-2026-07-28
tags: [groq, rate-limit, tpm, free-tier, model-behavior, benchmark, http-413]
summary: >
  Groq's free tier (on_demand service tier) enforces a 6000 Tokens Per Minute
  (TPM) limit. Any request where max_tokens > 6000 is rejected with HTTP 413
  before inference runs — regardless of actual output size. This affects all
  models on the Groq provider, not just reasoning models. The fix is per-tier
  token budgets that request only what each benchmark tier needs.
agent: grok
host: grok
cognitive_load: 2
verification: observed-and-verified
relations:
  - target: wiki/concepts/gemini-gemma-quota-rate-limits-2026-07-22.md
    type: complements
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
---

# Groq free tier TPM limit: 6000 tokens per minute

## Decision context

During fleet benchmark validation (2026-07-28), all 3 Groq models failed with
"Request too large" (HTTP 413). The initial hypothesis was that `max_tokens=32768`
on reasoning models caused context overflow. A discriminating test disproved
this: the non-reasoning `groq-llama-3-1-8b-instant` with `max_tokens=8192` also
failed. The actual root cause is a provider-level TPM limit, not a model-level
context limit.

## The constraint

Groq's free tier (`on_demand` service tier) enforces a **6000 TPM (Tokens Per
Minute)** limit. The API rejects any request where the reserved output budget
(`max_tokens`) exceeds 6000 — even if the model would only produce 30 tokens
of actual content.

**Error response (verified):**
```json
HTTP 413
{
  "error": {
    "message": "Request too large for model `llama-3.1-8b-instant` in organization `org_...` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Requested 8238, please reduce your message size and try again.",
    "type": "tokens",
    "code": "rate_limit_exceeded"
  }
}
```

## Affected models

All 3 Groq models in the fleet config have `max_completion_tokens > 6000`:

| Model | max_completion_tokens | reasoning | Fails? |
|-------|----------------------|-----------|--------|
| `groq-qwen3-6-27b` | 32768 | true | Yes |
| `groq-gpt-oss-120b` | 32768 | true | Yes |
| `groq-llama-3-1-8b-instant` | 8192 | false | Yes |

## The fix: per-tier token budgets

The benchmark now uses per-tier token budgets (`TIER_MAX_TOKENS`) instead of
requesting each model's full `max_completion_tokens`. Each tier requests only
what its prompt needs:

- mechanical: 512 tokens (needs ~30)
- reasoning-base: 512 non-reasoning / 5000 reasoning (needs ~200 + CoT)
- code-exec: 1024 (needs ~200)
- tool-calling: 512 (needs ~30)

All universal-tier budgets stay under 6000. After the fix, all 3 Groq models
pass on universal tiers. Deep tiers (long-context at 128K input, deep-reasoning
at 16384 output) are exempt — they intentionally test capabilities that exceed
free-tier limits.

**Verification:** `groq-llama-3-1-8b-instant` scored Q=1.0 on mechanical (466ms)
and `groq-qwen3-6-27b` scored Q=1.0 on reasoning-base (1701ms) after the fix.
Both were failing before.

## What this means for fleet routing

- Groq models work fine for short-prompt, short-output tasks (mechanical,
  tool-calling, simple code generation) where `max_tokens ≤ 6000`
- Groq models CANNOT be used for tasks requiring large output budgets
  (deep reasoning, long-form generation) without upgrading to Dev Tier
- When selecting a model for a task, check whether the task's expected output
  size fits within Groq's 6000 TPM — if not, route to a different provider
- The `--max-tokens` override flag can test specific budget levels, but any
  value > 6000 will fail on Groq free tier
- See [[model-fleet-provider-pools]] for the full fleet inventory and
  [[gemini-gemma-quota-rate-limits-2026-07-22]] for comparable rate-limit
  patterns on other providers
- The [[parameter-aware-benchmark-tier-system]] documents how per-tier budgets
  solve this class of problem generally

## Falsifier

This finding is wrong if Groq raises the free-tier TPM limit above 6000
(check by sending a request with `max_tokens=7000` and checking for HTTP 413).
The error message explicitly says "Limit 6000" so this is unlikely to change
without a pricing tier update.

## Sources

- Live API test 2026-07-28: HTTP 413 response from `api.groq.com/openai/v1/chat/completions`
  with `max_tokens=8192` on `llama-3.1-8b-instant`
- Groq console: `https://console.groq.com/settings/billing` (Dev Tier upgrade prompt)

## Receipts

- `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py` — `TIER_MAX_TOKENS`
  dict and `get_budget()` function (per-tier budget implementation)
- `~/.grok/skills/model-benchmark/scripts/benchmark.py:170` — `model_capacity`
  and `max_tokens` computation (engine budget logic)
- Commit `c89bb9c`: per-tier budgets fix that resolved the Groq failures
- Discriminating test: `groq-llama-3-1-8b-instant` with `max_tokens=8192`
  returned HTTP 413 with the exact TPM limit message (verified via direct
  `requests.post` call, not benchmark framework)
