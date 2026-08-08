---
title: "Spawn failure error taxonomy: 7-class classification with reactive quarantine"
created: 2026-08-08
source: session-2026-08-08
tags: [error-classification, spawn-gate, quarantine, posttoolusefailure, model-fleet, diagnostics, architecture, serde, rate-limit, context-window]
host: grok
agent: grok
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/evidence-driven-model-router-architecture.md
    type: complements
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: extends
  - target: wiki/concepts/hook-fleet-io-failure-modes-cascade-amplification.md
    type: refines
  - target: wiki/concepts/cohere-trial-api-quota-signals-and-failure-modes.md
    type: related
summary: >
  The PostToolUseFailure hook classifies spawn failures into a 7-class taxonomy
  (context_too_large, rate_limit, serde, model_gone, auth_error, provider_outage,
  unknown) with class-appropriate actions — replacing the prior binary (serde vs
  rate_limit) that misclassified context-too-large as serde and left auth/outage/gone
  errors unclassified. Combined with the decision to use reactive quarantine
  (spawn fails → classify → quarantine excludes model until cooldown) instead of
  proactive EOL tracking (expires_at field), the system self-heals without
  requiring the operator to maintain external data about provider lifecycles.
---

# Spawn failure error taxonomy: 7-class classification with reactive quarantine

## Decision context

The model-selection defect fix (design doc at `docs/design/model-selection-defect-fix-20260808/DESIGN.md`)
revealed that the PostToolUseFailure hook used a binary error classification:
serde vs rate_limit. This caused three problems:

1. **Context-too-large (422) was classified as serde** — both share HTTP 422, but
   a context-length error means the model works for smaller prompts, while a serde
   error means the model is fundamentally incompatible with Grok Build's transport.
   Treating them the same caused models to be quarantined as "broken" when they
   were just too small. See [[execution-path-based-model-routing-grok-build]]
   for how the spawn gate uses serde classification.

2. **Auth errors (401/403) were unclassified** — they fell through with no action,
   meaning the system couldn't distinguish "bad API key" from "model works fine."

3. **Model-gone (410) and provider-outage (500/502/503) were unclassified** — 410
   means the model is permanently dead (should quarantine with long cooldown),
   while 503 is transient (should quarantine with short cooldown). Both were
   silently ignored. The [[hook-fleet-io-failure-modes-cascade-amplification]]
   concept documents the advisory-write pattern that all these hooks follow.

Simultaneously, the design doc proposed a proactive `expires_at` field on each
candidate (Unit 2) to track vendor-announced end-of-life dates. The operator
rejected this: "Very few providers tell you the end-of-life date; it's almost
meaningless because it can change." The reactive quarantine loop — where failures
are classified and the model is temporarily excluded — handles dead models after
the first failure, making proactive tracking unnecessary.

## The 7-class taxonomy

| Class | HTTP codes | Detection | Action |
|-------|-----------|-----------|--------|
| `context_too_large` | 422 + context patterns | `CONTEXT_TOO_LARGE_PATTERNS` matched | Quarantine (standard cooldown) |
| `rate_limit` | 429 (always) | Status code or `RATE_LIMIT_PATTERNS` | Mark provider at 0%, quarantine |
| `serde` | 400/422 + serde patterns | `SERDE_BROKEN_PATTERNS` matched | Learn serde-broken (escalating cooldown) |
| `model_gone` | 410/404 | Status code | Quarantine (standard cooldown, long reprobe) |
| `auth_error` | 401/403 | Status code | **Log only** — operator issue |
| `provider_outage` | 500/502/503 | Status code | Quarantine with **60s** cooldown |
| `unknown` | anything else | No pattern matched | **Log only** — for investigation |

### Key design choices

**Context-too-large is checked before serde.** Both can produce HTTP 422, but
the distinction matters: a context error means the model works for smaller prompts,
while serde means the model output fails Grok Build's deserialization. The
`CONTEXT_TOO_LARGE_PATTERNS` list (context length, maximum tokens, input length,
etc.) is checked first. If matched, the model is quarantined with a standard
cooldown — it's not broken, just too small for the current orchestrator's prompt.

**Auth errors do NOT quarantine.** A 401/403 is an operator issue (bad API key,
expired credentials, wrong permissions). Quarantining the model would mask the
real problem — the operator needs to see the error in the diagnostic log and fix
the key. The error is logged to `spawn-errors.jsonl` with an actionable hint but
no quarantine record is written.

**Provider outages get a 60s cooldown, not the standard 300s.** A 500/502/503 is
transient — the provider's server is temporarily unavailable. The standard 5-minute
quarantine would over-block: by the time the cooldown expires, the provider is
likely back. The 60s cooldown lets the system retry quickly.

### Precedence rules

Context-too-large > rate_limit > model_gone > auth_error > provider_outage > serde > unknown.

Status codes take priority over pattern matching (industry best practice: HTTP
status is authoritative, error body text is ambiguous). The one exception is
context-too-large: it's checked before status-code-based serde classification
because a 422 with context patterns is definitively context-too-large, not serde.

## Reactive quarantine over proactive EOL

