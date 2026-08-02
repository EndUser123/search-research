---
title: Model error classification architecture improvements
thread_id: model-error-classification-architecture-20260801
created: 2026-08-01
status: OPEN — design needed
priority: MEDIUM
current_session_id: 019fb933-040b-7720-a257-e364f5df726f
last_updated_by: grok
last_updated_at: 2026-08-01T21:00:00Z
---

# Handoff: Model error classification architecture improvements

## Context

Session 019fb933 discovered that the entire `serde_broken` list (10 models) was false positives — caused by the PostToolUseFailure hook's overly broad pattern matching, missing prerequisite services, and quota exhaustion misclassified as serde. We fixed the immediate issues (mutual exclusivity, HTTP status routing, escalating cooldowns, error receipts). Three architectural improvements remain that need design work.

## /www research validation

The /www research confirmed these are industry-known patterns:
- OpenClaw, ccLoad, LLM-API-Key-Proxy all hit the same false-positive blacklist problem
- async-openai issues #61, #503, #548 confirm intermittent serde on OpenAI-compatible APIs
- API gateway best practices: structured exception hierarchy > HTTP status code > string matching

## Items

### 1. Structured exception hierarchy for error classification hooks

**Current:** `is_rate_limit_error(error_text, status_code)` and `is_serde_error(error_text, status_code)` use string matching with HTTP status code override.

**Target:** A typed exception classification system:
```python
class ErrorClass(Enum):
    RATE_LIMIT = "rate_limit"      # 429/503, retriable
    SERDE = "serde"                 # serialization/deserialization
    AUTH = "auth"                  # 401/403
    SERVER = "server"              # 5xx (not 503)
    CLIENT = "client"              # 400/422
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

def classify_error(error_text, status_code=None) -> ErrorClass:
    ...
```

This replaces the two separate boolean functions with a single classifier that returns one class. Both hooks consume the same classification. The spawn gate then decides per-class what to do (rate_limit → cooldown, serde → learn + cooldown, auth → hard block, etc.).

**Effort:** L (design + refactor both hooks + update tests)

### 2. Model-scoped cooldowns instead of provider-scoped

**Current:** Rate-limit hits mark the entire provider as exhausted (`update_cache(provider, pct=0)`). One model's rate limit blocks all sibling models on the same provider.

**Target:** Track cooldowns per model, not per provider. The quota cache structure needs to change from `{provider: {pct}}` to `{provider: {pct, models: {model_slug: {pct, expires}}}}`. The spawn gate checks model-level first, then falls back to provider-level.

**Effort:** L (cache structure change + both hooks + tests)

### 3. Recovery verification — auto re-test models after cooldown expiry

**Current:** When a learned-serde-broken entry's TTL expires, the model is silently allowed again. No verification that the model actually works.

**Target:** After cooldown expiry, the first spawn of that model should be treated as a "probe" — if it succeeds, clear the learned entry and reset fail_count. If it fails, re-learn with fresh evidence and advance the cooldown tier. This could be a lightweight hook or a periodic background check.

**Effort:** M (design the probe trigger + implement in spawn gate or separate script)

## Acceptance criteria

- [ ] Structured exception hierarchy designed and implemented
- [ ] Model-scoped cooldowns: one model's rate limit does not block siblings
- [ ] Recovery verification: models are re-tested after cooldown expiry
- [ ] All existing tests pass + new tests for each improvement

## Related

- Wiki concept: `tool-fallbacks.md` (spawn exclusions table)
- Wiki concept: `model-tool-calling-capability-matrix.md` (per-model capability tracking)
- Fleet registry: `skills/model-quota/scripts/fleet-models.json` (spawn_notes with verified test results)
- /www research findings: industry patterns from OpenClaw, ccLoad, async-openai
