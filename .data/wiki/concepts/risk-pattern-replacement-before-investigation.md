---
title: "Risk pattern: replacement before investigation"
created: 2026-08-06
source: sessions-20260726-through-20260801
tags: [risk-pattern, premature-recommendation, replacement, investigation]
summary: >
  Recommending that a tool/service/skill be replaced before enumerating
  what was tried with the current tool, what workarounds exist, and whether
  the failure was verified on our workload. The fix is a 3-point
  investigation gate before any replacement recommendation.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/agent-failure-modes-2026.md
    type: extends
---

# Risk pattern: replacement before investigation

## Pattern

When an external component (CLI, API, subprocess, hook) doesn't behave as expected, the agent recommends replacing it with an alternative before investigating: (1) what was actually tried with the current tool, (2) what workarounds exist in docs/issues, (3) whether the failure was verified on our actual workload vs a different context.

## Evidence

- **13+ handoffs across 2026-07-26 through 2026-08-01** exhibit this pattern.
- **Session 2026-07-26:** recommended replacing a search MCP server without evaluating alternatives (extend existing script, different transport, gateway).
- **Session 2026-08-01:** recommended replacing a caller's threading model to work around an undiagnosed callee failure. The root cause was a config mismatch in the callee, discoverable in seconds with an isolated test.

## What this means for our workspace

1. Before recommending replacement, enumerate: (a) specific flags/parameters tried, (b) workarounds from docs/issues/`tool-fallbacks`, (c) whether the failure was reproduced in isolation.
2. Applies to restructuring callers too — reproduce the callee failure in isolation before changing the orchestration layer.
3. Label any replacement recommendation that skips the gate as `[PREMATURE]`.

## Falsifier

If the investigation gate produces no additional information beyond the initial failure observation (all workarounds were already tried, docs have nothing), the gate is unnecessary overhead. In practice, the gate catches real misses >80% of the time.

## Related concepts

- [[agent-failure-modes-2026]] — premature optimization and replacement-before-investigation as documented failure modes
- [[narrative-as-signal]] — the narrative "it doesn't work" without investigation is a signal to read docs
- [[inference-chains-bare-numbers-destructive-write]] — inference chains lead to premature conclusions

## Receipts

- AGENTS.md § "Replacement-before-investigation"
- Wiki concept: `replacement-before-investigation-pattern` (referenced in AGENTS.md)
- 13+ handoffs: documented in AGENTS.md reference
