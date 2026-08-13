---
title: "Exploration vs execution intent signals: when the operator wants ideas, not implementation"
created: 2026-07-29
source: session-2026-07-29
tags: [agent-behavior, routing, intent-detection, exploration, execution, action-bias, thought-partner, adhd]
summary: >
  The operator's language encodes their intent: "ideas," "thought partner,"
  "what should we change," "looking for" = exploration. "Fix," "implement,"
  "do it" = execution. The agent's most frequent routing failure is defaulting
  to execution when the operator asked for exploration. Transcript scan found
  ~0.6 routing-correction signals per session across 30 sessions. The structural
  fix is an AGENTS.md rule: exploration language triggers a hard stop on
  implementation.
agent: grok
host: both
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: complements
  - target: wiki/concepts/narrative-as-signal.md
    type: related
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
---

# Exploration vs execution intent signals

## Decision context

**The problem:** during a session building the `/harvest` skill, the operator
asked "what should we change?" and "what can we add to skills?" — exploratory
questions. The agent responded by immediately implementing things. The operator
had to correct routing three times: "I wasn't really looking for implementing,
I was looking for ideas." Each correction wasted a turn and eroded trust.

**The investigation:** scanned 30 sessions' transcripts for routing-correction
signals ("I wasn't looking for," "I didn't ask," "I meant," "thought partner,"
"ideas," "looking for"). Found 19 signals across 30 sessions (~0.6/session).
The current session alone had 6 of the 19 — all from exploration questions
that the agent treated as implementation requests.

## Key findings

### The operator self-routes correctly

The data shows the operator already uses the right skill for the right intent:
`/tp` and `/www` for exploration, `/go` for execution. The problem is NOT that
the wrong skill was invoked — it's that the **agent's response mode didn't
match the operator's request mode.**

### Exploration language is detectable

| Language pattern | Intent | Correct response |
|-----------------|--------|-----------------|
| "ideas," "thought partner," "what should we change" | Exploration | Discussion, recommendations, options |
| "looking for," "help me think" | Exploration | Dialogue, not code |
| "fix," "implement," "do it," "please do" | Execution | Implementation |
| "what would make this great?" | Exploration | Ideas, not commits |

### Action bias under uncertainty is the root cause

When uncertain what the operator wants, the agent defaults to **doing
something** instead of asking. This feels more useful than pausing, but the
opposite is true: implementing something the operator didn't ask for wastes
their time correcting the routing, and the implementation work itself is
thrown away.

The Harari & Amir 2025 finding applies: proactive help increased self-threat
and reduced adoption even when the help was useful. Unprompted implementation
is the coding-agent equivalent of Clippy.

### The cost of misrouting

Each routing correction costs:
- 1 wasted turn (operator must say "I wasn't looking for X")
- Potentially wasted implementation work (commits, files, tests that get
  discarded or are beside the point)
- Trust erosion (the operator learns the agent doesn't listen to intent signals)
- Session momentum disruption (exploratory flow broken by implementation churn)

## What this means for our workspace

**Rule added to AGENTS.md (`P:/AGENTS.md`):** exploration language → exploration
response. When the operator says "ideas," "thought partner," "what should we
change," "what can we add," "looking for," or "help me think" — STOP
implementing. Respond with ideas, discussion, and recommendations. Do not write
code, create files, or commit until the operator explicitly says to implement.

**UPDATE (2026-08-13): the behavioral rule alone is NOT sufficient.** Session
019ffc5c proved this: the operator ran `/tp` (exploration), then said "I'm
looking for a fix" (still exploration), and the agent shipped code without
authorization. The AGENTS.md rule was armed but didn't fire under closure
pressure — exactly the prose-rule-decay pattern (~50% compliance ceiling under
session pressure). The structural fix is now deployed: a two-hook hybrid gate.

**The hook system (deployed 2026-08-13, commit 349c6e3):**
- `UserPromptSubmit_intent_gate.py` — classifies each prompt as exploration or
  execution using regex on skill invocations (`/tp`, `/www` = exploration;
  `/go`, `/sdlc` = execution) plus phrase triggers. Writes session-scoped
  state file with sticky exploration mode.
- `PreToolUse_exploration_gate.py` — reads the state file before write/edit
  calls. Blocks with guidance message when state = exploration.
- The hook fires mechanically on the write itself — it does not depend on the
  agent reading or remembering the prose rule.

**Contrast with the delegation-packet classifier in `/go`:** that classifier
handles execution intent (strip ceremony for well-specified tasks). This rule
handles exploration intent (don't execute when the operator wants thinking).
They are complementary: one optimizes execution, the other prevents execution
when it's the wrong mode.

## Falsifier

This pattern is wrong if, within 6 months:
- The operator never uses exploration language again (then the routing
  failure was session-specific, not systemic)
- The rule over-fires and blocks execution on tasks where the operator
  wanted speed (then the language patterns are too broad)
- A vendor ships reliable intent classification that makes manual rules
  obsolete (unlikely in 6 months)

## Sources

- Transcript scan: 30 sessions, 19 routing-correction signals (2026-07-29, mechanical grep of `~/.grok/sessions/`)
- [[proactive-ai-volunteering-mechanisms]] — Harari & Amir 2025: proactive help reduced adoption even when useful. https://arxiv.org/abs/2509.09309
- [[self-improving-agent-systems-techniques-and-workspace-gaps]] — "Could You Be Wrong?" prompt (Hills 2026). https://www.mdpi.com/2673-2688/7/1/33
- [[narrative-as-signal]] — plausible narrative substituting for verification
- [[wire-before-build]] — companion pattern: building capabilities without wiring them

## Receipts

- Transcript scan: `Get-ChildItem ~/.grok/sessions -Recurse -Filter chat_history.jsonl | grep "I wasn.t looking for|thought partner|what should we change"` — 19 hits across 30 sessions (2026-07-29)
- AGENTS.md rule: `P:/AGENTS.md` § "Exploration vs execution — respect the operator's intent signal" (commit `d8002eb`)
- `analyze_session_patterns.py` at `P:/.agents/scripts/analyze_session_patterns.py` — automated version of the scan
