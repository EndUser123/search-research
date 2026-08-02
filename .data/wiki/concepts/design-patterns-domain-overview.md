---
title: "Design Patterns Domain Overview"
created: 2026-08-02
source: session-2026-08-02
tags: [design-pattern, domain-overview, reference, index]
summary: >
  Index of 9 wiki concepts tagged 'design-pattern'. These span enforcement
  mechanisms, trigger coupling, verification gaps, instruction-state closure,
  plan-then-execute, skill screening, and critical-friend protocols.
agent: grok
host: both
cognitive_load: 1
verification: observed
confidence: 0.9
last_verified: 2026-08-02
half_life_days: 180
relations:
  - target: wiki/concepts/couple-triggers-to-events-that-actually-fire.md
    type: related
  - target: wiki/concepts/forgetting-not-rejecting-distinguish-non-use-from-disapproval.md
    type: related
---

# Design Patterns Domain Overview

This is a domain index, not a research concept. It groups the 9 wiki concepts tagged `design-pattern` by theme for navigability.

## Enforcement & Verification

- [[best-practices-enforcement-mechanism-grok-build]] — how enforcement mechanisms work on Grok Build (hooks, Stop gates, validators)
- [[external-state-cross-check-as-structural-fix]] — cross-checking external state as a structural fix for inference-without-verification
- [[instruction-to-state-closure-gap-obligation-ledger]] — desired-state tracking and obligation ledgers for instruction→implementation closure

## Trigger Coupling & Lifecycle

- [[couple-triggers-to-events-that-actually-fire]] — couple features to events that actually fire, not commands the operator never invokes
- [[forgetting-not-rejecting-distinguish-non-use-from-disapproval]] — forgetting ≠ rejecting: distinguish non-use from disapproval when removing features

## Skill & Agent Patterns

- [[skill-quick-fit-screening-pattern]] — 30-second triage before skill execution to avoid poor-fit invocations
- [[tool-use-protocol-subagent-critical-friend]] — tool use protocol for subagent critical-friend critiques
- [[plan-then-execute-pattern]] — plan-then-execute and other LLM agent design patterns (Beurer-Kellner et al., 2025)

## UI & Ecosystem

- [[textual-layout-widgets-ecosystem]] — Textual layout, widget catalog, and ecosystem design patterns

## Falsifier

This overview is wrong if the design-pattern tag is applied inconsistently or if concepts are miscategorized. Review periodically during `/wiki lint`.

## What this means for our workspace

This index makes the 9 design-pattern concepts navigable as a group. When designing a new feature or pattern, check this index first to avoid reinventing what's already documented.

## Receipts

- **9 concepts tagged design-pattern:** [FACT] verified by scanning all wiki concepts with PowerShell `Get-ChildItem` + regex match on `tags:.*design-pattern`. Result: 9 matches, listed above.
- **Categorization:** [INFERENCE] — the thematic grouping (enforcement, trigger coupling, skill patterns, UI) is my interpretation, not mechanically derived.
