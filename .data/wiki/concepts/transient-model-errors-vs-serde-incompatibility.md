---
title: "Transient model errors vs serde incompatibility: distinguishing finish_reason enum mismatches from field type failures"
created: 2026-08-03
source: session-20260803
tags: [model-dispatch, serde, error-classification, grok-build, transient, false-positive, deserializer, code-orchestrates-model-judges]
agent: grok
host: grok
cognitive_load: 2
verification: observed
summary: >
  Grok Build's deserializer uses closed enums for OpenAI-compatible fields.
  When a model returns a value outside the enum (e.g., finish_reason: "error"),
  the deserializer fails with "unknown variant" or "expected one of" — the same
  error class as real serde incompatibilities (null field type mismatches). But
  the root cause is different: the model errored internally on a specific prompt,
  not a systemic transport incompatibility. Misclassifying this as serde-broken
  permanently blocks a working model. The fix: the error classifier
  (PostToolUseFailure_spawn_quota.py) now distinguishes transient patterns
  ("unknown variant", "expected one of") from serde patterns ("invalid type",
  "missing field", "expected struct"). Transient errors don't get learned as
  serde-broken; the escalation cooldown catches genuinely broken models after
  2+ failures instead of 1.
relations:
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: extends
  - target: wiki/concepts/tool-fallbacks.md
    type: refines
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: related
  - target: wiki/concepts/serde-broken-false-positive-sweep-20260801.md
    type: related
---

# Transient model errors vs serde incompatibility

## Decision context

**The problem:** this session's `/design` writer subagent failed when
MiniMax-M3 returned `finish_reason: "error"` on a specific 37K-token prompt.
Grok Build's deserializer failed with `unknown variant 'error', expected one
of 'stop', 'length', 'tool_calls', 'content_filter', 'function_call'`. I
misclassified this as "M3 is serde-broken" (FM-18) and propagated that
misdiagnosis into the design doc.

The operator caught it: "M3 works fine, you are either trying to call it wrong,
or your interpretation of the error is wrong." M3 had succeeded 7 times in the
same session. The error was a one-off model error on one specific prompt, not a
systemic incompatibility.

**The real root cause:** Grok Build's deserializer types `finish_reason` as a
closed enum (`{stop, length, tool_calls, content_filter, function_call}`). When
any model returns a value outside this set — which is valid per the OpenAI-
compatible API spec — the deserializer fails. This is the same deserializer
weakness as the nemotron null-field serde issue, but at a different layer
(enum variant vs field type).

## The classification distinction

| Error class | Pattern | Example | Root cause | Action |
|---|---|---|---|---|
| **Serde incompatibility** | `invalid type: null, expected u32` | Nemotron returns null for optional fields | Model + transport are structurally incompatible on ALL prompts | Block model from this transport permanently |
| **Transient model error** | `unknown variant 'error', expected one of...` | M3 returns finish_reason: "error" on one prompt | Model errored internally on THIS prompt; works on others | Retry with different prompt; do NOT block |

The critical insight: **serialization error messages that contain "unknown
variant" or "expected one of" indicate enum mismatches, which are transient
(the model chose to return an unexpected value on one call). Serialization
errors containing "invalid type" or "missing field" indicate structural
incompatibilities, which are systemic (the model's response shape doesn't
match the deserializer's expectations on ANY call).**

## The fix

`PostToolUseFailure_spawn_quota.py` now has `TRANSIENT_MODEL_ERROR_PATTERNS`:

```python
TRANSIENT_MODEL_ERROR_PATTERNS = [
    "unknown variant",
    "expected one of",
]
```

These are checked BEFORE `SERDE_BROKEN_PATTERNS` in `is_serde_error()`. If a
serialization error matches a transient pattern, it returns `False` — the model
is not added to `learned-serde-broken.json`.

**False-negative tradeoff (accepted):** these patterns can also match genuine
serde errors that use the same Rust serde phrasing. The escalation cooldown
(30s → 5min → 1h → 24h) means genuinely broken models are still caught after
2+ failures. It's better to under-classify (retry) than over-classify
(permanently block a working model).

## What this means for our workspace

1. **The error classifier is the structural fix** — it prevents false-positive
   serde_broken entries based on error message content, not behavioral rules.

2. **The pattern generalizes** — any model returning an unexpected enum value
   (not just finish_reason) will hit this. Future Grok Build serde improvements
   (wider enums, Option types) would eliminate the root cause, but that's
   outside our control.

3. **The `/design` pipeline survived** — the writer subagent failed on one M3
   spawn, but retrying with parent-inherited model completed the design doc
   successfully. Transient errors are recoverable; systemic ones are not.

## Falsifier

This classification is wrong if:
- A model that returns `unknown variant` errors consistently fails on ALL
  prompts (not just one), meaning it IS systemically incompatible but produces
  enum-mismatch errors instead of field-type errors
- The escalation cooldown doesn't catch genuinely broken models within a
  reasonable timeframe (the 24h max cooldown may be too long for critical-path
  models)
- Grok Build widens its finish_reason enum to include "error", making the
  transient pattern unnecessary

## Receipts

- M3 spawn failure this session: `serialization error: unknown variant 'error', expected one of 'stop', 'length', 'tool_calls', 'content_filter', 'function_call' at line 1 column 76` — 1 failure out of 8 M3 spawns in the same session
- Nemotron serde failure (contrast): `serialization error: invalid type: null, expected u32 at line 1 column 331` — fails on ALL real prompts, passes trivial READY probes
- Hook fix: `PostToolUseFailure_spawn_quota.py` commit `40bce90`, `ef17cf2`, `40a6066`
- Operator correction: "M3 works fine, you are either trying to call it wrong, or your interpretation of the error is wrong"
- [[execution-path-based-model-routing-grok-build]] — documents AGENTS.md context injection overhead per transport
- [[serde-broken-false-positive-sweep-20260801]] — prior false-positive sweep that cleared 12 of 16 models
- [[code-orchestrates-model-judges-skill-scale]] — the principle behind moving error classification into code
- [[replacement-before-investigation-pattern]] — the behavioral pattern this misdiagnosis exemplifies