The design doc originally proposed an `expires_at: str | None` field on each
`CandidateRecord` (Unit 2), with an `is_expired()` gate in the router's
`evidence_eligibility()` function. The operator rejected this approach:

> "Very few providers tell you the end-of-life date; it's almost meaningless
> because it can change. I don't think we even need to look for that, nor do we
> need that code."

The reactive quarantine loop is the alternative:
1. A spawn fails with a model-gone error (410) or serde error
2. `PostToolUseFailure` classifies the error and writes a `QuarantineRecord`
3. The next `pick()` call reads quarantine records via `load_quarantine_records()`
4. The router's `health_gate` excludes quarantined candidates until `reprobe_after` elapses
5. After cooldown, the candidate is re-probed — if it fails again, the cooldown escalates

This loop is self-healing: it doesn't require the operator to research and maintain
EOL dates for 16+ candidates. The cost is one failed spawn (the first attempt after
a model dies), which is typically 8-38 seconds of wasted time. For a fleet that
dispatches dozens of spawns per session, this is negligible. The
[[evidence-driven-model-router-architecture]] concept covers how the router
consumes quarantine records via the `health_gate`.

**Rejected alternative (proactive EOL):** add `expires_at` to each candidate,
research each vendor's EOL announcement date, and gate on it. This was rejected
because (a) most providers don't announce EOL dates, (b) dates change silently,
(c) maintaining the data for 16+ candidates is ongoing operator overhead, and
(d) the reactive loop already handles the failure case with negligible cost.

## Diagnostic logging

Every classified failure is logged to `~/.cache/opencode/spawn-errors.jsonl`:

```json
{
  "ts": 1723123456.789,
  "model": "nim-deepseek-v4-flash",
  "provider": "nim",
  "error_class": "model_gone",
  "status_code": 410,
  "message": "410 Gone: model deprecated",
  "matched_patterns": [],
  "hint": "Model is permanently unavailable..."
}
```

This gives the operator a diagnostic trail to spot patterns: which providers fail
most, which error classes dominate, which models are chronically broken. The log
is append-only JSONL — one line per failure — and can be analyzed with standard
JSON tooling.

## What this means for our workspace

- **No proactive EOL maintenance needed.** The operator doesn't need to research
  vendor EOL dates. When a model dies, the first spawn fails, the error is
  classified, and the model is quarantined. The operator can review the diagnostic
  log to set `lifecycle: retired` in the registry at their convenience.

- **Context-too-large failures are recoverable.** A model that's too small for
  Grok's 60K system prompt (but works fine for smaller prompts) is quarantined,
  not treated as permanently broken. If the orchestrator switches to a leaner
  prompt, the model becomes viable again after the cooldown.

- **Auth failures surface immediately.** A 401/403 no longer silently falls
  through — it's logged with an actionable hint. The operator can grep the
  diagnostic log for `auth_error` to find credential issues.

- **Provider outages self-heal.** A transient 503 quarantines the model for 60
  seconds, not 5 minutes. The next spawn attempt after 60s retries the provider.

- **The `policy: excluded` field handles chronically unusable providers.**
  Cerebras (100K tokens/hour) and groq (similar low caps) are excluded from
  routing entirely via `policy: excluded` in the registry. They stay registered
  (discoverable for manual use) but disappear from automatic selection. This is
  more honest than token-budget-aware routing, which would require querying each
  provider's rate-limit API — most don't expose one reliably. The
  [[cohere-trial-api-quota-signals-and-failure-modes]] concept documents a
  related case where provider-specific quota semantics require special handling.

## Falsifier

If a provider announces an EOL date months in advance AND the first-failure cost
(8-38 seconds of wasted spawn time + the cognitive overhead of seeing the failure)
becomes material for the operator, proactive EOL tracking would be worth the
maintenance overhead. As of 2026-08-08, no provider in the fleet has announced an
EOL date more than 24 hours before the model went offline.

If the diagnostic log (`spawn-errors.jsonl`) accumulates a high volume of
`unknown` classifications (>20% of failures), the taxonomy needs expansion —
new patterns need to be added from the unclassified error text.

## Receipts

- `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` — `classify_error()` function
  (lines 96-168), `log_error()` function (lines 170-195), action path (lines 380-430)
- `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` — `CONTEXT_TOO_LARGE_PATTERNS`
  (lines 30-42), `MODEL_GONE_STATUS_CODES`, `AUTH_ERROR_STATUS_CODES`,
  `PROVIDER_OUTAGE_STATUS_CODES` (lines 23-35)
- `~/.grok/hooks/tests/test_spawn_quota_error_learner.py` — `TestRichClassification`
  class (13 tests covering all 7 classes + precedence + hint completeness)
- `~/.grok/skills/model-quota/scripts/model_router.py` — `evidence_eligibility()`
  reverted to lifecycle-only (no `expires_at` check)
- `docs/design/model-selection-defect-fix-20260808/DESIGN.md` — design doc with
  Execution Status documenting the revert decision

## Auto-related

- [[tool-fallbacks]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[scope-matching-verification-discipline]]
- [[serde-broken-false-positive-sweep-20260801]]

