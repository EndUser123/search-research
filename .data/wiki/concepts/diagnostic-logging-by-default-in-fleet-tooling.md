---
title: "Diagnostic logging by default in fleet tooling — summary outputs must classify failures, not just count them"
date: 2026-08-11
tags: [diagnostic-logging, fleet-tooling, pool-test, promote-models, root-cause, troubleshooting, infrastructure-vs-quality]
provenance:
  source: session 019fdf47
  trigger: "operator asked 'do we need better logging?' after 15+ min troubleshooting chain (PI binary WinError 2, timeout too short, provider name mismatch)"
  verified: 2026-08-11
---

# Diagnostic logging by default in fleet tooling

## The problem

Fleet benchmark and selection tools produce summary outputs that report **what** happened (pass/fail counts, quality scores) but not **why** (infrastructure failure vs model-quality failure). When running 24 models × 18 problems = 432 test cases, the summary is the only practical view — but it's blind to failure modes.

This session had three incidents where diagnostic-poor summaries caused 15+ minutes of unnecessary troubleshooting:

1. **PI binary WinError 2** — all 71 models scored 0/18 via PI. The summary showed "0/18 0.00 NO" for every model. Root cause was a missing binary path (infrastructure), not model quality. Took 3 tool calls to diagnose because the summary didn't classify the failure.

2. **Timeout too short** — PI method tests timed out at 300s. The summary showed "FAIL (pi timeout)" with no elapsed time. Took source-code reading to discover the timeout value and correlate with log timing.

3. **Provider name mismatch** — `promote_models.py` silently matched 0 evidence records for ZAI models. The summary showed "no evidence" with no explanation. Took tracing through 3 files to find the `z.ai` vs `zai` mismatch.

## The principle

**Every tool that aggregates multiple operations must classify failure modes in its summary output, not just count them.**

A summary that says "12/18 passed, 6 failed" is insufficient. It must say "12/18 passed, 6 failed: 4× infra:timeout, 2× quality:wrong_logic." The classification enables immediate triage: infrastructure failures are fixable by the operator (increase timeout, fix binary path, wait for quota); quality failures require different action (exclude model, adjust threshold, improve prompt).

## Required diagnostic patterns

### 1. Failure mode breakdown in summaries

Any tool that runs N operations and reports a summary must include a failure-mode breakdown:

```
SUMMARY: 24 models tested for reasoning
  gemma-4-31b-it             8/8  1.00  YES
  nemotron-3-super-120b      8/8  1.00  YES
  minimax-m3                 1/8  0.12   NO  [7× infra:rate_limited]
  nemotron-mini-4b           4/8  0.50   NO  [4× quality:wrong_answer]
```

The bracketed failure breakdown is the diagnostic layer. Without it, the operator can't distinguish "model can't reason" from "provider throttled us."

### 2. Elapsed time on timeout errors

Timeout errors must include the timeout value and elapsed time:

```
FAIL (pi timeout after 300s)      ← good
FAIL (pi timeout)                  ← bad — was it 5s or 300s?
```

This enables immediate diagnosis: if every timeout is exactly at the timeout boundary, the timeout is too short. If timeouts vary, the model is genuinely slow.

### 3. Match diagnostics in identity-matching tools

Tools that match records by identity (model name, provider, lane) must report WHY matches fail, not just that they failed:

```
zai-glm-4-7: 0/2922 matched (provider mismatch: registry=zai vs telemetry=z.ai)
```

vs:

```
zai-glm-4-7: no evidence
```

The first version tells the operator the fix (normalize provider name). The second version sends them on a 3-file trace.

## Implementation

The patterns are implemented in:

- `pool_test.py` — failure mode breakdown in both single-model and multi-model summaries
- `pool_test.py` — elapsed time in timeout error messages
- `promote_models.py --verbose` — identity match diagnostics with provider mismatch detection

## Durable rule

When building or modifying any fleet tool that aggregates operations:

1. **Classify, don't just count.** Every failure in a summary must carry a failure class (`infra:*` or `quality:*`).
2. **Include the parameter that caused the failure.** Timeout errors show the timeout value. Rate-limit errors show the status code. Binary-not-found errors show the binary name.
3. **When a match fails, show what was compared.** Identity mismatches show both sides. Path mismatches show both paths.

This is the same principle as [[claims-require-receipts]] applied to tool output: the summary IS the receipt for the batch run. A summary without failure classification is a claim without a receipt — it states what happened but provides no evidence for why.
