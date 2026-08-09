---
title: "Obligation enforcement vs justification detection — the root-cause fix for semantic-gate false positives"
created: 2026-08-09
source: session-2026-08-09 (/www research on equivalence-bypass-gate false-positive root cause)
tags: [enforcement, lexical-vs-semantic, obligation-vs-justification, control-plane, stop-hooks, false-positive, regex-authority, structural-enforcement, receipt-governed-execution, neurosymbolic]
summary: >
  The root cause of semantic Stop-hook false positives (a gate firing on
  discussion of itself) is not regex imprecision — it is architectural.
  The gate detects the JUSTIFICATION for violating an obligation ("inline
  is sufficient") rather than checking the OBLIGATION itself (was the
  required action executed?). The justification language is present in
  both "discussing the bypass" and "committing the bypass," making them
  indistinguishable by any prose-scanning mechanism. The fix: enforce the
  obligation via authoritative state (required-actions + execution receipts),
  not the justification via regex. Converges with three external sources:
  AWS neurosymbolic guardrails (BeforeToolCallEvent enforces rules, not prose),
  hexisteme AND-gate ("words plus the tool trail are not ambiguous"), and
  the existing wiki [[lexical-vs-semantic-verification-gap]] ("gates that
  fire correctly on the wrong thing").
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - P:/.data/wiki/concepts/lexical-vs-semantic-verification-gap.md (the workspace's existing framework for this failure class)
  - https://dev.to/aws/ai-agent-guardrails-rules-that-llms-cannot-bypass-596d (AWS neurosymbolic guardrails: BeforeToolCallEvent enforces symbolic rules before tool execution; 3/3 invalid operations blocked with zero FP)
  - https://dev.to/hexisteme/the-you-decide-reflex-blocking-ai-agent-decision-punting-with-a-stop-hook-1jbk (AND-gate: text signal + tool trail; "the identical sentence can be a punt or a legitimate question, and the only reliable tell is whether the agent had the data to answer it itself")
  - https://exesketch.com/blog/ai-agent-enforcement-gate-vs-receipt (gate vs receipt distinction: "a gate checks before the action; a receipt logs after")
  - https://www.linkedin.com/pulse/receipt-governed-execution-contract-mark-pippins-muyje (agentic execution receipt contract)
  - https://github.com/ota-run/ota/blob/main/docs/spec/execution-receipt.md (ota.run execution receipt spec: deterministic, machine-readable record)
relations:
  - target: wiki/concepts/lexical-vs-semantic-verification-gap.md
    type: extends — that concept names the general failure (gate fires on wrong layer); this concept names the specific root cause for semantic Stop hooks and the structural fix
  - target: wiki/concepts/agent-control-plane-enforcement-architectures-2026.md
    type: applies — that research identified the five-layer control plane; this concept identifies which layer (pre-execution policy + lifecycle state machine) solves the equivalence-bypass problem
  - target: wiki/concepts/narrative-as-signal-anti-dismissal-rule.md
    type: complements — narrative-as-signal covers the model-side failure (plausible story as evidence); this covers the system-side fix (enforce state, not story)
  - target: wiki/concepts/close-lighter-equivalent-loophole.md
    type: refines — that concept documented the equivalence-bypass pattern behaviorally; this concept identifies the architectural fix
---

# Obligation enforcement vs justification detection

## The failure

The equivalence-bypass Stop hook fired on a report discussing the gate itself. Three rounds of regex tuning could not prevent this. The root cause is not lexical — it is architectural.

## The three root causes

### 1. Detecting the justification instead of the obligation

The gate detects "lighter is sufficient" (the JUSTIFICATION for skipping a skill) rather than "skill was required but not executed" (the OBLIGATION). The justification language appears in both legitimate discussion and actual bypass, making them indistinguishable by prose scanning.

**Fix:** enforce the obligation. Check whether the required skill has an execution receipt (authoritative state), not whether the prose contains equivalence language.

**External convergence:** AWS neurosymbolic guardrails (Strands `BeforeToolCallEvent`) enforce symbolic rules (`payment_verified == True`) before tool execution — not whether the model's prose claims payment was verified. Result: 3/3 invalid operations blocked, zero false positives. The rule is code, not regex.

### 2. No authoritative requiredness state

Nothing in the system declares "/review is required for this work" in machine-readable state. Requiredness lives only in AGENTS.md prose. The gate cannot check obligation because the obligation is not represented as state.

**Fix:** write required actions to session-scoped state at work-start. The completion hook reads state and checks execution receipts.

**External convergence:** the exesketch article names the gate-vs-receipt distinction directly: "a gate checks before the action; a receipt logs after. They look similar in a diagram. In practice, they're opposite things."

### 3. Fail-open with no observability

The gate is permit-by-default; every uncertain path exits silently. False positives and false negatives are both invisible.

**Fix:** emit a counter recording which exit path fired. The hexisteme/fromzerotoship thread reaches: "a permit-by-default gate cannot fail loudly — every uncertain path collapses to the same silence. Visibility has to be emitted."

## The discriminating principle

For any enforcement mechanism, ask:

> "Does this gate check the STATE TRANSITION / OBLIGATION, or does it check the PROSE EXPLANATION for violating it?"

- If it checks state → structural enforcement. Correct authority level for deterministic gates.
- If it checks prose → semantic enforcement. Fundamentally limited: the identical text can be discussion or action, and no regex can reliably distinguish them.

The equivalence-bypass gate, psychological-narrative gate, narrative-sufficiency gate, and confabulation gate all check prose. The decision-contract, reviewer-classification, and revision-invalidation gates check structured artifacts. The former are architecturally fragile; the latter are sound.

## The design principle (from the hexisteme AND-gate)

> "Words alone are ambiguous; words plus the tool trail are not."

For Stop hooks: pair a cheap text signal with a behavioral/state signal. Block only when BOTH fire:
- Text signal: the agent said something suggesting the governed behavior
- State signal: the governed behavior's prerequisite is unmet (no execution receipt, no waiver)

The state signal is the disambiguator. It converts a probabilistic text match into a deterministic violation. And it cannot be fabricated by the same model being constrained — execution receipts are written by the runtime, not by prose.

## What this means for the equivalence-bypass gate

Replace prose-semantic enforcement with structural obligation enforcement:
1. /go writes required_actions to session-scoped state at work-start
2. The verification-receipt system records tool/skill execution
3. A completion hook checks: for each required action, does a receipt exist?
4. No receipt and no waiver → BLOCK (deterministic, no prose analysis)
5. Receipt or waiver exists → PASS (regardless of prose content)

This eliminates false positives on meta-discussion (the gate checks state, not prose), eliminates self-exemption (receipts are runtime-written), and catches novel euphemisms (the obligation is checked, not the words).
