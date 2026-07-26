---
title: "Rule-not-fired vs rule-doesn't-exist: the process-improvement meta-pattern"
created: 2026-07-21
source: session-2026-07-21
tags: [process, meta-pattern, rule-enforcement, architectural-decisions, trigger, skill-gating, alternatives-gate, agent-failure]
summary: >
  When a rule exists but doesn't fire, adding another rule doesn't help — the
  fix is a trigger or gate, not a new rule. Worked example: the agent had a rule
  requiring ≥2 alternatives for hard-to-reverse decisions, but built an MCP server
  from the user's suggestion without evaluating alternatives. The rule didn't fire
  because nothing structural forced it. The fix: an `architectural` profile in /go
  that gates implementation behind an alternatives block, plus an AGENTS.md hard
  rule with a named trigger. The meta-lesson: process failures on this host are
  overwhelmingly trigger failures, not knowledge gaps.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
relations:
  - target: wiki/concepts/agent-oversight-rubber-stamping
    type: related
  - target: wiki/concepts/llm-judgment-hooks
    type: related
  - target: wiki/concepts/grok-build-stop-hook-agent-text
    type: related
---

# Rule-not-fired vs rule-doesn't-exist

## The meta-pattern

Two distinct failure classes for behavioral rules in agent systems:

| Failure class | Symptom | Wrong fix | Right fix |
|---------------|---------|-----------|-----------|
| **Rule doesn't exist** | Agent doesn't know the rule | N/A | Write the rule |
| **Rule exists but doesn't fire** | Agent knows the rule but skips it under context pressure or user-direction | Write another rule (doesn't help — same attention failure) | Add a **trigger** or **gate** that forces the rule structurally |

**This session's observation:** the overwhelming majority of process failures on this host are **rule-not-fired**, not rule-doesn't-exist. The rules exist in AGENTS.md, CLAUDE.md, skill files. What fails is the trigger — nothing structural forces the agent to apply the rule at the right moment.

## The worked example (2026-07-21)

### What happened

The operator suggested "build a Search MCP server." The agent built it. The operator later asked `/tp`: "I feel like my suggestion was adopted but I don't know that it is optimal."

### What the rule said

`~/.grok/AGENTS.md` § Recommendations (line 384):
> "When the decision is hard to reverse, name ≥2 viable options plus the selection criterion."

The MCP server decision was hard to reverse (new architecture, config wiring, dispatch chain). The rule required alternatives evaluation. The rule didn't fire.

### Why it didn't fire

The rule is **advisory text in a large document**. The agent reads AGENTS.md at session start, carries a compressed version in context, and applies rules when it remembers to. Under three conditions, the rule gets skipped:

1. **User-direction pressure:** the user said "build X" → the agent treats this as authorization to build, not as a prompt requiring alternatives evaluation
2. **Context compression:** after compaction, specific rules degrade to general impressions
3. **No structural gate:** nothing prevents the `spawn_subagent` or `write` call until the alternatives block is emitted

### The fix (three layers, lightest to heaviest)

| Layer | Mechanism | Status (2026-07-21) | Reliability |
|-------|-----------|---------------------|-------------|
| **Skill gating** | `/go` `architectural` profile routes architectural work through an alternatives gate before implementation | ✅ Implemented | ~60-70% — depends on model attention |
| **Rule reinforcement** | AGENTS.md hard rule with named trigger and incident reference | ✅ Implemented | Same attention dependency |
| **Hook enforcement** | Stop hook reads chat_history.jsonl, detects architectural writes without alternatives block | Documented, not built | ~80-85% if built |

## The meta-lesson (why this is a wiki concept, not just a bug fix)

The pattern generalizes beyond this incident:

- **"The agent should verify before claiming done"** → rule exists (AGENTS.md edit-then-verify). Failure: agent skips verification under time pressure. Fix: not another rule; a hook.
- **"The agent should search before proposing"** → rule exists (AGENTS.md preflight). Failure: agent proposes without searching. Fix: not another rule; a gate in `/go` Step 0.
- **"The agent should not fabricate causal claims"** → rule exists (receipt rule). Failure: agent states causation without receipt. Fix: not another rule; a Stop hook with LLM judge.

**The repeated structure:** rule exists → rule doesn't fire → someone proposes adding another rule → the new rule also doesn't fire. The loop breaks only when a **structural trigger** (gate, hook, enforced checkpoint) replaces the **advisory text**.

## Diagnostic: how to tell which failure class you're in

| Question | If yes → rule-doesn't-exist | If yes → rule-not-fired |
|----------|---------------------------|------------------------|
| Is the rule written in AGENTS.md / CLAUDE.md / skill? | No → write it | Yes → next question |
| Did the agent cite or acknowledge the rule at any point in the session? | No | Yes, but didn't apply it |
| Would adding the same rule in different words fix it? | Maybe | No — same attention failure |
| Would a structural trigger (gate/hook) fix it? | Not needed | Yes |

## When NOT to add a trigger

Not every rule-not-fired warrants structural enforcement. The cost/benefit:

| Factor | Add trigger | Don't add trigger |
|--------|-------------|-------------------|
| Reversibility of the work the rule protects | ≥1.75 (hard to reverse) | ≤1.25 (trivial) |
| Frequency of the failure | Recurring across sessions | One-off |
| Cost of the trigger | Low (skill gate) or medium (hook) | High (complex hook with LLM judge on every turn) |
| Blast radius if the rule is skipped | Large (architectural, identity, data) | Small (formatting, style) |

## Relationship to existing concepts

- **Related** [[agent-oversight-rubber-stamping]] — covers the operator rubber-stamping agent output. This concept covers the inverse: the agent rubber-stamping the operator's suggestion. Same failure shape (approval without evaluation), different direction.
- **Related** [[llm-judgment-hooks]] — the heaviest enforcement layer for rule-not-fired. Two-layer regex+LLM pattern for when skill gating is insufficient.
- **Related** [[grok-build-stop-hook-agent-text]] — the technical enabler for hook-based enforcement on Grok Build (chat_history.jsonl workaround).

## Sources

- Session 2026-07-21: `/tp` critique (fresh subagent, 16 tool calls) identified the rule-not-fired pattern as the root cause of the alternatives-skip
- `~/.grok/AGENTS.md` § Recommendations (line 384): the rule that didn't fire
- `~/.grok/skills/go/SKILL.md` § `architectural` profile: the structural fix (skill gating)
- `~/.grok/AGENTS.md` § "Alternatives before architectural implementation": the reinforced rule

## Falsifier

This concept is wrong if:
- Adding triggers/gates does NOT improve rule adherence (the failure is something else — e.g., the rule itself is wrong, not unfired)
- The majority of process failures turn out to be rule-doesn't-exist after deeper analysis (this session's sample was N=1)
- Skill gating proves as unreliable as advisory text (both depend on model attention)

If any pattern appears within 3 months, revise or retire.

## Auto-related

- [[examples-over-rules-escape-hatch]]
- [[operator-collaboration-style-and-leverage]]

