---
title: "Iterative cross-model hardening loop"
created: 2026-08-10
source: session-019fe88b
tags: [cross-model-review, hardening, chatgpt, iterative, quality-method, workflow-pattern]
summary: >
  A proven workflow pattern for hardening enforcement/hook mechanisms: implement
  locally → send result to a web-hosted LLM (ChatGPT) → receive targeted critique →
  fix → resend. Each round finds real defects that self-review misses because the
  external model doesn't share the same closure-pressure pathway. Seven rounds
  during the obligation-ledger spike each found a distinct authority gap.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/multi-model-ensemble-design-patterns-for-ai-agent-skills.md
    type: extends
  - target: wiki/concepts/trust-over-believability.md
    type: complements
  - target: wiki/concepts/self-review-before-shipping-advice.md
    type: complements
---

# Iterative cross-model hardening loop

## Decision context

The obligation-ledger spike (2026-08-09) needed to be verified against
adversarial authority attacks. Self-review found some defects but shared
the same pattern-completion pathway that produced the work. The operator
directed using ChatGPT as an external reviewer via `/model-web`.

## The pattern

```
implement locally
    ↓
send result to web LLM (ChatGPT via /model-web)
    ↓
receive targeted critique (specific attacks, not generic feedback)
    ↓
fix identified defect
    ↓
resend result
    ↓
repeat until convergence (critique finds no new defects)
```

## What happened across 7 rounds

| Round | ChatGPT found | Defect class |
|---|---|---|
| 1 | "The receipt doesn't prove the skill ran" | Forgeability |
| 2 | "Multi-artifact ≠ unforgeable" | Trust-level inflation |
| 3 | "The conditional writer is the real gap" | Missing component |
| 4 | "Fix all three before retiring the old gate" | Premature retirement |
| 5 | "Mutation receipts are model-deletable" (root authority attack) | Authority source weakness |
| 6 | "Fix the freshness binding" (INT-001) | Timestamp semantics |
| 7 | "Verify, don't redesign" (closure discipline) | Scope creep prevention |

Each round materially strengthened the mechanism. The key property: the
external model does not share the implementing model's closure pressure.
It reads the report cold and asks "what's wrong with this?" without the
investment in the solution that produced it.

## Why it works better than self-review

Self-review shares the pattern-completion pathway that produced the work.
The assessing faculty has a bias toward confirming what it just built.
An external model reading the result cold has no such investment — it
applies independent judgment without the closure-pressure heuristic.

This is an instance of [[trust-over-believability]] applied iteratively:
the external critique is not more intelligent, but it is more independent.

## How to run it

1. Implement the mechanism or fix
2. Write a structured report (commits, evidence, test results)
3. Send to ChatGPT via `/model-web` using the conversation loop
4. Receive critique — classify each point as CONFIRMED / REJECTED
5. Fix confirmed defects
6. Resend updated report
7. Repeat until the critique finds no new defects (typically 3-7 rounds)

## What this means for our workspace

Any enforcement mechanism, hook system, or authority architecture should
go through at least one cross-model hardening round before retirement of
existing enforcement. The pattern is especially valuable for:
- Hook/gate mechanisms (authority sources are subtle)
- Security boundaries (self-review misses bypass paths)
- State-machine transitions (edge cases compound)

The `/model-web` skill supports this workflow natively — claim a ChatGPT
tab, send the report, receive critique, iterate.

## Falsifier

This pattern is wrong if: (a) self-review consistently finds the same
defects as cross-model review (making the external round redundant), or
(b) the external model's critique is consistently wrong or irrelevant
(making the round wasteful). During the obligation-ledger spike, 7/7
rounds produced actionable, correct findings — but this is one data
point. More sessions are needed to validate the general pattern.

## Receipts

- Session transcript: `~/.grok/sessions/P%3A%5C/019fe88b-af8e-77b2-87cd-04711b7f8257/chat_history.jsonl`
- Commits f9ca5e9 through a955e4b (~/.grok repo) — the 7-round implementation history
- ChatGPT conversation: `chatgpt.com/c/6a779f2a-1aec-83e8-be15-6523fdb0d2c5` (7 review rounds)
- Obligation-ledger commits document each round's defect + fix

## Auto-related

- [[grok-build-workflows-rhai-orchestration]]
- [[skill-catalog]]
- [[open-dynamic-workflow-cross-agent-orchestration]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]

