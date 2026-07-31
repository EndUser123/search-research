---
title: Extend the existing injection mechanism — don't build a parallel one
created: 2026-07-31
source: session-2026-07-31
tags: [chrome-acp, agent-rules, single-source-of-truth, maintenance, anti-pattern]
summary: >
  When a system already has an agent-context injection mechanism (e.g., BROWSER_RULES
  via _meta.rules on all ACP session handlers), adding a parallel bootstrap prompt
  that re-injects the same rules creates two sources of truth that drift. The correct
  response to "the agent needs to know X" is to add X to the existing mechanism, not
  build a new one. This is the extend-don't-duplicate principle applied to agent
  instruction injection.
host: grok
agent: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/chrome-acp-grok-build-setup-implementation.md
    type: observed-in
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: supports
---

## The pattern

Chrome-acp injects agent rules via `_meta: { rules: BROWSER_RULES }` on all three session handlers (`handleNewSession`, `handleLoadSession`, `handleResumeSession` in `server.js`). This is the single injection point for agent-visible operational rules.

When a proposal suggested adding a parallel "operational prompt template" wired into the orchestrator bootstrap, the risk was:

- **Duplicated rules** — the new prompt would re-state security invariants already in BROWSER_RULES
- **Drift** — two sources of truth for the same rules, guaranteed to diverge over time
- **Category errors** — proxy-layer facts (dedup timing, stopReason semantics) framed as agent-actionable instructions, when the agent can't observe or act on them
- **Dispatch chain modification** — adding a new bootstrap path triggers preflight requirements

## The fix

Extend BROWSER_RULES in `server.js` if the agent genuinely needs a new actionable fact. Keep the single `_meta.rules` injection boundary. Everything else (dedup timing, stopReason overload, protocol naming) belongs in operator docs, not agent prompts.

## Generalization

This applies to any system with an existing instruction injection mechanism. Before adding a new injection path:

1. Check whether the existing mechanism already covers the rule (grep the injection source)
2. If yes, don't duplicate — the existing injection is the source of truth
3. If no, add to the existing mechanism rather than creating a parallel one
4. Never inject proxy/transport-layer facts as agent-actionable instructions unless the agent can observe and act on them

## Falsifier

This principle is wrong if the existing injection mechanism is structurally incapable of expressing the needed rule (e.g., it only supports string content but you need structured JSON). In that case, a parallel mechanism is justified — but the burden is on proving the existing mechanism can't be extended.
