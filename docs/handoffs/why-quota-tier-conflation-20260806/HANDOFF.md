---
title: "/why --persist: quota-tier conflation — characterization claims need receipts"
created: 2026-08-06
session: 019fc303
status: OPEN
assignee: grok
---

# /why investigation: quota-tier conflation

## investigation_state:

```yaml
question: "Why did the agent conclude 'no metered quota exists' for Grok Build?"
root_cause: "Training-prior indistinguishability + receipt-rule scope gap — agent answered from training data about xAI's public API tier model without verifying Grok Build's consumer weekly pool"
confidence_tier: 2
hypotheses:
  - id: H1
    cause: "Training-prior indistinguishability"
    likelihood: HIGH
    test: "Would the agent run /usage if told 'this is a characterization claim'?"
    outcome: confirmed — no verification command was run before the claim
  - id: H2
    cause: "Receipt-rule scope gap — rule covers causal/failure claims, not characterization claims"
    likelihood: HIGH
    test: "Search AGENTS.md for 'characterization' in the receipt rule"
    outcome: confirmed — absent from the rule
  - id: H3
    cause: "Closure pressure specific to quota"
    likelihood: MEDIUM
    test: "Did the agent investigate at all, or immediately assert?"
    outcome: immediately asserted (from wiki concept)
pattern_match: "[[asserting-runtime-behavior-from-memory-not-testing]] + [[grok-build-grpc-web-billing-endpoint]]"
accurate_as_of_head: 9ef1fa5
```

## Problem

The agent concluded "no metered quota exists" for Grok Build, conflating the public xAI API tier model (rate-limit-based, no metered pool) with Grok Build's consumer subscription (weekly metered credit pool). This blocked quota dashboard work until the operator corrected it.

## Root cause

Genuine multi-causality — two independently necessary causes:

1. **Training-prior indistinguishability:** the agent answered from training data about xAI's public API without running any verification command (`/usage`, `/model-quota`). The training-prior knowledge felt identical to verified knowledge.

2. **Receipt-rule scope gap:** the receipt rule in AGENTS.md covers causal/failure claims ("why X failed") but not characterization claims ("what X is," "how X works"). Characterization claims feel safe — they're "just facts" — so they don't trigger the receipt gate.

## Recommended fix (not yet implemented)

Extend the receipt rule in `~/.grok/AGENTS.md` to explicitly cover characterization claims:

> Characterization claims — "X uses Y quota model," "X supports Z feature," "X works by W mechanism" — require the same receipts as causal claims. If you haven't run the verification command this session, label [INFERENCE].

Add "quota model" to the domain examples alongside runtime/platform/library behavior.

## Falsifier

If the agent runs `/usage` or `/model-quota` before making any claim about Grok Build's quota model, the conflation cannot occur — the command output shows the weekly pool directly (`credit_usage_percent` + reset timestamp from the gRPC-web endpoint).

## Wiki concepts that already capture this

- `[[grok-build-grpc-web-billing-endpoint]]` — the specific incident + gRPC-web endpoint
- `[[asserting-runtime-behavior-from-memory-not-testing]]` — the general pattern (asserting untested runtime/platform behavior as fact)

## Source files for staleness checking

- `C:/Users/brsth/.grok/AGENTS.md` (receipt rule, ~line 700)
- `P:/.data/wiki/concepts/grok-build-grpc-web-billing-endpoint.md`
- `P:/.data/wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md`
