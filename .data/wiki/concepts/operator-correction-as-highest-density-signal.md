---
title: "Operator correction as highest-density signal — minimize correction-to-fix latency"
created: 2026-08-01
source: session-019fbf02
tags: ['operator-collaboration', 'signal-density', 'skill-design', 'corrections']
summary: >
  Operator corrections are the highest-density signal in any session — one
  sentence can produce the most valuable output (a permanent skill fix). The
  agent's job is to make corrections structurally permanent as fast as possible.
  The asymmetry: corrections are dense signal; agent work is diffuse noise.
agent: grok
cognitive_load: 2
verification: observed
host: both
relations:
  - target: wiki/concepts/agent-failure-modes-2026.md
    type: extends
  - target: wiki/concepts/exploration-vs-execution-intent-signals.md
    type: complements
  - target: wiki/concepts/aar-always-deep-mode-operator-directive.md
    type: related
---

# Operator correction as highest-density signal

## Decision context

**Why this knowledge was needed:** in session 019fbf02, the operator's single
sentence — "AAR is always supposed to be D, there's not supposed to be any
other choice" — produced the session's most valuable output: a permanent skill
fix that eliminates a recurring friction point. The agent's prior work (the AAR
report itself) was valuable but diffuse; the correction was laser-focused.

## Key findings

### The signal asymmetry

Operator corrections carry more decision-weight per token than any other
session input. A correction:
1. Identifies a specific behavioral gap
2. Names the desired state
3. Implies the correction should be permanent (not just for this session)

Agent work, by contrast, is diffuse — many tool calls, many files, many
decisions, most of which are correct but none of which carry the same
decision-density.

### The correction-to-fix-latency metric

The value of a correction decays with time-to-permanent-fix. If the agent:
- Hears the correction
- Understands it
- Implements a permanent fix (skill edit, AGENTS.md rule, config change)
- Commits it

...all within the same turn, the correction's value is fully captured. If the
fix is deferred to a handoff, value decays — the handoff may not be picked up,
the correction's urgency may be lost, or the fix may be implemented differently.

### When this pattern fires

- Operator says "X should always be Y" → permanent config/skill fix
- Operator says "stop doing X" → AGENTS.md rule or skill edit
- Operator says "why did you do X?" → behavioral pattern to investigate
- Operator says "I thought we had made X more readable" → prior fix didn't stick

## What this means for our workspace

The system should prioritize correction-to-fix latency:
1. **Hear it fast** — the agent should detect corrections immediately (already
   detected by friction scanners)
2. **Understand it fast** — classify the correction type (behavioral, config,
   skill)
3. **Fix it fast** — apply the minimal sufficient intervention (AGENTS.md rule
   > skill edit > new skill > hook > config per AGENTS.md §10)
4. **Make it permanent** — commit in the same turn

The `/tp do?` acceptance trigger (`0 - Proceed with All`) is a related pattern:
it minimizes the latency between the operator seeing recommendations and the
agent executing them.

## Falsifier

If operator corrections consistently produce low-value fixes (the correction
was about a one-off issue, not a pattern), this finding overstates the
signal-density of corrections. Monitor: do corrections that become permanent
fixes recur as "should have done this earlier" in future AARs?

## Receipts

- Session 019fbf02: operator correction "AAR is always supposed to be D" →
  permanent fix in commit `f0979f1` within the same turn
- [[agent-failure-modes-2026]] — "Ugly wish-granting" refinement documents the
  inverse: agent failing to understand operator intent
- [[exploration-vs-execution-intent-signals]] — operator intent detection as
  the upstream mechanism
- [[friction-detection-operator-pushback-as-trigger]] — corrections as friction
  signals that trigger skill improvements
- [[replacement-before-investigation-pattern]] — the anti-pattern: replacing
  a system without investigating why the correction was needed

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[user-modeling-for-agentic-clis]]
- [[scope-matching-verification-discipline]]
- [[recurring-thinking-errors]]
- [[operator-explicit-simple-execution-vs-agent-optimization]]

