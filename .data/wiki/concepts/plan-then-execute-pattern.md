---
title: "Plan-Then-Execute and Other LLM Agent Design Patterns (Beurer-Kellner et al., 2025)"
created: 2026-07-20
source: session-2026-07-20
tags: ['design-patterns', 'llm-agents', 'security', 'prompt-injection', 'host-agnostic', 'beurer-kellner']
summary: >
  Academic design patterns for LLM agent security and reliability. Plan-Then-
  Execute fixes the plan before any tool exposure so tool outputs cannot
  redirect action selection. Action-Selector, Map-Reduce, Dual-LLM, Code-Then-
  Execute, Context-Minimization are the other five patterns. Common principle:
  constrain the agent's action surface to make prompt injection unable to
  trigger consequential actions.
agent: grok
cognitive_load: 3
verification: multi-source-verified
host: grok
---

## Summary

Beurer-Kellner et al.'s 2025 paper "Design Patterns for Securing LLM Agents against Prompt Injections" (11 authors from IBM, Invariant Labs, ETH Zurich, Google, Microsoft) proposes six design patterns that constrain agent action surfaces to limit what prompt injection can trigger. The patterns share one principle: **once an agent has ingested untrusted input, that input must be constrained so it cannot trigger consequential actions.** This is host-agnostic — applies to any LLM agent architecture.

## Key Findings

### The patterns

| Pattern | Mechanism | What it prevents |
|---|---|---|
| **Action-Selector** | Agents trigger tools but cannot be exposed to or act on tool responses. Modelled as "LLM-modulated switch statement." | Tool-output poisoning changing future actions |
| **Plan-Then-Execute** | Plans all tool calls before any chance of exposure to untrusted content; tool output can corrupt content but not action selection. | Mid-stream injection redirecting subsequent actions |
| **LLM Map-Reduce** | Sub-agents exposed to untrusted content return booleans/symbolic values; results aggregated safely later. | Sub-agent output poisoning the orchestrator |
| **Dual-LLM** | Privileged LLM coordinates a quarantined LLM; quarantined returns symbolic variables only; privileged decides what to show user. | Same as Map-Reduce but for tool-rich agents |
| **Code-Then-Execute** | Privileged LLM generates code in a sandboxed DSL with full data-flow analysis; tainted data tagged and tracked through entire process. | Same as Dual-LLM but with structural enforcement |
| **Context-Minimization** | Remove unnecessary content from context over multiple interactions; user prompt converted to DB query, user prompt removed before returning results. | User-prompt injection sneaking through query results |

### Common principle

> "Once an LLM agent has ingested untrusted input, it must be constrained so that it is impossible for that input to trigger any consequential actions — that is, actions with negative side effects on the system or its environment."

The patterns differ in how aggressively they constrain; they trade off utility vs security. Plan-Then-Execute is the most permissive; Action-Selector is the strictest.

### Why this matters for plan-mode workflows

Grok Build's `/plan` workflow has elements of Plan-Then-Execute (file edits are blocked during planning) but the implementation is leaky: subagents start with fresh `Inactive` plan-mode trackers and inherit parent's permission mode (including `bypassPermissions`); bash commands aren't inspected for file writes. See `wiki/concepts/grok-build-plan-mode-structured-thinking` for the host-specific surface.

### Operator corollary

When designing any agent system, ask: **can a tool response change which tool gets called next?** If yes, the system is not Plan-Then-Execute. The fix isn't better prompting — it's structural separation between planning and execution phases.

## Related

- [[agent-oversight-rubber-stamping]] — oversight without structure also fails to catch prompt-injection effects
- [[grok-build-plan-mode-structured-thinking]] — Grok Build's plan-mode is a leaky Plan-Then-Execute
- [[agent-failure-modes-2026]] — `summary-only-handoff-loss` and `async-reconciliation-failure` are the failure modes these patterns prevent

## Auto-related

<!-- auto-managed by wiki_after_write.py -->

## Sources

- session-2026-07-20 — Beurer-Kellner, Buesser, Cretu, Debenedetti, Dobos, Fabian, Fischer, Froelicher, Grosse, Naeff, Ozoani, Paverd, Tramèr, Volhejn. "Design Patterns for Securing LLM Agents against Prompt Injections." arxiv.org/abs/2506.08837 (2025-06-10)
- session-2026-07-20 — Simon Willison's annotated summary of the paper (simonwillison.net, 2025-06-13)
